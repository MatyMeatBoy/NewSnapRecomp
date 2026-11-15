import unittest
from newsnap import launcher_settings as settings
from newsnap.graphics_presets import PRESETS, apply_preset, matching_preset


class GraphicsPresetTests(unittest.TestCase):
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
