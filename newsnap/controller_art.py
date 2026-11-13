"""Original controller bitmap plus native Switch labels and live SDL highlights.

No image rewriting, SDL calls or output effects. `mapping`, when supplied, maps
Switch labels to SDL physical button names (for example {'A': 'south'}).
"""
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

ASSET_SHA256 = 'a8daabc38680527ad0bb4cc3115b9b07e157b0ea4f00aac27d1d042536b103c4'
ASSET_RELATIVE = Path('assets/controllers/ultimate2c-sprite.png')
SPRITE_SIZE = (104, 72)
CAPTION = 'Posiciones Switch · lectura física SDL'

# Sprite pixels, before the integer zoom and the header's vertical offset.
BUTTON_POSITIONS = {
    'A': (90.5, 20), 'B': (82.5, 28.5), 'X': (82.5, 12.5), 'Y': (74.5, 20),
    'L': (30, -6), 'R': (74, -6), 'ZL': (13, -6), 'ZR': (91, -6),
    '-': (37, 11), '+': (67, 11), 'L3': (20.5, 20.5), 'R3': (68, 38),
    'up': (36, 33), 'down': (36, 43), 'left': (31, 38), 'right': (41, 38),
}
SWITCH_TO_SDL = {
    'A': 'east', 'B': 'south', 'X': 'north', 'Y': 'west',
    'L': 'left_shoulder', 'R': 'right_shoulder', '-': 'back', '+': 'start',
    'L3': 'left_stick', 'R3': 'right_stick',
    'up': 'dpad_up', 'down': 'dpad_down', 'left': 'dpad_left', 'right': 'dpad_right',
}
TRIGGERS = {'ZL': 'left_trigger', 'ZR': 'right_trigger'}

# Every non-highlight colour below occurs in the source sprite's opaque palette.
INK = '#070402'
BUTTON = '#fbedaf'
BODY = '#fc977f'
HIGHLIGHT = '#38b7a5'  # UI state, not an artistic recolour of the source asset.

GLYPHS = {
    'A': ('010', '101', '111', '101', '101'),
    'B': ('110', '101', '110', '101', '110'),
    'X': ('101', '101', '010', '101', '101'),
    'Y': ('101', '101', '010', '010', '010'),
    'L': ('100', '100', '100', '100', '111'),
    'R': ('110', '101', '110', '101', '101'),
    'Z': ('111', '001', '010', '100', '111'),
    '3': ('110', '001', '010', '001', '110'),
    '+': ('000', '010', '111', '010', '000'),
    '-': ('000', '000', '111', '000', '000'),
    '^': ('010', '111', '010', '010', '000'),
    'v': ('000', '010', '010', '111', '010'),
    '<': ('001', '010', '100', '010', '001'),
    '>': ('100', '010', '001', '010', '100'),
}

# Native overlays cover the complete old button bounds first, then restore a
# clean pixel contour within those same bounds. The source's irregular dark
# bevels otherwise join the replacement letter and read as a second old glyph.
FACE_BOUNDS = {'X': (79, 9, 87, 17), 'Y': (71, 16, 79, 25),
               'A': (87, 16, 94, 25), 'B': (79, 24, 87, 33)}
FACE_CONTOURS = {
    'X': ((9, 81, 85), (10, 80, 86), (11, 79, 87), (12, 79, 87), (13, 79, 87),
          (14, 79, 87), (15, 80, 86), (16, 81, 85)),
    'Y': ((16, 73, 77), (17, 72, 78), (18, 71, 79), (19, 71, 79), (20, 71, 79),
          (21, 71, 79), (22, 71, 79), (23, 72, 78), (24, 73, 77)),
    'A': ((16, 89, 92), (17, 88, 93), (18, 87, 94), (19, 87, 94), (20, 87, 94),
          (21, 87, 94), (22, 87, 94), (23, 88, 93), (24, 89, 92)),
    'B': ((24, 81, 85), (25, 80, 86), (26, 79, 87), (27, 79, 87), (28, 79, 87),
          (29, 79, 87), (30, 79, 87), (31, 80, 86), (32, 81, 85)),
}
FACE_MASKS = {label: tuple((y, left+1, right-1) for y, left, right in rows[1:-1])
              for label, rows in FACE_CONTOURS.items()}
FACE_GLYPH_ORIGINS = {'X': (81, 11), 'Y': (73, 18), 'A': (89, 18), 'B': (81, 26)}
# The upper button is eight pixels high: a four-row X leaves a clear row above
# and below. The other buttons fit the original five-row letter grid.
FACE_GLYPHS = {**GLYPHS, 'X': ('101', '010', '010', '101')}


def asset_path(resource_root=None):
    candidates = []
    if resource_root is not None:
        candidates.append(Path(resource_root) / ASSET_RELATIVE)
    if getattr(sys, '_MEIPASS', None):
        candidates.append(Path(sys._MEIPASS) / ASSET_RELATIVE)
    candidates.append(Path(__file__).resolve().parents[1] / ASSET_RELATIVE)
    return next((path for path in candidates if path.is_file()), candidates[0])


def _axis(axes, name):
    try:
        return max(-32768, min(32767, int(axes.get(name, 0))))
    except (ValueError, TypeError, OverflowError):
        return 0


def active_controls(snapshot, mapping=None):
    """Physical SDL positions, not a promise about the game's current bindings."""
    if not snapshot or not snapshot.get('connected') or not snapshot.get('recognized'):
        return set()
    buttons, axes = snapshot.get('buttons') or {}, snapshot.get('axes') or {}
    positions = dict(SWITCH_TO_SDL)
    if mapping is not None:
        positions.update({label: physical for label, physical in mapping.items() if label in positions})
    pressed = {label for label, physical in positions.items() if buttons.get(physical, False)}
    pressed.update(label for label, axis in TRIGGERS.items() if _axis(axes, axis) > 16384)
    return pressed


class ControllerArt(ttk.Frame):
    """Native Tk panel; keep a reference and call set_buttons(snapshot) per poll.

    A single controller snapshot is accepted. None, disconnected devices and
    unrecognized joysticks clear the picture; raw indices remain in UI details.
    The immutable 104x72 bitmap is enlarged with PhotoImage.zoom (nearest, integer).
    """
    def __init__(self, parent, resource_root=None, *, scale=4, **kwargs):
        super().__init__(parent, **kwargs)
        if type(scale) is not int or scale < 1:
            raise ValueError('La escala del mando debe ser un entero positivo.')
        self.scale = scale
        self._offset = 12
        self._last = None
        self.caption = ttk.Label(self, text=CAPTION)
        self.caption.pack(anchor='center', pady=(0, 4))
        background = ttk.Style(self).lookup('TFrame', 'background') or self.winfo_toplevel().cget('background')
        self.canvas = tk.Canvas(self, width=104*scale, height=84*scale, background=background,
                                borderwidth=0, highlightthickness=0)
        self.canvas.pack()
        self._original = tk.PhotoImage(master=self, file=str(asset_path(resource_root)))
        if (self._original.width(), self._original.height()) != SPRITE_SIZE:
            raise ValueError('El recurso original del mando debe medir 104 × 72 píxeles.')
        self._sprite = self._original.zoom(scale, scale)
        self.canvas.create_image(0, self._offset*scale, image=self._sprite, anchor='nw')
        self.set_buttons(None)

    def _box(self, x0, y0, x1, y1, fill, outline='', width=0):
        z, dy = self.scale, self._offset
        return self.canvas.create_rectangle(x0*z, (y0+dy)*z, x1*z, (y1+dy)*z,
                                            fill=fill, outline=outline, width=width*z, tags='overlay')

    def _glyph(self, text, x, y, colour=INK, glyphs=GLYPHS):
        for index, char in enumerate(text):
            for row, line in enumerate(glyphs[char]):
                for column, pixel in enumerate(line):
                    if pixel == '1':
                        left = x + 4*index + column
                        self._box(left, y+row, left+1, y+row+1, colour)

    def _badge(self, label, x, y, pressed):
        width = len(label)*4-1
        self._box(x-width/2-1, y-3.5, x+width/2+1, y+3.5,
                  HIGHLIGHT if pressed else INK)
        self._glyph(label, x-width/2, y-2.5, INK if pressed else BUTTON)

    def set_buttons(self, snapshot, mapping=None):
        pressed = active_controls(snapshot, mapping)
        valid = bool(snapshot and snapshot.get('connected') and snapshot.get('recognized'))
        axes = snapshot.get('axes') or {} if valid else {}
        sticks = tuple((_axis(axes, name+'x'), _axis(axes, name+'y')) for name in ('left', 'right'))
        state = (frozenset(pressed), sticks, bool(mapping))
        if state == self._last:
            return
        self._last = state
        self.caption.configure(text=CAPTION if not mapping else 'Posiciones Switch · mapeo indicado')
        self.canvas.delete('overlay')
        for label, rows in FACE_MASKS.items():
            self._box(*FACE_BOUNDS[label], BODY)
            for y, left, right in FACE_CONTOURS[label]:
                self._box(left, y, right, y+1, INK)
            for y, left, right in rows:
                self._box(left, y, right, y+1, HIGHLIGHT if label in pressed else BUTTON)
            self._glyph(label, *FACE_GLYPH_ORIGINS[label], glyphs=FACE_GLYPHS)
        for label in ('ZL', 'L', 'R', 'ZR'):
            self._badge(label, *BUTTON_POSITIONS[label], label in pressed)
        for label in ('-', '+'):
            x, y = BUTTON_POSITIONS[label]
            self._badge(label, x, y, label in pressed)
        for index, label in enumerate(('L3', 'R3')):
            x, y = BUTTON_POSITIONS[label]
            self._badge(label, x, y+12, label in pressed)
            dx, dy = sticks[index]
            if label in pressed or dx or dy:
                z, top = self.scale, self._offset
                self.canvas.create_oval((x-8)*z, (y-8+top)*z, (x+8)*z, (y+8+top)*z,
                                        outline=HIGHLIGHT, width=z, tags='overlay')
            if dx or dy:
                # SDL Y grows downward, matching the native canvas; no game-axis inversion.
                px, py = round(x+dx/32768*5), round(y+dy/32768*5)
                self._box(px-1, py-1, px+1, py+1, HIGHLIGHT)
        for label, arrow in (('up', '^'), ('down', 'v'), ('left', '<'), ('right', '>')):
            if label in pressed:
                x, y = BUTTON_POSITIONS[label]
                self._box(x-2, y-3, x+3, y+3, HIGHLIGHT)
                self._glyph(arrow, x-1, y-2)
