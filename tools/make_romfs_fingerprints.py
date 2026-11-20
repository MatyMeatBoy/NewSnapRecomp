"""Derive public path/size/hash facts from the exact locally owned supported image.

Run as python -m tools.make_romfs_fingerprints --source-romfs PATH --output PATH.
Writes metadata only; normalized game bytes are streamed to a discard sink.
"""
import argparse
import hashlib
import json
from pathlib import Path

from newsnap.romfs_normalized import stream_image
from newsnap.upstream import extractor

SOURCE_SHA256 = 'f1c78b8e832085fc71f6d405cb7c8fa78b120565f13383aff8ead576424b513e'


class RangeReader:
    def __init__(self, path, offset, size):
        self.stream = Path(path).open('rb')
        self.stream.seek(offset)
        self.left = size

    def read(self, size=-1):
        size = self.left if size < 0 else min(size,self.left)
        data = self.stream.read(size); self.left -= len(data)
        return data

    def close(self):
        self.stream.close()

    def __enter__(self): return self
    def __exit__(self,*_): self.close()


class Discard:
    def write(self, data): return len(data)


def make_manifest(source, report=print):
    source = Path(source)
    before = source.stat()
    report('Verifying the exact original RomFS SHA256 (read only)',flush=True)
    with source.open('rb') as stream:
        digest = hashlib.file_digest(stream,'sha256').hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError('Original RomFS does not match the supported verified recipe')
    rows = extractor().index_romfs(source)
    report(f'Hashing {len(rows)} indexed members (read only)',flush=True)
    files = []
    for row in sorted(rows,key=lambda r:r['path'].encode('utf-8')):
        digest = hashlib.sha256()
        with RangeReader(source,row['offset'],row['size']) as stream:
            remaining = row['size']
            while remaining:
                block = stream.read(min(8 << 20,remaining))
                if not block: raise ValueError('Original RomFS member truncated')
                digest.update(block); remaining -= len(block)
        files.append({'path':row['path'],'size':row['size'],'sha256':digest.hexdigest()})
    manifest = {'version':1,'layout':'newsnap-romfs-v1','source_romfs_sha256':SOURCE_SHA256,
                'source_romfs_size':before.st_size,'files':files}
    lookup = {r['path']:r for r in rows}
    def open_member(path):
        row = lookup[path]
        return RangeReader(source,row['offset'],row['size'])
    report('Hashing the normalized image into a discard sink; no asset output',flush=True)
    manifest['normalized'] = stream_image(manifest,open_member,Discard())
    after = source.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino) != (after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('Original RomFS changed during metadata generation')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-romfs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    manifest = make_manifest(args.source_romfs)
    data = (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(data)
    print(json.dumps({'metadata_file':str(args.output),'metadata_sha256':hashlib.sha256(data).hexdigest(),
                      'file_count':len(manifest['files']),'normalized':manifest['normalized']},indent=2))


if __name__ == '__main__': main()
