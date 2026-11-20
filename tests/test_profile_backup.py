import hashlib
import json
import stat
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile


class ProfileBackupTests(unittest.TestCase):
    def test_pending_durable_commit_never_silently_backs_up_old_save(self):
        previous = self.backup()
        ready = self.profile / 'save-tx/ready-0000000012'
        ready.mkdir(parents=True)
        (ready / 'game.sav').write_bytes(b'newest committed progress')
        before = {path.relative_to(self.profile): path.read_bytes()
                  for path in self.profile.rglob('*') if path.is_file()}
        with self.assertRaisesRegex(ValueError, 'committed save.*recovery'):
            self.backup()
        self.assertEqual(list(self.backups.glob('*.zip')), [previous])
        self.assertFalse(list(self.backups.glob('.backup-*')))
        self.assertEqual(before, {path.relative_to(self.profile): path.read_bytes()
                                 for path in self.profile.rglob('*') if path.is_file()})

    def test_uncommitted_staging_does_not_hide_valid_committed_backup(self):
        for name in ('save-tx/work/game.sav', 'save-tx/new/game.sav'):
            path = self.profile / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'uncommitted changes')
        archive = self.backup()
        with zipfile.ZipFile(archive) as source:
            self.assertEqual(source.read('save/user/game.sav'), b'committed progress')
            self.assertFalse(any(name.startswith('save-tx/') for name in source.namelist()))

    def test_pending_commit_appearing_during_streaming_prevents_publication(self):
        original = self.mod._snapshot
        snapshots = 0
        def capture(*args):
            nonlocal snapshots
            snapshots += 1
            if snapshots == 2:
                pending = self.profile / 'save-tx/ready-0000000001'
                pending.mkdir(parents=True)
                (pending/'game.sav').write_bytes(b'latest')
            return original(*args)
        with patch.object(self.mod, '_snapshot', side_effect=capture):
            with self.assertRaisesRegex(ValueError, 'committed save.*recovery'):
                self.backup()
        self.assertFalse(list(self.backups.glob('*.zip')))
        self.assertFalse(list(self.backups.glob('.backup-*')))

    def test_readonly_data_clone_also_refuses_stale_profile(self):
        from newsnap.data_location import clone_readonly_data
        source = self.root/'GameData'
        recipe = {'exefs_sha256': {}}
        for name in ('main', 'sdk'):
            module = source/'exefs'/name
            module.parent.mkdir(parents=True, exist_ok=True)
            module.write_bytes(name.encode())
            recipe['exefs_sha256'][name] = hashlib.sha256(name.encode()).hexdigest()
        image = source/'romfs/romfs.bin'; image.parent.mkdir()
        image.write_bytes(b'fixture image')
        (source/'launcher.json').write_text(json.dumps({'profile': str(self.profile)}))
        ready = self.profile/'save-tx/ready-0000000001'
        ready.mkdir(parents=True); (ready/'game.sav').write_bytes(b'latest')
        destination = self.root/'copied-data'
        with self.assertRaisesRegex(ValueError, 'committed save.*recovery'):
            clone_readonly_data(source, destination, recipe, report=lambda _: None)
        self.assertFalse(destination.exists())
        self.assertFalse(list(self.root.glob('.data-copy-*')))
        self.assertEqual((ready/'game.sav').read_bytes(), b'latest')
        self.assertEqual((self.profile/'save/user/game.sav').read_bytes(), b'committed progress')

    def setUp(self):
        from newsnap import profile_backup
        self.mod = profile_backup
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / 'profile'
        self.profile.mkdir()
        (self.profile / 'account.uid').write_bytes(b'account')
        (self.profile / 'save/user').mkdir(parents=True)
        (self.profile / 'save/user/game.sav').write_bytes(b'committed progress')
        self.backups = self.root / 'synced'

    def backup(self, **kwargs):
        return self.mod.backup_profile(self.profile, self.backups, report=lambda _: None, **kwargs)

    def repack(self, archive, change):
        with zipfile.ZipFile(archive) as source:
            entries = {name: source.read(name) for name in source.namelist()}
        change(entries)
        damaged = self.root / 'changed.zip'
        with zipfile.ZipFile(damaged, 'w') as output:
            for name, data in entries.items():
                output.writestr(name, data)
        return damaged

    def test_roundtrip_only_committed_data_and_identity(self):
        for name in ('photos/picture.jpg', 'save-tx/incomplete', 'logs/run.log',
                     'prod.keys', 'cache/image', 'save/user/private.keys'):
            path = self.profile / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        archive = self.backup()
        with zipfile.ZipFile(archive) as source:
            names = set(source.namelist())
            self.assertEqual(names, {'account.uid', 'save/user/game.sav', 'photos/picture.jpg',
                                     self.mod.MANIFEST_NAME})
            manifest = json.loads(source.read(self.mod.MANIFEST_NAME))
            self.assertEqual(manifest['files']['account.uid']['sha256'], hashlib.sha256(b'account').hexdigest())
        target = self.root / 'restored'
        self.assertEqual(self.mod.restore_profile(archive, target), target)
        self.assertEqual((target / 'save/user/game.sav').read_bytes(), b'committed progress')
        self.assertEqual((target / 'account.uid').read_bytes(), b'account')

    def test_file_larger_than_launcher_cloud_limit_roundtrips(self):
        large = self.profile / 'save/user/large.bin'
        with large.open('wb') as stream:
            stream.truncate(65 * 1024 * 1024 + 19)
        archive = self.backup()
        target = self.mod.restore_profile(archive, self.root / 'large-restored')
        self.assertEqual((target / 'save/user/large.bin').stat().st_size, large.stat().st_size)
        with large.open('rb') as left, (target / 'save/user/large.bin').open('rb') as right:
            self.assertEqual(hashlib.file_digest(left, 'sha256').digest(),
                             hashlib.file_digest(right, 'sha256').digest())

    def test_destination_inside_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            self.mod.backup_profile(self.profile, self.profile / 'backups')
        self.assertFalse((self.profile / 'backups').exists())

    def test_cancel_leaves_previous_archive_and_no_scratch(self):
        previous = self.backup()
        cancel = threading.Event()
        def report(_):
            cancel.set()
        with self.assertRaises(RuntimeError):
            self.mod.backup_profile(self.profile, self.backups, report=report, cancel=cancel)
        self.assertTrue(previous.is_file())
        self.assertEqual(list(self.backups.glob('*.zip')), [previous])
        self.assertFalse(list(self.backups.glob('*.part')))

    def test_changed_source_cannot_publish(self):
        changed = False
        def report(_):
            nonlocal changed
            if not changed:
                (self.profile / 'account.uid').write_bytes(b'changed account')
                changed = True
        with self.assertRaisesRegex(RuntimeError, 'changed'):
            self.mod.backup_profile(self.profile, self.backups, report=report)
        self.assertFalse(list(self.backups.glob('*.zip')))
        self.assertFalse(list(self.backups.glob('*.part')))

    def test_publish_failure_keeps_old_backups(self):
        previous = self.backup()
        with patch.object(self.mod, '_publish', side_effect=OSError('injected publication failure')):
            with self.assertRaises(OSError):
                self.backup(keep=1)
        self.assertTrue(previous.exists())
        self.assertFalse(list(self.backups.glob('*.part')))

    def test_retention_only_matches_same_profile(self):
        unrelated = self.backups / 'unrelated.zip'
        self.backups.mkdir()
        unrelated.write_bytes(b'not our archive')
        other = self.root / 'other'
        other.mkdir()
        (other / 'account.uid').write_bytes(b'other account')
        other_backup = self.mod.backup_profile(other, self.backups, report=lambda _: None)
        for _ in range(4):
            latest = self.backup(keep=3)
        self.assertTrue(unrelated.exists())
        self.assertTrue(other_backup.exists())
        self.assertTrue(latest.exists())
        self.assertEqual(len(list(self.backups.glob('*.zip'))), 5)

    def test_restore_never_overwrites_existing_destination(self):
        archive = self.backup()
        target = self.root / 'restored'
        target.mkdir()
        (target / 'owner').write_bytes(b'original')
        with self.assertRaises((ValueError, FileExistsError)):
            self.mod.restore_profile(archive, target)
        self.assertEqual((target / 'owner').read_bytes(), b'original')

    def test_hash_corruption_has_no_partial_restore(self):
        archive = self.repack(self.backup(), lambda entries: entries.update({'account.uid': b'tampered'}))
        target = self.root / 'restored'
        with self.assertRaises((RuntimeError, ValueError)):
            self.mod.restore_profile(archive, target)
        self.assertFalse(target.exists())
        self.assertFalse(list(self.root.glob('.restore-*')))

    def test_restore_rejects_traversal_private_and_case_alias_entries(self):
        original = self.backup()
        for name in ('../escaped', 'save/../../escaped', 'prod.keys', 'Save/user/game.sav'):
            with self.subTest(name=name):
                archive = self.repack(original, lambda entries: entries.update({name: b'bad'}))
                target = self.root / 'restored'
                with self.assertRaises((RuntimeError, ValueError)):
                    self.mod.restore_profile(archive, target)
                self.assertFalse(target.exists())

    def test_duplicate_zip_entry_is_rejected(self):
        archive = self.backup()
        import warnings
        with warnings.catch_warnings(), zipfile.ZipFile(archive, 'a') as output:
            warnings.simplefilter('ignore', UserWarning)
            output.writestr('account.uid', b'account')
        with self.assertRaises((RuntimeError, ValueError)):
            self.mod.restore_profile(archive, self.root / 'restored')

    def test_zip_symlink_entry_is_rejected(self):
        archive = self.backup()
        malicious = self.root / 'linked.zip'
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(malicious, 'w') as output:
            for name in source.namelist():
                info = zipfile.ZipInfo(name)
                if name == 'account.uid':
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                output.writestr(info, source.read(name))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.mod.restore_profile(malicious, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())

    def test_nul_truncated_zip_name_cannot_alias_allowed_manifest_name(self):
        def change(entries):
            entries['save/user/gameXXXX'] = entries.pop('save/user/game.sav')
            manifest = json.loads(entries[self.mod.MANIFEST_NAME])
            manifest['files']['save/user/game'] = manifest['files'].pop('save/user/game.sav')
            entries[self.mod.MANIFEST_NAME] = json.dumps(manifest).encode()
        archive = self.repack(self.backup(), change)
        archive.write_bytes(archive.read_bytes().replace(b'save/user/gameXXXX', b'save/user/game\x00XXX'))
        with self.assertRaises(ValueError):
            self.mod.restore_profile(archive, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())

    def test_source_symlink_is_rejected_without_copying(self):
        path = self.profile / 'photos/link.jpg'
        path.parent.mkdir()
        try:
            path.symlink_to(self.profile / 'account.uid')
        except OSError:
            self.skipTest('symlink privileges unavailable')
        with self.assertRaises(ValueError):
            self.backup()
        self.assertFalse(self.backups.exists())

    def test_manifest_limits_are_checked_before_extraction(self):
        original = self.backup()
        def change(entries):
            manifest = json.loads(entries[self.mod.MANIFEST_NAME])
            manifest['files']['account.uid']['size'] = 17 * 1024 ** 3
            entries[self.mod.MANIFEST_NAME] = json.dumps(manifest).encode()
        archive = self.repack(original, change)
        with self.assertRaises((RuntimeError, ValueError)):
            self.mod.restore_profile(archive, self.root / 'restored')

    def test_restore_cancel_removes_staging(self):
        archive = self.backup()
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(RuntimeError):
            self.mod.restore_profile(archive, self.root / 'restored', cancel=cancel)
        self.assertFalse((self.root / 'restored').exists())
        self.assertFalse(list(self.root.glob('.restore-*')))

    def test_windows_ctime_only_stat_fstat_difference_does_not_reject_backup(self):
        real_fstat = self.mod.os.fstat
        def ctime_difference(fd):
            info = real_fstat(fd)
            return SimpleNamespace(st_dev=info.st_dev, st_ino=info.st_ino,
                                   st_size=info.st_size, st_mtime_ns=info.st_mtime_ns,
                                   st_ctime_ns=info.st_ctime_ns + 987654321)
        with patch.object(self.mod.os, 'fstat', side_effect=ctime_difference):
            archive = self.backup()
        target = self.mod.restore_profile(archive, self.root / 'ctime-restored')
        self.assertEqual((target / 'account.uid').read_bytes(), b'account')

    def test_changed_handle_identity_extent_or_mtime_still_rejects_backup(self):
        real_fstat = self.mod.os.fstat
        for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns'):
            with self.subTest(field=field):
                def changed(fd):
                    info = real_fstat(fd)
                    values = {name: getattr(info, name) for name in
                              ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')}
                    values[field] += 1
                    return SimpleNamespace(**values)
                with patch.object(self.mod.os, 'fstat', side_effect=changed):
                    with self.assertRaisesRegex(RuntimeError, 'changed'):
                        self.backup()
                self.assertFalse(list(self.backups.glob('*.zip')))
                self.assertFalse(list(self.backups.glob('*.part')))

    def test_two_hundred_unchanged_files_backup_restore_three_times(self):
        for number in range(200):
            (self.profile / 'save/user' / f'fixture-{number:03d}.bin').write_bytes(
                f'unchanged synthetic fixture {number}'.encode() * 5)
        for attempt in range(3):
            archive = self.backup()
            target = self.mod.restore_profile(archive, self.root / f'stress-restored-{attempt}')
            for number in range(200):
                self.assertEqual((target / 'save/user' / f'fixture-{number:03d}.bin').read_bytes(),
                                 f'unchanged synthetic fixture {number}'.encode() * 5)
        self.assertEqual(len(list(self.backups.glob('*.zip'))), 3)


if __name__ == '__main__':
    unittest.main()
