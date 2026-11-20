from pathlib import Path
import queue
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from newsnap.backup_ui import BackupPanel


class BackupPanelTests(unittest.TestCase):
    def test_backup_consent_is_localized_without_changing_cloud_scope(self):
        from newsnap import launcher_language as language
        from newsnap.backup_ui import CONSENT
        before=language.current_language(); self.addCleanup(language.set_language,before)
        language.set_language('es')
        self.assertTrue(language.tr(CONSENT).startswith('¿Activar'))
        self.assertIn('RecompLauncher no sube',language.tr(CONSENT))
        language.set_language('en')
        self.assertTrue(language.tr(CONSENT).startswith('Enable complete profile backups'))
        self.assertIn('RecompLauncher does not upload',language.tr(CONSENT))

    def panel(self):
        panel = BackupPanel.__new__(BackupPanel)
        app = SimpleNamespace(project=Path('fixture'), profile=Path('original-profile'), busy=False,
                              root=Mock(), profile_text=Mock(), preview=None,
                              photos=['photo'], thumbnails=['thumb'], page=2,
                              reload_options=Mock(), draw_page=Mock(), _tab_changed=Mock())
        def set_busy(value):
            app.busy = value
        app._set_busy = Mock(side_effect=set_busy)
        panel.launcher = app
        panel.frame = Mock()
        panel.events = queue.Queue()
        panel.cancel = threading.Event()
        panel.running = panel.closed = False
        panel.after_id = None
        panel.message = Mock()
        panel.folder = Mock()
        panel.buttons = [Mock() for _ in range(4)]
        panel.cancel_button = Mock()
        return panel

    def test_busy_commands_do_not_open_dialogs_or_change_configuration(self):
        panel = self.panel()
        panel.launcher.busy = True
        with patch('newsnap.backup_ui.file_picker.askdirectory') as directory, \
                patch('newsnap.backup_ui.file_picker.askopenfilename') as archive, \
                patch('newsnap.backup_ui.backup_settings.disable_backup_settings') as disable:
            panel.choose_folder()
            panel.disable()
            panel.backup_now()
            panel.restore()
        directory.assert_not_called()
        archive.assert_not_called()
        disable.assert_not_called()
        panel._sync_buttons()
        for button in panel.buttons:
            button.configure.assert_called_with(state='disabled')

    def test_failed_restore_never_changes_selected_profile(self):
        panel = self.panel()
        panel.running = True
        panel.launcher.busy = True
        with patch('newsnap.backup_ui.settings.save_profile') as save, \
                patch.object(panel, '_error') as error:
            panel._complete('restore', None, 'corrupt archive')
        save.assert_not_called()
        error.assert_called_once_with('corrupt archive')
        self.assertEqual(panel.launcher.profile, Path('original-profile'))
        self.assertFalse(panel.launcher.busy)

    def test_verified_restore_selects_only_on_ui_completion(self):
        panel = self.panel()
        panel.running = True
        with patch('newsnap.backup_ui.settings.save_profile') as save:
            panel._complete('restore', Path('new-profile'), None)
        save.assert_called_once_with(Path('fixture'), Path('new-profile'))
        self.assertEqual(panel.launcher.profile, Path('new-profile'))
        self.assertEqual(panel.launcher.photos, [])
        self.assertEqual(panel.launcher.thumbnails, [])
        self.assertEqual(panel.launcher.page, 0)
        panel.launcher.profile_text.set.assert_called_once_with('new-profile')
        panel.launcher.reload_options.assert_called_once()
        panel.launcher.draw_page.assert_called_once()

    def test_worker_communicates_by_queue_without_tk_callbacks(self):
        panel = self.panel()
        main_thread = threading.get_ident()
        seen = []
        def work(report, cancel):
            seen.append(threading.get_ident())
            report('progress')
            return Path('new-snapshot.zip')
        panel._start('backup', work)
        self.assertEqual(panel.events.get(timeout=3), ('progress', 'progress'))
        self.assertEqual(panel.events.get(timeout=3), ('done', 'backup', Path('new-snapshot.zip'), None))
        self.assertNotEqual(seen, [main_thread])
        panel.launcher.root.after.assert_not_called()

    def test_destroy_cancels_work_and_removes_poll_callback(self):
        panel = self.panel()
        panel.after_id = 'pending'
        panel._destroyed(SimpleNamespace(widget=panel.frame))
        self.assertTrue(panel.closed)
        self.assertTrue(panel.cancel.is_set())
        panel.launcher.root.after_cancel.assert_called_once_with('pending')
        panel._poll()
        panel.launcher.root.after.assert_not_called()


if __name__ == '__main__':
    unittest.main()
