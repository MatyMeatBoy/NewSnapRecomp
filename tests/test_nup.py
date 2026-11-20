import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from newsnap.nup import NupReader, NupError


def fixture(payload=b'game fixture', name=b'asset.bin', codec=0):
    stored = payload
    if codec == 1:
        import zstandard
        stored = zstandard.ZstdCompressor().compress(payload)
    pool = b'romfs' + name
    toc_size = 48 + 64 + 48 + 80 + 8 + len(pool)
    blob = (128 + toc_size + 15) // 16 * 16
    toc = struct.pack('<4sIQQQQQ', b'TOC\x01', 1, 2, 1, toc_size-len(pool), len(pool), 0)
    toc += struct.pack('<QIIIIBBHIQI20x', 0x0100F4300BF2C000, 0, 0xffffffff, 1, 0, 0, 0, 0, 0, 0, 0)
    toc += struct.pack('<IIIIQ', 0, 0, 0, 1, 0) + struct.pack('<IIIIQ', 0, 5, 1, 1, 0)
    toc += struct.pack('<IIQQQ32sBBH12x', 5, len(name), len(payload), blob if payload else 0,
                       len(stored) if payload else 0, hashlib.sha256(payload).digest(), codec, 0, 0)
    toc += struct.pack('<II', 1, 2) + pool
    header = struct.pack('<4sHHQQ32sQQII16s32s', b'NUP\x01',128,1,128,len(toc),
                         hashlib.sha256(toc).digest(),blob,blob+len(stored),1,0,bytes(16),bytes(32))
    return header + toc + bytes(blob-128-len(toc)) + stored


def program_fixture(*, title_id=0x0100F4300BF2C000, build_id=bytes(range(32))):
    main = bytearray(256); main[:4] = b'NSO0'; main[0x40:0x60] = build_id
    npdm = bytearray(192); npdm[:4] = b'META'
    struct.pack_into('<II',npdm,0x70,128,64)
    npdm[128:132] = b'ACI0'; struct.pack_into('<Q',npdm,144,title_id)
    contents = [(b'main',bytes(main)),(b'main.npdm',bytes(npdm)),(b'asset.bin',b'asset')]
    names = [b'',b'exefs',b'romfs']+[n for n,_ in contents]
    pool = b''; refs = []
    for name in names:
        refs.append((len(pool),len(name))); pool += name
    fixed = 48+64+3*24+3*80+5*4
    blob = (128+fixed+len(pool)+15)//16*16
    toc = struct.pack('<4sIQQQQQ',b'TOC\x01',1,3,3,fixed,len(pool),0)
    toc += struct.pack('<QIIIIBBHIQI20x',title_id,0,1,2,0,0,0,0,0,0,0)
    for i,(first,count) in enumerate([(0,2),(2,2),(4,1)]):
        toc += struct.pack('<IIIIQ',*refs[i],first,count,0)
    payload = bytearray()
    for i,(_,data) in enumerate(contents):
        while (blob+len(payload))%16: payload.append(0)
        off = blob+len(payload)
        toc += struct.pack('<IIQQQ32sBBH12x',*refs[3+i],len(data),off,len(data),
                           hashlib.sha256(data).digest(),0,0,0)
        payload += data
    toc += struct.pack('<5I',1,2,3,4,5)+pool
    header = struct.pack('<4sHHQQ32sQQII16s32s',b'NUP\x01',128,1,128,len(toc),
                         hashlib.sha256(toc).digest(),blob,blob+len(payload),1,0,bytes(16),bytes(32))
    return header+toc+bytes(blob-128-len(toc))+payload, hashlib.sha256(main).hexdigest()


class NupTests(unittest.TestCase):
    def reader(self, data, **limits):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / 'sample.nup'
        path.write_bytes(data)
        return NupReader(path, **limits)

    def test_raw_member_verified(self):
        with self.reader(fixture()) as r:
            self.assertEqual(r.packages[0].title_id, 0x0100F4300BF2C000)
            self.assertEqual(r.read_file(0, 'romfs/asset.bin'), b'game fixture')

    def test_zstd_member_verified(self):
        with self.reader(fixture(b'compressed fixture' * 1000, codec=1)) as r:
            self.assertEqual(r.read_file(0, 'romfs/asset.bin'), b'compressed fixture' * 1000)

    def test_bad_toc_hash_rejected(self):
        data = bytearray(fixture()); data[150] ^= 1
        with self.assertRaisesRegex(NupError, 'TOC'):
            self.reader(data)

    def test_bad_member_hash_rejected(self):
        data = bytearray(fixture()); data[-1] ^= 1
        with self.reader(data) as r, self.assertRaisesRegex(NupError, 'SHA'):
            r.read_file(0, 'romfs/asset.bin')

    def test_unsafe_names_rejected(self):
        for name in (b'../escape', b'CON', b'asset:stream', b'asset.', b'\\evil', b''):
            with self.subTest(name=name), self.assertRaises(NupError):
                self.reader(fixture(name=name))

    def test_limits_checked_before_member_read(self):
        with self.assertRaisesRegex(NupError, 'limit'):
            self.reader(fixture(), max_file_size=2)

    def test_staged_extraction_has_verified_receipt(self):
        with self.reader(fixture()) as r, tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'tree'
            receipt = r.extract_package(0, dest)
            self.assertEqual((dest / 'romfs/asset.bin').read_bytes(), b'game fixture')
            self.assertEqual(receipt['files'][0]['sha256'], hashlib.sha256(b'game fixture').hexdigest())

    def test_failed_extraction_does_not_publish_partial_tree(self):
        data = bytearray(fixture()); data[-1] ^= 1
        with self.reader(data) as r, tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'tree'
            with self.assertRaises(NupError):
                r.extract_package(0, dest)
            self.assertFalse(dest.exists())

    def test_exact_program_identity(self):
        data,digest = program_fixture()
        with self.reader(data) as r:
            identity = r.verify_program(0,expected_title_id=0x0100F4300BF2C000,
                                        expected_main_sha256=digest,expected_build_id='00010203')
            self.assertEqual(identity['main_sha256'],digest)
            with self.assertRaisesRegex(NupError,'SHA256'):
                r.verify_program(0,expected_title_id=0x0100F4300BF2C000,
                                 expected_main_sha256='0'*64)
            with self.assertRaisesRegex(NupError,'title'):
                r.verify_program(0,expected_title_id=42)
            with self.assertRaisesRegex(NupError,'build ID'):
                r.verify_program(0,expected_title_id=0x0100F4300BF2C000,
                                 expected_build_id='ffffffff')

    def test_identity_checked_before_extraction(self):
        data,digest = program_fixture()
        with self.reader(data) as r, tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'tree'
            with self.assertRaisesRegex(NupError,'SHA256'):
                r.extract_package(0,dest,expected_title_id=0x0100F4300BF2C000,
                                  expected_main_sha256='0'*64)
            self.assertFalse(dest.exists())
            receipt = r.extract_package(0,dest,expected_title_id=0x0100F4300BF2C000,
                                        expected_main_sha256=digest)
            self.assertEqual(receipt['main_sha256'],digest)
            self.assertEqual((dest/'romfs/asset.bin').read_bytes(),b'asset')

    def test_existing_destination_never_overwritten(self):
        with self.reader(fixture()) as r, tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(NupError,'exists'):
                r.extract_package(0,Path(tmp))

    def test_open_file_stream_requires_complete_verified_consumption(self):
        with self.reader(fixture()) as r:
            with self.assertRaisesRegex(NupError,'SHA256/size'):
                with r.open_file(0,'romfs/asset.bin') as source:
                    self.assertEqual(source.read(2),b'ga')
            with r.open_file(0,'romfs/asset.bin') as source:
                self.assertEqual(source.read(),b'game fixture')

    def test_streamed_nup_can_build_verified_normalized_image(self):
        from newsnap import romfs_normalized as R
        import io
        manifest = {'version':1,'layout':'newsnap-romfs-v1','files':[
            {'path':'asset.bin','size':12,'sha256':hashlib.sha256(b'game fixture').hexdigest()}]}
        with self.reader(fixture()) as r:
            out = io.BytesIO()
            expected = R.stream_image(manifest,lambda p:r.open_file(0,'romfs/'+p),out)
            manifest['normalized'] = expected
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)/'romfs.bin'
                self.assertEqual(R.write_image(manifest,lambda p:r.open_file(0,'romfs/'+p),target),expected)
                self.assertEqual(target.read_bytes(),out.getvalue())
