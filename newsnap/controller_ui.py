"""A main-thread SDL session owned by the launcher until its test window closes."""
import tkinter as tk
from tkinter import ttk

from . import launcher_settings as settings
from .paths import runtime_dir


def describe(controller):
    kind='Gamepad reconocido' if controller['recognized'] else 'Joystick sin mapeo de gamepad'
    state='conectado' if controller['connected'] else 'desconectado'
    buttons=controller['buttons']
    pressed=[str(name) for name,on in buttons.items() if on] if buttons else [str(i) for i,on in enumerate(controller['raw_buttons']) if on]
    axes=controller['axes'] or {str(i):value for i,value in enumerate(controller['raw_axes'])}
    capabilities=[name for name,available in controller['capabilities'].items() if available]
    return (f"{controller['name'] or 'Mando sin nombre'} · ID {controller['id']} · {state}\n"
            f"{kind}{' · virtual' if controller['virtual'] else ''}\n"
            f"GUID: {controller['guid']}\n"
            f"Botones pulsados: {', '.join(pressed) or 'ninguno'}\n"
            f"Ejes: {', '.join(f'{key}={value}' for key,value in axes.items()) or 'ninguno'}\n"
            f"Capacidades declaradas: {', '.join(capabilities) or 'ninguna adicional'}\n"
            f"{('Error: '+controller['error']) if controller['error'] else ''}")


class ControllerTest:
    def __init__(self,launcher):
        self.launcher=launcher
        self.session=None
        self.lock=None
        self.closed=False
        self.owns_busy=False
        self.after_id=None
        self.last_text=None
        self.window=tk.Toplevel(launcher.root)
        self.window.title('NewSnap · Prueba del mando')
        self.window.geometry('920x680')
        self.window.minsize(820,640)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        outer=ttk.Frame(self.window,padding=18);outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Comprueba tu mando',style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer,text='Pulsa los botones, mueve las palancas o desconecta y vuelve a conectar el mando. '
                  'Cierra esta prueba antes de iniciar el juego.',wraplength=740).pack(anchor='w',pady=10)
        self.state=ttk.Label(outer,text='Preparando SDL…',wraplength=740)
        self.state.pack(anchor='w',pady=6)
        footer=ttk.Frame(outer);footer.pack(side='bottom',fill='x',pady=(10,0))
        ttk.Button(footer,text='Cerrar prueba',command=self.close).pack(side='right')
        body=ttk.Frame(outer);body.pack(fill='both',expand=True)
        picture=ttk.Frame(body);picture.pack(side='left',anchor='n',padx=(0,16))
        from .controller_art import ControllerArt
        self.art=ControllerArt(picture,launcher.project,scale=4)
        self.art.pack(anchor='n')
        self.selector=ttk.Combobox(picture,state='disabled',width=43)
        self.selector.pack(fill='x',pady=8)
        self.selector.bind('<<ComboboxSelected>>',self.select_controller)
        self.controller_ids=[];self.controllers={};self.selected_controller=None
        details=ttk.Frame(body);details.pack(fill='both',expand=True)
        self.text=tk.Text(details,wrap='word',width=1,height=12,padx=12,pady=12)
        scroll=ttk.Scrollbar(details,command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set,state='disabled')
        scroll.pack(side='right',fill='y');self.text.pack(fill='both',expand=True)
        launcher._set_busy(True)
        self.owns_busy=True
        launcher.root.after(0,self.initialize)

    def initialize(self):
        if self.closed:return
        try:
            from .controller_probe import Session
            self.lock=settings.ProfileLock(self.launcher.profile)
            self.lock.__enter__()
            self.session=Session(runtime_dir(self.launcher.project))
            self.state.configure(text=f'SDL {self.session.sdl_version} · lectura en vivo, sin activar vibración.')
            self.poll()
        except Exception as error:
            self._release()
            self.state.configure(text=str(error))

    def poll(self):
        if self.closed or self.session is None:return
        try:
            values=self.session.snapshot()
            self.show_controllers(values)
            text='\n\n'.join(describe(value) for value in values) or 'No hay mandos conectados. Puedes conectar uno ahora.'
            if self.session.warnings:text+='\n\n'+'\n'.join(self.session.warnings)
            if text!=self.last_text:
                position=self.text.yview()
                self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('end',text)
                self.text.configure(state='disabled');self.text.yview_moveto(position[0]);self.last_text=text
            self.after_id=self.launcher.root.after(100,self.poll)
        except Exception as error:
            self._release()
            self.state.configure(text=str(error))

    def show_controllers(self,values):
        self.controllers={value['id']:value for value in values if value['connected']}
        ids=list(self.controllers)
        if self.selected_controller not in self.controllers:
            self.selected_controller=ids[0] if ids else None
        if ids!=self.controller_ids:
            self.controller_ids=ids
            self.selector.configure(values=tuple(f"{self.controllers[i]['name']} · ID {i}" for i in ids),
                                    state='readonly' if ids else 'disabled')
            if ids:self.selector.current(ids.index(self.selected_controller))
            else:self.selector.set('Sin mandos conectados')
        self.art.set_buttons(self.controllers.get(self.selected_controller))

    def select_controller(self,event=None):
        index=self.selector.current()
        if 0<=index<len(self.controller_ids):
            self.selected_controller=self.controller_ids[index]
            self.art.set_buttons(self.controllers.get(self.selected_controller))

    def _release(self):
        error=None
        session,self.session=self.session,None
        lock,self.lock=self.lock,None
        try:
            if session is not None:session.close()
        except Exception as failure:
            error=failure
        finally:
            try:
                if lock is not None:lock.__exit__(None,None,None)
            except Exception as failure:
                error=error or failure
            finally:
                if self.owns_busy:
                    self.owns_busy=False
                    self.launcher._set_busy(False)
        if error is not None:self.state.configure(text=str(error))

    def close(self):
        if self.closed:return
        self.closed=True
        if self.after_id is not None:self.launcher.root.after_cancel(self.after_id)
        self._release()
        self.window.destroy()
