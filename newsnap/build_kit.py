"""Acquire the public build kit matching the installed launcher, never owner data."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from urllib.parse import quote
import zipfile

from . import updater
from .maintenance import _cancel, _json, digest, verify_build_kit
from .version import VERSION

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


def _verify(kit, root, revision, cancel_event):
    updater._no_links(kit)
    manifest = _json(kit / 'build-kit.json')
    files = _inventory(manifest, revision)
    observed = set()
    expanded = 0
    for path in kit.rglob('*'):
        _cancel(cancel_event)
        updater._no_links(path)
        name = path.relative_to(kit).as_posix()
        updater._relative(name)
        if path.is_file():
            observed.add(name)
            expanded += path.stat().st_size
            if len(observed) > MAX_FILES + 1 or expanded > MAX_EXPANDED_BYTES:
                raise updater.UpdateError('Cached build kit exceeds its size limit')
        elif not path.is_dir():
            raise updater.UpdateError('Build kit contains a special file')
    if observed != set(files) | {'build-kit.json'}:
        raise updater.UpdateError('Build kit files differ from the exact inventory')
    verify_build_kit(kit, root, cancel_event)
    return kit


def _release(root, revision, tag):
    metadata = updater._read_json(updater.REPO_URL + '/releases/tags/' + quote(tag, safe=''))
    if (not isinstance(metadata, dict) or metadata.get('tag_name') != tag
            or metadata.get('draft') is not False or metadata.get('prerelease') is not False):
        raise updater.UpdateError('Matching stable build-kit release is unavailable')
    target = metadata.get('target_commitish')
    if isinstance(target, str) and re.fullmatch('[0-9a-fA-F]{40}', target) and target.lower() != revision:
        raise updater.UpdateError('Release revision differs from the installed launcher')
    assets = metadata.get('assets')
    name = f'NewSnapBuildKit-{VERSION}-windows-{revision[:8]}.zip'
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


def ensure_build_kit(root, progress=None, cancel_event=None):
    """Return an exactly verified offline cache, or acquire this installed release.

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
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f'{VERSION}-{revision}'
    if target.exists():
        progress('Verificando las herramientas guardadas…')
        return _verify(target, root, revision, cancel_event)
    progress('Buscando las herramientas de esta versión…')
    name, urls = _release(root, revision, tag)
    _cancel(cancel_event)
    scratch = Path(tempfile.mkdtemp(prefix='.build-kit-', dir=cache))
    try:
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
        candidate = scratch / 'kit'
        _extract(archive, candidate, revision, cancel_event)
        _verify(candidate, root, revision, cancel_event)
        _cancel(cancel_event)
        # Concurrent callers may already have published a verified generation.
        if target.exists():
            return _verify(target, root, revision, cancel_event)
        candidate.rename(target)
        return target
    except updater.DownloadCancelled as error:
        # Keep maintenance's public cancellation type without an updater import
        # dependency on maintenance (which also imports build/runtime modules).
        from .maintenance import MaintenanceCancelled
        raise MaintenanceCancelled('Reconstrucción cancelada; se conserva el runtime anterior.') from error
    finally:
        shutil.rmtree(scratch)
