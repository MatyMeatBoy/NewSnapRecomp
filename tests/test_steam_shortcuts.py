import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from newsnap import steam_shortcuts as s

ROOT = Path(__file__).resolve().parents[1]


class SteamShortcuts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        steam = Path(self.tmp.name) / 'Steam'
        self.config = steam / 'userdata' / '12345' / 'config'
        self.config.mkdir(parents=True)
        (steam / 'config').mkdir()
        (steam / 'config' / 'loginusers.vdf').write_text(
            '"users"\n{\n\t"76561197960278073"\n\t{\n\t\t"MostRecent"\t\t"1"\n\t}\n}\n')
        other = [['shortcuts', 0, [['0', 0, [['appid', 2, 123], ['AppName', 1, 'Other'], ['Exe', 1, '"C:/x.exe"']]]]]]
        (self.config / 'shortcuts.vdf').write_bytes(s.vdf_write(other))
        self.env = mock.patch.dict(os.environ, {'NEWSNAP_STEAM_DIR': str(steam)})
        self.env.start()
        self.game = Path(self.tmp.name) / 'Game'
        self.game.mkdir()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def names(self):
        items, _ = s.vdf_read((self.config / 'shortcuts.vdf').read_bytes())
        return [s._find(e[2], 'AppName')[2] for e in items[0][2]]

    def test_add_keeps_other_games_once_and_remove_restores(self):
        exe = self.game / 'NewSnapLauncher.exe'
        self.assertEqual(s.add_to_steam(self.game, exe, ROOT / 'assets/launcher'), 1)
        self.assertEqual(s.add_to_steam(self.game, exe, ROOT / 'assets/launcher'), 1)
        self.assertEqual(self.names(), ['Other', s.NAME])
        self.assertTrue(s.in_steam(self.game))
        self.assertEqual(len(list((self.config / 'grid').iterdir())), 4)
        self.assertTrue((self.config / s.BACKUP).is_file())
        self.assertEqual(s.remove_from_steam(self.game), 1)
        self.assertEqual(self.names(), ['Other'])
        self.assertFalse(s.in_steam(self.game))
        self.assertEqual(list((self.config / 'grid').iterdir()), [])

    def test_unreadable_list_is_never_overwritten(self):
        (self.config / 'shortcuts.vdf').write_bytes(b'\x00shortcuts\x00\x09bad')
        self.assertEqual(s.add_to_steam(self.game, self.game / 'x.exe', ROOT / 'assets/launcher'), 0)
        self.assertEqual((self.config / 'shortcuts.vdf').read_bytes(), b'\x00shortcuts\x00\x09bad')


if __name__ == '__main__':
    unittest.main()
