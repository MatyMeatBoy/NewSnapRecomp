"""Prepare optional local assets before starting the game's GPU workload."""
import json
import re
from .paths import data_dir, runtime_dir
from . import launcher_settings as settings

PROMPT = ('¿Quieres preparar las sombras HD?\n\n'
          'Incluye sombras del escenario y sombras en tiempo real a 4×.\n'
          'Tamaño estimado: hasta 6 GB; primera preparación: unos 35 minutos.\n'
          'Se genera en este PC con tu juego y requiere una descarga inicial de herramientas.\n\n'
          'Si eliges No, jugarás con sombras originales. Podrás activarlas después en Mejoras.')


def prepare_hd_shadows(root, env, report=print, ask=None, explicit=False, cancel=None):
    runtime, data = runtime_dir(root), data_dir(root)
    ini = runtime / 'newsnap.ini'
    selected = env.get('AC_HD_SHADOWS', settings.load_settings(ini)['hd_shadows'])
    env['AC_HD_SHADOWS'] = selected
    if selected != '1':
        return
    from . import game_textures, hdshadows
    folder = runtime / 'hdshadows'
    with settings.ProfileLock(folder):
        image = game_textures.image_key(runtime, data)
        if game_textures.complete(folder, image):
            return
        consent = folder / 'startup-consent.json'
        try:
            accepted = json.loads(consent.read_text(encoding='utf-8')).get('accepted') is True
        except (OSError, ValueError, AttributeError):
            accepted = False
        if not accepted:
            if explicit:
                accepted = True  # Explicit On in RecompLauncher is the player's choice.
            elif ask is not None:
                accepted = bool(ask(PROMPT))
                if not accepted:
                    settings.save_settings(ini, {'hd_shadows': '0'})
            if not accepted:
                env['AC_HD_SHADOWS'] = '0'
                report('HD shadows skipped; original shadows are active. Enable HD shadows in settings to prepare them.')
                return
            folder.mkdir(parents=True, exist_ok=True)
            consent.write_text(json.dumps({'format': 1, 'accepted': True}) + '\n', encoding='utf-8')
        report('HD shadows: preparing all courses before startup (first setup: about 35 minutes, up to 6 GB).')
        hdshadows.ensure_esrgan(report)
        if cancel is not None and cancel.is_set():
            raise RuntimeError('HD shadow preparation cancelled; completed maps are kept for the next start.')
        made, kept, failed = game_textures.install(runtime, data, report=report, cancel=cancel)
        if cancel is not None and cancel.is_set():
            raise RuntimeError('HD shadow preparation cancelled; completed maps are kept for the next start.')
        if failed or not game_textures.complete(folder, image):
            raise RuntimeError('HD shadows incomplete. Retry to resume, or disable HD shadows to play with the originals.')
        report(f'HD shadows ready ({made} generated, {kept} kept).')


HD_WARM_BYTES_PER_PACK = 128 * 1024 * 1024
PACK_DDS = re.compile(r'[0-9a-fA-F]{16}\.dds')


def warm_hd_assets(root, env, report=print, cancel=None):
    """Prime the OS file cache for installed DDS assets before the game opens."""
    runtime = runtime_dir(root)
    buffer = memoryview(bytearray(1024 * 1024))
    totals = []
    reported = False
    pack_override = env.get('AC_TEX_PACK')
    pack_setting = settings.load_settings(runtime / 'newsnap.ini')['tex_pack'] if pack_override is None else pack_override
    for folder, enabled in (('texpack', pack_setting != '0'),
                            ('hdshadows', env.get('AC_HD_SHADOWS') == '1')):
        total = 0
        if enabled:
            for path in sorted((runtime / folder).glob('*.dds')):
                if not PACK_DDS.fullmatch(path.name):
                    continue
                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                    with path.open('rb', buffering=0) as stream:
                        if stream.read(4) != b'DDS ':
                            continue
                        stream.seek(0)
                        if not reported:
                            report('Preparando texturas HD instaladas…')
                            reported = True
                        while total < HD_WARM_BYTES_PER_PACK:
                            if cancel is not None and cancel.is_set():
                                raise RuntimeError('Preparación de texturas HD cancelada.')
                            count = stream.readinto(buffer[:min(len(buffer), HD_WARM_BYTES_PER_PACK - total)])
                            if not count:
                                break
                            total += count
                except OSError:
                    # File warming is optional; the runtime still handles its usual loading path.
                    continue
                if total >= HD_WARM_BYTES_PER_PACK:
                    break
        totals.append(total)
    return tuple(totals)
