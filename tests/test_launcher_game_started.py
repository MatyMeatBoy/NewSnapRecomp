"""Once the game is up the launcher leaves the screen, stays alive behind it, and comes back only on failure."""
from pathlib import Path
import queue
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from newsnap.launcher import Launcher

ROOT = Path(__file__).resolve().parents[1]


def launcher():
    app = Launcher.__new__(Launcher)
    app.root = Mock()
    app.events = queue.Queue()
    app.home = SimpleNamespace(progress=Mock(), refresh=Mock())
    app.status = Mock()
    app.display = Mock()
    app._set_busy = Mock()
    app.reload_options = Mock()
    app._tab_changed = Mock()
    app._auto_hd_shadows = Mock(return_value=False)
    return app


class GameStartedTests(TestCase):
    def test_game_started_finishes_the_note_and_hides_the_window_once(self):
        app = launcher()
        app._handle(('game_started', None))
        app.home.progress.finish.assert_called_once_with('Juego iniciado')
        app.root.withdraw.assert_called_once_with()
        self.assertTrue(app.hidden_for_game)
        app.root.destroy.assert_not_called()          # the process stays: profile lock, restarts, session log
        app._handle(('game_started', None))           # the runtime reports it twice per start
        app.root.withdraw.assert_called_once_with()

    def test_poll_delivers_queued_events_and_keeps_polling(self):
        app = launcher()
        app.events.put(('status', 'Expedición en curso · cierra el juego para volver'))
        app.events.put(('game_started', None))
        app._poll()
        app.status.set.assert_called_once_with('Expedición en curso · cierra el juego para volver')
        app.root.withdraw.assert_called_once_with()
        app.root.after.assert_called_once_with(100, app._poll)

    def test_failed_game_brings_the_window_back_with_the_error(self):
        app = launcher()
        app._handle(('game_started', None))
        with patch('newsnap.launcher.messagebox.showerror') as showerror:
            app._handle(('finished', 'El juego se cerró con un error.'))
        app.root.deiconify.assert_called_once_with()
        self.assertFalse(app.hidden_for_game)
        showerror.assert_called_once()
        app.home.progress.finish.assert_called_with('No se pudo iniciar o continuar el juego', error=True)

    def test_normal_end_closes_the_hidden_launcher(self):
        app = launcher()
        app._handle(('game_started', None))
        app._handle(('finished', None))
        app.root.deiconify.assert_not_called()
        app.root.after.assert_called_once_with(300, app.close)

    def test_hd_shadows_build_keeps_the_launcher_after_the_game(self):
        app = launcher()
        app._auto_hd_shadows.return_value = True
        app._handle(('game_started', None))
        app._handle(('finished', None))
        app.root.after.assert_not_called()

    def test_there_is_one_game_started_branch(self):
        source = (ROOT / 'newsnap/launcher.py').read_text(encoding='utf-8')
        self.assertEqual(source.count("kind == 'game_started'"), 1)
