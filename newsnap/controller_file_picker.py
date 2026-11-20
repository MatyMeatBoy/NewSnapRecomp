"""Local Tk file pickers; browsing and selection never require typed paths."""
import fnmatch
import os
from pathlib import Path
import string
import tkinter as tk
from tkinter import ttk

from .controller_dialogs import askyesno, modal
from .launcher_language import tr


class Browser:
    """Read-only filesystem model, also usable without constructing any UI."""
    def __init__(self, directory, *, mode='open', filetypes=(), defaultextension=''):
        self.directory = Path(directory).expanduser().absolute()
        self.mode = mode
        self.filetypes = filetypes or ((tr('Todos los archivos'), '*'),)
        self.filter_index = 0
        self.extension = defaultextension

    def entries(self):
        patterns = self.filetypes[self.filter_index][1]
        if isinstance(patterns, str): patterns = patterns.split()
        patterns = [pattern.lower() for pattern in patterns]
        def accepted(path):
            return path.is_dir() or self.mode != 'directory' and any(
                pattern in ('*', '*.*') or fnmatch.fnmatchcase(path.name.lower(), pattern) for pattern in patterns)
        return sorted((path for path in self.directory.iterdir() if accepted(path)),
                      key=lambda path: (not path.is_dir(), path.name.casefold()))

    def enter(self, path):
        path = Path(path).expanduser().absolute()
        if not path.is_dir(): raise ValueError(tr('Elige una carpeta.'))
        # Probe before replacing the current directory; an inaccessible location
        # must not strand the picker away from its previous usable directory.
        with os.scandir(path): pass
        self.directory = path

    def choose(self, path=None):
        if path is None:
            if self.mode != 'directory': raise ValueError(tr('Elige un archivo.'))
            path = self.directory
        path = Path(path).expanduser()
        if not path.is_absolute(): path = self.directory / path
        if self.mode == 'directory':
            if not path.is_dir(): raise ValueError(tr('Elige una carpeta.'))
        elif self.mode == 'open':
            if not path.is_file(): raise ValueError(tr('Elige un archivo existente.'))
        else:
            if path.is_dir() or not path.name or not path.parent.is_dir():
                raise ValueError(tr('Elige un archivo en una carpeta existente.'))
            if self.extension and not path.suffix:
                path = path.with_suffix(self.extension if self.extension.startswith('.') else '.' + self.extension)
        return path.absolute()


def locations():
    result = [Path.home()]
    if os.name == 'nt':
        result.extend(Path(letter + ':\\') for letter in string.ascii_uppercase if Path(letter + ':\\').is_dir())
    else:
        result.append(Path('/'))
    return list(dict.fromkeys(result))


class FilePicker:
    def __init__(self, parent, *, mode='open', title='', initialdir=None, initialfile='', filetypes=(),
                 defaultextension='', **options):
        self.parent = parent
        directory = Path(initialdir).expanduser() if initialdir else Path.home()
        if not directory.is_dir(): directory = Path.home()
        self.browser = Browser(directory, mode=mode, filetypes=filetypes, defaultextension=defaultextension)
        self.result = ''
        self.window = window = tk.Toplevel(parent)
        window.title(title or tr('Elige un archivo'))
        window.geometry('780x540'); window.minsize(520, 360)
        frame = ttk.Frame(window, padding=16); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=tr('Sur: abrir/seleccionar · Este: cancelar · Izquierda/Derecha: mover el foco')).pack(anchor='w')
        self.path = tk.StringVar(value=str(self.browser.directory))
        ttk.Label(frame, textvariable=self.path, wraplength=730).pack(anchor='w', pady=8)
        top = ttk.Frame(frame); top.pack(fill='x', pady=(0, 8))
        ttk.Button(top, text=tr('Carpeta superior'), command=self.parent_folder).pack(side='left')
        ttk.Button(top, text=tr('Carpeta personal'), command=lambda: self.enter(Path.home())).pack(side='left', padx=6)
        self.places = locations()
        self.place = ttk.Combobox(top, state='readonly', values=[str(p) for p in self.places], width=28)
        self.place.pack(side='left', padx=6)
        self.place.bind('<<ComboboxSelected>>', lambda event: self.enter(self.places[self.place.current()]))
        filters = ttk.Combobox(top, state='readonly', values=[row[0] for row in self.browser.filetypes], width=22)
        filters.current(0); filters.pack(side='right')
        filters.bind('<<ComboboxSelected>>', lambda event: self.filter_changed(filters.current()))
        middle = ttk.Frame(frame); middle.pack(fill='both', expand=True)
        self.list = tk.Listbox(middle, exportselection=False, activestyle='dotbox', selectmode='browse')
        scroll = ttk.Scrollbar(middle, command=self.list.yview)
        self.list.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.list.pack(side='left', fill='both', expand=True)
        self.list.bind('<Return>', self.open_selected)
        self.list.bind('<Double-Button-1>', self.open_selected)
        self.name = tk.StringVar(value=initialfile)
        if mode == 'save':
            ttk.Label(frame, text=tr('Nombre del archivo')).pack(anchor='w', pady=(8, 0))
            entry = ttk.Entry(frame, textvariable=self.name); entry.pack(fill='x')
            entry.bind('<Return>', lambda event: self.select())
        self.error = tk.StringVar()
        ttk.Label(frame, textvariable=self.error, wraplength=730).pack(anchor='w', pady=8)
        bottom = ttk.Frame(frame); bottom.pack(fill='x')
        ttk.Button(bottom, text=tr('Cancelar'), command=self.cancel).pack(side='right')
        ttk.Button(bottom, text=tr('Seleccionar esta carpeta') if mode == 'directory' else tr('Guardar') if mode == 'save' else tr('Abrir'),
                   command=self.select).pack(side='right', padx=8)
        window.protocol('WM_DELETE_WINDOW', self.cancel)
        window.bind('<Escape>', lambda event: self.cancel())
        window.bind('<<ControllerBack>>', lambda event: self.cancel())
        self.rows = []
        self.refresh()

    def refresh(self):
        try:
            rows = self.browser.entries()
        except (OSError, ValueError) as error:
            self.error.set(str(error)); return
        self.rows = rows
        self.path.set(str(self.browser.directory)); self.error.set('')
        self.list.delete(0, 'end')
        for path in rows: self.list.insert('end', ('[+] ' if path.is_dir() else '    ') + path.name)
        if rows: self.list.selection_set(0); self.list.activate(0)

    def enter(self, path):
        try:
            self.browser.enter(path)
            self.refresh()
        except (OSError, ValueError) as error: self.error.set(str(error))

    def parent_folder(self):
        self.enter(self.browser.directory.parent)

    def filter_changed(self, index):
        self.browser.filter_index = index
        self.refresh()

    def selected(self):
        selection = self.list.curselection()
        return self.rows[selection[0]] if selection and selection[0] < len(self.rows) else None

    def open_selected(self, event=None):
        selected = self.selected()
        if selected is not None and selected.is_dir(): self.enter(selected)
        elif selected is not None:
            if self.browser.mode == 'save': self.name.set(selected.name)
            self.select()
        return 'break'

    def select(self):
        try:
            if self.browser.mode == 'save':
                if not self.name.get().strip(): raise ValueError(tr('Elige un nombre de archivo.'))
                chosen = self.browser.choose(self.name.get())
                if chosen.exists() and not askyesno(tr('Reemplazar archivo'), tr('¿Reemplazar este archivo?') + '\n' + str(chosen), parent=self.window): return
            else:
                selected = self.selected()
                if self.browser.mode == 'open' and selected is not None and selected.is_dir():
                    self.enter(selected); return
                chosen = self.browser.choose(None if self.browser.mode == 'directory' else selected)
            self.result = str(chosen)
            self.window.destroy()
        except (OSError, ValueError) as error: self.error.set(str(error))

    def cancel(self):
        self.result = ''
        self.window.destroy()

    def show(self):
        modal(self.window, self.parent, self.list)
        return self.result


def askopenfilename(**options):
    return FilePicker(mode='open', **options).show()


def askdirectory(**options):
    return FilePicker(mode='directory', **options).show()


def asksaveasfilename(**options):
    return FilePicker(mode='save', **options).show()
