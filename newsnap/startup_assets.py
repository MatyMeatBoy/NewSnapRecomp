"""Prepare optional local assets before starting the game's GPU workload."""
import json
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
