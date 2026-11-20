"""Full committed-profile backups to a user-selected folder, including large saves.

The caller MUST hold launcher_settings.ProfileLock(profile) throughout backup.
No cloud provider is contacted: the selected folder may be synced by the user's
own software. Restores always create a new profile, never replace a live one.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import uuid
import zipfile

MANIFEST_NAME = 'profile-backup.json'
MAX_FILE_BYTES = 16 * 1024 ** 3
MAX_TOTAL_BYTES = 64 * 1024 ** 3
MAX_FILES = 10000
MAX_MANIFEST_BYTES = 8 * 1024 ** 2
_CHUNK = 1024 * 1024
_PRIVATE_SUFFIXES = {'.keys', '.key', '.pem', '.pfx', '.p12', '.log'}


def _cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise RuntimeError('Profile backup/restore cancelled')


def _no_links(path):
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Profile backup paths cannot contain links or reparse points')


def _allowed(name):
    if (not isinstance(name, str) or not name or len(name) > 1024
            or '\\' in name or any(ord(c) < 32 for c in name)):
        raise ValueError('Invalid profile backup path')
    parts = name.split('/')
    for part in parts:
        if (not part or part in ('.', '..') or part.endswith((' ', '.'))
                or any(c in part for c in ':<>"|?*')
                or re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part)):
            raise ValueError('Unsafe profile backup path')
    path = PurePosixPath(name)
    if (name != 'account.uid' and (len(parts) < 2 or parts[0] not in ('save', 'photos'))
            or path.suffix.casefold() in _PRIVATE_SUFFIXES or path.name.casefold() == '.env'):
        raise ValueError('Only committed save, photos and account.uid may be backed up')
    return name


def _fingerprint(path):
    _no_links(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Profile backup input must be a regular file')
    return _stat_key(info)


def _stat_key(info):
    # On Windows path.stat and fstat can report different creation/ctime values
    # for the same unchanged file. Identity, extent and modification time are
    # shared by both APIs; compare those before/after streaming on both paths
    # and the opened handle. Content is independently protected by SHA-256.
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _require_settled_commit(profile, cancel):
    """Never mistake save/ for the latest commit while runtime recovery waits.

    fs_host.c ready_scan/newest_save prefer the highest positive unsigned
    ready-N directory to save/<uid>. Backup format 1 cannot safely normalize
    that root to an account's save directory, so refuse instead of silently
    publishing older progress. Caller holds ProfileLock; a second snapshot
    repeats this check before publication. Nothing here performs recovery.
    """
    transactions = profile / 'save-tx'
    _no_links(transactions)
    if not transactions.exists():
        return
    if not transactions.is_dir():
        raise ValueError('Save transaction path must be a directory')
    with os.scandir(transactions) as entries:
        for index, entry in enumerate(entries):
            _cancel(cancel)
            if index >= MAX_FILES:
                raise ValueError('Save transaction directory exceeds backup scan limits')
            if not entry.name.startswith('ready-'):
                continue
            candidate = Path(entry.path)
            _no_links(candidate)
            match = re.fullmatch(r'ready-([0-9]+)', entry.name)
            # Refuse oversized positive numbers too: Win32 strtoul saturates
            # on overflow, so ignoring one could disagree with ready_scan.
            if match and int(match[1]) > 0 and candidate.is_dir():
                raise ValueError('The latest committed save is waiting for runtime recovery in save-tx. '
                                 'No backup or data copy was made from the older save. '
                                 'Close other programs holding save files, start and close the game '
                                 'to finish recovery, then retry.')


def _snapshot(profile, cancel):
    _require_settled_commit(profile, cancel)
    found, aliases, nodes = {}, set(), 0

    def visit(path):
        nonlocal nodes
        _cancel(cancel)
        _no_links(path)
        nodes += 1
        if nodes > MAX_FILES * 3:
            raise ValueError('Profile backup directory tree is too large')
        if path.is_dir():
            with os.scandir(path) as entries:
                for entry in entries:
                    visit(Path(entry.path))
            return
        name = path.relative_to(profile).as_posix()
        # Keys/logs are never included, even if placed inside a save directory.
        if path.suffix.casefold() in _PRIVATE_SUFFIXES or path.name.casefold() == '.env':
            return
        _allowed(name)
        if name.casefold() in aliases:
            raise ValueError('Case aliases in profile backup inputs')
        aliases.add(name.casefold())
        found[name] = _fingerprint(path)
        if len(found) > MAX_FILES or found[name][2] > MAX_FILE_BYTES:
            raise ValueError('Profile backup exceeds the file count or 16 GiB file limit')

    for name in ('account.uid', 'save', 'photos'):
        path = profile / name
        if path.exists() or path.is_symlink():
            visit(path)
    if not found:
        raise ValueError('No committed profile files to back up')
    if sum(info[2] for info in found.values()) > MAX_TOTAL_BYTES:
        raise ValueError('Profile backup exceeds the 64 GiB total limit')
    return found


def _manifest(raw):
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('Profile backup manifest is too large')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate profile backup manifest key')
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Invalid profile backup manifest') from error
    if (not isinstance(value, dict) or type(value.get('format')) is not int or value['format'] != 1
            or not isinstance(value.get('profile_id'), str)
            or not re.fullmatch('[0-9a-f]{32}', value['profile_id'])
            or not isinstance(value.get('files'), dict) or not 0 < len(value['files']) <= MAX_FILES):
        raise ValueError('Invalid profile backup manifest')
    aliases, total = set(), 0
    for name, entry in value['files'].items():
        _allowed(name)
        if name.casefold() in aliases:
            raise ValueError('Case aliases in profile backup manifest')
        aliases.add(name.casefold())
        if (not isinstance(entry, dict) or type(entry.get('size')) is not int
                or not 0 <= entry['size'] <= MAX_FILE_BYTES
                or not isinstance(entry.get('sha256'), str)
                or not re.fullmatch('[0-9a-fA-F]{64}', entry['sha256'])):
            raise ValueError('Invalid profile backup file metadata')
        total += entry['size']
    if total > MAX_TOTAL_BYTES:
        raise ValueError('Profile backup exceeds the 64 GiB total limit')
    return value


def _publish(scratch, archive):
    if os.name == 'nt':
        os.rename(scratch, archive)  # Windows rename never replaces an existing file.
    else:
        os.link(scratch, archive)  # Atomic create-if-absent on POSIX too.
        scratch.unlink()


def _retire(destination, profile_id, keep, report):
    pattern = re.compile(r'newsnap-profile-' + profile_id + r'-\d{8}T\d{12}Z-[0-9a-f]{32}\.zip')
    candidates = []
    for path in destination.glob(f'newsnap-profile-{profile_id}-*.zip'):
        if not pattern.fullmatch(path.name):
            continue
        try:
            _no_links(path)
            with _open_zip(path) as archive:
                manifest = _read_manifest(archive)
            if manifest['profile_id'] == profile_id:
                candidates.append(path)
        except (OSError, ValueError, zipfile.BadZipFile):
            continue  # Never remove an unrecognized, corrupt or linked archive.
    for path in sorted(candidates, key=lambda p: p.name, reverse=True)[keep:]:
        try:
            _no_links(path)
            path.unlink()
        except (OSError, ValueError) as error:
            report(f'Could not retire old profile backup: {error}')


def backup_profile(profile, destination, keep=3, cancel=None, report=print):
    """Stream a ZIP64 full backup. Caller holds ProfileLock; keep defaults to 3.

    Retention applies only to recognized archives for this profile, after a new
    archive is safely published. Existing source data is never changed.
    """
    if type(keep) is not int or keep < 1:
        raise ValueError('Keep must be at least one complete profile backup')
    profile, destination = Path(os.path.abspath(profile)), Path(os.path.abspath(destination))
    _no_links(profile)
    _no_links(destination)
    if destination == profile or profile in destination.parents:
        raise ValueError('Backup destination must be outside the source profile')
    _cancel(cancel)
    snapshot = _snapshot(profile, cancel)
    profile_id = hashlib.sha256(os.path.normcase(str(profile)).encode('utf-8')).hexdigest()[:32]
    destination.mkdir(parents=True, exist_ok=True)
    _no_links(destination)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive = destination / f'newsnap-profile-{profile_id}-{stamp}-{uuid.uuid4().hex}.zip'
    fd, temporary = tempfile.mkstemp(prefix='.backup-', suffix='.part', dir=destination)
    os.close(fd)
    scratch = Path(temporary)
    try:
        files = {}
        with zipfile.ZipFile(scratch, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as output:
            for name, before in sorted(snapshot.items()):
                _cancel(cancel)
                path = profile / name
                if _fingerprint(path) != before:
                    raise RuntimeError('Profile source changed while backing up')
                digest, size = hashlib.sha256(), 0
                with path.open('rb') as source, output.open(name, 'w', force_zip64=True) as target:
                    if _fingerprint(path) != before or _stat_key(os.fstat(source.fileno())) != before:
                        raise RuntimeError('Profile source changed while backing up')
                    while block := source.read(_CHUNK):
                        _cancel(cancel)
                        size += len(block)
                        if size > before[2]:
                            raise RuntimeError('Profile source changed while backing up')
                        digest.update(block)
                        target.write(block)
                    if _stat_key(os.fstat(source.fileno())) != before:
                        raise RuntimeError('Profile source changed while backing up')
                if size != before[2] or _fingerprint(path) != before:
                    raise RuntimeError('Profile source changed while backing up')
                files[name] = {'size': size, 'sha256': digest.hexdigest()}
                report(f'Profile backup: {len(files)}/{len(snapshot)} files')
            manifest = {'format': 1, 'profile_id': profile_id, 'created_utc': stamp, 'files': files}
            raw = json.dumps(manifest, separators=(',', ':')).encode('utf-8')
            _manifest(raw)
            output.writestr(MANIFEST_NAME, raw)
        _cancel(cancel)
        if _snapshot(profile, cancel) != snapshot:
            raise RuntimeError('Profile source changed while backing up')
        with scratch.open('r+b') as stream:
            os.fsync(stream.fileno())
        _publish(scratch, archive)
        _retire(destination, profile_id, keep, report)
        return archive
    finally:
        scratch.unlink(missing_ok=True)


def _open_zip(path):
    # Bound central-directory allocation before ZipFile parses its entries.
    with path.open('rb') as stream:
        end = zipfile._EndRecData(stream)
    if (end is None or end[zipfile._ECD_ENTRIES_TOTAL] > MAX_FILES + 1
            or end[zipfile._ECD_SIZE] > (MAX_FILES + 1) * 4096):
        raise ValueError('Profile backup ZIP directory exceeds limits')
    return zipfile.ZipFile(path, 'r', allowZip64=True)


def _read_manifest(archive):
    infos = archive.infolist()
    if not 1 < len(infos) <= MAX_FILES + 1:
        raise ValueError('Profile backup ZIP file count exceeds limits')
    names = set()
    for info in infos:
        name = info.filename
        if (name.casefold() in names or info.orig_filename != name or info.is_dir() or info.flag_bits & 1
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                or info.external_attr & 0x400
                or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            raise ValueError('Unsafe or duplicate profile backup ZIP entry')
        names.add(name.casefold())
        if name != MANIFEST_NAME:
            _allowed(name)
    try:
        info = archive.getinfo(MANIFEST_NAME)
    except KeyError as error:
        raise ValueError('Profile backup manifest is missing') from error
    if info.file_size > MAX_MANIFEST_BYTES:
        raise ValueError('Profile backup manifest is too large')
    manifest = _manifest(archive.read(info))
    if {info.filename for info in infos} != set(manifest['files']) | {MANIFEST_NAME}:
        raise ValueError('Profile backup inventory differs from its manifest')
    for name, expected in manifest['files'].items():
        if archive.getinfo(name).file_size != expected['size']:
            raise ValueError('Profile backup size differs from its manifest')
    return manifest


def _remove_restore(stage, parent):
    if (stage.parent != parent or not stage.name.startswith('.restore-')
            or not stage.resolve().is_relative_to(parent.resolve())):
        raise ValueError('Unsafe profile restore cleanup boundary')
    _no_links(stage)
    shutil.rmtree(stage)


def restore_profile(archive, destination, cancel=None):
    """Verify and restore to a NEW profile directory; never overwrite live data."""
    archive, destination = Path(os.path.abspath(archive)), Path(os.path.abspath(destination))
    _no_links(archive)
    _no_links(destination)
    if destination.exists():
        raise FileExistsError('Restore requires a new, nonexistent profile directory')
    _cancel(cancel)
    with _open_zip(archive) as source:
        manifest = _read_manifest(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _no_links(destination.parent)
        stage = Path(tempfile.mkdtemp(prefix='.restore-', dir=destination.parent))
        try:
            for name, expected in manifest['files'].items():
                _cancel(cancel)
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                digest, size = hashlib.sha256(), 0
                with source.open(name) as incoming, target.open('xb') as output:
                    while block := incoming.read(_CHUNK):
                        _cancel(cancel)
                        size += len(block)
                        if size > expected['size']:
                            raise ValueError('Restored profile file exceeds its declared size')
                        digest.update(block)
                        output.write(block)
                if size != expected['size'] or digest.hexdigest() != expected['sha256'].lower():
                    raise ValueError('Profile backup checksum verification failed')
            _cancel(cancel)
            _no_links(destination)
            if destination.exists():
                raise FileExistsError('Restore destination appeared during extraction')
            stage.rename(destination)
            return destination
        finally:
            if stage.exists():
                _remove_restore(stage, destination.parent)
