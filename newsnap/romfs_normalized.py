"""Canonical, streamed RomFS construction from an independently pinned file recipe.

Only generic format metadata is synthesized. No original RomFS headers or game
assets are included here. Layout newsnap-romfs-v1 uses UTF-8 path order, single
hash buckets, 4-byte table records and 16-byte file-data alignment.
Format reference: switchbrew/libnx nx/include/switch/runtime/devices/romfs_dev.h.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import tempfile

NONE = 0xffffffff
BLOCK = 8 << 20


def _require(ok, text):
    if not ok:
        raise ValueError(text)


def _align(n, alignment):
    return (n+alignment-1)//alignment*alignment


def _validated_files(manifest):
    _require(manifest.get('version') == 1 and manifest.get('layout') == 'newsnap-romfs-v1',
             'Unsupported normalized RomFS manifest')
    files = manifest.get('files')
    _require(isinstance(files,list) and 0 < len(files) <= 500000, 'Invalid normalized file count')
    seen = set(); paths = []
    for item in files:
        path = item.get('path')
        _require(isinstance(path,str) and bool(path) and not path.startswith('/')
                 and '\\' not in path and '\0' not in path and ':' not in path
                 and all(p not in ('','.','..') for p in path.split('/'))
                 and path == str(PurePosixPath(path)), 'Unsafe normalized RomFS path')
        _require(path.casefold() not in seen, 'Duplicate normalized RomFS path')
        seen.add(path.casefold()); paths.append(path)
        _require(type(item.get('size')) is int and 0 <= item['size'] <= 16 << 30,
                 'Invalid normalized member size')
        _require(isinstance(item.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',item['sha256']),
                 'Invalid normalized member SHA256')
    _require(paths == sorted(paths,key=lambda p:p.encode('utf-8')), 'Noncanonical normalized file order')
    _require(sum(f['size'] for f in files) <= 128 << 30, 'Normalized aggregate size limit')
    return files


def load_manifest(path, expected_sha256):
    """Load metadata only after checking its independently pinned whole-file hash."""
    _require(bool(re.fullmatch('[0-9a-f]{64}',expected_sha256)), 'Invalid manifest hash pin')
    path = Path(path)
    _require(path.stat().st_size <= 64 << 20, 'Normalized manifest too large')
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == expected_sha256, 'Normalized manifest SHA256 mismatch')
    manifest = json.loads(data)
    _validated_files(manifest)
    _expected(manifest)
    return manifest


def _expected(manifest):
    expected = manifest.get('normalized',{})
    _require(type(expected.get('size')) is int and expected['size'] > 0 and
             isinstance(expected.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',expected['sha256']),
             'Missing or invalid expected normalized image identity')
    return expected


def layout(manifest):
    """Return deterministic generated tables and relative data offsets."""
    files = _validated_files(manifest)
    directories = {''}
    for item in files:
        parent = PurePosixPath(item['path']).parent
        while str(parent) != '.':
            directories.add(str(parent)); parent = parent.parent
    directories = sorted(directories,key=lambda p:p.encode('utf-8'))
    filepaths = {f['path'] for f in files}
    _require(not {p.casefold() for p in filepaths}.intersection(p.casefold() for p in directories),
             'Normalized file/directory collision')
    _require(len({p.casefold() for p in directories}) == len(directories), 'Normalized directory aliases')
    doff = {}; dsize = 0
    for path in directories:
        doff[path] = dsize
        dsize += _align(24+len(PurePosixPath(path).name.encode('utf-8')) if path else 24,4)
    foff = {}; fsize = 0; dataoff = {}; data_size = 0
    for item in files:
        path = item['path']; foff[path] = fsize
        fsize += _align(32+len(PurePosixPath(path).name.encode('utf-8')),4)
        data_size = _align(data_size,16); dataoff[path] = data_size; data_size += item['size']
    children = {p:[] for p in directories}; members = {p:[] for p in directories}
    def parent(path):
        value = str(PurePosixPath(path).parent)
        return '' if value == '.' else value
    for path in directories[1:]: children[parent(path)].append(path)
    for item in files: members[parent(item['path'])].append(item['path'])
    sibling = {}
    for group in list(children.values())+list(members.values()):
        for i,path in enumerate(group): sibling[path] = group[i+1] if i+1 < len(group) else None
    dtable = bytearray(); prev = NONE
    for path in directories:
        name = PurePosixPath(path).name.encode('utf-8') if path else b''
        record = struct.pack('<6I',doff[parent(path)] if path else 0,
                             doff[sibling[path]] if path and sibling[path] else NONE,
                             doff[children[path][0]] if children[path] else NONE,
                             foff[members[path][0]] if members[path] else NONE,prev,len(name))+name
        dtable += record+bytes(_align(len(record),4)-len(record)); prev = doff[path]
    dir_head = prev
    ftable = bytearray(); prev = NONE
    for item in files:
        path = item['path']; name = PurePosixPath(path).name.encode('utf-8')
        record = struct.pack('<IIQQII',doff[parent(path)],foff[sibling[path]] if sibling[path] else NONE,
                             dataoff[path],item['size'],prev,len(name))+name
        ftable += record+bytes(_align(len(record),4)-len(record)); prev = foff[path]
    dir_hash = 80; dir_table = dir_hash+4; file_hash = dir_table+len(dtable)
    file_table = file_hash+4; file_data = _align(file_table+len(ftable),16)
    header = struct.pack('<10Q',80,dir_hash,4,dir_table,len(dtable),file_hash,4,
                         file_table,len(ftable),file_data)
    metadata = header+struct.pack('<I',dir_head)+dtable+struct.pack('<I',prev)+ftable
    metadata += bytes(file_data-len(metadata))
    return metadata,dataoff,file_data+data_size


def stream_image(manifest, open_member, output):
    """Stream and verify every member; return whole output SHA256 and size.

    open_member(path) returns a context-managed binary stream. This function can
    be used with a discard sink to derive an expected identity without writing
    a second game image. Its result must be pinned before runtime import uses it.
    """
    metadata,offsets,total = layout(manifest)
    digest = hashlib.sha256(); count = 0
    def emit(data):
        nonlocal count
        written = output.write(data)
        _require(written is None or written == len(data), 'Short normalized output write')
        digest.update(data); count += len(data)
    emit(metadata); base = count
    for member in manifest['files']:
        gap = base+offsets[member['path']]-count
        _require(0 <= gap <= 15, 'Invalid normalized file alignment')
        if gap: emit(bytes(gap))
        actual = hashlib.sha256(); size = 0
        with open_member(member['path']) as source:
            while True:
                block = source.read(min(BLOCK,member['size']-size+1))
                if not block: break
                size += len(block)
                _require(size <= member['size'], f'Normalized member size mismatch: {member["path"]}')
                actual.update(block); emit(block)
        _require(size == member['size'] and actual.hexdigest() == member['sha256'],
                 f'Normalized member hash/size mismatch: {member["path"]}')
    _require(count == total, 'Normalized output size mismatch')
    identity = {'size':count,'sha256':digest.hexdigest()}
    if 'normalized' in manifest:
        _require(identity == _expected(manifest), 'Normalized whole-image identity mismatch')
    return identity


def write_image(manifest, open_member, destination):
    """Verify against the pinned expected image, then publish a new image atomically."""
    _expected(manifest)
    destination = Path(destination).absolute()
    _require(not os.path.lexists(destination), 'Normalized image destination exists')
    for parent in (destination.parent,*destination.parent.parents):
        info = parent.lstat()
        _require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
                 'Normalized output path crosses reparse point')
    with tempfile.TemporaryDirectory(prefix='romfs-normalized-',dir=destination.parent) as tmp:
        stage = Path(tmp)/'romfs.bin'
        with stage.open('xb') as output:
            identity = stream_image(manifest,open_member,output)
            output.flush(); os.fsync(output.fileno())
        _require(not os.path.lexists(destination), 'Normalized image destination appeared')
        stage.rename(destination)
    return identity
