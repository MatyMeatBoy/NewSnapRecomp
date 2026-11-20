"""Tk-owned message dialogs reachable by the launcher's gamepad navigation."""
import tkinter as tk
from tkinter import ttk

from .launcher_language import tr


def modal(window, parent, focus):
    """Wait locally and restore an enclosing modal's grab and keyboard focus."""
    previous_grab = parent.grab_current()
    previous_focus = parent.focus_get()
    window.transient(parent.winfo_toplevel())
    window.grab_set()
    focus.focus_set()
    try:
        parent.wait_window(window)
    finally:
        try:
            if previous_grab is not None and previous_grab.winfo_exists(): previous_grab.grab_set()
            if previous_focus is not None and previous_focus.winfo_exists(): previous_focus.focus_set()
        except tk.TclError:
            pass


def _message(title, message, *, parent, buttons, cancel=False):
    window = tk.Toplevel(parent)
    window.title(title)
    window.resizable(False, False)
    frame = ttk.Frame(window, padding=20); frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=message, wraplength=560).pack(anchor='w', pady=(0, 15))
    ttk.Label(frame, text=tr('Sur: seleccionar · Este: volver')).pack(anchor='w', pady=(0, 10))
    row = ttk.Frame(frame); row.pack(fill='x')
    result = [cancel]
    def finish(value):
        result[0] = value
        window.destroy()
    first = None
    for text, value in buttons:
        button = ttk.Button(row, text=tr(text), command=lambda value=value: finish(value))
        button.pack(side='left', padx=(0, 8))
        first = first or button
    window.protocol('WM_DELETE_WINDOW', lambda: finish(cancel))
    window.bind('<Escape>', lambda event: finish(cancel))
    window.bind('<<ControllerBack>>', lambda event: finish(cancel))
    modal(window, parent, first)
    return result[0]


def askokcancel(title=None, message=None, **options):
    return bool(_message(title or '', message or '', parent=options['parent'],
                         buttons=(('Cancelar', False), ('Aceptar', True)), cancel=False))


def askyesno(title=None, message=None, **options):
    return bool(_message(title or '', message or '', parent=options['parent'],
                         buttons=(('No', False), ('Sí', True)), cancel=False))


def showinfo(title=None, message=None, **options):
    _message(title or '', message or '', parent=options['parent'], buttons=(('Aceptar', True),), cancel=True)
    return 'ok'


def showerror(title=None, message=None, **options):
    return showinfo(title, message, **options)


def showwarning(title=None, message=None, **options):
    return showinfo(title, message, **options)
