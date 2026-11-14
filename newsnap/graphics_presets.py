"""Explicit scene-quality levels; never change pacing, colour or input policy."""

PRESETS = {
    'Original': {'render_scale': 'game', 'aniso': 'game', 'upscaling': 'off'},
    'Bajo': {'render_scale': '70', 'aniso': '2', 'upscaling': 'off'},
    'Medio': {'render_scale': '80', 'aniso': '4', 'upscaling': 'off'},
    'Alto': {'render_scale': '100', 'aniso': '8', 'upscaling': 'off'},
    'Ultra': {'render_scale': '100', 'aniso': '16', 'upscaling': 'off'},
}

DESCRIPTION = ('Original: escala y filtrado del juego. Bajo: escala 70 %, anisotrópico 2×. '
               'Medio: 80 %, 4×. Alto: 100 %, 8×. Ultra: 100 %, 16×. '
               'La escala afecta a cada dimensión de la escena, no al HUD. '
               'Todos desactivan la reconstrucción temporal y conservan el modo TV/portátil, '
               'los colores, el límite de FPS y la presentación. No cambian sombras ni efectos '
               'del juego. Puedes activar FSR/DLSS después: se indicará Personalizado. '
               'No se selecciona supersampling experimental automáticamente.')


def apply_preset(values, name):
    if name not in PRESETS:
        raise ValueError('Preset gráfico desconocido')
    return {**values, **PRESETS[name]}


def matching_preset(values):
    return next((name for name, preset in PRESETS.items()
                 if all(values.get(key) == value for key, value in preset.items())), 'Personalizado')
