"""Normalize NSZ, XCI and XCZ dumps into a plain NSP the pinned NCA reader accepts.

The reader (third_party/astral/tools/extract.py) only parses PFS0 with plain NCAs. XCI keeps its
NCAs in the HFS0 "secure" partition; NSZ/XCZ store them as NCZ. NCZ decoding follows nicoboss/nsz
(IndependentNczDecompressorConcise.py, BlockDecompressorReader.py): the first 0x4000 bytes are the
original NCA header, then NCZSECTN (offset, size, crypto type, key, counter per section), then
either one zstd stream or an NCZBLOCK table of zstd blocks of plaintext from 0x4000 on. Sections of
type 3/4 are re-encrypted with AES-CTR (counter = nonce[0:8] || offset >> 4). Each rebuilt NCA is
checked against its file name (the first 16 bytes of its SHA-256), as nsz does.
"""
import hashlib
import struct
from pathlib import Path

NCA_HEADER = 0x4000
CHUNK = 4 << 20


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _read(f, offset, length):
    f.seek(offset)
    data = f.read(length)
    _require(len(data) == length, 'Truncated game file')
    return data


def _partition(f, offset, bound, magic, stride):
    hdr = _read(f, offset, 16)
    _require(hdr[:4] == magic, f'Expected {magic.decode()}')
    count, strings = struct.unpack_from('<II', hdr, 4)
    _require(count <= 4096 and strings <= 1 << 20, 'Invalid partition table')
    size = 16 + count * stride + strings
    _require(size <= bound, 'Partition table out of bounds')
    raw = _read(f, offset, size)
    names = raw[16 + count * stride:]
    entries = []
    for i in range(count):
        off, length, name_off = struct.unpack_from('<QQI', raw, 16 + i * stride)
        _require(name_off < len(names), 'Invalid partition name')
        end = names.find(b'\0', name_off)
        _require(end >= 0, 'Invalid partition name')
        name = names[name_off:end].decode('utf-8')
        _require(name and name not in ('.', '..') and '/' not in name and '\\' not in name,
                 'Unsafe partition name')
        _require(size + off + length <= bound, 'Partition entry out of bounds')
        entries.append((name, offset + size + off, length))
    return entries


def entries(f, size):
    """(kind, [(name, offset, size)]) of an NSP/NSZ (PFS0) or XCI/XCZ (secure HFS0)."""
    if _read(f, 0, 4) == b'PFS0':
        return 'pfs0', _partition(f, 0, size, b'PFS0', 24)
    _require(size >= 0x138 and _read(f, 0x100, 4) == b'HEAD', 'Expected an NSP, NSZ, XCI or XCZ game file')
    root = struct.unpack('<Q', _read(f, 0x130, 8))[0]
    _require(root < size, 'Invalid XCI root partition')
    secure = [e for e in _partition(f, root, size - root, b'HFS0', 64) if e[0] == 'secure']
    _require(len(secure) == 1, 'Expected one XCI secure partition')
    return 'xci', _partition(f, secure[0][1], secure[0][2], b'HFS0', 64)


def needs_conversion(path):
    path = Path(path)
    with path.open('rb') as f:
        kind, items = entries(f, path.stat().st_size)
    return kind != 'pfs0' or any(name.lower().endswith('.ncz') for name, _, _ in items)


class _Window:
    """File-like view of [offset, offset + size) so zstd cannot read past the entry."""

    def __init__(self, f, offset, size):
        self.f, self.pos, self.end = f, offset, offset + size

    def read(self, n=-1):
        n = self.end - self.pos if n is None or n < 0 else min(n, self.end - self.pos)
        if n <= 0:
            return b''
        self.f.seek(self.pos)
        data = self.f.read(n)
        self.pos += len(data)
        return data


def _ctr(key, nonce, offset, data):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    skip = offset & 15
    counter = nonce[:8] + (offset >> 4).to_bytes(8, 'big')
    enc = Cipher(algorithms.AES(key), modes.CTR(counter)).encryptor()
    return enc.update(bytes(skip) + data)[skip:]


def _sections(f, offset, size):
    _require(_read(f, offset + NCA_HEADER, 8) == b'NCZSECTN', 'NCZ has no section table')
    count = struct.unpack('<Q', _read(f, offset + NCA_HEADER + 8, 8))[0]
    _require(0 < count <= 64, 'Invalid NCZ section count')
    sections = []
    for i in range(count):
        raw = _read(f, offset + NCA_HEADER + 16 + i * 0x40, 0x40)
        off, length, crypto = struct.unpack_from('<QQQ', raw)
        _require(crypto in (1, 3, 4) or crypto == 0, f'Unsupported NCZ crypto type {crypto}')
        sections.append((off, length, crypto, raw[0x20:0x30], raw[0x30:0x40]))
    sections.sort()
    _require(sections[0][0] == NCA_HEADER, 'NCZ sections must start after the NCA header')
    for (a, al, *_), (b, *_rest) in zip(sections, sections[1:]):
        _require(a + al == b, 'NCZ sections are not contiguous')
    return sections, offset + NCA_HEADER + 16 + count * 0x40


def _plain_chunks(f, start, end):
    """Decompressed bytes following the section table, in order."""
    import zstandard
    if _read(f, start, 8) == b'NCZBLOCK':
        hdr = _read(f, start, 24)
        exponent = hdr[11]
        _require(14 <= exponent <= 32, 'Invalid NCZBLOCK size')
        blocks, total = struct.unpack_from('<IQ', hdr, 12)
        sizes = struct.unpack(f'<{blocks}I', _read(f, start + 24, 4 * blocks))
        block = 1 << exponent
        pos = start + 24 + 4 * blocks
        d = zstandard.ZstdDecompressor()
        for i, length in enumerate(sizes):
            expected = block if i < blocks - 1 or total % block == 0 else total % block
            data = _read(f, pos, length)
            pos += length
            yield d.decompress(data, max_output_size=expected) if length < expected else data[:expected]
        _require(pos <= end, 'NCZ blocks out of bounds')
    else:
        reader = zstandard.ZstdDecompressor().stream_reader(_Window(f, start, end - start))
        while chunk := reader.read(CHUNK):
            yield chunk


def decompress_ncz(f, offset, size, out):
    """Write the NCA rebuilt from the NCZ at [offset, offset + size); return its SHA-256 hex."""
    sections, data_start = _sections(f, offset, size)
    digest = hashlib.sha256()
    header = _read(f, offset, NCA_HEADER)
    out.write(header)
    digest.update(header)
    pos, index = NCA_HEADER, 0
    total = sections[-1][0] + sections[-1][1]
    for chunk in _plain_chunks(f, data_start, offset + size):
        while chunk:
            _require(index < len(sections), 'NCZ has more data than its sections')
            s_off, s_len, crypto, key, nonce = sections[index]
            part = chunk[:s_off + s_len - pos]
            chunk = chunk[len(part):]
            if crypto in (3, 4):
                part = _ctr(key, nonce, pos, part)
            out.write(part)
            digest.update(part)
            pos += len(part)
            if pos == s_off + s_len:
                index += 1
    _require(pos == total, 'NCZ data ends before its sections')
    return digest.hexdigest()


def _copy(f, offset, size, out):
    digest = hashlib.sha256()
    f.seek(offset)
    left = size
    while left:
        data = f.read(min(CHUNK, left))
        _require(data, 'Truncated game file')
        out.write(data)
        digest.update(data)
        left -= len(data)
    return digest.hexdigest()


def to_nsp(source, target, progress=lambda name: None):
    """Write `target` as a PFS0 holding every entry of `source`, NCZ rebuilt as NCA."""
    source, target = Path(source), Path(target)
    with source.open('rb') as f:
        _, items = entries(f, source.stat().st_size)
        names = [n[:-4] + '.nca' if n.lower().endswith('.ncz') else n for n, _, _ in items]
        _require(len(set(names)) == len(names), 'Duplicate NCA after NCZ conversion')
        strings = b''.join(n.encode('utf-8') + b'\0' for n in names)
        strings += bytes(-(16 + 24 * len(names) + len(strings)) % 0x20)
        table = 16 + 24 * len(names) + len(strings)
        temporary = target.with_suffix(target.suffix + '.tmp')
        sizes = []
        with temporary.open('wb') as out:
            out.write(bytes(table))
            for (name, offset, size), new_name in zip(items, names):
                progress(new_name)
                start = out.tell()
                if name.lower().endswith('.ncz'):
                    digest = decompress_ncz(f, offset, size, out)
                else:
                    digest = _copy(f, offset, size, out)
                stem = new_name.split('.', 1)[0].lower()
                if new_name.lower().endswith('.nca') and len(stem) == 32 and all(c in '0123456789abcdef' for c in stem):
                    _require(digest[:32] == stem, f'{new_name} does not match its hash (damaged dump)')
                sizes.append(out.tell() - start)
            out.seek(0)
            out.write(b'PFS0' + struct.pack('<II', len(names), len(strings)) + bytes(4))
            data_offset, name_offset = 0, 0
            for new_name, length in zip(names, sizes):
                out.write(struct.pack('<QQII', data_offset, length, name_offset, 0))
                data_offset += length
                name_offset += len(new_name.encode('utf-8')) + 1
            out.write(strings)
    temporary.replace(target)
    return target
