"""Launcher configuration contracts: preserve native settings and isolate test input."""
import tempfile
import unittest
from pathlib import Path
from newsnap import launcher_settings as settings


class LauncherSettingsTests(unittest.TestCase):
    def test_legacy_anisotropy_is_shown_and_preserved_until_edited(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.ini'
            original = '[display]\naniso = auto\n'
            path.write_text(original)
            baseline = settings.load_settings(path)
            self.assertEqual(baseline['aniso'], 'auto')
            settings.save_edited_settings(path, baseline, dict(baseline))
            self.assertEqual(path.read_text(), original)
            settings.save_edited_settings(path, baseline, dict(baseline, aniso='16'))
            self.assertEqual(settings.load_settings(path)['aniso'], '16')

    def test_restart_supervisor_holds_profile_lock_until_final_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            exits = iter((75, 75, 0))
            attempts = []
            def run_attempt(number):
                attempts.append(number)
                with self.assertRaises(RuntimeError):
                    with settings.ProfileLock(folder / 'profile', folder / 'locks'):
                        self.fail('profile unlocked during restart')
                return next(exits)
            with settings.ProfileLock(folder / 'profile', folder / 'locks'):
                self.assertEqual(settings.supervise_game(run_attempt), 0)
            self.assertEqual(attempts, [1, 2, 3])
            with settings.ProfileLock(folder / 'profile', folder / 'locks'):
                pass

    def test_restart_supervisor_does_not_retry_other_exit_codes(self):
        exits, attempts = iter((75, 9)), []
        def run_attempt(number):
            attempts.append(number)
            return next(exits)
        self.assertEqual(settings.supervise_game(run_attempt), 9)
        self.assertEqual(attempts, [1, 2])

    def test_detailed_video_settings_roundtrip_and_preserve_unrelated_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            path.write_text('[display]\nfov = 105\n[mods]\ncustom = keep\n')
            chosen = {'operation_mode': 'handheld', 'render_scale': '70', 'upscaler': 'bilinear',
                      'sharpness': '65', 'aniso': '16', 'color_preset': 'custom',
                      'color_brightness': '-12', 'color_contrast': '125', 'color_saturation': '140',
                      'color_gamma': '1.1', 'aspect': 'stretch', 'vk_present': 'fifo_relaxed',
                      'window_size': '3440x1440'}
            settings.save_settings(path, chosen)
            current = settings.load_settings(path)
            for key, value in chosen.items():
                self.assertEqual(current[key], value)
            self.assertIn('fov = 105', path.read_text())
            self.assertIn('custom = keep', path.read_text())

    def test_video_presets_write_real_color_adjustments(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            settings.save_settings(path, {'color_preset': 'vivid'})
            current = settings.load_settings(path)
            self.assertEqual([current[key] for key in ('color_brightness', 'color_contrast', 'color_saturation', 'color_gamma')],
                             ['0', '115', '135', '0.95'])
            settings.save_settings(path, {'color_preset': 'clarity'})
            current = settings.load_settings(path)
            self.assertEqual([current[key] for key in ('color_brightness', 'color_contrast', 'color_saturation', 'color_gamma')],
                             ['2', '110', '115', '1'])

    def test_video_rejects_donor_scales_and_out_of_range_color(self):
        for key, value in [('render_scale', '75'), ('render_scale', '125'), ('render_scale', '200'),
                           ('aspect', 'wide'), ('aniso', '3'), ('operation_mode', '4k'),
                           ('sharpness', '101'), ('color_brightness', '-31'), ('color_contrast', '69'),
                           ('color_saturation', '201'), ('color_gamma', 'nan'), ('color_gamma', '1.21')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                settings.validate_settings({key: value})
        for scale in ('game', '50', '60', '70', '80', '90', '100'):
            self.assertEqual(settings.validate_settings({'render_scale': scale}), {'render_scale': scale})

    def test_external_game_settings_survive_launcher_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            path.write_text('[audio]\nvolume = 80\n[input]\nmouse_sens = 1\n')
            baseline = settings.load_settings(path)
            local = dict(baseline, mouse_sens='2')
            settings.save_settings(path, {'volume': '40'})
            current = settings.save_edited_settings(path, baseline, local)
            self.assertEqual(current['volume'], '40')
            self.assertEqual(current['mouse_sens'], '2')
            self.assertEqual(settings.load_settings(path)['volume'], '40')

    def test_reloading_keeps_intentional_local_edit_and_external_changes(self):
        baseline = {'volume': '80', 'mouse_sens': '1', 'motion': '1'}
        local = dict(baseline, mouse_sens='2')
        external = dict(baseline, volume='40', mouse_sens='3', motion='0')
        self.assertEqual(settings.merge_settings(baseline, local, external),
                         {'volume': '40', 'mouse_sens': '2', 'motion': '0'})

    def test_no_local_edit_does_not_rewrite_or_create_ini(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            baseline = settings.load_settings(path)
            settings.save_edited_settings(path, baseline, baseline)
            self.assertFalse(path.exists())
            path.write_bytes(b'; leave format intact\r\n[audio]\r\nvolume=80')
            baseline = settings.load_settings(path)
            before = path.stat().st_mtime_ns
            settings.save_edited_settings(path, baseline, baseline)
            self.assertEqual(path.read_bytes(), b'; leave format intact\r\n[audio]\r\nvolume=80')
            self.assertEqual(path.stat().st_mtime_ns, before)

    def test_diagnostic_environment_is_cleared_but_preferences_survive(self):
        env = settings.game_environment({'NEWSNAP_OODLE_REQUESTS': 'decode.bin', 'NEWSNAP_OODLE_OUTPUT': 'out',
            'AC_SWKBD_ANSWER': 'test', 'AC_SHOTS': '1', 'AC_SHOTS_DIR': 'shots', 'AC_PIPELINE_CACHE': 'test.bin',
            'AC_SHADER_CACHE': 'test', 'AC_TRACE': 'all', 'AC_DUMP_DIR': 'dump', 'AC_MOTION': '0',
            'AC_LANG': 'es', 'AC_BIND_A': 'Space', 'AC_RUMBLE_STRENGTH': '90', 'AC_SHADER_MEMO': '1'})
        self.assertEqual(env, {'AC_LANG': 'es', 'AC_BIND_A': 'Space', 'AC_RUMBLE_STRENGTH': '90',
                               'AC_SHADER_MEMO': '1', 'AC_GPU': 'vulkan', 'NEWSNAP_LAUNCHER': '1'})

    def test_profile_lock_rejects_same_profile_until_released(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            with settings.ProfileLock(folder / 'profile', folder / 'locks'):
                with self.assertRaises(RuntimeError):
                    with settings.ProfileLock(folder / 'profile', folder / 'locks'):
                        self.fail('same profile acquired twice')
                with settings.ProfileLock(folder / 'other-profile', folder / 'locks'):
                    pass
            with settings.ProfileLock(folder / 'profile', folder / 'locks'):
                pass
            self.assertFalse((folder / 'profile').exists())

    def test_update_preserves_unknown_lines_comments_and_case_aliases(self):
        original = '; personal\r\n[display]\r\nAC_FULLSCREEN = 0\r\ncustom = keep\r\n[input]\r\nmouse_sens = 1\r\n[other]\r\ncheat = abc\r\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            path.write_bytes(original.encode())
            settings.save_settings(path, {'fullscreen': '1', 'mouse_sens': '2.5', 'fps': '30'})
            result = path.read_bytes().decode()
            self.assertIn('; personal\r\n', result)
            self.assertIn('custom = keep\r\n', result)
            self.assertIn('[other]\r\ncheat = abc\r\n', result)
            self.assertEqual(settings.load_settings(path)['fullscreen'], '1')
            self.assertEqual(settings.load_settings(path)['fps'], '30')
            self.assertNotIn('\nfullscreen = ', result)

    def test_invalid_values_leave_file_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            path.write_text('[audio]\nvolume = 72\n')
            original = path.read_bytes()
            for key, value in [('fps', '120'), ('volume', '101'), ('mouse_sens', 'nan'),
                               ('mouse_sens', '-1'), ('motion', 'yes'), ('window_size', '0x720'),
                               ('vk_present', 'adaptive'), ('upscaling', 'dlss')]:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    settings.save_settings(path, {key: value})
                self.assertEqual(path.read_bytes(), original)

    def test_native_duplicate_keys_are_updated_even_across_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'astralchain.ini'
            path.write_text('[display]\nfullscreen=0\n[custom]\nAC_FULLSCREEN=0\n')
            settings.save_settings(path, {'fullscreen': '1'})
            self.assertEqual(settings.load_settings(path)['fullscreen'], '1')
            self.assertEqual(path.read_text().count('= 1'), 2)

    def test_launch_uses_explicit_profile_and_no_injected_input(self):
        root = Path('example root').resolve()
        command = settings.game_command(root, root / 'my profile')
        self.assertEqual(command, [str(root / 'build/updated/newsnap.exe'), '--profile', str(root / 'my profile'), '--boot'])
        env = settings.game_environment({'PATH': 'system', 'AC_INPUT': 'script', 'AC_INPUT_SCRIPT': 'x',
                                         'AC_FULLSCREEN': '0', 'AC_TEST_PAD': '1', 'AC_GPU': 'null',
                                         'AC_EXEFS': 'old computer', 'AC_ROMFS': 'old game'})
        self.assertEqual(env['PATH'], 'system')
        self.assertNotIn('AC_INPUT', env)
        self.assertNotIn('AC_INPUT_SCRIPT', env)
        self.assertNotIn('AC_FULLSCREEN', env)
        self.assertNotIn('AC_TEST_PAD', env)
        self.assertNotIn('AC_EXEFS', env)
        self.assertNotIn('AC_ROMFS', env)
        self.assertEqual(env['AC_GPU'], 'vulkan')
        self.assertEqual(env['NEWSNAP_LAUNCHER'], '1')

    def test_preparation_selects_library_then_observed_then_none(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertIsNone(settings.preparation_command(root))
            target = root / 'build/updated'
            target.mkdir(parents=True)
            (target / 'shader-programs.bin').touch()
            self.assertIsNone(settings.preparation_command(root))
            (target / 'shader-answers.bin').touch()
            self.assertEqual(settings.preparation_command(root)[-1], 'prepare')
            manifest = root / 'build/shader-unpack/programs/manifest.json'
            manifest.parent.mkdir(parents=True)
            manifest.touch()
            self.assertEqual(settings.preparation_command(root)[-2:], ['prepare', '--all'])

    def test_profile_preference_does_not_touch_save_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = root / 'uncreated profile'
            settings.save_profile(root, profile)
            self.assertEqual(settings.load_profile(root), profile)
            self.assertFalse(profile.exists())
            self.assertEqual(settings.load_profile(root / 'fresh'), root / 'fresh/build/profile')
