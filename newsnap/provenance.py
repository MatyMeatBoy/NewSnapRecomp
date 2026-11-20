"""Bind verified inputs and generated code to the exact source recipe."""
import json
from pathlib import Path

from .importer import source_digest, write_json, read_control_metadata

RECEIPT = 'generation-receipt.json'


def check_hash(path, expected):
    if not path.is_file() or source_digest(path) != expected:
        raise ValueError(f'Integrity mismatch: {path}. Import or generate again before building')


def verify_import(extracted):
    if (extracted/'nup-import.json').is_file():
        from .maintenance import verify_owner_inputs
        from .upstream import ROOT
        profile=json.loads((ROOT/'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))
        manifest,control=verify_owner_inputs(extracted,profile)
        manifest['romfs_sha256']=source_digest(extracted/'romfs/romfs.bin')
        return manifest,control
    manifests = {tag: json.loads((extracted.parent / tag / 'extraction-manifest.json').read_text(encoding='utf-8'))
                 for tag in ('base', 'updated')}
    for item in manifests['updated']['files']:
        if Path(item['name']).name != item['name'] or item['name'] in ('.', '..'):
            raise ValueError('Unsafe ExeFS manifest name')
        check_hash(extracted / 'exefs' / item['name'], item['sha256'])
    romfs = extracted / 'romfs'
    receipt = json.loads((romfs / 'import-receipt.json').read_text(encoding='utf-8'))
    if receipt.get('sources') != {tag: m['source_sha256'] for tag, m in manifests.items()}:
        raise ValueError('RomFS receipt belongs to different inputs')
    check_hash(romfs / 'romfs.bin', receipt.get('romfs_sha256'))
    check_hash(romfs / 'index.json', receipt.get('index_sha256'))
    control = extracted / 'control'
    receipt = json.loads((control / 'receipt.json').read_text(encoding='utf-8'))
    if receipt.get('source_sha256') != manifests['updated']['source_sha256']:
        raise ValueError('Control metadata belongs to a different update')
    return manifests['updated'], read_control_metadata(control)


def generation_recipe(source, manifest, patches=None):
    files = sorted((source / 'recomp').rglob('*.py')) + sorted((source / 'tools').glob('*.py'))
    return {'exefs': {f['name']: f['sha256'] for f in manifest['files']},
            'generator': {p.relative_to(source).as_posix(): source_digest(p) for p in files},
            'version': 'snap', 'modules': 'main,sdk',
            'patches': {'name': Path(patches).name, 'sha256': source_digest(patches)} if patches else None}


def output_hashes(generated):
    return {p.relative_to(generated).as_posix(): source_digest(p)
            for p in sorted(generated.rglob('*'))
            if p.is_file() and p.suffix in ('.c', '.h', '.json') and p.name != RECEIPT}


def record_generation(generated, recipe):
    outputs = output_hashes(generated)
    if not outputs or not (generated / 'layout.json').is_file():
        raise ValueError('Generation produced no layout or sources')
    write_json(generated / RECEIPT, {'recipe': recipe, 'outputs': outputs})


def verify_generation(generated, recipe):
    receipt = generated / RECEIPT
    if not receipt.is_file():
        raise ValueError('No generation provenance; build once without --no-generate')
    expected = json.loads(receipt.read_text(encoding='utf-8'))
    if expected.get('recipe') != recipe or expected.get('outputs') != output_hashes(generated):
        raise ValueError('Stale or modified generated code; build again without --no-generate')
