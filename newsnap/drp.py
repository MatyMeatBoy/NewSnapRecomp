"""Bounded metadata reader for Snap's DRPF archives; does not decode Oodle.

Format and cipher adapted from kwsch/NewSnap (SciresM and Kaphotics, ISC).
The complete ISC notice is in licenses/NewSnap-ISC.txt.
"""
import struct
import zlib

MASK = 0xFFFFFFFF


def signed(value):
    return value if value < 0x80000000 else value - 0x100000000


class Cipher:
    def __init__(self, seed, table):
        seed = sum(table[(seed >> (8 * i)) & 127] << (8 * i) for i in range(4))
        self.state = []
        for _ in range(4):
            seed = (seed * 0x41C64E6D + 12345) & MASK
            self.state.append(seed)

    def next(self):
        w, z, y, x = self.state
        t = (x ^ (x << 11)) & MASK
        w2 = (w ^ (signed(w) >> 19) ^ t ^ (signed(t) >> 8)) & MASK
        self.state = [w2, w, z, y]
        return w2 & 0x7FFFFFFF

    def word(self, value):
        low = self.next()
        high = self.next() // 0x40000000
        return value ^ (low | high << 31)


def entries(stream, offset, size):
    """Index entries in one bounded archive. Returned offsets are absolute in stream."""
    def read(relative, length):
        if relative < 0 or length < 0 or relative + length > size:
            raise ValueError('DRPF read out of bounds')
        stream.seek(offset + relative)
        result = stream.read(length)
        if len(result) != length:
            raise ValueError('Truncated DRPF')
        return result

    if size < 0x94 or size % 4:
        raise ValueError('Invalid DRPF size')
    header = read(0, 0x94)
    magic, crc, crypto, hsize, count = struct.unpack_from('<5I', header)
    if magic != 0x7F0E5359:
        raise ValueError('Invalid DRPF magic')
    table = header[0x14:0x94]
    encrypted = crypto != 0xC65753E8
    if encrypted:
        rng = Cipher(crc, table)
        crypto, hsize, count = (rng.word(x) for x in (crypto, hsize, count))
    if crypto != 0xC65753E8 or hsize != 0x90:
        raise ValueError('Invalid DRPF crypto header')
    if crc != zlib.crc32(struct.pack('<I', count) + table):
        raise ValueError('DRPF header checksum mismatch')
    if count > (size - 0x94) // 28:
        raise ValueError('Invalid DRPF entry count')
    result, pos = [], 0x94
    for _ in range(count):
        seed, *words = struct.unpack('<6I', read(pos, 24))
        rng = Cipher(seed, table) if encrypted else None
        if rng:
            words = [rng.word(x) for x in words]
        block_magic, total, extension, packed, unpacked = words
        if block_magic != 0xE0A331B4 or total < 28 or total % 4 or pos + total > size:
            raise ValueError('Invalid DRPF entry extent')
        name = bytearray()
        cursor = 24
        while cursor + 4 <= total and len(name) < 4096:
            value = struct.unpack('<I', read(pos + cursor, 4))[0]
            value = rng.word(value) if rng else value
            raw = struct.pack('<I', value)
            cursor += 4
            if b'\0' in raw:
                name.extend(raw.split(b'\0', 1)[0])
                break
            name.extend(raw)
        else:
            raise ValueError('Unterminated DRPF filename')
        if not name or packed < 4 or cursor + packed > total:
            raise ValueError('Invalid DRPF payload extent')
        value = struct.unpack('<I', read(pos + cursor, 4))[0]
        value = rng.word(value) if rng else value
        compressed = value == 0xE42D98BA
        if not compressed and packed != unpacked:
            raise ValueError('Invalid uncompressed DRPF size')
        result.append({'name': name.decode('ascii'), 'extension_crc': f'{extension:08x}',
                       'block_offset': offset + pos, 'block_size': total, 'crc32': seed,
                       'payload_offset': offset + pos + cursor, 'compressed_size': packed,
                       'decompressed_size': unpacked, 'compressed': compressed, 'encrypted': encrypted})
        pos += total
    return result


def payload(stream, archive_offset, entry):
    """Return decrypted stored bytes; compressed members still need Oodle decoding."""
    stream.seek(archive_offset + 0x14)
    table = stream.read(128)
    if len(table) != 128:
        raise ValueError('Truncated DRPF seed table')
    relative = entry['payload_offset'] - entry['block_offset']
    end = (relative + entry['compressed_size'] + 3) & ~3
    if relative < 24 or end > entry['block_size']:
        raise ValueError('Invalid DRPF payload range')
    stream.seek(entry['block_offset'] + 4)
    data = bytearray(stream.read(end - 4))
    if len(data) != end - 4:
        raise ValueError('Truncated DRPF payload')
    if entry['encrypted']:
        rng = Cipher(entry['crc32'], table)
        for offset in range(0, len(data), 4):
            word = struct.unpack_from('<I', data, offset)[0]
            struct.pack_into('<I', data, offset, rng.word(word))
    data = bytes(data[relative - 4:relative - 4 + entry['compressed_size']])
    if entry['compressed']:
        if data[:4] != struct.pack('<I', 0xE42D98BA):
            raise ValueError('Missing DRPF Oodle marker')
        return data[4:]
    if zlib.crc32(data) != entry['crc32']:
        raise ValueError('DRPF member checksum mismatch')
    return data
