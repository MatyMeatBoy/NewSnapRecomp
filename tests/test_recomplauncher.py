import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import shutil
import unittest
from unittest.mock import patch

try:
    adapter = importlib.import_module('newsnap.recomplauncher')
except ModuleNotFoundError:
    adapter = None


class RecompLauncherTests(unittest.TestCase):
    def readonly_selection(self, root):
        source = root/'existing'
        for name in ('exefs/main', 'exefs/sdk', 'romfs/romfs.bin'):
            path = source/name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'original fixture')
        adapter.select_data_dir(root, source)
        return source

    def test_prepare_existing_readonly_selection_without_game_argument_is_copied(self):
        from newsnap.paths import data_dir
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            root = Path(folder); source = self.readonly_selection(root)
            def clone(original, destination, **kwargs):
                self.assertEqual(original, source)
                self.assertFalse(destination.exists())
                return Path(shutil.copytree(original, destination))
            with patch('newsnap.data_location.is_writable_data', side_effect=lambda path: path != source), \
                 patch('newsnap.data_location.estimate_copy_bytes', return_value=1024), \
                 patch('newsnap.data_location.clone_readonly_data', side_effect=clone) as copy, \
                 patch('newsnap.home_state.verify') as verify, \
                 patch('newsnap.maintenance.assess_runtime', return_value={'needs_rebuild':False}), \
                 patch('newsnap.launcher_settings.validate_runtime_data'):
                adapter.prepare(root, adapter.arguments(['--recomplauncher-prepare']))
            copy.assert_called_once()
            verify.assert_called_once_with(root)
            self.assertNotEqual(data_dir(root), source)
            self.assertEqual((source/'exefs/main').read_bytes(), b'original fixture')

    def test_play_copies_readonly_selection_even_when_old_runtime_is_current(self):
        from newsnap.paths import data_dir
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            root = Path(folder); source = self.readonly_selection(root)
            with patch('newsnap.data_location.is_writable_data', side_effect=lambda path: path != source), \
                 patch('newsnap.data_location.estimate_copy_bytes', return_value=1024), \
                 patch('newsnap.data_location.clone_readonly_data', side_effect=lambda original, destination, **kw: Path(shutil.copytree(original, destination))) as copy, \
                 patch.object(adapter, 'prepare') as prepare, \
                 patch('newsnap.maintenance.assess_runtime', return_value={'needs_rebuild':False}), \
                 patch('newsnap.launcher_settings.validate_runtime_data'), \
                 patch('newsnap.startup_assets.prepare_hd_shadows'), \
                 patch.object(adapter.subprocess, 'Popen') as process:
                process.return_value.wait.return_value = 0
                self.assertEqual(adapter.play(root, {}), 0)
            copy.assert_called_once()
            prepare.assert_called_once()
            self.assertNotEqual(data_dir(root), source)

    def test_failed_readonly_copy_never_verifies_or_starts_old_selection(self):
        from newsnap.paths import data_dir
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            root = Path(folder); source = self.readonly_selection(root)
            with patch('newsnap.data_location.is_writable_data', return_value=False), \
                 patch('newsnap.data_location.estimate_copy_bytes', return_value=1024), \
                 patch('newsnap.data_location.clone_readonly_data', side_effect=ValueError('copy failed')), \
                 patch('newsnap.home_state.verify') as verify, \
                 patch.object(adapter.subprocess, 'Popen') as process:
                with self.assertRaisesRegex(ValueError, 'copy failed'):
                    adapter.prepare(root, adapter.arguments(['--recomplauncher-prepare']))
                with self.assertRaisesRegex(ValueError, 'copy failed'):
                    adapter.play(root, {})
            self.assertEqual(data_dir(root), source)
            verify.assert_not_called(); process.assert_not_called()

    def setUp(self):
        self.assertIsNotNone(adapter, 'RecompLauncher opt-in adapter is missing')

    def test_regular_launcher_arguments_are_not_claimed(self):
        for args in ([], ['--play'], ['--prepare'], ['--selftest-launcher'], ['--apply-update', 'job.json']):
            self.assertFalse(adapter.handles(args))
        self.assertTrue(adapter.handles(['--recomplauncher-play']))
        self.assertTrue(adapter.handles(['--recomplauncher-prepare']))

    def test_unknown_options_and_invalid_video_combinations_fail_before_start(self):
        for args in (['--set=fps=999'], ['--set=unsafe=value'], ['--set=fps'], ['--unknown']):
            with self.subTest(args=args), tempfile.TemporaryDirectory() as folder:
                with patch.object(adapter, 'play') as play, contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(adapter.main(['--recomplauncher-play', *args], Path(folder)), 2)
                    play.assert_not_called()

    def test_explicit_settings_survive_environment_sanitizing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.dict(os.environ, {'RECOMPLAUNCHER_MODE':'bigpicture', 'RECOMPLAUNCHER_PAD':'playstation',
                                         'AC_FPS':'30', 'AC_INPUT':'unwanted'}, clear=True):
                env = adapter.game_environment(root, {'fps':'144', 'fullscreen':'0'})
            self.assertEqual(env['AC_FPS'], '144')
            self.assertEqual(env['AC_FULLSCREEN'], '0')
            self.assertEqual(env['AC_PAD_LAYOUT'], 'playstation')
            self.assertEqual(env['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'], '0')
            self.assertNotIn('AC_INPUT', env)

    def test_desktop_and_bigpicture_defaults_do_not_write_ini(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for mode, expected in [('desktop','0'),('bigpicture','1')]:
                with patch.dict(os.environ, {'RECOMPLAUNCHER_MODE':mode}, clear=True):
                    self.assertEqual(adapter.game_environment(root,{})['AC_FULLSCREEN'], expected)
            self.assertFalse(list(root.rglob('*.ini')))

    def test_bad_pad_hint_does_not_become_a_runtime_option(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'RECOMPLAUNCHER_PAD':'invalid'}, clear=True):
            env=adapter.game_environment(Path(folder), {})
            self.assertNotIn('AC_PAD_LAYOUT',env)

    def test_folder_preparation_reuses_existing_verifiers_and_builder(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); data=root/'existing';data.mkdir()
            for name in ('exefs/main','exefs/sdk','romfs/romfs.bin'):
                p=data/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'fixture')
            args=adapter.arguments(['--recomplauncher-prepare','--game',str(data)])
            with patch('newsnap.home_state.verify', return_value={'verified':True}) as verify, \
                 patch('newsnap.maintenance.assess_runtime', return_value={'needs_rebuild':False}), \
                 patch('newsnap.launcher_settings.validate_runtime_data') as validate, \
                 patch('newsnap.build_kit.ensure_build_kit') as kit:
                adapter.prepare(root,args)
            verify.assert_called_once_with(root)
            validate.assert_called_once_with(root)
            kit.assert_not_called()
            self.assertEqual(json.loads((root/'launcher-settings.json').read_text())['game_data_relative'], 'existing')

    def test_encrypted_container_requires_update_and_explicit_keys_before_import(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); base=root/'base.nsp';base.write_bytes(b'fixture')
            args=adapter.arguments(['--recomplauncher-prepare','--game',str(base)])
            with patch('newsnap.importer.import_game') as imp:
                with self.assertRaisesRegex(ValueError,'update.*keys|keys.*update'):
                    adapter.prepare(root,args)
                imp.assert_not_called()

    def test_failed_preparation_is_nonzero_and_does_not_mark_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with contextlib.redirect_stderr(io.StringIO()), patch.object(adapter,'prepare',side_effect=ValueError('Wrong game')):
                self.assertEqual(adapter.main(['--recomplauncher-prepare','--game=bad'], root), 2)
            self.assertFalse((root/'recomplauncher-ready.json').exists())

    def test_completed_setup_alone_writes_ready_marker_and_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); out=io.StringIO()
            with patch.object(adapter,'prepare'), contextlib.redirect_stdout(out):
                self.assertEqual(adapter.main(['--recomplauncher-prepare','--game=fixture'],root),0)
            self.assertTrue((root/'recomplauncher-ready.json').is_file())
            self.assertIn('progress 1 ',out.getvalue())

    def test_no_implicit_download_without_bundled_or_explicit_kit(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{},clear=True):
            from newsnap.version import VERSION
            (Path(folder)/'MANIFEST.json').write_text(json.dumps({'version':VERSION,'source_revision':'a'*40}))
            (Path(folder)/'build-kits').mkdir()
            (Path(folder)/'build-kits/unrelated.zip').write_bytes(b'not the exact release kit')
            with patch('newsnap.build_kit.ensure_build_kit') as acquire:
                with self.assertRaisesRegex(ValueError,'kit|package'):
                    adapter.offline_kit(Path(folder))
                acquire.assert_not_called()

    def test_failed_reprepare_invalidates_previous_ready_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'recomplauncher-ready.json').write_text('{}')
            with contextlib.redirect_stderr(io.StringIO()), patch.object(adapter,'prepare',side_effect=ValueError('Wrong game')):
                self.assertEqual(adapter.main(['--recomplauncher-prepare','--game=bad'],root),2)
            self.assertFalse((root/'recomplauncher-ready.json').exists())

    def test_explicit_incompatible_video_combination_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                adapter.game_environment(Path(folder), {'upscaling':'off','frame_gen':'fsr'})

    def test_preserves_explicit_user_controller_layout(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'RECOMPLAUNCHER_PAD':'xbox'},clear=True):
            with patch('newsnap.launcher_settings.load_settings',return_value={'pad_layout':'nintendo'}):
                self.assertNotIn('AC_PAD_LAYOUT',adapter.game_environment(Path(folder),{}))

    def test_updated_release_rebuilds_without_requiring_the_original_dump_again(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch('newsnap.maintenance.assess_runtime',side_effect=[{'needs_rebuild':True},{'needs_rebuild':False}]), \
                 patch.object(adapter,'prepare') as prepare, \
                 patch('newsnap.launcher_settings.validate_runtime_data'), \
                 patch.object(adapter.subprocess,'Popen') as process, \
                 patch('newsnap.startup_assets.prepare_hd_shadows'):
                process.return_value.wait.return_value=0
                self.assertEqual(adapter.play(root,{}),0)
                prepare.assert_called_once()
                self.assertIsNone(prepare.call_args.args[1].game)

    def test_play_keeps_lock_through_reserved_restart_and_reports_crash(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);profile=root/'profile';profile.mkdir()
            state={'locked':False};calls=[]
            class Lock:
                def __init__(self,path): self.path=path
                def __enter__(self):state['locked']=True
                def __exit__(self,*args):state['locked']=False
            class Process:
                def wait(self):return 75 if len(calls)==1 else 9
            def start(command,**kw):
                self.assertTrue(state['locked']);calls.append(command);return Process()
            with patch('newsnap.launcher_settings.load_profile',return_value=profile), \
                 patch('newsnap.launcher_settings.ProfileLock',Lock), \
                 patch('newsnap.launcher_settings.validate_runtime_data'), \
                 patch('newsnap.maintenance.assess_runtime',return_value={'needs_rebuild':False}), \
                 patch.object(adapter.subprocess,'Popen',side_effect=start), \
                 patch('newsnap.startup_assets.prepare_hd_shadows') as assets:
                self.assertEqual(adapter.play(root, {}),9)
                self.assertEqual(assets.call_count,2)
            self.assertEqual(len(calls),2)
            self.assertNotIn('--boot',calls[0])
            self.assertFalse(state['locked'])
            self.assertEqual(len(list((root/'logs').glob('recomplauncher-game-*.log'))),2)


    def test_nup_prepare_needs_no_console_keys_and_uses_content_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); game=root/'renamed.bin'; game.write_bytes(b'NUP\x01'+bytes(124))
            args=adapter.arguments(['--recomplauncher-prepare','--game',str(game)])
            with patch.object(adapter,'offline_kit',return_value=root/'kit'), \
                 patch('newsnap.maintenance.run_build_command') as run, \
                 patch.object(adapter,'select_data_dir'), \
                 patch('newsnap.home_state.verify'), \
                 patch('newsnap.maintenance.assess_runtime',return_value={'needs_rebuild':False}), \
                 patch('newsnap.launcher_settings.validate_runtime_data'):
                adapter.prepare(root,args)
            command=run.call_args.args[0]
            self.assertIn('--nup',command)
            self.assertNotIn('--keys',command)


if __name__ == '__main__':unittest.main()
