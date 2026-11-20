"""Bounded NUP v1 reader, from a55uka/nup SPEC at a4840f06c94ddeb4.

NUP contains decrypted trees, not encrypted NCAs. Container hashes establish
integrity only; callers must compare game content to their trusted recipe.
No reference implementation code is imported or executed.
"""
from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import io
import os
from pathlib import Path
import stat
import struct
import tempfile


class NupError(ValueError):
    pass


def _require(ok, message):
    if not ok:
        raise NupError(message)


def _name(raw, *, root=False):
    try:
        name = raw.decode('utf-8')
    except UnicodeError as error:
        raise NupError('Invalid UTF-8 node name') from error
    if not name and root:
        return name
    stem = name.split('.')[0].upper()
    _require(name and name not in ('.', '..') and not any(c in name for c in '/\\:\0<>"|?*')
             and not any(ord(c) < 32 for c in name) and not name.endswith((' ', '.'))
             and stem not in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1,10)),
                              *(f'LPT{i}' for i in range(1,10))}, 'Unsafe NUP node name')
    return name


@dataclass(frozen=True)
class Package:
    title_id: int
    root_dir: int
    exefs_dir: int
    romfs_dir: int
    version: int
    kind: int
    flags: int


@dataclass(frozen=True)
class Member:
    name: str
    size: int
    offset: int
    stored_size: int
    sha256: bytes
    codec: int


class _Extent(io.RawIOBase):
    def __init__(self, stream, offset, size):
        self.stream, self.left = stream, size
        stream.seek(offset)

    def readable(self):
        return True

    def read(self, size=-1):
        size = self.left if size < 0 else min(size, self.left)
        data = self.stream.read(size)
        self.left -= len(data)
        return data

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


class _VerifiedStream:
    def __init__(self, reader, member):
        self.reader, self.member = reader, member
        self.digest = hashlib.sha256()
        self.size = 0

    def read(self, size=-1):
        if size == 0: return b''
        if size < 0:
            _require(self.member.size-self.size <= 64 << 20, 'NUP in-memory read limit')
            size = self.member.size-self.size+1
        try:
            block = self.reader.read(min(size,self.member.size-self.size+1))
        except Exception as error:
            raise NupError(f'NUP member decode failed: {self.member.name}') from error
        self.size += len(block)
        _require(self.size <= self.member.size, 'NUP decompression exceeds declared size')
        self.digest.update(block)
        if not block: self.check()
        return block

    def check(self):
        _require(self.size == self.member.size and self.digest.digest() == self.member.sha256,
                 f'NUP member SHA256/size mismatch: {self.member.name}')


class NupReader:
    def __init__(self, path, *, max_toc_size=64 << 20, max_file_size=16 << 30,
                 max_total_size=128 << 30, max_nodes=500000, max_packages=128):
        self.path = Path(path)
        self._stream = self.path.open('rb')
        try:
            self._parse(max_toc_size, max_file_size, max_total_size, max_nodes, max_packages)
        except BaseException:
            self.close()
            raise

    def close(self):
        self._stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _parse(self, max_toc, max_file, max_total, max_nodes, max_packages):
        stream = self._stream
        size = stream.seek(0, 2); stream.seek(0)
        header = stream.read(128)
        _require(len(header) == 128, 'Truncated NUP header')
        magic, hs, hv, to, ts, th, blob, total, pc, flags, uuid, reserved = struct.unpack(
            '<4sHHQQ32sQQII16s32s', header)
        _require(magic == b'NUP\x01' and hv == 1 and hs == 128 and to == hs,
                 'Unsupported NUP header version')
        _require(not flags and not any(reserved), 'Unsupported NUP header flags')
        _require(total == size and 48 <= ts <= max_toc and blob >= to+ts
                 and blob <= total and blob % 16 == 0 and 0 < pc <= max_packages,
                 'Invalid NUP bounds or limits')
        stream.seek(to); toc = stream.read(ts)
        _require(hashlib.sha256(toc).digest() == th, 'NUP TOC SHA256 mismatch')
        tm, count, nd, nf, po, ps, tr = struct.unpack_from('<4sIQQQQQ', toc)
        fixed = 48 + count*64 + nd*24 + nf*80
        _require(tm == b'TOC\x01' and count == pc and not tr and 0 < nd <= max_nodes
                 and nf <= max_nodes and fixed <= po <= ts and po+ps <= ts
                 and (po-fixed) % 4 == 0, 'Invalid NUP TOC layout')
        pool = toc[po:po+ps]
        def label(off, length, root=False):
            _require(off+length <= len(pool), 'NUP string outside pool')
            return _name(pool[off:off+length], root=root)
        self.packages = []
        metas = []
        for i in range(pc):
            pos = 48+i*64
            tid, root, ex, rom, ver, kind, fl, r1, r2, mo, ms = struct.unpack_from(
                '<QIIIIBBHIQI20x', toc, pos)
            _require(kind < 5 and not fl & ~1 and not r1 and not r2
                     and not any(toc[pos+44:pos+64]), 'Invalid NUP package flags')
            _require(root < nd and all(d == 0xffffffff or d < nd for d in (ex,rom)),
                     'Invalid NUP package directory')
            _require((mo == ms == 0) or (mo >= blob and mo+ms <= total), 'Invalid NUP metadata extent')
            if ms: metas.append((mo,mo+ms))
            self.packages.append(Package(tid,root,ex,rom,ver,kind,fl))
        _require(sum(p.kind == 0 for p in self.packages) <= 1, 'Multiple NUP base packages')
        _require(all(p.kind != 1 or p.flags & 1 or any(q.kind == 0 for q in self.packages)
                     for p in self.packages), 'NUP update needs base or standalone flag')
        self._dirs = []
        roots = {p.root_dir for p in self.packages}
        pos = 48+pc*64
        for i in range(nd):
            no, nl, first, nc, zero = struct.unpack_from('<IIIIQ', toc, pos); pos += 24
            _require(not zero, 'Invalid NUP directory reserved field')
            self._dirs.append((label(no,nl,root=i in roots),first,nc))
        self._files = []
        allocated = 0; extents = {}
        for i in range(nf):
            no,nl,sz,off,stored,digest,codec,cf,zero = struct.unpack_from('<IIQQQ32sBBH12x',toc,pos)
            _require(not cf and not zero and not any(toc[pos+68:pos+80]), 'Invalid NUP codec flags')
            pos += 80
            _require(codec in (0,1) and sz <= max_file, 'Unsupported NUP codec or member limit')
            _require((sz == 0 and off == stored == codec == 0) or
                     (sz > 0 and stored > 0 and off >= blob and off % 16 == 0
                      and off+stored <= total), 'Invalid NUP member extent')
            _require(codec != 0 or sz == stored, 'NUP raw size mismatch')
            allocated += sz
            _require(allocated <= max_total, 'NUP aggregate size limit')
            self._files.append(Member(label(no,nl),sz,off,stored,digest,codec))
            if stored:
                key = (off,off+stored); identity = (sz,digest,codec)
                _require(key not in extents or extents[key] == identity, 'Conflicting NUP shared extent')
                extents[key] = identity
        regions = sorted(list(extents)+metas)
        _require(all(a[1] <= b[0] for a,b in zip(regions,regions[1:])), 'Overlapping NUP extents')
        self._children = struct.unpack_from(f'<{(po-pos)//4}I', toc, pos)
        ranges = sorted((f,f+c) for _,f,c in self._dirs if c)
        _require(all(b <= len(self._children) for a,b in ranges)
                 and all(a[1] <= b[0] for a,b in zip(ranges,ranges[1:]))
                 and sum(c for _,_,c in self._dirs) == len(self._children), 'Invalid NUP child ranges')
        _require(all(i < nd+nf for i in self._children), 'Invalid NUP child node')
        self._trees = []
        for package in self.packages:
            self._walk(package.root_dir, '')
            mounted = {}
            for prefix,directory in (('exefs',package.exefs_dir),('romfs',package.romfs_dir)):
                if directory != 0xffffffff:
                    mounted.update(self._walk(directory,prefix))
            self._trees.append(mounted)

    def _walk(self, root, prefix):
        result = {}; visited = set(); aliases = set()
        stack = [(root,prefix)]
        while stack:
            directory, path = stack.pop()
            _require(directory not in visited, 'Cyclic or shared NUP directory')
            visited.add(directory)
            _,first,count = self._dirs[directory]
            raw_names = []
            for node in self._children[first:first+count]:
                isdir = node < len(self._dirs)
                name = self._dirs[node][0] if isdir else self._files[node-len(self._dirs)].name
                _require(bool(name), 'Empty NUP child name')
                child = f'{path}/{name}' if path else name
                _require(child.casefold() not in aliases and child.count('/') < 256,
                         'Duplicate or excessive-depth NUP path')
                aliases.add(child.casefold()); raw_names.append(name.encode('utf-8'))
                if isdir: stack.append((node,child))
                else: result[child] = self._files[node-len(self._dirs)]
            _require(raw_names == sorted(raw_names), 'Unsorted NUP children')
        return result

    def list_files(self, package=0):
        return dict(self._trees[package])

    @contextmanager
    def open_file(self, package, path):
        """Yield a bounded stream, validating size/hash on EOF and context exit.

        Consume streams serially: they share this reader's file handle.
        """
        member = self._trees[package][path]
        source = _Extent(self._stream,member.offset,member.stored_size)
        reader = source
        if member.codec == 1:
            import zstandard
            try:
                params = zstandard.get_frame_parameters(source.read(min(18,member.stored_size)))
                _require(params.content_size == member.size, 'NUP zstd content size mismatch')
                source = _Extent(self._stream,member.offset,member.stored_size)
                reader = zstandard.ZstdDecompressor(max_window_size=128 << 10).stream_reader(source)
            except zstandard.ZstdError as error:
                raise NupError('Invalid NUP zstd frame') from error
        verified = _VerifiedStream(reader,member)
        try:
            yield verified
            verified.check()
            _require(not verified.read(1), 'NUP member has excess decoded bytes')
        finally:
            reader.close()

    def copy_file(self, package, path, output):
        with self.open_file(package,path) as source:
            while True:
                block = source.read(1 << 20)
                if not block: break
                written = output.write(block)
                _require(written is None or written == len(block), 'Short NUP output write')

    def read_file(self, package, path, *, limit=64 << 20):
        _require(self._trees[package][path].size <= limit, 'NUP in-memory read limit')
        out = io.BytesIO(); self.copy_file(package,path,out)
        return out.getvalue()

    def verify_program(self, package, *, expected_title_id, expected_main_sha256=None,
                       expected_build_id=None):
        _require(all(path in self._trees[package] for path in ('exefs/main','exefs/main.npdm')),
                 'NUP package has no complete ExeFS program')
        # Verify the complete module while retaining only its small NSO header.
        class HeaderSink:
            def __init__(self): self.header = bytearray()
            def write(self, data):
                self.header.extend(data[:max(0,0x60-len(self.header))])
        sink = HeaderSink()
        self.copy_file(package,'exefs/main',sink)
        main = bytes(sink.header)
        npdm = self.read_file(package,'exefs/main.npdm',limit=1 << 20)
        _require(len(npdm) >= 128 and npdm[:4] == b'META', 'Invalid NUP NPDM')
        off,size = struct.unpack_from('<II',npdm,0x70)
        _require(size >= 0x40 and off >= 128 and off+size <= len(npdm)
                 and npdm[off:off+4] == b'ACI0', 'Invalid NUP ACI0')
        title = struct.unpack_from('<Q',npdm,off+16)[0]
        _require(title == expected_title_id and self.packages[package].title_id in
                 (title,title+0x800), 'Wrong NUP program title ID')
        _require(len(main) >= 0x60 and main[:4] == b'NSO0', 'Invalid NUP NSO main')
        digest = self._trees[package]['exefs/main'].sha256.hex()
        if expected_main_sha256:
            _require(digest == expected_main_sha256.lower(), 'Unsupported NUP main SHA256')
        build_id = main[0x40:0x60].hex()
        if expected_build_id:
            _require(build_id.startswith(expected_build_id.lower()), 'Unsupported NUP build ID')
        return {'title_id':f'{title:016X}','main_sha256':digest,'main_build_id':build_id}

    def extract_package(self, package, destination, *, expected_title_id=None,
                        expected_main_sha256=None, expected_build_id=None):
        """Publish a hash-verified tree into a NEW destination. Caller overlays updates.

        Without expected_title_id this verifies container integrity only. Callers
        must verify_program before importing into a playable runtime. This does
        not claim tree identity equals an original binary RomFS image.
        """
        _require(expected_title_id is not None or not (expected_main_sha256 or expected_build_id),
                 'NUP expected program hashes require a title ID')
        identity = (self.verify_program(package,expected_title_id=expected_title_id,
                                        expected_main_sha256=expected_main_sha256,
                                        expected_build_id=expected_build_id)
                    if expected_title_id is not None else {})
        destination = Path(destination).absolute()
        _require(not os.path.lexists(destination), 'NUP extraction destination exists')
        for parent in (destination.parent,*destination.parent.parents):
            info = parent.lstat()
            _require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
                     'NUP extraction path crosses reparse point')
        receipt = []
        with tempfile.TemporaryDirectory(prefix='nup-',dir=destination.parent) as tmp:
            stage = Path(tmp)/'complete'; stage.mkdir()
            for path,member in sorted(self._trees[package].items()):
                target = stage/path; target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as output: self.copy_file(package,path,output)
                receipt.append({'path':path,'size':member.size,'sha256':member.sha256.hex()})
            _require(not os.path.lexists(destination), 'NUP extraction destination appeared')
            stage.rename(destination)
        return dict(identity,files=receipt)
