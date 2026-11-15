"""Internal-resolution choices fitted to the player's display (REL-097): the launcher's list shows what each step
draws on this monitor, marks the step that matches it and leaves out the supersampling steps beyond twice the
display's height, which cost GPU time without showing more detail once reduced to the window."""
import os

BELOW = (50, 60, 70, 80, 90)
ABOVE = (125, 133, 150, 175, 200, 250, 300)
GAME_HEIGHT = 1080


def primary_display_size():
    """(width, height) of the primary display in physical pixels, or None when it cannot be read."""
    if os.name != 'nt':
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class DEVMODEW(ctypes.Structure):
            _fields_ = [('dmDeviceName', wintypes.WCHAR * 32), ('dmSpecVersion', wintypes.WORD),
                        ('dmDriverVersion', wintypes.WORD), ('dmSize', wintypes.WORD),
                        ('dmDriverExtra', wintypes.WORD), ('dmFields', wintypes.DWORD),
                        ('dmPositionX', wintypes.LONG), ('dmPositionY', wintypes.LONG),
                        ('dmDisplayOrientation', wintypes.DWORD), ('dmDisplayFixedOutput', wintypes.DWORD),
                        ('dmColor', ctypes.c_short), ('dmDuplex', ctypes.c_short),
                        ('dmYResolution', ctypes.c_short), ('dmTTOption', ctypes.c_short),
                        ('dmCollate', ctypes.c_short), ('dmFormName', wintypes.WCHAR * 32),
                        ('dmLogPixels', wintypes.WORD), ('dmBitsPerPel', wintypes.DWORD),
                        ('dmPelsWidth', wintypes.DWORD), ('dmPelsHeight', wintypes.DWORD),
                        ('dmDisplayFlags', wintypes.DWORD), ('dmDisplayFrequency', wintypes.DWORD)]
        mode = DEVMODEW()
        mode.dmSize = ctypes.sizeof(DEVMODEW)
        if not ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(mode)):   # ENUM_CURRENT_SETTINGS
            return None
        size = int(mode.dmPelsWidth), int(mode.dmPelsHeight)
        return size if size[0] >= 320 and size[1] >= 240 else None
    except Exception:
        return None


def _height(scale):
    return 1440 if scale == 133 else round(GAME_HEIGHT * scale / 100)   # 133 % is the 4/3 step: 1440p


def render_scale_choices(display_height=None, current=None):
    """{label: value} for the launcher's «Resolución interna» list. Without a known display every step is shown with
    its drawn height. With one, the step whose height matches the display is marked and steps above twice its height
    are left out; the current value always stays in the list."""
    known = isinstance(display_height, int) and 240 <= display_height <= 8640
    match = None
    if known and display_height > GAME_HEIGHT:
        match = min(ABOVE, key=lambda n: abs(_height(n) - display_height))
    choices = {}
    for n in BELOW:
        choices[f'{n} % · {_height(n)}p' + (' · más ligero' if n == 50 else '')] = str(n)
    choices[f'100 % · {GAME_HEIGHT}p · la del juego' + (' · tu pantalla' if known and display_height == GAME_HEIGHT else '')] = 'game'
    for n in ABOVE:
        if known and _height(n) > 2 * display_height and str(n) != current:
            continue
        label = f'{n} % · {_height(n)}p'
        if n == match:
            label += ' · tu pantalla'
        elif n == max(ABOVE):
            label += ' · más nítido'
        choices[label] = str(n)
    choices['Según la pantalla' + (f' · {display_height}p' if known else '')] = 'display'
    return choices
