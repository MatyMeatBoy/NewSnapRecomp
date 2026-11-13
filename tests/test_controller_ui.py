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

    def test_disconnect_clears_picture_and_selects_another_connected_pad(self):
        panel=self.panel();panel.art=SimpleNamespace(set_buttons=Mock())
        panel.selector=SimpleNamespace(configure=Mock(),current=Mock(),set=Mock())
        panel.controller_ids=[];panel.controllers={};panel.selected_controller=None
        first={'id':11,'connected':True,'name':'First'}
        second={'id':22,'connected':True,'name':'Second'}
        panel.show_controllers([first,second])
        panel.selector.current.return_value=1
        panel.select_controller()
        panel.art.set_buttons.assert_called_with(second)
        panel.show_controllers([first,{**second,'connected':False}])
        panel.art.set_buttons.assert_called_with(first)
        panel.show_controllers([])
        panel.art.set_buttons.assert_called_with(None)
        self.assertIsNone(panel.selected_controller)
        self.assertIsNone(panel.session)
        self.assertIsNone(panel.lock)
        panel._release()
        panel.launcher._set_busy.assert_called_once_with(False)
