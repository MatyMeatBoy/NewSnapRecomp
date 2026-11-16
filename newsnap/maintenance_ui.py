"""Launcher-owned background maintenance; Tk remains on its UI thread."""
import queue
import threading
from tkinter import ttk


def completion_message(result):
    if not result.get('rebuilt'):
        return 'Juego verificado; listo para iniciar.'
    proof=result.get('replacement',{})
    verified=all(proof.get(key) is True for key in
                 ('cache_absence_verified','transaction_removed','build_temporaries_removed'))
    if not verified:
        return 'Runtime reconstruido; sin comprobante de limpieza de cachés.'
    checked=len(proof.get('invalidated',[]))
    removed=len(proof.get('removed_existing',[]))
    message=(f'Juego reemplazado y verificado. Cachés anteriores: {removed} retiradas; '
             f'{checked}/{checked} rutas comprobadas; sin copias temporales de reconstrucción.')
    if proof.get('log_recorded') is False:
        message+=' El comprobante no se pudo guardar en el log.'
    return message

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
        from .progress_bar import page_bar
        self.bar=page_bar(row,width=220,height=12)   # this page's own view of the rebuild's progress
        if self.bar is not None:self.bar.pack(side='left',padx=(8,0))
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
        self._show_progress(None)
        def progress(message):
            self.events.put(('progress',message))
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

    def _show_progress(self,ratio,running=True):
        """Measured part of the current stage from left to right, or the travelling segment while it has no count."""
        bar=getattr(self,'bar',None)
        if bar is None:return
        bar.stop()
        if ratio is None and running:
            bar.configure(mode='indeterminate',value=0);bar.start()
        else:
            bar.configure(mode='determinate',maximum=1000,value=round((ratio or 0)*1000))

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if not self.active:
                    continue  # Late events cannot release another operation's busy ownership.
                if kind=='progress':
                    from .progress import coerce
                    update=coerce(value)
                    self.status.configure(text=update.label)
                    self.launcher.status.set(update.label)
                    self.launcher.home.progress.report(update)
                    self._show_progress(update.ratio)
                    continue
                self.active=False
                self._show_progress(0,running=False)
                self.repair.configure(state='normal')
                self.cancel.configure(state='disabled')
                self.launcher._set_busy(False)
                message=completion_message(value) if kind=='done' else value
                self.status.configure(text=message)
                self.launcher.status.set(message)
                self.launcher.home.progress.finish('Runtime verificado' if kind=='done' else 'Reconstrucción sin completar',error=kind!='done')
                if kind=='done' and self.resume_game:
                    self.launcher.root.after(100,self.launcher.launch)
                self.resume_game=False
        except queue.Empty:
            pass
        self.launcher.root.after(150,self.poll)
