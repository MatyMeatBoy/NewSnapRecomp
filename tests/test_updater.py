"""Updater integrity, repair and transactional owner-data protection."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import zipfile

from newsnap import updater


def package(files=None, extra=None):
    files = files or {'NewSnapLauncher.exe': b'new launcher', '_internal/runtime.dll': b'new runtime'}
    manifest = {'version': '0.3', 'source_revision': 'a'*40, 'contains_game_data': False,
                'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in files.items()}}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('release/MANIFEST.json', json.dumps(manifest))
        for name, data in files.items():
            archive.writestr('release/' + name, data)
        for name, data in (extra or {}).items():
            archive.writestr(name, data)
    return stream.getvalue()


class UpdaterTests(unittest.TestCase):
    def release(self):
        return updater.Release('v0.3', '0.3', 'NewSnapRecomp-0.3-windows.zip',
                               'https://github.com/MatyMeatBoy/NewSnapRecomp/releases/download/v0.3/test.zip',
                               'https://github.com/MatyMeatBoy/NewSnapRecomp/releases/download/v0.3/test.zip.sha256')

    def stage(self, root, data):
        release = self.release()
        checksum = hashlib.sha256(data).hexdigest().encode() + b'  ' + release.archive_name.encode() + b'\n'
        def download(url, path, limit):
            path.write_bytes(checksum if url == release.checksum_url else data)
        with patch.object(updater, '_download', side_effect=download):
            return updater.stage_update(release, root / 'scratch')

    def test_stable_metadata_and_no_stable(self):
        release = {'tag_name': 'v0.3', 'draft': False, 'prerelease': False, 'target_commitish': 'a'*40,
                   'assets': [{'name': 'NewSnapRecomp-0.3-windows.zip', 'browser_download_url': self.release().archive_url},
                              {'name': 'NewSnapRecomp-0.3-windows.zip.sha256', 'browser_download_url': self.release().checksum_url}]}
        with patch.object(updater, '_read_json', return_value=release):
            self.assertEqual(updater.check_stable().version, '0.3')
            release['assets'].append({'name': 'NewSnapBuildKit-0.3-windows.zip',
                                      'browser_download_url': self.release().archive_url})
            self.assertEqual(updater.check_stable().version, '0.3')
            release['assets'][-1]['name'] = 'NewSnapBuildKit-0.3-aaaaaaaa.zip'
            legacy_candidates = [a for a in release['assets'] if a['name'].endswith('.zip') and 'windows' in a['name']]
            self.assertEqual(len(legacy_candidates), 1)
            release['prerelease'] = True
            self.assertIsNone(updater.check_stable())
            release['prerelease'] = False
            release['draft'] = True
            self.assertIsNone(updater.check_stable())
        with patch.object(updater, '_read_json', side_effect=[HTTPError(updater.LATEST_URL, 404, 'no stable', {}, None),
                                                            {'full_name': 'MatyMeatBoy/NewSnapRecomp'}]):
            self.assertIsNone(updater.check_stable())
        with patch.object(updater, '_read_json', side_effect=HTTPError(updater.LATEST_URL, 403, 'rate limited', {}, None)):
            with self.assertRaises(updater.UpdateError):
                updater.check_stable()

    def test_private_repo_access_errors_are_not_no_stable(self):
        for status in (401, 403, 404):
            with self.subTest(status=status):
                inaccessible = HTTPError(updater.REPO_URL, status, 'private', {}, None)
                missing_latest = HTTPError(updater.LATEST_URL, 404, 'hidden', {}, None)
                with patch.object(updater, '_read_json', side_effect=[missing_latest, inaccessible]):
                    with self.assertRaisesRegex(updater.UpdateError, 'read access'):
                        updater.check_stable()
        with patch.object(updater, '_read_json', side_effect=HTTPError(updater.LATEST_URL, 401, 'private', {}, None)):
            with self.assertRaisesRegex(updater.UpdateError, 'token'):
                updater.check_stable()

    def test_private_assets_prefer_authenticated_api_urls(self):
        metadata = {'tag_name': 'v0.3', 'draft': False, 'prerelease': False, 'target_commitish': 'main',
                    'assets': [{'name': self.release().archive_name, 'browser_download_url': self.release().archive_url,
                                'url': updater.REPO_URL + '/releases/assets/100'},
                               {'name': self.release().archive_name + '.sha256', 'browser_download_url': self.release().checksum_url,
                                'url': updater.REPO_URL + '/releases/assets/101'}]}
        with patch.object(updater, '_read_json', return_value=metadata):
            release = updater.check_stable()
        self.assertEqual(release.archive_url, updater.REPO_URL + '/releases/assets/100')
        self.assertEqual(release.checksum_url, updater.REPO_URL + '/releases/assets/101')
        self.assertIsNone(release.source_revision)
        metadata['assets'][0]['url'] = 'https://api.github.com/repos/other/repo/releases/assets/1'
        with patch.object(updater, '_read_json', return_value=metadata):
            with self.assertRaises(updater.UpdateError):
                updater.check_stable()

    def test_authentication_is_never_forwarded_to_asset_redirects(self):
        from urllib.request import Request
        class Response(io.BytesIO):
            headers = {}
            def geturl(self):
                return 'https://release-assets.githubusercontent.com/test'
        opener = unittest.mock.Mock()
        opener.open.side_effect = lambda request, timeout: Response(b'content')
        with tempfile.TemporaryDirectory() as temp, patch.object(updater.github_auth, 'get_token', return_value='synthetic-test-token'), \
                patch.object(updater, 'build_opener', return_value=opener):
            updater._download(updater.REPO_URL + '/releases/assets/100', Path(temp) / 'asset', 100)
            request = opener.open.call_args.args[0]
            self.assertEqual(request.get_header('Authorization'), 'Bearer synthetic-test-token')
            self.assertNotIn('Authorization', request.headers)
            redirected = updater._SafeRedirect().redirect_request(request, None, 302, '', {},
                                        'https://release-assets.githubusercontent.com/asset')
            self.assertIsNone(redirected.get_header('Authorization'))
            updater._download('https://github.com/MatyMeatBoy/NewSnapRecomp/releases/download/v0.3/test.zip',
                              Path(temp) / 'public', 100)
            self.assertIsNone(opener.open.call_args.args[0].get_header('Authorization'))
            updater._download('https://api.github.com/repos/other/repo/releases/assets/1', Path(temp) / 'other', 100)
            self.assertIsNone(opener.open.call_args.args[0].get_header('Authorization'))

    def test_actual_existing_02_public_archive_stages(self):
        from newsnap.upstream import ROOT
        archive = ROOT / 'build/releases/NewSnapRecomp-0.2-alpha-windows-eca00335.zip'
        if not archive.is_file():
            self.skipTest('local public 0.2 artifact unavailable; no network download')
        release = updater.Release('v0.2-alpha', '0.2-alpha', archive.name,
                    'https://github.com/MatyMeatBoy/NewSnapRecomp/releases/download/v0.2-alpha/' + archive.name,
                    'https://github.com/MatyMeatBoy/NewSnapRecomp/releases/download/v0.2-alpha/' + archive.name + '.sha256',
                    'eca00335cbbf9a7e22bc0f87e668414a54480896')
        def download(url, path, limit):
            shutil.copyfile(archive.with_suffix('.zip.sha256') if url == release.checksum_url else archive, path)
        with tempfile.TemporaryDirectory() as temp, patch.object(updater, '_download', side_effect=download):
            staged = updater.stage_update(release, Path(temp) / 'scratch')
            self.assertTrue((staged / 'profiles/snap-2.0.1.json').is_file())
            self.assertTrue((staged / 'NewSnapLauncher.exe').is_file())
            self.assertEqual(len(json.loads((staged / 'MANIFEST.json').read_bytes())['files']), 1101)
        for name in ('profiles/owner.json', 'profiles/user/save.json', 'GameData/profiles/snap-2.0.1.json'):
            with self.assertRaises(updater.UpdateError):
                updater._public(name)

    def test_http_bounds_truncation_and_redirect_policy(self):
        class Response(io.BytesIO):
            headers = {}
            def geturl(self):
                return 'https://release-assets.githubusercontent.com/test'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'download'
            for advertised, content, limit in ((100, b'a', 200), (100, b'a', 5), (None, b'abcdef', 5)):
                response = Response(content)
                response.headers = {} if advertised is None else {'Content-Length': str(advertised)}
                opener = unittest.mock.Mock()
                opener.open.return_value = response
                with patch.object(updater, 'build_opener', return_value=opener):
                    with self.assertRaises(updater.UpdateError):
                        updater._download(self.release().archive_url, path, limit)
                path.unlink(missing_ok=True)
        with self.assertRaises(updater.UpdateError):
            updater._SafeRedirect().redirect_request(None, None, 302, '', {}, 'http://github.com/unsafe')

    def test_streaming_cancel_stops_reads_and_discards_newly_cancelled_chunk(self):
        event = threading.Event()
        class Response(io.BytesIO):
            headers = {}
            reads = 0
            def geturl(self):
                return 'https://release-assets.githubusercontent.com/test'
            def read(self, size=-1):
                self.assert_bounded = size == 1024 * 1024
                self.reads += 1
                block = super().read(size)
                if self.reads == 2:
                    event.set()
                return block
        response = Response(b'x' * (4 << 20))
        opener = unittest.mock.Mock()
        opener.open.return_value = response
        with tempfile.TemporaryDirectory() as temporary, patch.object(updater, 'build_opener', return_value=opener):
            target = Path(temporary) / 'partial'
            with self.assertRaises(updater.DownloadCancelled):
                updater._download(self.release().archive_url, target, 8 << 20, cancel_event=event)
            self.assertEqual(response.reads, 2)
            self.assertTrue(response.assert_bounded)
            self.assertEqual(target.stat().st_size, 1 << 20)
            self.assertTrue(response.closed)
            # Already-cancelled work does not open a connection or create output.
            opener.reset_mock()
            with self.assertRaises(updater.DownloadCancelled):
                updater._download(self.release().archive_url, Path(temporary) / 'new', 8 << 20, cancel_event=event)
            opener.open.assert_not_called()
            self.assertFalse((Path(temporary) / 'new').exists())

    def test_repair_preserves_owner_data_and_ini(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            staged = self.stage(root, package({'NewSnapLauncher.exe': b'new launcher', 'defaults.ini': b'new defaults'}))
            install = root / 'install'; install.mkdir()
            (install / 'NewSnapLauncher.exe').write_bytes(b'old launcher')
            (install / 'defaults.ini').write_bytes(b'my settings')
            (install / 'GameData').mkdir(); (install / 'GameData/save.bin').write_bytes(b'my save')
            for directory in ('newsnapGameData', 'profile', 'settings', 'logs'):
                (install / directory).mkdir()
                (install / directory / 'owner.txt').write_bytes(b'owner state')
            (install / 'personal.txt').write_bytes(b'keep')
            result = updater.apply_update(staged, install)
            self.assertEqual(result.version, '0.3')
            self.assertEqual((install / 'NewSnapLauncher.exe').read_bytes(), b'new launcher')
            self.assertEqual((install / 'defaults.ini').read_bytes(), b'my settings')
            self.assertEqual((install / 'GameData/save.bin').read_bytes(), b'my save')
            self.assertEqual((install / 'personal.txt').read_bytes(), b'keep')
            for directory in ('newsnapGameData', 'profile', 'settings', 'logs'):
                self.assertEqual((install / directory / 'owner.txt').read_bytes(), b'owner state')
            updater.apply_update(staged, install)  # same-version repair supported

    def test_checksum_and_archive_inventory_fail_closed(self):
        for data in (package(extra={'../escape': b'bad'}), package(extra={'release/unlisted.dll': b'bad'}),
                     package({'GameData/save.bin': b'private'}), package({'newsnap.exe': b'private'}),
                     package({'_internal/../../escape': b'bad'})):
            with self.subTest(data=hashlib.sha256(data).hexdigest()), tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(updater.UpdateError):
                    self.stage(Path(temp), data)
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(updater, '_download', side_effect=lambda url, path, limit: path.write_bytes(b'corrupt')):
                with self.assertRaises(updater.UpdateError):
                    updater.stage_update(self.release(), Path(temp) / 'scratch')

    def test_apply_revalidates_and_rejects_overlap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); staged = self.stage(root, package())
            with self.assertRaises(updater.UpdateError):
                updater.apply_update(staged, staged / 'nested')
            (staged / 'NewSnapLauncher.exe').write_bytes(b'tampered')
            with self.assertRaises(updater.UpdateError):
                updater.apply_update(staged, root / 'install')
            self.assertFalse((root / 'install').exists())

    def test_manifest_hash_damage_and_existing_staging_are_rejected(self):
        data = package()
        stream = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(stream, 'w') as target:
            for member in source.infolist():
                content = source.read(member)
                if member.filename.endswith('NewSnapLauncher.exe'):
                    content = b'BAD launcher'  # same length, valid ZIP CRC, wrong manifest hash
                target.writestr(member, content)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(updater.UpdateError):
                self.stage(root, stream.getvalue())
            self.assertFalse((root / 'scratch').exists())
            (root / 'scratch').mkdir()
            (root / 'scratch/keep.txt').write_text('mine')
            with self.assertRaises(updater.UpdateError):
                self.stage(root, data)
            self.assertEqual((root / 'scratch/keep.txt').read_text(), 'mine')

    def test_archive_symlinks_and_case_duplicates_are_rejected(self):
        for attack in ('symlink', 'case'):
            data = package()
            stream = io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(stream, 'w') as target:
                for member in source.infolist():
                    content = source.read(member)
                    if attack == 'symlink' and member.filename.endswith('NewSnapLauncher.exe'):
                        member.create_system = 3
                        member.external_attr = 0o120777 << 16
                    target.writestr(member, content)
                if attack == 'case':
                    target.writestr('release/NEWSNAPLAUNCHER.EXE', b'collision')
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(updater.UpdateError):
                    self.stage(Path(temp), stream.getvalue())

    def test_destination_reparse_points_rejected_before_mutation(self):
        # Windows junctions and symlinks share FILE_ATTRIBUTE_REPARSE_POINT.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real_lstat = Path.lstat
            def reparse(path, *args, **kwargs):
                info = real_lstat(path, *args, **kwargs)
                if path == root:
                    return unittest.mock.Mock(st_mode=info.st_mode, st_file_attributes=0x400)
                return info
            with patch.object(Path, 'lstat', reparse):
                with self.assertRaises(updater.UpdateError):
                    updater._no_links(root / 'runtime.dll')

    def test_transaction_rolls_back_on_mid_install_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); staged = self.stage(root, package())
            install = root / 'install'; install.mkdir()
            (install / 'NewSnapLauncher.exe').write_bytes(b'old launcher')
            original_replace = updater.os.replace
            calls = 0
            def fail_second_file(source, destination):
                nonlocal calls
                if str(source).endswith('.new'):
                    calls += 1
                    if calls == 2:
                        raise OSError('injected full disk')
                return original_replace(source, destination)
            with patch.object(updater.os, 'replace', side_effect=fail_second_file):
                with self.assertRaises(updater.UpdateError):
                    updater.apply_update(staged, install)
            self.assertEqual((install / 'NewSnapLauncher.exe').read_bytes(), b'old launcher')
            self.assertFalse((install / '_internal/runtime.dll').exists())
            self.assertFalse((install / 'MANIFEST.json').exists())

    def test_url_policy(self):
        for url in ('http://github.com/file', 'https://evil.example/file', 'https://github.com.evil.example/file',
                    'https://user@github.com/file', 'https://github.com:444/file'):
            with self.assertRaises(updater.UpdateError):
                updater._validate_url(url)


if __name__ == '__main__':
    unittest.main()
