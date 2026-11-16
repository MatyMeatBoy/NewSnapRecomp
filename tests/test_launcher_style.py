"""The launcher's look (LAUNCH-UI-02): typeface loading and fallback, progress bars, the title bar and artwork."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from newsnap import artwork, fonts, hdshadows_ui, progress_bar, shell_ui, window_chrome
from tools.check_content import violations

ROOT = Path(__file__).resolve().parents[1]
FONT = 'assets/fonts/Nunito[wght].ttf'


class FontTests(unittest.TestCase):
    def setUp(self):
        self.saved = dict(fonts._state)

    def tearDown(self):
        fonts._state.clear()
        fonts._state.update(self.saved)

    def test_shipped_font_is_found_and_registered_privately(self):
        files = fonts.font_files(ROOT)
        self.assertEqual([p.name for p in files], ['Nunito[wght].ttf'])
        calls = []
        self.assertTrue(fonts.load(ROOT, add=lambda path: calls.append(path) or 8, platform='nt'))
        self.assertEqual(calls, files)
        self.assertEqual(fonts.ui(11), ('Nunito', 11))
        self.assertEqual(fonts.ui(11, 'bold'), ('Nunito', 11, 'bold'))
        self.assertEqual(fonts.display(21), ('Nunito ExtraBold', 21))

    def test_refused_missing_or_failing_registration_falls_back_to_segoe(self):
        def broken(path):
            raise OSError('gdi32 unavailable')
        with tempfile.TemporaryDirectory() as empty:
            cases = ((ROOT, lambda path: 0, 'nt'), (ROOT, broken, 'nt'), (Path(empty), lambda path: 8, 'nt'),
                     (ROOT, lambda path: 8, 'posix'))
            for root, add, platform in cases:
                with self.subTest(root=root.name, platform=platform):
                    self.assertFalse(fonts.load(root, add=add, platform=platform))
                    self.assertEqual(fonts.family(), 'Segoe UI')
                    self.assertEqual(fonts.ui(10, 'bold'), ('Segoe UI', 10, 'bold'))
                    self.assertEqual(fonts.display(21), ('Segoe UI', 21, 'bold'))

    def test_a_font_tk_does_not_list_is_not_used(self):
        fonts.load(ROOT, add=lambda path: 8, platform='nt')
        self.assertFalse(fonts.confirm(['Segoe UI', 'Arial']))
        self.assertEqual(fonts.family(), 'Segoe UI')
        fonts.load(ROOT, add=lambda path: 8, platform='nt')
        self.assertTrue(fonts.confirm(['Arial', 'Nunito', 'Nunito ExtraBold']))

    def test_only_the_reviewed_font_bytes_may_enter_the_index(self):
        data = (ROOT / FONT).read_bytes()
        self.assertEqual(violations(FONT, data), [])
        changed = bytearray(data)
        changed[-1] ^= 1
        for candidate in (bytes(changed), data[:-1], data + b'\0', b'ordinary text'):
            self.assertTrue(violations(FONT, candidate))
        for path in ('assets/fonts/Other.ttf', 'assets/fonts/Nunito-Bold.ttf', 'assets/icons/Nunito[wght].ttf'):
            self.assertTrue(violations(path, data))
        for mode in ('100755', '120000'):
            self.assertTrue(violations(FONT, data, mode))
        licence = (ROOT / 'licenses/Nunito-OFL.txt').read_text(encoding='utf-8')
        self.assertIn('SIL Open Font License, Version 1.1', licence)
        self.assertIn('Nunito', (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8'))

    def test_the_frozen_launcher_ships_the_font(self):
        from tools.build_launcher import source_fingerprints
        self.assertIn(FONT, source_fingerprints(ROOT))
        self.assertIn("'assets/fonts'", (ROOT / 'tools/build_launcher.py').read_text(encoding='utf-8'))


class ProgressGeometryTests(unittest.TestCase):
    def test_fraction_is_clamped_and_never_invented(self):
        self.assertEqual(progress_bar.fraction(30, 100), 0.3)
        self.assertEqual(progress_bar.fraction(150, 100), 1.0)
        self.assertEqual(progress_bar.fraction(-5, 100), 0.0)
        for value, maximum in ((5, 0), (5, -1), ('x', 10), (None, 10), (float('nan'), 10)):
            self.assertEqual(progress_bar.fraction(value, maximum), 0.0)

    def test_indeterminate_segment_only_moves_left_to_right(self):
        previous = -1
        for step in range(0, 100):
            left, right = progress_bar.segment(step / 100, 400)
            self.assertTrue(0 <= left <= right <= 400)
            self.assertGreaterEqual(right, min(previous, 400) if step else 0)
            self.assertGreaterEqual(left, 0)
            previous = right
        self.assertEqual(progress_bar.segment(0.0, 400), (0, 0))          # enters from the left edge
        self.assertEqual(progress_bar.segment(0.999999, 400)[1], 400)      # leaves through the right edge
        lefts = [progress_bar.segment(step / 50, 400)[0] for step in range(50)]
        self.assertEqual(lefts, sorted(lefts))

    def test_shadow_build_messages_carry_the_real_count(self):
        parse = hdshadows_ui.parse_fraction
        self.assertEqual(parse('Sombras HD: 1234 de 9156 texturas · nivel LC_001_A'), (1234, 9156))
        self.assertEqual(parse('Sombras HD: 400 de 9156 texturas · leyendo el nivel LC_002_A…'), (400, 9156))
        self.assertEqual(parse('Sombras HD: 12/40 texturas'), (12, 40))
        self.assertEqual(parse('Sombras HD: 50 de 40 texturas'), (40, 40))
        for text in ('Sombras HD: leyendo los niveles del juego…', 'Sombras HD: 120 texturas generadas.',
                     'Descargando la herramienta de escalado (unos 45 MB, una sola vez)…', 'Sombras HD: 3 de 0 texturas', ''):
            self.assertIsNone(parse(text))

    def test_shadow_progress_never_goes_back_within_a_count(self):
        progress = hdshadows_ui.Progress()
        self.assertEqual(progress.update(100, 1000), 0.1)
        self.assertEqual(progress.update(400, 1000), 0.4)
        self.assertEqual(progress.update(350, 1000), 0.4)      # a late message cannot move the bar back
        self.assertEqual(progress.update(1000, 1000), 1.0)
        self.assertEqual(progress.update(5, 50), 0.1)          # another phase counts its own total


class WidgetTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)

    def tearDown(self):
        self.root.destroy()
        self.assertFalse(self.errors)

    def test_bar_fills_from_the_left_and_resets(self):
        bar = progress_bar.SnapBar(self.root, width=200, height=14)
        bar.pack()
        self.root.update_idletasks()
        self.assertEqual(str(bar['mode']), 'determinate')
        self.assertEqual(bar.filled_pixels(), (0, 0))
        bar.configure(maximum=1000, value=300)
        left, right = bar.filled_pixels()
        self.assertEqual(left, 0)
        self.assertAlmostEqual(right / 200, 0.3, delta=0.02)
        bar.configure(value=800)
        self.assertGreater(bar.filled_pixels()[1], right)
        bar.configure(value=100)      # a new stage: shown at once, no animation backwards
        self.assertIsNone(bar._timer)
        bar.stop()
        bar.configure(mode='determinate', value=0)
        self.assertEqual(bar.filled_pixels(), (0, 0))

    def test_indeterminate_runs_only_between_start_and_stop_and_leaves_no_timer(self):
        bar = progress_bar.SnapBar(self.root, width=200, height=14)
        bar.pack()
        bar.configure(mode='indeterminate')
        self.assertEqual(str(bar['mode']), 'indeterminate')
        self.assertEqual(bar.filled_pixels(), (0, 0))
        bar.start()
        self.assertIsNotNone(bar._timer)
        bar._step()
        bar._step()
        self.assertGreater(bar._phase, 0)
        bar.stop()
        self.assertIsNone(bar._timer)
        self.root.update()
        self.assertFalse(self.root.tk.call('after', 'info'))
        bar.start()
        bar.destroy()
        self.root.update()
        self.assertFalse(self.root.tk.call('after', 'info'))
        with self.assertRaises(tk.TclError):
            progress_bar.SnapBar(self.root).configure(mode='sideways')

    def test_shadow_button_bar_follows_the_build_and_resets(self):
        launcher = SimpleNamespace(root=self.root, project=ROOT / 'build/no-such-project', busy=False,
                                   status=tk.StringVar(master=self.root))
        button = hdshadows_ui.HdShadowsButton(launcher, self.root)
        self.assertEqual(button.bar.filled_pixels(), (0, 0))
        button.running = True
        button.show_activity()
        self.assertEqual(str(button.bar['mode']), 'indeterminate')
        button.show_message('Sombras HD: 2289 de 9156 texturas · nivel LC_001_A')
        self.assertEqual(str(button.bar['mode']), 'determinate')
        self.assertEqual(button.percent.get(), '25 %')
        self.assertEqual(launcher.status.get(), 'Sombras HD: 2289 de 9156 texturas · nivel LC_001_A')
        button.show_message('Sombras HD: 100 de 9156 texturas · nivel LC_001_A')
        self.assertEqual(button.percent.get(), '25 %')
        button._done()
        self.assertFalse(button.running)
        self.assertEqual(button.percent.get(), '')
        self.assertEqual(float(button.bar['value']), 0.0)
        self.root.update()
        self.assertFalse(self.root.tk.call('after', 'info'))

    def test_title_bar_buttons_drag_and_double_click(self):
        frame = Mock()
        closed = []
        bar = window_chrome.TitleBar(self.root, self.root, title='NewSnap', detail='prueba', on_close=lambda: closed.append(1),
                                     frame=frame)
        bar.pack(fill='x')
        self.root.update_idletasks()
        width = bar.winfo_width()
        event = lambda x: SimpleNamespace(x=x, y=window_chrome.HEIGHT // 2)
        bar._press(event(60))                               # the body: Windows moves the window
        frame.begin_move.assert_called_once_with()
        close_x = width - window_chrome.BUTTON_WIDTH // 2
        bar._press(event(close_x))
        self.assertEqual(bar.pressed, 2)
        bar._release(event(60))                             # released elsewhere: nothing happens
        self.assertEqual(closed, [])
        bar._press(event(close_x))
        bar._release(event(close_x))
        self.assertEqual(closed, [1])
        states = []
        self.root.state = lambda value=None: states.append(value) if value else ('zoomed' if states[-1:] == ['zoomed'] else 'normal')
        bar._double(event(60))
        bar.toggle_maximize()
        self.assertEqual(states, ['zoomed', 'normal'])
        self.root.iconify = Mock()
        bar._press(event(width - 3 * window_chrome.BUTTON_WIDTH + 5))
        bar._release(event(width - 3 * window_chrome.BUTTON_WIDTH + 5))
        self.root.iconify.assert_called_once_with()
        frame.begin_move.assert_called_once_with()          # the buttons never start a move

    def test_other_systems_and_failures_keep_a_native_window(self):
        holder = tk.Frame(self.root)
        chrome = window_chrome.Chrome(self.root, holder, title='NewSnap', platform='posix')
        self.assertEqual((chrome.mode, chrome.bar), ('plain', None))
        chrome = window_chrome.Chrome(self.root, holder, title='NewSnap', platform='nt')
        if chrome.bar is not None:
            chrome.frame = Mock()
            chrome.frame.strip.side_effect = OSError('no frame')
            chrome.frame.tint.return_value = True
            self.assertEqual(chrome.ensure(), 'native')      # no own bar: the system one, tinted
            self.assertFalse(chrome.bar.winfo_manager())
            chrome.frame.tint.side_effect = OSError('no dwm')
            chrome.mode = 'pending'
            self.assertEqual(chrome.ensure(), 'plain')

    def test_status_line_is_cut_to_the_width(self):
        measure = len
        self.assertEqual(shell_ui.fit_text('corto', 10, measure), 'corto')
        self.assertEqual(shell_ui.fit_text('una línea\nde estado larga', 12, measure), 'una línea d…')
        self.assertLessEqual(len(shell_ui.fit_text('x' * 500, 40, measure)), 40)


class ChromeLogicTests(unittest.TestCase):
    def test_frameless_style_keeps_resize_minimise_maximise(self):
        overlapped = 0x14CF0000        # visible overlapped window with caption, system menu, thick frame, boxes
        style = window_chrome.frameless_style(overlapped)
        self.assertEqual(style & window_chrome.WS_CAPTION, 0)
        for bit in (window_chrome.WS_THICKFRAME, window_chrome.WS_MINIMIZEBOX, window_chrome.WS_MAXIMIZEBOX,
                    window_chrome.WS_SYSMENU, 0x10000000):
            self.assertTrue(style & bit)
        self.assertEqual(window_chrome.frameless_style(style), style)

    def test_maximised_window_fills_the_work_area_not_the_taskbar(self):
        bounds = window_chrome.maximized_bounds((0, 0, 1536, 864), (0, 0, 1536, 816), (7, 7, 7, 7))
        self.assertEqual(bounds, (-7, -7, 1550, 830))
        second = window_chrome.maximized_bounds((1920, 0, 3840, 1080), (1920, 40, 3840, 1080), (8, 8, 8, 8))
        self.assertEqual(second, (-8, 32, 1936, 1056))

    def test_colour_and_button_hit_testing(self):
        self.assertEqual(window_chrome.colorref('#163d32'), 0x00323D16)
        width = 1000
        self.assertIsNone(window_chrome.button_at(400, width))
        self.assertEqual(window_chrome.button_at(width - 1, width), 2)
        self.assertEqual(window_chrome.button_at(width - window_chrome.BUTTON_WIDTH - 1, width), 1)
        self.assertEqual(window_chrome.button_at(width - 3 * window_chrome.BUTTON_WIDTH, width), 0)
        self.assertIsNone(window_chrome.button_at(width - 3 * window_chrome.BUTTON_WIDTH - 1, width))

    def test_artwork_is_generated_with_the_asked_sizes(self):
        for name in artwork.ICONS:
            image = artwork.icon(name, 22, '#163d32')
            self.assertEqual((image.size, image.mode), ((22, 22), 'RGBA'))
            self.assertGreater(image.getchannel('A').getextrema()[1], 200, name)
        self.assertEqual(artwork.paper((120, 90), '#e9e3cf', '#c9bf9f').size, (120, 90))
        self.assertEqual(artwork.sidebar_background((232, 400), '#1f5142', '#113229', '#57a57c').size, (232, 400))
        tile = artwork.panel((96, 96), 20, '#fffdf6', '#d3d4c4')
        self.assertEqual(artwork.stretch(tile, (300, 200), 40).size, (300, 200))
        self.assertEqual(artwork.mix('#000000', '#ffffff', 0.5), '#808080')


if __name__ == '__main__':
    unittest.main()
