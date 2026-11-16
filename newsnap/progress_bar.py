"""The launcher's progress bar: a rounded trough that fills from left to right.

It replaces ttk.Progressbar in the launcher's pages with the same small interface (`configure(mode=, value=,
maximum=)`, `bar['mode']`, `start()`, `stop()`), drawn on a canvas so both modes look right with the rounded theme:

- determinate: the fill covers the measured fraction, growing from the left edge. A larger value is approached in a
  few short steps; a smaller one (a new stage starting again from zero) is shown at once, never animated backwards.
- indeterminate: a short segment travels from the left edge to the right one and comes in again from the left; it
  runs only between `start()` and `stop()`.

`fraction()` and `segment()` are the pure geometry, used by the tests.
"""
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk

from . import artwork
from .theme import CREAM, GREEN, LEAF, pill

TROUGH, TROUGH_EDGE = '#dedccb', '#cfcdb9'
FRAME_MS = 30          # one animation step
SWEEP_MS = 1500        # one left-to-right pass of the indeterminate segment
SEGMENT = 0.28         # its length, as a part of the bar


def fraction(value, maximum):
    """The filled part, clamped to 0..1; unknown or invalid numbers are an empty bar."""
    try:
        value, maximum = float(value), float(maximum)
    except (TypeError, ValueError):
        return 0.0
    if not maximum > 0 or value != value:
        return 0.0
    return max(0.0, min(1.0, value / maximum))


def segment(phase, width, part=SEGMENT):
    """Left and right edges in pixels of the travelling segment at `phase` (0..1, increasing with time).

    It starts just outside the left edge and leaves through the right one, so its motion is always left to right."""
    length = max(1, round(width * part))
    left = round(-length + (width + length) * (phase % 1.0))
    return max(0, left), min(width, left + length)


class SnapBar(tk.Canvas):
    def __init__(self, parent, *, height=14, width=220, background=CREAM, mode='determinate', maximum=100, value=0, **ignored):
        super().__init__(parent, height=height, width=width, bg=background, highlightthickness=0, borderwidth=0)
        self._mode, self._maximum, self._value = str(mode), float(maximum), float(value)
        self._shown = fraction(value, maximum)      # what is drawn (approaches the target in determinate mode)
        self._phase, self._running, self._timer = 0.0, False, None
        self._bar_height, self._size, self._photo = height, None, None
        self._item = self.create_image(0, 0, anchor='nw')
        self.bind('<Configure>', lambda event: self._draw(), add='+')
        self.bind('<Destroy>', self._destroyed, add='+')

    # --- the ttk.Progressbar interface the launcher uses ---
    def configure(self, cnf=None, **options):
        options = dict(cnf or {}, **options)
        changed = False
        if 'mode' in options:
            mode = str(options.pop('mode'))
            if mode not in ('determinate', 'indeterminate'):
                raise tk.TclError(f'bad mode "{mode}"')
            if mode != self._mode:
                self._mode, self._phase, changed = mode, 0.0, True
                if mode == 'indeterminate':
                    self._shown = 0.0
        if 'maximum' in options:
            self._maximum, changed = float(options.pop('maximum')), True
        if 'value' in options:
            self._value, changed = float(options.pop('value')), True
        options.pop('style', None)
        options.pop('length', None)
        if options:
            super().configure(**options)
        if changed:
            self._retarget()
        return None

    config = configure

    def cget(self, key):
        if key == 'mode':
            return self._mode
        if key == 'value':
            return self._value
        if key == 'maximum':
            return self._maximum
        return super().cget(key)

    __getitem__ = cget

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def start(self, interval=None):
        """Begins the indeterminate animation (ignored in determinate mode, whose value says everything)."""
        self._running = True
        if self._mode == 'indeterminate':
            self._schedule()

    def stop(self):
        """Ends every animation; a determinate bar shows its value at once."""
        self._running = False
        self._cancel()
        self._phase = 0.0
        if self._mode == 'determinate':
            self._shown = fraction(self._value, self._maximum)
        self._draw()

    # --- animation ---
    def _retarget(self):
        if self._mode == 'determinate':
            target = fraction(self._value, self._maximum)
            if target <= self._shown or not self.winfo_ismapped():
                self._shown = target          # backwards (a new stage) or not visible: no animation
                self._cancel()
            else:
                self._schedule()
        elif self._running:
            self._schedule()
        else:
            self._cancel()
        self._draw()

    def _schedule(self):
        if self._timer is None:
            self._timer = self.after(FRAME_MS, self._step)

    def _cancel(self):
        if self._timer is not None:
            try:
                self.after_cancel(self._timer)
            except tk.TclError:
                pass
            self._timer = None

    def _step(self):
        self._cancel()      # at most one timer, also when a step is asked for directly
        if self._mode == 'indeterminate':
            if not self._running:
                return
            self._phase = (self._phase + FRAME_MS / SWEEP_MS) % 1.0
            self._schedule()
        else:
            target = fraction(self._value, self._maximum)
            gap = target - self._shown
            if gap > 0.002:
                self._shown += max(gap * 0.35, 0.004)
                self._shown = min(self._shown, target)
                self._schedule()
            else:
                self._shown = target
        self._draw()

    def _destroyed(self, event):
        if event.widget is self:
            self._running = False
            self._cancel()

    def destroy(self):
        self._running = False
        self._cancel()
        super().destroy()

    # --- drawing ---
    def _pictures(self, width, height):
        if self._size != (width, height):
            self._size = (width, height)
            self._trough = pill((width, height), TROUGH, outline=TROUGH_EDGE)
            self._fill = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            self._fill.paste(artwork.vertical_gradient((width, height), artwork.mix(LEAF, '#ffffff', 0.18), GREEN),
                             (0, 0), self._trough.getchannel('A'))
            shine = Image.new('L', (width, height), 0)
            ImageDraw.Draw(shine).rounded_rectangle((3, 2, width - 4, max(3, height // 2 - 1)), height // 4, fill=46)
            self._fill.paste(Image.new('RGB', (width, height), (255, 255, 255)), (0, 0),
                             Image.composite(shine, Image.new('L', (width, height), 0), self._trough.getchannel('A')))
        return self._trough, self._fill

    def _draw(self):
        try:
            width, height = self.winfo_width(), self.winfo_height()
        except tk.TclError:
            return
        if width < 8 or height < 4:
            return
        trough, fill = self._pictures(width, height)
        if self._mode == 'indeterminate':
            left, right = segment(self._phase, width) if self._running else (0, 0)
        else:
            left, right = 0, (0 if self._shown <= 0 else max(height, round(width * self._shown)))
        picture = trough.copy()
        if right > left:
            mask = Image.new('L', (width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle((left, 0, right - 1, height - 1), height // 2, fill=255)
            picture.paste(fill, (0, 0), Image.composite(mask, Image.new('L', (width, height), 0), fill.getchannel('A')))
        self._photo = ImageTk.PhotoImage(picture, master=self)
        self.itemconfigure(self._item, image=self._photo)

    def filled_pixels(self):
        """(left, right) of the fill as drawn now, for tests and diagnostics."""
        width, height = self.winfo_width(), self.winfo_height()
        if width < 8:      # not laid out yet: the size it asks for
            width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        if self._mode == 'indeterminate':
            return segment(self._phase, width) if self._running else (0, 0)
        return 0, (0 if self._shown <= 0 else max(height, round(width * self._shown)))


def page_bar(parent, **options):
    """A bar for a page that can also be built without widgets (its tests): None when `parent` is not a Tk widget.
    Callers treat the bar as optional, so the work it shows never depends on it."""
    return SnapBar(parent, **options) if hasattr(parent, 'tk') else None
