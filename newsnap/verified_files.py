"""Receipts of files this PC already hashed: «is this still the file we verified?» without reading it again.

A receipt is kept per absolute path with what the file looked like when its SHA-256 was computed:

    size, mtime_ns          always
    dev, ino                the volume serial and file id, when the system gives them (0 otherwise)
    edges                   for files of EDGE_MINIMUM bytes or more, the SHA-256 of their first and last EDGE_BYTES
    sha256                  the digest that was computed
    at                      when the read began

A receipt taken less than RACY_SECONDS after the file was last written is not used: another write inside the same
clock tick would leave the same time on the file. Such a file is read again at its next check, which renews the
receipt (the rule git applies to its index).

`VerifiedFiles.digest(path)` returns the stored digest when all of that still matches and reads the whole file
otherwise (then it stores the new receipt). `full=True` always reads the whole file: the player's explicit
«verificar», and every place that trusts a file for the first time, use it.

Limits, stated plainly. This answers «unchanged since we hashed it» from metadata, as the launcher's Home receipt
already did (newsnap/home_state.py). A file whose content was replaced while its size, modification time and (when
recorded) file id were all restored on purpose is not noticed, unless the change touches the first or last mebibyte
of a large file. Silent corruption of the disk under an unchanged file is not noticed either: the full check finds
both. The receipts live beside the files they describe, so whoever can rewrite them can rewrite the files too; they
are a convenience of the player's own PC, never evidence for a file that arrives from somewhere else.

The store is a JSON file written atomically; a missing, oversized or damaged store just means hashing again, and a
store that cannot be written is ignored.
"""
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path

STORE = 'newsnap-verified-files.json'
FORMAT = 1
LIMIT = 512                    # receipts kept by default (the game data and its runtime are a few dozen files)
MAX_STORE_BYTES = 32 << 20
EDGE_BYTES = 1 << 20
EDGE_MINIMUM = 32 << 20        # smaller files are cheap to read whole when their metadata changes
BLOCK = 4 << 20
RACY_SECONDS = 3               # covers the coarsest file time in use (FAT: 2 s)
_HEX = re.compile('[0-9a-f]{64}')


def key_of(path):
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _look(path):
    """What can be read about a file without opening it."""
    value = os.stat(path)
    return {'size': value.st_size, 'mtime_ns': value.st_mtime_ns,
            'dev': int(getattr(value, 'st_dev', 0) or 0), 'ino': int(getattr(value, 'st_ino', 0) or 0)}


def edges(path, size=None):
    """SHA-256 of the first and last EDGE_BYTES of a large file; None for the others."""
    size = os.stat(path).st_size if size is None else size
    if size < EDGE_MINIMUM:
        return None
    value = hashlib.sha256()
    with open(path, 'rb') as stream:
        value.update(stream.read(EDGE_BYTES))
        stream.seek(size - EDGE_BYTES)
        value.update(stream.read(EDGE_BYTES))
    return value.hexdigest()


def _same_file(entry, seen):
    """The recorded metadata against the current one. File ids count only when both sides have them."""
    if entry['size'] != seen['size'] or entry['mtime_ns'] != seen['mtime_ns']:
        return False
    if entry.get('at', 0) * 1e9 - entry['mtime_ns'] < RACY_SECONDS * 1e9:
        return False
    if entry.get('ino') and seen['ino'] and (entry['ino'] != seen['ino'] or entry.get('dev', 0) != seen['dev']):
        return False
    return True


def _valid(entry):
    return (isinstance(entry, dict) and type(entry.get('size')) is int and type(entry.get('mtime_ns')) is int
            and isinstance(entry.get('sha256'), str) and bool(_HEX.fullmatch(entry['sha256']))
            and type(entry.get('dev', 0)) is int and type(entry.get('ino', 0)) is int
            and (entry.get('edges') is None or isinstance(entry['edges'], str) and bool(_HEX.fullmatch(entry['edges'])))
            and isinstance(entry.get('at', 0), (int, float)))


class VerifiedFiles:
    """Receipts in one store file. store=None keeps them in memory only (one operation)."""

    def __init__(self, store=None, limit=LIMIT):
        self.store = Path(store) if store is not None else None
        self.limit = limit
        self.entries = {}
        self.changed = False
        self.hashed = 0            # files read whole through this object (for tests and measurements)
        self.reused = 0            # digests answered from a receipt
        self._load()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()

    def _load(self):
        if self.store is None:
            return
        try:
            with self.store.open('rb') as stream:
                raw = stream.read(MAX_STORE_BYTES + 1)
            if len(raw) > MAX_STORE_BYTES:
                return
            value = json.loads(raw.decode('utf-8'))
            files = value.get('files') if isinstance(value, dict) and value.get('format') == FORMAT else None
            if isinstance(files, dict):
                self.entries = {name: entry for name, entry in files.items()
                                if isinstance(name, str) and _valid(entry)}
        except (OSError, ValueError, TypeError, AttributeError):
            self.entries = {}

    def save(self):
        """Best effort: a receipt that cannot be written costs a later hash, nothing else."""
        if self.store is None or not self.changed:
            return False
        if len(self.entries) > self.limit:
            newest = sorted(self.entries.items(), key=lambda item: item[1].get('at', 0), reverse=True)
            self.entries = dict(newest[:self.limit])
        temporary = None
        try:
            self.store.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix='.verified-files-', suffix='.tmp', dir=self.store.parent)
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump({'format': FORMAT, 'files': self.entries}, stream, separators=(',', ':'))
            os.replace(temporary, self.store)
            self.changed = False
            return True
        except OSError:
            return False
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def known(self, path, seen=None):
        """The stored digest when the file still looks like the one that was hashed, else None. Never reads it whole."""
        entry = self.entries.get(key_of(path))
        if entry is None:
            return None
        try:
            seen = seen or _look(path)
            if not _same_file(entry, seen):
                return None
            if entry.get('edges') is not None or seen['size'] >= EDGE_MINIMUM:
                if entry.get('edges') is None or edges(path, seen['size']) != entry['edges']:
                    return None
        except OSError:
            return None
        return entry['sha256']

    def record(self, path, sha256, seen=None, at=None):
        """Store a digest the caller computed from the file as it is now (seen, at: its metadata and the time
        from before the read)."""
        seen = seen or _look(path)
        self.entries[key_of(path)] = dict(seen, sha256=sha256, edges=edges(path, seen['size']),
                                          at=time.time() if at is None else at)
        self.changed = True

    def forget(self, path):
        if self.entries.pop(key_of(path), None) is not None:
            self.changed = True

    def forget_under(self, folder):
        prefix = key_of(folder) + os.sep
        for name in [name for name in self.entries if name.startswith(prefix)]:
            del self.entries[name]
            self.changed = True

    def moved(self, source, target):
        """After renaming source to target: the receipt follows the file when it provably is the same file.

        That needs the file id (same volume, same id, same size and time); without one the receipt is dropped and
        the next check reads the file.
        """
        entry = self.entries.pop(key_of(source), None)
        if entry is None:
            return False
        self.changed = True
        try:
            seen = _look(target)
        except OSError:
            return False
        if not entry.get('ino') or not seen['ino'] or not _same_file(dict(entry, at=float('inf')), seen):
            return False
        self.entries[key_of(target)] = entry
        return True

    def moved_folder(self, source, target):
        """After renaming the folder source to target: {key: receipt} of the files that provably are the same."""
        prefix, base, found = key_of(source) + os.sep, key_of(target) + os.sep, {}
        for name, entry in self.entries.items():
            if name.startswith(prefix) and entry.get('ino'):
                try:
                    seen = _look(base + name[len(prefix):])
                except OSError:
                    continue
                if seen['ino'] and _same_file(dict(entry, at=float('inf')), seen):
                    found[base + name[len(prefix):]] = entry
        return found

    def digest(self, path, cancel=None, *, full=False):
        """SHA-256 of path: from its receipt when unchanged, else (or with full=True) by reading it whole.

        cancel: called between blocks; it raises to stop.
        """
        if not full:
            stored = self.known(path)
            if stored is not None:
                self.reused += 1
                return stored
        before, started = _look(path), time.time()
        value = hashlib.sha256()
        with open(path, 'rb') as stream:
            while block := stream.read(BLOCK):
                if cancel is not None:
                    cancel()
                value.update(block)
        result = value.hexdigest()
        self.hashed += 1
        try:
            # A file that changed while it was read gets no receipt: the next check reads it again.
            if _look(path) == before:
                self.record(path, result, before, started)
            else:
                self.forget(path)
        except OSError:
            self.forget(path)
        return result
