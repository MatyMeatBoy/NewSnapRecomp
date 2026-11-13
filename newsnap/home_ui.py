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
        ttk.Label(parent,text='Tu próxima expedición',style='Title.TLabel').pack(anchor='w',pady=(0,12))
        self.version=ttk.Label(parent,text='',style='Muted.TLabel');self.version.pack(anchor='w',pady=(0,14))
        card=ttk.LabelFrame(parent,text='Datos del juego',padding=16);card.pack(fill='x',pady=(0,12))
        self.data_state=ttk.Label(card,text='Sin datos cargados',font=('Segoe UI',13,'bold'))
        self.data_state.pack(anchor='w')
        self.location=ttk.Label(card,text='',wraplength=760,style='Muted.TLabel');self.location.pack(anchor='w',pady=(6,12))
        actions=ttk.Frame(card);actions.pack(anchor='w')
        self.load_button=ttk.Button(actions,text='Cargar GameData…',command=self.choose_data)
        self.load_button.pack(side='left')
        self.verify_button=ttk.Button(actions,text='Verificar datos',command=self.verify)
        self.verify_button.pack(side='left',padx=8)
        self.cancel_button=ttk.Button(actions,text='Cancelar',command=self.cancel.set,state='disabled')
        self.cancel_button.pack(side='left')
        profile=ttk.Frame(parent);profile.pack(fill='x',pady=(0,10))
        ttk.Label(profile,text='Perfil activo',font=('Segoe UI',11,'bold')).pack(anchor='w')
        launcher.profile_text=tk.StringVar(value=str(launcher.profile))
        launcher.profile_label=ttk.Label(profile,textvariable=launcher.profile_text,wraplength=760,style='Muted.TLabel')
        launcher.profile_label.pack(anchor='w',pady=4)
        launcher.profile_button=ttk.Button(profile,text='Elegir perfil…',command=launcher.choose_profile)
        launcher.profile_button.pack(anchor='w',pady=4)
        launcher.prepare=tk.BooleanVar(value=True)
        ttk.Checkbutton(parent,text='Preparar gráficos antes de jugar',variable=launcher.prepare).pack(anchor='w',pady=(6,4))
        ttk.Label(parent,text='La verificación y la preparación necesarias se muestran aquí, antes de abrir el juego.',
                  wraplength=760,style='Muted.TLabel').pack(anchor='w')
        launcher.play_button=ttk.Button(footer,text='Iniciar expedición  →',style='Accent.TButton',command=launcher.launch)
        launcher.play_button.pack(side='right')
        self.update_notice=ttk.Button(self.notice_slot,text='',command=lambda:launcher.tabs.select(launcher.update_tab))
        self.credits=ttk.Button(footer,text='Créditos y licencias',command=launcher.show_credits)
        self.credits.pack(side='left')
        self.refresh();launcher.root.after(150,self.poll)

    def refresh(self):
        value=home_state.state(self.launcher.project)
        self.location.configure(text=value['directory'])
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
        self.verify_button.configure(state='disabled' if busy else 'normal')
        self.cancel_button.configure(state='normal' if self.verifying else 'disabled')

    def choose_data(self):
        if self.launcher.busy:return
        chosen=filedialog.askdirectory(parent=self.launcher.root,title='Elige tu carpeta GameData',mustexist=True)
        if not chosen:return
        try:
            selected=select_data_dir(self.launcher.project,chosen)
            self.launcher.ini=runtime_dir(self.launcher.project)/'astralchain.ini'
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
                self.verifying=False;self.launcher._set_busy(False);self.refresh()
                self.launcher.status.set('Datos del juego verificados.' if kind=='verified' else value)
                if kind=='verified' and self.resume:self.launcher.root.after(50,self.launcher.launch)
                self.resume=False
        except queue.Empty:pass
        self.launcher.root.after(150,self.poll)
