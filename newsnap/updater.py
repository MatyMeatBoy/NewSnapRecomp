"""Stable GitHub launcher updates; owner game data never participates.

Transport integrity trusts HTTPS to the canonical repository and its checksum asset.
The checksum is not a detached signature. Call apply_update only after launcher/game
processes have stopped (the caller owns shutdown and any restart supervisor).
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile
from . import github_auth

REPO_URL = 'https://api.github.com/repos/MatyMeatBoy/NewSnapRecomp'
LATEST_URL = REPO_URL + '/releases/latest'
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_EXPANDED_BYTES = 2 * 1024 * 1024 * 1024
MAX_FILES = 20000
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
_HOSTS = {'api.github.com', 'github.com', 'objects.githubusercontent.com',
          'release-assets.githubusercontent.com', 'github-releases.githubusercontent.com'}
_PROTECTED = {'gamedata', 'newsnapgamedata', 'profile', 'settings', 'logs',
              'saves', 'savegames', 'config', 'configs'}
_FORBIDDEN_SUFFIXES = {'.nsp', '.nsz', '.xci', '.nca', '.keys', '.nso', '.npdm', '.drp', '.nushdb', '.bin', '.sav', '.srm', '.log'}
_PROTECTED_NAMES = {'newsnap.exe', 'main', 'sdk', 'settings.json', 'config.json', 'launcher-settings.json'}
_ASSET_PREFIX = 'https://github.com/MatyMeatBoy/NewSnapRecomp/releases/download/'


class UpdateError(RuntimeError):
    """An update could not be verified or installed safely."""


@dataclass(frozen=True)
class Release:
    tag_name: str
    version: str
    archive_name: str
    archive_url: str
    checksum_url: str
    source_revision: str | None = None


@dataclass(frozen=True)
class UpdateResult:
    version: str
    source_revision: str
    installed_files: tuple[str, ...]
    preserved_files: tuple[str, ...]


def _validate_url(url):
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise UpdateError('Invalid update URL port') from exc
    if (parsed.scheme != 'https' or parsed.hostname not in _HOSTS or
            parsed.username or parsed.password or port not in (None, 443) or parsed.fragment):
        raise UpdateError('Update downloads require an approved GitHub HTTPS host')
    return url


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header('Authorization')
        return redirected


def _canonical_api(url):
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.hostname == 'api.github.com' and
            (parsed.path == urlsplit(REPO_URL).path or parsed.path.startswith(urlsplit(REPO_URL).path + '/')))


def _asset_url(url):
    if not isinstance(url, str):
        raise UpdateError('Release asset has no download URL')
    _validate_url(url)
    if not (url.startswith(_ASSET_PREFIX) or re.fullmatch(re.escape(REPO_URL) + r'/releases/assets/[0-9]+', url)):
        raise UpdateError('Release assets must belong to the canonical repository')
    return url


class DownloadCancelled(UpdateError):
    """The caller cancelled a bounded download between transport operations."""


def _download(url, path, limit, *, cancel_event=None):
    def check_cancel():
        if cancel_event is not None and cancel_event.is_set():
            raise DownloadCancelled('Download cancelled')

    check_cancel()
    _validate_url(url)
    api = _canonical_api(url)
    accept = ('application/vnd.github+json' if api and '/releases/assets/' not in urlsplit(url).path
              else 'application/octet-stream')
    request = Request(url, headers={'User-Agent': 'NewSnapRecomp-Updater', 'Accept': accept})
    if api:
        try:
            token = github_auth.get_token()
        except (OSError, ValueError) as exc:
            raise UpdateError('Cannot load GitHub credentials; configure repository access') from exc
        if token:
            # urllib omits unredirected headers when following an asset redirect.
            request.add_unredirected_header('Authorization', 'Bearer ' + token)
    try:
        check_cancel()
        with build_opener(_SafeRedirect()).open(request, timeout=30) as response:
            check_cancel()
            _validate_url(response.geturl())
            length = response.headers.get('Content-Length')
            if length is not None and (not length.isdigit() or int(length) > limit):
                raise UpdateError('Update download exceeds the permitted size')
            size = 0
            with Path(path).open('xb') as output:
                while True:
                    check_cancel()
                    chunk = response.read(1024 * 1024)
                    check_cancel()
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > limit:
                        raise UpdateError('Update download exceeds the permitted size')
                    check_cancel()
                    output.write(chunk)
                check_cancel()
            if length is not None and size != int(length):
                raise UpdateError('Update download was truncated')
    except HTTPError:
        raise
    except (OSError, URLError) as exc:
        raise UpdateError(f'Update download failed: {exc}') from exc


def _read_json(url):
    with tempfile.TemporaryDirectory(prefix='newsnap-release-') as temp:
        path = Path(temp) / 'release.json'
        _download(url, path, 2 * 1024 * 1024)
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError) as exc:
            raise UpdateError('GitHub returned invalid release metadata') from exc


def check_stable():
    """Return the latest stable Windows release, or None if an accessible repo has none.

    Does not compare installed versions: requesting the same version supports repair.
    """
    try:
        data = _read_json(LATEST_URL)
    except HTTPError as exc:
        if exc.code == 404:
            try:
                repository = _read_json(REPO_URL)
            except HTTPError as access_error:
                if access_error.code in (401, 403, 404):
                    raise UpdateError('GitHub repository access is unavailable; configure a token with read access to NewSnapRecomp') from access_error
                raise UpdateError(f'GitHub repository lookup failed (HTTP {access_error.code})') from access_error
            if not isinstance(repository, dict) or repository.get('full_name', '').casefold() != 'matymeatboy/newsnaprecomp':
                raise UpdateError('Cannot confirm access to the canonical GitHub repository')
            return None
        if exc.code in (401, 403):
            raise UpdateError(f'GitHub access failed (HTTP {exc.code}); check repository token access and API rate limits') from exc
        raise UpdateError(f'GitHub release lookup failed (HTTP {exc.code})') from exc
    if not isinstance(data, dict):
        raise UpdateError('Invalid release metadata')
    if data.get('draft') is not False or data.get('prerelease') is not False:
        return None
    tag = data.get('tag_name')
    if not isinstance(tag, str) or not tag:
        raise UpdateError('Release has no version tag')
    assets = data.get('assets', [])
    if not isinstance(assets, list):
        raise UpdateError('Invalid release asset inventory')
    candidates = [a for a in assets if isinstance(a, dict) and isinstance(a.get('name'), str)
                  and not a['name'].lower().startswith('newsnapbuildkit-')
                  and a['name'].lower().endswith('.zip') and 'windows' in a['name'].lower()
                  and 'arm64' not in a['name'].lower()]
    if len(candidates) != 1:
        raise UpdateError('Stable release must provide exactly one Windows launcher ZIP')
    archive = candidates[0]
    checksums = [a for a in assets if isinstance(a, dict) and a.get('name') == archive['name'] + '.sha256']
    if len(checksums) != 1:
        raise UpdateError('Stable release has no unique matching SHA-256 asset')
    urls = []
    for asset in (archive, checksums[0]):
        browser_url = asset.get('browser_download_url')
        if not isinstance(browser_url, str) or not browser_url.startswith(_ASSET_PREFIX):
            raise UpdateError('Release assets must belong to the canonical repository')
        _asset_url(browser_url)
        urls.append(_asset_url(asset.get('url') or browser_url))
    revision = data.get('target_commitish')
    if not isinstance(revision, str) or not re.fullmatch('[0-9a-fA-F]{40}', revision):
        revision = None  # A branch name is not a source revision; the manifest supplies it.
    return Release(tag, tag.removeprefix('v'), archive['name'], urls[0], urls[1], revision)


def _relative(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        raise UpdateError('Invalid archive path')
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise UpdateError('Unsafe archive path')
    for part in path.parts:
        if (any(c in part for c in ':<>"|?*') or any(ord(c) < 32 for c in part) or part.endswith((' ', '.')) or
                re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part)):
            raise UpdateError('Unsafe Windows archive path')
    return path


def _public(name):
    path = _relative(name)
    if (any(p.casefold() == 'profiles' for p in path.parts) and
            not re.fullmatch(r'profiles/snap-[0-9]+\.[0-9]+\.[0-9]+\.json', name)):
        raise UpdateError('Only curated Snap specification JSONs may use the public profiles folder')
    if (any(p.casefold() in _PROTECTED for p in path.parts) or path.name.casefold() in _PROTECTED_NAMES or
            path.suffix.casefold() in _FORBIDDEN_SUFFIXES or name.casefold() == 'manifest.json'):
        raise UpdateError(f'Owner data or private content is forbidden in an update: {name}')
    return path


def _no_links(path):
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise UpdateError(f'Update paths cannot contain links or junctions: {part}')


def _manifest(raw):
    if len(raw) > MAX_MANIFEST_BYTES:
        raise UpdateError('Manifest is too large')
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise UpdateError('Invalid update manifest') from exc
    if (not isinstance(data, dict) or data.get('contains_game_data') is not False or
            not isinstance(data.get('version'), str) or not data['version'] or
            not isinstance(data.get('source_revision'), str) or
            not re.fullmatch('[0-9a-fA-F]{40}', data['source_revision']) or
            not isinstance(data.get('files'), dict) or not data['files'] or len(data['files']) > MAX_FILES):
        raise UpdateError('Manifest does not describe a public launcher release')
    seen = set(); total = 0
    for name, entry in data['files'].items():
        _public(name)
        if name.casefold() in seen:
            raise UpdateError('Case-insensitive duplicate in manifest')
        seen.add(name.casefold())
        if (not isinstance(entry, dict) or type(entry.get('size')) is not int or entry['size'] < 0 or
                not isinstance(entry.get('sha256'), str) or not re.fullmatch('[0-9a-fA-F]{64}', entry['sha256'])):
            raise UpdateError('Invalid manifest file size or checksum')
        total += entry['size']
    if total > MAX_EXPANDED_BYTES:
        raise UpdateError('Expanded update exceeds the permitted size')
    return data


def _digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def stage_update(release, staging_dir):
    """Download and validate into a new private directory; return its release folder."""
    if len(_relative(release.archive_name).parts) != 1:
        raise UpdateError('Invalid release archive filename')
    for url in (release.archive_url, release.checksum_url):
        _asset_url(url)
    scratch = Path(staging_dir).absolute()
    _no_links(scratch)
    try:
        scratch.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise UpdateError('Staging requires a new empty directory') from exc
    try:
        archive_path = scratch / 'download.zip'
        checksum_path = scratch / 'download.sha256'
        _download(release.checksum_url, checksum_path, 4096)
        checksum = checksum_path.read_text(encoding='ascii').strip().split()
        if (len(checksum) not in (1, 2) or not re.fullmatch('[0-9a-fA-F]{64}', checksum[0]) or
                (len(checksum) == 2 and checksum[1].lstrip('*') != release.archive_name)):
            raise UpdateError('Invalid update SHA-256 sidecar')
        _download(release.archive_url, archive_path, MAX_ARCHIVE_BYTES)
        if _digest(archive_path) != checksum[0].lower():
            raise UpdateError('Update ZIP checksum does not match')
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_FILES * 2:
                raise UpdateError('Invalid archive member count')
            inventory = {}; top = None; expanded = 0; names = set()
            for member in members:
                name = member.filename.rstrip('/') if member.is_dir() else member.filename
                path = _relative(name)
                if len(path.parts) < (1 if member.is_dir() else 2):
                    raise UpdateError('Archive needs one top-level release folder')
                if top is None:
                    top = path.parts[0]
                if path.parts[0] != top or name.casefold() in names:
                    raise UpdateError('Archive has multiple roots or duplicate paths')
                if any(part.casefold() in _PROTECTED for part in path.parts[1:]):
                    raise UpdateError('Owner data directories are forbidden in an update')
                names.add(name.casefold())
                mode = member.external_attr >> 16
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR) or member.external_attr & 0x400:
                    raise UpdateError('Archive links and special files are forbidden')
                if member.flag_bits & 1:
                    raise UpdateError('Encrypted update archives are forbidden')
                expanded += member.file_size
                if expanded > MAX_EXPANDED_BYTES + MAX_MANIFEST_BYTES:
                    raise UpdateError('Expanded update exceeds the permitted size')
                if not member.is_dir():
                    inventory['/'.join(path.parts[1:])] = member
            if 'MANIFEST.json' not in inventory or inventory['MANIFEST.json'].file_size > MAX_MANIFEST_BYTES:
                raise UpdateError('Archive has no bounded MANIFEST.json')
            manifest = _manifest(archive.read(inventory['MANIFEST.json']))
            if manifest['version'] != release.version:
                raise UpdateError('Release version and manifest disagree')
            if release.source_revision and manifest['source_revision'].lower() != release.source_revision.lower():
                raise UpdateError('Release source revision and manifest disagree')
            if set(inventory) != set(manifest['files']) | {'MANIFEST.json'}:
                raise UpdateError('Archive files do not match the manifest inventory')
            destination = scratch / 'payload' / top
            for name, member in inventory.items():
                if name != 'MANIFEST.json' and member.file_size != manifest['files'][name]['size']:
                    raise UpdateError('Archive size differs from manifest')
                target = destination.joinpath(*PurePosixPath(name).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                if name != 'MANIFEST.json' and _digest(target) != manifest['files'][name]['sha256'].lower():
                    raise UpdateError('Extracted update checksum does not match manifest')
        archive_path.unlink(); checksum_path.unlink()
        return destination
    except Exception as exc:
        shutil.rmtree(scratch)
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError(f'Update staging failed: {exc}') from exc


def apply_update(staged_folder, install_root):
    """Replace manifest-owned public files transactionally, preserving existing INIs.

    Revalidates staged bytes. Old files absent from the new manifest are retained;
    no uninstallation or owner-data migration is performed. Call from an external
    supervisor when updating a running frozen launcher.
    """
    staged = Path(staged_folder).absolute(); install = Path(install_root).absolute()
    _no_links(staged); _no_links(install)
    staged_resolved = staged.resolve(); install_resolved = install.resolve()
    if staged_resolved == install_resolved or staged_resolved in install_resolved.parents or install_resolved in staged_resolved.parents:
        raise UpdateError('Staging and installation must not overlap')
    try:
        manifest_path = staged / 'MANIFEST.json'
        _no_links(manifest_path)
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise UpdateError('Manifest is too large')
        raw = manifest_path.read_bytes(); manifest = _manifest(raw)
        for name, entry in manifest['files'].items():
            source = staged.joinpath(*PurePosixPath(name).parts)
            target = install.joinpath(*PurePosixPath(name).parts)
            _no_links(source); _no_links(target)
            if not source.is_file() or source.stat().st_size != entry['size'] or _digest(source) != entry['sha256'].lower():
                raise UpdateError(f'Staged file failed verification: {name}')
            if target.exists() and not target.is_file():
                raise UpdateError(f'Installation destination is not a file: {name}')
        _no_links(install / 'MANIFEST.json')
        if (install / 'MANIFEST.json').exists() and not (install / 'MANIFEST.json').is_file():
            raise UpdateError('Installed manifest destination is not a file')
        install.mkdir(parents=True, exist_ok=True)
        transaction = Path(tempfile.mkdtemp(prefix='.newsnap-update-', dir=install.parent))
        journal = []; installed = []; preserved = []; created_dirs = []
        try:
            # Prepare and verify every replacement before touching installed bytes.
            prepared = []
            for index, name in enumerate([*manifest['files'], 'MANIFEST.json']):
                target = install.joinpath(*PurePosixPath(name).parts)
                if target.exists() and target.suffix.lower() == '.ini':
                    preserved.append(name); continue
                incoming = transaction / f'{index}.new'
                shutil.copy2(staged.joinpath(*PurePosixPath(name).parts), incoming)
                if name != 'MANIFEST.json' and _digest(incoming) != manifest['files'][name]['sha256'].lower():
                    raise UpdateError('Prepared update changed during copying')
                if name == 'MANIFEST.json' and incoming.read_bytes() != raw:
                    raise UpdateError('Staged manifest changed during copying')
                prepared.append((name, incoming, target, transaction / f'{index}.backup'))
            for name, incoming, target, backup in prepared:
                _no_links(target)
                missing = []; parent = target.parent
                while not parent.exists():
                    missing.append(parent); parent = parent.parent
                for directory in reversed(missing):
                    directory.mkdir(); created_dirs.append(directory)
                existed = target.exists()
                if existed:
                    os.replace(target, backup)
                journal.append((target, backup, existed))
                os.replace(incoming, target)
                installed.append(name)
        except Exception as exc:
            rollback_errors = []
            for target, backup, existed in reversed(journal):
                try:
                    if existed:
                        os.replace(backup, target)
                    else:
                        target.unlink(missing_ok=True)
                except OSError as failure:
                    rollback_errors.append(str(failure))
            for directory in reversed(created_dirs):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            if rollback_errors:
                raise UpdateError(f'Update failed; recovery backups retained at {transaction}: {rollback_errors}') from exc
            shutil.rmtree(transaction, ignore_errors=True)
            raise UpdateError(f'Update failed and was rolled back: {exc}') from exc
        shutil.rmtree(transaction, ignore_errors=True)
        return UpdateResult(manifest['version'], manifest['source_revision'], tuple(installed), tuple(preserved))
    except UpdateError:
        raise
    except OSError as exc:
        raise UpdateError(f'Cannot install update: {exc}') from exc
