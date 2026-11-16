import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from newsnap import verified_files as V


def aged(path, data=None, seconds=120):
    """Write data (if given) and put the file's time in the past, as a file verified some time ago has."""
    path = Path(path)
    if data is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    moment = time.time_ns() - seconds * 10 ** 9
    os.utime(path, ns=(moment, moment))
    return path


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Receipts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.store = self.folder / 'meta' / V.STORE
        self.file = aged(self.folder / 'data.bin', b'first content')

    def test_unchanged_file_is_answered_without_reading_it(self):
        receipts = V.VerifiedFiles(self.store)
        self.assertEqual(receipts.digest(self.file), sha(b'first content'))
        self.assertEqual((receipts.hashed, receipts.reused), (1, 0))
        self.assertTrue(receipts.save())
        again = V.VerifiedFiles(self.store)
        with patch('builtins.open', side_effect=AssertionError('the file must not be opened')):
            self.assertEqual(again.digest(self.file), sha(b'first content'))
        self.assertEqual((again.hashed, again.reused), (0, 1))
        self.assertFalse(again.save())   # nothing changed: the store is not rewritten

    def test_same_size_with_another_time_is_read_again(self):
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(self.file)
        aged(self.file, b'OTHER content', seconds=60)   # same length, another modification time
        self.assertEqual(receipts.digest(self.file), sha(b'OTHER content'))
        self.assertEqual(receipts.hashed, 2)
        self.assertEqual(receipts.digest(self.file), sha(b'OTHER content'))
        self.assertEqual(receipts.hashed, 2)

    def test_truncated_or_grown_file_is_read_again(self):
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(self.file)
        moment = self.file.stat().st_mtime_ns
        self.file.write_bytes(b'first')
        os.utime(self.file, ns=(moment, moment))   # the time put back: the size still differs
        self.assertEqual(receipts.digest(self.file), sha(b'first'))
        self.assertEqual(receipts.hashed, 2)

    def test_replaced_file_with_the_same_size_and_time_is_noticed_by_its_file_id(self):
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(self.file)
        if not receipts.entries[V.key_of(self.file)]['ino']:
            self.skipTest('this file system gives no file id')
        moment = self.file.stat().st_mtime_ns
        other = self.folder / 'other.bin'
        other.write_bytes(b'OTHER content')
        os.utime(other, ns=(moment, moment))
        keep = self.folder / 'keep.bin'
        self.file.rename(keep)                      # the old file id stays in use, so the new file gets another
        other.rename(self.file)
        self.assertEqual(receipts.digest(self.file), sha(b'OTHER content'))
        self.assertEqual(receipts.hashed, 2)

    def test_known_limit_same_file_rewritten_in_place_with_time_restored(self):
        """Documented limit: same file id, size and time. Only a full check reads the new content."""
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(self.file)
        moment = self.file.stat().st_mtime_ns
        with self.file.open('r+b') as stream:
            stream.write(b'FIRST')
        os.utime(self.file, ns=(moment, moment))
        self.assertEqual(receipts.digest(self.file), sha(b'first content'))             # not noticed
        self.assertEqual(receipts.digest(self.file, full=True), sha(b'FIRST content'))   # the full check does
        self.assertEqual(receipts.digest(self.file), sha(b'FIRST content'))              # and renews the receipt

    def test_large_file_changed_at_either_end_with_time_restored_is_noticed(self):
        with patch.object(V, 'EDGE_MINIMUM', 64), patch.object(V, 'EDGE_BYTES', 16):
            data = bytearray(os.urandom(200))
            aged(self.file, bytes(data))
            receipts = V.VerifiedFiles(self.store)
            receipts.digest(self.file)
            self.assertIsNotNone(receipts.entries[V.key_of(self.file)]['edges'])
            moment = self.file.stat().st_mtime_ns
            for position in (3, 190):
                data[position] ^= 0xFF
                with self.file.open('r+b') as stream:
                    stream.write(bytes(data))
                os.utime(self.file, ns=(moment, moment))
                self.assertEqual(receipts.digest(self.file), sha(bytes(data)), position)
            self.assertEqual(receipts.hashed, 3)
            data[100] ^= 0xFF                      # the middle: the documented limit
            with self.file.open('r+b') as stream:
                stream.write(bytes(data))
            os.utime(self.file, ns=(moment, moment))
            self.assertNotEqual(receipts.digest(self.file), sha(bytes(data)))
            self.assertEqual(receipts.digest(self.file, full=True), sha(bytes(data)))

    def test_file_written_just_before_its_receipt_is_read_again(self):
        fresh = self.folder / 'fresh.bin'
        fresh.write_bytes(b'just written')
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(fresh)
        self.assertIsNone(receipts.known(fresh))   # a write in the same clock tick would look the same
        fresh.write_bytes(b'just WRITTEN')
        self.assertEqual(receipts.digest(fresh), sha(b'just WRITTEN'))

    def test_full_always_reads_and_missing_file_raises(self):
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(self.file)
        receipts.digest(self.file, full=True)
        self.assertEqual(receipts.hashed, 2)
        with self.assertRaises(FileNotFoundError):
            receipts.digest(self.folder / 'absent.bin')
        self.file.unlink()
        self.assertIsNone(receipts.known(self.file))
        with self.assertRaises(FileNotFoundError):
            receipts.digest(self.file)

    def test_cancel_stops_the_read_and_leaves_no_receipt(self):
        receipts = V.VerifiedFiles(self.store)

        def stop():
            raise RuntimeError('stopped')
        with self.assertRaises(RuntimeError):
            receipts.digest(self.file, stop)
        self.assertEqual(receipts.entries, {})

    def test_missing_corrupt_or_foreign_store_means_hashing(self):
        self.store.parent.mkdir()
        for content in (b'', b'not json', b'[]', b'{"format": 99, "files": {}}',
                        json.dumps({'format': 1, 'files': {V.key_of(self.file): {'size': 'x'}}}).encode(),
                        json.dumps({'format': 1, 'files': {V.key_of(self.file): {
                            'size': 13, 'mtime_ns': self.file.stat().st_mtime_ns, 'sha256': 'zz'}}}).encode()):
            self.store.write_bytes(content)
            receipts = V.VerifiedFiles(self.store)
            self.assertEqual(receipts.entries, {}, content)
            self.assertEqual(receipts.digest(self.file), sha(b'first content'))
            self.assertEqual(receipts.hashed, 1)

    def test_oversized_store_is_ignored(self):
        self.store.parent.mkdir()
        with patch.object(V, 'MAX_STORE_BYTES', 8):
            self.store.write_text(json.dumps({'format': 1, 'files': {}}))
            self.assertEqual(V.VerifiedFiles(self.store).entries, {})

    def test_store_is_bounded_and_keeps_the_newest(self):
        receipts = V.VerifiedFiles(self.store, limit=3)
        for number in range(6):
            path = aged(self.folder / f'{number}.bin', bytes([number]))
            receipts.digest(path)
            receipts.entries[V.key_of(path)]['at'] = 1000 + number
        receipts.save()
        kept = V.VerifiedFiles(self.store, limit=3).entries
        self.assertEqual(sorted(Path(name).name for name in kept), ['3.bin', '4.bin', '5.bin'])

    def test_store_is_written_atomically_and_unwritable_store_is_harmless(self):
        receipts = V.VerifiedFiles(self.store)
        receipts.digest(self.file)
        with patch.object(V.os, 'replace', side_effect=PermissionError('in use')):
            self.assertFalse(receipts.save())
        self.assertFalse(self.store.exists())
        self.assertEqual(list(self.store.parent.iterdir()), [])   # no temporary file left
        self.assertTrue(receipts.save())
        self.assertEqual(json.loads(self.store.read_text())['format'], 1)
        self.assertEqual([p.name for p in self.store.parent.iterdir()], [V.STORE])

    def test_memory_only_store_writes_nothing(self):
        receipts = V.VerifiedFiles()
        receipts.digest(self.file)
        self.assertFalse(receipts.save())
        self.assertEqual(receipts.digest(self.file), sha(b'first content'))
        self.assertEqual(receipts.reused, 1)

    def test_receipt_follows_a_renamed_file_only_with_its_file_id(self):
        receipts = V.VerifiedFiles()
        receipts.digest(self.file)
        if not receipts.entries[V.key_of(self.file)]['ino']:
            self.skipTest('this file system gives no file id')
        target = self.folder / 'moved.bin'
        self.file.rename(target)
        self.assertTrue(receipts.moved(self.file, target))
        self.assertEqual(receipts.known(target), sha(b'first content'))
        self.assertNotIn(V.key_of(self.file), receipts.entries)
        # another file put at the destination does not inherit a receipt
        other = aged(self.folder / 'other.bin', b'first content')
        receipts.digest(other)
        target.write_bytes(b'something else')
        self.assertFalse(receipts.moved(other, target))
        self.assertIsNone(receipts.known(target))

    def test_receipts_follow_a_renamed_folder(self):
        source = self.folder / 'stage'
        files = [aged(source / 'a.bin', b'a'), aged(source / 'sub/b.bin', b'b')]
        receipts = V.VerifiedFiles()
        for path in files:
            receipts.digest(path)
        if not all(entry['ino'] for entry in receipts.entries.values()):
            self.skipTest('this file system gives no file id')
        target = self.folder / 'final'
        source.rename(target)
        aged(target / 'sub/b.bin', b'B', seconds=60)   # changed after the move: its receipt does not follow
        moved = receipts.moved_folder(source, target)
        self.assertEqual(list(moved), [V.key_of(target / 'a.bin')])
        after = V.VerifiedFiles()
        after.entries = moved
        self.assertEqual(after.known(target / 'a.bin'), sha(b'a'))

    def test_forget_under_only_drops_that_folder(self):
        receipts = V.VerifiedFiles()
        inside, beside = aged(self.folder / 'kit/a', b'a'), aged(self.folder / 'kit-2/a', b'a')
        receipts.digest(inside)
        receipts.digest(beside)
        receipts.forget_under(self.folder / 'kit')
        self.assertEqual(list(receipts.entries), [V.key_of(beside)])


if __name__ == '__main__':
    unittest.main()
