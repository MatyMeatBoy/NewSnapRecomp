"""Failed controller windows cannot release a later launcher operation."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

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

    def test_failed_initialization_restores_modal_navigation(self):
        for failure in ('lock', 'session'):
            with self.subTest(failure=failure):
                panel=self.panel()
                panel.launcher.profile='fixture-profile'
                panel.launcher.project='fixture-install'
                panel.launcher.navigation=SimpleNamespace(resume=Mock())
                lock=MagicMock()
                if failure=='lock':lock.__enter__.side_effect=RuntimeError('profile in use')
                with patch('newsnap.controller_ui.settings.ProfileLock',return_value=lock), \
                     patch('newsnap.controller_probe.launcher_runtime',return_value='fixture-sdl'), \
                     patch('newsnap.controller_probe.Session',side_effect=RuntimeError('SDL failed')):
                    panel.initialize()
                self.assertIsNone(panel.session)
                self.assertIsNone(panel.lock)
                panel.launcher.navigation.resume.assert_called_once_with()
                panel.launcher._set_busy.assert_called_once_with(False)
                panel.window.destroy.assert_not_called()

    def test_successful_session_keeps_face_buttons_diagnostic_only(self):
        panel=self.panel()
        panel.launcher.profile='fixture-profile'
        panel.launcher.project='fixture-install'
        panel.launcher.navigation=SimpleNamespace(resume=Mock())
        panel.poll=Mock()
        with patch('newsnap.controller_ui.settings.ProfileLock',return_value=MagicMock()), \
             patch('newsnap.controller_probe.launcher_runtime',return_value='fixture-sdl'), \
             patch('newsnap.controller_probe.Session',return_value=SimpleNamespace(sdl_version='3.2.0')):
            panel.initialize()
        panel.poll.assert_called_once_with()
        panel.launcher.navigation.resume.assert_not_called()
        self.assertTrue(panel.owns_busy)

    def test_snapshot_failure_releases_session_before_resuming_navigation(self):
        panel=self.panel()
        session=SimpleNamespace(snapshot=Mock(side_effect=RuntimeError('disconnected')),close=Mock())
        panel.session=session
        panel.launcher.navigation=SimpleNamespace(resume=Mock())
        def resumed():
            session.close.assert_called_once_with()
            self.assertIsNone(panel.session)
        panel.launcher.navigation.resume.side_effect=resumed
        panel.poll()
        panel.launcher.navigation.resume.assert_called_once_with()

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
