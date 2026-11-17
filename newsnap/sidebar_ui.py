"""Launcher navigation (LAUNCH-UI-01/02): a column with the brand, one real button per page (its own icon, with rest,
hover, pressed and selected states), the version and the main action pill, in place of the row of tabs. The pages
stay in the launcher's Notebook, whose tab row is hidden, so every `launcher.tabs.select(...)` keeps working and the
column follows it. Everything is drawn on one canvas over a background made by code (artwork.py): shapes come from
theme.py's antialiased images, the icons from artwork.icon()."""

from .launcher_language import tr
import tkinter as tk
import tkinter.font as tkfont

from . import artwork, fonts
from .theme import pill

GREEN, GREEN_TOP, CREAM, AMBER, MUTED, LEAF = '#163d32', '#1f5142', '#f5f1e5', '#dfa648', '#9fb8ad', '#57a57c'
WIDTH = 232
ITEM_H, ITEM_GAP, ITEM_X, ITEMS_TOP = 46, 6, 14, 122
PLAY_H = 58
ICONS = {'Inicio': 'home', 'Álbum': 'album', 'Opciones': 'options', 'Controles': 'controls', 'Mejoras': 'mods',
         'Actualizaciones': 'updates'}
ACTION_ICONS = {'play': 'play', 'verify': 'check', 'load': 'play'}


class Sidebar(tk.Canvas):
    def __init__(self, parent, notebook, pages, *, version, play, icon_path=None):
        super().__init__(parent, bg=GREEN, width=WIDTH, highlightthickness=0, borderwidth=0, takefocus=True)
        from PIL import Image, ImageTk
        self.Image, self.ImageTk = Image, ImageTk
        self.notebook, self.items, self.play_command, self.busy = notebook, [], play, False
        self.action = {'label': tr('Jugar'), 'kind': 'play', 'enabled': True}
        self._hover = self._pressed = None
        self._bg_photo, self._bg_height = None, None
        mk = self._mk = lambda picture: ImageTk.PhotoImage(picture, master=self)
        size = (WIDTH - 2 * ITEM_X, ITEM_H)
        self.pills = {
            'rest': mk(_ghost(size)),
            'hover': mk(artwork.with_alpha(pill(size, '#ffffff'), 0.17)),
            'pressed': mk(artwork.with_alpha(pill(size, '#000000'), 0.22)),
            'selected': mk(_raised(size, '#fffdf6', '#ece6d2')),
            'selected_pressed': mk(_raised(size, '#ece6d2', '#e2dcc6', press=1))}
        play_size = (WIDTH - 36, PLAY_H)
        self.play_images = {
            ('play', 'normal'): mk(_raised(play_size, '#f3c66f', '#dc9f3c', gloss=150)),
            ('play', 'active'): mk(_raised(play_size, '#f9d488', '#e6ad4b', gloss=170)),
            ('play', 'pressed'): mk(_raised(play_size, '#d29a3c', '#c98f31', press=1)),
            ('verify', 'normal'): mk(_raised(play_size, '#e3f1e3', '#b5d8bf', gloss=150)),
            ('verify', 'active'): mk(_raised(play_size, '#f0f8ee', '#c6e2cd', gloss=170)),
            ('verify', 'pressed'): mk(_raised(play_size, '#a9cdb4', '#9fc4aa', press=1)),
            'disabled': mk(artwork.with_alpha(_raised(play_size, '#b9b7a4', '#a9a792', press=1), 0.55))}
        self.action_icons = {(name, state): mk(artwork.icon(name, 24, colour))
                             for name in ('play', 'check') for state, colour in (('normal', GREEN), ('disabled', '#31493f'))}
        self._bg = self.create_image(0, 0, anchor='nw')
        brand = None
        if icon_path is not None:
            try:
                with Image.open(icon_path) as original:
                    brand = original.convert('RGBA').resize((44, 44), Image.LANCZOS)
            except (OSError, ValueError):
                brand = None
        self._brand = mk(brand if brand is not None else artwork.icon('camera', 40, AMBER))
        self.create_image(18, 22, image=self._brand, anchor='nw')
        self.create_text(70, 43, text='NewSnap', anchor='w', fill=CREAM, font=fonts.display(19))
        self.create_text(20, 76, text=tr('NEW POKÉMON SNAP\nPORT NATIVO'), anchor='nw', fill=AMBER, font=fonts.ui(8, 'bold'),
                         justify='left')
        self.icons = {}
        for index, page in enumerate(pages):
            frame, title = page[0], page[1]
            name = page[2] if len(page) > 2 else {tr(label): icon for label, icon in ICONS.items()}.get(title, 'home')
            self.items.append(self._item(index, frame, title, name))
        self._play_bg = self.create_image(18, 0, anchor='nw', image=self.play_images[('play', 'normal')])
        self._play_icon = self.create_image(0, 0, anchor='center', image=self.action_icons[('play', 'normal')])
        self._play_font = tkfont.Font(root=self, font=fonts.display(15))
        self._play_text = self.create_text(0, 0, anchor='w', text=tr('Jugar'), fill=GREEN, font=self._play_font)
        self._focus_ring = self.create_rectangle(0, 0, 0, 0, outline=CREAM, width=2, state='hidden')
        self.bind('<Return>', lambda event: self.invoke_play())
        self.bind('<space>', lambda event: self.invoke_play())
        self.bind('<FocusIn>', lambda event: self._paint_play())
        self.bind('<FocusOut>', lambda event: self._paint_play())
        self._version = self.create_text(20, 0, anchor='w', text=''.join((tr('Versión '), f'{version}',)), fill=MUTED, font=fonts.ui(9))
        self.bind('<Configure>', lambda event: self._layout(event.height), add='+')
        self.bind('<Motion>', self._motion)
        self.bind('<Leave>', lambda event: self._set(None, self._pressed))
        self.bind('<ButtonPress-1>', self._press)
        self.bind('<ButtonRelease-1>', self._release)
        notebook.bind('<<NotebookTabChanged>>', lambda event: self.refresh(), add='+')
        self._layout(int(self.cget('height')) or 600)
        self.refresh()

    # --- construction ---
    def _item(self, index, frame, title, name):
        y = ITEMS_TOP + index * (ITEM_H + ITEM_GAP)
        self.icons[index] = {state: self._mk(artwork.icon(name, 22, colour))
                             for state, colour in (('rest', '#dfe9df'), ('selected', GREEN))}
        bg = self.create_image(ITEM_X, y, anchor='nw', image=self.pills['rest'])
        icon = self.create_image(ITEM_X + 28, y + ITEM_H // 2 - 1, anchor='center', image=self.icons[index]['rest'])
        text = self.create_text(ITEM_X + 52, y + ITEM_H // 2 - 1, text=title, anchor='w', fill=CREAM, font=fonts.ui(12, 'bold'))
        return {'frame': frame, 'bg': bg, 'icon': icon, 'text': text, 'y': y, 'title': title}

    def _layout(self, height):
        height = max(height, ITEMS_TOP + len(self.items) * (ITEM_H + ITEM_GAP) + PLAY_H + 60)
        if height != self._bg_height:
            self._bg_height = height
            self._bg_photo = self._mk(artwork.sidebar_background((WIDTH, height), GREEN_TOP, '#113229', LEAF))
            self.itemconfigure(self._bg, image=self._bg_photo)
        self._play_y = height - 40 - PLAY_H
        self.coords(self._play_bg, 18, self._play_y)
        self.coords(self._focus_ring, 16, self._play_y-2, WIDTH-16, self._play_y+PLAY_H-2)
        self.coords(self._version, 22, height - 20)
        self._paint_play()

    # --- pointer: every button has rest, hover and pressed states and acts on release ---
    def _target(self, event):
        x, y = event.x, event.y
        if ITEM_X <= x < WIDTH - ITEM_X:
            for index, item in enumerate(self.items):
                if item['y'] <= y < item['y'] + ITEM_H:
                    return index
        if 18 <= x < WIDTH - 18 and self._play_y <= y < self._play_y + PLAY_H - 4:
            return 'play'
        return None

    def _motion(self, event):
        self._set(self._target(event), self._pressed)

    def _press(self, event):
        target = self._target(event)
        self._set(target, target)

    def _release(self, event):
        pressed, target = self._pressed, self._target(event)
        self._set(target, None)
        if pressed is None or pressed != target:
            return
        if target == 'play':
            self.invoke_play()
        else:
            self.select(target)

    def _set(self, hover, pressed):
        if (hover, pressed) != (self._hover, self._pressed):
            self._hover, self._pressed = hover, pressed
            self.configure(cursor='hand2' if hover is not None and (hover != 'play' or self._play_enabled()) else '')
            self.refresh()

    def select(self, index):
        """Shows the page of the button at `index`."""
        self.notebook.select(self.items[index]['frame'])

    def invoke_play(self):
        if self._play_enabled():
            self.play_command()

    # --- painting ---
    def refresh(self):
        try:
            current = self.notebook.select()
        except tk.TclError:
            return
        for index, item in enumerate(self.items):
            selected = current == str(item['frame'])
            pressed = self._pressed == index and self._hover == index
            if selected:
                image = self.pills['selected_pressed' if pressed else 'selected']
            else:
                image = self.pills['pressed' if pressed else 'hover' if self._hover == index and self._pressed in (None, index) else 'rest']
            self.itemconfigure(item['bg'], image=image)
            self.itemconfigure(item['icon'], image=self.icons[index]['selected' if selected else 'rest'])
            self.itemconfigure(item['text'], fill=GREEN if selected else CREAM)
        self._paint_play()

    def _play_enabled(self):
        return not self.busy and self.action['enabled']

    def _paint_play(self):
        self.itemconfigure(self._focus_ring, state='normal' if self.focus_get() == self else 'hidden')
        kind = 'verify' if self.action['kind'] == 'verify' else 'play'
        enabled = self._play_enabled()
        if not enabled:
            image = self.play_images['disabled']
        elif self._pressed == 'play' and self._hover == 'play':
            image = self.play_images[(kind, 'pressed')]
        else:
            image = self.play_images[(kind, 'active' if self._hover == 'play' and self._pressed in (None, 'play') else 'normal')]
        down = 1 if enabled and self._pressed == 'play' and self._hover == 'play' else 0
        self.itemconfigure(self._play_bg, image=image)
        icon = ACTION_ICONS.get(self.action['kind'], 'play')
        self.itemconfigure(self._play_icon, image=self.action_icons[(icon, 'normal' if enabled else 'disabled')])
        self.itemconfigure(self._play_text, text=self.action['label'], fill=GREEN if enabled else '#31493f')
        total = 24 + 10 + self._play_font.measure(self.action['label'])
        left = (WIDTH - total) // 2
        middle = self._play_y + (PLAY_H - 4) // 2 + down
        self.coords(self._play_icon, left + 12, middle)
        self.coords(self._play_text, left + 34, middle)

    def set_busy(self, busy):
        self.busy = busy
        self._paint_play()

    def set_action(self, label, kind='play', enabled=True):
        """The main action follows the state of the game data: «Jugar», «Verificar», «Verificando…»."""
        self.action = {'label': label, 'kind': kind, 'enabled': enabled}
        self._paint_play()


def _ghost(size):
    """A button at rest on the green column: a faint lighter fill with a slightly stronger rim."""
    from PIL import Image, ImageChops
    body = pill(size, '#ffffff')
    inner = Image.new('L', size, 0)
    inner.paste(pill((size[0] - 2, size[1] - 2), '#ffffff').getchannel('A'), (1, 1))
    rim = ImageChops.subtract(body.getchannel('A'), inner)
    out = body.copy()
    out.putalpha(ImageChops.add(body.getchannel('A').point(lambda v: int(v * 0.075)), rim.point(lambda v: int(v * 0.20))))
    return out


def _raised(size, top, bottom, gloss=120, press=0):
    """A pill that stands out from the column: gradient, light upper edge and a soft shadow."""
    return pill(size, top, fill2=bottom, shadow=True, gloss=gloss, press=press)


def chip(parent, text, kind='neutral'):
    """A rounded status label: 'ok' green, 'warn' amber, 'neutral' grey."""
    from PIL import ImageTk
    colours = {'ok': ('#d5e8dc', '#163d32'), 'warn': ('#f6e2b8', '#6b4a10'), 'neutral': ('#e5e5d9', '#3d5a50')}
    background, foreground = colours.get(kind, colours['neutral'])
    font = fonts.ui(10, 'bold')
    width = int(tkfont.Font(root=parent, font=font).measure(text)) + 26
    image = ImageTk.PhotoImage(pill((width, 26), background, outline=artwork.mix(background, foreground, 0.18)), master=parent)
    label = tk.Label(parent, text=text, image=image, compound='center', font=font, fg=foreground, bg='#f5f1e5', bd=0)
    label.image = image
    return label
