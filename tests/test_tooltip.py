"""Real Tk lifecycle checks; no physical pointer movement or external windows."""
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from newsnap.tooltip import Tooltip, attach


class TooltipTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'Tk display unavailable: {exc}')
        self.root.withdraw()
        self.errors = []
        self.root.report_callback_exception = lambda *error: self.errors.append(error)
        # Tk suppresses synthetic window events for unmapped widgets. Keep the
        # root withdrawn and map a tiny, noninteractive test owner off screen.
        self.host = tk.Toplevel(self.root, takefocus=False)
        self.host.overrideredirect(True)
        self.host.geometry('1x1+10000+10000')
        self.widget = tk.Button(self.host, text='Option')
        self.widget.pack()
        self.root.update()
        self.tooltips = []

    def tearDown(self):
        for tooltip in self.tooltips:
            tooltip.close()
        self.root.destroy()
        self.assertEqual(self.errors, [])

    def tooltip(self, **kwargs):
        tooltip = Tooltip(self.widget, 'Useful option description. ' * 8,
                          delay=25, **kwargs)
        self.tooltips.append(tooltip)
        return tooltip

    def pump(self, seconds=.075):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.root.update()
            time.sleep(.003)
        self.root.update()

    def popups(self):
        return [child for child in self.widget.winfo_children()
                if isinstance(child, tk.Toplevel)]

    def test_leave_and_destroy_cancel_pending_show(self):
        self.tooltip()
        self.widget.event_generate('<Enter>')
        self.assertEqual(self.popups(), [])
        self.widget.event_generate('<Leave>')
        self.pump()
        self.assertEqual(self.popups(), [])
        self.widget.event_generate('<Enter>')
        self.widget.destroy()
        self.pump()

    def test_keyboard_focus_show_hide_preserves_existing_binding_and_focus(self):
        calls = []
        self.widget.bind('<FocusIn>', lambda event: calls.append('focus'))
        tooltip = self.tooltip()
        focus = self.root.focus_get()
        self.widget.event_generate('<FocusIn>')
        self.pump()
        self.assertEqual(calls, ['focus'])
        popup, = self.popups()
        self.assertTrue(popup.overrideredirect())
        self.assertTrue(popup.attributes('-topmost'))
        self.assertEqual(str(popup.cget('takefocus')), '0')
        self.assertIs(self.root.focus_get(), focus)
        self.widget.event_generate('<FocusOut>')
        self.assertEqual(self.popups(), [])
        tooltip.close()
        tooltip.close()
        self.widget.event_generate('<FocusIn>')
        self.pump()
        self.assertEqual(calls, ['focus', 'focus'])
        self.assertEqual(self.popups(), [])

    def test_pointer_edge_popup_bounded_and_button_hides(self):
        self.tooltip(wraplength=160)
        with patch.object(self.widget, 'winfo_pointerxy', return_value=(100000, 100000)):
            self.widget.event_generate('<Enter>')
            self.pump()
        popup, = self.popups()
        self.assertGreaterEqual(popup.winfo_rootx(), 0)
        self.assertGreaterEqual(popup.winfo_rooty(), 0)
        self.assertLessEqual(popup.winfo_rootx() + popup.winfo_width(),
                             popup.winfo_screenwidth())
        self.assertLessEqual(popup.winfo_rooty() + popup.winfo_height(),
                             popup.winfo_screenheight())
        label, = popup.winfo_children()
        self.assertEqual(int(label.cget('wraplength')), 160)
        self.widget.event_generate('<ButtonPress-1>')
        self.assertEqual(self.popups(), [])

    def test_attach_replaces_old_tooltip_and_owner_destroy_closes_popup(self):
        first = attach(self.widget, 'Old', delay=25)
        second = attach(self.widget, 'New', delay=25)
        self.tooltips.extend([first, second])
        self.widget.event_generate('<FocusIn>')
        self.pump()
        popup, = self.popups()
        self.assertEqual(popup.winfo_children()[0].cget('text'), 'New')
        self.widget.destroy()
        self.pump()
        self.assertFalse(popup.winfo_exists())


if __name__ == '__main__':
    unittest.main()
