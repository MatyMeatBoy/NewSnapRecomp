"""Prepare observed shader variants on this GPU before guest execution."""
import shutil
import struct
import json
import os
import re
from collections import Counter
from pathlib import Path

from .build import run_logged
from .importer import write_json, source_digest
from .upstream import ROOT
from .nushdb import shaders, program_record
from .paths import shader_library_dir, is_release_layout, runtime_dir


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


def prepare_observed(folder, all_libraries=False):
    folder = Path(folder).resolve()
    exe = folder / 'newsnap.exe'
    if not exe.is_file():
        raise ValueError('Build newsnap.exe before preparing shaders')
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
    previous = folder / 'shader-prepared.previous.bin'
    if prepared.exists():
        prepared.replace(previous)
    env = dict(os.environ, AC_PIPELINE_CACHE=str(folder / 'pipeline-cache.bin'))
    logfile = (runtime_dir(ROOT) / 'logs' if is_release_layout(ROOT) else ROOT / 'build/logs') / 'prepare-shaders.log'
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
    write_json(folder / 'newsnap-shader-preparation.json', {
        'scope': 'library defaults and observed variants' if all_libraries else 'observed variants only',
        'census': census, 'variants': count,
        'prepared_sha256': source_digest(prepared), 'exe_sha256': source_digest(exe),
        'translator_sha256': source_digest(folder / 'ac_xlate.exe')})
    print(f'Prepared {count} shader variants before gameplay. Unvisited scenes remain unverified.', flush=True)
    return count
