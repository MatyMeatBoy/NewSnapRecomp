"""Manual release catalog and quiet notifications for newer stable releases."""
from pathlib import Path
import os
import queue
import subprocess
import sys
import tempfile
import threading
from tkinter import messagebox, simpledialog, ttk

from . import updater
from . import launcher_settings as settings
from . import github_auth
from .update_versions import newer
from .version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES


def runtime_update_status(root):
    """A public-launcher update cannot silently stand in for a private rebuild."""
    try:
        metadata = settings.validate_runtime_data(root)
    except (OSError, ValueError) as error:
        return False, f'Runtime privado pendiente de comprobar: {error}'
    if metadata is None:
        return False, 'Copia de desarrollo: la compatibilidad del runtime se comprueba al preparar la entrega.'
    version = metadata.get('runtime_version', 'sin versión')
    capabilities = metadata.get('capabilities', [])
    if (metadata.get('runtime_api') != RUNTIME_API or not isinstance(capabilities, list)
            or not all(isinstance(capability, str) for capability in capabilities)
            or not set(RUNTIME_CAPABILITIES).issubset(capabilities)):
        return False, (f'Runtime privado {version}: necesitas recompilarlo para incluir todas las mejoras '
                       'de este launcher. Tus archivos importados y partidas se conservan.')
    return True, f'Runtime privado {version}: interfaz y capacidades compatibles; archivo verificado.'


class UpdatePanel:
    def __init__(self, launcher, parent, automatic=True):
        self.launcher, self.root = launcher, launcher.root
        self.events = queue.Queue()
        self.release = None
        self.catalog = []
        self.working = False
        self.checking_stable = False
        self.notified_tag = None
        self.installing = False
        ttk.Label(parent, text='Actualizaciones', style='Title.TLabel').pack(anchor='w')
        try:
            version = (launcher.project / 'VERSION').read_text(encoding='ascii').strip()
        except OSError:
            version = VERSION
        ttk.Label(parent, text=f'Launcher instalado: {version}').pack(anchor='w', pady=(16, 8))
        self.status = ttk.Label(parent, text='Consulta las versiones publicadas en GitHub.', wraplength=760)
        self.status.pack(anchor='w', pady=8)
        ttk.Label(parent, text='Conserva tus datos del juego, perfiles y ajustes. También permite reinstalar '
                  'la misma versión para reparar los archivos del launcher. '
                  'La consulta manual incluye versiones alpha y prerelease.',
                  wraplength=760, style='Muted.TLabel').pack(anchor='w', pady=8)
        ttk.Label(parent, text='Al iniciar una expedición, el launcher comprueba si el juego necesita '
                  'reconstruirse localmente con tus datos y las herramientas verificadas. '
                  'Después prepara los shaders para tu GPU y controlador si hace falta.',
                  wraplength=760, style='Muted.TLabel').pack(anchor='w', pady=8)
        self.runtime_status = ttk.Label(parent, text='Comprobando el runtime privado…', wraplength=760)
        self.runtime_status.pack(anchor='w', pady=8)
        from .maintenance_ui import RuntimeMaintenance
        self.maintenance = RuntimeMaintenance(launcher, parent, self.runtime_status)
        def inspect_runtime():
            self.events.put(('runtime', runtime_update_status(launcher.project)[1]))
        threading.Thread(target=inspect_runtime, daemon=True).start()
        self.check = ttk.Button(parent, text='Consultar versiones publicadas', command=self.check_catalog)
        self.check.pack(anchor='w', pady=(15, 8))
        self.selector = ttk.Combobox(parent, values=(), state='disabled', width=52)
        self.selector.pack(anchor='w', pady=(0, 8))
        self.selector.bind('<<ComboboxSelected>>', self.select_release)
        self.install = ttk.Button(parent, text='Descargar e instalar / reparar',
                                  command=self.download, state='disabled')
        self.install.pack(anchor='w')
        from .progress_bar import page_bar
        self.bar = page_bar(parent, width=420, height=12)   # moves while GitHub is consulted or a version downloads
        if self.bar is not None:
            self.bar.pack(anchor='w', pady=(12, 0))
        access = ttk.Frame(parent)
        access.pack(anchor='w', pady=(18, 8))
        ttk.Button(access, text='Acceso a repositorio privado…', command=self.configure_access).pack(side='left')
        ttk.Button(access, text='Quitar credencial guardada', command=self.remove_access).pack(side='left', padx=10)
        ttk.Label(parent, text='Para el repositorio privado, usa un token de lectura con acceso a NewSnapRecomp. '
                  'Se guarda en el Administrador de credenciales de Windows. También se admite tu sesión '
                  'de GitHub CLI o GH_TOKEN / GITHUB_TOKEN; el token no se copia a GameData.',
                  wraplength=760, style='Muted.TLabel').pack(anchor='w')
        if not getattr(sys, 'frozen', False):
            ttk.Label(parent, text='En una copia de desarrollo puedes consultar versiones. '
                      'La instalación automática funciona desde NewSnapLauncher.exe.',
                      wraplength=760, style='Muted.TLabel').pack(anchor='w', pady=16)
        self.root.after(150, self.poll)
        if automatic and getattr(sys, 'frozen', False):
            self.root.after(1200, self.check_stable)

    def configure_access(self):
        if self.working:
            return
        token = simpledialog.askstring('Acceso a GitHub',
                    'Token de lectura con acceso al repositorio privado NewSnapRecomp:',
                    show='•', parent=self.root)
        if not token:
            return
        try:
            github_auth.save_token(token)
        except (OSError, ValueError) as error:
            self.status.configure(text=str(error))
        else:
            self.check_catalog()

    def remove_access(self):
        if self.working:
            return
        try:
            github_auth.remove_token()
        except (OSError, ValueError) as error:
            self.status.configure(text=str(error))
        else:
            self.status.configure(text='Credencial de Windows retirada. Las variables de entorno o la sesión de GitHub CLI siguen siendo independientes.')

    def _activity(self, running):
        """The consultation and the download report no byte counts: the bar shows activity, then rests empty."""
        bar = getattr(self, 'bar', None)
        if bar is None:
            return
        bar.stop()
        if running:
            bar.configure(mode='indeterminate', value=0)
            bar.start()
        else:
            bar.configure(mode='determinate', value=0)

    def check_stable(self):
        """Startup only: never select a release, install, or own launcher busy state."""
        if getattr(self, 'checking_stable', False):
            return
        self.checking_stable = True

        def work():
            try:
                self.events.put(('stable', updater.check_stable()))
            except Exception as error:
                self.events.put(('stable_error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def _selector_state(self, state):
        selector = getattr(self, 'selector', None)
        if selector is not None:
            selector.configure(state=state)

    def check_catalog(self):
        if self.working:
            return
        self.working = True
        self.check.configure(state='disabled')
        self.install.configure(state='disabled')
        self._selector_state('disabled')
        self.status.configure(text='Consultando versiones publicadas en GitHub…')
        self._activity(True)

        def work():
            try:
                self.events.put(('catalog', updater.list_releases()))
            except Exception as error:
                self.events.put(('error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def _show_catalog(self, releases):
        # GitHub's catalog is ordered newest first. Retain the actual validated
        # Release object for each selection, including prereleases and repairs.
        self.catalog = list(releases)
        self.release = self.catalog[0] if self.catalog else None
        selector = getattr(self, 'selector', None)
        if selector is not None:
            selector.configure(values=tuple(release.tag_name for release in self.catalog))
            if self.catalog:
                selector.current(0)
            else:
                selector.set('')
        self._selector_state('readonly' if self.catalog else 'disabled')
        self._selected_status()

    def _selected_status(self):
        self.status.configure(text=(f'Versión elegida: {self.release.tag_name} · lista para instalar o reparar'
                                    if self.release else 'No hay versiones publicadas con un launcher compatible.'))
        self.install.configure(state=('normal' if self.release and getattr(sys, 'frozen', False)
                                      and not self.working else 'disabled'))

    def select_release(self, event=None):
        if self.working:
            return
        index = self.selector.current()
        if 0 <= index < len(self.catalog):
            self.release = self.catalog[index]
            self._selected_status()

    def download(self):
        if self.working or not self.release or not getattr(sys, 'frozen', False):
            return
        if self.launcher.busy:
            self.status.configure(text='Cierra la expedición o espera a que termine la preparación antes de actualizar.')
            return
        try:
            settings.validate_runtime_data(self.launcher.project)
        except ValueError:
            # Public repair also works with absent/old private data. Preserve its
            # INI instead of making a native rebuild a prerequisite for updating.
            pass
        else:
            if not self.launcher.save_options():
                return
        release = self.release
        if not messagebox.askyesno('Instalar versión del launcher',
                f'Se descargará {release.tag_name} y se reiniciará el launcher para instalarla. '
                'Puedes usar esta opción aunque ya tengas esa versión. Tus datos y partidas se conservarán. '
                'El runtime privado del juego se conserva y puede necesitar una recompilación por separado. '
                'Si es incompatible, no se escribirán ajustes nuevos sobre él. '
                '¿Continuar?', parent=self.root):
            return
        self.working = True
        self.check.configure(state='disabled')
        self.install.configure(state='disabled')
        self._selector_state('disabled')
        self.installing = True
        self.launcher._set_busy(True)
        self.status.configure(text=f'Descargando y verificando {release.tag_name}…')
        self._activity(True)

        def work():
            try:
                scratch = Path(tempfile.mkdtemp(prefix='NewSnap-update-'))
                folder = updater.stage_update(release, scratch / 'download')
                self.events.put(('staged', folder))
            except Exception as error:
                self.events.put(('error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'runtime':
                    self.runtime_status.configure(text=value)
                    continue
                if kind in ('stable', 'stable_error'):
                    self.checking_stable = False
                    if kind == 'stable_error':
                        if not self.working and not getattr(self, 'catalog', []):
                            self.status.configure(text=f'No se pudo comprobar el aviso automático: {value}')
                        continue
                    if (value and newer(getattr(value, 'version', value.tag_name), VERSION)
                            and value.tag_name != getattr(self, 'notified_tag', None)):
                        self.notified_tag = value.tag_name
                        if not self.working and not getattr(self, 'catalog', []):
                            self.status.configure(text=f'Nueva versión estable disponible: {value.tag_name}')
                        notify = getattr(self.launcher, 'notify_update', None)
                        if callable(notify):
                            notify(value)
                    continue
                self.working = False
                self._activity(False)
                self.check.configure(state='normal')
                if kind == 'catalog':
                    self._show_catalog(value)
                elif kind == 'release':
                    self._show_catalog([value] if value else [])
                elif kind == 'error':
                    if self.installing:
                        self.launcher._set_busy(False)
                        self.installing = False
                    self.status.configure(text=f'No se completó la actualización: {value}')
                    if self.release and getattr(sys, 'frozen', False):
                        self.install.configure(state='normal')
                    self._selector_state('readonly' if getattr(self, 'catalog', []) else 'disabled')
                elif kind == 'staged':
                    try:
                        from .update_worker import create_job
                        job = create_job(value, self.launcher.project, os.getpid())
                        hidden = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                        environment = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT='1')
                        subprocess.Popen([str(value / 'NewSnapLauncher.exe'), '--apply-update', str(job)],
                                         cwd=value, env=environment, creationflags=hidden)
                    except Exception as error:
                        self.launcher._set_busy(False)
                        self.installing = False
                        self.status.configure(text=f'No se pudo iniciar la instalación: {error}')
                        self.install.configure(state='normal')
                        self._selector_state('readonly' if getattr(self, 'catalog', []) else 'disabled')
                    else:
                        self.root.destroy()
                        return
        except queue.Empty:
            pass
        self.root.after(150, self.poll)
