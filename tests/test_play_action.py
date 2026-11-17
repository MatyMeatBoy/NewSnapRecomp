"""The main button says what a press does: «Verificar» until the game data is verified, then «Jugar»."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from newsnap.home_ui import HomePanel
from newsnap.launcher import Launcher
from newsnap.play_action import play_action


class PlayActionTests(TestCase):
    def test_label_follows_the_state_of_the_game_data(self):
        cases = (
            ({'loaded': False, 'verified': False}, {}, ('Cargar juego…', 'load', 'play', True)),
            ({'loaded': True, 'verified': False}, {}, ('Verificar', 'verify', 'verify', True)),
            ({'loaded': True, 'verified': True}, {}, ('Jugar', 'play', 'play', True)),
            ({'loaded': True, 'verified': False}, {'busy': True, 'verifying': True}, ('Verificando…', 'verify', 'verify', False)),
            ({'loaded': True, 'verified': False}, {'busy': True}, ('Verificar', 'verify', 'verify', False)),   # a rebuild runs
            ({'loaded': True, 'verified': True}, {'busy': True}, ('Jugar', 'play', 'play', False)),            # the game runs
            ({'loaded': False, 'verified': True}, {}, ('Cargar juego…', 'load', 'play', True)),                        # no data: never «verified»
            ({}, {}, ('Cargar juego…', 'load', 'play', True)),
        )
        for state, options, expected in cases:
            with self.subTest(state=state, options=options):
                action = play_action(state, **options)
                self.assertEqual((action['label'], action['action'], action['kind'], action['enabled']), expected)

    def panel(self, state, busy=False, checking=False):
        launcher = SimpleNamespace(busy=busy, play_button=Mock(), sidebar=Mock())
        return SimpleNamespace(launcher=launcher, last_state=state, checking=checking)

    def test_sidebar_is_the_only_primary_action(self):
        panel = self.panel({'loaded': True, 'verified': False})
        HomePanel.sync_action(panel)
        panel.launcher.play_button.configure.assert_not_called()
        panel.launcher.sidebar.set_action.assert_called_once_with('Verificar', 'verify', True)

        panel = self.panel({'loaded': True, 'verified': False}, busy=True, checking=True)
        HomePanel.sync_action(panel)
        panel.launcher.play_button.configure.assert_not_called()
        panel.launcher.sidebar.set_action.assert_called_once_with('Verificando…', 'verify', False)

        panel = self.panel({'loaded': True, 'verified': True})      # the verification ended well: «Jugar» by itself
        HomePanel.sync_action(panel)
        panel.launcher.play_button.configure.assert_not_called()
        panel.launcher.sidebar.set_action.assert_called_once_with('Jugar', 'play', True)

    def test_missing_runtime_exposes_build_before_play(self):
        state={'loaded':True,'verified':True,'needs_build':True}
        self.assertEqual(play_action(state)['action'], 'build')
        self.assertEqual(play_action(state)['label'], 'Construir juego')
        self.assertFalse(play_action(state,busy=True)['enabled'])
        home=SimpleNamespace(refresh=Mock(return_value=state),verify=Mock())
        maintenance=SimpleNamespace(start=Mock())
        app=SimpleNamespace(busy=False,home=home,updates=SimpleNamespace(maintenance=maintenance),launch=Mock())
        Launcher.primary_action(app)
        maintenance.start.assert_called_once_with(resume_game=False)
        app.launch.assert_not_called()

    def test_pressing_verify_verifies_without_starting_the_game(self):
        home = SimpleNamespace(refresh=Mock(return_value={'loaded': True, 'verified': False}), verify=Mock())
        app = SimpleNamespace(busy=False, home=home, launch=Mock())
        Launcher.primary_action(app)
        home.verify.assert_called_once_with()           # no resume_game: the button becomes «Jugar» and waits
        app.launch.assert_not_called()

    def test_pressing_play_plays_and_missing_data_keeps_the_choose_data_flow(self):
        for state in ({'loaded': True, 'verified': True}, {'loaded': False, 'verified': False}):
            home = SimpleNamespace(refresh=Mock(return_value=state), verify=Mock())
            app = SimpleNamespace(busy=False, home=home, launch=Mock())
            Launcher.primary_action(app)
            app.launch.assert_called_once_with()
            home.verify.assert_not_called()

    def test_busy_launcher_ignores_the_press(self):
        home = SimpleNamespace(refresh=Mock(), verify=Mock())
        app = SimpleNamespace(busy=True, home=home, launch=Mock())
        Launcher.primary_action(app)
        home.refresh.assert_not_called()
        app.launch.assert_not_called()

    def test_a_direct_play_request_still_verifies_and_resumes(self):
        home = SimpleNamespace(refresh=Mock(return_value={'loaded': True, 'verified': False}), verify=Mock())
        app = SimpleNamespace(busy=False, home=home)
        Launcher.launch(app)                             # --play, Steam, the desktop shortcut
        home.verify.assert_called_once_with(resume_game=True)
