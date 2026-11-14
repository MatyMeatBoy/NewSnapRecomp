import hashlib
import json
import tempfile
import threading
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from newsnap import maintenance as m
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES


class OwnerRuntimeFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'GameData'
        self.data.mkdir()
        (self.data / 'newsnap.exe').write_bytes(b'old executable')
        self.marker = {'format': 1, 'game_version': '2.0.1', 'runtime_api': RUNTIME_API,
                       'runtime_version': VERSION, 'capabilities': list(RUNTIME_CAPABILITIES),
                       'native_executable_sha256': m.digest(self.data / 'newsnap.exe')}
        self.write_marker()

    def write_marker(self):
        (self.data / 'newsnap-game.json').write_text(json.dumps(self.marker))

    def candidate(self):
        candidate = self.root / 'candidate'
        candidate.mkdir()
        (candidate / 'newsnap.exe').write_bytes(b'new executable')
        metadata = dict(self.marker, native_executable_sha256=m.digest(candidate / 'newsnap.exe'))
        (candidate / 'newsnap-game.json').write_text(json.dumps(metadata))
        return candidate


class MaintenanceTests(OwnerRuntimeFixture, TestCase):
    def test_same_version_corruption_requires_repair(self):
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        (self.data / 'newsnap.exe').write_bytes(b'corrupted')
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

    def test_missing_capability_requires_rebuild_even_same_version(self):
        self.marker['capabilities'] = []
        self.write_marker()
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

    def test_install_preserves_owner_profile_settings_and_recordings(self):
        (self.data / 'profile').mkdir()
        (self.data / 'profile/save').write_bytes(b'my save')
        (self.data / 'astralchain.ini').write_bytes(b'my settings')
        (self.data / 'shader-programs.bin').write_bytes(b'observed')
        (self.data / 'pipeline-cache.bin').write_bytes(b'old driver cache')
        m.install_candidate(self.root, self.candidate())
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'new executable')
        self.assertEqual((self.data / 'profile/save').read_bytes(), b'my save')
        self.assertEqual((self.data / 'astralchain.ini').read_bytes(), b'my settings')
        self.assertEqual((self.data / 'shader-programs.bin').read_bytes(), b'observed')
        self.assertFalse((self.data / 'pipeline-cache.bin').exists())
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])

    def test_failure_during_switch_restores_all_old_runtime_files(self):
        candidate = self.candidate()
        (self.data / 'SDL3.dll').write_bytes(b'old dll')
        (candidate / 'SDL3.dll').write_bytes(b'new dll')
        replace = Path.replace
        def fail(source, target):
            if source == candidate / 'newsnap-game.json':
                raise OSError('injected commit failure')
            return replace(source, target)
        with patch.object(Path, 'replace', fail):
            with self.assertRaisesRegex(OSError, 'injected commit failure'):
                m.install_candidate(self.root, candidate)
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'old executable')
        self.assertEqual((self.data / 'SDL3.dll').read_bytes(), b'old dll')
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])

    def test_cancel_before_commit_leaves_runtime_untouched(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(m.MaintenanceCancelled):
            m.install_candidate(self.root, self.candidate(), cancel_event=event)
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'old executable')

    def test_recovery_finishes_interrupted_switch_before_next_launch(self):
        transaction = self.data / '.runtime-transaction'
        (transaction / 'backup').mkdir(parents=True)
        (transaction / 'backup/newsnap.exe').write_bytes(b'old executable')
        (transaction / 'journal.json').write_text(json.dumps({'format': 2, 'files': {'newsnap.exe': True},
            'backup': m._backup_inventory(transaction / 'backup')}))
        (self.data / 'newsnap.exe').write_bytes(b'incomplete candidate')
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])
        self.assertTrue(m.recover_runtime(self.root))
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'old executable')

    def test_input_verification_rejects_same_size_modified_romfs(self):
        (self.data / 'exefs').mkdir()
        (self.data / 'romfs').mkdir()
        (self.data / 'exefs/main').write_bytes(b'code')
        (self.data / 'romfs/romfs.bin').write_bytes(b'romf')
        profile = {'exefs_sha256': {'main': m.digest(self.data / 'exefs/main')},
                   'romfs_sha256': hashlib.sha256(b'romf').hexdigest(),
                   'verified_control': {'display_version': '2.0.1', 'save_size': 42, 'journal_size': 2}}
        self.assertEqual(m.verify_owner_inputs(self.data, profile)[1]['save_size'], 42)
        for module in ('sdk','subsdk0','subsdk9'):
            extra=self.data/'exefs'/module
            extra.write_bytes(b'unverified module')
            with self.assertRaisesRegex(ValueError,'Unexpected ExeFS module'):
                m.verify_owner_inputs(self.data,profile)
            extra.unlink()
        (self.data / 'romfs/romfs.bin').write_bytes(b'evil')
        with self.assertRaisesRegex(ValueError, 'RomFS'):
            m.verify_owner_inputs(self.data, profile)

    def test_candidate_cannot_replace_profile(self):
        candidate = self.candidate()
        (candidate / 'profile').mkdir()
        (candidate / 'profile/save').write_bytes(b'bad save')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            m.install_candidate(self.root, candidate)
        self.assertFalse((self.data / 'profile').exists())

class BuildOwnerTests(TestCase):
    def test_owner_build_rejects_unverified_input_before_generation(self):
        from newsnap import build as builder
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'profiles').mkdir()
            profile = {'exefs_sha256': {'main': '0' * 64}, 'romfs_sha256': '0' * 64,
                       'verified_control': {'display_version': '2.0.1', 'save_size': 42, 'journal_size': 2}}
            (root / 'profiles/snap-2.0.1.json').write_text(json.dumps(profile))
            (root / 'owner/exefs').mkdir(parents=True)
            (root / 'owner/exefs/main').write_bytes(b'modified')
            # This fixture tests owner verification; tool integrity has its own real fixtures.
            with patch.object(builder, 'ROOT', root), patch.object(builder, 'verify_translator'):
                with self.assertRaisesRegex(ValueError, 'ExeFS main'):
                    builder.build(root / 'sdk', owner_data=root / 'owner', work_dir=root / 'work')
            self.assertFalse((root / 'work/generated').exists())

class KitAndProcessTests(TestCase):
    def test_cancellation_stops_owned_writer_before_returning(self):
        import sys
        import time
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            late = folder / 'late'
            script = folder / 'writer.py'
            script.write_text('import time,pathlib\ntime.sleep(5)\n' + f'pathlib.Path({str(late)!r}).write_text("late")\n')
            event = threading.Event()
            timer = threading.Timer(0.3, event.set)
            timer.start()
            self.addCleanup(timer.cancel)
            with self.assertRaises(m.MaintenanceCancelled):
                m.run_build_command([sys.executable, script], folder, folder / 'log', event)
            self.assertFalse(late.exists())

    def test_build_kit_rejects_capability_mismatch_before_execution(self):
        from newsnap.upstream import COMMIT
        with tempfile.TemporaryDirectory() as temporary:
            kit = Path(temporary)
            (kit / 'build-kit.json').write_text(json.dumps({'format': 1, 'runtime_version': VERSION,
                'runtime_api': RUNTIME_API, 'capabilities': [], 'donor_commit': COMMIT, 'files': {}}))
            with self.assertRaisesRegex(ValueError, 'does not match'):
                m.verify_build_kit(kit)

    def test_public_build_kit_rejects_game_input_in_source(self):
        from tools.package_build_kit import verify_kit_tree
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'source').mkdir()
            (folder / 'source/main').write_bytes(b'private')
            with self.assertRaisesRegex(ValueError, 'private'):
                verify_kit_tree(folder)

class KitIntegrityTests(TestCase):
    def test_unlisted_executable_code_is_rejected(self):
        from newsnap.upstream import COMMIT
        with tempfile.TemporaryDirectory() as temporary:
            kit = Path(temporary)
            files = {}
            for name in ('python/python.exe', 'source/newsnap/maintenance.py', 'source/newsnap/build.py',
                         'source/third_party/astral/tools/build_game.py', 'sdk/llvm/bin/clang.exe', 'sdk/bin/ninja.exe'):
                path = kit / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'tool')
                files[name] = m.digest(path)
            (kit / 'source/sitecustomize.py').write_bytes(b'unlisted code')
            (kit / 'build-kit.json').write_text(json.dumps({'format': 1, 'runtime_version': VERSION,
                'runtime_api': RUNTIME_API, 'capabilities': list(RUNTIME_CAPABILITIES),
                'donor_commit': COMMIT, 'files': files}))
            with self.assertRaisesRegex(ValueError, 'Unlisted'):
                m.verify_build_kit(kit)

class NestedRuntimeTests(OwnerRuntimeFixture, TestCase):
    def test_nested_vendor_files_and_terms_are_switched_with_runtime(self):
        candidate = self.candidate()
        (candidate / 'licenses').mkdir()
        (candidate / 'licenses/NVIDIA-DLSS.txt').write_bytes(b'vendor terms')
        (candidate / 'nvngx_dlss.dll').write_bytes(b'vendor dll')
        m.install_candidate(self.root, candidate)
        self.assertEqual((self.data / 'licenses/NVIDIA-DLSS.txt').read_bytes(), b'vendor terms')
        self.assertEqual((self.data / 'nvngx_dlss.dll').read_bytes(), b'vendor dll')

    def test_nested_failed_switch_restores_previous_terms(self):
        (self.data / 'licenses').mkdir()
        (self.data / 'licenses/NVIDIA-DLSS.txt').write_bytes(b'old terms')
        candidate = self.candidate()
        (candidate / 'licenses').mkdir()
        (candidate / 'licenses/NVIDIA-DLSS.txt').write_bytes(b'new terms')
        replace = Path.replace
        def fail(source, target):
            if source == candidate / 'newsnap-game.json':
                raise OSError('commit failed')
            return replace(source, target)
        with patch.object(Path, 'replace', fail):
            with self.assertRaises(OSError):
                m.install_candidate(self.root, candidate)
        self.assertEqual((self.data / 'licenses/NVIDIA-DLSS.txt').read_bytes(), b'old terms')

class ArtifactIntegrityTests(OwnerRuntimeFixture, TestCase):
    def test_new_receipt_detects_damaged_support_dll(self):
        (self.data / 'SDL3.dll').write_bytes(b'known dll')
        self.marker['runtime_files'] = {'newsnap.exe': m.digest(self.data / 'newsnap.exe'),
                                       'SDL3.dll': m.digest(self.data / 'SDL3.dll')}
        self.write_marker()
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        (self.data / 'SDL3.dll').write_bytes(b'damaged dll')
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

class OwnerIndexTests(TestCase):
    def test_reconstructed_index_is_accepted_by_real_donor_consumer(self):
        import subprocess,sys
        from types import SimpleNamespace
        from newsnap import build as builder
        donor_consumer = Path(__file__).resolve().parents[1] / 'third_party/astral/tools/romfs_index.py'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / 'owner'
            (data / 'exefs').mkdir(parents=True)
            (data / 'romfs').mkdir()
            (data / 'exefs/main').write_bytes(b'code')
            (data / 'romfs/romfs.bin').write_bytes(b'romf')
            (root / 'profiles').mkdir()
            (root / 'profiles/snap-2.0.1.json').write_text(json.dumps({
                'exefs_sha256': {'main': m.digest(data / 'exefs/main')},
                'romfs_sha256': m.digest(data / 'romfs/romfs.bin'),
                'verified_control': {'display_version': '2.0.1', 'save_size': 42, 'journal_size': 2}}))
            with patch.object(builder, 'ROOT', root), patch.object(builder, 'verify_translator'), patch('newsnap.upstream.extractor',
                    return_value=SimpleNamespace(index_romfs=lambda _: [])), patch.object(builder, 'adapt_sources',
                    side_effect=RuntimeError('stop after verified staging')):
                with self.assertRaisesRegex(RuntimeError, 'stop after verified staging'):
                    builder.build(root / 'sdk', owner_data=data, work_dir=root / 'work')
            output = root / 'consumer-output'
            output.mkdir()
            result = subprocess.run([sys.executable, donor_consumer, '--romfs', root / 'work/owner-romfs',
                                     '--out', output], capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((output / 'romfs-index.bin').read_bytes().startswith(b'ACRFS1'))

class EmbeddedPythonTests(TestCase):
    def test_embedded_python_can_import_build_tools_siblings(self):
        import subprocess
        from newsnap import build as builder
        root=Path(__file__).resolve().parents[1]
        python=root/'toolchain/astral-release/Astral Chain-Setup/python/python.exe'
        if not python.is_file():
            self.skipTest('portable donor Python not installed')
        script=root/'third_party/astral/tools/build_game.py'
        with patch.object(builder.sys,'executable',str(python)):
            command=builder.python_script_command(script,'--help')
        result=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('--romfs',result.stdout)

class PublicShaderTests(TestCase):
    def test_precompiled_public_header_matches_real_donor_recipe_without_shader_tools(self):
        import importlib.util,shutil
        from newsnap import build as builder
        root=Path(__file__).resolve().parents[1]
        header=root/'build/updated/fsr3_spv.h'
        if not header.is_file():self.skipTest('local public shader header unavailable')
        with tempfile.TemporaryDirectory() as temporary:
            temp=Path(temporary)
            (temp/'sdk/precompiled').mkdir(parents=True)
            shutil.copy2(header,temp/'sdk/precompiled/fsr3_spv.h')
            source=root/'third_party/astral'
            builder.stage_runtime_shaders(temp/'sdk',source,temp/'out')
            spec=importlib.util.spec_from_file_location('public_shader_test',source/'tools/ffx_sdk.py')
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with patch.object(module,'fetch',side_effect=AssertionError('unexpected network/compiler')):
                self.assertEqual(module.header(temp/'out'),temp/'out/fsr3_spv.h')
            (temp/'sdk/precompiled/fsr3_spv.h').write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError,'shader header'):
                builder.stage_runtime_shaders(temp/'sdk',source,temp/'out')

class RuntimeRecipeTests(OwnerRuntimeFixture, TestCase):
    def test_runtime_version_mismatch_requires_rebuild(self):
        self.marker['runtime_version']='older-version'
        self.write_marker()
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

    def test_same_version_different_source_recipe_requires_rebuild(self):
        revision='a'*40
        (self.root/'MANIFEST.json').write_text(json.dumps({'source_revision':revision}))
        self.marker['runtime_source_revision']=revision
        self.write_marker()
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        self.marker['runtime_source_revision']='b'*40
        self.write_marker()
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

class BackupDurabilityTests(OwnerRuntimeFixture, TestCase):
    def interrupted(self):
        transaction=self.data/m.TRANSACTION
        backup=transaction/'backup'
        backup.mkdir(parents=True)
        (backup/'newsnap.exe').write_bytes(b'old executable')
        (backup/'SDL3.dll').write_bytes(b'old dll')
        (transaction/'journal.json').write_text(json.dumps({'format':2,
            'files':{'newsnap.exe':True,'SDL3.dll':True},'backup':m._backup_inventory(backup)}))
        (self.data/'newsnap.exe').write_bytes(b'healthy live executable')
        (self.data/'SDL3.dll').write_bytes(b'healthy live dll')
        return transaction,backup

    def test_same_size_tampered_backup_refuses_all_live_writes(self):
        transaction,backup=self.interrupted()
        (backup/'SDL3.dll').write_bytes(b'bad dll')
        with self.assertRaisesRegex(ValueError,'backup integrity'):
            m.recover_runtime(self.root)
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'healthy live executable')
        self.assertEqual((self.data/'SDL3.dll').read_bytes(),b'healthy live dll')
        self.assertTrue((transaction/'journal.json').exists())

    def test_truncated_backup_refuses_all_live_writes(self):
        transaction,backup=self.interrupted()
        (backup/'SDL3.dll').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'backup integrity'):
            m.recover_runtime(self.root)
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'healthy live executable')
        self.assertTrue((transaction/'journal.json').exists())

    def test_every_backup_file_is_synced_before_journal_publication(self):
        synced=[]
        synced_directories=[]
        real_sync=m._sync_file
        replace=Path.replace
        checked=[]
        def sync(path):
            synced.append(Path(path))
            return real_sync(path)
        def publish(source,target):
            if Path(target).name=='journal.json':
                backup=self.data/m.TRANSACTION/'backup'
                expected={p for p in backup.rglob('*') if p.is_file()}
                self.assertTrue(expected)
                self.assertTrue(expected.issubset(synced))
                self.assertTrue({backup, backup.parent, self.data}.issubset(synced_directories))
                journal=json.loads(source.read_text())
                self.assertEqual(journal['backup'],m._backup_inventory(backup))
                self.assertFalse(journal['directory_sync_supported'])
                checked.append(True)
            return replace(source,target)
        def directory(path):
            synced_directories.append(Path(path))
            return False  # Filesystem refuses directory flushing; data still syncs.
        with patch.object(m,'_sync_file',sync),patch.object(m,'_sync_directory',directory),patch.object(Path,'replace',publish):
            m.install_candidate(self.root,self.candidate())
        self.assertEqual(checked,[True])

class PackageNamingTests(TestCase):
    def test_dotted_release_version_is_kept_in_build_kit_archive_name(self):
        from tools.package_build_kit import archive_path
        name=Path('build/releases/NewSnapBuildKit-0.4.0-alpha-windows-abcdef12')
        self.assertEqual(archive_path(name).name,'NewSnapBuildKit-0.4.0-alpha-windows-abcdef12.zip')

class RecoveryCleanupTests(OwnerRuntimeFixture, TestCase):
    def test_interrupted_backup_cleanup_cannot_leave_a_pending_recovery_journal(self):
        import shutil
        transaction=self.data/m.TRANSACTION
        backup=transaction/'backup'
        backup.mkdir(parents=True)
        (backup/'newsnap.exe').write_bytes(b'old executable')
        (transaction/'journal.json').write_text(json.dumps({'format':2,'files':{'newsnap.exe':True},
            'backup':m._backup_inventory(backup)}))
        (self.data/'newsnap.exe').write_bytes(b'incomplete replacement')
        rmtree=shutil.rmtree
        def interrupt(path,*args,**kwargs):
            if Path(path)==transaction:
                rmtree(backup)
                raise OSError('cleanup interrupted')
            return rmtree(path,*args,**kwargs)
        with patch.object(m.shutil,'rmtree',interrupt):
            with self.assertRaisesRegex(OSError,'cleanup interrupted'):
                m.recover_runtime(self.root)
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'old executable')
        self.assertFalse((transaction/'journal.json').exists())
        self.assertTrue(m.recover_runtime(self.root))
        self.assertFalse(transaction.exists())


class VerifiedReplacementTests(OwnerRuntimeFixture, TestCase):
    def test_switch_returns_verified_cache_absence_and_leaves_no_old_runtime(self):
        for name in m.INVALIDATED:
            path=self.data/name
            if name=='shader-cache':path.mkdir();(path/'old.spv').write_bytes(b'old cache')
            else:path.write_bytes(b'old cache')
        (self.data/'shader-programs.bin').write_bytes(b'observed programs')
        report=m.install_candidate(self.root,self.candidate())
        self.assertIsInstance(report,dict)
        self.assertEqual(set(report['invalidated']),set(m.INVALIDATED))
        self.assertTrue(report['cache_absence_verified'])
        self.assertTrue(report['transaction_removed'])
        self.assertEqual(report['runtime_sha256'],m.digest(self.data/'newsnap.exe'))
        self.assertFalse((self.data/m.TRANSACTION).exists())
        self.assertEqual((self.data/'shader-programs.bin').read_bytes(),b'observed programs')
        self.assertFalse(any((self.data/name).exists() for name in m.INVALIDATED))

    def test_silent_cache_removal_failure_rolls_back_before_commit(self):
        stale=self.data/'pipeline-cache.bin';stale.write_bytes(b'stale pipeline')
        remove=m._remove
        def keep_one(path):
            if path==stale:return
            return remove(path)
        with patch.object(m,'_remove',side_effect=keep_one):
            with self.assertRaisesRegex(ValueError,'cache|cachÃ©'):
                m.install_candidate(self.root,self.candidate())
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'old executable')
        self.assertEqual(stale.read_bytes(),b'stale pipeline')
        self.assertFalse((self.data/m.TRANSACTION).exists())

    def test_post_replace_corruption_is_detected_and_restores_previous_runtime(self):
        candidate=self.candidate();replace=Path.replace
        def corrupt(source,target):
            result=replace(source,target)
            if source==candidate/'newsnap.exe':Path(target).write_bytes(b'corrupted after move')
            return result
        with patch.object(Path,'replace',corrupt):
            with self.assertRaisesRegex(ValueError,'integrity|hash|integridad'):
                m.install_candidate(self.root,candidate)
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'old executable')
        self.assertFalse((self.data/m.TRANSACTION).exists())

    def test_repeated_switches_do_not_accumulate_backups_or_temporary_outputs(self):
        (self.data/'profile').mkdir();(self.data/'profile/save').write_bytes(b'preserve save')
        for _ in range(3):
            candidate=self.candidate();report=m.install_candidate(self.root,candidate)
            candidate.rmdir()
            self.assertTrue(report['transaction_removed'])
            self.assertEqual({p.name for p in self.data.iterdir()}, {'profile','newsnap.exe','newsnap-game.json'})
            self.assertEqual((self.data/'profile/save').read_bytes(),b'preserve save')

    def test_cleanup_failure_does_not_report_success_or_restore_committed_generation(self):
        remove_tree=m.shutil.rmtree
        transaction=self.data/m.TRANSACTION
        def keep_backup(path,*args,**kwargs):
            if Path(path)==transaction:return
            return remove_tree(path,*args,**kwargs)
        with patch.object(m.shutil,'rmtree',side_effect=keep_backup):
            with self.assertRaisesRegex(ValueError,'cleanup incomplete'):
                m.install_candidate(self.root,self.candidate())
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'new executable')
        self.assertTrue(transaction.exists())
        self.assertFalse((transaction/'journal.json').exists())
        self.assertTrue(m.recover_runtime(self.root))
        self.assertFalse(transaction.exists())
        self.assertEqual((self.data/'newsnap.exe').read_bytes(),b'new executable')


class VerifiedRecoveryTests(BackupDurabilityTests):
    def test_corrupt_restore_retains_good_backup_and_journal_for_retry(self):
        transaction, backup = self.interrupted()
        replace = Path.replace
        def corrupt(source, target):
            result = replace(source, target)
            if source == transaction / 'restore-newsnap.exe':
                Path(target).write_bytes(b'corrupt restore')
            return result
        with patch.object(Path, 'replace', corrupt):
            with self.assertRaisesRegex(ValueError, 'restor.*integrity'):
                m.recover_runtime(self.root)
        self.assertTrue((transaction / 'journal.json').is_file())
        self.assertEqual((backup / 'newsnap.exe').read_bytes(), b'old executable')
        self.assertTrue(m.recover_runtime(self.root))
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'old executable')
        self.assertFalse(transaction.exists())

    def test_nested_cache_junction_is_rejected_without_copying_profile(self):
        import os, subprocess
        profile = self.data / 'profile'
        profile.mkdir()
        (profile / 'save').write_bytes(b'private save')
        cache = self.data / 'shader-cache'
        cache.mkdir()
        link = cache / 'nested'
        if os.name == 'nt':
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(profile)],
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.addCleanup(lambda: link.rmdir() if link.exists() else None)
        else:
            link.symlink_to(profile, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'link'):
            m.install_candidate(self.root, self.candidate())
        self.assertEqual((profile / 'save').read_bytes(), b'private save')
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'old executable')
        self.assertFalse((self.data / m.TRANSACTION).exists())


class BuildWorkspaceCleanupTests(TestCase):
    def test_silent_cleanup_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary)
            work = data / '.runtime-build-test'
            work.mkdir()
            with patch.object(m.shutil, 'rmtree', return_value=None):
                with self.assertRaisesRegex(ValueError, 'build cleanup incomplete'):
                    m._cleanup_build_workspace(data, work)
            self.assertTrue(work.is_dir())

    def test_cleanup_rejects_external_workspace_and_ordinary_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / 'GameData'
            data.mkdir()
            for work in (root / '.runtime-build-external', data / 'profile'):
                work.mkdir()
                (work / 'save').write_bytes(b'preserve')
                with self.assertRaisesRegex(ValueError, 'Unsafe runtime build'):
                    m._cleanup_build_workspace(data, work)
                self.assertEqual((work / 'save').read_bytes(), b'preserve')
