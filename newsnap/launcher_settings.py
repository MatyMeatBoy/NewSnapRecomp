"""Safe, narrow edits to the runtime INI and local launcher preferences."""
import json
import hashlib
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from .paths import runtime_dir, data_dir, default_profile, shader_library_dir, is_release_layout
from .version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES

DEFAULTS = {'fullscreen': '1', 'window_size': 'auto', 'vk_present': 'mailbox',
            'fps': '60', 'volume': '100', 'mouse_sens': '1', 'motion': '1',
            'operation_mode': 'docked', 'render_scale': 'display', 'upscaler': 'bilinear',
            'sharpness': '0', 'aniso': '16', 'shadow_scale': 'auto', 'aspect': 'fit', 'color_preset': 'default',
            'color_brightness': '0', 'color_contrast': '100', 'color_saturation': '100', 'color_gamma': '1'}
SECTIONS = {'fullscreen': 'display', 'window_size': 'display', 'vk_present': 'display',
            'fps': 'frame rate', 'volume': 'audio', 'mouse_sens': 'input', 'motion': 'input',
            'operation_mode': 'language', **{key: 'display' for key in DEFAULTS if key not in
                ('fullscreen', 'window_size', 'vk_present', 'fps', 'volume', 'mouse_sens', 'motion', 'operation_mode')}}
# Same four actual colour adjustments as runtime/ui/menu.cpp; the preset name alone has no visual effect.
COLOR_KEYS = ('color_brightness', 'color_contrast', 'color_saturation', 'color_gamma')
NEUTRAL_SETTINGS = {'color_preset':'default', 'color_brightness':'0', 'color_contrast':'100',
                    'color_saturation':'100', 'color_gamma':'1', 'sharpness':'0', 'upscaler':'bilinear'}
COLOR_PRESETS = {name: dict(zip(COLOR_KEYS, values)) for name, values in {
    'default': ('0', '100', '100', '1'), 'vivid': ('0', '115', '135', '0.95'),
    'clarity': ('2', '110', '115', '1')}.items()}
# Render scales above 100 %: host supersampling in TV mode (SS-02).
SUPERSAMPLE_SCALES = ('125', '133', '150', '175', '200', '250', '300', 'display')

CHOICES = {'vk_present': ('mailbox', 'fifo', 'immediate'),
           'operation_mode': ('docked', 'handheld'), 'render_scale': ('game', '50', '60', '70', '80', '90', '100') + SUPERSAMPLE_SCALES,
           'upscaler': ('fsr', 'bilinear'), 'aniso': ('game', '2', '4', '8', '16', 'auto'), 'shadow_scale': ('1', '2', '4', 'auto'), 'frame_gen': ('off', 'fsr'), 'hd_photos': ('1', '0'), 'hd_shadows': ('0', '1'), 'tex_pack': ('1', '0'), 'tex_pack_save': ('0', '1'),
           'aspect': ('fit', 'stretch', 'ultrawide'), 'color_preset': ('default', 'vivid', 'clarity', 'custom')}
RANGES = {'volume': (0, 100, True), 'mouse_sens': (0, 10, False), 'sharpness': (0, 100, True),
          'color_brightness': (-30, 30, True), 'color_contrast': (70, 150, True),
          'color_saturation': (50, 200, True), 'color_gamma': (0.8, 1.2, False)}
ENV_UI_OVERRIDES = frozenset(DEFAULTS)
# Snap 2.0.1 control NACP: support mask 0x72fd, restricted to nonempty title slots.
# The runtime accepts more codes for other games; the launcher offers this game's set.
LANGUAGES = ('', 'en-US', 'ja', 'fr', 'de', 'es-419', 'es', 'it', 'fr-CA', 'ko', 'zh-Hant', 'zh-Hans')
BINDING_DEFAULTS = {
    'bind_a': 'key:mouse_l,key:e,pad:default', 'bind_b': 'key:lshift,pad:default',
    'bind_x': 'key:space,pad:default', 'bind_y': 'pad:default',
    'bind_lclick': 'key:lctrl,pad:default', 'bind_rclick': 'key:c,pad:default',
    'bind_l': 'key:q,pad:default', 'bind_r': 'key:r,pad:default',
    'bind_zl': 'key:mouse_r,key:z,pad:default', 'bind_zr': 'key:f,key:x,pad:default',
    'bind_plus': 'key:tab,pad:default', 'bind_minus': 'key:m,pad:default',
    'bind_left': 'key:1,pad:default', 'bind_up': 'key:2,pad:default',
    'bind_right': 'key:3,pad:default', 'bind_down': 'key:4,pad:default',
    'bind_lstick_left': 'key:a', 'bind_lstick_up': 'key:w', 'bind_lstick_right': 'key:d', 'bind_lstick_down': 'key:s',
    'bind_rstick_left': 'key:left', 'bind_rstick_up': 'key:up', 'bind_rstick_right': 'key:right', 'bind_rstick_down': 'key:down'}
CONTROL_DEFAULTS = {'mouse_sens': '1', 'motion': '1', 'gyro_sens': '2.5', 'pad_layout': 'auto', 'rumble_strength': '130',
                    'rumble_curve': '0.6', 'rumble_triggers': '0', 'stick_deadzone': '8',
                    'lstick_deadzone': '', 'rstick_deadzone': '', **BINDING_DEFAULTS}
DEFAULTS.update(CONTROL_DEFAULTS)
DEFAULTS.update(lang='', audio_prefill_ms='20', perf_overlay='off')
DEFAULTS.update(upscaling='auto', upscaling_quality='native', frame_gen='off', hd_photos='1', hd_shadows='0', tex_pack='1', tex_pack_save='0')
ENV_UI_OVERRIDES = ENV_UI_OVERRIDES | {'upscaling', 'upscaling_quality'}
SECTIONS.update(upscaling='display', upscaling_quality='display', frame_gen='display', hd_photos='display', hd_shadows='display', tex_pack='display', tex_pack_save='display')
SECTIONS.update({key: 'input' for key in CONTROL_DEFAULTS})
SECTIONS.update(lang='language', audio_prefill_ms='audio', perf_overlay='display')
CHOICES.update(lang=LANGUAGES, pad_layout=('auto', 'nintendo', 'xbox', 'playstation'),
               upscaling=('off', 'auto', 'fsr3', 'fsr4', 'dlss'),
               upscaling_quality=('native', 'quality', 'balanced', 'performance'),
               perf_overlay=('off', 'fps', 'full'))
RANGES.update(gyro_sens=(0.1, 10, False), rumble_strength=(0, 300, True), rumble_curve=(0.2, 1.5, False),
              stick_deadzone=(0, 50, False), lstick_deadzone=(0, 50, False),
              rstick_deadzone=(0, 50, False), audio_prefill_ms=(0, 500, False))
# Names and reserved keys mirror input_map.c/input_map.h, not OS virtual-key codes.
BINDING_KEYS = frozenset('abcdefghijklmnopqrstuvwxyz0123456789') | frozenset(('space tab lshift lctrl up down left right '
    'mouse_l mouse_r mouse_m mouse_x1 mouse_x2 enter backspace rshift rctrl lalt capslock insert delete home end '
    'pageup pagedown f2 f3 f4 f5 f6 f7 f9 f12 num0 num1 num2 num3 num4 num5 num6 num7 num8 num9 '
    'num_add num_sub num_mul num_div num_decimal minus equals lbracket rbracket semicolon apostrophe comma period slash backslash grave').split())
BINDING_PADS = frozenset(('south east west north lstick rstick l r start back dpad_left dpad_up dpad_right dpad_down '
                         'zl zr lpaddle1 rpaddle1 lpaddle2 rpaddle2').split())
ENTRY = re.compile(r'^(\s*)((?:AC_)?[A-Za-z_0-9]+)\s*=.*$', re.IGNORECASE)


def _key(value):
    return value.lower().removeprefix('ac_')


def valid_binding(key, value):
    if key not in BINDING_DEFAULTS or len(value.encode('utf-8')) > 255 or any(c in value for c in '\r\n\0'):
        return False
    if not value:
        return True  # An unset runtime value restores both keyboard and pad defaults.
    tokens = [token.strip().lower() for token in value.split(',') if token.strip()]
    if not tokens:
        return False
    for token in tokens:
        if token == 'none':
            continue
        kind, separator, name = token.partition(':')
        name = name.strip()
        if not separator or kind not in ('key', 'pad'):
            return False
        if kind == 'pad' and ('lstick_' in key or 'rstick_' in key):
            return False
        if name != 'default' and name not in (BINDING_KEYS if kind == 'key' else BINDING_PADS):
            return False
    return True


def validate_settings(values):
    result = {}
    for key, raw in values.items():
        value = str(raw).strip()
        valid = False
        if key in BINDING_DEFAULTS:
            valid = valid_binding(key, value)
        elif key in ('lstick_deadzone', 'rstick_deadzone') and value == '':
            valid = True
        elif key in ('fullscreen', 'motion', 'rumble_triggers'):
            valid = value in ('0', '1')
        elif key == 'fps':
            valid = value in ('30', '60', '90', '120', '144', 'display', 'vrr')
        elif key in CHOICES:
            valid = value in CHOICES[key]
        elif key == 'window_size' and value == 'auto':
            valid = True
        elif key == 'window_size':
            match = re.fullmatch(r'(\d{2,5})x(\d{2,5})', value)
            valid = bool(match and all(64 <= int(n) <= 16384 for n in match.groups()))
        elif key in RANGES:
            try:
                number = float(value)
                low, high, integer = RANGES[key]
                valid = math.isfinite(number) and low <= number <= high
                if integer:
                    valid = valid and number.is_integer()
            except ValueError:
                pass
        if not valid:
            raise ValueError(f'Valor no válido para {key}: {value}')
        result[key] = value
    # A caller may pass one setting at a time (reading the file line by line, saving one change). A rule
    # that relates two settings is only judged here when both are present; save_settings and the launch
    # check the whole combination with validate_video_combination. Judging frame_gen alone read the
    # missing upscaler as Original: the launcher refused frame generation and dropped it on reload.
    validate_video_combination(result, complete=False)
    return result


def validate_video_combination(values, complete=True):
    """Rules between video settings. complete=False: values may hold only some settings, and a rule is skipped
    unless every setting it relates is present (missing ones are not read as their defaults)."""
    def have(*keys):
        return complete or all(key in values for key in keys)

    upscaling = values.get('upscaling', 'off')
    frame_gen = values.get('frame_gen', 'off') == 'fsr'
    # 'display' is the default and adapts by itself: no host scale while an upscaler runs or in handheld (MENU-02).
    explicit = values.get('render_scale') in SUPERSAMPLE_SCALES and values.get('render_scale') != 'display'
    if have('frame_gen', 'upscaling') and frame_gen and upscaling not in ('fsr3', 'fsr4', 'auto'):
        raise ValueError('La generación de fotogramas FSR necesita el escalado AMD FSR 3.1 o FSR 4, o Automático (cualquier calidad, también Nativo).')
    # MENU-03: Automatic steps aside by itself above 100 % (the runtime reads it as Original); a chosen
    # upscaler does not, so that combination is still refused.
    if have('upscaling', 'render_scale') and upscaling not in ('off', 'auto') and explicit:
        raise ValueError('Con un escalado elegido (FSR o DLSS), la resolución interna la marca su calidad. Elige 100 % o menos, o deja el escalado en Automático.')
    if have('frame_gen', 'upscaling', 'render_scale') and frame_gen and upscaling == 'auto' and explicit:
        raise ValueError('La generación de fotogramas FSR necesita FSR, y con una resolución interna superior al 100 % el '
                         'escalado Automático no usa ninguno. Elige AMD FSR 3.1 o FSR 4 con una resolución interna de 100 % o menos.')
    if have('operation_mode', 'render_scale') and values.get('operation_mode') == 'handheld' and explicit:
        raise ValueError('La escala experimental superior al 100 % requiere salida TV. Elige «TV · 1920 × 1080» o reduce la escala al 100 % o menos para usar el modo portátil.')


def _settings_source(path):
    path = Path(path)
    if path.name == 'newsnap.ini' and not path.exists():
        legacy = path.with_name('astralchain.ini')
        if legacy.is_file():
            return legacy
    return path


def load_settings(path):
    result = dict(DEFAULTS)
    path = _settings_source(path)
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match = ENTRY.match(line)
            if match and (key := _key(match[2])) in DEFAULTS:
                value = line.split('=', 1)[1].strip().strip('"')
                if key == 'vk_present' and value == 'fifo_relaxed':
                    value = 'fifo'   # FIFO Relaxed is no longer offered (0.9.11): plain VSync, its closest mode
                if key in BINDING_DEFAULTS:
                    # Do not erase legacy/user text just because this editor cannot validate it.
                    result[key] = value
                    continue
                try:
                    result.update(validate_settings({key: value}))
                except ValueError:
                    pass
    return result


def _atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_settings(path, values):
    """Change only recognized keys; preserve all other bytes and comments."""
    values = validate_settings(values)
    if values.get('color_preset') in COLOR_PRESETS:
        values = {**COLOR_PRESETS[values['color_preset']], **values}
    if not values:
        return
    path = Path(path)
    validate_video_combination({**load_settings(path), **values})
    source = _settings_source(path)
    raw = source.read_bytes() if source.is_file() else b''
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8')
    ending = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines(keepends=True)
    found = set()
    for index, line in enumerate(lines):
        match = ENTRY.match(line.rstrip('\r\n'))
        if match and (key := _key(match[2])) in values:
            eol = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
            lines[index] = f'{match[1]}{match[2]} = {values[key]}{eol}'
            found.add(key)
    for section in dict.fromkeys(SECTIONS.values()):
        missing = [key for key in values if key not in found and SECTIONS[key] == section]
        if not missing:
            continue
        # Insert into existing section or add one, keeping unrelated sections verbatim.
        start = next((i for i, line in enumerate(lines) if line.strip().lower() == f'[{section}]'), None)
        if start is None:
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += ending
            lines += [ending, f'[{section}]{ending}']
            insertion = len(lines)
        else:
            insertion = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
            if insertion and not lines[insertion - 1].endswith('\n'):
                lines[insertion - 1] += ending
        lines[insertion:insertion] = [f'{key} = {values[key]}{ending}' for key in missing]
    _atomic_write(path, bom + ''.join(lines).encode('utf-8'))


def merge_settings(baseline, local, current):
    """Keep external changes except where the user explicitly edited this UI."""
    merged = dict(current)
    merged.update({key: value for key, value in local.items() if value != baseline.get(key)})
    return merged


def save_edited_settings(path, baseline, local):
    changes = {key: value for key, value in local.items() if value != baseline.get(key)}
    validate_video_combination({**load_settings(path), **changes})
    save_settings(path, changes)
    return load_settings(path)


class ProfileInUseError(RuntimeError):
    """The profile is already held by a launcher operation."""


class ProfileLock:
    """OS-owned lock: released after crashes without touching profile contents."""
    def __init__(self, profile, directory=None):
        identity = os.path.normcase(str(Path(profile).resolve()))
        digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()
        self.path = Path(directory or Path(tempfile.gettempdir()) / 'newsnap-launcher-locks') / f'{digest}.lock'
        self.file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = self.path.open('a+b')
        try:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            stream.close()
            raise ProfileInUseError('Este perfil está en uso por otra expedición o por la actualización del álbum. Espera a que termine antes de continuar.') from error
        self.file = stream
        return self

    def __exit__(self, *args):
        if self.file is not None:
            self.file.close()
            self.file = None


def game_command(root, profile):
    # --boot is the runtime's bounded startup probe: it exits successfully at
    # the first NVN call. Interactive play uses its normal mode instead.
    return [str(runtime_dir(root) / 'newsnap.exe'), '--profile', str(Path(profile))]


def validate_runtime_data(root):
    """Check the release runtime ABI and executable receipt before writing or starting."""
    if not is_release_layout(root):
        return None
    directory = runtime_dir(root)
    message = (f'Actualiza tu carpeta {directory.name} para NewSnap {VERSION} antes de guardar ajustes o iniciar. '
               'Los datos actuales no incluyen un ejecutable compatible y verificado con esta versión del launcher.')
    try:
        with (directory / 'newsnap-game.json').open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError(message)
        metadata = json.loads(raw.decode('utf-8-sig'))
        if (not isinstance(metadata, dict) or type(metadata.get('format')) is not int or metadata['format'] != 1
                or type(metadata.get('runtime_api')) is not int or metadata['runtime_api'] != RUNTIME_API
                or metadata.get('game_version') != '2.0.1'):
            raise ValueError(message)
        capabilities = metadata.get('capabilities')
        required = set(RUNTIME_CAPABILITIES)
        if not isinstance(capabilities, list) or not all(isinstance(value, str) for value in capabilities) or not required.issubset(capabilities):
            raise ValueError(message)
        expected = metadata.get('native_executable_sha256')
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-fA-F]{64}', expected):
            raise ValueError(message)
        digest = hashlib.sha256()
        with (directory / 'newsnap.exe').open('rb') as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b''):
                digest.update(chunk)
        if digest.hexdigest() != expected.lower():
            raise ValueError(message)
        return metadata
    except (OSError, ValueError, TypeError) as error:
        raise ValueError(message) from error


def game_failure_message(code, logfile):
    """Use only the final 64 KiB; never load or expose a complete private log."""
    try:
        with Path(logfile).open('rb') as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 65536))
            tail = stream.read(65536).lower()
    except OSError:
        tail = b''
    if b'snap supersampling allocation failed' in tail:
        return (f'No hubo memoria suficiente para crear las imágenes del supersampling experimental. '
                f'Reduce la escala interna al 100 % en Vídeo → Avanzado y reinicia la expedición. '
                f'Tus ajustes no se han cambiado automáticamente. Registro: {logfile}.')
    return f'El juego terminó con código {code}. Revisa {logfile}.'


def game_environment(environment=None, root=None):
    env = dict(os.environ if environment is None else environment)
    # The launcher is an interactive session, never a continuation of a test script.
    for name in list(env):
        upper = name.upper()
        if (upper.startswith(('AC_INPUT', 'AC_TEST_', 'AC_DUMP', 'AC_FLIGHT', 'AC_SHOTS', 'AC_REC_'))
                or upper in {'NEWSNAP_OODLE_REQUESTS', 'NEWSNAP_OODLE_OUTPUT', 'NEWSNAP_DISPLAY_STATUS',
                             'NEWSNAP_PHOTO_TRACE_DIR', 'NEWSNAP_UPLOAD_TRACE', 'AC_SWKBD_ANSWER',
                             'AC_SWKBD_TEST', 'AC_TRACE', 'AC_PRESENT_SHOT', 'AC_PIPELINE_CACHE', 'AC_SHADER_CACHE'}
                or upper in {'AC_EXEFS', 'AC_ROMFS', 'AC_PROFILE_DIR', 'AC_ROMFS_INDEX'}
                or _key(name) in ENV_UI_OVERRIDES):
            env.pop(name)
    env['AC_GPU'] = 'vulkan'
    env['NEWSNAP_LAUNCHER'] = '1'
    if root is not None and is_release_layout(root):
        root = Path(root)
        translator = root / 'ac_xlate.exe'
        env['AC_XLATE'] = str(translator if translator.is_file() else runtime_dir(root) / 'ac_xlate.exe')
        env['AC_EXEFS'] = str((data_dir(root) / 'exefs').resolve())
        env['AC_ROMFS'] = str((data_dir(root) / 'romfs').resolve())
        env['AC_ROMFS_INDEX'] = str((runtime_dir(root) / 'romfs-index.bin').resolve())
        env['PATH'] = os.pathsep.join(filter(None, (str(root), str(runtime_dir(root)), env.get('PATH', ''))))
    return env


def supervise_game(run_attempt):
    """Restart only on the runtime's reserved launcher protocol exit code."""
    attempt = 1
    while True:
        code = run_attempt(attempt)
        if code != 75:
            return code
        attempt += 1


def preparation_command(root):
    root = Path(root)
    command = ([sys.executable, '--prepare'] if getattr(sys, 'frozen', False) else
               [sys.executable, '-m', 'newsnap', 'prepare', '--build-dir', str(runtime_dir(root))])
    if (shader_library_dir(root) / 'manifest.json').is_file():
        return command + ['--all']
    if all((runtime_dir(root) / name).is_file() for name in ('shader-programs.bin', 'shader-answers.bin')):
        return command
    return None


def shader_preparation_required(root):
    marker = runtime_dir(root) / 'newsnap-game.json'
    try:
        return json.loads(marker.read_text(encoding='utf-8')).get('shader_preparation_required') is True
    except (OSError, ValueError, AttributeError):
        return False


def clear_shader_preparation_required(root):
    marker = runtime_dir(root) / 'newsnap-game.json'
    if shader_preparation_required(root):
        metadata = json.loads(marker.read_text(encoding='utf-8'))
        metadata['shader_preparation_required'] = False
        _atomic_write(marker, (json.dumps(metadata, indent=2) + '\n').encode('utf-8'))


def load_profile(root):
    root = Path(root)
    try:
        record = json.loads(_preferences_path(root).read_text(encoding='utf-8'))
        if not isinstance(record, dict):
            raise ValueError('Invalid launcher preferences')
        data_relative=record.get('profile_data_relative')
        if isinstance(data_relative,str) and data_relative and not Path(data_relative).is_absolute():
            candidate=(data_dir(root)/data_relative).resolve()
            if candidate.is_relative_to(data_dir(root).resolve()):return candidate
        relative = record.get('profile_relative')
        if isinstance(relative, str) and relative and not Path(relative).is_absolute():
            candidate = (root / relative).resolve()
            if candidate.is_relative_to(root.resolve()):
                return candidate
        value = record.get('profile')
        if isinstance(value, str) and value and Path(value).is_absolute():
            return Path(value)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return default_profile(root)


def save_profile(root, profile):
    root, profile = Path(root).resolve(), Path(profile).resolve()
    record = ({'profile_data_relative':profile.relative_to(data_dir(root).resolve()).as_posix()}
              if is_release_layout(root) and profile.is_relative_to(data_dir(root).resolve()) else
              {'profile_relative': profile.relative_to(root).as_posix()} if profile.is_relative_to(root)
              else {'profile': str(profile)})
    _atomic_write(_preferences_path(root), json.dumps(record, ensure_ascii=False).encode('utf-8'))


def _preferences_path(root):
    root = Path(root)
    return runtime_dir(root) / 'launcher.json' if is_release_layout(root) else root / 'build/launcher.json'
