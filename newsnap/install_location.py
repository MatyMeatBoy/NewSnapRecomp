"""Relocate a read-only public launcher, never its owner's data or settings.

The caller retains the original path, reports relocation, and supervises the
returned launcher with the original arguments and inherited output handles.
No network or process launch is performed here.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

from . import updater

_OWNER_PARTS = {'gamedata-import', 'hdshadows', 'texpack', 'photos', 'save',
                'save-tx', 'save-backup', 'imports', 'exefs', 'romfs',
                'shader-cache', 'pipeline-cache'}


def _can_write(root):
    """Probe real creation, rather than trusting permission bits or os.access."""
    try:
        fd, name = tempfile.mkstemp(prefix='.newsnap-write-', dir=root)
        try:
            os.close(fd)
        finally:
            Path(name).unlink()
        return True
    except OSError:
        return False


def _version(value):
    match = re.fullmatch(r'(\d+(?:\.\d+){1,3})(?:-([A-Za-z0-9.-]+))?', value)
    if not match:
        raise updater.UpdateError('Unrecognized launcher version in relocation manifest')
    numbers = tuple(int(n) for n in match[1].split('.'))
    suffix = tuple((0, int(n)) if n.isdigit() else (1, n)
                   for n in (match[2] or '').split('.'))
    return numbers + (0,) * (4 - len(numbers)), match[2] is None, suffix


def _manifest(root):
    path = root / 'MANIFEST.json'
    updater._no_links(path)
    with path.open('rb') as stream:
        raw = stream.read(updater.MAX_MANIFEST_BYTES + 1)
    manifest = updater._manifest(raw)
    files = manifest['files']
    if 'NewSnapLauncher.exe' not in files:
        raise updater.UpdateError('Relocation manifest must include NewSnapLauncher.exe')
    _version(manifest['version'])
    for name in files:
        if any(part.casefold() in _OWNER_PARTS for part in Path(name).parts):
            raise updater.UpdateError('Owner data is forbidden in a public relocation manifest')
    return manifest, raw


def _verify(root, manifest, *, owned_ini=False):
    for name, expected in manifest['files'].items():
        path = root / name
        updater._no_links(path)
        if owned_ini and path.is_file() and path.suffix.casefold() == '.ini':
            continue  # A first-install default becomes the owner's configuration.
        if (not path.is_file() or path.stat().st_size != expected['size']
                or updater._digest(path).lower() != expected['sha256'].lower()):
            raise updater.UpdateError(f'Public relocation file failed verification: {name}')


@contextmanager
def _copy_lock(path, timeout=30):
    """A process-owned lock; abandoned copies do not leave a permanently busy flag."""
    updater._no_links(path)
    with path.open('a+b') as stream:
        stream.seek(0, os.SEEK_END)
        if not stream.tell():
            stream.write(b'0')
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            stream.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if time.monotonic() >= deadline:
                    raise updater.UpdateError('Another launcher relocation is still running') from error
                time.sleep(.05)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _remove_stage(stage, parent):
    # Recursive deletion is restricted to the exact scratch child we created.
    if (stage.parent != parent or not stage.name.startswith('.relocate-')
            or not stage.resolve().is_relative_to(parent.resolve())):
        raise updater.UpdateError('Unsafe relocation cleanup boundary')
    updater._no_links(stage)
    shutil.rmtree(stage)


def _upgrade(stage, target, manifest):
    """Replace only public inventory, retaining recovery bytes if rollback fails."""
    recovery = Path(tempfile.mkdtemp(prefix='.relocate-recovery-', dir=target.parent))
    changed, created = [], []
    keep_recovery = False
    try:
        for number, name in enumerate([*manifest['files'], 'MANIFEST.json']):
            output = target / name
            updater._no_links(output)
            if output.is_file() and output.suffix.casefold() == '.ini':
                continue
            missing, parent = [], output.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created.append(directory)
            existed = output.exists()
            if existed and not output.is_file():
                raise updater.UpdateError('Public relocation destination is not a file')
            backup = recovery / str(number)
            if existed:
                os.replace(output, backup)
            changed.append((output, backup, existed))
            os.replace(stage / name, output)
        _verify(target, manifest, owned_ini=True)
    except Exception as error:
        failures = []
        for output, backup, existed in reversed(changed):
            try:
                if existed:
                    os.replace(backup, output)
                else:
                    output.unlink(missing_ok=True)
            except OSError as rollback_error:
                failures.append(str(rollback_error))
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass
        if failures:
            keep_recovery = True
            raise updater.UpdateError(f'Relocation recovery retained at {recovery}: {failures}') from error
        raise updater.UpdateError(f'Relocation upgrade rolled back: {error}') from error
    finally:
        if not keep_recovery:
            _remove_stage(recovery, target.parent)


def writable_install(root, local_root=None):
    """Return writable root, or a verified per-source public copy in local storage.

    local_root overrides the LocalAppData base for tests/explicit configuration.
    New instances are published by an atomic directory rename. Upgrades use a
    rollback transaction and preserve unlisted files and existing INIs.
    An existing invalid instance is rejected, never erased or repaired over data.
    Same/newer verified instances are reused, so an old protected installation
    cannot downgrade the user's updated writable copy.
    """
    root = Path(os.path.abspath(root))
    updater._no_links(root)
    if not root.is_dir():
        raise updater.UpdateError('Launcher installation is not a directory')
    if _can_write(root):
        return root
    manifest, raw = _manifest(root)
    # Verify the source even when an existing newer destination will be reused.
    _verify(root, manifest)
    identity = os.path.normcase(str(root))
    key = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:32]
    if local_root is None:
        local_root = os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local'
    parent = Path(os.path.abspath(local_root)) / 'NewSnapRecomp/installs'
    target = parent / key
    # A destination must never alias the source or contain it.
    if target == root or target in root.parents or root in target.parents:
        raise updater.UpdateError('Writable fallback must be separate from the original installation')
    updater._no_links(parent)
    parent.mkdir(parents=True, exist_ok=True)
    updater._no_links(parent)
    with _copy_lock(parent / (key + '.lock')):
        updater._no_links(target)
        if target.exists():
            current, _ = _manifest(target)
            _verify(target, current, owned_ini=True)
            if _version(current['version']) >= _version(manifest['version']):
                if not _can_write(target):
                    raise updater.UpdateError('The local launcher instance is also read-only')
                return target
        stage = Path(tempfile.mkdtemp(prefix='.relocate-', dir=parent))
        try:
            for name in manifest['files']:
                source, output = root / name, stage / name
                updater._no_links(source)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, output)
            (stage / 'MANIFEST.json').write_bytes(raw)
            _verify(stage, manifest)
            # Detect a source update during copying; do not publish mixed generations.
            if _manifest(root)[1] != raw:
                raise updater.UpdateError('Original launcher manifest changed during relocation')
            if target.exists():
                _upgrade(stage, target, manifest)
                # INIs belong to the owner after first installation; preserve
                # them instead of treating edited settings as corruption.
                _verify(target, manifest, owned_ini=True)
            else:
                stage.rename(target)
            return target
        finally:
            if stage.exists():
                _remove_stage(stage, parent)
