"""Verified private extraction, reusing the selected upstream's NCA/IVFC reader."""
import hashlib
import json
import struct
import tempfile
from pathlib import Path

from .upstream import COMMIT, TITLE_ID, UPDATE_ID, extractor


def select_program(records, update=False):
    programs = [(r, h) for r, h in records if r['content_type'] == 0]
    if len(programs) != 1:
        raise ValueError('Expected exactly one Program NCA')
    record, header = programs[0]
    if record['title_id'] != TITLE_ID:
        raise ValueError(f'Expected New Pokémon Snap ({TITLE_ID}); got {record["title_id"]}')
    metadata = [r['title_id'] for r, _ in records if r['content_type'] == 1]
    if update and UPDATE_ID not in metadata:
        raise ValueError('Expected a New Pokémon Snap update package')
    if not update and UPDATE_ID in metadata:
        raise ValueError('Expected the base package; got an update')
    return record, header


def source_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validated_existing(source, output, manifest, *, digest=None):
    if manifest.get('source_sha256') != (digest or source_digest(source)):
        return False
    files = manifest.get('files', [])
    if not files:
        return False
    for item in files:
        name = item['name']
        if Path(name).name != name or name in ('.', '..'):
            return False
        path = output / name
        if not path.is_file() or source_digest(path) != item['sha256']:
            return False
    return True


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def import_exefs(source, keys, destination, *, update=False):
    e = extractor()
    print(f'Verifying source: {source.name}', flush=True)
    digest = source_digest(source)
    if destination.exists():
        manifest_path = destination / 'extraction-manifest.json'
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if validated_existing(source, destination / 'exefs', manifest, digest=digest):
                print(f'ExeFS verified, reused: {destination.name}', flush=True)
                return manifest
        raise ValueError(f'{destination} is stale or incomplete; use a new --work directory')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='exefs-', dir=destination.parent) as temporary:
        stage = Path(temporary) / 'complete'
        manifest = e.extract_exefs(source, keys, stage / 'exefs', update=update)
        manifest.update(source_sha256=digest, title_id=TITLE_ID, upstream_commit=COMMIT)
        write_json(stage / 'extraction-manifest.json', manifest)
        stage.rename(destination)
    print(f'ExeFS extracted and block hashes verified: {destination.name}', flush=True)
    return manifest


def import_game(base, update, keys, work, *, hactool=None, exefs_only=False):
    e = extractor()
    base, update, keys, work = (Path(p).resolve() for p in (base, update, keys, work))
    for source in (base, update, keys):
        if not source.is_file():
            raise ValueError(f'Missing input: {source.name}')
    # Validate both identities and ticket/key availability before writing output.
    tickets, inputs = e.program_ncas(base, update, keys)
    del tickets
    manifests = {}
    for tag, source in (('base', base), ('updated', update)):
        manifests[tag] = import_exefs(source, keys, work / tag, update=tag == 'updated')
    if exefs_only:
        return manifests
    if not hactool or not Path(hactool).is_file():
        raise ValueError('ExeFS is ready. Pass --hactool PATH to merge and verify the update RomFS')
    romfs = work / 'updated' / 'romfs'
    identity = {tag: m['source_sha256'] for tag, m in manifests.items()}
    if romfs.exists():
        receipt = romfs / 'import-receipt.json'
        if receipt.is_file():
            existing = json.loads(receipt.read_text(encoding='utf-8'))
            if (existing.get('sources') == identity and (romfs / 'romfs.bin').is_file()
                    and (romfs / 'index.json').is_file()
                    and source_digest(romfs / 'romfs.bin') == existing.get('romfs_sha256')
                    and source_digest(romfs / 'index.json') == existing.get('index_sha256')):
                print('Merged RomFS and index verified, reused', flush=True)
                return manifests
        raise ValueError(f'{romfs} is stale or incomplete; use a new --work directory')
    header = inputs[1][2]
    sizes = []
    for i in range(4):
        fs = header[0x400 + i * 512:0x600 + i * 512]
        if fs[4] == 4 and fs[8:12] == b'IVFC':
            sizes.append(struct.unpack_from('<Q', fs, 0x18 + 5 * 24 + 8)[0])
    if len(sizes) != 1 or not 0 < sizes[0] < 1 << 39:
        raise ValueError('Unsupported update IVFC layout')
    # Upstream deletes an existing target; pass only a fresh staging path.
    with tempfile.TemporaryDirectory(prefix='romfs-', dir=work / 'updated') as temporary:
        stage = Path(temporary) / 'complete'
        report = e.merge_update_romfs(base, update, keys, Path(hactool).resolve(), stage,
                                     work / 'logs', sizes[0],
                                     phase=lambda name: print(f'RomFS: {name}', flush=True))
        write_json(stage / 'import-receipt.json', {
            'sources': identity, 'romfs_sha256': report['romfs_sha256'],
            'index_sha256': source_digest(stage / 'index.json'), 'upstream_commit': COMMIT})
        stage.rename(romfs)
    print(f'Updated RomFS verified: {len(report["files"])} files, {report["romfs_size"]} bytes', flush=True)
    return manifests
