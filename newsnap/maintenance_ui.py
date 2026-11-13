"""Launcher-owned background maintenance; Tk remains on its UI thread."""
import queue
import threading
from tkinter import ttk

class RuntimeMaintenance:
    def __init__(self, launcher, parent, status):
        self.launcher, self.status = launcher, status
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.active = False
        self.resume_game = False
        row=ttk.Frame(parent)
        row.pack(anchor='w',pady=8)
        self.repair=ttk.Button(row,text='Verificar / reconstruir juego',command=lambda:self.start(force=True))
        self.repair.pack(side='left')
        self.cancel=ttk.Button(row,text='Cancelar preparación',command=self.cancel_event.set,state='disabled')
        self.cancel.pack(side='left',padx=8)
        launcher.root.after(150,self.poll)

    def start(self, *, force=False, resume_game=False):
        if self.active or self.launcher.busy:
            return False
        self.active=True
        self.resume_game=resume_game
        self.cancel_event.clear()
        self.launcher._set_busy(True)
        self.repair.configure(state='disabled')
        self.cancel.configure(state='normal')
        self.status.configure(text='Preparando la reconstrucción local…')
        def progress(message):
            self.events.put(('progress',str(message)))
        def work():
            try:
                from .build_kit import ensure_build_kit
                from .maintenance import rebuild_runtime, recover_runtime, assess_runtime
                from .launcher_settings import ProfileLock, load_profile
                with ProfileLock(load_profile(self.launcher.project)):
                    recover_runtime(self.launcher.project)
                if not force and not assess_runtime(self.launcher.project)['needs_rebuild']:
                    self.events.put(('done',{'rebuilt':False}))
                    return
                kit=ensure_build_kit(self.launcher.project,progress=progress,cancel_event=self.cancel_event)
                result=rebuild_runtime(self.launcher.project,kit,cancel_event=self.cancel_event,progress=progress,force=force)
                self.events.put(('done',result))
            except Exception as error:
                self.events.put(('error',str(error)))
        threading.Thread(target=work,daemon=True).start()
        return True

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if not self.active:
                    continue  # Late events cannot release another operation's busy ownership.
                if kind=='progress':
                    self.status.configure(text=value)
                    self.launcher.status.set(value)
                    continue
                self.active=False
                self.repair.configure(state='normal')
                self.cancel.configure(state='disabled')
                self.launcher._set_busy(False)
                message=(('Juego reconstruido y verificado. Los shaders se prepararán antes de jugar.'
                          if value.get('rebuilt') else 'Juego verificado; listo para iniciar.')
                         if kind=='done' else value)
                self.status.configure(text=message)
                self.launcher.status.set(message)
                if kind=='done' and self.resume_game:
                    self.launcher.root.after(100,self.launcher.launch)
                self.resume_game=False
        except queue.Empty:
            pass
        self.launcher.root.after(150,self.poll)
