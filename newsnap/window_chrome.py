"""The launcher's own title bar (LAUNCH-UI-02): the window keeps being a normal Windows window, without its caption.

On Windows the native caption is removed from the window's style (WS_CAPTION off; WS_THICKFRAME, WS_MINIMIZEBOX,
WS_MAXIMIZEBOX and WS_SYSMENU stay), so the taskbar entry, Alt+Tab, minimise/restore, resizing by the edges, Win+arrow
and drag-to-edge snapping, the rounded corners and the shadow are still the system's. `TitleBar` draws the bar in the
launcher's style with its own minimise / maximise / close buttons; dragging it hands the move to Windows
(ReleaseCapture + WM_NCLBUTTONDOWN/HTCAPTION), so snapping while dragging works as with a native bar. The thin strip
Windows keeps above the client area (the top resize border) is painted in the bar's colour through DWM, so it reads
as part of the bar. A window without a caption would maximise over the taskbar: WM_GETMINMAXINFO is answered with
the monitor's work area instead.

Fallbacks, in order: if the frame cannot be changed the bar is not shown and the native title bar is tinted in the
launcher's colours (DwmSetWindowAttribute, Windows 11); if that fails too, or on another system, the window is a
plain native one. Nothing here raises to the launcher.
"""
import os
import tkinter as tk

from . import artwork, fonts
from .theme import AMBER, BAR, BAR_TEXT, CREAM, INK

HEIGHT = 40
BUTTON_WIDTH = 46
GWL_STYLE, GWL_EXSTYLE, GWLP_WNDPROC = -16, -20, -4
WS_CAPTION, WS_THICKFRAME, WS_SYSMENU = 0x00C00000, 0x00040000, 0x00080000
WS_MINIMIZEBOX, WS_MAXIMIZEBOX = 0x00020000, 0x00010000
WM_GETMINMAXINFO, WM_NCLBUTTONDOWN, HTCAPTION = 0x0024, 0x00A1, 2
SWP_FRAME = 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010      # FRAMECHANGED, NOMOVE, NOSIZE, NOZORDER, NOACTIVATE
DWMWA_BORDER_COLOR, DWMWA_CAPTION_COLOR, DWMWA_TEXT_COLOR = 34, 35, 36
_KEEP = []     # window procedures stay referenced for the life of the process


def colorref(colour):
    """'#rrggbb' as a Windows COLORREF (0x00bbggrr)."""
    r, g, b = artwork.rgb(colour)
    return r | g << 8 | b << 16


def frameless_style(style):
    """The window style without a caption but still sizeable, minimisable and maximisable."""
    return (style & ~WS_CAPTION) | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU


def maximized_bounds(monitor, work, frame):
    """Position (relative to the monitor) and size of the maximised window so its client area fills the work area.

    `monitor` and `work` are (left, top, right, bottom); `frame` is the thickness of the invisible sizing border on
    each side (left, top, right, bottom), which Windows expects to hang outside the screen."""
    return (work[0] - monitor[0] - frame[0], work[1] - monitor[1] - frame[1],
            work[2] - work[0] + frame[0] + frame[2], work[3] - work[1] + frame[1] + frame[3])


def button_at(x, width, count=3, button_width=BUTTON_WIDTH):
    """Index (0 = leftmost) of the title bar button under x, or None over the draggable part."""
    first = width - count * button_width
    if x < first or x >= width:
        return None
    return int((x - first) // button_width)


class NativeFrame:
    """The Win32 side. Every method may raise; `Chrome` turns a failure into the fallback."""

    def __init__(self, root):
        import ctypes
        from ctypes import wintypes
        self.root, self.hwnd, self._old, self._proc = root, None, None, None
        self.min_size = None      # the smallest client area (Tk's minsize), enforced with the real frame
        self.ct, self.wt = ctypes, wintypes
        u = self.user32 = ctypes.WinDLL('user32')
        self.dwm = ctypes.WinDLL('dwmapi')
        pointer_sized = ctypes.sizeof(ctypes.c_void_p) == 8
        self._get_ptr = u.GetWindowLongPtrW if pointer_sized else u.GetWindowLongW
        self._set_ptr = u.SetWindowLongPtrW if pointer_sized else u.SetWindowLongW
        self.LRESULT = ctypes.c_ssize_t
        for function, restype, argtypes in (
                (u.GetAncestor, wintypes.HWND, [wintypes.HWND, ctypes.c_uint]),
                (self._get_ptr, ctypes.c_void_p, [wintypes.HWND, ctypes.c_int]),
                (self._set_ptr, ctypes.c_void_p, [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]),
                (u.GetWindowLongW, ctypes.c_long, [wintypes.HWND, ctypes.c_int]),
                (u.SetWindowLongW, ctypes.c_long, [wintypes.HWND, ctypes.c_int, ctypes.c_long]),
                (u.SetWindowPos, wintypes.BOOL, [wintypes.HWND, wintypes.HWND] + [ctypes.c_int] * 4 + [ctypes.c_uint]),
                (u.CallWindowProcW, self.LRESULT, [ctypes.c_void_p, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]),
                (u.PostMessageW, wintypes.BOOL, [wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]),
                (u.ReleaseCapture, wintypes.BOOL, []),
                (u.IsWindow, wintypes.BOOL, [wintypes.HWND]),
                (u.MonitorFromWindow, wintypes.HANDLE, [wintypes.HWND, wintypes.DWORD]),
                (u.GetMonitorInfoW, wintypes.BOOL, [wintypes.HANDLE, ctypes.c_void_p]),
                (u.AdjustWindowRectEx, wintypes.BOOL, [ctypes.c_void_p, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]),
                (self.dwm.DwmSetWindowAttribute, ctypes.c_long, [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD])):
            function.restype, function.argtypes = restype, argtypes

    def wrapper(self, window=None):
        """The top-level Win32 window Tk wraps this toplevel in (it exists once the window was mapped)."""
        window = window or self.root
        return self.user32.GetAncestor(window.winfo_id(), 2)

    def style(self, hwnd):
        return self.user32.GetWindowLongW(hwnd, GWL_STYLE) & 0xFFFFFFFF

    def tint(self, window, caption, text, border=None):
        """Colours of the native caption / top strip, its text and the window border. True when DWM accepted them."""
        hwnd = self.wrapper(window)
        done = True
        for attribute, colour in ((DWMWA_CAPTION_COLOR, caption), (DWMWA_TEXT_COLOR, text), (DWMWA_BORDER_COLOR, border or caption)):
            value = self.wt.DWORD(colorref(colour))
            done = self.dwm.DwmSetWindowAttribute(hwnd, attribute, self.ct.byref(value), 4) == 0 and done
        return done

    def strip(self):
        """Removes the caption from the launcher's window (again, if Tk made a new wrapper) and hooks maximising."""
        hwnd = self.wrapper()
        if not hwnd or hwnd == self.root.winfo_id():
            raise OSError('the window has no frame yet')
        style = self.style(hwnd)
        wanted = frameless_style(style)
        if wanted != style:
            signed = wanted - (1 << 32) if wanted & 0x80000000 else wanted
            self.user32.SetWindowLongW(hwnd, GWL_STYLE, signed)
            if self.style(hwnd) != wanted or not self.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_FRAME):
                raise OSError('the window style could not be changed')
        if hwnd != self.hwnd:
            self.hwnd = hwnd
            self._hook(hwnd)
        return hwnd

    def _hook(self, hwnd):
        ct, wt, user32 = self.ct, self.wt, self.user32
        old = self._get_ptr(hwnd, GWLP_WNDPROC)
        if not old:
            return

        class MINMAXINFO(ct.Structure):
            _fields_ = [(name, wt.POINT) for name in ('reserved', 'max_size', 'max_position', 'min_track', 'max_track')]

        class MONITORINFO(ct.Structure):
            _fields_ = [('size', wt.DWORD), ('monitor', wt.RECT), ('work', wt.RECT), ('flags', wt.DWORD)]

        def procedure(window, message, wparam, lparam):
            result = user32.CallWindowProcW(old, window, message, wparam, lparam)
            if message == WM_GETMINMAXINFO and lparam:
                try:
                    info = MINMAXINFO.from_address(lparam)
                    monitor = MONITORINFO(size=ct.sizeof(MONITORINFO))
                    if user32.GetMonitorInfoW(user32.MonitorFromWindow(window, 2), ct.byref(monitor)):
                        rect = wt.RECT(0, 0, 0, 0)
                        user32.AdjustWindowRectEx(ct.byref(rect), user32.GetWindowLongW(window, GWL_STYLE) & 0xFFFFFFFF, False,
                                                  user32.GetWindowLongW(window, GWL_EXSTYLE) & 0xFFFFFFFF)
                        m, w = monitor.monitor, monitor.work
                        x, y, width, height = maximized_bounds((m.left, m.top, m.right, m.bottom), (w.left, w.top, w.right, w.bottom),
                                                               (-rect.left, -rect.top, rect.right, rect.bottom))
                        info.max_position.x, info.max_position.y = x, y
                        info.max_size.x, info.max_size.y = width, height
                        info.max_track.x, info.max_track.y = max(info.max_track.x, width), max(info.max_track.y, height)
                        if self.min_size:   # Tk adds the caption it believes the window still has
                            info.min_track.x = self.min_size[0] + rect.right - rect.left
                            info.min_track.y = self.min_size[1] + rect.bottom - rect.top
                except Exception:
                    pass
            return result

        proc = ct.WINFUNCTYPE(self.LRESULT, wt.HWND, ct.c_uint, wt.WPARAM, wt.LPARAM)(procedure)
        _KEEP.append(proc)
        self._old, self._proc = old, proc
        self._set_ptr(hwnd, GWLP_WNDPROC, ct.cast(proc, ct.c_void_p))

    def unhook(self):
        """Gives the window its original procedure back before it is destroyed."""
        if self.hwnd and self._old and self.user32.IsWindow(self.hwnd):
            current = self._get_ptr(self.hwnd, GWLP_WNDPROC)
            if current == self.ct.cast(self._proc, self.ct.c_void_p).value:
                self._set_ptr(self.hwnd, GWLP_WNDPROC, self._old)
        self._old = None

    def begin_move(self):
        """Windows moves the window from here on, exactly as from a native title bar (snap included)."""
        hwnd = self.hwnd or self.wrapper()
        self.user32.ReleaseCapture()
        self.user32.PostMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)


class TitleBar(tk.Canvas):
    """The bar itself: icon, title, a draggable body and three buttons with hover and pressed states."""
    BUTTONS = ('minimize', 'maximize', 'close')

    def __init__(self, parent, root, *, title, detail='', on_close=None, frame=None):
        super().__init__(parent, height=HEIGHT, bg=BAR, highlightthickness=0, borderwidth=0)
        from PIL import ImageTk
        from .theme import pill
        self.root, self.frame, self.on_close = root, frame, on_close or root.destroy
        self.hover = self.pressed = None
        mk = lambda picture: ImageTk.PhotoImage(picture, master=self)
        self._icons = {(name, state): mk(artwork.icon(name, 18, colour))
                       for name in (*self.BUTTONS, 'restore')
                       for state, colour in (('rest', BAR_TEXT), ('hover', '#ffffff'))}
        self._pads = {'hover': mk(pill((BUTTON_WIDTH - 8, HEIGHT - 12), artwork.mix(BAR, '#ffffff', 0.14))),
                      'pressed': mk(pill((BUTTON_WIDTH - 8, HEIGHT - 12), artwork.mix(BAR, '#ffffff', 0.07))),
                      'close_hover': mk(pill((BUTTON_WIDTH - 8, HEIGHT - 12), '#d9534a')),
                      'close_pressed': mk(pill((BUTTON_WIDTH - 8, HEIGHT - 12), '#b8433b'))}
        self._brand = mk(artwork.icon('camera', 20, AMBER))
        self.create_image(14, HEIGHT // 2, image=self._brand, anchor='w')
        name = self.create_text(42, HEIGHT // 2, text=title, anchor='w', fill=CREAM, font=fonts.ui(11, 'bold'))
        self.create_text(self.bbox(name)[2] + 10, HEIGHT // 2 + 1, text=detail, anchor='w',
                         fill=artwork.mix(BAR, BAR_TEXT, 0.62), font=fonts.ui(10))
        self._items = []
        for name in self.BUTTONS:
            pad = self.create_image(0, HEIGHT // 2, image='', anchor='center')
            glyph = self.create_image(0, HEIGHT // 2, image=self._icons[(name, 'rest')], anchor='center')
            self._items.append((pad, glyph))
        self.bind('<Configure>', lambda event: self._layout(event.width), add='+')
        self.bind('<Motion>', self._motion)
        self.bind('<Leave>', lambda event: self._set(None, self.pressed))
        self.bind('<ButtonPress-1>', self._press)
        self.bind('<B1-Motion>', self._motion)
        self.bind('<ButtonRelease-1>', self._release)
        self.bind('<Double-Button-1>', self._double)
        self._state_binding = root.bind('<Configure>', self._window_changed, add='+')
        self._zoomed = False
        self._layout(self.winfo_reqwidth())

    # --- what the buttons do (also called directly by the tests) ---
    def minimize(self):
        self.root.iconify()

    def toggle_maximize(self):
        self.root.state('normal' if self.root.state() == 'zoomed' else 'zoomed')
        self._window_changed()

    def close(self):
        self.on_close()

    def start_move(self):
        if self.frame is not None:
            self.frame.begin_move()

    # --- pointer ---
    def _index(self, event):
        if not 0 <= event.y < HEIGHT:
            return None
        return button_at(event.x, self.winfo_width(), len(self.BUTTONS))

    def _motion(self, event):
        self._set(self._index(event), self.pressed)

    def _press(self, event):
        index = self._index(event)
        if index is None:
            self.start_move()
        else:
            self._set(index, index)

    def _release(self, event):
        pressed, index = self.pressed, self._index(event)
        self._set(index, None)
        if pressed is not None and pressed == index:
            self._set(None, None)
            (self.minimize, self.toggle_maximize, self.close)[index]()

    def _double(self, event):
        if self._index(event) is None:
            self.toggle_maximize()
        else:
            self._press(event)

    def _set(self, hover, pressed):
        self.hover, self.pressed = hover, pressed
        self._paint()

    def _paint(self):
        for index, (pad, glyph) in enumerate(self._items):
            name = self.BUTTONS[index]
            if name == 'maximize' and self._zoomed:
                name = 'restore'
            close = self.BUTTONS[index] == 'close'
            if self.pressed == index and self.hover == index:
                image = self._pads['close_pressed' if close else 'pressed']
            elif self.hover == index and self.pressed in (None, index):
                image = self._pads['close_hover' if close else 'hover']
            else:
                image = ''
            self.itemconfigure(pad, image=image)
            self.itemconfigure(glyph, image=self._icons[(name, 'hover' if image else 'rest')])

    def _layout(self, width):
        first = width - len(self.BUTTONS) * BUTTON_WIDTH
        for index, (pad, glyph) in enumerate(self._items):
            x = first + index * BUTTON_WIDTH + BUTTON_WIDTH // 2 - 2
            self.coords(pad, x, HEIGHT // 2)
            self.coords(glyph, x, HEIGHT // 2)

    def _window_changed(self, event=None):
        if event is not None and event.widget is not self.root:
            return
        try:
            zoomed = self.root.state() == 'zoomed'
        except tk.TclError:
            return
        if zoomed != self._zoomed:
            self._zoomed = zoomed
            self._paint()


class Chrome:
    """Chooses and keeps the window's top: 'custom' (own bar), 'native' (tinted system bar) or 'plain'."""

    def __init__(self, root, container, *, title, detail='', on_close=None, platform=None):
        self.root, self.bar, self.frame, self.mode = root, None, None, 'plain'
        self._shown = True
        if (platform or os.name) != 'nt':
            return
        try:
            self.frame = NativeFrame(root)
            self.bar = TitleBar(container, root, title=title, detail=detail, on_close=on_close, frame=self.frame)
            self.bar.pack(side='top', fill='x')
            self.mode = 'pending'
        except Exception:
            self.frame = self.bar = None
            return
        root.bind('<Map>', self._mapped, add='+')
        root.bind('<Destroy>', self._destroyed, add='+')
        root.bind_class('Toplevel', '<Map>', self._dialog_mapped, add='+')
        try:   # the window appears once its frame is ready, without a flash of the system bar
            if root.state() == 'normal' and not root.winfo_ismapped():
                root.attributes('-alpha', 0.0)
                self._shown = False
                root.after(2500, self._reveal)
        except tk.TclError:
            pass

    def _mapped(self, event):
        if event.widget is self.root:
            self.ensure()
            self.root.after(40, self._reveal)

    def _reveal(self):
        if not self._shown:
            self._shown = True
            try:
                self.root.attributes('-alpha', 1.0)
                if self.root.winfo_ismapped():
                    self.ensure()
            except tk.TclError:
                pass

    def ensure(self):
        """Puts the custom frame in place (again); on any failure the launcher gets the native bar back."""
        if self.mode not in ('pending', 'custom'):
            return self.mode
        try:
            first = self.mode == 'pending'
            size = (self.root.winfo_width(), self.root.winfo_height())
            minimum = self.root.minsize()
            self.frame.min_size = minimum if min(minimum) > 1 else None
            self.frame.strip()
            self.frame.tint(self.root, BAR, BAR_TEXT)
            self.mode = 'custom'
            if first and self.root.state() == 'normal' and min(size) > 1:
                # without the caption the same outer window has a taller client area: back to the size asked for
                self.root.geometry('%dx%d' % size)
        except Exception:
            self._fall_back()
        return self.mode

    def _fall_back(self):
        self.mode = 'plain'
        try:
            self.bar.pack_forget()
        except tk.TclError:
            pass
        try:
            if self.frame.tint(self.root, BAR, BAR_TEXT):
                self.mode = 'native'
        except Exception:
            pass

    def _dialog_mapped(self, event):
        """Credits, photo view, controller test: their native title bars in the launcher's paper colour."""
        window = event.widget
        try:
            if isinstance(window, tk.Toplevel) and not window.overrideredirect():
                self.frame.tint(window, CREAM, INK, '#cfcab6')
        except Exception:
            pass

    def _destroyed(self, event):
        if event.widget is self.root and self.frame is not None:
            try:
                self.frame.unhook()
            except Exception:
                pass
