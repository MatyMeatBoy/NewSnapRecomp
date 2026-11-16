"""«Generar sombras HD» in the launcher's Mejoras tab (HD-SHADOW-01/02): builds, on this PC, the HD shadows of every
level from the player's game files (newsnap/game_textures.py, newsnap/hdshadows.py), in a background thread with its
progress in the status bar. It can be stopped and goes on later from where it was."""
import threading
import tkinter as tk
from tkinter import ttk

from .paths import data_dir, runtime_dir


class HdShadowsButton:
    label = 'Generar sombras HD'

    def __init__(self, launcher, parent):
        self.launcher, self.running, self.cancel = launcher, False, threading.Event()
        self.after = None
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=(0, 10))
        self.button = ttk.Button(row, text=self.label, command=self.toggle)
        self.button.pack(side='left')
        self.state = tk.StringVar(value=self._summary())
        ttk.Label(row, textvariable=self.state, style='Muted.TLabel', wraplength=520).pack(side='left', padx=(10, 0))

    def folder(self):
        return runtime_dir(self.launcher.project) / 'hdshadows'

    def _summary(self):
        from .game_textures import complete
        folder = self.folder()
        made = sum(1 for p in folder.glob('*.dds') if len(p.stem) == 16) if folder.is_dir() else 0
        if complete(folder):
            return f'Listo: las sombras de todos los niveles están en HD ({made} texturas).'
        if made:
            return f'{made} texturas en HD · faltan niveles: pulsa el botón para continuar.'
        return 'Sin generar. Se hace una vez, con tu propio juego: unos 35 minutos y 6 GB.'

    def waiting(self):
        """True while the HD shadows of some level are not built."""
        from .game_textures import complete
        return not complete(self.folder())

    def toggle(self):
        """The button: start, or stop. A build the player stopped does not start again by itself in this session."""
        self.launcher.hd_shadows_stopped = self.running
        if self.running:
            self.stop()
        else:
            self.start()

    def stop(self):
        """Stops the build; what is made stays and the next start goes on from there."""
        if self.running:
            self.cancel.set()
            self.button.configure(state='disabled')

    def _work(self, report):
        from .game_textures import install
        from .hdshadows import ensure_esrgan, generate
        ensure_esrgan(report)
        project = self.launcher.project
        made, kept, failed = install(runtime_dir(project), data_dir(project), report=report, cancel=self.cancel)
        if not self.cancel.is_set():   # light maps saved while playing by versions before 0.9.15
            more = generate(self.folder(), report=report, cancel=self.cancel)
            made, failed = made + more[0], failed + more[2]
        if self.cancel.is_set():
            report('Sombras HD: detenido. Lo generado se conserva; continúa al volver a pulsar el botón.')
        else:
            report(f'Sombras HD: {made} texturas generadas' + (f', {failed} sin procesar' if failed else '')
                   + '. Se ven desde la próxima vez que abras el juego.')

    def start(self, after=None):
        if self.running or self.launcher.busy:
            return False
        self.after = after
        self.running = True
        self.cancel.clear()
        self.button.configure(text='Detener')
        status = self.launcher.status

        def report(text):
            self.launcher.root.after(0, status.set, text)

        def work():
            try:
                self._work(report)
            except Exception as error:   # shown to the player; the game is not affected
                report(f'{self.label} sin completar: {error}')
            finally:
                self.launcher.root.after(0, self._done)

        threading.Thread(target=work, daemon=True).start()
        return True

    def _done(self):
        self.running = False
        self.button.configure(state='normal', text=self.label)
        self.state.set(self._summary())
        after, self.after = self.after, None
        if after and not self.cancel.is_set():
            after()


class TexturePackButton(HdShadowsButton):
    """«Generar pack de texturas HD» (TEXPACK-01): the colour textures saved in texpack/src, enlarged into texpack/."""
    label = 'Generar pack de texturas HD'

    def folder(self):
        return runtime_dir(self.launcher.project) / 'texpack'

    def _summary(self):
        from .texpack_gen import pending
        folder = self.folder()
        if not (folder / 'src').is_dir():
            return 'Aún no hay texturas guardadas: activa «Guardar texturas para el pack» y juega.'
        made = sum(1 for p in folder.glob('*.dds') if len(p.stem) == 16)
        return f'{made} texturas en HD · {len(pending(folder))} por generar'

    def waiting(self):
        from .texpack_gen import pending
        return bool(pending(self.folder())) if (self.folder() / 'src').is_dir() else False

    def _work(self, report):
        from .hdshadows import ensure_esrgan
        from .texpack_gen import generate
        ensure_esrgan(report)
        made, failed = generate(self.folder(), report=report, cancel=self.cancel)
        report(f'Pack de texturas HD: {made} texturas generadas'
               + (f', {failed} sin procesar' if failed else '') + '. Se usan al volver a cargarlas.')
