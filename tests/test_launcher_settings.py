"""Launcher configuration contracts: preserve native settings and isolate test input."""
import tempfile
import os
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
from newsnap import launcher_settings as settings
from newsnap.upstream import ROOT, UPSTREAM
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES


class LauncherSettingsTests(unittest.TestCase):
    def test_runtime_data_requires_current_abi_capabilities_and_native_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertIsNone(settings.validate_runtime_data(root))
            data = root / 'newsnapGameData'
            data.mkdir()
            native = b'private native fixture, not game content'
            (data / 'newsnap.exe').write_bytes(native)
            marker = data / 'newsnap-game.json'
            valid = {'format': 1, 'runtime_api': RUNTIME_API, 'game_version': '2.0.1',
                     'native_executable_sha256': hashlib.sha256(native).hexdigest(),
                     'runtime_source_revision': 'compatible-different-source-revision',
                     'capabilities': list(RUNTIME_CAPABILITIES)}
            for invalid in ({'format': 1, 'game_version': '2.0.1'}, dict(valid, runtime_api=1),
                            dict(valid, native_executable_sha256='0' * 64), dict(valid, capabilities=['launcher-restart75']),
                            dict(valid, game_version='1.0.0'), [], dict(valid, format=True),
                            dict(valid, capabilities=['launcher-restart75', 'native-render-levels', 'docked-supersampling'])):
                marker.write_text(json.dumps(invalid))
                with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, re.escape(VERSION)):
                    settings.validate_runtime_data(root)
            marker.write_text(json.dumps(valid))
            self.assertEqual(settings.validate_runtime_data(root)['runtime_api'], RUNTIME_API)
            (data / 'newsnap.exe').write_bytes(native + b'tampered')
            with self.assertRaisesRegex(ValueError, re.escape(VERSION)):
                settings.validate_runtime_data(root)

    def test_game_failure_message_reads_only_bounded_log_tail(self):
        with tempfile.TemporaryDirectory() as folder:
            logfile = Path(folder) / 'game.log'
            marker = b'snap supersampling allocation failed'
            logfile.write_bytes(b'x' * (80 * 1024) + marker + b'\n')
            message = settings.game_failure_message(70, logfile)
            self.assertIn('100 %', message)
            self.assertIn('reinicia', message.lower())
            logfile.write_bytes(marker + b'x' * (80 * 1024))
            message = settings.game_failure_message(9, logfile)
            self.assertIn('9', message)
            self.assertNotIn('100 %', message)
            self.assertLess(len(message), 1000)
            self.assertIn('9', settings.game_failure_message(9, Path(folder) / 'missing.log'))

    def test_docked_is_default_and_handheld_persists_at_native_scale(self):
        self.assertEqual(settings.DEFAULTS['operation_mode'], 'docked')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.ini'
            settings.save_settings(path, {'operation_mode': 'handheld', 'render_scale': '90'})
            self.assertEqual(settings.load_settings(path)['operation_mode'], 'handheld')
            self.assertEqual(settings.load_settings(path)['render_scale'], '90')

    def test_experimental_supersampling_requires_tv_in_full_and_partial_edits(self):
        for scale in ('125', '150', '200'):
            with self.subTest(scale=scale):
                self.assertEqual(settings.validate_settings({'operation_mode': 'docked', 'render_scale': scale})['render_scale'], scale)
                with self.assertRaisesRegex(ValueError, 'TV'):
                    settings.validate_settings({'operation_mode': 'handheld', 'render_scale': scale})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.ini'
            settings.save_settings(path, {'operation_mode': 'docked', 'render_scale': '100'})
            baseline = settings.load_settings(path)
            settings.save_settings(path, {'operation_mode': 'handheld'})
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'TV'):
                settings.save_edited_settings(path, baseline, dict(baseline, render_scale='200'))
            self.assertEqual(path.read_bytes(), original)
            settings.save_settings(path, {'operation_mode': 'docked', 'render_scale': '150'})
            baseline = settings.load_settings(path)
            with self.assertRaisesRegex(ValueError, 'TV'):
                settings.save_edited_settings(path, baseline, dict(baseline, operation_mode='handheld'))

    def test_control_catalog_matches_pinned_configuration_metadata(self):
        from newsnap.adapt import adapt_sources
        with tempfile.TemporaryDirectory() as temporary:
            staged = adapt_sources(Path(temporary) / 'source')
            text = (staged / 'runtime/cfg.c').read_text(encoding='utf-8')
        metadata = {name.lower(): (default, choices) for name, default, choices in
                    re.findall(r'\{"([A-Z_]+)", "([^"]*)", "([^"]*)", (?:LIVE|RESTART)\}', text)}
        for key in ('lang', 'pad_layout', 'rumble_strength', 'rumble_curve', 'rumble_triggers',
                    'motion', 'stick_deadzone', 'lstick_deadzone', 'rstick_deadzone', 'mouse_sens', 'perf_overlay'):
            with self.subTest(key=key):
                default, domain = metadata[key]
                self.assertEqual(settings.DEFAULTS[key], default)
                if key in settings.CHOICES:
                    self.assertEqual(set(settings.CHOICES[key]) - {''}, set(domain.split('|')))
                elif key in settings.RANGES:
                    low, high = map(float, domain.split('..'))
                    self.assertEqual(settings.RANGES[key][:2], (low, high))

    def test_explicit_snap_bindings_preserve_native_default_mapping(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang is needed for the real input mapper fixture')
        from newsnap.input_adapt import edits
        source = (UPSTREAM / 'runtime/input_map.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/input_map.c']:
            self.assertEqual(source.count(before), 1)
            source = source.replace(before, after, 1)
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'input_map.c').write_text(source, encoding='utf-8')
            shutil.copyfile(UPSTREAM / 'runtime/input_map.h', folder / 'input_map.h')
            (folder / 'host.h').write_text('void rt_log(const char *, ...);\n')
            (folder / 'cfg.h').write_text('const char *cfg_get(const char *);\ndouble cfg_double(const char *);\n')
            calls = '\n'.join(f'if (!input_map_bind("{key[5:].upper()}", "{value}")) return 2;'
                              for key, value in settings.BINDING_DEFAULTS.items())
            (folder / 'test.c').write_text('''
#include <string.h>
const char *cfg_get(const char *s) { (void)s; return 0; }
double cfg_double(const char *s) { (void)s; return 8; }
void rt_log(const char *s, ...) { (void)s; }
#include "input_map.c"
int main(void) {
 unsigned char keys[ACTION_COUNT][KEY_COUNT]={0}, pads[PAD_LAYOUT_COUNT][ACTION_COUNT][PAD_COUNT]={0};
 for(int i=0;i<input_map.nkeys;i++) keys[input_map.keys[i].action][input_map.keys[i].key]=1;
 for(int l=0;l<PAD_LAYOUT_COUNT;l++) for(int i=0;i<input_map.npads[l];i++)
  pads[l][input_map.pads[l][i].action][input_map.pads[l][i].pad]=1;
''' + calls + '''
 for(int a=0;a<ACTION_COUNT;a++) {
  uint8_t actual_keys[INPUT_BINDING_MAX], actual_pads[INPUT_PAD_BINDING_MAX];
  unsigned char got_keys[KEY_COUNT]={0};
  int n=input_map_keys_of(&input_map,a,actual_keys,INPUT_BINDING_MAX);
  for(int i=0;i<n;i++) got_keys[actual_keys[i]]=1;
  if(memcmp(got_keys,keys[a],KEY_COUNT)) return 3;
  for(int l=0;l<PAD_LAYOUT_COUNT;l++) {
   unsigned char got_pads[PAD_COUNT]={0};
   n=input_map_pads_of(&input_map,a,l,actual_pads,INPUT_PAD_BINDING_MAX);
   for(int i=0;i<n;i++) got_pads[actual_pads[i]]=1;
   if(memcmp(got_pads,pads[l][a],PAD_COUNT)) return 4;
  }
 }
 return 0;
}
''', encoding='utf-8')
            exe = folder / ('bindings.exe' if os.name == 'nt' else 'bindings')
            subprocess.run([compiler, str(folder / 'test.c'), '-o', str(exe),
                            *([] if os.name == 'nt' else ['-lm'])], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_gamedata_commands_profile_and_public_runtime_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'GameData'
            data.mkdir()
            (data / 'newsnap-game.json').write_text('{}')
            libraries = data / 'shader-libraries'
            libraries.mkdir()
            (libraries / 'manifest.json').write_text('{}')
            self.assertEqual(settings.game_command(root, data / 'profile'),
                             [str(data / 'newsnap.exe'), '--profile', str(data / 'profile'), '--boot'])
            self.assertEqual(settings.load_profile(root), data / 'profile')
            self.assertEqual(settings.preparation_command(root),
                             [sys.executable, '-m', 'newsnap', 'prepare', '--build-dir', str(data), '--all'])
            with patch.object(sys, 'frozen', True, create=True):
                self.assertEqual(settings.preparation_command(root), [sys.executable, '--prepare', '--all'])
            (data / 'ac_xlate.exe').touch()
            env = settings.game_environment({'PATH': 'system'}, root=root)
            self.assertEqual(env['AC_XLATE'], str(data / 'ac_xlate.exe'))
            (root / 'ac_xlate.exe').touch()
            env = settings.game_environment({'PATH': 'system'}, root=root)
            self.assertEqual(env['AC_XLATE'], str(root / 'ac_xlate.exe'))
            self.assertEqual(env['PATH'].split(os.pathsep)[0], str(root))
            self.assertIn('system', env['PATH'].split(os.pathsep))
            settings.save_profile(root, data / 'profile')
            self.assertTrue((data / 'launcher.json').is_file())
            self.assertFalse((root / 'build').exists())
            self.assertEqual(settings.load_profile(root), data / 'profile')

    def test_control_audio_language_settings_and_bindings_roundtrip(self):
        chosen = {'lang': 'es-419', 'pad_layout': 'playstation', 'rumble_strength': '210',
                  'rumble_curve': '0.8', 'rumble_triggers': '1', 'stick_deadzone': '12',
                  'lstick_deadzone': '', 'rstick_deadzone': '15', 'audio_prefill_ms': '35.5',
                  'perf_overlay': 'full', 'bind_a': 'KEY:mouse_l, key:E, pad:south',
                  'bind_rstick_left': 'key:left, key:j', 'bind_y': 'none'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.ini'
            path.write_text('[mods]\npersonal = yes\n')
            settings.save_settings(path, chosen)
            loaded = settings.load_settings(path)
            for key, value in chosen.items():
                self.assertEqual(loaded[key], value)
            self.assertIn('personal = yes', path.read_text())

    def test_binding_validation_matches_physical_key_and_pad_grammar(self):
        for key, value in [('bind_a', 'key:f1'), ('bind_a', 'mouse_l'), ('bind_a', 'key:unknown'),
                           ('bind_a', 'pad:a'), ('bind_rstick_up', 'pad:north'),
                           ('bind_a', 'key:e\nvolume=0'), ('bind_a', 'key:e,' * 50),
                           ('bind_notreal', 'key:e'), ('lang', 'xx'), ('pad_layout', 'steam'),
                           ('rumble_strength', '301'), ('rumble_curve', '0.19'), ('rumble_triggers', '2'),
                           ('lstick_deadzone', '51'), ('rstick_deadzone', '-1'), ('audio_prefill_ms', '501')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                settings.validate_settings({key: value})
        for value in ('', 'none', 'key:default,pad:default', 'KEY:mouse_l, pad:rpaddle2', 'key:comma,key:num_add'):
            self.assertEqual(settings.validate_settings({'bind_a': value}), {'bind_a': value})

    def test_existing_binding_text_is_preserved_even_if_legacy_token_is_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.ini'
            path.write_text('[input]\nbind_a = key:e, legacy:custom\n')
            baseline = settings.load_settings(path)
            self.assertEqual(baseline['bind_a'], 'key:e, legacy:custom')
            settings.save_edited_settings(path, baseline, dict(baseline, volume='40'))
            self.assertIn('bind_a = key:e, legacy:custom', path.read_text())
            self.assertEqual(settings.load_settings(path)['volume'], '40')

    def test_internal_profile_follows_moved_application_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            first, moved = Path(folder) / 'original', Path(folder) / 'moved'
            profile = first / 'build/profile'
            settings.save_profile(first, profile)
            first.rename(moved)
            self.assertEqual(settings.load_profile(moved), moved / 'build/profile')

    def test_relative_profile_cannot_escape_application_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'build').mkdir()
            (root / 'build/launcher.json').write_text('{"profile_relative":"../../other-profile"}')
            self.assertEqual(settings.load_profile(root), root / 'build/profile')
            (root / 'build/launcher.json').write_text('[]')
            self.assertEqual(settings.load_profile(root), root / 'build/profile')

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
        for key, value in [('render_scale', '75'), ('render_scale', '250'), ('render_scale', '300'),
                           ('aspect', 'wide'), ('aniso', '3'), ('operation_mode', '4k'),
                           ('sharpness', '101'), ('color_brightness', '-31'), ('color_contrast', '69'),
                           ('color_saturation', '201'), ('color_gamma', 'nan'), ('color_gamma', '1.21')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                settings.validate_settings({key: value})
        for scale in ('game', '50', '60', '70', '80', '90', '100', '125', '150', '200'):
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
                               ('vk_present', 'adaptive'), ('upscaling', 'unknown')]:
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
            self.assertEqual(settings.preparation_command(root),
                             [sys.executable, '-m', 'newsnap', 'prepare', '--build-dir', str(target)])
            manifest = root / 'build/shader-unpack/programs/manifest.json'
            manifest.parent.mkdir(parents=True)
            manifest.touch()
            self.assertEqual(settings.preparation_command(root)[-1], '--all')

    def test_profile_preference_does_not_touch_save_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = root / 'uncreated profile'
            settings.save_profile(root, profile)
            self.assertEqual(settings.load_profile(root), profile)
            self.assertFalse(profile.exists())
            self.assertEqual(settings.load_profile(root / 'fresh'), root / 'fresh/build/profile')
