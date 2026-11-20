import hashlib
import io
from pathlib import Path
import struct
import tempfile
import threading
import unittest

from newsnap.nup_import import import_nup
from newsnap.romfs_normalized import stream_image

TITLE = 0x0100F4300BF2C000


def modules(tag=b'supported'):
    main = bytearray(256); main[:4] = b'NSO0'; main[0x40:0x60] = bytes(range(32))
    main[128:128+len(tag)] = tag
    npdm = bytearray(192); npdm[:4] = b'META'
    struct.pack_into('<II',npdm,0x70,128,64); npdm[128:132] = b'ACI0'
    struct.pack_into('<Q',npdm,144,TITLE)
    return {'exefs/main':bytes(main),'exefs/main.npdm':bytes(npdm),
            'exefs/rtld':b'rtld','exefs/sdk':b'sdk'}


def pack_nup(packages):
    """Own synthetic v1 fixture writer; no third-party tool or game assets."""
    dirs = []; file_rows = []; pkg_rows = []
    for package in packages:
        payloads = package['files']; paths = {''}
        for path in payloads:
            bits = path.split('/')[:-1]
            for n in range(1,len(bits)+1): paths.add('/'.join(bits[:n]))
        paths = sorted(paths,key=lambda p:p.encode())
        lookup = {p:len(dirs)+i for i,p in enumerate(paths)}; root = lookup['']
        pkg_rows.append((package,root,lookup.get('exefs',0xffffffff),lookup.get('romfs',0xffffffff)))
        for path in paths: dirs.append((path,lookup,payloads))
        for path,data in sorted(payloads.items()): file_rows.append((root,path,data))
    pool = bytearray()
    def label(name):
        data = name.encode(); result = (len(pool),len(data)); pool.extend(data); return result
    labels_d = [label(path.rsplit('/',1)[-1]) for path,_,_ in dirs]
    labels_f = [label(path.rsplit('/',1)[-1]) for _,path,_ in file_rows]
    children = []; ranges = []
    for path,lookup,payloads in dirs:
        root = lookup['']; kids = []
        for sub,node in lookup.items():
            if sub and sub.rpartition('/')[0] == path: kids.append((sub.rsplit('/',1)[-1],node))
        for i,(r,file,_) in enumerate(file_rows):
            if r == root and file.rpartition('/')[0] == path:
                kids.append((file.rsplit('/',1)[-1],len(dirs)+i))
        start = len(children); children.extend(node for _,node in sorted(kids))
        ranges.append((start,len(kids)))
    fixed = 48+len(packages)*64+len(dirs)*24+len(file_rows)*80+len(children)*4
    blob = (128+fixed+len(pool)+15)//16*16
    toc = struct.pack('<4sIQQQQQ',b'TOC\x01',len(packages),len(dirs),len(file_rows),fixed,len(pool),0)
    for package,root,ex,rom in pkg_rows:
        toc += struct.pack('<QIIIIBBHIQI20x',package.get('title_id',TITLE),root,ex,rom,
                           package.get('version',0),package.get('kind',0),package.get('flags',0),0,0,0,0)
    for ref,extent in zip(labels_d,ranges): toc += struct.pack('<IIIIQ',*ref,*extent,0)
    payload = bytearray()
    for ref,(_,_,data) in zip(labels_f,file_rows):
        while (blob+len(payload))%16: payload.append(0)
        off = blob+len(payload) if data else 0
        toc += struct.pack('<IIQQQ32sBBH12x',*ref,len(data),off,len(data),hashlib.sha256(data).digest(),0,0,0)
        payload.extend(data)
    toc += struct.pack(f'<{len(children)}I',*children)+pool
    header = struct.pack('<4sHHQQ32sQQII16s32s',b'NUP\x01',128,1,128,len(toc),
                         hashlib.sha256(toc).digest(),blob,blob+len(payload),len(packages),0,bytes(16),bytes(32))
    return header+toc+bytes(blob-128-len(toc))+payload


class NupImportTests(unittest.TestCase):
    def setup_case(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name); supported = modules()
        profile = {'main_sha256':hashlib.sha256(supported['exefs/main']).hexdigest(),
                   'main_build_id':bytes(range(20)).hex(),
                   'exefs_sha256':{p.split('/')[-1]:hashlib.sha256(v).hexdigest() for p,v in supported.items()}}
        romfs = {'asset.bin':b'updated asset','keep.bin':b'base asset'}
        manifest = {'version':1,'layout':'newsnap-romfs-v1','files':[
            {'path':p,'size':len(v),'sha256':hashlib.sha256(v).hexdigest()} for p,v in sorted(romfs.items())]}
        manifest['normalized'] = stream_image(manifest,lambda p:io.BytesIO(romfs[p]),io.BytesIO())
        profile['romfs_normalized'] = manifest['normalized']
        packages = [
            {'kind':0,'version':0,'files':dict(modules(b'base'),**{'romfs/asset.bin':b'old asset','romfs/keep.bin':b'base asset'})},
            {'kind':1,'version':2,'files':dict(supported,**{'romfs/asset.bin':b'updated asset'})},
            {'kind':1,'version':3,'files':dict(modules(b'unsupported newer'),**{'romfs/asset.bin':b'wrong newer asset'})}]
        return root,profile,manifest,packages

    def test_supported_update_overlays_base_and_excludes_newer(self):
        root,profile,manifest,packages = self.setup_case()
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        updated = import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        self.assertEqual(updated,root/'work/updated')
        self.assertEqual(hashlib.sha256((updated/'romfs/romfs.bin').read_bytes()).hexdigest(),manifest['normalized']['sha256'])
        self.assertEqual((updated/'exefs/main').read_bytes(),modules()['exefs/main'])
        self.assertTrue((updated/'nup-import.json').is_file())

    def test_missing_extra_or_changed_romfs_never_publishes(self):
        for mutation in ('missing','extra','changed'):
            with self.subTest(mutation=mutation):
                root,profile,manifest,packages = self.setup_case()
                if mutation == 'missing': del packages[0]['files']['romfs/keep.bin']
                elif mutation == 'extra': packages[1]['files']['romfs/extra.bin'] = b'extra'
                else: packages[1]['files']['romfs/asset.bin'] = b'changed asset'
                source = root/'game.nup'; source.write_bytes(pack_nup(packages))
                with self.assertRaises(ValueError):
                    import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
                self.assertFalse((root/'work/updated').exists())

    def test_unknown_code_module_rejected(self):
        root,profile,manifest,packages = self.setup_case()
        packages[1]['files']['exefs/subsdk9'] = b'unexpected module'
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        with self.assertRaises(ValueError):
            import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        self.assertFalse((root/'work/updated').exists())

    def test_cancelled_import_never_publishes(self):
        root,profile,manifest,packages = self.setup_case()
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        cancel = threading.Event(); cancel.set()
        with self.assertRaises(ValueError):
            import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None,cancel=cancel)
        self.assertFalse((root/'work/updated').exists())

    def test_wrong_supported_main_rejected(self):
        root,profile,manifest,packages = self.setup_case()
        packages[1]['files']['exefs/main'] = modules(b'wrong main')['exefs/main']
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        with self.assertRaises(ValueError):
            import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        self.assertFalse((root/'work/updated').exists())

    def test_payload_hash_checked_beyond_untrusted_toc_hashes(self):
        root,profile,manifest,packages = self.setup_case()
        data = bytearray(pack_nup(packages))
        pos = data.index(b'updated asset'); data[pos] ^= 1
        source = root/'game.nup'; source.write_bytes(data)
        with self.assertRaisesRegex(ValueError,'SHA256'):
            import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        self.assertFalse((root/'work/updated').exists())
        self.assertEqual(list((root/'work').iterdir()),[])

    def test_cancel_during_streaming_leaves_no_published_image(self):
        root,profile,manifest,packages = self.setup_case()
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        cancel = threading.Event()
        def report(message):
            if 'canonical image' in message: cancel.set()
        with self.assertRaisesRegex(ValueError,'cancelled'):
            import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=report,cancel=cancel)
        self.assertFalse((root/'work/updated').exists())

    def test_complete_standalone_update_is_supported(self):
        root,profile,manifest,packages = self.setup_case()
        update = packages[1]
        update['files']['romfs/keep.bin'] = b'base asset'
        update.update(flags=1,title_id=TITLE+0x800)
        source = root/'game.nup'; source.write_bytes(pack_nup([update]))
        result = import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        self.assertTrue((result/'romfs/romfs.bin').is_file())

    def test_existing_destination_remains_untouched(self):
        root,profile,manifest,packages = self.setup_case()
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        updated = root/'work/updated'; updated.mkdir(parents=True)
        sentinel = updated/'owner-sentinel'; sentinel.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError,'exists'):
            import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        self.assertEqual(sentinel.read_bytes(),b'keep')

    def test_bundled_manifest_pin_is_enforced(self):
        from unittest.mock import patch
        import json
        from newsnap import nup_import as N
        root,profile,manifest,packages = self.setup_case()
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        recipe_path = root/'assets/game-fingerprints/synthetic-files.json'; recipe_path.parent.mkdir(parents=True)
        data = json.dumps(manifest).encode(); recipe_path.write_bytes(data)
        profile['romfs_normalized'].update(manifest='assets/game-fingerprints/synthetic-files.json',
                                          manifest_sha256=hashlib.sha256(data).hexdigest())
        with patch.object(N,'ROOT',root):
            result = import_nup(source,root/'work',profile=profile,report=lambda _:None)
            self.assertTrue((result/'nup-import.json').is_file())
            recipe_path.write_bytes(data+b' ')
            with self.assertRaisesRegex(ValueError,'manifest SHA256'):
                import_nup(source,root/'work2',profile=profile,report=lambda _:None)

    def test_update_record_may_use_patch_id_but_program_uses_base_id(self):
        root,profile,manifest,packages = self.setup_case()
        packages[1]['title_id'] = TITLE+0x800
        source = root/'game.nup'; source.write_bytes(pack_nup(packages))
        result = import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
        import json
        receipt = json.loads((result/'nup-import.json').read_text())
        self.assertEqual(receipt['overlay_packages'],[0,1])

    def test_foreign_program_or_record_identity_is_rejected(self):
        for forged in ('npdm','package'):
            with self.subTest(forged=forged):
                root,profile,manifest,packages = self.setup_case()
                if forged == 'npdm':
                    npdm = bytearray(packages[1]['files']['exefs/main.npdm'])
                    struct.pack_into('<Q',npdm,144,TITLE+0x10000)
                    packages[1]['files']['exefs/main.npdm'] = bytes(npdm)
                else:
                    packages[1]['title_id'] = TITLE+0x10000
                source = root/'game.nup'; source.write_bytes(pack_nup(packages))
                with self.assertRaises(ValueError):
                    import_nup(source,root/'work',profile=profile,expected_manifest=manifest,report=lambda _:None)
                self.assertFalse((root/'work/updated').exists())
