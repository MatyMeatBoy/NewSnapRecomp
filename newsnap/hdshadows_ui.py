"""«Generar sombras HD» in the launcher's Mejoras tab (HD-SHADOW-01/02): builds, on this PC, the HD shadows of every
level from the player's game files (newsnap/game_textures.py, newsnap/hdshadows.py), in a background thread. Its own
progress bar beside the button fills from left to right with the real part done (textures made of the total), with
the same text in the status bar. It can be stopped and goes on later from where it was."""

from .launcher_language import tr
import re
import threading
import tkinter as tk
from tkinter import ttk

from .paths import data_dir, runtime_dir

# «Sombras HD: 1234 de 9156 texturas · nivel LC_001_A» (game_textures.install) and «Sombras HD: 12/40 texturas»
COUNT = re.compile(r'(\d{1,9})\s*(?:de|/)\s*(\d{1,9})\s+texturas')


def parse_fraction(text):
    """(done, total) from a progress message of the build, or None when the message carries no count."""
    match = COUNT.search(str(text))
    if not match:
        return None
    done, total = int(match.group(1)), int(match.group(2))
    if total <= 0 or done < 0:
        return None
    return min(done, total), total


class Progress:
    """The numbers of one run: the bar never goes back while the same total is being counted."""

    def __init__(self):
        self.done, self.total = 0, 0

    def update(self, done, total):
        """Takes a new count; returns the fraction 0..1 to show."""
        if total != self.total:
            self.done, self.total = 0, total      # another phase with its own total starts from its own count
        self.done = max(self.done, min(done, total))
        return self.done / self.total if self.total > 0 else 0.0


class HdShadowsButton:
    label = 'Generar sombras HD'

    def __init__(self, launcher, parent):
        self.launcher, self.running, self.cancel = launcher, False, threading.Event()
        self.after = None
        self.progress = Progress()
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=(0, 4))
        self.button = ttk.Button(row, text=self.label, command=self.toggle)
        self.button.pack(side='left')
        from .progress_bar import SnapBar
        self.bar = SnapBar(row, width=260, height=14)
        self.bar.pack(side='left', padx=(14, 10))
        self.percent = tk.StringVar(value='')
        ttk.Label(row, textvariable=self.percent, style='Strong.TLabel', width=6).pack(side='left')
        self.state = tk.StringVar(value=self._summary())
        text = ttk.Label(parent, textvariable=self.state, style='Muted.TLabel', wraplength=640, justify='left')
        text.pack(anchor='w', fill='x', pady=(0, 10))
        text.bind('<Configure>', lambda event: text.configure(wraplength=max(200, event.width)))

    def folder(self):
        return runtime_dir(self.launcher.project) / 'hdshadows'

    def _summary(self):
        from .game_textures import complete
        folder = self.folder()
        made = sum(1 for p in folder.glob('*.dds') if len(p.stem) == 16) if folder.is_dir() else 0
        if complete(folder):
            return ''.join((tr('Listo: las sombras de todos los niveles están en HD ('), f'{made}', tr(' texturas).'),))
        if made:
            return ''.join((f'{made}', tr(' texturas en HD · faltan niveles: pulsa el botón para continuar.'),))
        return tr('Sin generar. Se hace una vez, con tu propio juego: unos 35 minutos y 6 GB.')

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

    def _work(self, report, progress=None):
        from .game_textures import install
        from .hdshadows import ensure_esrgan, generate
        from .launcher_settings import ProfileLock
        with ProfileLock(self.folder()):
            ensure_esrgan(report)
            project = self.launcher.project
            made, kept, failed = install(runtime_dir(project), data_dir(project), report=report, cancel=self.cancel)
            if not self.cancel.is_set():   # light maps saved while playing by versions before 0.9.15
                extra = {'progress': progress} if progress is not None else {}
                more = generate(self.folder(), report=report, cancel=self.cancel, **extra)
                made, failed = made + more[0], failed + more[2]
            if self.cancel.is_set():
                report(tr('Sombras HD: detenido. Lo generado se conserva; continúa al volver a pulsar el botón.'))
            else:
                report(f'Sombras HD: {made} texturas generadas' + (''.join((tr(', '), f'{failed}', tr(' sin procesar'),)) if failed else '')
                       + tr('. Se ven desde la próxima vez que abras el juego.'))

    # --- progress, on the Tk thread ---
    def show_message(self, text):
        """A message of the build: the status bar and this row's text; a count in it moves the bar."""
        self.launcher.status.set(text)
        self.state.set(text)
        count = parse_fraction(text)
        if count is not None:
            self.show_count(*count)

    def show_count(self, done, total):
        if not self.running:
            return
        fraction = self.progress.update(done, total)
        self.bar.stop()
        self.bar.configure(mode='determinate', maximum=1000, value=round(fraction * 1000))
        self.percent.set(f'{int(fraction * 100)} %')

    def show_activity(self):
        """Work without a count yet (reading the levels, the one-time download): the travelling segment."""
        self.progress = Progress()
        self.bar.configure(mode='indeterminate', value=0)
        self.bar.start()
        self.percent.set('')

    def reset_bar(self):
        self.progress = Progress()
        self.bar.stop()
        self.bar.configure(mode='determinate', value=0)
        self.percent.set('')

    def start(self, after=None):
        if self.running or self.launcher.busy:
            return False
        self.after = after
        self.running = True
        self.cancel.clear()
        self.button.configure(text='Detener')
        self.show_activity()
        root = self.launcher.root

        def report(text):
            root.after(0, self.show_message, text)

        def progress(done, total):   # hdshadows.generate's own counter, when it is called directly
            root.after(0, self.show_message, f'Sombras HD: {done}/{total} texturas')

        def work():
            try:
                self._work(report, progress)
            except Exception as error:   # shown to the player; the game is not affected
                report(''.join((f'{self.label}', tr(' sin completar: '), f'{error}',)))
            finally:
                root.after(0, self._done)

        threading.Thread(target=work, daemon=True).start()
        return True

    def _done(self):
        self.running = False
        self.button.configure(state='normal', text=self.label)
        self.reset_bar()
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
            return tr('Aún no hay texturas guardadas: activa «Guardar texturas para el pack» y juega.')
        made = sum(1 for p in folder.glob('*.dds') if len(p.stem) == 16)
        return f'{made} texturas en HD · {len(pending(folder))} por generar'

    def waiting(self):
        from .texpack_gen import pending
        return bool(pending(self.folder())) if (self.folder() / 'src').is_dir() else False

    def _work(self, report, progress=None):
        from .hdshadows import ensure_esrgan
        from .texpack_gen import generate
        ensure_esrgan(report)
        made, failed = generate(self.folder(), report=report, cancel=self.cancel)
        report(''.join((tr('Pack de texturas HD: '), f'{made}', tr(' texturas generadas'),))
               + (''.join((tr(', '), f'{failed}', tr(' sin procesar'),)) if failed else '') + tr('. Se usan al volver a cargarlas.'))
