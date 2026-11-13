"""Stable release updates, downloaded before handing off to an external worker."""
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
from .version import RUNTIME_API, RUNTIME_CAPABILITIES


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
        self.working = False
        self.installing = False
        ttk.Label(parent, text='Actualizaciones', style='Title.TLabel').pack(anchor='w')
        try:
            version = (launcher.project / 'VERSION').read_text(encoding='ascii').strip()
        except OSError:
            version = '0.3 en desarrollo'
        ttk.Label(parent, text=f'Launcher instalado: {version}').pack(anchor='w', pady=(16, 8))
        self.status = ttk.Label(parent, text='Canal estable de GitHub', wraplength=760)
        self.status.pack(anchor='w', pady=8)
        ttk.Label(parent, text='Conserva tus datos del juego, perfiles y ajustes. También permite reinstalar '
                  'la misma versión estable para reparar los archivos del launcher.',
                  wraplength=760, style='Muted.TLabel').pack(anchor='w', pady=8)
        ttk.Label(parent, text='Tras actualizar, el launcher reconstruye el juego localmente si hace falta, '
                  'usando tus datos y las herramientas verificadas de esa versión. '
                  'Después prepara los shaders para tu GPU y controlador.',
                  wraplength=760, style='Muted.TLabel').pack(anchor='w', pady=8)
        self.runtime_status = ttk.Label(parent, text='Comprobando el runtime privado…', wraplength=760)
        self.runtime_status.pack(anchor='w', pady=8)
        from .maintenance_ui import RuntimeMaintenance
        self.maintenance = RuntimeMaintenance(launcher, parent, self.runtime_status)
        def inspect_runtime():
            self.events.put(('runtime', runtime_update_status(launcher.project)[1]))
        threading.Thread(target=inspect_runtime, daemon=True).start()
        self.check = ttk.Button(parent, text='Buscar última estable', command=self.check_stable)
        self.check.pack(anchor='w', pady=(15, 8))
        self.install = ttk.Button(parent, text='Descargar e instalar / reparar',
                                  command=self.download, state='disabled')
        self.install.pack(anchor='w')
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
            self.check_stable()

    def remove_access(self):
        if self.working:
            return
        try:
            github_auth.remove_token()
        except (OSError, ValueError) as error:
            self.status.configure(text=str(error))
        else:
            self.status.configure(text='Credencial de Windows retirada. Las variables de entorno o la sesión de GitHub CLI siguen siendo independientes.')

    def check_stable(self):
        if self.working:
            return
        self.working = True
        self.check.configure(state='disabled')
        self.install.configure(state='disabled')
        self.status.configure(text='Consultando versiones estables en GitHub…')

        def work():
            try:
                self.events.put(('release', updater.check_stable()))
            except Exception as error:
                self.events.put(('error', str(error)))
        threading.Thread(target=work, daemon=True).start()

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
        if not messagebox.askyesno('Instalar versión estable',
                f'Se descargará {self.release.tag_name} y se reiniciará el launcher para instalarla. '
                'Puedes usar esta opción aunque ya tengas esa versión. Tus datos y partidas se conservarán. '
                'El runtime privado del juego se conserva y puede necesitar una recompilación por separado. '
                'Si es incompatible, no se escribirán ajustes nuevos sobre él. '
                '¿Continuar?', parent=self.root):
            return
        self.working = True
        self.check.configure(state='disabled')
        self.install.configure(state='disabled')
        self.installing = True
        self.launcher._set_busy(True)
        self.status.configure(text='Descargando y verificando la versión estable…')
        release = self.release

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
                self.working = False
                self.check.configure(state='normal')
                if kind == 'release':
                    self.release = value
                    self.status.configure(text=f'Última estable: {value.tag_name} · lista para instalar o reparar'
                                          if value else 'Todavía no hay una versión estable publicada. '
                                          'Las versiones alpha y prerelease no se instalan automáticamente.')
                    if value and getattr(sys, 'frozen', False):
                        self.install.configure(state='normal')
                elif kind == 'error':
                    if self.installing:
                        self.launcher._set_busy(False)
                        self.installing = False
                    self.status.configure(text=f'No se completó la actualización: {value}')
                    if self.release and getattr(sys, 'frozen', False):
                        self.install.configure(state='normal')
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
                    else:
                        self.root.destroy()
                        return
        except queue.Empty:
            pass
        self.root.after(150, self.poll)
