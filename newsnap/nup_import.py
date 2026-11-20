"""Import supported decrypted NUP trees without weakening game verification.

This is a separate path from NCA extraction: it synthesizes a canonical RomFS
whose entire identity and individual files come from a pinned metadata recipe.
No NCA/IVFC provenance is claimed for these decrypted input files.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from .nup import NupReader
from . import romfs_normalized as normalized
from .upstream import ROOT, TITLE_ID, extractor


def _require(ok, text):
    if not ok: raise ValueError(text)


def _cancelled(cancel):
    if cancel is not None and cancel.is_set():
        raise ValueError('NUP import cancelled')


def _safe_directory(path):
    for part in (path,*path.parents):
        try: info = part.lstat()
        except FileNotFoundError: continue
        _require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
                 'NUP import path crosses a reparse point')


def _digest(path, cancel=None):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        while True:
            _cancelled(cancel)
            block = source.read(8 << 20)
            if not block: break
            digest.update(block)
    return digest.hexdigest()


def _write_json(path, data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def _manifest(profile, expected_manifest):
    recipe = profile.get('romfs_normalized',{})
    if expected_manifest is None:
        name = recipe.get('manifest')
        _require(isinstance(name,str) and name.startswith('assets/game-fingerprints/')
                 and '\\' not in name and all(p not in ('','.','..') for p in name.split('/')),
                 'Missing trusted normalized RomFS manifest path')
        expected_manifest = normalized.load_manifest(ROOT/name,recipe.get('manifest_sha256',''))
    normalized.layout(expected_manifest)
    expected = expected_manifest.get('normalized')
    _require(isinstance(expected,dict) and all(recipe.get(k) == expected.get(k) for k in ('size','sha256')),
             'Profile and trusted normalized RomFS identity disagree')
    return expected_manifest


def _select(reader, profile, title):
    relevant = [(i,p) for i,p in enumerate(reader.packages)
                if (p.kind == 0 and p.title_id == title) or
                   (p.kind == 1 and p.title_id in (title,title+0x800))]
    candidates = []
    for index,package in relevant:
        member = reader.list_files(index).get('exefs/main')
        if member and member.sha256.hex() == profile['main_sha256']:
            reader.verify_program(index,expected_title_id=title,
                                  expected_main_sha256=profile['main_sha256'],
                                  expected_build_id=profile['main_build_id'])
            candidates.append((index,package))
    _require(bool(candidates), 'NUP has no supported verified New Pokemon Snap program')
    candidates.sort(key=lambda item:(item[1].version,item[1].kind))
    selected,package = candidates[-1]
    _require(sum(p.version == package.version and p.kind == package.kind for _,p in candidates) == 1,
             'Ambiguous supported NUP program packages')
    bases = [(i,p) for i,p in relevant if p.kind == 0]
    updates = [(i,p) for i,p in relevant if p.kind == 1 and p.version <= package.version]
    if package.kind == 0:
        updates = []
    _require(len({p.version for _,p in updates}) == len(updates), 'Ambiguous NUP update versions')
    layers = bases+sorted(updates,key=lambda item:item[1].version)
    _require(any(i == selected for i,_ in layers), 'Supported NUP package not selected for overlay')
    return selected,layers


def import_nup(source, work, profile=None, expected_manifest=None, report=print, cancel=None):
    """Return newly published work/updated, or leave it absent on any failure.

    Explicit profile/manifest dictionaries are trusted caller inputs for tests or
    development. Normal launches load the bundled supported profile and pinned
    metadata. Nothing from the NUP may supply either trusted recipe.
    """
    _cancelled(cancel)
    source,work = Path(source).absolute(),Path(work).absolute()
    if profile is None:
        profile = json.loads((ROOT/'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))
    manifest = _manifest(profile,expected_manifest)
    title = int(TITLE_ID,16)
    expected_exefs = profile['exefs_sha256']
    _require(expected_exefs.get('main') == profile['main_sha256'], 'Inconsistent supported ExeFS recipe')
    _require(all(Path(name).name == name and name not in ('','.','..')
                 and '/' not in name and '\\' not in name for name in expected_exefs),
             'Unsafe supported ExeFS recipe path')
    destination = work/'updated'
    _safe_directory(work)
    _require(not os.path.lexists(destination), 'NUP import destination already exists')
    report('Verifying your NUP source and supported program')
    before = source.stat()
    source_hash = _digest(source,cancel)
    with NupReader(source) as reader:
        _cancelled(cancel)
        selected,layers = _select(reader,profile,title)
        merged = {}
        for index,package in layers:
            for path,member in reader.list_files(index).items(): merged[path] = (index,member)
        exefs = {p[len('exefs/'):]:v for p,v in merged.items() if p.startswith('exefs/')}
        _require(set(exefs) == set(expected_exefs), 'NUP ExeFS has missing or unexpected modules')
        _require(all(m.sha256.hex() == expected_exefs[name] for name,(_,m) in exefs.items()),
                 'NUP ExeFS differs from the supported module recipe')
        romfs = {p[len('romfs/'):]:v for p,v in merged.items() if p.startswith('romfs/')}
        expected_files = {f['path']:f for f in manifest['files']}
        _require(set(romfs) == set(expected_files), 'NUP RomFS has missing or unexpected files')
        _require(all(member.size == expected_files[path]['size'] and
                     member.sha256.hex() == expected_files[path]['sha256']
                     for path,(_,member) in romfs.items()), 'NUP RomFS differs from the supported file recipe')
        _safe_directory(work); work.mkdir(parents=True,exist_ok=True); _safe_directory(work)
        with tempfile.TemporaryDirectory(prefix='nup-import-',dir=work) as tmp:
            stage = Path(tmp)/'updated'; stage.mkdir()
            (stage/'exefs').mkdir(); (stage/'romfs').mkdir()
            class CheckedReader:
                def __init__(self, stream): self.stream = stream
                def read(self,size=-1):
                    _cancelled(cancel)
                    return self.stream.read(size)
            @contextmanager
            def open_member(path):
                _cancelled(cancel)
                index,_ = romfs[path]
                with reader.open_file(index,'romfs/'+path) as stream:
                    yield CheckedReader(stream)
            for name,(index,member) in sorted(exefs.items()):
                _cancelled(cancel)
                report(f'Verifying NUP module: {name}')
                with reader.open_file(index,'exefs/'+name) as incoming, (stage/'exefs'/name).open('xb') as output:
                    while True:
                        _cancelled(cancel); block = incoming.read(8 << 20)
                        if not block: break
                        output.write(block)
            report('Verifying all NUP RomFS files and building the canonical image')
            identity = normalized.write_image(manifest,open_member,stage/'romfs/romfs.bin')
            _cancelled(cancel)
            index = extractor().index_romfs(stage/'romfs/romfs.bin')
            _require({f['path']:f['size'] for f in index} == {p:f['size'] for p,f in expected_files.items()},
                     'Generated NUP RomFS index differs from trusted files')
            _write_json(stage/'romfs/index.json',{'status':'pass','romfs_size':identity['size'],
                                                'romfs_sha256':identity['sha256'],'files':index})
            index_hash = _digest(stage/'romfs/index.json',cancel)
            _write_json(stage/'romfs/import-receipt.json',{'format':'newsnap-nup-romfs-v1',
                        'sources':{'nup':source_hash},'romfs_sha256':identity['sha256'],'index_sha256':index_hash})
            receipt = {'format':'newsnap-nup-import-v1','source_sha256':source_hash,
                       'title_id':TITLE_ID,'selected_package':selected,
                       'selected_version':reader.packages[selected].version,
                       'overlay_packages':[i for i,_ in layers],
                       'exefs_sha256':expected_exefs,
                       'romfs':dict(identity,layout='newsnap-romfs-v1'),
                       'manifest_sha256':profile['romfs_normalized'].get('manifest_sha256')}
            _write_json(stage/'nup-import.json',receipt)
            after = source.stat()
            _require((before.st_size,before.st_mtime_ns,before.st_ino) ==
                     (after.st_size,after.st_mtime_ns,after.st_ino), 'NUP source changed during import')
            _cancelled(cancel)
            _require(not os.path.lexists(destination), 'NUP import destination appeared during import')
            _safe_directory(work); stage.rename(destination)
    report('NUP verified and imported')
    return destination
