"""Tk-thread presentation of measured progress and honest unknown-duration work."""
import time
import tkinter as tk
from tkinter import ttk

from .progress import coerce


class PreparationPanel(ttk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent,text='Preparación de la expedición',padding=10)
        self.label=tk.StringVar(self,value='Listo para iniciar')
        self.detail=tk.StringVar(self,value='El progreso aparecerá aquí al preparar el juego.')
        self.elapsed=tk.StringVar(self,value='')
        self.note=tk.StringVar(self,value='')
        self.active=False;self.started=None;self._tick_id=None
        ttk.Label(self,textvariable=self.label,font=('Segoe UI',11,'bold'),wraplength=540).pack(anchor='w')
        self.bar=ttk.Progressbar(self,mode='determinate',maximum=100,style='Snap.Horizontal.TProgressbar')
        self.bar.pack(fill='x',pady=(8,5))
        row=ttk.Frame(self);row.pack(fill='x')
        ttk.Label(row,textvariable=self.detail,style='Muted.TLabel',font=('Segoe UI',9)).pack(side='left')
        ttk.Label(row,textvariable=self.elapsed,style='Muted.TLabel',font=('Segoe UI',9)).pack(side='right')
        ttk.Label(self,textvariable=self.note,style='Muted.TLabel',wraplength=540,font=('Segoe UI',9)).pack(anchor='w',pady=(5,0))
        self.bind('<Destroy>',self._destroyed,add='+')

    def begin(self,label):
        self.stop();self.active=True;self.started=time.monotonic()
        self.note.set('');self.elapsed.set('0:00 transcurridos')
        self.report(label);self._tick()

    def report(self,message):
        value=coerce(message);self.label.set(value.label)
        self.bar.stop()
        if value.ratio is None:
            self.bar.configure(mode='indeterminate',value=0)
            self.detail.set('En curso · duración pendiente de medir')
            if self.active:self.bar.start(25)
        else:
            self.bar.configure(mode='determinate',value=value.ratio*100)
            scope='este lote' if value.stage=='compile' else 'esta etapa'
            self.detail.set(f'{value.current:,} / {value.total:,} · {value.ratio*100:.0f} % de {scope}')

    def set_note(self,message):
        self.note.set(message)

    def _tick(self):
        if not self.active:return
        seconds=int(time.monotonic()-self.started)
        self.elapsed.set(f'{seconds//60}:{seconds%60:02d} transcurridos')
        self._tick_id=self.after(1000,self._tick)

    def stop(self):
        self.active=False
        if self.bar.winfo_exists():self.bar.stop()
        if self._tick_id is not None:
            self.after_cancel(self._tick_id);self._tick_id=None

    def finish(self,label,*,error=False):
        self.stop();self.label.set(label)
        self.bar.configure(mode='determinate',value=0 if error else 100)
        self.detail.set('Sin completar' if error else 'Preparación finalizada')

    def _destroyed(self,event):
        if event.widget is self:self.stop()

    def destroy(self):
        # Stop ttk's Tcl autostep while the child command still exists. The
        # parent's Destroy notification arrives after its children are gone.
        self.stop()
        super().destroy()
