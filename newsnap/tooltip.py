"""Small Tk tooltips for mouse hover and keyboard focus.

Keep the returned Tooltip when explicit cleanup is useful; owner destruction
also closes it. ``attach`` replaces a previous tooltip attached by this module.
All calls, like other Tk operations, belong on the Tk thread.
"""
from .launcher_language import tr
import tkinter as tk


class Tooltip:
    def __init__(self, widget, text, *, delay=450, wraplength=360):
        self.widget = widget
        self.text = str(text)
        self.delay = max(0, int(delay))
        self.wraplength = max(1, int(wraplength))
        self._timer = None
        self._popup = None
        self._closed = False
        self._bindings = []
        for sequence, handler in (
            ('<Enter>', self._enter), ('<Leave>', self.hide),
            ('<FocusIn>', self._focus), ('<FocusOut>', self.hide),
            ('<ButtonPress>', self.hide), ('<Unmap>', self.hide),
            ('<Destroy>', self._destroy),
        ):
            self._bindings.append((sequence, widget.bind(sequence, handler, add='+')))

    def _enter(self, event=None):
        self._schedule(keyboard=False)

    def _focus(self, event=None):
        self._schedule(keyboard=True)

    def _schedule(self, *, keyboard):
        self.hide()
        if not self._closed and self.text:
            self._timer = self.widget.after(self.delay, lambda: self._show(keyboard))

    def _show(self, keyboard):
        self._timer = None
        if self._closed:
            return
        try:
            if not self.widget.winfo_exists():
                return
            popup = self._popup = tk.Toplevel(self.widget, takefocus=False)
            popup.withdraw()
            popup.overrideredirect(True)
            popup.attributes('-topmost', True)
            screen_w = self.widget.winfo_screenwidth()
            screen_h = self.widget.winfo_screenheight()
            margin = 8
            limit_w = max(1, screen_w - 2 * margin)
            limit_h = max(1, screen_h - 2 * margin)
            from . import fonts
            label = tk.Label(popup, text=self.text, justify='left', anchor='nw', font=fonts.ui(10),
                             background='#fffdf6', foreground='#203c34',
                             highlightthickness=1, highlightbackground='#b9bfae',
                             relief='flat', borderwidth=0, padx=10, pady=7,
                             wraplength=min(self.wraplength, max(1, limit_w - 16)),
                             takefocus=False)
            label.pack(fill='both', expand=True)
            popup.update_idletasks()
            width = min(popup.winfo_reqwidth(), limit_w)
            height = min(popup.winfo_reqheight(), limit_h)
            if keyboard:
                x = self.widget.winfo_rootx()
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
            else:
                x, y = self.widget.winfo_pointerxy()
                x += 16
                y += 20
            x = max(margin, min(x, screen_w - width - margin))
            y = max(margin, min(y, screen_h - height - margin))
            popup.geometry(f'{width}x{height}+{x}+{y}')
            popup.deiconify()
        except tk.TclError:
            # A callback or application teardown may destroy the owner.
            self.hide()

    def hide(self, event=None):
        """Cancel a delayed show and dismiss the popup without changing focus."""
        if self._timer is not None:
            timer, self._timer = self._timer, None
            try:
                self.widget.after_cancel(timer)
            except tk.TclError:
                pass
        if self._popup is not None:
            popup, self._popup = self._popup, None
            try:
                popup.destroy()
            except tk.TclError:
                pass

    def _destroy(self, event):
        if event.widget is self.widget:
            self.close()

    def close(self):
        """Release this tooltip's bindings and timer; safe to call repeatedly."""
        if self._closed:
            return
        self._closed = True
        self.hide()
        for sequence, binding in self._bindings:
            try:
                self.widget.unbind(sequence, binding)
            except tk.TclError:
                pass
        self._bindings.clear()


def attach(widget, text, **kwargs):
    """Attach one tooltip to a widget, replacing any prior ``attach`` result."""
    previous = getattr(widget, '_newsnap_tooltip', None)
    if previous is not None:
        previous.close()
    tooltip = Tooltip(widget, text, **kwargs)
    widget._newsnap_tooltip = tooltip
    return tooltip
