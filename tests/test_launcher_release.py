import tempfile
import unittest
from pathlib import Path

from tools.build_launcher import source_fingerprints
from tools.package_windows_release import verify_public_tree
from newsnap.paths import runtime_dir, default_profile


class LauncherReleaseTests(unittest.TestCase):
    def test_owner_data_folder_alias_is_resolved_without_copying_or_renaming(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'newsnapGameData'
            data.mkdir()
            (data / 'newsnap-game.json').write_text('{}')
            self.assertEqual(runtime_dir(root), data)
            self.assertEqual(default_profile(root), data / 'profile')
    def test_game_data_is_rejected_from_public_exe_release(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'NewSnapLauncher.exe').write_bytes(b'own launcher fixture')
            verify_public_tree(root)
            (root / 'gamedata').mkdir()
            with self.assertRaises(ValueError):
                verify_public_tree(root)
        for name in ('MAIN', 'NEWSNAP.EXE', 'prod.keys', 'romfs.bin'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / name).write_bytes(b'private fixture')
                with self.assertRaises(ValueError):
                    verify_public_tree(root)
    def test_frozen_recipe_detects_code_and_icon_changes_but_excludes_game_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, value in {'newsnap/launcher.py': b'original code', 'assets/icons/newsnap.ico': b'original art',
                                'GameData/exefs/main': b'private code'}.items():
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(value)
            before = source_fingerprints(root)
            self.assertEqual(set(before), {'newsnap/launcher.py', 'assets/icons/newsnap.ico'})
            (root / 'GameData/exefs/main').write_bytes(b'other private data')
            self.assertEqual(source_fingerprints(root), before)
            (root / 'newsnap/launcher.py').write_bytes(b'new code')
            self.assertNotEqual(source_fingerprints(root), before)


if __name__ == '__main__':
    unittest.main()
