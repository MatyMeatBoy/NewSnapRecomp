"""Home keeps loading, verification and launch in one explicit flow."""
from datetime import datetime
import queue
import threading
import tkinter as tk
from tkinter import filedialog,ttk

from . import home_state,launcher_settings as settings
from .paths import data_dir,runtime_dir,select_data_dir
from .version import VERSION


class HomePanel:
    def __init__(self,launcher,parent):
        self.launcher=launcher
        self.events=queue.Queue();self.cancel=threading.Event();self.resume=False
        self.verifying=False
        footer=ttk.Frame(parent,padding=(0,12,0,0));footer.pack(side='bottom',fill='x')
        self.notice_slot=ttk.Frame(parent);self.notice_slot.pack(fill='x')
        content=ttk.Frame(parent);content.pack(fill='both',expand=True)
        from .hero_ui import SnapCover
        self.cover=SnapCover(content,launcher);self.cover.pack(side='left',anchor='n',padx=(0,22))
        body=ttk.Frame(content);body.pack(side='left',fill='both',expand=True)
        ttk.Label(body,text='Tu próxima expedición',style='Title.TLabel').pack(anchor='w',pady=(0,5))
        self.version=ttk.Label(body,text='',style='Muted.TLabel',wraplength=530);self.version.pack(anchor='w',pady=(0,6))
        card=ttk.LabelFrame(body,text='Datos del juego',padding=10);card.pack(fill='x',pady=(0,6))
        self.data_state=ttk.Label(card,text='Sin datos cargados',font=('Segoe UI',13,'bold'))
        self.data_state.pack(anchor='w')
        self.location=ttk.Label(card,text='',wraplength=510,style='Muted.TLabel',font=('Segoe UI',9));self.location.pack(anchor='w',pady=(4,6))
        from .tooltip import Tooltip
        self.location_tooltip=Tooltip(self.location,'',wraplength=600)
        actions=ttk.Frame(card);actions.pack(anchor='w')
        self.load_button=ttk.Button(actions,text='Cargar GameData…',command=self.choose_data)
        self.load_button.pack(side='left')
        self.import_button=ttk.Button(actions,text='Importar NSP/XCI/NSZ…',command=self.import_dump)
        self.import_button.pack(side='left',padx=(8,0))
        self.verify_button=ttk.Button(actions,text='Verificar datos',command=self.verify)
        self.verify_button.pack(side='left',padx=8)
        self.cancel_button=ttk.Button(actions,text='Cancelar',command=self.cancel.set,state='disabled')
        self.cancel_button.pack(side='left')
        launcher.prepare=tk.BooleanVar(value=True)
        prepare = ttk.Checkbutton(body,text='Precompilar shaders disponibles',variable=launcher.prepare)
        prepare.pack(anchor='w',pady=(6,4))
        from .tooltip import Tooltip
        Tooltip(prepare, 'Prepara los shaders y pipelines registrados para esta GPU antes de jugar. Si es el primer inicio y aún no hay registros, el juego arranca y los compila durante la expedición. Un cambio de GPU/controlador/runtime puede requerir preparar de nuevo la caché.')
        from .progress_ui import PreparationPanel
        self.progress=PreparationPanel(body);self.progress.pack(fill='x',pady=(6,0))
        launcher.play_button=ttk.Button(footer,text='Iniciar expedición  →',style='Accent.TButton',command=launcher.launch)
        launcher.play_button.pack(side='right')
        self.update_notice=ttk.Button(self.notice_slot,text='',command=lambda:launcher.tabs.select(launcher.update_tab))
        self.credits=ttk.Button(footer,text='Créditos y licencias',command=launcher.show_credits)
        self.credits.pack(side='left')
        self.refresh();launcher.root.after(150,self.poll)

    def show_preparation_note(self,message):
        self.progress.set_note(message)

    def refresh(self):
        value=home_state.state(self.launcher.project)
        location=value['directory']
        self.location.configure(text=location if len(location)<=90 else location[:26]+'…'+location[-62:])
        self.location_tooltip.text=location
        runtime=value['runtime_version'] or 'por preparar'
        self.version.configure(text=f'Launcher {VERSION}  ·  Juego 2.0.1  ·  Runtime {runtime}')
        if value['verified']:
            date=datetime.fromtimestamp(value['verified_at']).strftime('%d/%m %H:%M')
            text='Datos verificados · '+date
        elif value['loaded']:text='Datos cargados · verificación pendiente'
        else:text='Carga tu carpeta GameData para comenzar'
        self.data_state.configure(text=text)
        self.verify_button.configure(state='normal' if value['loaded'] and not self.launcher.busy else 'disabled')
        return value

    def set_busy(self,busy):
        self.load_button.configure(state='disabled' if busy else 'normal')
        self.import_button.configure(state='disabled' if busy else 'normal')
        self.verify_button.configure(state='disabled' if busy else 'normal')
        self.cancel_button.configure(state='normal' if self.verifying else 'disabled')
        if busy and not self.progress.active:self.progress.begin('Preparando el inicio…')
        elif not busy:self.progress.stop()

    def choose_data(self):
        if self.launcher.busy:return
        chosen=filedialog.askdirectory(parent=self.launcher.root,title='Elige tu carpeta GameData',mustexist=True)
        if not chosen:return
        HomePanel._use_data(self,chosen)

    def import_dump(self):
        """Import the base game (NSP, NSZ, XCI or XCZ), the 2.0.1 update (NSP or NSZ) and prod.keys into GameData.

        Runs `newsnap import` with the build kit's Python (cryptography, the pinned NCA reader) and the
        bundled hactool for the update RomFS; the owner's files are only read."""
        if self.launcher.busy:return
        ask=lambda title,types:filedialog.askopenfilename(parent=self.launcher.root,title=title,filetypes=types)
        base=ask('Juego base de New Pokémon Snap',[('Volcado del juego','*.nsp *.nsz *.xci *.xcz'),('Todos','*.*')])
        if not base:return
        update=ask('Actualización 2.0.1',[('Actualización','*.nsp *.nsz'),('Todos','*.*')])
        if not update:return
        keys=ask('Tus claves de consola (prod.keys)',[('Claves','*.keys'),('Todos','*.*')])
        if not keys:return
        from pathlib import Path
        from .upstream import ROOT
        hactool=ROOT/'tools/hactool.exe'
        if not hactool.is_file():hactool=ROOT/'toolchain/hactool/hactool.exe'
        if not hactool.is_file():
            self.launcher.status.set('Falta hactool.exe junto al launcher: reinstala el paquete.');return
        work=Path(self.launcher.project)/'GameData-import'
        self.verifying=True;self.cancel.clear();self.launcher._set_busy(True)
        self.progress.report('Importando tu juego (ExeFS y RomFS)… puede tardar varios minutos')
        def job():
            try:
                from .build_kit import ensure_build_kit
                from .maintenance import run_build_command
                kit=Path(ensure_build_kit(self.launcher.project,cancel_event=self.cancel))
                command=[kit/'python/python.exe','-B','-E','-s','-m','newsnap','import','--base',base,'--update',update,
                         '--keys',keys,'--work',work,'--hactool',hactool]
                run_build_command(command,kit/'source',Path(self.launcher.project)/'logs/import.log',self.cancel)
                self.events.put(('imported',str(work/'updated')))
            except Exception as error:self.events.put(('error','Importación sin completar: '+str(error)))
        threading.Thread(target=job,daemon=True).start()

    def _use_data(self,chosen):
        try:
            selected=select_data_dir(self.launcher.project,chosen)
            self.launcher.ini=runtime_dir(self.launcher.project)/'newsnap.ini'
            self.launcher.profile=settings.load_profile(self.launcher.project)
            self.launcher.profile_text.set(str(self.launcher.profile))
            self.launcher.baseline=settings.load_settings(self.launcher.ini)
            self.launcher._set_option_values(self.launcher.baseline)
            self.launcher._album_loaded=False
            self.launcher.status.set('GameData cargado. Verifica los datos o inicia la expedición.')
        except (OSError,ValueError) as error:self.launcher.status.set(str(error))
        self.refresh()

    def verify(self,*,resume_game=False):
        if self.launcher.busy:return False
        if not self.refresh()['loaded']:
            self.choose_data();return False
        self.verifying=True;self.resume=resume_game;self.cancel.clear()
        self.launcher._set_busy(True)
        self.launcher.status.set('Verificando ExeFS y RomFS de tu juego…')
        self.progress.report('Verificando ExeFS y RomFS de tu juego…')
        def work():
            try:
                with settings.ProfileLock(self.launcher.profile):value=home_state.verify(self.launcher.project,self.cancel)
                self.events.put(('verified',value))
            except Exception as error:self.events.put(('error',str(error)))
        threading.Thread(target=work,daemon=True).start();return True

    def notify_update(self,release):
        self.update_notice.configure(text=f'Nueva estable disponible: {release.tag_name} · ver actualización')
        self.update_notice.pack(anchor='w',pady=(0,8))

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                self.verifying=False;self.launcher._set_busy(False)
                if kind=='imported':
                    self._use_data(value);self.progress.finish('Juego importado');continue
                self.refresh()
                self.launcher.status.set('Datos del juego verificados.' if kind=='verified' else value)
                self.progress.finish('Datos del juego verificados' if kind=='verified' else 'Verificación sin completar',error=kind!='verified')
                if kind=='verified' and self.resume:self.launcher.root.after(50,self.launcher.launch)
                self.resume=False
        except queue.Empty:pass
        self.launcher.root.after(150,self.poll)
