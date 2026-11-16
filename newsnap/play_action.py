"""What the launcher's main button says and does, as a pure function of the state of the game data.

The state comes from home_state.state(): `loaded` (the game files are in GameData) and `verified` (a current
verification receipt exists; an update or changed files make it False again). The Home button and the sidebar's pill
both show this, so the label always tells what a press will do.
"""
PLAY, VERIFY, VERIFYING = 'Jugar', 'Verificar', 'Verificando…'


def play_action(state, *, busy=False, verifying=False):
    """Returns {'label', 'action', 'kind', 'enabled'}.

    action: 'load' (no game data: the press opens the «choose data» flow, with the play label as before), 'verify'
    (data present but not verified: the press runs the verification and the button becomes «Jugar» when it ends
    well) or 'play'. kind chooses the look: 'verify' or 'play'. While a verification runs the button is disabled and
    says so; while anything else keeps the launcher busy (a rebuild, the game itself) it keeps its label, disabled.
    """
    loaded, verified = bool(state.get('loaded')), bool(state.get('verified'))
    if verifying:
        return {'label': VERIFYING, 'action': 'verify', 'kind': 'verify', 'enabled': False}
    if not loaded:
        return {'label': PLAY, 'action': 'load', 'kind': 'play', 'enabled': not busy}
    if not verified:
        return {'label': VERIFY, 'action': 'verify', 'kind': 'verify', 'enabled': not busy}
    return {'label': PLAY, 'action': 'play', 'kind': 'play', 'enabled': not busy}
