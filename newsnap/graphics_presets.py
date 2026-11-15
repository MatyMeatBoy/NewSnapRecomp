"""Graphics presets: NewSnap's recommended default and the classic levels; never change colour or input policy."""

PRESETS = {
    'Recomendado': {'render_scale': 'display', 'aniso': '16', 'upscaling': 'off', 'shadow_scale': 'auto',
                    'hd_photos': '1', 'fps': '60', 'window_size': 'auto', 'fullscreen': '1'},
    'Original': {'render_scale': 'game', 'aniso': 'game', 'upscaling': 'off', 'shadow_scale': '1', 'hd_photos': '0'},
    'Bajo': {'render_scale': '70', 'aniso': '2', 'upscaling': 'off', 'shadow_scale': '1', 'hd_photos': '1'},
    'Medio': {'render_scale': '80', 'aniso': '4', 'upscaling': 'off', 'shadow_scale': '1', 'hd_photos': '1'},
    'Alto': {'render_scale': '100', 'aniso': '8', 'upscaling': 'off', 'shadow_scale': '2', 'hd_photos': '1'},
    'Ultra': {'render_scale': 'display', 'aniso': '16', 'upscaling': 'off', 'shadow_scale': '4', 'hd_photos': '1'},
}

DESCRIPTION = ('Recomendado (predeterminado): resolución según la pantalla, anisotrópico 16×, sombras automáticas, '
               'miniaturas de fotos en HD, 60 FPS, ventana automática a pantalla completa. '
               'Original: el juego tal cual (escala, filtrado y sombras originales, miniaturas originales). '
               'Bajo: escala 70 %, 2×. Medio: 80 %, 4×. Alto: 100 %, 8×, sombras 2×. '
               'Ultra: resolución según la pantalla, 16×, sombras 4×. '
               'Bajo a Ultra no cambian el límite de FPS, la ventana ni la presentación. Ninguno toca los colores ni '
               'la lógica del juego. Puedes activar FSR/DLSS después: se indicará Personalizado.')


def apply_preset(values, name):
    if name not in PRESETS:
        raise ValueError('Preset gráfico desconocido')
    return {**values, **PRESETS[name]}


def matching_preset(values):
    return next((name for name, preset in PRESETS.items()
                 if all(values.get(key) == value for key, value in preset.items())), 'Personalizado')
