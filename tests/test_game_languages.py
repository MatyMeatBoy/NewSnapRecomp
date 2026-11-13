"""Only languages advertised by the verified Snap control metadata may be selected."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

from newsnap import launcher_settings as settings
from newsnap.metadata import parse_nacp_languages
from newsnap.upstream import ROOT

EXPECTED = ('en-US', 'ja', 'fr', 'de', 'es-419', 'es', 'it', 'fr-CA', 'ko', 'zh-Hant', 'zh-Hans')


class GameLanguageTests(unittest.TestCase):
    def test_settings_offer_only_game_languages_and_auto(self):
        self.assertEqual(settings.LANGUAGES, ('', *EXPECTED))
        self.assertEqual(settings.CHOICES['lang'], settings.LANGUAGES)
        for code in ('', *EXPECTED):
            self.assertEqual(settings.validate_settings({'lang': code}), {'lang': code})
        for code in ('pt', 'pt-BR', 'nl', 'ru', 'en-GB', 'zh-CN', 'zh-TW', 'xx'):
            with self.subTest(code=code), self.assertRaises(ValueError):
                settings.validate_settings({'lang': code})

    def test_mask_and_nonempty_title_both_required(self):
        nacp = bytearray(0x4000)
        struct.pack_into('<I', nacp, 0x302c, 0x72fd)
        for slot in range(16):
            nacp[slot*0x300:slot*0x300+5] = b'Title'
        self.assertEqual(parse_nacp_languages(nacp), EXPECTED)
        nacp[5*0x300:5*0x300+0x200] = bytes(0x200)
        self.assertEqual(parse_nacp_languages(nacp), tuple(code for code in EXPECTED if code != 'es-419'))
        struct.pack_into('<I', nacp, 0x302c, 0)
        self.assertEqual(parse_nacp_languages(nacp), ())
        with self.assertRaises(ValueError):
            parse_nacp_languages(nacp[:0x100])

    def test_optional_real_control_matches_verified_receipt(self):
        control = ROOT / 'build/extracted/updated/control'
        romfs = control / 'romfs.bin'
        receipt = control / 'receipt.json'
        if not romfs.is_file() or not receipt.is_file():
            self.skipTest('owner control data unavailable; synthetic metadata fixture remains authoritative test')
        expected_hash = '5158fb8738bbacf4743c832a2b6e80ace365377010883f2e8afd7515a9f7605a'
        self.assertEqual(json.loads(receipt.read_text())['romfs_sha256'], expected_hash)
        data = romfs.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), expected_hash)
        self.assertEqual(parse_nacp_languages(data[512:512+0x4000]), EXPECTED)


if __name__ == '__main__':
    unittest.main()
