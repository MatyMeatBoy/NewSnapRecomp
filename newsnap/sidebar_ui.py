"""Launcher navigation (LAUNCH-UI-01): a sidebar with the brand, one entry per page, the version and a Play button,
in place of the row of tabs. The pages stay in the launcher's Notebook, whose tab row is hidden, so every
`launcher.tabs.select(...)` keeps working and the sidebar follows it."""
import tkinter as tk

GREEN, GREEN_HI, GREEN_SEL, CREAM, AMBER, MUTED = '#163d32', '#1f4e40', '#245846', '#f5f1e5', '#dfa648', '#9fb8ad'


class Sidebar(tk.Frame):
    def __init__(self, parent, notebook, pages, *, version, play):
        super().__init__(parent, bg=GREEN, width=212)
        self.pack_propagate(False)
        self.notebook, self.items = notebook, []
        tk.Label(self, text='NewSnap', font=('Segoe UI', 22, 'bold'), fg=CREAM, bg=GREEN).pack(anchor='w', padx=22, pady=(22, 0))
        tk.Label(self, text='NEW POKÉMON SNAP\nPORT NATIVO', font=('Segoe UI', 8, 'bold'), fg=AMBER, bg=GREEN,
                 justify='left').pack(anchor='w', padx=22, pady=(2, 22))
        for frame, title in pages:
            self.items.append(self._item(frame, title))
        bottom = tk.Frame(self, bg=GREEN)
        bottom.pack(side='bottom', fill='x', padx=18, pady=18)
        self.play = tk.Button(bottom, text='▶  Jugar', command=play, font=('Segoe UI', 14, 'bold'), fg=GREEN, bg=AMBER,
                              activebackground='#efc070', activeforeground=GREEN, relief='flat', bd=0, cursor='hand2',
                              disabledforeground='#7c6a45', pady=10)
        self.play.pack(fill='x')
        tk.Label(bottom, text=f'Versión {version}', font=('Segoe UI', 9), fg=MUTED, bg=GREEN).pack(anchor='w', pady=(10, 0))
        notebook.bind('<<NotebookTabChanged>>', lambda event: self.refresh(), add='+')
        self.refresh()

    def _item(self, frame, title):
        row = tk.Frame(self, bg=GREEN, cursor='hand2')
        row.pack(fill='x')
        bar = tk.Frame(row, bg=GREEN, width=4)
        bar.pack(side='left', fill='y')
        label = tk.Label(row, text=title, font=('Segoe UI', 12), fg=CREAM, bg=GREEN, anchor='w', padx=18, pady=9)
        label.pack(side='left', fill='x', expand=True)
        item = {'frame': frame, 'row': row, 'bar': bar, 'label': label}
        for widget in (row, label):
            widget.bind('<Button-1>', lambda event: self.notebook.select(frame))
            widget.bind('<Enter>', lambda event: self._paint(item, hover=True))
            widget.bind('<Leave>', lambda event: self._paint(item))
        return item

    def _paint(self, item, hover=False):
        selected = self.notebook.select() == str(item['frame'])
        background = GREEN_SEL if selected else GREEN_HI if hover else GREEN
        item['row'].configure(bg=background)
        item['label'].configure(bg=background, font=('Segoe UI', 12, 'bold' if selected else 'normal'))
        item['bar'].configure(bg=AMBER if selected else background)

    def refresh(self):
        for item in self.items:
            self._paint(item)

    def set_busy(self, busy):
        self.play.configure(state='disabled' if busy else 'normal')


def chip(parent, text, kind='neutral'):
    """A small status label: 'ok' green, 'warn' amber, 'neutral' grey."""
    colours = {'ok': ('#d5e8dc', '#163d32'), 'warn': ('#f6e2b8', '#6b4a10'), 'neutral': ('#e5e5d9', '#3d5a50')}
    background, foreground = colours.get(kind, colours['neutral'])
    return tk.Label(parent, text=text, font=('Segoe UI', 9, 'bold'), bg=background, fg=foreground, padx=10, pady=3)
