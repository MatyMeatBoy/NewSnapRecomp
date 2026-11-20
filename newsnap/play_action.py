"""One persistent primary action: load, verify, check/build the local game, then play."""
from .launcher_language import tr

PLAY, VERIFY, VERIFYING = 'Jugar', 'Verificar', 'Verificando…'


def play_action(state, *, busy=False, verifying=False):
    """Return a translated label and stable action/kind identifiers; checks and busy work cannot be invoked."""
    loaded, verified = bool(state.get('loaded')), bool(state.get('verified'))
    if verifying:
        return {'label': tr(VERIFYING), 'action': 'verify', 'kind': 'verify', 'enabled': False}
    if not loaded:
        return {'label': tr('Cargar juego…'), 'action': 'load', 'kind': 'play', 'enabled': not busy}
    if not verified:
        return {'label': tr(VERIFY), 'action': 'verify', 'kind': 'verify', 'enabled': not busy}
    if state.get('runtime_checking'):
        return {'label': tr('Comprobando juego…'), 'action': 'check', 'kind': 'verify', 'enabled': False}
    if state.get('needs_build'):
        return {'label': tr('Preparando…') if busy else tr('Construir y jugar'), 'action': 'build', 'kind': 'verify', 'enabled': not busy}
    return {'label': tr(PLAY), 'action': 'play', 'kind': 'play', 'enabled': not busy}
