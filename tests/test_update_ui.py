import unittest
import queue
from types import SimpleNamespace
import sys
from pathlib import Path
from unittest.mock import patch, Mock

from newsnap import update_ui
from newsnap.version import RUNTIME_API, RUNTIME_CAPABILITIES


class RuntimeUpdateStatusTests(unittest.TestCase):
    def test_private_runtime_mismatch_cannot_block_public_launcher_repair(self):
        panel = update_ui.UpdatePanel.__new__(update_ui.UpdatePanel)
        panel.root = None
        panel.working = False
        panel.installing = False
        panel.release = SimpleNamespace(tag_name='v0.3.0-alpha')
        panel.launcher = SimpleNamespace(busy=False, project=Path('fixture'),
                                         save_options=Mock(return_value=False), _set_busy=Mock())
        panel.check, panel.install, panel.status = Mock(), Mock(), Mock()
        with patch.object(sys, 'frozen', True, create=True), \
             patch.object(update_ui.settings, 'validate_runtime_data', side_effect=ValueError('old runtime')), \
             patch.object(update_ui.messagebox, 'askyesno', return_value=True), \
             patch.object(update_ui.threading, 'Thread'):
            panel.download()
        panel.launcher.save_options.assert_not_called()
        panel.launcher._set_busy.assert_called_once_with(True)

    def test_background_check_failure_cannot_release_an_active_game(self):
        panel = update_ui.UpdatePanel.__new__(update_ui.UpdatePanel)
        panel.events = queue.Queue()
        panel.events.put(('error', 'GitHub request timed out'))
        panel.root = SimpleNamespace(after=Mock())
        panel.launcher = SimpleNamespace(busy=True, _set_busy=Mock())
        panel.check, panel.install, panel.status = Mock(), Mock(), Mock()
        panel.release = None
        panel.working = True
        panel.installing = False
        panel.poll()
        panel.launcher._set_busy.assert_not_called()
        self.assertTrue(panel.launcher.busy)

    def test_failed_download_releases_only_its_own_busy_state(self):
        panel = update_ui.UpdatePanel.__new__(update_ui.UpdatePanel)
        panel.events = queue.Queue()
        panel.events.put(('error', 'download checksum failed'))
        panel.root = SimpleNamespace(after=Mock())
        panel.launcher = SimpleNamespace(busy=True, _set_busy=Mock())
        panel.check, panel.install, panel.status = Mock(), Mock(), Mock()
        panel.release = None
        panel.working = True
        panel.installing = True
        panel.poll()
        panel.launcher._set_busy.assert_called_once_with(False)
        self.assertFalse(panel.installing)

    def test_old_runtime_requires_rebuild_instead_of_reporting_full_update(self):
        old = {'runtime_api': RUNTIME_API, 'runtime_version': '0.2-alpha',
               'capabilities': [c for c in RUNTIME_CAPABILITIES if c != 'controller-db']}
        with patch.object(update_ui.settings, 'validate_runtime_data', return_value=old):
            compatible, message = update_ui.runtime_update_status(Path('fixture'))
        self.assertFalse(compatible)
        self.assertIn('recompilar', message)
        self.assertIn('0.2-alpha', message)

    def test_matching_runtime_and_invalid_owner_data_have_distinct_statuses(self):
        current = {'runtime_api': RUNTIME_API, 'runtime_version': '0.3.0-dev',
                   'capabilities': list(RUNTIME_CAPABILITIES)}
        with patch.object(update_ui.settings, 'validate_runtime_data', return_value=current):
            self.assertTrue(update_ui.runtime_update_status(Path('fixture'))[0])
        with patch.object(update_ui.settings, 'validate_runtime_data', side_effect=ValueError('datos inválidos')):
            okay, message = update_ui.runtime_update_status(Path('fixture'))
            self.assertFalse(okay)
            self.assertIn('datos inválidos', message)

    def test_development_layout_without_runtime_receipt_is_not_a_verified_install(self):
        with patch.object(update_ui.settings, 'validate_runtime_data', return_value=None):
            okay, message = update_ui.runtime_update_status(Path('fixture'))
        self.assertFalse(okay)
        self.assertIn('desarrollo', message)
