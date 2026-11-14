"""Only verified private generated code can enter a bounded owner cache."""
import hashlib
import json
import shutil
import tempfile
import threading
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from newsnap import generation_cache as gc
from newsnap.provenance import record_generation, verify_generation


class CacheFixture:
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.cache=gc.GenerationCache(self.root/'cache')
        self.owner=gc.owner_identity(self.root/'owner',{'files':[{'name':'main','sha256':'a'*64}]},'b'*64)
        self.recipe={'exefs':{'main':'a'*64},'generator':{'recomp/gen.py':'c'*64},'version':'snap'}
        self.generated=self.root/'generated'
        self.generated.mkdir()
        (self.generated/'main.c').write_text('int generated_function(void) { return 7; }\n')
        (self.generated/'layout.h').write_text('#define MODULE_BASE 0x7100000000\n')
        (self.generated/'layout.json').write_text('{"module":"main"}\n')
        record_generation(self.generated,self.recipe)

    def entries(self):
        return [p for p in (self.root/'cache').iterdir() if p.is_dir() and len(p.name)==64]

    def directory_link(self,link,target):
        import os
        try:os.symlink(target,link,target_is_directory=True)
        except OSError:
            if os.name!='nt':self.skipTest('directory symlinks unavailable')
            import subprocess
            quote=lambda p:"'"+str(p).replace("'","''")+"'"
            self.assertTrue(target.resolve().is_relative_to(self.root.resolve()))
            self.assertTrue(link.parent.resolve().is_relative_to(self.root.resolve()))
            subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
                f'New-Item -ItemType Junction -Path {quote(link)} -Target {quote(target)} | Out-Null'],
                check=True,capture_output=True)


class GenerationCacheTests(CacheFixture,TestCase):
    def test_cold_cache_misses_then_independent_verified_snapshot_restores(self):
        self.assertFalse(self.cache.restore(self.owner,self.recipe,self.root/'cold'))
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        destination=self.root/'restored'
        self.assertTrue(self.cache.restore(self.owner,self.recipe,destination))
        verify_generation(destination,self.recipe)
        self.assertEqual((destination/'main.c').read_bytes(),(self.generated/'main.c').read_bytes())
        (destination/'main.c').write_text('changed restored output')
        second=self.root/'second'
        self.assertTrue(self.cache.restore(self.owner,self.recipe,second))
        verify_generation(second,self.recipe)
        self.assertNotEqual((destination/'main.c').read_bytes(),(second/'main.c').read_bytes())

    def test_owner_path_original_hash_or_generator_recipe_mismatch_is_a_miss(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        other_owner=gc.owner_identity(self.root/'other-owner',{'files':[{'name':'main','sha256':'a'*64}]},'b'*64)
        modified_owner=gc.owner_identity(self.root/'owner',{'files':[{'name':'main','sha256':'d'*64}]},'b'*64)
        other_recipe=dict(self.recipe,generator={'recomp/gen.py':'d'*64})
        self.assertFalse(self.cache.restore(other_owner,self.recipe,self.root/'other'))
        self.assertFalse(self.cache.restore(modified_owner,self.recipe,self.root/'modified'))
        self.assertFalse(self.cache.restore(self.owner,other_recipe,self.root/'stale'))

    def test_tampered_cached_code_regenerates_and_a_fresh_publish_repairs_it(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        entry=self.entries()[0]
        code=entry/'generated/main.c'
        original=code.read_bytes()
        code.write_bytes(bytes([original[0]^1])+original[1:])
        self.assertFalse(self.cache.restore(self.owner,self.recipe,self.root/'bad'))
        self.assertFalse((self.root/'bad').exists())
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        self.assertTrue(self.cache.restore(self.owner,self.recipe,self.root/'repaired'))
        verify_generation(self.root/'repaired',self.recipe)

    def test_cached_executable_or_objects_are_never_restored_or_published(self):
        (self.generated/'newsnap.exe').write_bytes(b'never trust this executable')
        self.assertFalse(self.cache.publish(self.owner,self.recipe,self.generated))
        (self.generated/'newsnap.exe').unlink()
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        (self.entries()[0]/'generated/old.o').write_bytes(b'never trust this object')
        self.assertFalse(self.cache.restore(self.owner,self.recipe,self.root/'bad'))

    def test_cancellation_cleans_partial_publish_and_preserves_fresh_sources(self):
        event=threading.Event()
        original=gc._copy_file
        def copy(source,target,cancel_event):
            original(source,target,cancel_event)
            event.set()
        with patch.object(gc,'_copy_file',copy):
            with self.assertRaises(gc.GenerationCacheCancelled):
                self.cache.publish(self.owner,self.recipe,self.generated,event)
        self.assertFalse(any(p.name.startswith('.publish-') for p in (self.root/'cache').iterdir()))
        self.assertEqual(self.entries(),[])
        verify_generation(self.generated,self.recipe)

    def test_cancellation_cleans_partial_restore_without_touching_destination(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        event=threading.Event()
        original=gc._copy_file
        def copy(source,target,cancel_event):
            original(source,target,cancel_event)
            event.set()
        with patch.object(gc,'_copy_file',copy):
            with self.assertRaises(gc.GenerationCacheCancelled):
                self.cache.restore(self.owner,self.recipe,self.root/'cancelled',event)
        self.assertFalse((self.root/'cancelled').exists())
        self.assertFalse(any(p.name.startswith('.generated-cache-') for p in self.root.iterdir()))

    def test_last_two_recipes_are_kept_and_unrelated_paths_are_preserved(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        first=self.entries()[0]
        sentinel=self.root/'cache/unrelated.txt'
        sentinel.write_text('keep me')
        for tag in ('2','3'):
            recipe=dict(self.recipe,generator={'recomp/gen.py':tag*64})
            record_generation(self.generated,recipe)
            self.assertTrue(self.cache.publish(self.owner,recipe,self.generated))
        self.assertEqual(len(self.entries()),2)
        self.assertFalse(first.exists())
        self.assertEqual(sentinel.read_text(),'keep me')
        self.assertTrue((self.root/'owner').exists() is False)

    def test_byte_budget_evicts_only_owned_cache_entries(self):
        cache=gc.GenerationCache(self.root/'cache',max_bytes=30000)
        (self.generated/'main.c').write_text('a'*18000)
        record_generation(self.generated,self.recipe)
        self.assertTrue(cache.publish(self.owner,self.recipe,self.generated))
        other=dict(self.recipe,generator={'recomp/gen.py':'d'*64})
        record_generation(self.generated,other)
        self.assertTrue(cache.publish(self.owner,other,self.generated))
        self.assertEqual(len(self.entries()),1)
        self.assertTrue(cache.restore(self.owner,other,self.root/'latest'))

    def test_unmarked_nonempty_or_unwritable_cache_is_a_safe_miss(self):
        cache_root=self.root/'foreign'
        cache_root.mkdir()
        sentinel=cache_root/'important.save'
        sentinel.write_bytes(b'untouched')
        cache=gc.GenerationCache(cache_root)
        self.assertFalse(cache.publish(self.owner,self.recipe,self.generated))
        self.assertEqual(sentinel.read_bytes(),b'untouched')
        with patch.object(self.cache,'_prepare',side_effect=PermissionError('read only')):
            self.assertFalse(self.cache.restore(self.owner,self.recipe,self.root/'readonly'))
            self.assertFalse(self.cache.publish(self.owner,self.recipe,self.generated))
        verify_generation(self.generated,self.recipe)

    def test_existing_destination_is_never_replaced(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        destination=self.root/'valuable'
        destination.mkdir()
        (destination/'save').write_bytes(b'keep')
        self.assertFalse(self.cache.restore(self.owner,self.recipe,destination))
        self.assertEqual((destination/'save').read_bytes(),b'keep')

    def test_optout_does_not_create_cache(self):
        cache=gc.GenerationCache(self.root/'disabled',environment={'NEWSNAP_GENERATION_CACHE':'0'})
        self.assertFalse(cache.publish(self.owner,self.recipe,self.generated))
        self.assertFalse(cache.restore(self.owner,self.recipe,self.root/'unused'))
        self.assertFalse((self.root/'disabled').exists())

class CacheSafetyTests(CacheFixture,TestCase):
    def test_publish_failure_never_leaves_a_partial_entry_or_stage(self):
        replace=Path.replace
        def fail(source,target):
            if Path(source).name.startswith('.publish-'):
                raise OSError('disk full while publishing')
            return replace(source,target)
        with patch.object(Path,'replace',fail):
            self.assertFalse(self.cache.publish(self.owner,self.recipe,self.generated))
        self.assertEqual(self.entries(),[])
        self.assertFalse(any(p.name.startswith('.publish-') for p in (self.root/'cache').iterdir()))
        verify_generation(self.generated,self.recipe)

    def test_owner_input_identity_cannot_claim_another_generation_receipt(self):
        owner=dict(self.owner,exefs={'main':'d'*64})
        self.assertFalse(self.cache.publish(owner,self.recipe,self.generated))

    def test_foreign_hex_child_is_not_deleted_to_meet_a_cache_budget(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        foreign=self.root/'cache'/('f'*64)
        foreign.write_bytes(b'unrelated owner file')
        recipe=dict(self.recipe,generator={'recomp/gen.py':'d'*64})
        record_generation(self.generated,recipe)
        self.assertFalse(self.cache.publish(self.owner,recipe,self.generated))
        self.assertEqual(foreign.read_bytes(),b'unrelated owner file')
        self.assertEqual(len(self.entries()),1)

    def test_linked_cache_root_never_modifies_its_target(self):
        outside=self.root/'outside'
        outside.mkdir()
        (outside/'important.save').write_bytes(b'keep me')
        link=self.root/'linked-cache'
        self.directory_link(link,outside)
        cache=gc.GenerationCache(link)
        self.assertFalse(cache.publish(self.owner,self.recipe,self.generated))
        self.assertEqual((outside/'important.save').read_bytes(),b'keep me')
        self.assertEqual(list(outside.iterdir()),[outside/'important.save'])

    def test_corrupt_generation_receipt_is_a_miss_and_can_be_repaired(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        (self.entries()[0]/'generated/generation-receipt.json').write_bytes(b'broken JSON')
        self.assertFalse(self.cache.restore(self.owner,self.recipe,self.root/'broken'))
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        self.assertTrue(self.cache.restore(self.owner,self.recipe,self.root/'recovered'))

    def test_link_inside_entry_cannot_redirect_restore_or_eviction_into_a_profile(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        outside=self.root/'profile'
        outside.mkdir()
        (outside/'save').write_bytes(b'preserve this progress')
        entry=self.entries()[0]
        self.directory_link(entry/'generated/junction',outside)
        self.assertFalse(self.cache.restore(self.owner,self.recipe,self.root/'unsafe'))
        recipe=dict(self.recipe,generator={'recomp/gen.py':'d'*64})
        record_generation(self.generated,recipe)
        self.assertFalse(self.cache.publish(self.owner,recipe,self.generated))
        self.assertEqual((outside/'save').read_bytes(),b'preserve this progress')
        self.assertTrue(entry.exists())
        self.assertEqual(len(self.entries()),1)

class BuildCacheIntegrationTests(TestCase):
    def test_warm_owner_build_skips_only_verified_generation_and_still_compiles(self):
        from types import SimpleNamespace
        from newsnap import build as builder
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            owner=root/'owner'
            (owner/'exefs').mkdir(parents=True)
            (owner/'romfs').mkdir()
            (owner/'exefs/main').write_bytes(b'code')
            (owner/'romfs/romfs.bin').write_bytes(b'romf')
            digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            (root/'profiles').mkdir()
            (root/'profiles/snap-2.0.1.json').write_text(json.dumps({
                'main_sha256':digest(owner/'exefs/main'),'oodle_decompress_offset':0,
                'exefs_sha256':{'main':digest(owner/'exefs/main')},'romfs_sha256':digest(owner/'romfs/romfs.bin'),
                'verified_control':{'display_version':'2.0.1','save_size':42,'journal_size':2}}))
            (root/'patches').mkdir()
            for name in ('snap-2.0.1-render.txt','snap-2.0.1-supersample.txt','snap-2.0.1-random-range.txt',
                         'snap-2.0.1-high-fps.txt'):
                (root/'patches'/name).write_text('')
            sdk=root/'sdk'
            (sdk/'bin').mkdir(parents=True)
            for name in ('SDL3.dll','libopus-0.dll','ac_xlate.exe','ac_xlate.id'):(sdk/'bin'/name).write_bytes(b'fixture tool')
            # Real tool verification against a controlled public fixture pin.
            tool = b'fixture tool'
            tool_id = 'a' * 64
            (sdk/'bin/ac_xlate.id').write_text(tool_id + '\n',encoding='ascii')
            (root/'profiles/translator-windows.json').write_text(json.dumps(dict(
                format=1,platform='windows-x64',size=len(tool),sha256=hashlib.sha256(tool).hexdigest(),identity=tool_id)))
            calls={'generate':0,'compile':0}
            def adapt(destination,**kwargs):
                for name in ('recomp/gen.py','tools/build_game.py'):
                    path=destination/name
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text('# identical generation recipe across work directories\n')
                return destination
            def run(command,*args):
                output=Path(command[command.index('--out')+1])
                output.mkdir(parents=True,exist_ok=True)
                if any(Path(str(x)).name=='gen.py' for x in command):
                    calls['generate']+=1
                    (output/'layout.json').write_text('{}')
                    (output/'main.c').write_text('int generated_owner_code;')
                    (output/'layout.h').write_text('#pragma once')
                else:
                    calls['compile']+=1
                    (output/'newsnap.exe').write_bytes(b'newly compiled fixture')
            with patch('newsnap.translator.PIN',root/'profiles/translator-windows.json'),\
                 patch.object(builder,'ROOT',root),patch.object(builder,'adapt_sources',side_effect=adapt),\
                 patch.object(builder,'stage_runtime_shaders',return_value=True),patch.object(builder,'run_logged',side_effect=run),\
                 patch.object(builder,'verify_random_range_original') as verify_bridge,\
                 patch('newsnap.upstream.extractor',return_value=SimpleNamespace(index_romfs=lambda _:[])),\
                 patch('tools.fetch_upscaler_sdk.verify',return_value=True),patch('newsnap.upscaler_adapt.stage_sdk'),\
                 patch('tools.fetch_dlss.verify',return_value=False):
                first=builder.build(sdk,owner_data=owner,work_dir=root/'cold',generation_cache_root=root/'cache')
                second=builder.build(sdk,owner_data=owner,work_dir=root/'warm',generation_cache_root=root/'cache')
                self.assertEqual(verify_bridge.call_count,2)
                verify_bridge.assert_called_with(owner/'exefs')
                with patch.object(builder,'verify_random_range_original',side_effect=ValueError('unverified original span')),\
                     patch('newsnap.generation_cache.GenerationCache.restore') as restore:
                    with self.assertRaisesRegex(ValueError,'unverified original span'):
                        builder.build(sdk,owner_data=owner,work_dir=root/'refused',generation_cache_root=root/'cache')
                    restore.assert_not_called()
            self.assertEqual(calls,{'generate':1,'compile':2})
            self.assertTrue(first.is_file() and second.is_file())
            self.assertEqual(json.loads((root/'warm/logs/generation-cache.json').read_text())['restored'],True)

class ReceiptScopeTests(CacheFixture,TestCase):
    def test_nested_receipt_named_json_cannot_bypass_the_output_inventory(self):
        extra=self.generated/'other/generation-receipt.json'
        extra.parent.mkdir()
        extra.write_text('{"unverified":"extra"}')
        verify_generation(self.generated,self.recipe)  # Existing producer skips this basename.
        self.assertFalse(self.cache.publish(self.owner,self.recipe,self.generated))

    def test_copy_corruption_is_detected_before_atomic_publication(self):
        copy=gc._copy_file
        def corrupt(source,target,event):
            copy(source,target,event)
            if target.name=='main.c':target.write_bytes(b'corrupted while copying')
        with patch.object(gc,'_copy_file',corrupt):
            self.assertFalse(self.cache.publish(self.owner,self.recipe,self.generated))
        self.assertEqual(self.entries(),[])
        verify_generation(self.generated,self.recipe)

class GeneratorEnvironmentTests(CacheFixture,TestCase):
    def test_python_or_dependency_environment_change_requires_generation(self):
        import copy
        environment=gc.current_generator_environment()
        first=gc.GenerationCache(self.root/'cache',generator_environment=environment)
        self.assertTrue(first.publish(self.owner,self.recipe,self.generated))
        for field in ('numpy','capstone','lz4'):
            changed=copy.deepcopy(environment)
            changed['packages'][field]='different-version'
            cache=gc.GenerationCache(self.root/'cache',generator_environment=changed)
            self.assertFalse(cache.restore(self.owner,self.recipe,self.root/field))
        changed=copy.deepcopy(environment)
        changed['python']['version'][2]+=1
        cache=gc.GenerationCache(self.root/'cache',generator_environment=changed)
        self.assertFalse(cache.restore(self.owner,self.recipe,self.root/'python'))
        for field in ('implementation','cache_tag'):
            changed=copy.deepcopy(environment)
            changed['python'][field]='different-runtime'
            cache=gc.GenerationCache(self.root/'cache',generator_environment=changed)
            self.assertFalse(cache.restore(self.owner,self.recipe,self.root/field))

    def test_missing_dependency_versions_are_explicit_identity_values(self):
        from importlib.metadata import PackageNotFoundError
        with patch('newsnap.generation_cache.metadata.version',side_effect=PackageNotFoundError):
            environment=gc.current_generator_environment()
        self.assertEqual(environment['packages'],{name:'unknown: not installed' for name in ('numpy','capstone','lz4')})

class WorkerCacheOptionsTests(TestCase):
    def test_explicit_cache_optout_survives_worker_environment_sanitization(self):
        import os,sys
        from newsnap import maintenance as maintenance
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            log=root/'worker.log'
            script='import os,json; print(json.dumps({"cache":os.getenv("NEWSNAP_GENERATION_CACHE"),"unsafe":os.getenv("NEWSNAP_UNSAFE")}))'
            with patch.dict(os.environ,{'NEWSNAP_GENERATION_CACHE':'0','NEWSNAP_UNSAFE':'test value'}):
                maintenance.run_build_command([sys.executable,'-c',script],root,log)
            self.assertEqual(json.loads(log.read_text()),{'cache':'0','unsafe':None})

    def test_injected_cache_root_is_an_explicit_worker_argument(self):
        from contextlib import nullcontext
        from newsnap import maintenance as maintenance
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'GameData').mkdir()
            (root/'GameData/newsnap-game.json').write_text('{}')
            kit=root/'kit'
            (kit/'source').mkdir(parents=True)
            commands=[]
            def stop(command,*args):
                commands.append(command)
                raise RuntimeError('stop before native work')
            with patch('newsnap.launcher_settings.ProfileLock',return_value=nullcontext()),\
                 patch.object(maintenance,'verify_build_kit',return_value={'source_revision':'a'*40}),\
                 patch.object(maintenance,'run_build_command',side_effect=stop):
                with self.assertRaisesRegex(RuntimeError,'stop before native work'):
                    maintenance.rebuild_runtime(root,kit,force=True,generation_cache_root=root/'cache')
            command=commands[0]
            self.assertEqual(Path(command[command.index('--generation-cache-root')+1]),(root/'cache').resolve())

class UnavailableEnvironmentTests(CacheFixture,TestCase):
    def test_unreadable_dependency_identity_falls_back_to_fresh_generation(self):
        with patch('newsnap.generation_cache.metadata.version',side_effect=PermissionError('metadata unreadable')):
            cache=gc.GenerationCache(self.root/'cache')
            self.assertFalse(cache.publish(self.owner,self.recipe,self.generated))
            self.assertFalse(cache.restore(self.owner,self.recipe,self.root/'unavailable'))
        verify_generation(self.generated,self.recipe)

class MaintenanceCacheReceiptTests(TestCase):
    def test_cache_timing_receipt_survives_maintenance_staging_cleanup(self):
        from contextlib import nullcontext
        from newsnap import maintenance as maintenance
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            data=root/'GameData'
            data.mkdir()
            (data/'newsnap-game.json').write_text('{}')
            kit=root/'kit'
            (kit/'source').mkdir(parents=True)
            expected={'format':1,'restored':True,'generator_ran':False,'generation_seconds':0.0}
            def worker(command,cwd,logfile,*args):
                logfile.parent.mkdir(parents=True,exist_ok=True)
                logfile.write_text('fixture worker')
                work=Path(command[command.index('--work')+1])
                (work/'logs').mkdir()
                (work/'logs/generation-cache.json').write_text(json.dumps(expected))
            with patch('newsnap.launcher_settings.ProfileLock',return_value=nullcontext()),\
                 patch.object(maintenance,'verify_build_kit',return_value={'source_revision':'a'*40}),\
                 patch.object(maintenance,'run_build_command',side_effect=worker),patch.object(maintenance,'install_candidate',return_value={'invalidated':list(maintenance.INVALIDATED),'removed_existing':[],'cache_absence_verified':True,'transaction_removed':True}):
                result=maintenance.rebuild_runtime(root,kit,force=True,generation_cache_root=root/'cache')
            self.assertEqual(result['generation_cache'],expected)
            self.assertEqual(json.loads((data/'logs/generation-cache.json').read_text()),expected)
            self.assertFalse(list(data.glob('.runtime-build-*')))

class CacheArgumentLinkTests(CacheFixture,TestCase):
    def test_worker_argument_does_not_erase_a_link_before_cache_guard_checks(self):
        from contextlib import nullcontext
        from newsnap import maintenance as maintenance
        data=self.root/'GameData'
        data.mkdir()
        (data/'newsnap-game.json').write_text('{}')
        kit=self.root/'kit'
        (kit/'source').mkdir(parents=True)
        outside=self.root/'outside-cache'
        outside.mkdir()
        link=self.root/'cache-link'
        self.directory_link(link,outside)
        commands=[]
        def stop(command,*args):
            commands.append(command)
            raise RuntimeError('stop before native work')
        with patch('newsnap.launcher_settings.ProfileLock',return_value=nullcontext()),\
             patch.object(maintenance,'verify_build_kit',return_value={'source_revision':'a'*40}),\
             patch.object(maintenance,'run_build_command',side_effect=stop):
            with self.assertRaisesRegex(RuntimeError,'stop before native work'):
                maintenance.rebuild_runtime(self.root,kit,force=True,generation_cache_root=link)
        argument=Path(commands[0][commands[0].index('--generation-cache-root')+1])
        self.assertEqual(argument,link.absolute())
        self.assertNotEqual(argument,outside.resolve())

class CacheBudgetFailureTests(CacheFixture,TestCase):
    def test_failed_eviction_cannot_publish_a_third_entry(self):
        for tag in ('1','2'):
            recipe=dict(self.recipe,generator={'recomp/gen.py':tag*64})
            record_generation(self.generated,recipe)
            self.assertTrue(self.cache.publish(self.owner,recipe,self.generated))
        recipe=dict(self.recipe,generator={'recomp/gen.py':'3'*64})
        record_generation(self.generated,recipe)
        with patch.object(self.cache,'_remove_owned',side_effect=PermissionError('read-only old cache')):
            self.assertFalse(self.cache.publish(self.owner,recipe,self.generated))
        self.assertEqual(len(self.entries()),2)
        self.assertFalse(any(p.name.startswith('.publish-') for p in (self.root/'cache').iterdir()))
        verify_generation(self.generated,recipe)

    def test_oversized_entry_is_not_restored_when_budget_is_lower(self):
        self.assertTrue(self.cache.publish(self.owner,self.recipe,self.generated))
        small=gc.GenerationCache(self.root/'cache',max_bytes=1)
        self.assertFalse(small.restore(self.owner,self.recipe,self.root/'oversized'))
        self.assertFalse((self.root/'oversized').exists())
