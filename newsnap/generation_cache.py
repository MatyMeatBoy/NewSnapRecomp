"""Bounded local snapshots of verified owner-derived C/H/JSON, never native code.

Cache failure is a miss. Original imports are verified by the caller on every
build; a hit additionally requires the same owner path, inputs and exact recipe.
Snapshots are copied and reverified, so future generation cannot mutate a cache
entry through a shared inode. Only the last two published recipes (and at most
1 GiB) are retained. Nothing in this module uploads private generated code.
"""
from contextlib import contextmanager
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import time

from .provenance import RECEIPT, verify_generation

ROOT_MARKER = '.newsnap-generated-cache.json'
ROOT_IDENTITY = {'format': 1, 'kind': 'NewSnapRecomp private generated cache'}
ENTRY_KIND = 'NewSnapRecomp private generated snapshot'
HEX = re.compile(r'[a-f0-9]{64}')
FAILURES = (OSError, ValueError, TypeError, KeyError, RecursionError)


class GenerationCacheCancelled(RuntimeError):
    pass


def _cancel(event):
    if event is not None and event.is_set():
        raise GenerationCacheCancelled('Reconstrucción cancelada; la caché anterior se conserva.')


def _key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def owner_identity(directory, manifest, romfs_sha256):
    return {'path': os.path.normcase(str(Path(directory).resolve())),
            'exefs': {f['name']: f['sha256'] for f in manifest['files']},
            'romfs_sha256': romfs_sha256}


def current_generator_environment():
    packages = {}
    for name in ('numpy', 'capstone', 'lz4'):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = 'unknown: not installed'
    return {'python': {'implementation': sys.implementation.name,
                       'cache_tag': sys.implementation.cache_tag or 'unknown',
                       'version': list(sys.version_info[:3])}, 'packages': packages}


def _valid_environment(environment):
    if not isinstance(environment, dict):
        return False
    python, packages = environment.get('python'), environment.get('packages')
    return (isinstance(python, dict) and isinstance(packages, dict) and
            all(isinstance(python.get(k), str) and python[k] for k in ('implementation', 'cache_tag')) and
            isinstance(python.get('version'), list) and len(python['version']) == 3 and
            all(type(n) is int and n >= 0 for n in python['version']) and
            all(isinstance(packages.get(k), str) and packages[k] for k in ('numpy', 'capstone', 'lz4')))


def _entry_key(owner, recipe_hash, environment):
    return _key({'owner': owner, 'recipe_sha256': recipe_hash, 'generator_environment': environment})


def _valid_owner(owner):
    return (isinstance(owner, dict) and isinstance(owner.get('path'), str) and
            Path(owner['path']).is_absolute() and isinstance(owner.get('exefs'), dict) and
            bool(owner['exefs']) and
            all(isinstance(x, str) and HEX.fullmatch(x) for x in owner['exefs'].values()) and
            isinstance(owner.get('romfs_sha256'), str) and bool(HEX.fullmatch(owner['romfs_sha256'])))


def _check_identity(owner, recipe):
    if not _valid_owner(owner) or owner['exefs'] != recipe.get('exefs'):
        raise ValueError('Owner inputs do not match the generation recipe')


def _read(path):
    with path.open('rb') as stream:
        raw = stream.read((8 << 20) + 1)
    if len(raw) > 8 << 20:
        raise ValueError('Oversized private cache metadata')
    return json.loads(raw)


def _write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def _no_links(path):
    """Check raw ancestors before resolving, including Windows reparse points."""
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Private cache links/reparse points are not allowed')


def _tree(folder):
    _no_links(folder)
    base = folder.resolve()
    pending, files = [folder], []
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for item in entries:
                path = Path(item.path)
                info = item.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                    raise ValueError('Private cache tree contains a link/reparse point')
                if not path.resolve().is_relative_to(base):
                    raise ValueError('Private cache path leaves its container')
                if stat.S_ISDIR(info.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    files.append(path)
                else:
                    raise ValueError('Unsupported private cache file type')
    return sorted(files)


def _generated_files(folder, recipe):
    files = _tree(folder)
    if any(p.suffix not in ('.c', '.h', '.json') for p in files):
        raise ValueError('Private generation cache accepts only C/H/JSON and its receipt')
    receipt = _read(folder / RECEIPT)
    actual = {p.relative_to(folder).as_posix() for p in files} - {RECEIPT}
    if not isinstance(receipt, dict) or actual != set(receipt.get('outputs', {})):
        raise ValueError('Generated file set differs from the complete output inventory')
    verify_generation(folder, recipe)
    return files


def _copy_file(source, destination, cancel_event):
    with source.open('rb') as original, destination.open('xb') as target:
        for block in iter(lambda: original.read(1 << 20), b''):
            _cancel(cancel_event)
            target.write(block)
        target.flush()
        os.fsync(target.fileno())


def _copy_generated(source, destination, recipe, cancel_event):
    files = _generated_files(source, recipe)
    destination.mkdir()
    for path in files:
        _cancel(cancel_event)
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        _copy_file(path, target, cancel_event)
    _cancel(cancel_event)
    _generated_files(destination, recipe)


@contextmanager
def _lock(root):
    path = root / 'cache.lock'
    _no_links(path)
    with path.open('a+b') as stream:
        stream.seek(0, os.SEEK_END)
        if not stream.tell():
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Closing releases the OS lock after success, failure or process death.
        yield


class GenerationCache:
    def __init__(self, root=None, *, max_entries=2, max_bytes=1 << 30, environment=None,
                 generator_environment=None):
        environment = os.environ if environment is None else environment
        local = environment.get('LOCALAPPDATA')
        if root is None and local:
            root = Path(local) / 'NewSnapRecomp/generated-cache'
        self.root = Path(root).absolute() if root is not None else None
        self.enabled = self.root is not None and environment.get('NEWSNAP_GENERATION_CACHE') != '0'
        self.max_entries, self.max_bytes = max_entries, max_bytes
        self.generator_environment = generator_environment
        self.status = 'miss' if self.enabled else 'disabled'
        if self.enabled and self.generator_environment is None:
            try:
                self.generator_environment = current_generator_environment()
            except (OSError, ValueError):
                # An optional cache must not turn missing/unreadable dependency
                # metadata into a failure of a fresh owner build.
                self.enabled = False
                self.status = 'unavailable'

    def _prepare(self):
        if not self.enabled:
            return False
        if type(self.max_entries) is not int or self.max_entries < 1 or type(self.max_bytes) is not int or self.max_bytes < 1:
            raise ValueError('Invalid generation-cache budget')
        if not _valid_environment(self.generator_environment):
            raise ValueError('Invalid generator environment identity')
        _no_links(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        marker = self.root / ROOT_MARKER
        if not marker.exists():
            if any(self.root.iterdir()):
                raise ValueError('Refusing to claim a nonempty unmarked cache directory')
            _write(marker, ROOT_IDENTITY)
        if _read(marker) != ROOT_IDENTITY:
            raise ValueError('Unrecognized generation-cache root')
        return True

    def _inside(self, path):
        _no_links(path)
        if path.parent != self.root or not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('Cache cleanup target leaves the dedicated cache root')

    def _metadata(self, entry):
        self._inside(entry)
        if not HEX.fullmatch(entry.name):
            raise ValueError('Unrecognized private cache entry name')
        _tree(entry)
        metadata = _read(entry / 'entry.json')
        owner = metadata['owner']
        recipe_hash = metadata['recipe_sha256']
        environment = metadata.get('generator_environment')
        if (metadata.get('format') != 1 or metadata.get('kind') != ENTRY_KIND or
                not _valid_owner(owner) or
                not isinstance(recipe_hash, str) or not HEX.fullmatch(recipe_hash) or
                not _valid_environment(environment) or _entry_key(owner, recipe_hash, environment) != entry.name or
                type(metadata.get('created_ns')) is not int or metadata['created_ns'] < 0):
            raise ValueError('Invalid private-cache ownership metadata')
        return metadata

    def _remove_owned(self, entry):
        self._metadata(entry)
        # Both the resolved target and every tree member were checked immediately
        # before recursive removal; imports/profiles are never cleanup targets.
        shutil.rmtree(entry)

    def _remove_stage(self, stage):
        self._inside(stage)
        if not stage.name.startswith('.publish-') or _read(stage / 'stage.json') != ROOT_IDENTITY:
            raise ValueError('Unrecognized private cache staging directory')
        _tree(stage)
        shutil.rmtree(stage)

    def _clean_stages(self):
        # The OS lock proves another publisher cannot still own these stages.
        for stage in self.root.iterdir():
            if stage.name.startswith('.publish-'):
                self._remove_stage(stage)

    def _entries(self):
        result = []
        for entry in self.root.iterdir():
            if not HEX.fullmatch(entry.name):
                continue
            # If an entry-shaped path is not safely owned, stop publication rather
            # than deleting it or exceeding the budget around an unknown object.
            metadata = self._metadata(entry)
            result.append((entry, metadata, sum(p.stat().st_size for p in _tree(entry))))
        return result

    def _prune(self, incoming_name=None, incoming_size=0):
        entries = sorted((value for value in self._entries() if value[0].name != incoming_name),
                         key=lambda value: (value[1]['created_ns'], value[0].name))
        total = sum(value[2] for value in entries) + incoming_size
        reserved = int(incoming_name is not None)
        while len(entries) + reserved > self.max_entries or total > self.max_bytes:
            entry, _, size = entries.pop(0)
            self._remove_owned(entry)
            total -= size

    def restore(self, owner, recipe, destination, cancel_event=None):
        destination, stage = Path(destination).absolute(), None
        try:
            _cancel(cancel_event)
            _check_identity(owner, recipe)
            if not self._prepare() or destination.exists():
                return False
            _no_links(destination)
            with _lock(self.root):
                self._clean_stages()
                entry = self.root / _entry_key(owner, _key(recipe), self.generator_environment)
                if not entry.exists():
                    return False
                metadata = self._metadata(entry)
                if (metadata['owner'] != owner or metadata['recipe_sha256'] != _key(recipe) or
                        metadata['generator_environment'] != self.generator_environment):
                    return False
                if sum(p.stat().st_size for p in _tree(entry)) > self.max_bytes:
                    return False
                destination.parent.mkdir(parents=True, exist_ok=True)
                stage = Path(tempfile.mkdtemp(prefix='.generated-cache-', dir=destination.parent))
                _copy_generated(entry / 'generated', stage / 'generated', recipe, cancel_event)
                _cancel(cancel_event)
                if destination.exists():
                    return False
                (stage / 'generated').replace(destination)
                self.status = 'hit'
                return True
        except FAILURES:
            self.status = 'unavailable'
            return False
        finally:
            if stage is not None and stage.exists():
                # This is our freshly allocated destination-side scratch folder,
                # never the destination itself or any caller-owned directory.
                try:
                    _no_links(stage)
                    _tree(stage)
                    shutil.rmtree(stage)
                except FAILURES:
                    pass

    def publish(self, owner, recipe, generated, cancel_event=None):
        generated, stage = Path(generated), None
        try:
            _cancel(cancel_event)
            _check_identity(owner, recipe)
            if not self._prepare():
                return False
            files = _generated_files(generated, recipe)
            if sum(p.stat().st_size for p in files) > self.max_bytes:
                return False
            with _lock(self.root):
                self._clean_stages()
                self._entries()  # Preflight eviction ownership before publishing.
                entry = self.root / _entry_key(owner, _key(recipe), self.generator_environment)
                if entry.exists():
                    self._metadata(entry)
                    try:
                        _generated_files(entry / 'generated', recipe)
                        self._prune()
                        return True
                    except (ValueError, OSError):
                        pass  # Replace a corrupt, but safely owned, entry below.
                stage = Path(tempfile.mkdtemp(prefix='.publish-', dir=self.root))
                _write(stage / 'stage.json', ROOT_IDENTITY)
                _copy_generated(generated, stage / 'generated', recipe, cancel_event)
                _write(stage / 'entry.json', {'format': 1, 'kind': ENTRY_KIND, 'owner': owner,
                                             'recipe_sha256': _key(recipe), 'created_ns': time.time_ns(),
                                             'generator_environment': self.generator_environment})
                size = sum(p.stat().st_size for p in _tree(stage))
                if size > self.max_bytes:
                    return False
                _cancel(cancel_event)
                # Reserve the final budget before publication. A read-only old
                # entry cannot leave an extra published entry above the limit.
                self._prune(entry.name, size)
                if entry.exists():
                    self._remove_owned(entry)
                stage.replace(entry)  # Readers only observe a complete snapshot.
                stage = None
                self.status = 'stored'
                return True
        except FAILURES:
            self.status = 'unavailable'
            return False
        finally:
            if stage is not None and stage.exists():
                try:
                    self._remove_stage(stage)
                except FAILURES:
                    pass
