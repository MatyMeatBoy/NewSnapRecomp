import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch


def release(root, version='0.9.25', files=None):
    files = files or {'NewSnapLauncher.exe': b'launcher', '_internal/runtime.dll': b'runtime'}
    root.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = {'version': version, 'source_revision': 'a' * 40, 'contains_game_data': False,
                'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in files.items()}}
    (root / 'MANIFEST.json').write_text(json.dumps(manifest))
    return manifest


class InstallLocationTests(unittest.TestCase):
    def setUp(self):
        from newsnap import install_location
        self.mod = install_location
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / 'readonly'
        self.source.mkdir()
        self.local = self.base / 'local'

    def fallback(self):
        with patch.object(self.mod, '_can_write', side_effect=lambda p: p != self.source):
            return self.mod.writable_install(self.source, local_root=self.local)

    def test_writable_root_needs_no_manifest_or_relocation(self):
        self.assertEqual(self.mod.writable_install(self.source, self.local), self.source)
        self.assertEqual(list(self.source.iterdir()), [])
        self.assertFalse(self.local.exists())

    def test_copies_only_verified_public_inventory(self):
        release(self.source)
        (self.source / 'portable.txt').write_text('')
        (self.source / 'owner.keys').write_text('private')
        before = {p.name: p.read_bytes() for p in self.source.iterdir() if p.is_file()}
        target = self.fallback()
        self.assertTrue(target.is_relative_to(self.local / 'NewSnapRecomp/installs'))
        self.assertEqual((target / 'NewSnapLauncher.exe').read_bytes(), b'launcher')
        self.assertFalse((target / 'owner.keys').exists())
        self.assertFalse((target / 'portable.txt').exists())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.source.iterdir() if p.is_file()})
        self.assertEqual(self.fallback(), target)

    def test_integrity_failure_has_no_ready_target_or_staging(self):
        release(self.source)
        (self.source / '_internal/runtime.dll').write_bytes(b'corrupt')
        with self.assertRaises((RuntimeError, ValueError)):
            self.fallback()
        self.assertFalse(list(self.local.rglob('NewSnapLauncher.exe')))
        self.assertFalse(list(self.local.rglob('.relocate-*')))

    def test_rejects_traversal_and_private_inventory(self):
        for name in ('../outside.dll', 'GameData/profile/account.uid', 'hdshadows/map.dds',
                     'GameData-import/data.json', 'owner.keys', 'launcher-settings.json'):
            with self.subTest(name=name):
                manifest = release(self.source)
                manifest['files'][name] = {'size': 0, 'sha256': '0' * 64}
                (self.source / 'MANIFEST.json').write_text(json.dumps(manifest))
                with self.assertRaises((RuntimeError, ValueError)):
                    self.fallback()

    def test_newer_verified_target_is_reused_and_userdata_preserved(self):
        release(self.source)
        target = self.fallback()
        release(target, '0.9.26', {'NewSnapLauncher.exe': b'newer'})
        profile = target / 'GameData/profile/save'
        profile.mkdir(parents=True)
        (profile / 'owner.bin').write_bytes(b'owner')
        self.assertEqual(self.fallback(), target)
        self.assertEqual((target / 'NewSnapLauncher.exe').read_bytes(), b'newer')
        self.assertEqual((profile / 'owner.bin').read_bytes(), b'owner')

    def test_older_target_upgrade_preserves_userdata(self):
        release(self.source, '0.9.24')
        target = self.fallback()
        (target / 'launcher-settings.json').write_bytes(b'owner preference')
        release(self.source, '0.9.25', {'NewSnapLauncher.exe': b'new version'})
        self.assertEqual(self.fallback(), target)
        self.assertEqual((target / 'NewSnapLauncher.exe').read_bytes(), b'new version')
        self.assertEqual((target / 'launcher-settings.json').read_bytes(), b'owner preference')

    def test_existing_ini_and_unlisted_retired_folder_are_preserved(self):
        release(self.source, '0.9.24', {'NewSnapLauncher.exe': b'old', 'defaults.ini': b'default'})
        target = self.fallback()
        (target / 'defaults.ini').write_bytes(b'personal changes')
        old_folder = target / 'pruebas-amd'
        old_folder.mkdir()
        script = old_folder / 'my-test.bat'
        script.write_bytes(b'user script')
        release(self.source, '0.9.25', {'NewSnapLauncher.exe': b'new', 'defaults.ini': b'new defaults'})
        self.assertEqual(self.fallback(), target)
        self.assertEqual((target / 'defaults.ini').read_bytes(), b'personal changes')
        self.assertEqual(script.read_bytes(), b'user script')
        self.assertEqual(self.fallback(), target)

    def test_upgrade_failure_rolls_back_public_files(self):
        release(self.source, '0.9.24')
        target = self.fallback()
        original = (target / 'MANIFEST.json').read_bytes()
        release(self.source, '0.9.25', {'NewSnapLauncher.exe': b'new'})
        replace = self.mod.os.replace
        def fail_new_manifest(source, dest):
            if Path(source).name == 'MANIFEST.json' and Path(source).parent.name.startswith('.relocate-'):
                raise OSError('injected failure')
            return replace(source, dest)
        with patch.object(self.mod.os, 'replace', side_effect=fail_new_manifest):
            with self.assertRaisesRegex(RuntimeError, 'rolled back'):
                self.fallback()
        self.assertEqual((target / 'NewSnapLauncher.exe').read_bytes(), b'launcher')
        self.assertEqual((target / 'MANIFEST.json').read_bytes(), original)
        self.assertFalse(list(self.local.rglob('.relocate-*')))

    def test_concurrent_relocations_share_one_verified_instance(self):
        release(self.source)
        results, failures = [], []
        def relocate():
            try:
                results.append(self.mod.writable_install(self.source, self.local))
            except Exception as error:
                failures.append(error)
        with patch.object(self.mod, '_can_write', side_effect=lambda path: Path(path) != self.source):
            threads = [threading.Thread(target=relocate) for _ in range(3)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(10)
            self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 3)
        self.assertEqual(len(set(results)), 1)
        self.assertEqual((results[0] / 'NewSnapLauncher.exe').read_bytes(), b'launcher')

    def test_corrupt_existing_target_is_not_overwritten(self):
        release(self.source)
        target = self.fallback()
        (target / 'NewSnapLauncher.exe').write_bytes(b'corrupt')
        with self.assertRaises((RuntimeError, ValueError)):
            self.fallback()
        self.assertEqual((target / 'NewSnapLauncher.exe').read_bytes(), b'corrupt')

    def test_linked_inventory_is_rejected(self):
        release(self.source)
        linked = self.source / '_internal/runtime.dll'
        linked.unlink()
        outside = self.base / 'outside.dll'
        outside.write_bytes(b'runtime')
        try:
            linked.symlink_to(outside)
        except OSError:
            self.skipTest('symlinks unavailable')
        with self.assertRaises((RuntimeError, ValueError)):
            self.fallback()

    def test_interrupted_copy_removes_only_owned_scratch(self):
        release(self.source)
        with patch.object(self.mod.shutil, 'copyfile', side_effect=OSError('copy failed')):
            with self.assertRaises((RuntimeError, OSError)):
                self.fallback()
        self.assertFalse(list(self.local.rglob('.relocate-*')))
        self.assertFalse(list(self.local.rglob('NewSnapLauncher.exe')))


if __name__ == '__main__':
    unittest.main()
