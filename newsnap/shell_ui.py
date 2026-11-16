"""The launcher's main area (LAUNCH-UI-02): a textured paper backdrop with the pages on a raised rounded sheet and
the status line beneath it. The backdrop and the sheet are one image drawn by code (artwork.py) for the current
size; the pages' Notebook is placed over the sheet, inside its rounded border."""
import tkinter as tk
import tkinter.font as tkfont

from . import artwork, fonts
from .theme import CREAM, DESK, DESK_EDGE, LEAF, LINE, MUTED, WHITE

MARGIN = 12          # backdrop visible around the sheet (the sheet's shadow lives here)
INSET = 9            # the pages start this far inside the sheet, clear of its rounded corners
STATUS = 34          # height of the status line under the sheet
RADIUS = 20


def fit_text(text, width, measure):
    """`text` on one line no wider than `width` pixels, cut with an ellipsis when needed."""
    text = ' '.join(str(text).split())
    if measure(text) <= width:
        return text
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if measure(text[:middle].rstrip() + '…') <= width:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + '…'


class Backdrop(tk.Canvas):
    def __init__(self, parent, status):
        super().__init__(parent, bg=DESK, highlightthickness=0, borderwidth=0)
        from PIL import ImageTk
        self.ImageTk, self.status, self.content = ImageTk, status, None
        self._photo, self._job, self._drawn = None, None, None
        self._sheet = artwork.panel((96, 96), RADIUS, WHITE, LINE, shadow=58, blur=6, offset=3, margin=MARGIN, fill2=CREAM)
        self._image = self.create_image(0, 0, anchor='nw')
        self._font = tkfont.Font(root=self, font=fonts.ui(10))
        self._dot = self.create_oval(0, 0, 8, 8, fill=LEAF, outline='')
        self._text = self.create_text(0, 0, anchor='w', fill=MUTED, font=self._font)
        self._window = None
        status.trace_add('write', lambda *args: self._status())
        self.bind('<Configure>', self._resized, add='+')

    def host(self, widget):
        """The pages' Notebook: kept over the sheet."""
        self.content = widget
        self._window = self.create_window(MARGIN + INSET, MARGIN + INSET, window=widget, anchor='nw')
        self._place()

    def _area(self):
        return max(60, self.winfo_width()), max(60, self.winfo_height())

    def _place(self):
        w, h = self._area()
        if self._window is not None:
            self.itemconfigure(self._window, width=max(40, w - 2 * (MARGIN + INSET)),
                               height=max(40, h - STATUS - 2 * (MARGIN + INSET) + 6))
        y = h - STATUS // 2 - 3
        self.coords(self._dot, MARGIN + 12, y - 4, MARGIN + 20, y + 4)
        self.coords(self._text, MARGIN + 30, y)
        self._status()

    def _status(self):
        try:
            width = self._area()[0] - 2 * MARGIN - 44
            self.itemconfigure(self._text, text=fit_text(self.status.get(), width, self._font.measure))
        except tk.TclError:
            pass

    def _resized(self, event):
        self._place()
        if self._drawn is None:
            self._paint()
        elif self._job is None:
            self._job = self.after(45, self._paint)

    def _paint(self):
        self._job = None
        size = self._area()
        if size == self._drawn:
            return
        self._drawn = size
        w, h = size
        picture = artwork.paper(size, DESK, DESK_EDGE)
        sheet = artwork.stretch(self._sheet, (w, h - STATUS + 6), RADIUS + MARGIN + 8)
        picture.paste(sheet, (0, 0), sheet)
        self._photo = self.ImageTk.PhotoImage(picture, master=self)
        self.itemconfigure(self._image, image=self._photo)
