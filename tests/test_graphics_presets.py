import unittest
import json
from pathlib import Path
from newsnap import launcher_settings as settings
from newsnap.graphics_presets import PRESETS, apply_preset, matching_preset


class GraphicsPresetTests(unittest.TestCase):
    def test_recomplauncher_appearance_defaults_to_no_overrides(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] / 'recomplauncher.json').read_text(encoding='utf-8'))
        setting = next(item for item in manifest['settings'] if item['id'] == 'appearance')
        self.assertEqual(setting['choices'][0]['args'], [])
        self.assertEqual(setting['choices'][1]['args'],
                         ['--set=' + key + '=' + value for key, value in PRESETS['Aspecto original'].items()])

    def test_original_appearance_is_explicit_and_does_not_change_defaults(self):
        before = dict(settings.DEFAULTS)
        values = dict(before, fps='144', hd_shadows='1', frame_gen='fsr', upscaling='fsr3')
        result = apply_preset(values, 'Aspecto original')
        self.assertEqual(settings.DEFAULTS, before)
        self.assertEqual(values['fps'], '144')
        self.assertEqual(result['fps'], '30')
        for key in ('hd_shadows', 'hd_photos', 'ui_motion', 'tex_pack'):
            self.assertEqual(result[key], '0')
        self.assertEqual(result['frame_gen'], 'off')
        self.assertEqual(result['render_scale'], 'game')
        self.assertEqual(result['aniso'], 'game')
        self.assertEqual(result['color_gamma'], '1')
        self.assertEqual(matching_preset(result), 'Aspecto original')

    def test_levels_are_valid_and_preserve_timing_colour_and_controls(self):
        original = dict(settings.DEFAULTS, fps='30', vk_present='fifo', motion='0', lang='es')
        for mode in ('docked', 'handheld'):
            for name in PRESETS:
                with self.subTest(mode=mode, name=name):
                    values = dict(original, operation_mode=mode)
                    result = apply_preset(values, name)
                    settings.validate_settings(result)
                    for key in values.keys() - set(PRESETS[name]):
                        self.assertEqual(result[key], values[key])
                    self.assertEqual(matching_preset(result), name)
                    self.assertEqual(values, dict(original, operation_mode=mode))

    def test_manual_provider_or_scale_is_custom(self):
        values = apply_preset(settings.DEFAULTS, 'Alto')
        self.assertEqual(matching_preset(dict(values, upscaling='fsr3')), 'Personalizado')
        self.assertEqual(matching_preset(dict(values, render_scale='90')), 'Personalizado')
        with self.assertRaises(ValueError):
            apply_preset(values, 'Unknown')
