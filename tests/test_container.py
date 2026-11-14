import hashlib
import io
import os
import struct
import tempfile
import unittest
from pathlib import Path

import zstandard

from newsnap import container


def table(magic, files, stride):
    names = b''.join(n.encode() + b'\0' for n, _ in files)
    out, off, noff = [], 0, 0
    for n, data in files:
        entry = struct.pack('<QQI', off, len(data), noff)
        if stride == 64:
            entry += struct.pack('<IQ', 0x200, 0) + bytes(32)
        else:
            entry += bytes(4)
        out.append(entry)
        off += len(data)
        noff += len(n) + 1
    return magic + struct.pack('<II', len(files), len(names)) + bytes(4) + b''.join(out) + names + b''.join(d for _, d in files)


def sample(block):
    key, nonce = os.urandom(16), os.urandom(8) + bytes(8)
    header, plain = os.urandom(0x4000), os.urandom(0x10000) + bytes(0x30000)
    sections = [(0x4000, 0x8000, 1, bytes(16), bytes(16)), (0xC000, 0x38000, 3, key, nonce)]
    nca = header + plain[:0x8000] + container._ctr(key, nonce, 0xC000, plain[0x8000:])
    body = b'NCZSECTN' + struct.pack('<Q', 2) + b''.join(
        struct.pack('<QQQQ', o, s, c, 0) + k + n for o, s, c, k, n in sections)
    if block:
        size = 1 << 14
        blocks = [plain[i:i + size] for i in range(0, len(plain), size)]
        packed = [zstandard.ZstdCompressor().compress(b) for b in blocks]
        packed = [p if len(p) < len(b) else b for p, b in zip(packed, blocks)]
        body += b'NCZBLOCK' + bytes([2, 1, 0, 14]) + struct.pack('<IQ', len(blocks), len(plain))
        body += struct.pack(f'<{len(packed)}I', *map(len, packed)) + b''.join(packed)
    else:
        body += zstandard.ZstdCompressor().compress(plain)
    return nca, header + body, hashlib.sha256(nca).hexdigest()[:32]


class ContainerTest(unittest.TestCase):
    def roundtrip(self, image, expected):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / 'in', Path(tmp) / 'out.nsp'
            src.write_bytes(image)
            self.assertTrue(container.needs_conversion(src))
            container.to_nsp(src, dst)
            self.assertFalse(container.needs_conversion(dst))
            with dst.open('rb') as f:
                kind, items = container.entries(f, dst.stat().st_size)
                got = {n: (f.seek(o), f.read(s))[1] for n, o, s in items}
            self.assertEqual(kind, 'pfs0')
            self.assertEqual(got, expected)

    def test_nsz_stream_and_block(self):
        for block in (False, True):
            nca, ncz, name = sample(block)
            self.roundtrip(table(b'PFS0', [(name + '.ncz', ncz), ('x.tik', b'T' * 0x2C0)], 24),
                           {name + '.nca': nca, 'x.tik': b'T' * 0x2C0})

    def test_xcz_secure_partition(self):
        nca, ncz, name = sample(True)
        plain = os.urandom(0x400)
        secure = table(b'HFS0', [(name + '.ncz', ncz), ('meta.cnmt.nca', plain)], 64)
        root = table(b'HFS0', [('update', b''), ('secure', secure)], 64)
        head = bytearray(0x200)
        head[0x100:0x104] = b'HEAD'
        struct.pack_into('<Q', head, 0x130, 0x200)
        self.roundtrip(bytes(head) + root, {name + '.nca': nca, 'meta.cnmt.nca': plain})

    def test_damaged_ncz_is_rejected(self):
        nca, ncz, name = sample(False)
        bad = table(b'PFS0', [(('0' * 32) + '.ncz', ncz)], 24)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'in.nsz'
            src.write_bytes(bad)
            with self.assertRaisesRegex(ValueError, 'does not match'):
                container.to_nsp(src, Path(tmp) / 'out.nsp')

    def test_plain_nsp_is_used_as_is(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'in.nsp'
            src.write_bytes(table(b'PFS0', [('a.nca', b'A' * 32)], 24))
            self.assertFalse(container.needs_conversion(src))


if __name__ == '__main__':
    unittest.main()
