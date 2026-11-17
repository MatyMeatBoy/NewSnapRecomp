"""Home's «Añadir a Steam» / «Quitar de Steam» and «Acceso directo» buttons (newsnap/steam_shortcuts.py)."""

from .launcher_language import tr
import sys
from pathlib import Path
from tkinter import messagebox, ttk


class ShortcutButtons:
    def __init__(self, launcher, parent):
        self.launcher = launcher
        self.steam = ttk.Button(parent, text=tr('Añadir a Steam'), command=self.toggle_steam)
        self.steam.pack(side='left', padx=(0, 8))
        self.link = ttk.Button(parent, text=tr('Acceso directo'), command=self.shortcut)
        self.link.pack(side='left', padx=(0, 8))
        from .tooltip import Tooltip
        Tooltip(self.steam, tr('Lo añade a tu biblioteca de Steam como juego externo, con portada, logo e icono: para jugar con Steam Input, Big Picture o la superposición de Steam. Abre el juego directamente con tus ajustes. Steam lee la lista al iniciarse: si está abierto, reinícialo.'))
        Tooltip(self.link, tr('Crea un acceso directo en el escritorio que abre el juego directamente con tus ajustes.'))
        if self.exe() is None:
            for button in (self.steam, self.link):
                button.configure(state='disabled')
        self.refresh()

    def exe(self):
        if getattr(sys, 'frozen', False):
            return Path(sys.executable)
        candidate = Path(self.launcher.project) / 'NewSnapLauncher.exe'
        return candidate if candidate.is_file() else None

    def refresh(self):
        from .steam_shortcuts import in_steam
        try:
            self.steam.configure(text=tr('Quitar de Steam') if in_steam(self.launcher.project) else tr('Añadir a Steam'))
        except OSError:
            pass

    def toggle_steam(self):
        from . import steam_shortcuts as s
        root = Path(self.launcher.project)
        try:
            if s.in_steam(root):
                done = s.remove_from_steam(root)
                text = (tr('Quitado de Steam. Si Steam está abierto, reinícialo para que desaparezca de la biblioteca.')
                        if done else tr('No estaba en la lista de juegos de Steam; no se cambió nada.'))
            else:
                done = s.add_to_steam(root, self.exe(), root / 'assets/launcher')
                text = (tr('Añadido a Steam con su portada. Si Steam está abierto, reinícialo para verlo en la biblioteca.')
                        if done else tr('No se encontró Steam (o ninguna cuenta ha iniciado sesión en él).'))
        except (OSError, ValueError) as error:
            done, text = 0, ''.join((tr('No se pudo cambiar Steam: '), f'{error}',))
        self.launcher.status.set(text)
        if not done:
            messagebox.showwarning('Steam', text, parent=self.launcher.root)
        self.refresh()

    def shortcut(self):
        from .steam_shortcuts import desktop_shortcut
        try:
            link = desktop_shortcut(self.launcher.project, self.exe())
            self.launcher.status.set(''.join((tr('Acceso directo creado en el escritorio: '), f'{link.name}',)))
        except (OSError, Exception) as error:   # PowerShell or COM unavailable: say so, nothing else changes
            self.launcher.status.set(''.join((tr('No se pudo crear el acceso directo: '), f'{error}',)))
