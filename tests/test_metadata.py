import struct
import unittest

from newsnap.metadata import parse_nacp, parse_nacp_languages


class MetadataTests(unittest.TestCase):
    def test_language_slot_order_and_invalid_title(self):
        nacp = bytearray(0x4000)
        struct.pack_into('<I', nacp, 0x302c, (1 << 0) | (1 << 1) | (1 << 5) | (1 << 15))
        for slot in (0, 1, 5, 15):
            nacp[slot * 0x300:slot * 0x300 + 5] = b'Title'
        self.assertEqual(parse_nacp_languages(nacp), ('en-US', 'en-GB', 'es-419', 'pt-BR'))
        nacp[0] = 0xff
        with self.assertRaisesRegex(ValueError, 'localized title'):
            parse_nacp_languages(nacp)

    def test_version_and_save_capacity_come_from_control(self):
        nacp = bytearray(0x4000)
        nacp[0x3060:0x3065] = b'9.8.7'
        struct.pack_into('<QQ', nacp, 0x3080, 1024, 512)
        self.assertEqual(parse_nacp(nacp), {'display_version': '9.8.7', 'save_size': 1024, 'journal_size': 512})
        with self.assertRaises(ValueError):
            parse_nacp(nacp[:0x100])
        struct.pack_into('<Q', nacp, 0x3080, 1 << 63)
        with self.assertRaises(ValueError):
            parse_nacp(nacp)
