import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from newsnap import build_kit as kit
from newsnap.maintenance import MaintenanceCancelled
from newsnap.upstream import COMMIT
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES

REAL_DOWNLOAD = kit.updater._download


class BuildKitAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'installed'
        self.root.mkdir()
        self.cache = self.base / 'cache'
        self.revision = 'a' * 40
        (self.root / 'MANIFEST.json').write_text(json.dumps({'version': VERSION, 'source_revision': self.revision}))
        self.name = f'NewSnapBuildKit-{VERSION}-aaaaaaaa.zip'
        self.data = {name: b'public fixture' for name in (
            'python/python.exe', 'source/newsnap/maintenance.py', 'source/newsnap/build.py',
            'source/third_party/astral/tools/build_game.py', 'sdk/llvm/bin/clang.exe', 'sdk/bin/ninja.exe')}
        self.manifest = {'format': 1, 'runtime_version': VERSION, 'source_revision': self.revision,
                         'runtime_api': RUNTIME_API, 'capabilities': list(RUNTIME_CAPABILITIES),
                         'donor_commit': COMMIT, 'contains_game_data': False,
                         'files': {n: hashlib.sha256(b).hexdigest() for n, b in self.data.items()}}
        self.payload = self.archive()
        self.release = {'tag_name': 'v' + VERSION, 'draft': False, 'prerelease': False,
                        'target_commitish': self.revision, 'assets': [
                            {'name': self.name, 'url': kit.updater.REPO_URL + '/releases/assets/1'},
                            {'name': self.name + '.sha256', 'url': kit.updater.REPO_URL + '/releases/assets/2'}]}
        self.calls = []
        self.patches = [patch.object(kit, '_cache_root', return_value=self.cache),
                        patch.object(kit.updater, '_read_json', side_effect=self.lookup),
                        patch.object(kit.updater, '_download', side_effect=self.download),
                        patch.dict(os.environ, {'NEWSNAP_BUILD_KIT': ''})]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def archive(self, extra=None):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as output:
            for name, data in self.data.items():
                output.writestr('kit/' + name, data)
            output.writestr('kit/build-kit.json', json.dumps(self.manifest))
            if extra:
                output.writestr(*extra)
        return stream.getvalue()

    def lookup(self, url):
        self.calls.append(url)
        self.assertEqual(url, kit.updater.REPO_URL + '/releases/tags/v' + VERSION)
        return self.release

    def download(self, url, path, limit, **kwargs):
        self.calls.append(url)
        if url.endswith('/2'):
            path.write_text(hashlib.sha256(self.payload).hexdigest() + '  ' + self.name + '\n')
        else:
            path.write_bytes(self.payload)

    def test_matching_same_version_installs_and_offline_reuses_verified_cache(self):
        result = kit.ensure_build_kit(self.root)
        self.assertTrue(result.is_relative_to(self.cache))
        self.assertFalse((self.root / 'GameData').exists())
        self.assertEqual(len(self.calls), 3)
        self.calls.clear()
        self.assertEqual(kit.ensure_build_kit(self.root), result)
        self.assertEqual(self.calls, [])
        self.assertEqual(list(self.cache.glob('.build-kit-*')), [])

    def test_source_revision_mismatch_never_publishes(self):
        self.manifest['source_revision'] = 'b' * 40
        self.payload = self.archive()
        with self.assertRaisesRegex(kit.updater.UpdateError, 'revision'):
            kit.ensure_build_kit(self.root)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_archive_hash_and_extracted_file_hash_are_independent_checks(self):
        original = self.download
        def bad_sidecar(url, path, limit, **kwargs):
            if url.endswith('/2'):
                path.write_text('0' * 64 + '  ' + self.name)
            else:
                original(url, path, limit)
        with patch.object(kit.updater, '_download', side_effect=bad_sidecar):
            with self.assertRaisesRegex(kit.updater.UpdateError, 'ZIP checksum'):
                kit.ensure_build_kit(self.root)
        self.data['sdk/bin/ninja.exe'] = b'corrupt compiler tool'
        # The ZIP sidecar is now valid; the manifest still pins the original file.
        self.payload = self.archive()
        with self.assertRaisesRegex(kit.updater.UpdateError, 'extracted checksum'):
            kit.ensure_build_kit(self.root)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_release_tag_and_asset_filename_cannot_select_latest_recipe(self):
        self.release['tag_name'] = 'v999.0'
        with self.assertRaisesRegex(kit.updater.UpdateError, 'stable'):
            kit.ensure_build_kit(self.root)
        self.release['tag_name'] = 'v' + VERSION
        self.release['assets'][0]['name'] = 'NewSnapBuildKit-999-windows-aaaaaaaa.zip'
        with self.assertRaisesRegex(kit.updater.UpdateError, 'matching'):
            kit.ensure_build_kit(self.root)

    def test_bad_sidecar_fails_before_archive_and_preserves_owner_files(self):
        owner = self.root / 'GameData/save'
        owner.parent.mkdir()
        owner.write_bytes(b'owner')
        with patch.object(kit.updater, '_download', side_effect=lambda u, p, l, **kw: p.write_text('0' * 64)):
            with self.assertRaises(kit.updater.UpdateError):
                kit.ensure_build_kit(self.root)
        self.assertEqual(owner.read_bytes(), b'owner')
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_zip_escape_windows_reserved_duplicates_links_and_unlisted_rejected(self):
        link = zipfile.ZipInfo('kit/sdk/link')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for name in ('kit/../escape', 'kit/source/CON.txt', 'kit/SDK/bin/ninja.exe',
                     'kit/source/unlisted.txt', link):
            with self.subTest(name=str(name)):
                self.payload = self.archive((name, b'bad'))
                with self.assertRaises((kit.updater.UpdateError, ValueError)):
                    kit.ensure_build_kit(self.root)
                self.assertEqual(list(self.cache.iterdir()), [])
                self.assertFalse((self.base / 'escape').exists())

    def test_zip_bomb_bound_rejects_before_publication(self):
        with patch.object(kit, 'MAX_EXPANDED_BYTES', 32):
            with self.assertRaisesRegex(kit.updater.UpdateError, 'size limit'):
                kit.ensure_build_kit(self.root)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_cancellation_rolls_back_stage(self):
        event = threading.Event()
        def download(url, path, limit, **kwargs):
            self.download(url, path, limit)
            event.set()
        with patch.object(kit.updater, '_download', side_effect=download):
            with self.assertRaises(MaintenanceCancelled):
                kit.ensure_build_kit(self.root, cancel_event=event)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_actual_streaming_cancellation_removes_stage_and_preserves_previous_cache(self):
        self.cache.mkdir()
        previous = self.cache / 'previous-generation'
        previous.mkdir()
        (previous / 'kit.txt').write_bytes(b'verified prior cache')
        owner = self.root / 'GameData/save'
        owner.parent.mkdir()
        owner.write_bytes(b'owner save')
        for cancel_checksum in (False, True):
            with self.subTest(cancel_checksum=cancel_checksum):
                event = threading.Event()
                responses = []
                class Response(io.BytesIO):
                    headers = {}
                    def __init__(self, payload, cancel_after):
                        super().__init__(payload)
                        self.reads = 0
                        self.cancel_after = cancel_after
                    def geturl(self):
                        return 'https://release-assets.githubusercontent.com/fixture'
                    def read(self, size=-1):
                        self.reads += 1
                        block = super().read(size)
                        if self.reads == self.cancel_after:
                            event.set()
                        return block
                def open_response(request, timeout):
                    checksum = request.full_url.endswith('/2')
                    payload = ((hashlib.sha256(self.payload).hexdigest() + '  ' + self.name).encode()
                               if checksum else b'x' * (3 << 20))
                    after = 1 if cancel_checksum and checksum else 2 if not checksum else 999
                    response = Response(payload, after)
                    responses.append(response)
                    return response
                opener = unittest.mock.Mock()
                opener.open.side_effect = open_response
                with patch.object(kit.updater, '_download', new=REAL_DOWNLOAD), \
                        patch.object(kit.updater, 'build_opener', return_value=opener), \
                        patch.object(kit.updater.github_auth, 'get_token', return_value=None):
                    with self.assertRaises(MaintenanceCancelled):
                        kit.ensure_build_kit(self.root, cancel_event=event)
                self.assertEqual(len(responses), 1 if cancel_checksum else 2)
                self.assertEqual(responses[-1].reads, 1 if cancel_checksum else 2)
                self.assertTrue(all(response.closed for response in responses))
                self.assertEqual(list(self.cache.iterdir()), [previous])
                self.assertEqual((previous / 'kit.txt').read_bytes(), b'verified prior cache')
                self.assertEqual(owner.read_bytes(), b'owner save')

    def test_foreign_asset_and_release_revision_rejected(self):
        self.release['assets'][0]['url'] = 'https://api.github.com/repos/evil/repo/releases/assets/1'
        with self.assertRaises(kit.updater.UpdateError):
            kit.ensure_build_kit(self.root)
        self.release['target_commitish'] = 'b' * 40
        with self.assertRaisesRegex(kit.updater.UpdateError, 'revision'):
            kit.ensure_build_kit(self.root)

    def test_corrupt_cached_inventory_and_wrong_installed_version_rejected(self):
        result = kit.ensure_build_kit(self.root)
        (result / 'source/build-kit.json').write_text('{}')
        with self.assertRaisesRegex(kit.updater.UpdateError, 'exact inventory'):
            kit.ensure_build_kit(self.root)
        (self.root / 'MANIFEST.json').write_text(json.dumps({'version': '0.0', 'source_revision': self.revision}))
        with self.assertRaisesRegex(kit.updater.UpdateError, 'version/source'):
            kit.ensure_build_kit(self.root)

    def test_explicit_override_is_verified_and_never_implicit_developer_root(self):
        result = kit.ensure_build_kit(self.root)
        self.calls.clear()
        with patch.dict(os.environ, {'NEWSNAP_BUILD_KIT': str(result)}):
            self.assertEqual(kit.ensure_build_kit(self.root), result)
        self.assertFalse(self.calls)
        (result / 'sdk/bin/ninja.exe').write_bytes(b'tampered')
        with patch.dict(os.environ, {'NEWSNAP_BUILD_KIT': str(result)}):
            with self.assertRaisesRegex(ValueError, 'integrity'):
                kit.ensure_build_kit(self.root)


if __name__ == '__main__':
    unittest.main()
