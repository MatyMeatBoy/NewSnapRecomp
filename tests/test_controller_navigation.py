from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from newsnap.controller_navigation import InputActions, Navigation


def pad(**buttons):
    return {'id': 7, 'recognized': True, 'connected': True, 'buttons': buttons, 'axes': {}}


class InputTests(TestCase):
    def test_requires_neutral_before_accepting_held_button(self):
        actions = InputActions()
        self.assertEqual(actions.update([pad(south=True)], 0), [])
        self.assertEqual(actions.update([pad()], .1), [])
        self.assertEqual(actions.update([pad(south=True)], .2), ['activate'])
        self.assertEqual(actions.update([pad(south=True)], 1), [])

    def test_direction_repeat_and_axis_deadzone(self):
        actions = InputActions()
        actions.update([pad()], 0)
        self.assertEqual(actions.update([pad(dpad_down=True)], .1), ['down'])
        self.assertEqual(actions.update([pad(dpad_down=True)], .2), [])
        self.assertEqual(actions.update([pad(dpad_down=True)], .6), ['down'])
        self.assertEqual(actions.update([{**pad(), 'axes': {'leftx': 7000}}], .7), [])
        self.assertEqual(actions.update([{**pad(), 'axes': {'leftx': 25000}}], .8), ['right'])

    def test_disconnect_and_changed_controller_require_neutral(self):
        actions = InputActions(); actions.update([pad()], 0)
        self.assertEqual(actions.update([], 1), [])
        self.assertEqual(actions.update([{**pad(south=True), 'id': 8}], 2), [])
        actions.update([{**pad(), 'id': 8}], 3)
        self.assertEqual(actions.update([{**pad(east=True), 'id': 8}], 4), ['back'])

    def test_does_not_merge_or_use_unmapped_controllers(self):
        actions = InputActions()
        self.assertEqual(actions.update([{**pad(south=True), 'recognized': False}], 0), [])
        actions.update([pad(), {**pad(), 'id': 8}], 1)
        self.assertEqual(actions.update([pad(), {**pad(south=True), 'id': 8}], 2), [])


class OwnershipTests(TestCase):
    def navigator(self):
        root = SimpleNamespace(after=Mock(return_value='timer'), after_cancel=Mock())
        session = SimpleNamespace(navigation_snapshot=Mock(return_value=[pad()]), close=Mock())
        active = [True]
        nav = Navigation(root, Mock(return_value=session), foreground=lambda: active[0])
        nav.dispatch = Mock()
        return nav, session, active

    def test_no_session_or_input_when_other_app_is_foreground(self):
        nav, session, active = self.navigator(); active[0] = False
        nav.start()
        nav.session_factory.assert_not_called()
        nav.dispatch.assert_not_called()

    def test_loses_focus_releases_session_and_clears_held_state(self):
        nav, session, active = self.navigator(); nav.start()
        active[0] = False; nav._poll()
        session.close.assert_called_once()
        self.assertIsNone(nav.session)
        nav.dispatch.assert_not_called()

    def test_pause_close_cancel_and_release_exactly_once(self):
        nav, session, active = self.navigator(); nav.start()
        nav.pause(); nav.close(); nav.close()
        session.close.assert_called_once()
        self.assertTrue(nav.closed)

    def test_failed_snapshot_releases_and_reports_error(self):
        nav, session, active = self.navigator()
        nav.on_error = Mock(); session.navigation_snapshot.side_effect = RuntimeError('input failed')
        nav.start()
        session.close.assert_called_once()
        nav.on_error.assert_called_once()
        self.assertIsNone(nav.session)

    def test_next_poll_is_scheduled_before_modal_activation(self):
        nav, session, active = self.navigator(); nav.start()
        session.navigation_snapshot.return_value = [pad(south=True)]
        nav.dispatch.side_effect = lambda action: self.assertIsNotNone(nav.timer)
        nav.on_error = Mock()
        nav._poll()
        nav.dispatch.assert_called_once_with('activate')
        nav.on_error.assert_not_called()


class DispatchTests(TestCase):
    def navigator(self, kind):
        scope = Mock(); scope.winfo_toplevel.return_value = scope
        widget = Mock(); widget.winfo_toplevel.return_value = scope
        widget.winfo_class.return_value = kind
        widget.winfo_viewable.return_value = True
        widget.cget.return_value = 'normal'
        root = Mock(); root.grab_current.return_value = scope; root.focus_get.return_value = widget
        return Navigation(root, Mock()), widget, scope

    def test_activate_button_invokes_only_local_widget(self):
        nav, widget, scope = self.navigator('TButton')
        nav.dispatch('activate')
        widget.invoke.assert_called_once_with()

    def test_combobox_activate_cycles_without_native_popup(self):
        nav, widget, scope = self.navigator('TCombobox')
        widget.cget.return_value = ('one', 'two'); widget.current.return_value = 0
        nav.dispatch('activate')
        widget.current.assert_called_with(1)
        widget.event_generate.assert_called_once_with('<<ComboboxSelected>>')

    def test_modal_back_targets_grab_owner(self):
        nav, widget, scope = self.navigator('Listbox')
        nav.dispatch('back')
        scope.event_generate.assert_called_once_with('<<ControllerBack>>')
        widget.event_generate.assert_not_called()

    def test_direction_on_list_stays_local(self):
        nav, widget, scope = self.navigator('Listbox')
        nav.dispatch('down')
        widget.event_generate.assert_called_once_with('<Down>')
