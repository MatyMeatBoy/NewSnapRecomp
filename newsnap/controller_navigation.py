"""Foreground-only SDL gamepad navigation for launcher-owned Tk widgets.

No synthetic operating-system input is sent. The injected session factory owns
DLL verification; one session exists only while this launcher has focus.
"""
import ctypes
import os
import time
import tkinter as tk


class InputActions:
    """Translate one mapped gamepad, requiring neutral after every handoff."""
    BUTTONS = {'dpad_up': 'up', 'dpad_down': 'down', 'dpad_left': 'left',
               'dpad_right': 'right', 'south': 'activate', 'east': 'back',
               'left_shoulder': 'previous_tab', 'right_shoulder': 'next_tab'}
    REPEAT = frozenset(('up', 'down', 'left', 'right'))

    def __init__(self):
        self.reset()

    def reset(self):
        self.device = None
        self.armed = False
        self.held = set()
        self.deadlines = {}

    def update(self, controllers, now):
        pads = {row['id']: row for row in controllers
                if row.get('connected') and row.get('recognized') and not row.get('error')}
        if self.device not in pads:
            self.reset()
            if not pads:
                return []
            self.device = next(iter(pads))
        row = pads[self.device]
        pressed = {action for button, action in self.BUTTONS.items() if row.get('buttons', {}).get(button)}
        axes = row.get('axes', {})
        for name, negative, positive in (('leftx', 'left', 'right'), ('lefty', 'up', 'down')):
            value = axes.get(name, 0)
            if value < -16000: pressed.add(negative)
            elif value > 16000: pressed.add(positive)
        if not self.armed:
            if not pressed: self.armed = True
            return []
        # Opposing directions cancel rather than repeatedly moving focus twice.
        for a, b in (('left', 'right'), ('up', 'down')):
            if a in pressed and b in pressed: pressed.difference_update((a, b))
        actions = []
        for action in self.BUTTONS.values():
            if action not in pressed: continue
            if action not in self.held:
                actions.append(action)
                self.deadlines[action] = now + .4
            elif action in self.REPEAT and now >= self.deadlines.get(action, now):
                actions.append(action)
                self.deadlines[action] = now + .12
        self.held = pressed
        return actions


def launcher_foreground(root):
    """Require both OS foreground ownership and current Tk keyboard focus."""
    try:
        if not root.winfo_viewable() or root.focus_displayof() is None:
            return False
        if os.name == 'nt':
            from ctypes import wintypes
            user = ctypes.windll.user32
            user.GetForegroundWindow.restype = wintypes.HWND
            user.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(user.GetForegroundWindow(), ctypes.byref(pid))
            return pid.value == os.getpid()
        return True
    except (tk.TclError, OSError):
        return False


class Navigation:
    def __init__(self, root, session_factory, enabled=lambda: True, foreground=None, on_error=None):
        self.root, self.session_factory = root, session_factory
        self.enabled = enabled
        self.foreground = foreground or (lambda: launcher_foreground(root))
        self.on_error = on_error or (lambda error: None)
        self.actions = InputActions()
        self.session = None
        self.timer = None
        self.paused = False
        self.closed = False
        self.started = False
        self.retry_at = 0

    def start(self):
        if self.closed or self.started: return
        self.started = True
        self._poll()

    def _cancel_timer(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None

    def _release(self):
        session, self.session = self.session, None
        self.actions.reset()
        if session is not None: session.close()

    def pause(self):
        self.paused = True
        self._cancel_timer()
        self._release()

    def resume(self):
        if self.closed: return
        self.paused = False
        self.retry_at = 0
        self._cancel_timer()
        if self.started: self._poll()
        else: self.start()

    def close(self):
        if self.closed: return
        self.closed = True
        self._cancel_timer()
        self._release()

    def _poll(self):
        self.timer = None
        if self.closed or self.paused: return
        # A button may enter Tk.wait_window(). Keep input alive in that nested
        # event loop by scheduling before dispatch, rather than on return.
        self.timer = self.root.after(40, self._poll)
        try:
            if not self.enabled() or not self.foreground():
                self._release()
            elif time.monotonic() >= self.retry_at:
                if self.session is None: self.session = self.session_factory()
                reader = getattr(self.session, 'navigation_snapshot', None) or self.session.snapshot
                for action in self.actions.update(reader(), time.monotonic()):
                    # Activation can launch a game, hide a window or open a modal.
                    if self.closed or self.paused or not self.enabled() or not self.foreground(): break
                    self.dispatch(action)
        except Exception as error:
            try: self._release()
            except Exception: pass
            self.retry_at = time.monotonic() + 5
            self.on_error(error)

    def feed_external(self, controllers):
        """Use the diagnostic window's exclusive session without opening another."""
        if self.closed or not self.paused or not self.enabled() or not self.foreground(): return
        for action in self.actions.update(controllers, time.monotonic()):
            if self.closed or not self.paused or not self.foreground(): break
            self.dispatch(action)

    def _scope(self):
        return self.root.grab_current() or self.root

    @staticmethod
    def _usable(widget):
        try:
            return widget.winfo_viewable() and 'disabled' not in str(widget.cget('state'))
        except tk.TclError:
            return widget.winfo_viewable()

    def _travel(self, current, backwards=False):
        scope = self._scope().winfo_toplevel()
        candidate = current
        for _ in range(512):
            candidate = candidate.tk_focusPrev() if backwards else candidate.tk_focusNext()
            if candidate == current: break
            if candidate.winfo_toplevel() == scope and self._usable(candidate):
                candidate.focus_set()
                return

    def dispatch(self, action):
        scope = self._scope()
        current = self.root.focus_get()
        if current is None or current.winfo_toplevel() != scope.winfo_toplevel():
            current = scope
            self._travel(current)
            current = self.root.focus_get() or scope
        if action == 'back':
            scope.event_generate('<<ControllerBack>>')
            return
        if action in ('previous_tab', 'next_tab'):
            self._change_tab(current, -1 if action == 'previous_tab' else 1)
            return
        kind = current.winfo_class()
        if not self._usable(current):
            self._travel(current)
            return
        if kind == 'TCombobox' and action in ('activate', 'left', 'right'):
            values = current.cget('values')
            if values:
                index = current.current()
                current.current((max(index, 0) + (-1 if action == 'left' else 1)) % len(values))
                current.event_generate('<<ComboboxSelected>>')
        elif action == 'activate':
            if kind in ('TButton', 'Button', 'TCheckbutton', 'Checkbutton', 'TRadiobutton', 'Radiobutton'):
                current.invoke()
            else:
                current.event_generate('<Return>')
        elif action in ('up', 'down') and kind in ('Listbox', 'Treeview'):
            current.event_generate('<Up>' if action == 'up' else '<Down>')
        elif action in ('left', 'right', 'up', 'down'):
            self._travel(current, action in ('left', 'up'))

    def _change_tab(self, current, direction):
        # The notebook may be an ancestor of the focused control, or a sibling
        # of the Home panel. Only search inside the active modal/root scope.
        scope = self._scope()
        widgets = [scope]
        while widgets:
            widget = widgets.pop(0)
            if widget.winfo_class() == 'TNotebook':
                tabs = [tab for tab in widget.tabs() if widget.tab(tab, 'state') != 'disabled']
                selected = widget.select()
                if tabs:
                    index = tabs.index(selected) if selected in tabs else 0
                    widget.select(tabs[(index + direction) % len(tabs)])
                return
            widgets.extend(widget.winfo_children())
