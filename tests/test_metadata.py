import struct
import unittest

from newsnap.metadata import parse_nacp


class MetadataTests(unittest.TestCase):
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
