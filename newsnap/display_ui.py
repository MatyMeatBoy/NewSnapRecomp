"""Presentation observations stay distinct from settings and driver policy."""
from tkinter import ttk

from .display_status import read_status


class DisplayPanel:
    def __init__(self, launcher, parent):
        self.launcher=launcher
        self.path=None
        self.process_id=None
        self.started_at=0
        self.generation=0
        self.requested=ttk.Label(parent,text='',wraplength=760,style='Muted.TLabel')
        self.requested.pack(anchor='w',pady=(10,3))
        self.presentation=ttk.Label(parent,text='Presentación: inicia una expedición para comprobarla.',wraplength=760)
        self.presentation.pack(anchor='w',pady=(10,4))
        self.monitor=ttk.Label(parent,text='',wraplength=760,style='Muted.TLabel')
        self.monitor.pack(anchor='w',pady=3)
        self.details=ttk.Label(parent,text='FreeSync/G-SYNC del monitor y activación del controlador: sin verificar.',
                               wraplength=760,style='Muted.TLabel')
        self.details.pack(anchor='w',pady=(3,8))
        launcher.root.after(500,self.poll)

    def observe(self,path,process_id,started_at):
        self.path,self.process_id,self.started_at=path,process_id,started_at
        self.generation=0
        self.presentation.configure(text='Presentación: esperando la primera observación del juego…')
        self.monitor.configure(text='')

    def stop(self):
        self.path=self.process_id=None
        self.monitor.configure(text='')
        self.presentation.configure(text='Expedición cerrada · el registro conserva sus observaciones de pantalla.')

    def poll(self):
        self.requested.configure(text='Modo Vulkan solicitado: '+self.launcher.presentation.get())
        if self.path is not None:
            value=read_status(self.path,self.process_id,started_at=self.started_at)
            if value['available'] and value['generation']>=self.generation:
                self.generation=value['generation']
                label={'variable':'Presentación variable observada · fuente Vulkan.',
                       'fixed':'Presentación fija observada · fuente Vulkan.',
                       'unknown':'Presentación sin verificar · la API aún no ofrece un resultado válido.'}[value['presentation']]
                self.presentation.configure(text=label)
                name=value['monitor_name'] or value['monitor_id'] or 'Sin identificar'
                mode=value['actual_present_mode'] or 'sin verificar'
                self.monitor.configure(text=f"Pantalla: {name} · modo Vulkan efectivo: {mode}")
                requested={'VSync · FIFO':'fifo','Mailbox':'mailbox',
                           'Sin VSync · Immediate':'immediate','VSync adaptable · FIFO Relaxed':'fifo_relaxed'}.get(self.launcher.presentation.get())
                if requested and mode not in (requested,'sin verificar'):
                    self.monitor.configure(text=f"Pantalla: {name} · modo Vulkan efectivo: {mode}. Difiere de la selección actual; puede corresponder a un ajuste pendiente de reinicio o a un fallback del runtime/controlador.")
            else:
                self.presentation.configure(text='Presentación sin verificar · no hay una observación actual del juego.')
                self.monitor.configure(text='')
        self.launcher.root.after(500,self.poll)
