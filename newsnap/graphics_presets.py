"""Explicit graphics presets; importing this module never changes saved settings."""

PRESETS = {
    'Recomendado': {'render_scale': 'display', 'aniso': '16', 'upscaling': 'off', 'anti_aliasing': 'high', 'shadow_scale': 'auto',
                    'hd_photos': '1', 'fps': '60', 'window_size': 'auto', 'fullscreen': '1'},
    'Aspecto original': {'render_scale': 'game', 'aniso': 'game', 'upscaling': 'off', 'anti_aliasing': 'off',
                         'shadow_scale': 'auto', 'hd_photos': '0', 'hd_shadows': '0', 'fps': '30',
                         'frame_gen': 'off', 'tex_pack': '0', 'ui_motion': '0', 'sharpness': '0',
                         'color_preset': 'default', 'color_brightness': '0', 'color_contrast': '100',
                         'color_saturation': '100', 'color_gamma': '1'},
    'Original': {'render_scale': 'game', 'aniso': 'game', 'upscaling': 'off', 'anti_aliasing': 'off', 'shadow_scale': 'auto', 'hd_photos': '0'},
    'Bajo': {'render_scale': '70', 'aniso': '2', 'upscaling': 'off', 'anti_aliasing': 'low', 'shadow_scale': 'auto', 'hd_photos': '1'},
    'Medio': {'render_scale': '80', 'aniso': '4', 'upscaling': 'off', 'anti_aliasing': 'medium', 'shadow_scale': 'auto', 'hd_photos': '1'},
    'Alto': {'render_scale': '100', 'aniso': '8', 'upscaling': 'off', 'anti_aliasing': 'high', 'shadow_scale': 'auto', 'hd_photos': '1'},
    'Ultra': {'render_scale': 'display', 'aniso': '16', 'upscaling': 'off', 'anti_aliasing': 'ultra', 'shadow_scale': 'auto', 'hd_photos': '1'},
}

DESCRIPTION = ('Recomendado (predeterminado): resolución según la pantalla, antialiasing SMAA Alto, sin escalador, anisotrópico 16×, sombras automáticas, '
               'miniaturas de fotos en HD, 60 FPS, ventana automática a pantalla completa. '
               'Aspecto original (opcional): 30 FPS, resolución y filtrado del juego, sin mejoras HD, '
               'generación de fotogramas ni interpolación de menús; color neutro. No cambia los valores predeterminados. '
               'Original: escala y filtrado del juego, sin antialiasing añadido, miniaturas originales. '
               'Bajo: escala 70 %, 2×, SMAA Bajo. Medio: 80 %, 4×, SMAA Medio. Alto: 100 %, 8×, SMAA Alto. '
               'Ultra: resolución según la pantalla, 16×, SMAA Ultra. '
               'Bajo a Ultra no cambian el límite de FPS, la ventana, la presentación ni los colores. Ninguno cambia '
               'la lógica del juego. Puedes activar FSR/DLSS después: se indicará Personalizado.')


def apply_preset(values, name):
    if name not in PRESETS:
        raise ValueError('Preset gráfico desconocido')
    return {**values, **PRESETS[name]}


def matching_preset(values):
    return next((name for name, preset in PRESETS.items()
                 if all(values.get(key) == value for key, value in preset.items())), 'Personalizado')
