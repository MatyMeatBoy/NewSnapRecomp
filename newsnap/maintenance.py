"""Rebuild an owner's runtime locally, then switch recoverably without touching saves.

Build kits contain public source and portable tools only. Console keys and original
packages are never consulted. A failed or cancelled build leaves the active runtime
intact; an interrupted installation is rolled back before another launch.
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath

from .paths import data_dir
from .upstream import COMMIT
from .version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES

RUNTIME_FILES = ('newsnap.exe', 'SDL3.dll', 'libopus-0.dll', 'ac_xlate.exe',
                 'ac_xlate.id', 'romfs-index.bin', 'libxess.dll', 'nvngx_dlss.dll',
                 'upscalers/amd_fidelityfx_loader_vk.dll', 'upscalers/amd_fidelityfx_upscaler_vk.dll',
                 'upscalers/license.md', 'upscalers/3rdpartynotice.md',
                 'licenses/NVIDIA-DLSS.txt', 'licenses/NVIDIA-DLSS-receipt.json',
                 'licenses/FidelityFX-SDK-1.1.4-LICENSE.txt',
                 'newsnap-game.json')
REQUIRED_FILES = ('newsnap.exe', 'SDL3.dll', 'libopus-0.dll', 'ac_xlate.exe', 'ac_xlate.id', 'romfs-index.bin')
INVALIDATED = ('pipeline-cache.bin', 'shader-prepared.bin', 'newsnap-shader-preparation.json',
               'shader-prepared-driver.txt', 'shader-cache')
TRANSACTION = '.runtime-transaction'


class MaintenanceCancelled(RuntimeError):
    pass


def digest(path, cancel_event=None):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 << 20), b''):
            _cancel(cancel_event)
            value.update(block)
    return value.hexdigest()


def _cancel(event):
    if event is not None and event.is_set():
        raise MaintenanceCancelled('Reconstrucción cancelada; se conserva el runtime anterior.')


def _json(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(8 << 20)
        if stream.read(1):
            raise ValueError('Maintenance metadata exceeds its size limit')
    return json.loads(raw.decode('utf-8-sig'))


def assess_runtime(root):
    directory = data_dir(root)
    try:
        if (directory / TRANSACTION).exists():
            raise ValueError('Hay una reconstrucción interrumpida que necesita recuperación.')
        marker = _json(directory / 'newsnap-game.json')
        if (marker.get('format') != 1 or marker.get('runtime_api') != RUNTIME_API or
                marker.get('runtime_version') != VERSION or
                marker.get('game_version') != '2.0.1' or
                not set(RUNTIME_CAPABILITIES).issubset(marker.get('capabilities', []))):
            raise ValueError('El runtime local necesita las funciones de esta versión.')
        if (Path(root) / 'MANIFEST.json').is_file():
            revision = _json(Path(root) / 'MANIFEST.json').get('source_revision')
            if revision and marker.get('runtime_source_revision', marker.get('source_revision')) != revision:
                raise ValueError('El runtime local necesita la receta de esta actualización.')
        if digest(directory / 'newsnap.exe') != marker.get('native_executable_sha256'):
            raise ValueError('El ejecutable local falta o necesita reparación.')
        _verify_runtime_files(directory, marker)
        return {'needs_rebuild': False, 'reason': '', 'runtime_version': marker.get('runtime_version')}
    except (OSError, ValueError, TypeError, AttributeError) as error:
        return {'needs_rebuild': True, 'reason': str(error), 'runtime_version': None}


def _verify_runtime_files(directory, marker):
    inventory = marker.get('runtime_files', {})
    if not isinstance(inventory, dict) or not set(inventory).issubset(RUNTIME_FILES):
        raise ValueError('Invalid runtime artifact receipt')
    for name, expected in inventory.items():
        if digest(directory / name) != expected:
            raise ValueError(f'El archivo {name} necesita reparación.')


def validate_owner_modules(directory, expected):
    """Reject unverified modules that the generator's load order would consume."""
    for name in ('main', *(f'subsdk{i}' for i in range(10)), 'sdk'):
        if name not in expected and (Path(directory)/'exefs'/name).exists():
            raise ValueError(f'Unexpected ExeFS module {name}; use the verified game 2.0.1 inputs')


def verify_owner_inputs(directory, profile, cancel_event=None):
    """Verify original bytes against the public supported-version fingerprints."""
    directory = Path(directory)
    expected = profile.get('exefs_sha256')
    if not isinstance(expected, dict) or not expected or not profile.get('romfs_sha256'):
        raise ValueError('The build recipe has no verified owner-input fingerprints')
    validate_owner_modules(directory,expected)
    files = []
    for name, checksum in expected.items():
        if PurePosixPath(name).name != name or name in ('.', '..') or '\\' in name:
            raise ValueError('Unsafe ExeFS name in build recipe')
        path = directory / 'exefs' / name
        if digest(path, cancel_event) != checksum:
            raise ValueError(f'ExeFS {name} differs from the supported verified game 2.0.1')
        files.append({'name': name, 'sha256': checksum, 'size': path.stat().st_size})
    if digest(directory / 'romfs/romfs.bin', cancel_event) != profile['romfs_sha256']:
        raise ValueError('RomFS differs from the supported verified game 2.0.1')
    control = profile['verified_control']
    if control.get('display_version') != '2.0.1' or any(type(control.get(k)) is not int or control[k] <= 0
                                                       for k in ('save_size', 'journal_size')):
        raise ValueError('Missing verified control metadata in recipe')
    return {'files': files}, control


def _remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _safe_runtime_path(directory, name):
    path = directory / name
    for parent in (path, *path.parents):
        if parent == directory:
            break
        if parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction()):
            raise ValueError('Runtime links cannot be switched safely')
    return path


def _sync_file(path):
    with Path(path).open('r+b') as stream:
        stream.flush()
        os.fsync(stream.fileno())


def _sync_directory(path):
    """Best effort metadata flush; Windows/filesystems may reject directory flushes.

    File data is always fsynced. This protocol protects process interruption; it
    does not promise recovery from every filesystem/device power-loss behavior.
    """
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
        create.restype = wintypes.HANDLE
        handle = create(str(Path(path).resolve()), 0xC0000000, 7, None, 3, 0x02000000, None)
        if handle == ctypes.c_void_p(-1).value:
            return False
        kernel.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        try:
            return bool(kernel.FlushFileBuffers(handle))
        finally:
            kernel.CloseHandle(handle)
    try:
        handle = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(handle)
            return True
        finally:
            os.close(handle)
    except OSError:
        return False


def _sync_tree(folder):
    paths = list(Path(folder).rglob('*'))
    for path in paths:
        if path.is_file():
            _sync_file(path)
    directories = [p for p in paths if p.is_dir()] + [Path(folder)]
    # Attempt every directory, even when the filesystem rejects an earlier one.
    return all([_sync_directory(p) for p in sorted(directories, key=lambda p: len(p.parts), reverse=True)])


def _backup_inventory(backup, cancel_event=None):
    if not backup.is_dir():
        raise ValueError('Runtime backup integrity failure: backup directory missing')
    files, directories = {}, []
    for path in sorted(backup.rglob('*')):
        _cancel(cancel_event)
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Runtime backup integrity failure: backup link')
        name = path.relative_to(backup).as_posix()
        if path.is_dir():
            directories.append(name)
        elif path.is_file():
            files[name] = {'size': path.stat().st_size, 'sha256': digest(path, cancel_event)}
        else:
            raise ValueError('Runtime backup integrity failure: unsupported backup entry')
    return {'files': files, 'directories': directories}


def recover_runtime(root):
    """Idempotently restore the previous generation after a failed switch."""
    directory = data_dir(root)
    transaction = directory / TRANSACTION
    _safe_runtime_path(directory, TRANSACTION)
    if not transaction.exists():
        return False
    journal_path = transaction / 'journal.json'
    if not journal_path.exists():
        # Backups are copied before publishing a journal; active files are intact.
        shutil.rmtree(transaction)
        return True
    journal = _json(journal_path)
    files = journal.get('files', {})
    if journal.get('format') != 2 or not isinstance(files, dict) or not set(files).issubset(RUNTIME_FILES + INVALIDATED):
        raise ValueError('Unsafe runtime recovery journal; keep the transaction for manual recovery')
    if _backup_inventory(transaction / 'backup') != journal.get('backup'):
        raise ValueError('Runtime backup integrity failure; keep the transaction for manual recovery')
    # Validate the whole backup and every destination before any live write.
    for name, existed in files.items():
        if type(existed) is not bool:
            raise ValueError('Invalid runtime recovery state')
        _safe_runtime_path(directory, name)
        if existed and not (transaction / 'backup' / name).exists():
            raise ValueError(f'Runtime backup integrity failure: missing {name}')
    for name, existed in files.items():
        target, backup = _safe_runtime_path(directory, name), transaction / 'backup' / name
        if existed:
            if not backup.exists():
                raise ValueError(f'Runtime recovery backup missing: {name}')
            # Copy, rather than consume, backup so a second interrupted recovery works.
            temporary = transaction / ('restore-' + name)
            temporary.parent.mkdir(parents=True, exist_ok=True)
            _remove(temporary)
            if backup.is_dir():
                shutil.copytree(backup, temporary)
                _sync_tree(temporary)
                _remove(target)
            else:
                shutil.copy2(backup, temporary)
                _sync_file(temporary)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(target)
            _sync_directory(target.parent)
        else:
            _remove(target)
            _sync_directory(target.parent)
    # Restored bytes and metadata precede committing recovery. Cleanup must never
    # leave a pending journal referring to already discarded backup files.
    journal_path.unlink()
    _sync_directory(transaction)
    shutil.rmtree(transaction)
    return True


def install_candidate(root, candidate, cancel_event=None):
    """Only a validated, finite list of runtime artifacts can enter GameData.

    Callers hold the profile lock. Cancellation is accepted before the switch;
    once replacing files starts it completes or rolls back as one transaction.
    """
    directory, candidate = data_dir(root), Path(candidate)
    for path in candidate.rglob('*'):
        relative = path.relative_to(candidate).as_posix()
        if (path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()) or
                path.is_file() and relative not in RUNTIME_FILES or
                path.is_dir() and not any(n.startswith(relative + '/') for n in RUNTIME_FILES)):
            raise ValueError('Unexpected file in runtime candidate')
    marker = _json(candidate / 'newsnap-game.json')
    if (marker.get('runtime_api') != RUNTIME_API or
            not set(RUNTIME_CAPABILITIES).issubset(marker.get('capabilities', [])) or
            digest(candidate / 'newsnap.exe') != marker.get('native_executable_sha256')):
        raise ValueError('Runtime candidate failed compatibility/integrity validation')
    _verify_runtime_files(candidate, marker)
    _cancel(cancel_event)
    recover_runtime(root)
    transaction = directory / TRANSACTION
    backup = transaction / 'backup'
    backup.mkdir(parents=True)
    names = list(RUNTIME_FILES) + list(INVALIDATED)
    for name in names:
        _safe_runtime_path(directory, name)
    journal = {'format': 2, 'files': {n: (directory / n).exists() for n in names}}
    try:
        for name, exists in journal['files'].items():
            _cancel(cancel_event)
            if exists:
                source = directory / name
                if source.is_symlink() or (hasattr(source, 'is_junction') and source.is_junction()):
                    raise ValueError('Runtime links cannot be switched safely')
                if source.is_dir():
                    shutil.copytree(source, backup / name)
                else:
                    (backup / name).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, backup / name)
        _cancel(cancel_event)
        journal['backup'] = _backup_inventory(backup, cancel_event)
        # Durable file data precedes the journal and the first live replacement.
        synced = [_sync_tree(backup), _sync_tree(candidate), _sync_directory(transaction),
                  _sync_directory(directory)]
        journal['directory_sync_supported'] = all(synced)
        _cancel(cancel_event)
        journal_temporary = transaction / 'journal.tmp'
        with journal_temporary.open('w', encoding='utf-8') as stream:
            json.dump(journal, stream)
            stream.flush()
            os.fsync(stream.fileno())
        journal_temporary.replace(transaction / 'journal.json')
        _sync_directory(transaction)
        for name in names:
            if (candidate / name).exists():
                (directory / name).parent.mkdir(parents=True, exist_ok=True)
                (candidate / name).replace(directory / name)
            else:
                _remove(directory / name)
            _sync_directory((directory / name).parent)
    except BaseException:
        recover_runtime(root)
        raise
    # Removing the journal commits the generation. Backups are then disposable.
    (transaction / 'journal.json').unlink()
    _sync_directory(transaction)
    shutil.rmtree(transaction)


def verify_build_kit(kit_root, root=None, cancel_event=None):
    kit = Path(kit_root).resolve()
    manifest = _json(kit / 'build-kit.json')
    if (manifest.get('format') != 1 or manifest.get('runtime_version') != VERSION or
            manifest.get('runtime_api') != RUNTIME_API or manifest.get('donor_commit') != COMMIT or
            set(manifest.get('capabilities', [])) != set(RUNTIME_CAPABILITIES)):
        raise ValueError('Build kit does not match this launcher/runtime recipe')
    if root is not None and (Path(root) / 'MANIFEST.json').exists():
        revision = _json(Path(root) / 'MANIFEST.json').get('source_revision')
        if revision and revision != manifest.get('source_revision'):
            raise ValueError('Build kit source revision differs from the installed release')
    listed = manifest.get('files')
    if not isinstance(listed, dict):
        raise ValueError('Build kit has no file inventory')
    for path in kit.rglob('*'):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Build kit links are not allowed')
        if path.is_file() and path.name != 'build-kit.json' and path.relative_to(kit).as_posix() not in listed:
            raise ValueError(f'Unlisted build kit file: {path.relative_to(kit)}')
    for name, expected in listed.items():
        relative = PurePosixPath(name)
        path = kit.joinpath(*relative.parts)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or not path.resolve().is_relative_to(kit):
            raise ValueError('Unsafe build kit path')
        if digest(path, cancel_event) != expected:
            raise ValueError(f'Build kit integrity mismatch: {name}')
    for required in ('python/python.exe', 'source/newsnap/maintenance.py', 'source/newsnap/build.py',
                     'source/third_party/astral/tools/build_game.py', 'sdk/llvm/bin/clang.exe', 'sdk/bin/ninja.exe'):
        if required not in manifest['files']:
            raise ValueError(f'Build kit is incomplete: {required}')
    return manifest


def _stop_tree(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=False,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def run_build_command(command, cwd, logfile, cancel_event=None, progress=None):
    """Keep output on disk, poll cancellation, and reap the entire owned tool tree."""
    logfile.parent.mkdir(parents=True, exist_ok=True)
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
    environment = dict(os.environ)
    cache_optout = environment.get('NEWSNAP_GENERATION_CACHE') == '0'
    for key in list(environment):
        if key.upper().startswith(('PYTHON', 'AC_', 'NEWSNAP_')):
            environment.pop(key)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['PYTHONUNBUFFERED'] = '1'
    if cache_optout:
        environment['NEWSNAP_GENERATION_CACHE'] = '0'
    from .progress import ProgressTail, unbuffered_command
    tail=ProgressTail(progress or (lambda value:None))
    with logfile.open('wb') as log, logfile.open('rb') as reader:
        process = subprocess.Popen(unbuffered_command(command), cwd=cwd, env=environment,
                                   stdout=log, stderr=subprocess.STDOUT, **flags)
        try:
            while process.poll() is None:
                _cancel(cancel_event)
                # Bound work and memory per poll, without dropping raw output.
                for _ in range(4):
                    block=reader.read(64<<10)
                    if not block:break
                    tail.feed(block)
                    _cancel(cancel_event)
                time.sleep(0.1)
            _cancel(cancel_event)
            # Include final buffered output, including a last line without LF.
            while block:=reader.read(64<<10):
                _cancel(cancel_event)
                tail.feed(block)
            tail.finish()
            if process.returncode:
                raise ValueError(f'La reconstrucción falló ({process.returncode}). Registro: {logfile}')
        except BaseException:
            _stop_tree(process)
            raise


def rebuild_runtime(root, kit_root, cancel_event=None, progress=None, force=False, *, generation_cache_root=None):
    from .launcher_settings import ProfileLock, load_profile
    root, kit = Path(root), Path(kit_root).resolve()
    progress = progress or (lambda text: None)
    with ProfileLock(load_profile(root)):
        recover_runtime(root)
        if not force and not assess_runtime(root)['needs_rebuild']:
            return {'rebuilt': False}
        from .progress import ProgressUpdate
        progress(ProgressUpdate('verify-tools','Verificando las herramientas de reconstrucción…'))
        manifest = verify_build_kit(kit, root, cancel_event)
        directory = data_dir(root)
        work = Path(tempfile.mkdtemp(prefix='.runtime-build-', dir=directory))
        try:
            # Adaptation and all generated output go to work, never the kit.
            source = kit / 'source'
            progress(ProgressUpdate('verify-inputs','Verificando tus datos originales…'))
            command = [kit / 'python/python.exe', '-B', '-E', '-s', '-m', 'newsnap.maintenance',
                       '--worker', '--data', directory.resolve(), '--work', work.resolve(),
                       '--sdk', kit / 'sdk', '--source-revision', manifest['source_revision']]
            if generation_cache_root is not None:
                # Preserve raw link components so the cache's reparse-point
                # guards can reject them before any writes or eviction.
                command += ['--generation-cache-root', Path(generation_cache_root).absolute()]
            logfile = directory / 'logs/runtime-rebuild.log'
            run_build_command(command, source, logfile, cancel_event, progress)
            _cancel(cancel_event)
            cache_record = None
            cache_receipt = work / 'logs/generation-cache.json'
            if cache_receipt.is_file():
                cache_record = _json(cache_receipt)
                shutil.copy2(cache_receipt, directory / 'logs/generation-cache.json')
            progress(ProgressUpdate('activate','Activando el runtime verificado…'))
            install_candidate(root, work / 'candidate', cancel_event)
            return {'rebuilt': True, 'runtime_version': VERSION, 'logfile': str(logfile),
                    'generation_cache': cache_record}
        finally:
            shutil.rmtree(work)


def _worker():
    import argparse
    from .build import build
    from .upstream import ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true', required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--generation-cache-root', type=Path)
    args = parser.parse_args()
    tools = args.sdk / 'shader-tools'
    exe = build(args.sdk, shader_tools=tools if tools.is_dir() else None,
                owner_data=args.data, work_dir=args.work, jobs=min(8, os.cpu_count() or 1),
                generation_cache_root=args.generation_cache_root)
    candidate = args.work / 'candidate'
    candidate.mkdir()
    for name in RUNTIME_FILES:
        if name != 'newsnap-game.json' and (exe.parent / name).is_file():
            (candidate / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(exe.parent / name, candidate / name)
    if any(not (candidate / name).is_file() for name in REQUIRED_FILES):
        raise ValueError('Build did not produce the complete runtime artifact set')
    # Verify both the host artifact and loading the exact owner modules; no guest,
    # GPU or real profile is opened by these two probes.
    for mode in ('--selftest', '--probe-loader'):
        print('Checking candidate host selftest' if mode=='--selftest' else
              'Checking candidate owner-module loader',flush=True)
        probe_log = args.work / (mode[2:] + '.log')
        try:
            run_build_command([candidate / 'newsnap.exe', '--exefs', args.data / 'exefs',
                               '--romfs', args.data / 'romfs', '--profile', args.work / 'probe-profile', mode],
                              candidate, probe_log)
        except ValueError:
            # The parent removes its staging directory; keep bounded diagnostics
            # in its persistent rebuild log before propagating the failure.
            with probe_log.open('rb') as stream:
                stream.seek(max(0, probe_log.stat().st_size - 32768))
                print(stream.read().decode('utf-8', errors='replace'), flush=True)
            raise
    profile = _json(ROOT / 'profiles/snap-2.0.1.json')
    marker = {'format': 1, 'game_version': '2.0.1', 'runtime_api': RUNTIME_API,
              'runtime_version': VERSION, 'runtime_source_revision': args.source_revision,
              'source_revision': args.source_revision,
              'main_sha256': profile['main_sha256'], 'contains_console_keys': False,
              'native_executable_sha256': digest(candidate / 'newsnap.exe'),
              'runtime_files': {name: digest(candidate / name) for name in RUNTIME_FILES
                                if name != 'newsnap-game.json' and (candidate / name).is_file()},
              'capabilities': list(RUNTIME_CAPABILITIES), 'shader_preparation_required': True}
    (candidate / 'newsnap-game.json').write_text(json.dumps(marker, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    _worker()
