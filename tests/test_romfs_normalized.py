import hashlib
import io
from pathlib import Path
import tempfile
import unittest

from newsnap import romfs_normalized as R
from newsnap.upstream import extractor


class NormalizedRomfs(unittest.TestCase):
    def sample(self):
        files = {'a.bin':b'root', 'dir/b.bin':b'nested payload', 'empty':b''}
        manifest = {'version':1,'layout':'newsnap-romfs-v1','files':[
            {'path':p,'size':len(v),'sha256':hashlib.sha256(v).hexdigest()}
            for p,v in sorted(files.items())]}
        return manifest,files

    def test_generated_image_indexes_and_reads_exact_files(self):
        manifest,files = self.sample()
        with tempfile.TemporaryDirectory() as tmp:
            out = io.BytesIO()
            identity = R.stream_image(manifest,lambda p:io.BytesIO(files[p]),out)
            image = Path(tmp)/'romfs.bin'; image.write_bytes(out.getvalue())
            index = extractor().index_romfs(image)
            self.assertEqual([x['path'] for x in index], sorted(files))
            for row in index:
                self.assertEqual(out.getvalue()[row['offset']:row['offset']+row['size']],files[row['path']])
            self.assertEqual(identity['sha256'],hashlib.sha256(out.getvalue()).hexdigest())
            self.assertEqual(identity['size'],len(out.getvalue()))

    def test_wrong_file_hash_rejects_without_publishing(self):
        manifest,files = self.sample()
        manifest['normalized'] = {'sha256':'0'*64,'size':1}
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'romfs.bin'
            with self.assertRaisesRegex(ValueError,'member'):
                R.write_image(manifest,lambda p:io.BytesIO(b'bad'),dest)
            self.assertFalse(dest.exists())

    def test_write_requires_expected_hash_and_checks_complete_image(self):
        manifest,files = self.sample()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'romfs.bin'
            with self.assertRaisesRegex(ValueError,'normalized'):
                R.write_image(manifest,lambda p:io.BytesIO(files[p]),dest)
            out = io.BytesIO()
            manifest['normalized'] = R.stream_image(manifest,lambda p:io.BytesIO(files[p]),out)
            R.write_image(manifest,lambda p:io.BytesIO(files[p]),dest)
            self.assertEqual(dest.read_bytes(),out.getvalue())

    def test_noncanonical_or_unsafe_paths_rejected(self):
        manifest,files = self.sample()
        manifest['files'].reverse()
        with self.assertRaisesRegex(ValueError,'canonical'):
            R.stream_image(manifest,lambda p:io.BytesIO(files[p]),io.BytesIO())
        manifest['files'] = [{'path':'../bad','size':0,'sha256':hashlib.sha256(b'').hexdigest()}]
        with self.assertRaises(ValueError):
            R.stream_image(manifest,lambda p:io.BytesIO(),io.BytesIO())

    def test_pinned_manifest_rejects_changed_metadata(self):
        import json
        manifest,files = self.sample()
        manifest['normalized'] = R.stream_image(manifest,lambda p:io.BytesIO(files[p]),io.BytesIO())
        data = json.dumps(manifest).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'recipe.json'; path.write_bytes(data)
            pin = hashlib.sha256(data).hexdigest()
            self.assertEqual(R.load_manifest(path,pin),manifest)
            path.write_bytes(data+b' ')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                R.load_manifest(path,pin)

    def test_wrong_whole_image_identity_never_publishes(self):
        manifest,files = self.sample()
        manifest['normalized'] = {'size':1,'sha256':'0'*64}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'romfs.bin'
            with self.assertRaisesRegex(ValueError,'whole-image'):
                R.write_image(manifest,lambda p:io.BytesIO(files[p]),target)
            self.assertFalse(target.exists())
