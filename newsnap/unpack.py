"""Index and decode shader archives locally using the player's own code."""
import json
import os
import struct
import zlib
from pathlib import Path

from .build import run_logged
from .drp import entries, payload
from .importer import write_json, source_digest
from .provenance import verify_import
from .upstream import ROOT


def unpack_shaders(limit=0):
    if limit < 0:
        raise ValueError('Shader sample limit must be nonnegative')
    extracted = ROOT / 'build/extracted/updated'
    manifest, _ = verify_import(extracted)
    folder = ROOT / 'build/shader-unpack'
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / ('sample' if limit else 'programs')
    output.mkdir(exist_ok=True)
    files = json.loads((extracted / 'romfs/index.json').read_text(encoding='utf-8'))['files']
    inventory, selected = [], []
    request = folder / 'requests.bin'
    with (extracted / 'romfs/romfs.bin').open('rb') as image, request.open('wb') as stream:
        stream.write(struct.pack('<3I', 0x444F534E, 1, 0))
        for archive in files:
            if not archive['path'].endswith('.drp'):
                continue
            for item in entries(image, archive['offset'], archive['size']):
                if item['extension_crc'] != '2f6d9b0b':
                    continue
                ordinal = len(selected)
                stored = payload(image, archive['offset'], item)
                stream.write(struct.pack('<5I', ordinal, len(stored), item['decompressed_size'],
                                         item['crc32'], int(item['compressed'])))
                stream.write(stored)
                selected.append(dict(item, archive=archive['path'], ordinal=ordinal))
                if limit and len(selected) >= limit:
                    break
            if limit and len(selected) >= limit:
                break
        stream.seek(8)
        stream.write(struct.pack('<I', len(selected)))
    if not selected:
        raise ValueError('No shader archives found')
    print(f'Decoding {len(selected)} shader archives using the original verified decoder', flush=True)
    exe = ROOT / 'build/updated/newsnap.exe'
    env = dict(os.environ, AC_GPU='null', NEWSNAP_OODLE_REQUESTS=str(request), NEWSNAP_OODLE_OUTPUT=str(output))
    run_logged([exe, '--boot'], folder / 'decode.log', env)
    for item in selected:
        path = output / f'{item["ordinal"]:05d}.nushdb'
        data = path.read_bytes()
        if len(data) != item['decompressed_size'] or zlib.crc32(data) != item['crc32']:
            raise ValueError(f'Decoded member {item["ordinal"]} failed verification')
        inventory.append(dict(item, decoded_size=len(data), sha256=source_digest(path)))
    write_json(output / 'manifest.json', {'source_sha256': manifest['source_sha256'], 'members': inventory})
    print(f'{len(inventory)} shader archives decoded and CRC32 verified: {output}', flush=True)
    return inventory
