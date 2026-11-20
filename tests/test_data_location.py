import hashlib
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class DataLocationTests(unittest.TestCase):
    def setUp(self):
        from newsnap import data_location
        self.mod = data_location
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'original'
        self.source.mkdir()
        self.destination = self.root / 'writable-data'
        files = {'exefs/main': b'main', 'exefs/sdk': b'sdk', 'exefs/rtld': b'rtld',
                 'romfs/romfs.bin': b'original image', 'newsnap.ini': b'[display]\nhd_shadows=0\n',
                 'profile/account.uid': b'original account', 'profile/save/user/game.sav': b'progress',
                 'profile/photos/photo.jpg': b'photo bytes', 'profile/save-tx/work/partial': b'incomplete',
                 'profile/logs/private.log': b'log', 'newsnap.exe': b'old executable',
                 'hdshadows/map.dds': b'old mod', 'cache/pipelines': b'old cache', 'prod.keys': b'private'}
        for name, data in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.recipe = {'exefs_sha256': {name.split('/')[1]: hashlib.sha256(data).hexdigest()
                                       for name, data in files.items() if name.startswith('exefs/')},
                       'romfs_sha256': hashlib.sha256(files['romfs/romfs.bin']).hexdigest(),
                       'verified_control': {'display_version': '2.0.1', 'save_size': 1024, 'journal_size': 1024}}
        self.extractor = SimpleNamespace(index_romfs=Mock(return_value=[{'path': 'test', 'offset': 0, 'size': 1}]))

    def clone(self, **kwargs):
        with patch.object(self.mod, 'extractor', return_value=self.extractor):
            return self.mod.clone_readonly_data(self.source, self.destination, self.recipe,
                                                report=lambda _: None, **kwargs)

    def source_bytes(self):
        return {p.relative_to(self.source).as_posix(): p.read_bytes()
                for p in self.source.rglob('*') if p.is_file()}

    def test_clone_preserves_committed_profile_and_leaves_source_unchanged(self):
        before = self.source_bytes()
        result = self.clone()
        self.assertEqual(result, self.destination)
        self.assertEqual(self.source_bytes(), before)
        for name in ('exefs/main', 'exefs/sdk', 'exefs/rtld', 'romfs/romfs.bin', 'newsnap.ini',
                     'profile/account.uid', 'profile/save/user/game.sav', 'profile/photos/photo.jpg'):
            self.assertEqual((result / name).read_bytes(), before[name])
        for name in ('newsnap.exe', 'hdshadows', 'cache', 'prod.keys', 'profile/save-tx', 'profile/logs'):
            self.assertFalse((result / name).exists(), name)
        index = json.loads((result / 'romfs/index.json').read_text())
        self.assertEqual(index['romfs_sha256'], self.recipe['romfs_sha256'])
        self.extractor.index_romfs.assert_called_once()
        from newsnap.launcher_settings import load_profile
        self.assertEqual(load_profile(result), result / 'profile')

    def test_estimate_counts_only_selected_inputs_and_committed_profile(self):
        expected = sum((self.source / name).stat().st_size for name in (
            'exefs/main', 'exefs/sdk', 'exefs/rtld', 'romfs/romfs.bin', 'newsnap.ini',
            'profile/account.uid', 'profile/save/user/game.sav', 'profile/photos/photo.jpg'))
        self.assertEqual(self.mod.estimate_copy_bytes(self.source, self.recipe), expected)

    def test_existing_destination_is_never_overwritten(self):
        self.destination.mkdir()
        marker = self.destination / 'owner'
        marker.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            self.clone()
        self.assertEqual(marker.read_bytes(), b'keep')

    def test_mid_copy_cancellation_removes_owned_staging_only(self):
        cancel = threading.Event()
        original = self.mod._copy_file
        def interrupt(*args, **kwargs):
            value = original(*args, **kwargs)
            cancel.set()
            return value
        with patch.object(self.mod, '_copy_file', side_effect=interrupt):
            with self.assertRaises(RuntimeError):
                self.clone(cancel=cancel)
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob('.data-copy-*')))
        self.assertTrue((self.source / 'profile/account.uid').exists())

    def test_unverified_image_cannot_publish_a_copy(self):
        (self.source / 'romfs/romfs.bin').write_bytes(b'wrong image')
        with self.assertRaisesRegex(ValueError, 'RomFS'):
            self.clone()
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob('.data-copy-*')))
        self.extractor.index_romfs.assert_not_called()

    def test_writable_external_profile_pointer_is_preserved(self):
        external = self.root / 'external-profile'
        external.mkdir()
        (external / 'account.uid').write_bytes(b'external account')
        (self.source / 'launcher.json').write_text(json.dumps({'profile': str(external)}))
        result = self.clone()
        from newsnap.launcher_settings import load_profile
        self.assertEqual(load_profile(result), external)
        self.assertFalse((result / 'profile').exists())
        self.assertEqual((external / 'account.uid').read_bytes(), b'external account')

    def test_readonly_external_profile_is_copied_without_modifying_it(self):
        external = self.root / 'external-profile'
        external.mkdir()
        (external / 'account.uid').write_bytes(b'external account')
        (self.source / 'launcher.json').write_text(json.dumps({'profile': str(external)}))
        with patch.object(self.mod, 'is_writable_data', return_value=False):
            result = self.clone()
        self.assertEqual((result / 'profile/account.uid').read_bytes(), b'external account')
        self.assertEqual((external / 'account.uid').read_bytes(), b'external account')

    def test_real_write_probe_cleans_temporary_file(self):
        before = set(self.source.iterdir())
        self.assertTrue(self.mod.is_writable_data(self.source))
        self.assertEqual(set(self.source.iterdir()), before)
        with patch.object(self.mod.tempfile, 'mkstemp', side_effect=PermissionError('read only')):
            self.assertFalse(self.mod.is_writable_data(self.source))

    def test_source_mutation_after_copy_is_detected(self):
        original = self.mod._copy_file
        def mutate(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if Path(path).name == 'main':
                Path(path).write_bytes(b'changed main')
            return result
        with patch.object(self.mod, '_copy_file', side_effect=mutate):
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                self.clone()
        self.assertFalse(self.destination.exists())

    def test_pinned_normalized_image_is_accepted_and_indexed_by_actual_hash(self):
        original = self.recipe['romfs_sha256']
        self.recipe['romfs_sha256'] = '1' * 64
        self.recipe['romfs_normalized'] = {'sha256': original,
                                          'size': (self.source / 'romfs/romfs.bin').stat().st_size}
        result = self.clone()
        index = json.loads((result / 'romfs/index.json').read_text())
        self.assertEqual(index['romfs_sha256'], original)

    def test_new_profile_is_created_when_original_has_no_progress(self):
        import shutil
        shutil.rmtree(self.source / 'profile')
        result = self.clone()
        self.assertTrue((result / 'profile').is_dir())
        self.assertFalse((self.source / 'profile').exists())

    def test_settings_are_bounded_and_extra_unverified_module_is_rejected(self):
        (self.source / 'newsnap.ini').write_bytes(b'x' * (self.mod.MAX_INI_BYTES + 1))
        with self.assertRaisesRegex(ValueError, 'settings'):
            self.clone()
        self.assertFalse(self.destination.exists())
        (self.source / 'newsnap.ini').unlink()
        (self.source / 'exefs/subsdk0').write_bytes(b'unknown module')
        with self.assertRaisesRegex(ValueError, 'Unexpected ExeFS'):
            self.clone()
        self.assertFalse(self.destination.exists())

    def test_unsafe_recipe_cannot_copy_outside_source(self):
        self.recipe['exefs_sha256']['../escape'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Unsafe module'):
            self.clone()
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
