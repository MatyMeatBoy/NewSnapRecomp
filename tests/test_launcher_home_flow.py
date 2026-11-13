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

    def test_current_runtime_with_required_missing_shaders_reports_failure(self):
        event,empty=self.worker(False)
        self.assertEqual(event[0],'finished')
        self.assertIn('Faltan las bibliotecas',event[1])
        self.assertTrue(empty)

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
