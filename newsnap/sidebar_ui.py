"""Launcher navigation (LAUNCH-UI-01): a sidebar with the brand, rounded («bubble») page entries, the version and a
Play pill, in place of the row of tabs. The pages stay in the launcher's Notebook, whose tab row is hidden, so every
`launcher.tabs.select(...)` keeps working and the sidebar follows it. Shapes come from theme.py's antialiased images."""
import tkinter as tk
import tkinter.font as tkfont

from .theme import pill

GREEN, GREEN_HI, GREEN_SEL, CREAM, AMBER, MUTED = '#163d32', '#1f4e40', '#2b5f4e', '#f5f1e5', '#dfa648', '#9fb8ad'
WIDTH = 220


class Sidebar(tk.Frame):
    def __init__(self, parent, notebook, pages, *, version, play):
        super().__init__(parent, bg=GREEN, width=WIDTH)
        self.pack_propagate(False)
        self.notebook, self.items, self.play_command, self.busy = notebook, [], play, False
        from PIL import ImageTk
        mk = lambda picture: ImageTk.PhotoImage(picture, master=self)
        self.pills = {'hover': mk(pill((WIDTH - 28, 42), GREEN_HI)), 'selected': mk(pill((WIDTH - 28, 42), GREEN_SEL))}
        self.play_images = {'normal': mk(pill((WIDTH - 36, 56), AMBER)), 'active': mk(pill((WIDTH - 36, 56), '#efc070')),
                            'disabled': mk(pill((WIDTH - 36, 56), '#8f8467'))}
        tk.Label(self, text='NewSnap', font=('Segoe UI', 23, 'bold'), fg=CREAM, bg=GREEN).pack(anchor='w', padx=24, pady=(24, 0))
        tk.Label(self, text='NEW POKÉMON SNAP\nPORT NATIVO', font=('Segoe UI', 8, 'bold'), fg=AMBER, bg=GREEN,
                 justify='left').pack(anchor='w', padx=24, pady=(2, 20))
        for frame, title in pages:
            self.items.append(self._item(frame, title))
        bottom = tk.Frame(self, bg=GREEN)
        bottom.pack(side='bottom', fill='x', padx=18, pady=18)
        self.play = tk.Canvas(bottom, width=WIDTH - 36, height=56, bg=GREEN, highlightthickness=0, cursor='hand2')
        self.play.pack()
        self._play_bg = self.play.create_image(0, 0, image=self.play_images['normal'], anchor='nw')
        self.play.create_text((WIDTH - 36) // 2, 28, text='▶  Jugar', fill=GREEN, font=('Segoe UI', 15, 'bold'))
        self.play.bind('<Button-1>', lambda event: None if self.busy else self.play_command())
        self.play.bind('<Enter>', lambda event: self._paint_play('active'))
        self.play.bind('<Leave>', lambda event: self._paint_play('normal'))
        tk.Label(bottom, text=f'Versión {version}', font=('Segoe UI', 9), fg=MUTED, bg=GREEN).pack(anchor='w', pady=(12, 0))
        notebook.bind('<<NotebookTabChanged>>', lambda event: self.refresh(), add='+')
        self.refresh()

    def _paint_play(self, state):
        self.play.itemconfigure(self._play_bg, image=self.play_images['disabled' if self.busy else state])

    def _item(self, frame, title):
        canvas = tk.Canvas(self, width=WIDTH - 28, height=42, bg=GREEN, highlightthickness=0, cursor='hand2')
        canvas.pack(padx=14, pady=2, anchor='w')
        bg = canvas.create_image(0, 0, anchor='nw', image='')
        dot = canvas.create_oval(14, 18, 20, 24, fill=AMBER, outline='', state='hidden')
        text = canvas.create_text(30, 21, text=title, anchor='w', fill=CREAM, font=('Segoe UI', 12))
        item = {'frame': frame, 'canvas': canvas, 'bg': bg, 'dot': dot, 'text': text}
        canvas.bind('<Button-1>', lambda event: self.notebook.select(frame))
        canvas.bind('<Enter>', lambda event: self._paint(item, hover=True))
        canvas.bind('<Leave>', lambda event: self._paint(item))
        return item

    def _paint(self, item, hover=False):
        selected = self.notebook.select() == str(item['frame'])
        c = item['canvas']
        c.itemconfigure(item['bg'], image=self.pills['selected'] if selected else self.pills['hover'] if hover else '')
        c.itemconfigure(item['dot'], state='normal' if selected else 'hidden')
        c.itemconfigure(item['text'], font=('Segoe UI', 12, 'bold' if selected else 'normal'))

    def refresh(self):
        for item in self.items:
            self._paint(item)

    def set_busy(self, busy):
        self.busy = busy
        self._paint_play('normal')


def chip(parent, text, kind='neutral'):
    """A rounded status label: 'ok' green, 'warn' amber, 'neutral' grey."""
    from PIL import ImageTk
    colours = {'ok': ('#d5e8dc', '#163d32'), 'warn': ('#f6e2b8', '#6b4a10'), 'neutral': ('#e5e5d9', '#3d5a50')}
    background, foreground = colours.get(kind, colours['neutral'])
    font = ('Segoe UI', 9, 'bold')
    width = int(tkfont.Font(root=parent, font=font).measure(text)) + 24
    image = ImageTk.PhotoImage(pill((width, 24), background), master=parent)
    label = tk.Label(parent, text=text, image=image, compound='center', font=font, fg=foreground, bg='#f5f1e5', bd=0)
    label.image = image
    return label
