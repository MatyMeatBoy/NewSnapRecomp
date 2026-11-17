import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from newsnap import launcher_language as language

class LauncherLanguageTests(unittest.TestCase):
    def tearDown(self):
        language.set_language('es')

    def test_windows_display_language_wins_over_regional_locale(self):
        with patch.object(language, 'windows_ui_language', return_value='en-US'), patch.object(language.locale, 'getlocale', return_value=('es_CL', 'UTF-8')):
            self.assertEqual(language.system_language(), 'en')
        with patch.object(language, 'windows_ui_language', return_value='es-MX'):
            self.assertEqual(language.system_language(), 'es')
        with patch.object(language, 'windows_ui_language', return_value='ja-JP'):
            self.assertEqual(language.system_language(), 'en')

    def test_first_run_and_explicit_choice_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(language, 'system_language', return_value='en'):
                self.assertEqual(language.load_language(root), 'en')
                language.save_language(root, 'es')
                self.assertEqual(language.load_language(root), 'es')
            with self.assertRaises(ValueError): language.save_language(root, 'bogus')

    def test_corrupt_preference_falls_back_and_other_files_are_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'launcher-settings.json').write_text('{"game_data_path":"D:/My Data"}')
            language.preference_path(root).write_text('[]')
            with patch.object(language, 'system_language', return_value='en'):
                self.assertEqual(language.load_language(root), 'en')
            language.save_language(root, 'es')
            self.assertEqual(json.loads((root/'launcher-settings.json').read_text()), {'game_data_path':'D:/My Data'})

    def test_translation_is_explicit_and_keeps_paths_and_machine_values(self):
        language.set_language('en')
        self.assertEqual(language.tr('Jugar'), 'Play')
        self.assertEqual(language.tr('Cargar GameData…'), 'Load GameData…')
        for value in ('D:/Juego/My Photos', 'fps', 'fullscreen', 'off'):
            self.assertEqual(language.tr(value), value)
        language.set_language('es')
        self.assertEqual(language.tr('Jugar'), 'Jugar')

    def test_home_has_no_second_primary_action(self):
        source=(Path(__file__).resolve().parents[1]/'newsnap/home_ui.py').read_text(encoding='utf-8')
        self.assertNotIn('launcher.play_button=ttk.Button', source)
        cover=(Path(__file__).resolve().parents[1]/'newsnap/hero_ui.py').read_text(encoding='utf-8')
        self.assertNotIn('LENTAL · CUADERNO DE CAMPO', cover)
        self.assertNotIn('Encuadra tu próxima aventura.', cover)


class RuntimeActionAssessmentTests(unittest.TestCase):
    def test_actual_integrity_assessment_is_cached_and_invalidated_by_dependencies(self):
        import queue
        from types import SimpleNamespace
        from newsnap.home_ui import HomePanel
        from newsnap.version import VERSION
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/'GameData';data.mkdir()
            (data/'newsnap.exe').write_bytes(b'fixture')
            panel=SimpleNamespace(launcher=SimpleNamespace(project=root),events=queue.Queue())
            def state():return {'loaded':True,'verified':True,'directory':str(data),'runtime_version':VERSION}
            def thread(target,daemon):return SimpleNamespace(start=target)
            with patch('newsnap.home_ui.settings.is_release_layout',return_value=True), patch('newsnap.home_ui.threading.Thread',side_effect=thread), patch('newsnap.maintenance.assess_runtime',return_value={'needs_rebuild':True,'reason':'damaged dependency'}) as assess:
                value=state();HomePanel.runtime_state(panel,value)
                self.assertTrue(value['runtime_checking'])
                kind,result=panel.events.get_nowait();self.assertEqual(kind,'runtime_assessed')
                panel._runtime_assessment=result;panel._runtime_pending_key=None
                value=state();HomePanel.runtime_state(panel,value)
                self.assertTrue(value['needs_build']);self.assertFalse(value['runtime_checking'])
                assess.assert_called_once_with(root)
                (data/'SDL3.dll').write_bytes(b'changed')
                value=state();HomePanel.runtime_state(panel,value)
                self.assertTrue(value['runtime_checking']);self.assertEqual(assess.call_count,2)

    def test_checking_state_cannot_start_play_or_rebuild(self):
        from newsnap.play_action import play_action
        state={'loaded':True,'verified':True,'runtime_checking':True}
        result=play_action(state)
        self.assertEqual(result['action'],'check');self.assertFalse(result['enabled'])

    def test_assessment_does_not_release_an_unrelated_busy_operation(self):
        import queue
        from types import SimpleNamespace
        from newsnap.home_ui import HomePanel
        events=queue.Queue();events.put(('runtime_assessed',('old',{'needs_rebuild':True})))
        busy=unittest.mock.Mock();refresh=unittest.mock.Mock()
        panel=SimpleNamespace(events=events,_runtime_pending_key='new',refresh=refresh,poll=unittest.mock.Mock(),
            launcher=SimpleNamespace(_set_busy=busy,root=SimpleNamespace(after=unittest.mock.Mock())))
        HomePanel.poll(panel)
        busy.assert_not_called();refresh.assert_not_called()


class LauncherConstructionTests(unittest.TestCase):
    def test_english_pages_preset_values_and_language_restart_keep_pending_settings(self):
        import tkinter as tk
        from newsnap.launcher import Launcher
        try:r=tk.Tk()
        except tk.TclError as error:self.skipTest(str(error))
        r.withdraw()
        try:
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);language.save_language(root,'en')
                app=Launcher(r,project=root,check_updates=False);r.update()
                self.assertEqual(app.home.action['label'],'Load game…')
                self.assertFalse(hasattr(app,'play_button'))
                self.assertEqual(app.tabs.tab(app.play_tab,'text'),'Home')
                for page in (app.play_tab,app.album_tab,app.options_tab,app.controls_tab,app.mods_tab,app.update_tab):
                    app.tabs.select(page);r.update()
                app.quality_preset.set('Low');app._apply_quality_preset()
                self.assertEqual(app._option_values()['render_scale'],'70')
                app.launcher_language.set('Español');app._change_launcher_language()
                self.assertTrue(app.restart_requested)
                self.assertEqual(app.pending_options['render_scale'],'70')
                self.assertEqual(language.load_language(root),'es')
                r2=tk.Tk();r2.withdraw()
                try:
                    app2=Launcher(r2,project=root,check_updates=False)
                    app2._set_option_values(app.pending_options);r2.update()
                    self.assertEqual(app2.tabs.tab(app2.play_tab,'text'),'Inicio')
                    self.assertEqual(app2._option_values()['render_scale'],'70')
                finally:r2.destroy()
        finally:
            try:r.destroy()
            except tk.TclError:pass
            language.set_language('es')
