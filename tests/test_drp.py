import io
import struct
import unittest
import zlib

from newsnap.drp import entries, payload


def archive():
    table = bytes(range(128))
    count = struct.pack('<I', 1)
    crc = zlib.crc32(count + table)
    header = struct.pack('<5I', 0x7F0E5359, crc, 0xC65753E8, 0x90, 1) + table
    payload = b'abc!'
    chunk = struct.pack('<6I', 0, 0xE0A331B4, 32, 0x2F6D9B0B, 4, 4) + b's\0\0\0' + payload
    return header + chunk


class DrpTests(unittest.TestCase):
    def test_index_without_loading_or_decompressing_payload(self):
        result = entries(io.BytesIO(archive()), 0, len(archive()))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 's')
        self.assertEqual(result[0]['extension_crc'], '2f6d9b0b')
        self.assertEqual(result[0]['payload_offset'], 0x94 + 28)
        self.assertFalse(result[0]['compressed'])

    def test_bad_crc_and_chunk_extents_are_rejected(self):
        data = bytearray(archive())
        data[0x14] ^= 1
        with self.assertRaises(ValueError):
            entries(io.BytesIO(data), 0, len(data))

    def test_payload_checks_plaintext_crc_and_compression_marker(self):
        data = bytearray(archive())
        struct.pack_into('<I', data, 0x94, zlib.crc32(b'abc!'))
        stream = io.BytesIO(data)
        item, = entries(stream, 0, len(data))
        self.assertEqual(payload(stream, 0, item), b'abc!')
        data[-1] ^= 1
        with self.assertRaises(ValueError):
            payload(io.BytesIO(data), 0, item)
        item['compressed'] = True
        with self.assertRaises(ValueError):
            payload(io.BytesIO(data), 0, item)
        data = bytearray(archive())
        struct.pack_into('<I', data, 0x94 + 8, 0x10000000)
        with self.assertRaises(ValueError):
            entries(io.BytesIO(data), 0, len(data))


if __name__ == '__main__':
    unittest.main()
