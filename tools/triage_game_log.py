"""Classify how a game session ended from its launcher log (KEYBOARD-CRASH).

The launcher writes each session to GameData/logs/launcher-game-<session>-NNN.log.
A game started directly (without the launcher) writes GameData/logs/astralchain.log
and keeps the previous runs as totk.1.log ... totk.N.log.
This reads one such log (or the newest one in a folder) and answers the question
a "the game closed" report leaves open: host exception, fatal runtime error,
window closed, launcher-requested restart, timed run, or a log with no ending.

Read-only.  The summary redacts user-profile paths and never copies game data;
it is meant to be pasted into a bug report.
"""
import argparse
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 64 << 20
LOG_PATTERNS = ('launcher-game-*.log', 'astralchain.log', 'totk.*.log')
NOISE = re.compile(r'^\[host\] (perf:|fps:|kernel:|vk_rec:|vk_usnap:|frametime|mem:|vk: replay queue|'
                   r'nvn: asynchronous replay|audout: the output ran dry|input: script|photo_trace:|upload_trace|'
                   r'menu: [0-9.]+ ms|dlaa: )')
USER_PATH = re.compile(r'(?i)\b[a-z]:[\\/]+users[\\/]+[^\\/\s"\']+')
FRAME = re.compile(r'\bframe (\d+)\b')
KEYBOARD = re.compile(r'^\[host\] (swkbd:|Snap names:)')
DIALOG = re.compile(r'^\[host\] (err:|nifm:|account:|friends:|album:)')
FOCUS = re.compile(r'^\[host\] gfx: window (gained|lost) the focus')
GPU = re.compile(r'^\[host\] vk: using gpu \d+: (.+)$')
DRIVER = re.compile(r'driver shader cache: \S+ \S+ "([^"]*)"')
SERVICE = re.compile(r'^FATAL: sm: service "([^"]+)" is not implemented')
EXCEPTION = re.compile(r'^FATAL: (.+?) \((0x[0-9a-fA-F]+)\) at host ')
CAPS_DRIVER = re.compile(r'^\[host\] vk caps: .*? driver (.+?) \(id \d+')
PATCHES = re.compile(r'^\[host\] patches: (.+?) \(page ')
RUN_FOLDER = re.compile(r'^\[host\] cfg: (?:read|no settings file at) (.+?)[\\/]astralchain\.ini')
NO_FUNCTION = re.compile(r'^FATAL: rt_dispatch: no function at guest pc \S+ \((\S+?)\)')
# The JPEG encoder of the SDK leaves through longjmp to this setjmp return; runtimes before 0.3 cannot follow it.
JPEG_LONGJMP_SITE = 'sdk+0x273060'

VERDICTS = {
    'excepción-host': (71, 'El proceso terminó por una excepción capturada por el informe de fallos del runtime.'),
    'fatal-runtime': (70, 'El runtime se detuvo a propósito ante una condición que no sabe atender.'),
    'ventana-cerrada': (0, 'La ventana del juego recibió una orden de cierre y el runtime salió ordenadamente.'),
    'reinicio-solicitado': (75, 'El runtime pidió al launcher reiniciar la sesión.'),
    'fin-programado': (0, 'Ejecución de prueba con duración fija que terminó correctamente.'),
    'sin-marca-final': (None, 'El log acaba sin excepción, fatal ni cierre: proceso terminado desde fuera, cuelgue o '
                              'log incompleto.'),
}


def runtime_generation(patch_sets, color_transfer):
    """Which release line a runtime belongs to, from what it prints at start.

    The patch sets changed with the releases: snap_render alone up to 0.1.x,
    snap_supersample from 0.2, snap_random_range from 0.5.  The final colour
    transfer line also exists from 0.5 only.  An inference from the log, not a
    hash of the executable.
    """
    if patch_sets is None:
        return 'desconocida'
    if 'snap_random_range' in patch_sets:
        return '0.5 o posterior'
    if 'snap_supersample' in patch_sets:
        return '0.5 o posterior' if color_transfer else '0.2 a 0.4'
    if 'snap_render' in patch_sets:
        return '0.1.x (anterior a 0.2)'
    return 'desconocida'


def redact(line):
    return USER_PATH.sub('%USERPROFILE%', line)


def newest_log(folder):
    folder = Path(folder)
    logs = [p for pattern in LOG_PATTERNS for p in folder.glob(pattern) if p.is_file()]
    logs.sort(key=lambda p: (p.stat().st_mtime, p.name))
    if not logs:
        raise ValueError(f'No hay ningún log de sesión ({", ".join(LOG_PATTERNS)}) en {folder}')
    return logs[-1]


def read_lines(path):
    path = Path(path)
    size = path.stat().st_size
    with path.open('rb') as stream:
        if size > MAX_BYTES:
            stream.seek(size - MAX_BYTES)
            stream.readline()   # drop the cut line
        data = stream.read(MAX_BYTES)
    return size, data.decode('utf-8', errors='replace').splitlines()


def triage_lines(lines):
    """Classify a session from its log lines; returns a JSON-serialisable dict."""
    report = {'gpu': None, 'driver': None, 'last_frame': None, 'keyboard': [], 'dialogs': [], 'focus': [],
              'fatal': None, 'hints': []}
    fatal_at, closed, restart, passed = None, False, False, False
    patch_sets, color_transfer, folder = None, False, None
    for index, line in enumerate(lines):
        if match := PATCHES.match(line):
            patch_sets = [item.strip().removesuffix(' on') for item in match.group(1).split(',') if item.strip().endswith(' on')]
        if line.startswith('[host] vk: final SDR byte transfer'):
            color_transfer = True
        if folder is None and (match := RUN_FOLDER.match(line)):
            folder = redact(match.group(1))
        if match := CAPS_DRIVER.match(line):
            report['driver'] = match.group(1).strip()
        if match := GPU.match(line):
            report['gpu'] = match.group(1).strip()
        if report['driver'] is None and (match := DRIVER.search(line)):
            report['driver'] = match.group(1)
        if match := FRAME.search(line):
            report['last_frame'] = int(match.group(1))
        if KEYBOARD.match(line):
            report['keyboard'].append(redact(line))
        elif DIALOG.match(line):
            report['dialogs'].append(redact(line))
        elif FOCUS.match(line):
            report['focus'].append(redact(line))
        if line.startswith('FATAL: ') and fatal_at is None:
            fatal_at = index
        if line.startswith('[host] gfx: window closed;'):
            closed, restart = True, 'restarting' in line
        if line.startswith('boot: passed'):
            passed = True
    report['keyboard'] = report['keyboard'][-12:]
    report['dialogs'] = report['dialogs'][-12:]
    report['focus'] = report['focus'][-6:]
    generation = runtime_generation(patch_sets, color_transfer)
    report['runtime'] = {'patch_sets': patch_sets, 'final_color_transfer_line': color_transfer, 'folder': folder,
                         'generation': generation}
    if generation not in ('0.5 o posterior', 'desconocida'):
        report['hints'].append(f'El runtime que escribió este log es de la generación {generation}, no la 0.5: sus '
                               'síntomas no dicen nada del código actual. Comprobar qué ejecutable se inició.')
    if fatal_at is not None:
        block = [redact(line) for line in lines[fatal_at:fatal_at + 80]]
        first = lines[fatal_at]
        fatal = {'message': redact(first), 'block': block}
        if match := EXCEPTION.match(first):
            verdict = 'excepción-host'
            fatal.update(what=match.group(1), code=match.group(2))
            fatal['lifted_function'] = next((redact(line.strip()) for line in block if 'in lifted function' in line), None)
            fatal['guest_frames'] = [redact(line.strip()) for line in block if line.lstrip().startswith('guest frame')][:12]
            if 'reading address' in first or 'writing address' in first:
                report['hints'].append('Acceso a memoria inválido: la primera función «lifted» y los guest frames '
                                       'dicen qué código del juego lo provocó.')
        else:
            verdict = 'fatal-runtime'
            if match := SERVICE.match(first):
                fatal['service'] = match.group(1)
                report['hints'].append(f'El juego abrió el servicio de sistema «{match.group(1)}», que el runtime no '
                                       'implementa: hace falta una respuesta de host para esa función.')
            elif match := NO_FUNCTION.match(first):
                fatal['guest_pc'] = match.group(1)
                if match.group(1) == JPEG_LONGJMP_SITE:
                    fatal['known'] = 'jpeg-longjmp'
                    report['hints'].append('Salida por longjmp del codificador JPEG del SDK al guardar una foto: '
                                           'defecto conocido de los runtimes anteriores a 0.3, corregido con las '
                                           'continuaciones de salto (snap_jump).')
                else:
                    report['hints'].append('Salto indirecto a una dirección que no es inicio de función: posible '
                                           'longjmp, corrutina o puntero de función dañado.')
            elif first.startswith('FATAL: ipc:') or first.startswith('FATAL: svc'):
                report['hints'].append('Llamada de sistema o comando IPC sin implementar en el runtime.')
            elif 'ShowKeyboard' in first:
                report['hints'].append('Fallo dentro de la ventana de entrada de texto del host.')
        report['fatal'] = fatal
    elif closed:
        verdict = 'reinicio-solicitado' if restart else 'ventana-cerrada'
        if report['keyboard'] and not restart:
            report['hints'].append('Hubo entrada de texto en la sesión: comprobar si el cierre de ventana llegó '
                                   'justo después de la última línea «swkbd».')
    elif passed:
        verdict = 'fin-programado'
    else:
        verdict = 'sin-marca-final'
    report['verdict'] = verdict
    report['expected_exit_code'], report['meaning'] = VERDICTS[verdict]
    meaningful = [redact(line) for line in lines if line.strip() and not NOISE.match(line)]
    report['tail'] = meaningful[-30:]
    return report


def triage(path):
    path = Path(path)
    if path.is_dir():
        path = newest_log(path)
    size, lines = read_lines(path)
    report = triage_lines(lines)
    report.update(file=path.name, bytes=size, lines=len(lines))
    return report


def render(report):
    out = [f"Log: {report['file']} ({report['bytes']} bytes, {report['lines']} líneas)",
           f"Veredicto: {report['verdict']} — {report['meaning']}",
           f"Código de salida esperado: {report['expected_exit_code']}",
           f"GPU: {report['gpu'] or 'desconocida'} · driver: {report['driver'] or 'desconocido'} · "
           f"último frame citado: {report['last_frame']}",
           f"Runtime: generación {report['runtime']['generation']} · parches {report['runtime']['patch_sets']} · "
           f"carpeta {report['runtime']['folder'] or 'desconocida'}"]
    for hint in report['hints']:
        out.append(f'Pista: {hint}')
    if report['fatal']:
        out += ['', '--- bloque fatal ---'] + report['fatal']['block'][:45]
    for title, key in (('teclado', 'keyboard'), ('diálogos y servicios', 'dialogs'), ('foco de ventana', 'focus')):
        if report[key]:
            out += ['', f'--- {title} ---'] + report[key]
    out += ['', '--- últimas líneas relevantes ---'] + report['tail']
    return '\n'.join(out) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('log', type=Path, help='log de sesión o la carpeta GameData/logs (elige el más reciente)')
    parser.add_argument('--json', action='store_true', help='salida JSON en lugar de texto')
    args = parser.parse_args(argv)
    try:
        report = triage(args.log)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=1) + '\n' if args.json else render(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
