import tkinter as tk
from unittest import TestCase

from newsnap.progress import ProgressUpdate
from newsnap.progress_ui import PreparationPanel


class PreparationPanelTests(TestCase):
    def setUp(self):
        try:self.root=tk.Tk()
        except tk.TclError as error:self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.callback_errors=[]
        self.root.report_callback_exception=lambda *args:self.callback_errors.append(args)
        self.panel=PreparationPanel(self.root)

    def tearDown(self):
        self.root.destroy()
        self.assertFalse(self.callback_errors)

    def test_real_units_and_unknown_phase_never_reuse_old_percent(self):
        self.panel.begin('Preparando')
        self.panel.report(ProgressUpdate('compile','Compilando',3,10))
        self.assertIn('30 %',self.panel.detail.get())
        self.assertIn('3 / 10',self.panel.detail.get())
        self.assertEqual(str(self.panel.bar['mode']),'determinate')
        self.panel.report(ProgressUpdate('link','Enlazando'))
        self.assertNotIn('%',self.panel.detail.get())
        self.assertEqual(str(self.panel.bar['mode']),'indeterminate')

    def test_failure_stops_clock_and_never_reports_completion(self):
        self.panel.begin('Preparando')
        self.panel.report(ProgressUpdate('compile','Compilando',3,10))
        self.panel.finish('No se pudo iniciar',error=True)
        self.assertFalse(self.panel.active)
        self.assertIsNone(self.panel._tick_id)
        self.assertNotIn('100',self.panel.detail.get())
        self.assertEqual(self.panel.label.get(),'No se pudo iniciar')

    def test_new_operation_resets_previous_note_and_counts(self):
        self.panel.begin('Primera operación')
        self.panel.set_note('Compilación durante el juego')
        self.panel.finish('Listo')
        self.panel.begin('Otra operación')
        self.assertEqual(self.panel.note.get(),'')
        self.assertNotIn('100',self.panel.detail.get())
        self.assertTrue(self.panel.active)

    def test_destroy_cancels_both_clock_and_ttk_autostep(self):
        self.panel.begin('Verificando')
        self.panel.destroy()
        self.root.update()
        self.assertFalse(self.root.tk.call('after','info'))
