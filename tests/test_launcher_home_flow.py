"""Home launch must repair outdated runtimes before validating their shaders."""
from contextlib import nullcontext
from pathlib import Path
import queue
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from newsnap.launcher import Launcher
from newsnap.home_ui import HomePanel
from newsnap import launcher_settings as settings
from newsnap.paths import select_data_dir


class HomeLaunchFlowTests(TestCase):
    def worker(self, needs_rebuild):
        app=Launcher.__new__(Launcher)
        app.project=Path('fixture');app.events=queue.Queue();app.process=None
        app._execute_game=Mock()
        with patch('newsnap.launcher.settings.ProfileLock',return_value=nullcontext()), \
             patch('newsnap.launcher.settings.is_release_layout',return_value=True), \
             patch('newsnap.maintenance.assess_runtime',return_value={'needs_rebuild':needs_rebuild}), \
             patch('newsnap.launcher.settings.shader_preparation_required',return_value=True):
            app._run_game(Path('fixture/profile'),None)
        app._execute_game.assert_not_called()
        return app.events.get_nowait(),app.events.empty()

    def test_missing_shader_library_does_not_prevent_runtime_rebuild(self):
        event,empty=self.worker(True)
        self.assertEqual(event,('maintenance_needed',None))
        self.assertTrue(empty)

    def test_fresh_rebuilt_runtime_launches_without_shader_recordings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data=root/'GameData';data.mkdir()
            marker=data/'newsnap-game.json'
            marker.write_text('{"shader_preparation_required": true}',encoding='utf-8')
            original=marker.read_bytes()
            app=Launcher.__new__(Launcher)
            app.project=root;app.events=queue.Queue();app.process=None
            app._execute_game=Mock()
            with patch('newsnap.launcher.settings.ProfileLock',return_value=nullcontext()), \
                 patch('newsnap.launcher.settings.is_release_layout',return_value=True), \
                 patch('newsnap.maintenance.assess_runtime',return_value={'needs_rebuild':False}):
                app._run_game(root/'profile',None)
            app._execute_game.assert_called_once_with(root/'profile',None)
            self.assertEqual(marker.read_bytes(),original)
            events=list(app.events.queue)
            self.assertTrue(any(e[0]=='preparation_fallback' for e in events))
            self.assertIn(('finished',None),events)
            self.assertFalse(any(e[0]=='maintenance_needed' for e in events))

    def test_available_preparation_failure_stops_before_game_and_keeps_pending_marker(self):
        self.preparation_outcome(1)

    def test_available_preparation_success_clears_pending_only_before_game(self):
        self.preparation_outcome(0)

    def preparation_outcome(self,code):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data=root/'GameData';data.mkdir()
            marker=data/'newsnap-game.json'
            marker.write_text('{"shader_preparation_required": true}',encoding='utf-8')
            original=marker.read_bytes();app=Launcher.__new__(Launcher)
            app.project=root;app.events=queue.Queue();app.process=None
            process=SimpleNamespace(wait=Mock(return_value=code),pid=42)
            calls=[]
            def popen(command,**kwargs):
                calls.append((command,settings.shader_preparation_required(root)))
                return process
            with patch('newsnap.launcher.subprocess.Popen',side_effect=popen), \
                 patch('newsnap.launcher.settings.game_environment',return_value={}), \
                 patch('newsnap.launcher.settings.game_command',return_value=['native-game']), \
                 patch('newsnap.session_log.runtime_identity',return_value={}):
                if code:
                    with self.assertRaisesRegex(RuntimeError,'preparación'):
                        app._execute_game(root/'profile',['preparation-worker'])
                    self.assertEqual(marker.read_bytes(),original)
                    self.assertEqual(calls,[(['preparation-worker'],True)])
                else:
                    app._execute_game(root/'profile',['preparation-worker'])
                    self.assertEqual(calls,[(['preparation-worker'],True),(['native-game'],False)])

    def test_unloaded_home_loads_data_without_navigating_to_updates(self):
        app=SimpleNamespace(busy=False,home=SimpleNamespace(
            refresh=Mock(return_value={'loaded':False}),choose_data=Mock()),
            tabs=SimpleNamespace(select=Mock()))
        Launcher.launch(app)
        app.home.choose_data.assert_called_once_with()
        app.tabs.select.assert_not_called()

    def test_reselecting_data_keeps_its_custom_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data=root/'GameData'
            (data/'exefs').mkdir(parents=True);(data/'romfs').mkdir()
            for name in ('main','sdk'):(data/'exefs'/name).write_bytes(b'fixture')
            (data/'romfs/romfs.bin').write_bytes(b'fixture')
            select_data_dir(root,data)
            custom=data/'my-custom-profile'
            settings.save_profile(root,custom)
            preference=(data/'launcher.json').read_bytes()
            app=SimpleNamespace(busy=False,root=None,project=root,
                profile=custom,profile_text=SimpleNamespace(set=Mock()),
                status=SimpleNamespace(set=Mock()),_set_option_values=Mock())
            panel=SimpleNamespace(launcher=app,refresh=Mock())
            with patch('newsnap.home_ui.filedialog.askdirectory',return_value=str(data)):
                HomePanel.choose_data(panel)
            self.assertEqual(app.profile,custom)
            self.assertEqual((data/'launcher.json').read_bytes(),preference)
