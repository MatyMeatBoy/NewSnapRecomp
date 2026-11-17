"""Home keeps loading, verification and launch in one explicit flow."""

from .launcher_language import tr
from datetime import datetime
import queue
import threading
import tkinter as tk
from tkinter import filedialog,ttk

from . import fonts,home_state,launcher_settings as settings
from .paths import data_dir,runtime_dir,select_data_dir
from .version import VERSION


class HomePanel:
    def __init__(self,launcher,parent):
        self.launcher=launcher
        self.events=queue.Queue();self.cancel=threading.Event();self.resume=False
        self.verifying=False;self.checking=False;self.last_state={'loaded':False,'verified':False}
        footer=ttk.Frame(parent,padding=(0,12,0,0));footer.pack(side='bottom',fill='x')
        self.notice_slot=ttk.Frame(parent);self.notice_slot.pack(fill='x')
        content=ttk.Frame(parent);content.pack(fill='both',expand=True)
        from .hero_ui import SnapCover
        self.cover=SnapCover(content,launcher);self.cover.pack(side='left',anchor='n',padx=(0,24))
        body=ttk.Frame(content);body.pack(side='left',fill='both',expand=True)
        ttk.Label(body,text=tr('Tu próxima expedición'),style='Title.TLabel').pack(anchor='w',pady=(0,2))
        self.version=ttk.Label(body,text='',style='Caption.TLabel',wraplength=530);self.version.pack(anchor='w',pady=(0,8))
        self.chips=ttk.Frame(body);self.chips.pack(anchor='w',pady=(0,8))
        card=ttk.LabelFrame(body,text=tr('Datos del juego'));card.pack(fill='x',pady=(0,4))
        self.data_state=ttk.Label(card,text=tr('Sin datos cargados'),style='Heading.TLabel')
        self.data_state.pack(anchor='w')
        self.location=ttk.Label(card,text='',wraplength=400,style='Caption.TLabel');self.location.pack(anchor='w',pady=(2,8))
        from .tooltip import Tooltip
        self.location_tooltip=Tooltip(self.location,'',wraplength=600)
        ttk.Label(card, text=tr('Carga una carpeta GameData ya importada o importa tu propio volcado. Los archivos existentes se usan donde están.'), wraplength=430, style='Caption.TLabel').pack(anchor='w', pady=(0,8))
        actions=ttk.Frame(card);actions.pack(anchor='w')
        self.load_button=ttk.Button(actions,text=tr('Cargar GameData…'),command=self.choose_data)
        self.load_button.grid(row=0,column=0,sticky='w',padx=(0,8),pady=(0,4))
        self.import_button=ttk.Button(actions,text=tr('Importar NSP/XCI/NSZ…'),command=self.import_dump)
        self.import_button.grid(row=0,column=1,sticky='w',pady=(0,4))
        self.verify_button=ttk.Button(actions,text=tr('Verificar datos'),command=self.verify)
        self.verify_button.grid(row=1,column=0,sticky='w',padx=(0,8))
        self.cancel_button=ttk.Button(actions,text=tr('Cancelar'),command=self.cancel.set,state='disabled')
        self.cancel_button.grid(row=1,column=1,sticky='w')
        launcher.prepare=tk.BooleanVar(value=True)
        prepare = ttk.Checkbutton(body,text=tr('Precompilar shaders disponibles'),variable=launcher.prepare)
        prepare.pack(anchor='w',pady=(4,2))
        from .tooltip import Tooltip
        Tooltip(prepare, tr('Prepara los shaders y pipelines registrados para esta GPU antes de jugar. Si es el primer inicio y aún no hay registros, el juego arranca y los compila durante la expedición. Un cambio de GPU/controlador/runtime puede requerir preparar de nuevo la caché.'))
        from .progress_ui import PreparationPanel
        self.progress=PreparationPanel(body);self.progress.pack(fill='x',pady=(2,0))
        self.update_notice=ttk.Button(self.notice_slot,text='',command=lambda:launcher.tabs.select(launcher.update_tab))
        from .shortcuts_ui import ShortcutButtons
        self.shortcuts=ShortcutButtons(launcher,footer)
        self.credits=ttk.Button(footer,text=tr('Créditos y licencias'),command=launcher.show_credits)
        self.credits.pack(side='left')
        self.refresh();launcher.root.after(150,self.poll)

    def show_preparation_note(self,message):
        self.progress.set_note(message)

    def refresh(self):
        value=home_state.state(self.launcher.project)
        location=value['directory']
        self.location.configure(text=location if len(location)<=90 else location[:26]+'…'+location[-62:])
        self.location_tooltip.text=location
        runtime=value['runtime_version'] or tr('por preparar')
        self.version.configure(text=''.join((tr('Launcher '), f'{VERSION}', tr('  ·  Juego 2.0.1  ·  Runtime '), f'{runtime}',)))
        if value['verified']:
            date=datetime.fromtimestamp(value['verified_at']).strftime('%d/%m %H:%M')
            text=tr('Datos verificados · ')+date
        elif value['loaded']:text=tr('Datos cargados · verificación pendiente')
        else:text=tr('Carga tu carpeta GameData para comenzar')
        self.data_state.configure(text=text)
        self._chips(value)
        if value['loaded']:
            self.load_button.configure(text=tr('Cambiar carpeta…'))
            self.load_button.grid()
        else:
            self.load_button.grid_remove()
        self.verify_button.configure(state='normal' if value['loaded'] and not self.launcher.busy else 'disabled')
        self.runtime_state(value)
        self.last_state=value;self.sync_action()
        return value

    def runtime_state(self, value):
        """Use the launcher's real integrity check, asynchronously, before offering Play."""
        value['needs_build'] = False
        value['runtime_checking'] = False
        if not (value['loaded'] and value['verified'] and settings.is_release_layout(self.launcher.project)):
            return
        from pathlib import Path
        from .maintenance import RUNTIME_FILES, TRANSACTION, assess_runtime
        directory = Path(value['directory'])
        paths = [directory/name for name in sorted(set(RUNTIME_FILES) | {'newsnap-game.json', TRANSACTION})]
        paths.append(Path(self.launcher.project)/'MANIFEST.json')
        def stamp(path):
            try:
                st = path.stat()
                return (st.st_size, st.st_mtime_ns)
            except OSError:
                return None
        key = (str(directory), tuple(stamp(path) for path in paths))
        cached = getattr(self, '_runtime_assessment', None)
        if cached is not None and cached[0] == key:
            value['needs_build'] = cached[1]['needs_rebuild']
            return
        value['runtime_checking'] = True
        if getattr(self, '_runtime_pending_key', None) == key:
            return
        self._runtime_pending_key = key
        root = self.launcher.project
        def check():
            try:
                result = assess_runtime(root)
            except Exception as error:
                result = {'needs_rebuild': True, 'reason': str(error)}
            self.events.put(('runtime_assessed', (key, result)))
        threading.Thread(target=check, daemon=True).start()

    def sync_action(self):
        """Keep the sidebar's single primary action in sync with data and runtime integrity."""
        from .play_action import play_action
        launcher=self.launcher
        action=play_action(self.last_state,busy=bool(getattr(launcher,'busy',False)),verifying=self.checking)
        self.action=action
        sidebar=getattr(launcher,'sidebar',None)
        if sidebar is not None and hasattr(sidebar,'set_action'):
            sidebar.set_action(action['label'],action['kind'],action['enabled'])
        return action

    def _chips(self,value):
        from .sidebar_ui import chip
        for widget in self.chips.winfo_children():widget.destroy()
        items=[(tr('Datos verificados'),'ok') if value['verified'] else (tr('Datos cargados · sin verificar'),'warn') if value['loaded']
               else (tr('Sin datos del juego'),'warn')]
        runtime=value['runtime_version']
        items.append((f'Runtime {runtime}','ok') if runtime else (tr('Runtime por preparar'),'neutral'))
        if value['loaded']:
            try:
                prepared=(runtime_dir(self.launcher.project)/'shader-prepared.bin').is_file() and                          not settings.shader_preparation_required(self.launcher.project)
            except OSError:prepared=False
            items.append((tr('Shaders listos'),'ok') if prepared else (tr('Shaders por preparar'),'neutral'))
        for text,kind in items:chip(self.chips,text,kind).pack(side='left',padx=(0,6))

    def set_busy(self,busy):
        self.load_button.configure(state='disabled' if busy else 'normal')
        self.import_button.configure(state='disabled' if busy else 'normal')
        self.verify_button.configure(state='disabled' if busy else 'normal')
        self.cancel_button.configure(state='normal' if self.verifying else 'disabled')
        if busy and not self.progress.active:self.progress.begin(tr('Preparando el inicio…'))
        elif not busy:self.progress.stop()
        self.sync_action()

    def choose_data(self):
        if self.launcher.busy:return
        chosen=filedialog.askdirectory(parent=self.launcher.root,title=tr('Elige tu carpeta GameData'),mustexist=True)
        if not chosen:return
        HomePanel._use_data(self,chosen)

    def import_dump(self):
        """Import the base game (NSP, NSZ, XCI or XCZ), the 2.0.1 update (NSP or NSZ) and prod.keys into GameData.

        Runs `newsnap import` with the build kit's Python (cryptography, the pinned NCA reader) and the
        bundled hactool for the update RomFS; the owner's files are only read."""
        if self.launcher.busy:return
        ask=lambda title,types:filedialog.askopenfilename(parent=self.launcher.root,title=title,filetypes=types)
        base=ask(tr('Juego base de New Pokémon Snap'),[(tr('Volcado del juego'),'*.nsp *.nsz *.xci *.xcz'),(tr('Todos'),'*.*')])
        if not base:return
        update=ask(tr('Actualización 2.0.1'),[(tr('Actualización'),'*.nsp *.nsz'),(tr('Todos'),'*.*')])
        if not update:return
        keys=ask(tr('Tus claves de consola (prod.keys)'),[(tr('Claves'),'*.keys'),(tr('Todos'),'*.*')])
        if not keys:return
        from pathlib import Path
        from .upstream import ROOT
        hactool=ROOT/'tools/hactool.exe'
        if not hactool.is_file():hactool=ROOT/'toolchain/hactool/hactool.exe'
        if not hactool.is_file():
            self.launcher.status.set(tr('Falta hactool.exe junto al launcher: reinstala el paquete.'));return
        work=Path(self.launcher.project)/'GameData-import'
        from tkinter import messagebox
        if not messagebox.askokcancel(tr('Confirmar importación'), tr('Los archivos importados se guardarán en: ')+str((work/'updated').resolve()), parent=self.launcher.root):return
        self.verifying=True;self.cancel.clear();self.launcher._set_busy(True)
        self.progress.report(tr('Importando tu juego (ExeFS y RomFS)… puede tardar varios minutos'))
        def job():
            try:
                from .build_kit import ensure_build_kit
                from .maintenance import run_build_command
                kit=Path(ensure_build_kit(self.launcher.project,cancel_event=self.cancel))
                command=[kit/'python/python.exe','-B','-E','-s','-m','newsnap','import','--base',base,'--update',update,
                         '--keys',keys,'--work',work,'--hactool',hactool]
                run_build_command(command,kit/'source',Path(self.launcher.project)/'logs/import.log',self.cancel)
                self.events.put(('imported',str(work/'updated')))
            except Exception as error:self.events.put(('error',tr('Importación sin completar: ')+str(error)))
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
            self.launcher.status.set(tr('GameData cargado. Verifica los datos o inicia la expedición.'))
        except (OSError,ValueError) as error:self.launcher.status.set(str(error))
        self.refresh()

    def verify(self,*,resume_game=False):
        if self.launcher.busy:return False
        if not self.refresh()['loaded']:
            self.choose_data();return False
        self.verifying=self.checking=True;self.resume=resume_game;self.cancel.clear()
        self.launcher._set_busy(True)
        self.launcher.status.set(tr('Verificando ExeFS y RomFS de tu juego…'))
        self.progress.report(tr('Verificando ExeFS y RomFS de tu juego…'))
        def work():
            try:
                with settings.ProfileLock(self.launcher.profile):value=home_state.verify(self.launcher.project,self.cancel)
                self.events.put(('verified',value))
            except Exception as error:self.events.put(('error',str(error)))
        threading.Thread(target=work,daemon=True).start();return True

    def notify_update(self,release):
        self.update_notice.configure(text=''.join((tr('Nueva estable disponible: '), f'{release.tag_name}', tr(' · ver actualización'),)))
        self.update_notice.pack(anchor='w',pady=(0,8))

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind == 'runtime_assessed':
                    if value[0] == getattr(self, '_runtime_pending_key', None):
                        self._runtime_assessment = value
                        self._runtime_pending_key = None
                        self.refresh()
                    continue
                self.verifying=self.checking=False;self.launcher._set_busy(False)
                if kind=='imported':
                    self._use_data(value);self.progress.finish(tr('Juego importado'));continue
                self.refresh()
                self.launcher.status.set(tr('Datos del juego verificados.') if kind=='verified' else value)
                self.progress.finish(tr('Datos del juego verificados') if kind=='verified' else tr('Verificación sin completar'),error=kind!='verified')
                if kind=='verified' and self.resume:self.launcher.root.after(50,self.launcher.launch)
                self.resume=False
        except queue.Empty:pass
        self.launcher.root.after(150,self.poll)
