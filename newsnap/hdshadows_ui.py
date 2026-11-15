"""«Generar sombras HD» in the launcher's Mejoras tab (HD-SHADOW-01): enlarges, on this PC, the light maps the game
wrote while HD shadows were on (newsnap/hdshadows.py), in a background thread with its progress in the status bar."""
import threading
import tkinter as tk
from tkinter import ttk

from .paths import runtime_dir


class HdShadowsButton:
    def __init__(self, launcher, parent):
        self.launcher, self.running, self.cancel = launcher, False, threading.Event()
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=(0, 10))
        self.button = ttk.Button(row, text='Generar sombras HD', command=self.start)
        self.button.pack(side='left')
        self.state = tk.StringVar(value=self._summary())
        ttk.Label(row, textvariable=self.state, style='Muted.TLabel', wraplength=520).pack(side='left', padx=(10, 0))

    def folder(self):
        return runtime_dir(self.launcher.project) / 'hdshadows'

    def _summary(self):
        from .hdshadows import pending
        folder = self.folder()
        if not (folder / 'src').is_dir():
            return 'Aún no hay mapas de luz guardados: activa la opción y juega un nivel.'
        made = sum(1 for p in folder.glob('*.dds') if len(p.stem) == 16)
        waiting = len(pending(folder))
        return f'{made} mapas en HD · {waiting} por generar'

    def start(self):
        if self.running or self.launcher.busy:
            return
        self.running = True
        self.cancel.clear()
        self.button.configure(state='disabled')
        status = self.launcher.status

        def report(text):
            self.launcher.root.after(0, status.set, text)

        def work():
            try:
                from .hdshadows import ensure_esrgan, generate
                ensure_esrgan(report)
                made, kept, failed = generate(self.folder(), report=report, cancel=self.cancel)
                report(f'Sombras HD: {made} mapas generados'
                       + (f', {failed} sin procesar' if failed else '') + '. Se usan al volver a entrar al nivel.')
            except Exception as error:   # shown to the player; the game is not affected
                report(f'Sombras HD sin completar: {error}')
            finally:
                self.launcher.root.after(0, self._done)

        threading.Thread(target=work, daemon=True).start()

    def _done(self):
        self.running = False
        self.button.configure(state='normal')
        self.state.set(self._summary())
