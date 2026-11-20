"""Prepare observed shader variants on this GPU before guest execution."""
import hashlib
import shutil
import struct
import json
import os
import re
import tempfile
import subprocess
from contextlib import contextmanager
from collections import Counter
from pathlib import Path

from .build import run_logged
from .importer import write_json, source_digest
from .upstream import ROOT
from .nushdb import shaders, program_record
from .paths import shader_library_dir, is_release_layout, runtime_dir


@contextmanager
def _preparation_outputs(folder):
    """Restore the last successful record/receipt after a failed preparation.

    Driver caches remain runtime-owned. A unique same-volume backup is retained
    if rollback itself fails, so its previous evidence can still be recovered.
    """
    names = ('shader-prepared.bin', 'newsnap-shader-preparation.json')
    backup = Path(tempfile.mkdtemp(prefix='.shader-prepare-', dir=folder))
    moved = []
    cleanup = False
    try:
        try:
            for name in names:
                path = folder / name
                if path.exists():
                    path.replace(backup / name)
                    moved.append(name)
        except BaseException:
            for name in moved:
                (backup / name).replace(folder / name)
            cleanup = True
            raise
        try:
            yield
        except BaseException:
            for name in names:
                if name in moved:
                    (backup / name).replace(folder / name)
                else:
                    (folder / name).unlink(missing_ok=True)
            cleanup = True
            raise
        cleanup = True
    finally:
        if cleanup:
            for name in names:
                (backup / name).unlink(missing_ok=True)
            backup.rmdir()


def validate_recording(data, answers):
    expected = (b'ACSANS\0\0' + struct.pack('<II', 2, 221) if answers else
                b'ACSPRG\0\0' + struct.pack('<II', 1, 0))
    if data[:16] != expected:
        raise ValueError('Invalid shader recording header')
    if answers:
        if (len(data) - 16) % 221:
            raise ValueError('Torn shader answer recording; replay the scene to recover it')
        return
    offset = 16
    while offset < len(data):
        if len(data) - offset < 44 + 0x880:
            raise ValueError('Torn shader program recording')
        stage, size, c1size = struct.unpack_from('<III', data, offset)
        total = 44 + 0x880 + size + c1size
        if stage not in (0, 4, 5) or size > 64 << 20 or c1size > size or total > len(data) - offset:
            raise ValueError('Invalid shader program recording')
        offset += total


def seed_libraries(folder, libraries):
    """Add default variants; observed driver answers remain necessary for exact coverage."""
    manifest = json.loads((libraries / 'manifest.json').read_text(encoding='utf-8'))
    programs, answers, seen = bytearray(), bytearray(), set()
    counts = Counter()
    for member in manifest['members']:
        path = libraries / f'{member["ordinal"]:05d}.nushdb'
        if source_digest(path) != member['sha256']:
            raise ValueError('Shader library no longer matches the verified decoding receipt')
        for stage, key, control, code, c1 in shaders(path.read_bytes()):
            counts[str(stage)] += 1
            if stage == 3 or key in seen:
                continue
            seen.add(key)
            programs.extend(program_record(stage, key, control, code, c1))
            answers.extend(struct.pack('<I', stage) + key + bytes(32) + b'\x04' * 32 + bytes(120) + b'\x02')
    for target, magic, version, record, extra in (
        ('programs', b'ACSPRG\0\0', 1, 0, programs),
        ('answers', b'ACSANS\0\0', 2, 221, answers),
    ):
        path = folder / f'seed-{target}.bin'
        # Observed records precede defaults and preserve their higher priority.
        original = path.read_bytes() if path.is_file() else magic + struct.pack('<II', version, record)
        validate_recording(original, target == 'answers')
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(original + extra)
        temporary.replace(path)
    return {'library_stages': dict(counts), 'unique_supported_programs': len(seen),
            'unsupported_geometry_stages': counts['3'],
            'coverage': 'default texture answers plus observed variants; exact unseen variants/pipelines unverified'}


RECEIPT = 'newsnap-shader-preparation.json'


def preparation_inputs(folder, all_libraries=False, libraries=None):
    """Everything a preparation is made from: the runtime, the translator, the recordings of play and, with
    all_libraries, the decoded shader libraries (their manifest and the name, size and time of each file).

    The executable, the translator and the recordings are recognised by their receipts when unchanged
    (verified_files), so asking this before every game start reads no large file again.
    """
    from .launcher_settings import _settings_source
    from .verified_files import STORE, VerifiedFiles
    folder = Path(folder)
    receipts = VerifiedFiles(folder / STORE)
    names = ('newsnap.exe', 'ac_xlate.exe', 'ac_xlate.id', 'shader-answers.bin', 'shader-programs.bin',
             'pipeline-keys.bin')
    files = {name: receipts.digest(folder / name) if (folder / name).is_file() else None for name in names}
    receipts.save()
    listing = None
    if all_libraries:
        libraries = Path(libraries if libraries is not None else shader_library_dir(ROOT))
        value = hashlib.sha256((libraries / 'manifest.json').read_bytes())
        with os.scandir(libraries) as found:
            for name, size, moment in sorted((entry.name, entry.stat().st_size, entry.stat().st_mtime_ns)
                                             for entry in found if entry.is_file()):
                value.update(f'{name}\0{size}\0{moment}\n'.encode('utf-8'))
        listing = value.hexdigest()
    config = dict.fromkeys(('GPL', 'PIPE_PREBUILD', 'PIPE_SYNC'))
    ini = _settings_source(folder / 'newsnap.ini')
    if ini.is_file():
        for line in ini.read_text(encoding='utf-8-sig').splitlines():
            key, _, value = line.partition('=')
            key = key.strip().upper().removeprefix('AC_')
            value = value.strip()
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if key in config and value:
                config[key] = value
    for key in config:
        config[key] = os.environ.get(f'AC_{key}', config[key])
    return {'format': 2, 'scope': 'all' if all_libraries else 'observed', 'files': files, 'libraries': listing,
            'pipeline_settings': config}


def already_prepared(folder, inputs):
    """The number of variants of the last finished preparation when it was made from exactly these inputs and
    what it left is still there; None when the preparation has to run.

    Running it again from the same inputs gives the same record. The driver's own cache is not ours to check:
    with another driver the game rebuilds it in the background at its start (vk_pipeline.c, «driver cache»),
    with or without a preparation before. NEWSNAP_PREPARE_ALWAYS=1 runs the preparation regardless.
    """
    folder = Path(folder)
    try:
        if os.environ.get('NEWSNAP_PREPARE_ALWAYS') == '1':
            return None
        receipt = json.loads((folder / RECEIPT).read_text(encoding='utf-8'))
        if not isinstance(receipt, dict) or receipt.get('inputs') != inputs or type(receipt.get('variants')) is not int:
            return None
        marker = folder / 'newsnap-game.json'
        if marker.is_file() and json.loads(marker.read_text(encoding='utf-8')).get('shader_preparation_required') is True:
            return None   # a rebuilt runtime asks for a preparation: it runs
        prepared = folder / 'shader-prepared.bin'
        data = prepared.read_bytes()
        if (len(data) < 16 or data[:8] != b'ACSPRP\0\0' or (len(data) - 16) // 36 != receipt['variants']
                or hashlib.sha256(data).hexdigest() != receipt.get('prepared_sha256')):
            return None
        if any(not (folder / name).is_file() for name in ('seed-answers.bin', 'seed-programs.bin')):
            return None
        if (folder / 'shader-prepare-journal.bin').exists():   # the driver crashed in the last run
            return None
        if receipt.get('shader_cache') is not (folder / 'shader-cache').is_dir():
            return None   # the translated shaders the preparation left were removed
        if receipt.get('recorded_pipeline_cache') and (folder / 'pipeline-cache.bin').stat().st_size < 32:
            return None
        return receipt['variants']
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def _prepare_recorded_pipelines(exe, logfile, env):
    try:
        with logfile.open('wb') as stream:
            subprocess.run([exe, '--prepare-recorded-pipelines'], cwd=exe.parent, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                           check=True, timeout=300)
        return 'prepare-shaders: recorded graphics cache saved' in logfile.read_text(encoding='utf-8', errors='replace')
    except (OSError, subprocess.SubprocessError):
        print(f'Optional recorded pipeline preparation did not finish. See {logfile}.', flush=True)
        return False


def prepare_observed(folder, all_libraries=False):
    folder = Path(folder).resolve()
    exe = folder / 'newsnap.exe'
    if not exe.is_file():
        raise ValueError('Build newsnap.exe before preparing shaders')
    try:
        inputs = preparation_inputs(folder, all_libraries)
    except (OSError, ValueError):
        inputs = None   # e.g. no library manifest: the preparation below reports it
    count = already_prepared(folder, inputs) if inputs else None
    if count is not None:
        print(f'Shaders already prepared from these recordings and this runtime ({count} variants): nothing to do.',
              flush=True)
        return count
    for source, target, magic, version, record in (
        ('shader-answers.bin', 'seed-answers.bin', b'ACSANS\0\0', 2, 221),
        ('shader-programs.bin', 'seed-programs.bin', b'ACSPRG\0\0', 1, 0),
    ):
        path = folder / source
        if not path.is_file() and not all_libraries:
            raise ValueError('No observed shader recordings; run a scene before preparing its variants')
        data = path.read_bytes() if path.is_file() else magic + struct.pack('<II', version, record)
        validate_recording(data, record == 221)
        temporary = folder / (target + '.tmp')
        if path.is_file():
            shutil.copyfile(path, temporary)
        else:
            temporary.write_bytes(data)
        temporary.replace(folder / target)
    census = seed_libraries(folder, shader_library_dir(ROOT)) if all_libraries else {}
    print(f'Shader census: {census or "observed variants only"}', flush=True)
    prepared = folder / 'shader-prepared.bin'
    env = dict(os.environ, AC_PIPELINE_CACHE=str(folder / 'pipeline-cache.bin'))
    logfile = (runtime_dir(ROOT) / 'logs' if is_release_layout(ROOT) else ROOT / 'build/logs') / 'prepare-shaders.log'
    with _preparation_outputs(folder):
        run_logged([exe, '--prepare-shaders'], logfile, env)
        log = logfile.read_text(encoding='utf-8')
        translation = re.search(r', (\d+) translations failed', log)
        driver = re.search(r'; (\d+) failed, (\d+) not in the shader cache', log)
        if not translation or not driver or any(int(n) for n in (translation[1], *driver.groups())):
            raise ValueError(f'Shader preparation incomplete; inspect {logfile}')
        data = prepared.read_bytes()
        if len(data) < 16 or data[:8] != b'ACSPRP\0\0' or struct.unpack_from('<II', data, 8) != (1, 36) or (len(data) - 16) % 36:
            raise ValueError('The runtime did not produce a valid preparation record')
        count = (len(data) - 16) // 36
        recorded_cache = (
            'vk_pipeline: graphics pipeline library off:' in log
            and (folder / 'pipeline-keys.bin').is_file()
            and _prepare_recorded_pipelines(exe, logfile.with_name('prepare-recorded-pipelines.log'), env))
        write_json(folder / RECEIPT, {
            'scope': 'library defaults and observed variants' if all_libraries else 'observed variants only',
            'census': census, 'variants': count, 'inputs': inputs,
            'shader_cache': (folder / 'shader-cache').is_dir(),
            'recorded_pipeline_cache': recorded_cache,
            'prepared_sha256': source_digest(prepared), 'exe_sha256': source_digest(exe),
            'translator_sha256': source_digest(folder / 'ac_xlate.exe')})
    print(f'Prepared {count} shader variants before gameplay. Unvisited scenes remain unverified.', flush=True)
    return count
