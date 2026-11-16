"""Acquire the public build kit matching the installed launcher, never owner data."""
import hashlib
from contextlib import contextmanager
import errno
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import time
from urllib.parse import quote
from urllib.error import HTTPError
import zipfile

from . import updater
from .maintenance import _cancel, _json, digest, verify_build_kit
from .version import VERSION
from .paths import data_dir
from .launcher_settings import load_profile
from .verified_files import VerifiedFiles

MAX_ARCHIVE_BYTES = 2 << 30
MAX_EXPANDED_BYTES = 6 << 30
MAX_FILES = 50000
MAX_MANIFEST_BYTES = 8 << 20


def _identity(root):
    installed = _json(Path(root) / 'MANIFEST.json')
    revision = installed.get('source_revision')
    if (installed.get('version') != VERSION or not isinstance(revision, str)
            or not re.fullmatch('[0-9a-f]{40}', revision)):
        raise updater.UpdateError('Installed launcher has no matching version/source revision')
    tag = installed.get('tag_name', 'v' + VERSION)
    if tag not in (VERSION, 'v' + VERSION):
        raise updater.UpdateError('Installed release tag differs from its version')
    return revision, tag


def _cache_root():
    base = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.cache'))
    return base / 'NewSnapRecomp/build-kits'


def _inventory(manifest, revision):
    if (not isinstance(manifest, dict) or manifest.get('contains_game_data') is not False
            or manifest.get('source_revision') != revision):
        raise updater.UpdateError('Build kit source revision or public-content declaration differs')
    files = manifest.get('files')
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        raise updater.UpdateError('Invalid build kit inventory')
    seen = {'build-kit.json'}
    for name, checksum in files.items():
        updater._relative(name)
        if name.casefold() in seen or not isinstance(checksum, str) or not re.fullmatch('[0-9a-f]{64}', checksum):
            raise updater.UpdateError('Duplicate path or invalid build kit checksum')
        seen.add(name.casefold())
    return files


def kit_receipts(kit):
    """Receipts (verified_files) of a kit of the launcher's own cache, kept beside it; None for any other kit."""
    kit = Path(kit).absolute()
    try:
        cache = _cache_root().absolute()
    except (OSError, RuntimeError):
        return None
    if kit.parent != cache or not re.fullmatch(r'[0-9A-Za-z.+-]+-[0-9a-f]{40}', kit.name):
        return None
    return VerifiedFiles(cache / f'.verified-{kit.name}.json', limit=MAX_FILES + 16)


def _entries(folder, prefix=''):
    """(relative name, file information) of everything under folder, from the directory listings.

    A link or junction is refused where it is found, as updater._no_links does. That function also walks up from
    every path to the drive root (three system calls per level, for each of the thousands of files of a kit);
    here the kit folder and what is above it are checked once by the caller, and what is below it as it is listed.
    """
    with os.scandir(folder) as found:
        entries = sorted(found, key=lambda entry: entry.name)
    for entry in entries:
        info = entry.stat(follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise updater.UpdateError(f'Update paths cannot contain links or junctions: {entry.path}')
        yield prefix + entry.name, info
        if stat.S_ISDIR(info.st_mode):
            yield from _entries(entry.path, prefix + entry.name + '/')


def _verify(kit, root, revision, cancel_event, receipts=None):
    """The exact inventory, then maintenance.verify_build_kit. receipts: see verify_build_kit; None reads it all."""
    updater._no_links(kit)
    manifest = _json(kit / 'build-kit.json')
    files = _inventory(manifest, revision)
    observed = set()
    expanded = 0
    for name, info in _entries(kit):
        _cancel(cancel_event)
        updater._relative(name)
        if stat.S_ISREG(info.st_mode):
            observed.add(name)
            expanded += info.st_size
            if len(observed) > MAX_FILES + 1 or expanded > MAX_EXPANDED_BYTES:
                raise updater.UpdateError('Cached build kit exceeds its size limit')
        elif not stat.S_ISDIR(info.st_mode):
            raise updater.UpdateError('Build kit contains a special file')
    if observed != set(files) | {'build-kit.json'}:
        raise updater.UpdateError('Build kit files differ from the exact inventory')
    verify_build_kit(kit, root, cancel_event, receipts)
    return kit


def _release(root, revision, tag):
    try:
        metadata = updater._read_json(updater.REPO_URL + '/releases/tags/' + quote(tag, safe=''))
    except HTTPError as error:
        if error.code != 404:
            raise
        raise updater.UpdateError(
            'No se puede acceder al kit de esta versión en GitHub. Usa el paquete Windows completo '
            'con sus herramientas incluidas o configura el acceso al repositorio.') from error
    # The installed manifest/tag is already bound to this launcher in _identity.
    # Fetching its exact kit must also work after an explicit alpha/dev install;
    # this does not discover newer prereleases or change automatic update policy.
    installed_prerelease = bool(re.fullmatch(
        r'\d+\.\d+\.\d+-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*(?:\+[0-9A-Za-z.-]+)?', VERSION))
    if (not isinstance(metadata, dict) or metadata.get('tag_name') != tag
            or metadata.get('draft') is not False
            or not (metadata.get('prerelease') is False
                    or installed_prerelease and metadata.get('prerelease') is True)):
        raise updater.UpdateError('Matching published build-kit release is unavailable')
    target = metadata.get('target_commitish')
    if isinstance(target, str) and re.fullmatch('[0-9a-fA-F]{40}', target) and target.lower() != revision:
        raise updater.UpdateError('Release revision differs from the installed launcher')
    assets = metadata.get('assets')
    # Legacy launcher clients select one ZIP containing "windows". Keep the
    # separate tool kit outside that selector so they can still update.
    name = f'NewSnapBuildKit-{VERSION}-{revision[:8]}.zip'
    if not isinstance(assets, list):
        raise updater.UpdateError('Release has no build-kit assets')
    urls = []
    for expected in (name, name + '.sha256'):
        matches = [a for a in assets if isinstance(a, dict) and a.get('name') == expected]
        if len(matches) != 1:
            raise updater.UpdateError('Release has no unique matching build kit and checksum')
        asset = matches[0]
        urls.append(updater._asset_url(asset.get('url') or asset.get('browser_download_url')))
    return name, urls


def _extract(archive_path, destination, revision, cancel_event):
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if not members or len(members) > MAX_FILES * 2:
            raise updater.UpdateError('Invalid build-kit member count')
        inventory, seen, top, total = {}, set(), None, 0
        for member in members:
            _cancel(cancel_event)
            name = member.filename.rstrip('/') if member.is_dir() else member.filename
            path = updater._relative(name)
            if len(path.parts) < (1 if member.is_dir() else 2):
                raise updater.UpdateError('Build kit requires one root folder')
            if top is None:
                top = path.parts[0]
            if path.parts[0] != top or name.casefold() in seen:
                raise updater.UpdateError('Multiple roots or duplicate build-kit paths')
            seen.add(name.casefold())
            mode = member.external_attr >> 16
            if (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or member.external_attr & 0x400 or member.flag_bits & 1):
                raise updater.UpdateError('Build-kit links, special or encrypted files are forbidden')
            total += member.file_size
            if total > MAX_EXPANDED_BYTES or member.file_size > MAX_EXPANDED_BYTES:
                raise updater.UpdateError('Expanded build kit exceeds its size limit')
            if not member.is_dir():
                inventory['/'.join(path.parts[1:])] = member
        entry = inventory.get('build-kit.json')
        if entry is None or entry.file_size > MAX_MANIFEST_BYTES:
            raise updater.UpdateError('Build kit has no bounded root manifest')
        manifest = json.loads(archive.read(entry))
        expected = _inventory(manifest, revision)
        if set(inventory) != set(expected) | {'build-kit.json'}:
            raise updater.UpdateError('ZIP differs from the exact build-kit inventory')
        for name, member in inventory.items():
            _cancel(cancel_event)
            target = destination.joinpath(*updater._relative(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            value = hashlib.sha256()
            size = 0
            with archive.open(member) as source, target.open('xb') as output:
                while block := source.read(1 << 20):
                    _cancel(cancel_event)
                    size += len(block)
                    if size > member.file_size:
                        raise updater.UpdateError('Build-kit extraction exceeds its declared size')
                    value.update(block)
                    output.write(block)
            if size != member.file_size or (name != 'build-kit.json' and value.hexdigest() != expected[name]):
                raise updater.UpdateError('Build-kit extracted checksum or size mismatch')


def _bundled_archive(root, revision, cancel_event):
    name = f'build-kits/NewSnapBuildKit-{VERSION}-{revision[:8]}.zip'
    archive = root / name
    updater._no_links(archive)
    metadata = _json(root / 'MANIFEST.json')
    files = metadata.get('files', {})
    pin = files.get(name) if isinstance(files, dict) else None
    if not archive.exists() and pin is None:
        return None
    if (not isinstance(pin, dict) or not isinstance(pin.get('size'), int)
            or isinstance(pin['size'], bool) or not 0 < pin['size'] <= MAX_ARCHIVE_BYTES
            or not isinstance(pin.get('sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', pin['sha256'])
            or not archive.is_file() or archive.stat().st_size != pin['size']):
        raise updater.UpdateError('El kit incluido falta o difiere del manifiesto del launcher.')
    if digest(archive, cancel_event) != pin['sha256']:
        raise updater.UpdateError('El kit incluido está dañado; extrae de nuevo el paquete completo.')
    return archive


CACHE_INTEGRITY_ERRORS = (ValueError, FileNotFoundError, updater.UpdateError)


@contextmanager
def _publication_lock(cache, revision, cancel_event):
    """Serialize final directory switches; OS releases the lock on process exit."""
    path=cache/f'.publish-{VERSION}-{revision}.lock'
    updater._no_links(path)
    with path.open('a+b') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise updater.UpdateError('Build-kit publication lock is not a regular file')
        if not stream.tell():
            stream.write(b'\0');stream.flush()
        deadline=time.monotonic()+30
        while True:
            _cancel(cancel_event)
            try:
                stream.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError as error:
                if error.errno not in (errno.EACCES,errno.EAGAIN,errno.EDEADLK):raise
                if time.monotonic()>=deadline:
                    raise updater.UpdateError('Another build-kit publication is still running') from error
                time.sleep(.05)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name=='nt':
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(stream,fcntl.LOCK_UN)


def _publish_candidate(candidate, target, root, revision, cancel_event, *, repair):
    cache=target.parent
    # Both operands are children we own, and no recursive cleanup ever touches
    # target or quarantine. Failed caches remain available for diagnosis.
    if target.name!=f'{VERSION}-{revision}' or candidate.parent.parent!=cache:
        raise updater.UpdateError('Invalid build-kit publication boundary')
    updater._no_links(target);updater._no_links(candidate)
    with _publication_lock(cache,revision,cancel_event):
        _cancel(cancel_event)
        quarantine=None
        if target.exists():
            try:
                return _verify(target,root,revision,cancel_event)
            except CACHE_INTEGRITY_ERRORS as error:
                if isinstance(error,updater.DownloadCancelled):raise
                if not repair:raise
            # Cancellation is accepted before switching; finish/restore the
            # directory transaction once the previous generation is moved.
            _cancel(cancel_event)
            quarantine=Path(tempfile.mkdtemp(prefix='.invalid-build-kit-',dir=cache))
            target.rename(quarantine/'kit')
        try:
            candidate.rename(target)
        except OSError:
            if target.exists():
                # An uncooperative/older publisher may have won the race.
                # Return only a fully verified generation, never overwrite it.
                return _verify(target,root,revision,cancel_event)
            if quarantine is not None:
                (quarantine/'kit').rename(target)
                quarantine.rmdir()
            raise
        return target


def ensure_build_kit(root, progress=None, cancel_event=None, full=False):
    """Return an exactly verified offline cache, or acquire this installed release.

    A cached kit whose files were hashed before on this PC and are unchanged since is recognised by its
    receipts (verified_files) instead of being read again; full=True reads and hashes every file. A kit that
    arrives (download or bundled archive) is always read whole before its first use.

    NEWSNAP_BUILD_KIT is an explicit developer override, also fully verified.
    Transport uses the updater's authenticated, redirect-safe GitHub download.
    Cancellation is checked during bounded downloads and each extracted chunk.
    """
    progress = progress or (lambda message: None)
    root = Path(root).resolve()
    _cancel(cancel_event)
    revision, tag = _identity(root)
    override = os.environ.get('NEWSNAP_BUILD_KIT')
    if override:
        return _verify(Path(override).absolute(), root, revision, cancel_event)
    cache = _cache_root().absolute()
    updater._no_links(cache)
    # A configured application cache may never alias owner data or installation.
    resolved = cache.resolve()
    if resolved == root or resolved.is_relative_to(root):
        raise updater.UpdateError('Build-kit cache must be outside the installation and owner data')
    target = cache / f'{VERSION}-{revision}'
    for owner in (data_dir(root).resolve(),load_profile(root).resolve()):
        if resolved==owner or resolved.is_relative_to(owner) or owner.is_relative_to(target.resolve()):
            raise updater.UpdateError('Build-kit cache must not contain or alias owner data')
    cache.mkdir(parents=True, exist_ok=True)
    updater._no_links(target)
    bundled=None
    if target.exists():
        progress('Verificando las herramientas guardadas…')
        receipts = kit_receipts(target)
        if full and receipts is not None:
            receipts.entries.clear()   # every file is read again and gets a new receipt
            receipts.changed = True
        try:
            return _verify(target, root, revision, cancel_event, receipts)
        except CACHE_INTEGRITY_ERRORS as error:
            if isinstance(error,updater.DownloadCancelled):raise
            # Never turn a cache error into an implicit network acquisition.
            # A complete exact offline bundle is required for automatic repair.
            bundled=_bundled_archive(root,revision,cancel_event)
            if bundled is None:raise
        finally:
            if receipts is not None:receipts.save()
    if bundled is None:
        bundled = _bundled_archive(root, revision, cancel_event)
    if bundled is None:
        progress('Buscando las herramientas de esta versión…')
        name, urls = _release(root, revision, tag)
    _cancel(cancel_event)
    scratch = Path(tempfile.mkdtemp(prefix='.build-kit-', dir=cache))
    try:
        archive = bundled
        if archive is None:
            sidecar, archive = scratch / 'checksum', scratch / 'archive.zip'
            updater._download(urls[1], sidecar, 4096, cancel_event=cancel_event)
            _cancel(cancel_event)
            checksum = sidecar.read_text(encoding='ascii').strip().split()
            if (len(checksum) not in (1, 2) or not re.fullmatch('[0-9a-fA-F]{64}', checksum[0])
                    or len(checksum) == 2 and checksum[1].lstrip('*') != name):
                raise updater.UpdateError('Invalid build-kit SHA-256 sidecar')
            progress('Descargando las herramientas de reconstrucción…')
            updater._download(urls[0], archive, MAX_ARCHIVE_BYTES, cancel_event=cancel_event)
            if digest(archive, cancel_event) != checksum[0].lower():
                raise updater.UpdateError('Build-kit ZIP checksum does not match')
        else:
            progress('Preparando las herramientas incluidas…')
        candidate = scratch / 'kit'
        _extract(archive, candidate, revision, cancel_event)
        # Read whole before its first use. The receipts of that read follow the files into the cache when the
        # folder is renamed (same file ids), so the rebuild that comes next does not read the kit a third time.
        receipts = VerifiedFiles(limit=MAX_FILES + 16)
        _verify(candidate, root, revision, cancel_event, receipts)
        _cancel(cancel_event)
        published = _publish_candidate(candidate,target,root,revision,cancel_event,repair=bundled is not None)
        stored = kit_receipts(published)
        if stored is not None and published == target and not candidate.exists():
            stored.entries = receipts.moved_folder(candidate, target)
            stored.changed = True
            stored.save()
        return published
    except updater.DownloadCancelled as error:
        # Keep maintenance's public cancellation type without an updater import
        # dependency on maintenance (which also imports build/runtime modules).
        from .maintenance import MaintenanceCancelled
        raise MaintenanceCancelled('Reconstrucción cancelada; se conserva el runtime anterior.') from error
    finally:
        shutil.rmtree(scratch)
