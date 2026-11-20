"""Explicit owner-data cloning into a new writable GameData directory.

Callers obtain consent and show destination/estimated size before calling clone.
No old native executable, cache, HD mod, key or runtime receipt is trusted/copied.
The original directory and its committed profile remain in place.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from . import launcher_settings as settings, maintenance, profile_backup
from .profile_backup import _no_links, _fingerprint, _stat_key
from .upstream import extractor

MAX_INI_BYTES = 65536
_CHUNK = 1024 * 1024


def _cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise RuntimeError('Game data copy cancelled; original data was preserved')


def is_writable_data(source):
    """Probe actual creation/deletion; never alter an existing file."""
    source = Path(os.path.abspath(source))
    try:
        _no_links(source)
        if not source.is_dir():
            return False
        fd, name = tempfile.mkstemp(prefix='.newsnap-data-probe-', dir=source)
        try:
            os.close(fd)
        finally:
            Path(name).unlink()
        return True
    except (OSError, ValueError):
        return False


def _recipe(profile):
    if profile is None:
        from .home_state import _profile
        profile = _profile()
    expected = profile.get('exefs_sha256') if isinstance(profile, dict) else None
    if not isinstance(expected, dict) or not expected or 'main' not in expected or 'sdk' not in expected:
        raise ValueError('Game data copy requires a supported verified game recipe')
    for name in expected:
        if (not isinstance(name, str) or name in ('.', '..')
                or not re.fullmatch('[A-Za-z0-9_.-]+', name)
                or re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', name)):
            raise ValueError('Unsafe module name in game data recipe')
    return profile


def _inputs(source, recipe):
    maintenance.validate_owner_modules(source, recipe['exefs_sha256'])
    files = {f'exefs/{name}': (source / 'exefs' / name, None) for name in recipe['exefs_sha256']}
    files['romfs/romfs.bin'] = source / 'romfs/romfs.bin', None
    ini = source / 'newsnap.ini'
    if not ini.exists():
        legacy = source / 'astralchain.ini'
        _no_links(legacy)
        ini = legacy if legacy.exists() else ini
    _no_links(ini)
    if ini.exists():
        if _fingerprint(ini)[2] > MAX_INI_BYTES:
            raise ValueError('Existing game settings exceed the 64 KiB copy limit')
        files['newsnap.ini'] = ini, None
    return {name: (path, _fingerprint(path)) for name, (path, _) in files.items()}


def _profile_files(profile, cancel=None):
    _no_links(profile)
    if not profile.exists():
        return {}
    if not profile.is_dir():
        raise ValueError('Existing save profile is not a directory')
    try:
        return profile_backup._snapshot(profile, cancel)
    except ValueError as error:
        if str(error) == 'No committed profile files to back up':
            return {}
        raise


def estimate_copy_bytes(source, profile=None):
    """Logical content size; excludes new index and temporary ZIP-transfer space.

    This is a bounded metadata-only scan. External profile data is conservatively
    included even if it can later be kept in place; estimates never write-probe it.
    """
    source = Path(os.path.abspath(source))
    _no_links(source)
    files = _inputs(source, _recipe(profile))
    owner = settings.load_profile(source)
    saved = _profile_files(owner)
    return sum(info[2] for _, info in files.values()) + sum(info[2] for info in saved.values())


def _copy_file(source, target, before, cancel=None):
    """Copy bytes to a fresh writable file with handle and path race checks."""
    _cancel(cancel)
    if _fingerprint(source) != before:
        raise RuntimeError('Original game data changed during copy')
    target.parent.mkdir(parents=True, exist_ok=True)
    digest, count = hashlib.sha256(), 0
    with source.open('rb') as incoming, target.open('xb') as output:
        if _stat_key(os.fstat(incoming.fileno())) != before:
            raise RuntimeError('Original game data changed during copy')
        while block := incoming.read(_CHUNK):
            _cancel(cancel)
            count += len(block)
            if count > before[2]:
                raise RuntimeError('Original game data changed during copy')
            digest.update(block)
            output.write(block)
        if _stat_key(os.fstat(incoming.fileno())) != before:
            raise RuntimeError('Original game data changed during copy')
        output.flush()
        os.fsync(output.fileno())
    if count != before[2] or _fingerprint(source) != before:
        raise RuntimeError('Original game data changed during copy')
    return digest.hexdigest()


def _cleanup(work, parent):
    if (work.parent != parent or not work.name.startswith('.data-copy-')
            or not work.resolve().is_relative_to(parent.resolve())):
        raise ValueError('Unsafe owner-data copy cleanup boundary')
    _no_links(work)
    shutil.rmtree(work)


def clone_readonly_data(source, destination, profile=None, cancel=None, report=print):
    """Explicitly clone verified inputs and preserve progress, into NEW destination.

    The function acquires the source save ProfileLock itself. A writable external
    custom profile is retained by absolute pointer; default/local/read-only
    profiles transfer account.uid, committed save and photos through ZIP64.
    Caller must not hold that profile lock already. Destination is published only
    after complete input verification and profile restoration have succeeded.
    """
    source, destination = Path(os.path.abspath(source)), Path(os.path.abspath(destination))
    _no_links(source)
    _no_links(destination)
    if destination.exists():
        raise FileExistsError('Game data copy requires a new destination')
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('Game data copy destination must be separate from original data')
    recipe = _recipe(profile)
    inputs = _inputs(source, recipe)
    owner = Path(os.path.abspath(settings.load_profile(source)))
    _no_links(owner)
    _cancel(cancel)
    with settings.ProfileLock(owner):
        saved = _profile_files(owner, cancel)
        external = owner != source and source not in owner.parents
        keep_external = external and owner.is_dir() and is_writable_data(owner)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _no_links(destination.parent)
        work = Path(tempfile.mkdtemp(prefix='.data-copy-', dir=destination.parent))
        stage = work / 'GameData'
        stage.mkdir()
        try:
            hashes = {}
            for number, (name, (path, before)) in enumerate(inputs.items(), 1):
                report(f'Copying verified game inputs: {number}/{len(inputs)} files ({name})')
                hashes[name] = _copy_file(path, stage / name, before, cancel)
                if _fingerprint(path) != before:
                    raise RuntimeError('Original game data changed during copy')
            _cancel(cancel)
            report('Verifying the complete copied game image and modules…')
            maintenance.verify_owner_inputs(stage, recipe, cancel_event=cancel, full=True)
            _cancel(cancel)
            files = extractor().index_romfs(stage / 'romfs/romfs.bin')
            _cancel(cancel)
            index = {'status': 'pass', 'romfs_size': (stage / 'romfs/romfs.bin').stat().st_size,
                     'romfs_sha256': hashes['romfs/romfs.bin'], 'files': files}
            (stage / 'romfs/index.json').write_text(json.dumps(index) + '\n', encoding='utf-8')
            if keep_external:
                preferences = {'profile': str(owner)}
                report('Keeping your existing writable external save profile in place.')
            else:
                if saved:
                    report('Preserving account identity, committed saves and photos…')
                    archive = profile_backup.backup_profile(owner, work / 'profile-transfer',
                                                           cancel=cancel, report=report)
                    profile_backup.restore_profile(archive, stage / 'profile', cancel=cancel)
                else:
                    (stage / 'profile').mkdir()
                preferences = {'profile_data_relative': 'profile'}
            (stage / 'launcher.json').write_text(json.dumps(preferences) + '\n', encoding='utf-8')
            _cancel(cancel)
            if any(_fingerprint(path) != before for path, before in inputs.values()):
                raise RuntimeError('Original game data changed during copy')
            if _profile_files(owner, cancel) != saved:
                raise RuntimeError('Original save profile changed during copy')
            _no_links(destination)
            if destination.exists():
                raise FileExistsError('Game data destination appeared during copy')
            stage.rename(destination)
            return destination
        finally:
            _cleanup(work, destination.parent)
