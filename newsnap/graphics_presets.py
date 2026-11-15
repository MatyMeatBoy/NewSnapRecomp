"""Graphics presets: NewSnap's recommended default and the classic levels; never change colour or input policy."""

PRESETS = {
    'Recomendado': {'render_scale': 'display', 'aniso': '16', 'upscaling': 'off', 'anti_aliasing': 'high', 'shadow_scale': 'auto',
                    'hd_photos': '1', 'fps': '60', 'window_size': 'auto', 'fullscreen': '1'},
    'Original': {'render_scale': 'game', 'aniso': 'game', 'upscaling': 'off', 'anti_aliasing': 'off', 'shadow_scale': 'auto', 'hd_photos': '0'},
    'Bajo': {'render_scale': '70', 'aniso': '2', 'upscaling': 'off', 'anti_aliasing': 'low', 'shadow_scale': 'auto', 'hd_photos': '1'},
    'Medio': {'render_scale': '80', 'aniso': '4', 'upscaling': 'off', 'anti_aliasing': 'medium', 'shadow_scale': 'auto', 'hd_photos': '1'},
    'Alto': {'render_scale': '100', 'aniso': '8', 'upscaling': 'off', 'anti_aliasing': 'high', 'shadow_scale': 'auto', 'hd_photos': '1'},
    'Ultra': {'render_scale': 'display', 'aniso': '16', 'upscaling': 'off', 'anti_aliasing': 'ultra', 'shadow_scale': 'auto', 'hd_photos': '1'},
}

DESCRIPTION = ('Recomendado (predeterminado): resolución según la pantalla, antialiasing SMAA Alto, sin escalador, anisotrópico 16×, sombras automáticas, '
               'miniaturas de fotos en HD, 60 FPS, ventana automática a pantalla completa. '
               'Original: el juego tal cual (escala, filtrado y sombras originales, miniaturas originales). '
               'Bajo: escala 70 %, 2×, SMAA Bajo. Medio: 80 %, 4×, SMAA Medio. Alto: 100 %, 8×, SMAA Alto. '
               'Ultra: resolución según la pantalla, 16×, SMAA Ultra. '
               'Bajo a Ultra no cambian el límite de FPS, la ventana ni la presentación. Ninguno toca los colores ni '
               'la lógica del juego. Puedes activar FSR/DLSS después: se indicará Personalizado.')


def apply_preset(values, name):
    if name not in PRESETS:
        raise ValueError('Preset gráfico desconocido')
    return {**values, **PRESETS[name]}


def matching_preset(values):
    return next((name for name, preset in PRESETS.items()
                 if all(values.get(key) == value for key, value in preset.items())), 'Personalizado')
