"""Opt-in complete-profile backups and restore-to-new-profile launcher panel."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk
import uuid

from . import backup_settings, launcher_settings as settings
from . import controller_dialogs as dialogs
from . import controller_file_picker as file_picker
from .launcher_language import tr

CONSENT = ('¿Activar las copias completas del perfil en esta carpeta?\n\nIncluyen las partidas confirmadas, las fotos y la identidad de la cuenta, también los archivos de más de 64 MB. Se conservan las últimas tres copias de cada perfil.\n\nSi la carpeta está sincronizada, tu proveedor de nube gestiona las subidas y el almacenamiento. RecompLauncher no sube estas copias completas del perfil. Puedes desactivar las copias futuras sin borrar las existentes.')


class BackupPanel:
    def __init__(self, launcher, parent):
        self.launcher = launcher
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.running = self.closed = False
        self.after_id = None
        self.frame = frame = ttk.LabelFrame(parent, text=tr('Copias completas del perfil'), padding=12)
        frame.pack(fill='x', pady=(12, 8))
        self.folder = tk.StringVar(value='')
        self.message = tk.StringVar(value='')
        ttk.Label(frame, textvariable=self.folder, wraplength=630).pack(anchor='w', fill='x')
        ttk.Label(frame, text=tr('Opcional: elige una carpeta local o sincronizada. Se incluyen los archivos grandes de partidas y fotos; se conservan tres copias completas por perfil.'),
                  wraplength=630, style='Muted.TLabel').pack(anchor='w', fill='x', pady=6)
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x')
        self.buttons = []
        for label, command in (('Elegir carpeta de copias', self.choose_folder),
                               ('Desactivar copias', self.disable),
                               ('Crear copia ahora', self.backup_now),
                               ('Restaurar copia', self.restore)):
            button = ttk.Button(buttons, text=tr(label), command=command)
            button.pack(side='left', padx=(0, 6), pady=3)
            self.buttons.append(button)
        self.cancel_button = ttk.Button(frame, text=tr('Cancelar copia/restauración'), command=self.cancel.set,
                                        state='disabled')
        self.cancel_button.pack(anchor='w', pady=(6, 0))
        ttk.Label(frame, textvariable=self.message, wraplength=630,
                  style='Muted.TLabel').pack(anchor='w', fill='x', pady=(6, 0))
        frame.bind('<Destroy>', self._destroyed, add='+')
        self.refresh()
        self._schedule()

    def _available(self):
        return not self.closed and not self.running and not getattr(self.launcher, 'busy', False)

    def _schedule(self):
        if self.closed:
            return
        try:
            self.after_id = self.launcher.root.after(100, self._poll)
        except (tk.TclError, RuntimeError):
            self.closed = True
            self.cancel.set()

    def _destroyed(self, event):
        if event.widget is not self.frame:
            return
        self.closed = True
        self.cancel.set()
        if self.after_id is not None:
            try:
                self.launcher.root.after_cancel(self.after_id)
            except (tk.TclError, RuntimeError):
                pass
        if self.running:
            try:
                self.launcher._set_busy(False)
            except (tk.TclError, RuntimeError):
                pass

    def refresh(self):
        try:
            config = backup_settings.load_backup_settings(self.launcher.project)
            self.folder.set(tr('Carpeta de copias: ') + config['destination'] if config else tr('Las copias completas del perfil están desactivadas.'))
        except (OSError, ValueError) as error:
            self.folder.set(tr('Revisa los ajustes de las copias: ') + str(error))

    def _error(self, error):
        self.message.set(str(error))
        dialogs.showerror(tr('Copia/restauración del perfil'), str(error), parent=self.launcher.root)

    def choose_folder(self):
        if not self._available():
            return
        selected = file_picker.askdirectory(parent=self.launcher.root, title=tr('Elige una carpeta de copias local o sincronizada'))
        if not selected or not self._available():
            return
        try:
            backup_settings.validate_destination(selected, self.launcher.profile, probe=True)
            if not dialogs.askyesno(tr('Activar copias completas del perfil'), tr(CONSENT) + '\n\n' + selected,
                                    parent=self.launcher.root):
                return
            if not self._available():
                return
            backup_settings.save_backup_settings(self.launcher.project, selected, profile=self.launcher.profile)
            self.refresh()
            self.message.set(tr('Activado: se crea una copia completa después de cada sesión de juego.'))
        except (OSError, ValueError) as error:
            self._error(error)

    def disable(self):
        if not self._available():
            return
        try:
            backup_settings.disable_backup_settings(self.launcher.project)
            self.refresh()
            self.message.set(tr('Copias futuras desactivadas. Se conservan los archivos existentes.'))
        except (OSError, ValueError) as error:
            self._error(error)

    def backup_now(self):
        if not self._available():
            return
        try:
            config = backup_settings.load_backup_settings(self.launcher.project)
            if config is None:
                self.choose_folder()
                config = backup_settings.load_backup_settings(self.launcher.project)
            if config is None or not self._available():
                return
            profile = Path(self.launcher.profile)
            destination = backup_settings.validate_destination(config['destination'], profile)
            def work(report, cancel):
                from .profile_backup import backup_profile
                with settings.ProfileLock(profile):
                    return backup_profile(profile, destination, keep=config['keep'], cancel=cancel, report=report)
            self._start('backup', work)
        except (OSError, ValueError) as error:
            self._error(error)

    def restore(self):
        if not self._available():
            return
        selected = file_picker.askopenfilename(parent=self.launcher.root, title=tr('Elige una copia completa del perfil'),
                                               filetypes=((tr('Copias del perfil'), '*.zip'),))
        if not selected or not self._available():
            return
        parent = file_picker.askdirectory(parent=self.launcher.root, title=tr('Elige dónde crear el perfil restaurado'),
                                           initialdir=str(Path(self.launcher.profile).parent))
        if not parent or not self._available():
            return
        try:
            profile = Path(self.launcher.profile)
            parent = backup_settings.validate_destination(parent, profile, probe=True)
            target = parent / ('NewSnap-restored-' + uuid.uuid4().hex)
            text = (tr('¿Restaurar en un perfil nuevo y seleccionarlo después de verificarlo? Se conservará tu perfil actual.') + '\n\n' + str(target))
            if not dialogs.askyesno(tr('Restaurar perfil completo'), text, parent=self.launcher.root):
                return
            if not self._available():
                return
            def work(report, cancel):
                from .profile_backup import restore_profile
                with settings.ProfileLock(profile):
                    report(tr('Verificando y restaurando el perfil completo…'))
                    return restore_profile(selected, target, cancel=cancel)
            self._start('restore', work)
        except (OSError, ValueError) as error:
            self._error(error)

    def _start(self, kind, work):
        if not self._available():
            return
        self.running = True
        self.cancel.clear()
        self.launcher._set_busy(True)
        self.message.set(tr('Creando una copia completa del perfil…') if kind == 'backup' else tr('Restaurando el perfil completo…'))
        self._sync_buttons()
        def report(text):
            self.events.put(('progress', str(text)))
        def worker():
            try:
                result = work(report, self.cancel)
                self.events.put(('done', kind, result, None))
            except Exception as error:
                self.events.put(('done', kind, None, str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def _select_restored(self, profile):
        # Only called on Tk's thread after extraction and hash checks succeeded.
        app = self.launcher
        settings.save_profile(app.project, profile)
        app.profile = Path(profile)
        label = getattr(app, 'profile_text', None)
        if label is not None:
            label.set(str(profile))
        app.photos, app.thumbnails, app.page = [], [], 0
        app._album_loaded = False
        app.album_generation = getattr(app, 'album_generation', 0) + 1
        preview = getattr(app, 'preview', None)
        if preview is not None and preview.winfo_exists():
            preview.destroy()
        for name in ('reload_options', 'draw_page', '_tab_changed'):
            callback = getattr(app, name, None)
            if callable(callback):
                callback()

    def _complete(self, kind, result, error):
        self.running = False
        self.launcher._set_busy(False)
        self._sync_buttons()
        if error:
            self._error(error)
            return
        try:
            if kind == 'restore':
                self._select_restored(result)
                self.message.set(tr('Perfil nuevo restaurado y seleccionado: ') + str(result))
            else:
                self.message.set(tr('Copia completa del perfil guardada: ') + str(result))
        except (OSError, ValueError) as failure:
            self._error(tr('Se conservó el perfil restaurado, pero no se pudo seleccionar: ') + str(failure))

    def _sync_buttons(self):
        enabled = self._available()
        for button in self.buttons:
            button.configure(state='normal' if enabled else 'disabled')
        self.cancel_button.configure(state='normal' if self.running else 'disabled')

    def _poll(self):
        self.after_id = None
        if self.closed:
            return
        try:
            for _ in range(100):
                try:
                    event = self.events.get_nowait()
                except queue.Empty:
                    break
                if event[0] == 'progress':
                    self.message.set(event[1])
                else:
                    self._complete(*event[1:])
            self._sync_buttons()
        except tk.TclError:
            self.closed = True
            self.cancel.set()
        self._schedule()
