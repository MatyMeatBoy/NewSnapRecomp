from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import Mock, patch

from newsnap.controller_file_picker import Browser


class PickerLanguageTests(TestCase):
    def test_validation_message_uses_selected_language(self):
        from newsnap import launcher_language as language
        before=language.current_language(); self.addCleanup(language.set_language,before)
        with tempfile.TemporaryDirectory() as folder:
            browser=Browser(Path(folder))
            language.set_language('es')
            with self.assertRaisesRegex(ValueError,'Elige un archivo existente'):
                browser.choose('missing')
            language.set_language('en')
            with self.assertRaisesRegex(ValueError,'Choose an existing file'):
                browser.choose('missing')


class BrowserTests(TestCase):
    def test_filters_case_insensitively_but_keeps_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'directory').mkdir()
            for name in ('game.NSP', 'update.nsz', 'keys.keys', '.hidden.nsp'):
                (root/name).touch()
            browser = Browser(root, filetypes=[('Game', '*.nsp *.nsz')])
            self.assertEqual([p.name for p in browser.entries()], ['directory', '.hidden.nsp', 'game.NSP', 'update.nsz'])

    def test_directory_mode_cannot_choose_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'game.nsp').touch()
            browser = Browser(root, mode='directory')
            self.assertEqual(browser.entries(), [])
            self.assertEqual(browser.choose(), root)
            with self.assertRaises(ValueError): browser.choose(root/'game.nsp')

    def test_open_requires_existing_file_and_navigation_does_not_select_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); child = root/'child'; child.mkdir()
            browser = Browser(root)
            browser.enter(child)
            self.assertEqual(browser.directory, child)
            with self.assertRaises(ValueError): browser.choose()
            with self.assertRaises(ValueError): browser.choose(child/'missing')

    def test_save_adds_default_extension_and_checks_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); browser = Browser(root, mode='save', defaultextension='.json')
            self.assertEqual(browser.choose('report'), root/'report.json')
            with self.assertRaises(ValueError): browser.choose('missing/report')

    def test_all_file_pattern_includes_extensionless_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'README').touch()
            self.assertEqual(Browser(root, filetypes=[('All', '*.*')]).entries(), [root/'README'])

    def test_inaccessible_directory_does_not_change_current_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); child = root/'child'; child.mkdir()
            browser = Browser(root)
            with patch('newsnap.controller_file_picker.os.scandir', side_effect=PermissionError('Denied')):
                with self.assertRaises(PermissionError): browser.enter(child)
            self.assertEqual(browser.directory, root)

    def test_select_this_folder_uses_current_directory(self):
        from newsnap.controller_file_picker import FilePicker
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); child = root/'child'; child.mkdir()
            picker = FilePicker.__new__(FilePicker)
            picker.browser = Browser(root, mode='directory')
            picker.window = Mock(); picker.error = Mock(); picker.selected = Mock(return_value=child)
            picker.select()
            self.assertEqual(picker.result, str(root))
