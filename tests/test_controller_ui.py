"""Failed controller windows cannot release a later launcher operation."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from newsnap.controller_ui import ControllerTest


class ControllerOwnershipTests(TestCase):
    def panel(self):
        panel=ControllerTest.__new__(ControllerTest)
        panel.launcher=SimpleNamespace(_set_busy=Mock(),root=SimpleNamespace(after_cancel=Mock()))
        panel.window=SimpleNamespace(destroy=Mock())
        panel.state=SimpleNamespace(configure=Mock())
        panel.session=None;panel.lock=None;panel.closed=False;panel.after_id=None
        panel.owns_busy=True
        return panel

    def test_closing_failed_window_does_not_release_later_operation(self):
        panel=self.panel()
        panel._release()
        panel.launcher._set_busy.reset_mock()  # A later operation now owns busy.
        panel.close()
        panel.launcher._set_busy.assert_not_called()
        panel.window.destroy.assert_called_once_with()

    def test_cleanup_failure_still_releases_busy_once(self):
        panel=self.panel()
        panel.session=SimpleNamespace(close=Mock(side_effect=RuntimeError('SDL close failed')))
        panel.lock=SimpleNamespace(__exit__=Mock(side_effect=OSError('lock close failed')))
        panel._release()
        panel.launcher._set_busy.assert_called_once_with(False)
        self.assertIsNone(panel.session)
        self.assertIsNone(panel.lock)
        panel._release()
        panel.launcher._set_busy.assert_called_once_with(False)
