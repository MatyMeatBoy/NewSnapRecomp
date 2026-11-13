import unittest
from pathlib import Path

from tools.check_content import violations


class ContentTests(unittest.TestCase):
    def test_only_reviewed_original_icons_are_allowed_as_binary_assets(self):
        icon = Path(__file__).resolve().parent.parent / 'assets/icons/icon-16.png'
        data = icon.read_bytes()
        self.assertFalse(violations('assets/icons/icon-16.png', data))
        self.assertTrue(violations('assets/icons/icon-16.png', data + b'\0unreviewed'))
        self.assertTrue(violations('assets/icons/unknown.png', data))

    def test_private_inputs_and_renamed_secrets_are_rejected(self):
        self.assertTrue(violations('prod.keys', b'private'))
        self.assertTrue(violations('innocent.txt', b'header_key = ' + b'a' * 64))
        self.assertTrue(violations('generated/main/main_0000.c', b'code'))
        self.assertTrue(violations('misc.txt', b'NSO0\0binary'))
        self.assertTrue(violations('renamed.c', b'// AC_RECOMP_' + b'GENERATED_FROM_GAME_CODE: main'))
        self.assertFalse(violations('newsnap/importer.py', b'print("hello")'))
        self.assertFalse(violations('third_party/astral', b'', '160000'))


if __name__ == '__main__':
    unittest.main()
