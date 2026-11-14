"""Closed Windows packages carry an exact, independently verified offline kit."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import package_windows_release as package
from newsnap.upstream import COMMIT


class OfflineKitPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.revision='a'*40
        self.candidate=self.root/'build/launcher-dist/NewSnapLauncher'
        self.candidate.mkdir(parents=True)
        (self.candidate/'NewSnapLauncher.exe').write_bytes(b'public frozen launcher')
        (self.candidate/'launcher-build.json').write_text(json.dumps({'inputs':{'source':'pin'}}))
        self.releases=self.root/'build/releases'
        self.releases.mkdir(parents=True)
        self.name=f'NewSnapBuildKit-{package.VERSION}-{self.revision[:8]}.zip'
        for name,value in [('ROOT',self.root),('source_fingerprints',lambda:{'source':'pin'})]:
            context=patch.object(package,name,value)
            context.start();self.addCleanup(context.stop)
        context=patch.object(package.subprocess,'run',return_value=type('Result',(),{'returncode':0})())
        context.start();self.addCleanup(context.stop)
        context=patch.object(package.subprocess,'check_output',return_value=self.revision+'\n')
        context.start();self.addCleanup(context.stop)

    def make_kit(self,changes=None,extra=None,damage=False):
        files={name:b'public tool source' for name in (
            'python/python.exe','source/newsnap/maintenance.py','source/newsnap/build.py',
            'source/third_party/astral/tools/build_game.py','sdk/llvm/bin/clang.exe','sdk/bin/ninja.exe')}
        if extra:files.update(extra)
        manifest={'format':1,'runtime_version':package.VERSION,'runtime_api':package.RUNTIME_API,
            'capabilities':list(package.RUNTIME_CAPABILITIES),'source_revision':self.revision,
            'donor_commit':COMMIT,'contains_game_data':False,
            'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
        manifest.update(changes or {})
        archive=self.releases/self.name
        with zipfile.ZipFile(archive,'w') as output:
            for name,data in files.items():
                output.writestr(self.name[:-4]+'/'+name,data+b'damaged' if damage else data)
            output.writestr(self.name[:-4]+'/build-kit.json',json.dumps(manifest))
        archive.with_suffix('.zip.sha256').write_text(package.digest(archive)+'  '+self.name+'\n')
        return archive

    def test_exact_nested_archive_and_sidecar_are_manifest_pinned(self):
        kit=self.make_kit()
        archive=package.package()
        destination=archive.with_suffix('')
        manifest=json.loads((destination/'MANIFEST.json').read_text())
        for name in [self.name,self.name+'.sha256']:
            relative='build-kits/'+name
            source=self.releases/name
            self.assertEqual((destination/relative).read_bytes(),source.read_bytes())
            self.assertEqual(manifest['files'][relative],{'size':source.stat().st_size,'sha256':package.digest(source)})
        self.assertFalse(any('llvm/' in name or 'python/' in name for name in manifest['files']))
        self.assertTrue(kit.exists())

    def test_missing_kit_fails_before_destination_creation(self):
        with self.assertRaises((ValueError,FileNotFoundError)):
            package.package()
        self.assertEqual(list(self.releases.glob('NewSnapRecomp-*')),[])

    def test_wrong_identity_private_and_damaged_inputs_fail_closed(self):
        cases=[({'source_revision':'b'*40},None,False),
               ({'runtime_version':'0.0.1'},None,False),
               ({'runtime_api':999},None,False),
               ({'capabilities':[]},None,False),
               ({'donor_commit':'b'*40},None,False),
               ({'contains_game_data':True},None,False),
               ({},{'source/generated/main.c':b'private'},False),
               ({},{'source/GameData/exefs/main':b'private'},False),
               ({},None,True)]
        for changes,extra,damage in cases:
            with self.subTest(changes=changes,extra=extra,damage=damage):
                self.make_kit(changes,extra,damage)
                with self.assertRaises((ValueError,package.updater.UpdateError,zipfile.BadZipFile)):
                    package.package()
                self.assertEqual(list(self.releases.glob('NewSnapRecomp-*')),[])

    def test_wrong_sidecar_and_unlisted_member_fail(self):
        archive=self.make_kit()
        sidecar=archive.with_suffix('.zip.sha256')
        sidecar.write_text('0'*64+'  '+self.name+'\n')
        with self.assertRaises(ValueError):package.package()
        with zipfile.ZipFile(archive,'a') as output:
            output.writestr(self.name[:-4]+'/source/extra.py',b'unlisted')
        sidecar.write_text(package.digest(archive)+'  '+self.name+'\n')
        with self.assertRaises(ValueError):package.package()

    def test_unsafe_members_and_missing_required_tool_fail(self):
        for member in ['../escape', self.name[:-4]+'/source/../escape',
                       'AnotherKit/source/a.py',self.name[:-4]+'/build-kit.json']:
            with self.subTest(member=member):
                archive=self.make_kit()
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore',UserWarning)
                    with zipfile.ZipFile(archive,'a') as output:
                        output.writestr(member,b'unlisted')
                archive.with_suffix('.zip.sha256').write_text(package.digest(archive)+'  '+self.name+'\n')
                with self.assertRaises((ValueError,package.updater.UpdateError)):
                    package.package()
        self.make_kit({'files':{}})
        with self.assertRaises((ValueError,package.updater.UpdateError)):package.package()

    def test_existing_assets_and_frozen_fingerprint_remain_protected(self):
        self.make_kit()
        (self.candidate/'launcher-build.json').write_text(json.dumps({'inputs':{'stale':'pin'}}))
        with self.assertRaisesRegex(ValueError,'Stale launcher'):
            package.package()
        (self.candidate/'launcher-build.json').write_text(json.dumps({'inputs':{'source':'pin'}}))
        destination=self.releases/f'NewSnapRecomp-{package.VERSION}-windows-{self.revision[:8]}'
        destination.mkdir()
        (destination/'sentinel').write_bytes(b'old immutable asset')
        with self.assertRaises(FileExistsError):package.package()
        self.assertEqual((destination/'sentinel').read_bytes(),b'old immutable asset')

    def test_size_bounds_reject_without_overwriting_assets(self):
        self.make_kit()
        with patch.object(package,'MAX_PACKAGE_BYTES',10):
            with self.assertRaisesRegex(ValueError,'limit'):package.package()
        self.assertEqual(list(self.releases.glob('NewSnapRecomp-*')),[])
        with patch.object(package,'MAX_PACKAGE_EXPANDED_BYTES',10):
            with self.assertRaisesRegex(ValueError,'2 GiB'):package.package()
        self.assertFalse(list(self.releases.glob('NewSnapRecomp-*.zip')))


if __name__=='__main__':unittest.main()
