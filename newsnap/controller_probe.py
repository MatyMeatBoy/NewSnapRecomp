"""Read-only SDL3 controller diagnostics, owned and pumped by the UI main thread.

ctypes declarations follow bundled SDL3 headers (cdecl, C bool, Uint32 IDs,
Sint16 axes, 16-byte GUID by value). No video, output effects or profile writes.
"""
import ctypes as C
import os
from pathlib import Path
import threading

GAMEPAD = 0x2000
BUTTONS = ('south', 'east', 'west', 'north', 'back', 'guide', 'start', 'left_stick',
           'right_stick', 'left_shoulder', 'right_shoulder', 'dpad_up', 'dpad_down',
           'dpad_left', 'dpad_right', 'misc1', 'right_paddle1', 'left_paddle1',
           'right_paddle2', 'left_paddle2', 'touchpad', 'misc2', 'misc3', 'misc4', 'misc5', 'misc6')
AXES = ('leftx', 'lefty', 'rightx', 'righty', 'left_trigger', 'right_trigger')
HINTS = ('SDL_GAMECONTROLLERCONFIG', 'SDL_GAMECONTROLLERCONFIG_FILE',
         'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS')
_active = None


class ProbeError(RuntimeError):
    pass


class GUID(C.Structure):
    _fields_ = [('data', C.c_uint8 * 16)]


def _text(value):
    return value.decode('utf-8', errors='replace') if value else ''


def _load(runtime_dir):
    if os.name != 'nt':
        raise ProbeError('El diagnóstico requiere el runtime SDL3 de Windows.')
    directory = Path(runtime_dir).absolute()
    dll = directory / 'SDL3.dll'
    # An absolute DLL name plus controlled search excludes cwd and PATH.
    if directory.is_symlink() or dll.is_symlink() or not dll.is_file():
        raise ProbeError('Falta el SDL3.dll del runtime local.')
    return C.CDLL(str(dll.resolve()), winmode=0x100 | 0x1000)


def _unload(library):
    if library is not None and os.name == 'nt' and getattr(library, '_handle', 0):
        import _ctypes
        _ctypes.FreeLibrary(library._handle)
        library._handle = 0


def _bind(sdl):
    p, i, u, b, s = C.c_void_p, C.c_int, C.c_uint32, C.c_bool, C.c_char_p
    functions = {
        'SDL_GetVersion': (i, []), 'SDL_GetError': (s, []), 'SDL_ClearError': (b, []),
        'SDL_InitSubSystem': (b, [u]), 'SDL_QuitSubSystem': (None, [u]),
        'SDL_PumpEvents': (None, []), 'SDL_UpdateJoysticks': (None, []),
        'SDL_FlushEvents': (None, [u, u]), 'SDL_free': (None, [p]),
        'SDL_GetHint': (s, [s]), 'SDL_SetHintWithPriority': (b, [s, s, i]),
        'SDL_ResetHint': (b, [s]), 'SDL_AddGamepadMappingsFromFile': (i, [s]),
        'SDL_AddGamepadMapping': (i, [s]),
        'SDL_GetJoysticks': (C.POINTER(u), [C.POINTER(i)]),
        'SDL_GetJoystickNameForID': (s, [u]), 'SDL_GetJoystickGUIDForID': (GUID, [u]),
        'SDL_GetJoystickVendorForID': (C.c_uint16, [u]),
        'SDL_GetJoystickProductForID': (C.c_uint16, [u]),
        'SDL_IsGamepad': (b, [u]), 'SDL_IsJoystickVirtual': (b, [u]),
        'SDL_OpenJoystick': (p, [u]), 'SDL_CloseJoystick': (None, [p]),
        'SDL_JoystickConnected': (b, [p]), 'SDL_GetJoystickProperties': (u, [p]),
        'SDL_GetNumJoystickAxes': (i, [p]), 'SDL_GetNumJoystickButtons': (i, [p]),
        'SDL_GetNumJoystickHats': (i, [p]), 'SDL_GetJoystickAxis': (C.c_int16, [p, i]),
        'SDL_GetJoystickButton': (b, [p, i]), 'SDL_GetJoystickHat': (C.c_uint8, [p, i]),
        'SDL_OpenGamepad': (p, [u]), 'SDL_CloseGamepad': (None, [p]),
        'SDL_GetGamepadName': (s, [p]), 'SDL_GetGamepadMapping': (p, [p]),
        'SDL_GetGamepadButton': (b, [p, i]), 'SDL_GetGamepadAxis': (C.c_int16, [p, i]),
        'SDL_GetBooleanProperty': (b, [u, s, b]),
    }
    for name, (result, arguments) in functions.items():
        function = getattr(sdl, name)
        function.restype, function.argtypes = result, arguments


class Session:
    """Own one SDL input diagnostic; caller holds launcher busy/profile lock.

    Construct, pump, snapshot and close on Python's main (Tk) thread. env is an
    optional mapping of SDL hint overrides, never written to os.environ or disk.
    Devices removed since the prior snapshot disappear and their handles close.
    A disconnect racing a read is reported with connected=false, then removed.
    """
    def __init__(self, runtime_dir, env=None):
        global _active
        self._thread = threading.get_ident()
        self._sdl = None
        self._handles = {}
        self._hints = {}
        self._init_attempted = False
        self._closed = False
        self.warnings = []
        self.sdl_version = None
        self._main_thread()
        if _active is not None:
            raise ProbeError('Ya hay un diagnóstico de mandos abierto.')
        _active = self
        try:
            self._sdl = _load(runtime_dir)
            _bind(self._sdl)
            version = self._sdl.SDL_GetVersion()
            if version < 3002000 or version >= 4000000:
                raise ProbeError('SDL3 no ofrece la ABI de mandos requerida (3.2 o posterior).')
            self.sdl_version = f'{version // 1000000}.{version // 1000 % 1000}.{version % 1000}'
            for name in HINTS:
                if env is not None and name in env:
                    key = name.encode()
                    self._hints[key] = self._sdl.SDL_GetHint(key)
                    if not self._sdl.SDL_SetHintWithPriority(key, str(env[name]).encode('utf-8'), 2):
                        raise ProbeError('No se pudo aplicar la configuración SDL del mando.')
            self._init_attempted = True
            if not self._sdl.SDL_InitSubSystem(GAMEPAD):
                raise ProbeError('No se pudo iniciar SDL: ' + self._error())
            self._mappings(Path(runtime_dir))
        except BaseException as error:
            try:
                self.close()
            except Exception:
                pass  # Preserve the initialization error after exhaustive cleanup.
            if isinstance(error, Exception) and not isinstance(error, ProbeError):
                raise ProbeError('No se pudo iniciar el diagnóstico SDL: ' + str(error)) from error
            raise

    def _main_thread(self):
        if threading.current_thread() is not threading.main_thread() or threading.get_ident() != self._thread:
            raise ProbeError('SDL de mandos debe usarse en el hilo principal de la ventana.')

    def _ready(self):
        self._main_thread()
        if self._closed:
            raise ProbeError('El diagnóstico de mandos está cerrado.')

    def _error(self):
        return _text(self._sdl.SDL_GetError()) or 'Error SDL sin detalle'

    def _mappings(self, directory):
        sdl = self._sdl
        if sdl.SDL_GetHint(b'SDL_GAMECONTROLLERCONFIG_FILE'):
            return
        path = directory / 'gamecontrollerdb.txt'
        if not path.is_file():
            return
        inline = sdl.SDL_GetHint(b'SDL_GAMECONTROLLERCONFIG')
        if sdl.SDL_AddGamepadMappingsFromFile(str(path.absolute()).encode('utf-8')) < 0:
            self.warnings.append('No se pudo leer gamecontrollerdb.txt: ' + self._error())
        if inline:
            for line in inline.split(b'\n'):
                line = line.rstrip(b'\r')
                if line and sdl.SDL_AddGamepadMapping(line) < 0:
                    self.warnings.append('No se pudo aplicar un mapeo SDL explícito: ' + self._error())

    def pump(self):
        self._ready()
        self._sdl.SDL_PumpEvents()
        self._sdl.SDL_UpdateJoysticks()
        # Consume input/hotplug events after state updates; never accumulate a
        # queue in this exclusive input-only session or touch another subsystem.
        self._sdl.SDL_FlushEvents(0x600, 0x6ff)

    def _close_device(self, handles):
        joystick, gamepad = handles
        try:
            if gamepad:
                self._sdl.SDL_CloseGamepad(gamepad)
        finally:
            if joystick:
                self._sdl.SDL_CloseJoystick(joystick)

    def navigation_snapshot(self):
        """Mapped controls only, without diagnostic mapping/capability allocations."""
        self.pump()
        sdl, count = self._sdl, C.c_int()
        ids = sdl.SDL_GetJoysticks(C.byref(count))
        if not ids:
            raise ProbeError('No se pudieron enumerar los mandos: ' + self._error())
        try:
            if not 0 <= count.value <= 256: raise ProbeError('Cantidad de mandos inválida')
            present = [int(ids[i]) for i in range(count.value)]
        finally:
            sdl.SDL_free(ids)
        for instance in list(self._handles):
            if instance not in present: self._close_device(self._handles.pop(instance))
        rows = []
        for instance in present:
            if not sdl.SDL_IsGamepad(instance): continue
            if instance not in self._handles:
                joy = sdl.SDL_OpenJoystick(instance)
                pad = sdl.SDL_OpenGamepad(instance) if joy else None
                if joy: self._handles[instance] = (joy, pad)
            joy, pad = self._handles.get(instance, (None, None))
            if not pad: continue
            rows.append({'id':instance, 'recognized':True, 'connected':bool(sdl.SDL_JoystickConnected(joy)),
                         'buttons':{name:bool(sdl.SDL_GetGamepadButton(pad,i)) for i,name in enumerate(BUTTONS)},
                         'axes':{name:int(sdl.SDL_GetGamepadAxis(pad,i)) for i,name in enumerate(AXES[:2])}})
        return rows

    def snapshot(self):
        self.pump()
        sdl = self._sdl
        count = C.c_int()
        sdl.SDL_ClearError()
        ids = sdl.SDL_GetJoysticks(C.byref(count))
        if not ids:
            raise ProbeError('No se pudieron enumerar los mandos: ' + self._error())
        try:
            if count.value < 0 or count.value > 256:
                raise ProbeError('SDL devolvió una cantidad de mandos inválida.')
            present = [int(ids[index]) for index in range(count.value)]
        finally:
            sdl.SDL_free(ids)
        for instance in list(self._handles):
            if instance not in present:
                self._close_device(self._handles.pop(instance))
        result = []
        for instance in present:
            sdl.SDL_ClearError()
            guid = sdl.SDL_GetJoystickGUIDForID(instance)
            recognized = bool(sdl.SDL_IsGamepad(instance))
            if instance not in self._handles:
                joystick = sdl.SDL_OpenJoystick(instance)
                gamepad = sdl.SDL_OpenGamepad(instance) if recognized and joystick else None
                if joystick:
                    self._handles[instance] = (joystick, gamepad)
            joystick, gamepad = self._handles.get(instance, (None, None))
            if joystick and recognized and not gamepad:
                gamepad = sdl.SDL_OpenGamepad(instance)
                self._handles[instance] = (joystick, gamepad)
            row = {'id': instance, 'name': _text(sdl.SDL_GetJoystickNameForID(instance)),
                   'guid': bytes(guid.data).hex(), 'vendor': sdl.SDL_GetJoystickVendorForID(instance),
                   'product': sdl.SDL_GetJoystickProductForID(instance), 'recognized': recognized,
                   'virtual': bool(sdl.SDL_IsJoystickVirtual(instance)),
                   'connected': bool(joystick and sdl.SDL_JoystickConnected(joystick)),
                   'mapping': None, 'buttons': {}, 'axes': {}, 'raw_buttons': [], 'raw_axes': [],
                   'hats': [], 'capabilities': {}, 'error': None}
            if joystick:
                row['raw_buttons'] = [bool(sdl.SDL_GetJoystickButton(joystick, n)) for n in self._indices(sdl.SDL_GetNumJoystickButtons(joystick))]
                row['raw_axes'] = [int(sdl.SDL_GetJoystickAxis(joystick, n)) for n in self._indices(sdl.SDL_GetNumJoystickAxes(joystick))]
                row['hats'] = [int(sdl.SDL_GetJoystickHat(joystick, n)) for n in self._indices(sdl.SDL_GetNumJoystickHats(joystick))]
                properties = sdl.SDL_GetJoystickProperties(joystick)
                row['capabilities'] = {name: bool(sdl.SDL_GetBooleanProperty(properties, ('SDL.joystick.cap.' + name).encode(), False))
                                       for name in ('mono_led', 'rgb_led', 'player_led', 'rumble', 'trigger_rumble')}
            if gamepad:
                row['name'] = _text(sdl.SDL_GetGamepadName(gamepad)) or row['name']
                mapping = sdl.SDL_GetGamepadMapping(gamepad)
                if mapping:
                    try:
                        row['mapping'] = _text(C.string_at(mapping))
                    finally:
                        sdl.SDL_free(mapping)
                row['buttons'] = {name: bool(sdl.SDL_GetGamepadButton(gamepad, n)) for n, name in enumerate(BUTTONS)}
                row['axes'] = {name: int(sdl.SDL_GetGamepadAxis(gamepad, n)) for n, name in enumerate(AXES)}
            error = _text(sdl.SDL_GetError())
            if error:
                row['error'] = error
            elif not joystick or recognized and not gamepad:
                row['error'] = 'El dispositivo no se pudo abrir como mando SDL.'
            result.append(row)
        return result

    @staticmethod
    def _indices(count):
        if count < 0 or count > 256:
            raise ProbeError('SDL devolvió una cantidad de controles inválida.')
        return range(count)

    def close(self):
        global _active
        if self._closed:
            return
        self._main_thread()
        self._closed = True
        errors = []
        def cleanup(function, *arguments):
            try:
                function(*arguments)
            except Exception as error:
                errors.append(error)
        try:
            if self._sdl is not None:
                for joystick, gamepad in self._handles.values():
                    if gamepad:
                        cleanup(self._sdl.SDL_CloseGamepad, gamepad)
                    if joystick:
                        cleanup(self._sdl.SDL_CloseJoystick, joystick)
                self._handles.clear()
                if self._init_attempted:
                    cleanup(self._sdl.SDL_QuitSubSystem, GAMEPAD)
                for key, value in self._hints.items():
                    if value is None:
                        cleanup(self._sdl.SDL_ResetHint, key)
                    else:
                        cleanup(self._sdl.SDL_SetHintWithPriority, key, value, 2)
        finally:
            cleanup(_unload, self._sdl)
            self._sdl = None
            if _active is self:
                _active = None
        if errors:
            raise ProbeError('No se pudo cerrar por completo SDL: ' + str(errors[0])) from errors[0]

    def __enter__(self):
        self._ready()
        return self

    def __exit__(self, *exception):
        self.close()


def launcher_runtime(root):
    """Resolve a pinned public DLL even before the first game build exists."""
    import hashlib, json
    root = Path(root)
    pin = json.loads((root/'assets/controllers/launcher-sdl.json').read_text(encoding='utf-8'))
    for directory in (root/'tools/launcher-sdl', root/'toolchain/launcher-sdl'):
        dll = directory/'SDL3.dll'
        if dll.is_file() and not dll.is_symlink() and hashlib.sha256(dll.read_bytes()).hexdigest() == pin['sha256']:
            return directory
    raise ProbeError('Falta el SDL3 verificado del launcher; reinstala el paquete completo.')
