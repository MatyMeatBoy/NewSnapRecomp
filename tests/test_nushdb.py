import struct
import unittest

from newsnap.nushdb import shaders


def library(stage=0):
    data = bytearray(0x1000)
    data[:4] = b'HBSS'
    data[16:24] = b'RDHS\x01\x00\x02\x00'
    struct.pack_into('<QQ', data, 24, 0x28, 1)
    struct.pack_into('<IIQQQ', data, 0x48, stage, 2, 0xb0, 0xf00, 0xf00)
    struct.pack_into('<I', data, 0x148, 0x100)
    data[0x200:0x204] = b'\x34\x12\x76\x98'
    struct.pack_into('<Q', data, 0x220, 0x880)
    struct.pack_into('<II', data, 0x900, 0x38, 0x40)
    struct.pack_into('<I', data, 0x914, {0: 0, 3: 2, 4: 1, 5: 5}[stage])
    return data


class ShaderTests(unittest.TestCase):
    def test_stages_and_constant_buffer(self):
        for stage in (0, 3, 4, 5):
            row, = shaders(library(stage))
            self.assertEqual(row[0], stage)
            self.assertEqual(len(row[1]), 32)
            self.assertEqual(len(row[2]), 0x880)
            self.assertEqual(len(row[3]), 0x40)
            self.assertEqual(len(row[4]), 8)

    def test_truncation_extents_and_stage_mismatch(self):
        for offset, fmt, value in ((24, '<Q', 2**63), (32, '<Q', 10001),
                                   (0x148, '<I', 0xffff), (0x900, '<I', 0x41),
                                   (0x914, '<I', 5)):
            data = library()
            struct.pack_into(fmt, data, offset, value)
            with self.assertRaises(ValueError):
                list(shaders(data))
        with self.assertRaises(ValueError):
            list(shaders(library()[:0x100]))
