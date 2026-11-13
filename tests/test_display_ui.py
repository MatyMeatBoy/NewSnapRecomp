from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch

from newsnap.display_ui import DisplayPanel


class DisplayFreshnessTests(TestCase):
    def panel(self):
        panel=DisplayPanel.__new__(DisplayPanel)
        panel.launcher=SimpleNamespace(root=SimpleNamespace(after=Mock()))
        panel.path=Path('observation.json');panel.process_id=42;panel.started_at=0;panel.generation=3
        panel.presentation=SimpleNamespace(configure=Mock())
        panel.monitor=SimpleNamespace(configure=Mock())
        return panel

    def test_stale_report_removes_previous_monitor_details(self):
        panel=self.panel()
        with patch('newsnap.display_ui.read_status',return_value={'available':False}):
            panel.poll()
        panel.monitor.configure.assert_called_once_with(text='')

    def test_closing_game_removes_previous_monitor_details(self):
        panel=self.panel()
        panel.stop()
        panel.monitor.configure.assert_called_once_with(text='')
        self.assertIsNone(panel.path)
