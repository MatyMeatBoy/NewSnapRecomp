from unittest import TestCase
from unittest.mock import Mock, patch

from newsnap import controller_dialogs as dialogs


class DialogTests(TestCase):
    def setUp(self):
        from newsnap import launcher_language as language
        self.addCleanup(language.set_language,language.current_language())
        language.set_language('es')

    def test_controller_hint_uses_selected_language(self):
        from newsnap import launcher_language as language
        before=language.current_language()
        self.addCleanup(language.set_language,before)
        language.set_language('es')
        self.assertEqual(language.tr('Sur: seleccionar · Este: volver'),'Sur: seleccionar · Este: volver')
        language.set_language('en')
        self.assertEqual(language.tr('Sur: seleccionar · Este: volver'),'South: select · East: back')

    @patch('newsnap.controller_dialogs._message', return_value=False)
    def test_confirmation_cancel_is_false_and_default_is_cancel(self, message):
        from newsnap import launcher_language as language
        for selected,labels in (('es',('Cancelar','Aceptar')),('en',('Cancel','OK'))):
            with self.subTest(language=selected):
                language.set_language(selected)
                self.assertFalse(dialogs.askokcancel('Import', 'Continue?', parent='parent'))
                buttons=message.call_args.kwargs['buttons']
                self.assertEqual(tuple(language.tr(label) for label,value in buttons),labels)
                self.assertEqual(tuple(value for label,value in buttons),(False,True))
                self.assertEqual(message.call_args.kwargs['parent'],'parent')
                self.assertFalse(message.call_args.kwargs['cancel'])

    @patch('newsnap.controller_dialogs._message', return_value=True)
    def test_yes_no_and_info_compatibility(self, message):
        self.assertTrue(dialogs.askyesno('Replace', 'Replace?', parent='parent'))
        self.assertEqual(dialogs.showerror('Error', 'Unavailable', parent='parent'), 'ok')
        self.assertEqual(dialogs.showinfo('Info', 'Ready', parent='parent'), 'ok')

    def test_nested_modal_restores_previous_grab_and_focus(self):
        parent = Mock(); window = Mock(); focus = Mock()
        previous_grab = parent.grab_current.return_value
        previous_focus = parent.focus_get.return_value
        dialogs.modal(window, parent, focus)
        window.grab_set.assert_called_once_with()
        focus.focus_set.assert_called_once_with()
        parent.wait_window.assert_called_once_with(window)
        previous_grab.grab_set.assert_called_once_with()
        previous_focus.focus_set.assert_called_once_with()

    def test_destroyed_parent_widgets_do_not_receive_restored_focus(self):
        parent = Mock(); window = Mock(); focus = Mock()
        parent.grab_current.return_value.winfo_exists.return_value = False
        parent.focus_get.return_value.winfo_exists.return_value = False
        dialogs.modal(window, parent, focus)
        parent.grab_current.return_value.grab_set.assert_not_called()
        parent.focus_get.return_value.focus_set.assert_not_called()
