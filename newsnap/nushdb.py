"""Bounded reader for SSBH 1.2 shader libraries and their NVN payloads.

Format reference: ultimate-research/ssbh_lib, formats/shdr.rs (MIT).
Runtime hashes/seed layouts follow the pinned Astral runtime (MIT).
"""
import hashlib
import struct


def shaders(data):
    def span(offset, size):
        if offset < 0 or size < 0 or offset + size > len(data):
            raise ValueError('Shader library extent outside file')
        return data[offset:offset + size]

    def number(fmt, offset):
        return struct.unpack(fmt, span(offset, struct.calcsize(fmt)))[0]

    if span(0, 4) != b'HBSS' or span(16, 8) != b'RDHS\x01\x00\x02\x00':
        raise ValueError('Unsupported shader library header')
    table, count = 24 + number('<Q', 24), number('<Q', 32)
    if count > 10000:
        raise ValueError('Too many shader library entries')
    span(table, count * 56)
    for index in range(count):
        entry = table + index * 56
        stage = number('<I', entry + 8)
        if stage not in (0, 3, 4, 5):
            raise ValueError('Unknown shader stage')
        offset = entry + 16 + number('<Q', entry + 16)
        size = number('<Q', entry + 24)
        if size != number('<Q', entry + 32):
            raise ValueError('Inconsistent shader binary lengths')
        blob = span(offset, size)
        if len(blob) < 0x4c:
            raise ValueError('Truncated shader binary')
        control_offset = struct.unpack_from('<I', blob, 0x48)[0]
        if control_offset + 0x880 > len(blob):
            raise ValueError('Truncated NVN control')
        control = blob[control_offset:control_offset + 0x880]
        if control[:4] != b'\x34\x12\x76\x98':
            raise ValueError('Invalid NVN control magic')
        c1offset, length = struct.unpack_from('<II', control, 0x700)
        nvn_stage = struct.unpack_from('<I', control, 0x714)[0]
        if nvn_stage != {0: 0, 3: 2, 4: 1, 5: 5}[stage]:
            raise ValueError('Shader stage disagrees with control')
        start = control_offset + struct.unpack_from('<Q', control, 0x20)[0]
        if c1offset > length or not length or start + length > len(blob):
            raise ValueError('Invalid shader code extent')
        if stage != 5 and length <= 0x30:
            raise ValueError('Missing graphics shader prefix')
        code = blob[start:start + length]
        c1 = code[c1offset:]
        key = hashlib.sha256(struct.pack('<I', stage) + control + struct.pack('<Q', length)
                             + code + struct.pack('<I', len(c1)) + c1).digest()
        yield stage, key, control, code, c1


def program_record(stage, key, control, code, c1):
    return struct.pack('<III', stage, len(code), len(c1)) + key + control + code + c1
