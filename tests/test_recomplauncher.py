import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    adapter = importlib.import_module('newsnap.recomplauncher')
except ModuleNotFoundError:
    adapter = None


class RecompLauncherTests(unittest.TestCase):
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
                 patch.object(adapter.subprocess,'Popen') as process:
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
                 patch.object(adapter.subprocess,'Popen',side_effect=start):
                self.assertEqual(adapter.play(root, {}),9)
            self.assertEqual(len(calls),2)
            self.assertNotIn('--boot',calls[0])
            self.assertFalse(state['locked'])
            self.assertEqual(len(list((root/'logs').glob('recomplauncher-game-*.log'))),2)


if __name__ == '__main__':unittest.main()
