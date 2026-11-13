import unittest
from unittest.mock import patch

from newsnap import updater
from newsnap.update_versions import newer


class UpdateVersionTests(unittest.TestCase):
    def test_auto_only_notifies_strictly_newer_stable_version(self):
        for candidate,current,expected in [('0.4.0','0.4.0-alpha',True),('0.4.0','0.4.0',False),
                ('0.4.0','0.5.0-dev',False),('0.4.1','0.4.0',True),('v0.10.0','0.9.9',True),
                ('0.4.0-alpha.10','0.4.0-alpha.2',True),('latest','0.4.0',False),
                ('0.4.0','unknown',False),('0.4.0-alpha','0.4.0',False)]:
            with self.subTest(candidate=candidate,current=current):self.assertEqual(newer(candidate,current),expected)

    def test_manual_catalog_accepts_alpha_and_same_version_without_weakening_assets(self):
        base=updater._ASSET_PREFIX+'v0.4.0-alpha/'
        release={'tag_name':'v0.4.0-alpha','draft':False,'prerelease':True,
            'assets':[{'name':name,'browser_download_url':base+name} for name in
                ('NewSnapRecomp-0.4.0-alpha-windows-test.zip','NewSnapRecomp-0.4.0-alpha-windows-test.zip.sha256')]}
        self.assertIsNone(updater.parse_release(release,stable_only=True))
        with patch.object(updater,'_read_json',return_value=[release,dict(release,draft=True),{'draft':False}]):
            values=updater.list_releases()
        self.assertEqual([v.version for v in values],['0.4.0-alpha'])
        release['assets'][0]['browser_download_url']='https://untrusted.example/update.zip'
        with self.assertRaises(updater.UpdateError):updater.parse_release(release)
