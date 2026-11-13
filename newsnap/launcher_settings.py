"""Safe, narrow edits to the runtime INI and local launcher preferences."""
import json
import hashlib
import math
import os
from pathlib import Path
import re
import sys
import tempfile

DEFAULTS = {'fullscreen': '1', 'window_size': '1920x1080', 'vk_present': 'mailbox',
            'fps': '60', 'volume': '100', 'mouse_sens': '1', 'motion': '1',
            'operation_mode': 'docked', 'render_scale': 'game', 'upscaler': 'fsr',
            'sharpness': '80', 'aniso': 'game', 'aspect': 'fit', 'color_preset': 'default',
            'color_brightness': '0', 'color_contrast': '100', 'color_saturation': '100', 'color_gamma': '1'}
SECTIONS = {'fullscreen': 'display', 'window_size': 'display', 'vk_present': 'display',
            'fps': 'frame rate', 'volume': 'audio', 'mouse_sens': 'input', 'motion': 'input',
            'operation_mode': 'language', **{key: 'display' for key in DEFAULTS if key not in
                ('fullscreen', 'window_size', 'vk_present', 'fps', 'volume', 'mouse_sens', 'motion', 'operation_mode')}}
# Same four actual colour adjustments as runtime/ui/menu.cpp; the preset name alone has no visual effect.
COLOR_KEYS = ('color_brightness', 'color_contrast', 'color_saturation', 'color_gamma')
COLOR_PRESETS = {name: dict(zip(COLOR_KEYS, values)) for name, values in {
    'default': ('0', '100', '100', '1'), 'vivid': ('0', '115', '135', '0.95'),
    'clarity': ('2', '110', '115', '1')}.items()}
CHOICES = {'vk_present': ('mailbox', 'fifo', 'immediate', 'fifo_relaxed'),
           'operation_mode': ('docked', 'handheld'), 'render_scale': ('game', '50', '60', '70', '80', '90', '100'),
           'upscaler': ('fsr', 'bilinear'), 'aniso': ('game', '2', '4', '8', '16', 'auto'),
           'aspect': ('fit', 'stretch'), 'color_preset': ('default', 'vivid', 'clarity', 'custom')}
RANGES = {'volume': (0, 100, True), 'mouse_sens': (0, 10, False), 'sharpness': (0, 100, True),
          'color_brightness': (-30, 30, True), 'color_contrast': (70, 150, True),
          'color_saturation': (50, 200, True), 'color_gamma': (0.8, 1.2, False)}
ENTRY = re.compile(r'^(\s*)((?:AC_)?[A-Za-z_0-9]+)\s*=.*$', re.IGNORECASE)


def _key(value):
    return value.lower().removeprefix('ac_')


def validate_settings(values):
    result = {}
    for key, raw in values.items():
        value = str(raw).strip()
        valid = False
        if key in ('fullscreen', 'motion'):
            valid = value in ('0', '1')
        elif key == 'fps':
            valid = value in ('30', '60')
        elif key in CHOICES:
            valid = value in CHOICES[key]
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
    return result


def load_settings(path):
    result = dict(DEFAULTS)
    path = Path(path)
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match = ENTRY.match(line)
            if match and (key := _key(match[2])) in DEFAULTS:
                value = line.split('=', 1)[1].strip().strip('"')
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
    raw = path.read_bytes() if path.is_file() else b''
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
    return [str(Path(root) / 'build/updated/newsnap.exe'), '--profile', str(Path(profile)), '--boot']


def game_environment(environment=None):
    env = dict(os.environ if environment is None else environment)
    # The launcher is an interactive session, never a continuation of a test script.
    for name in list(env):
        upper = name.upper()
        if (upper.startswith(('AC_INPUT', 'AC_TEST_', 'AC_DUMP', 'AC_FLIGHT', 'AC_SHOTS', 'AC_REC_'))
                or upper in {'NEWSNAP_OODLE_REQUESTS', 'NEWSNAP_OODLE_OUTPUT', 'AC_SWKBD_ANSWER',
                             'AC_SWKBD_TEST', 'AC_TRACE', 'AC_PRESENT_SHOT', 'AC_PIPELINE_CACHE', 'AC_SHADER_CACHE'}
                or upper in {'AC_EXEFS', 'AC_ROMFS', 'AC_PROFILE_DIR', 'AC_ROMFS_INDEX'}
                or _key(name) in DEFAULTS):
            env.pop(name)
    env['AC_GPU'] = 'vulkan'
    env['NEWSNAP_LAUNCHER'] = '1'
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
    command = [sys.executable, '-m', 'newsnap', 'prepare']
    if (root / 'build/shader-unpack/programs/manifest.json').is_file():
        return command + ['--all']
    if all((root / 'build/updated' / name).is_file() for name in ('shader-programs.bin', 'shader-answers.bin')):
        return command
    return None


def load_profile(root):
    root = Path(root)
    try:
        value = json.loads((root / 'build/launcher.json').read_text(encoding='utf-8'))['profile']
        if isinstance(value, str) and value and Path(value).is_absolute():
            return Path(value)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return root / 'build/profile'


def save_profile(root, profile):
    _atomic_write(Path(root) / 'build/launcher.json',
                  json.dumps({'profile': str(Path(profile).resolve())}, ensure_ascii=False).encode('utf-8'))
