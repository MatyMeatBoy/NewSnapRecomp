from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch

from newsnap.display_ui import DisplayPanel


class DisplayFreshnessTests(TestCase):
    def panel(self):
        panel=DisplayPanel.__new__(DisplayPanel)
        panel.launcher=SimpleNamespace(root=SimpleNamespace(after=Mock()),presentation=SimpleNamespace(get=lambda:'Mailbox'))
        panel.path=Path('observation.json');panel.process_id=42;panel.started_at=0;panel.generation=3
        panel.presentation=SimpleNamespace(configure=Mock())
        panel.requested=SimpleNamespace(configure=Mock())
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

    def test_effective_fifo_does_not_claim_requested_mailbox_or_vrr_is_active(self):
        panel=self.panel()
        value={'available':True,'generation':3,'presentation':'unknown',
               'monitor_name':'Test monitor','monitor_id':'test','actual_present_mode':'fifo'}
        with patch('newsnap.display_ui.read_status',return_value=value):
            panel.poll()
        panel.requested.configure.assert_called_with(text='Modo Vulkan solicitado: Mailbox')
        self.assertIn('efectivo: fifo',panel.monitor.configure.call_args.kwargs['text'])
        self.assertIn('Difiere',panel.monitor.configure.call_args.kwargs['text'])
        self.assertIn('sin verificar',panel.presentation.configure.call_args.kwargs['text'])
