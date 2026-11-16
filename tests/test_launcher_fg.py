"""LAUNCH-FG-01: frame generation can be saved one setting at a time; retired test files leave an installation."""
from pathlib import Path
import tempfile
import unittest

from newsnap import launcher_settings as settings
from newsnap.updater import remove_retired_files


class FrameGenerationSettingsTests(unittest.TestCase):
    def save(self, ini, baseline, **changes):
        values = {**baseline, **changes}
        values.update(settings.NEUTRAL_SETTINGS)
        return settings.save_edited_settings(ini, baseline, values)

    def test_frame_generation_saved_after_the_upscaler_and_read_back(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'newsnap.ini'
            current = self.save(ini, settings.load_settings(ini), upscaling='fsr4')
            # the owner's sequence: the upscaler was saved earlier, now only frame generation changes
            current = self.save(ini, current, frame_gen='fsr')
            self.assertEqual((current['upscaling'], current['frame_gen']), ('fsr4', 'fsr'))
            # and the file reads back the same: one line at a time, frame_gen before or after upscaling
            self.assertEqual(settings.load_settings(ini)['frame_gen'], 'fsr')
            text = ini.read_text(encoding='utf-8')
            lines = text.splitlines()
            lines.sort(key=lambda line: not line.startswith('frame_gen'))   # frame_gen first in its section
            ini.write_text('[display]\n' + '\n'.join(line for line in lines if '=' in line) + '\n', encoding='utf-8')
            self.assertEqual(settings.load_settings(ini)['frame_gen'], 'fsr')

    def test_one_setting_alone_is_not_judged_against_missing_ones(self):
        self.assertEqual(settings.validate_settings({'frame_gen': 'fsr'}), {'frame_gen': 'fsr'})
        self.assertEqual(settings.validate_settings({'upscaling': 'fsr4'}), {'upscaling': 'fsr4'})
        self.assertEqual(settings.validate_settings({'render_scale': '150'}), {'render_scale': '150'})
        # both present: the rule applies
        with self.assertRaises(ValueError):
            settings.validate_settings({'frame_gen': 'fsr', 'upscaling': 'off'})
        with self.assertRaises(ValueError):
            settings.validate_settings({'upscaling': 'fsr4', 'render_scale': '150'})

    def test_whole_combinations(self):
        ok = [{'upscaling': 'fsr3', 'frame_gen': 'fsr'}, {'upscaling': 'fsr4', 'frame_gen': 'fsr'},
              {'upscaling': 'auto', 'frame_gen': 'fsr'}, {'upscaling': 'auto', 'frame_gen': 'fsr', 'render_scale': 'display'},
              {'upscaling': 'auto', 'render_scale': '150'},   # MENU-03: Automatic steps aside above 100 %
              {'upscaling': 'off', 'render_scale': '200'}]
        bad = [{'upscaling': 'off', 'frame_gen': 'fsr'}, {'upscaling': 'dlss', 'frame_gen': 'fsr'},
               {'frame_gen': 'fsr'},                                         # complete: missing upscaler is Original
               {'upscaling': 'fsr4', 'render_scale': '150'},
               {'upscaling': 'auto', 'frame_gen': 'fsr', 'render_scale': '150'}]   # Automatic would be Original there
        for values in ok:
            with self.subTest(ok=values):
                settings.validate_video_combination(values)
        for values in bad:
            with self.subTest(bad=values), self.assertRaises(ValueError):
                settings.validate_video_combination(values)

    def test_a_rejected_combination_is_not_written(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'newsnap.ini'
            base = settings.load_settings(ini)
            with self.assertRaises(ValueError):
                self.save(ini, base, upscaling='off', frame_gen='fsr')   # no upscaler: refused as a whole
            current = settings.load_settings(ini)
            self.assertEqual((current['frame_gen'], current['upscaling']), ('off', 'off'))   # nothing was written (the default)


class RetiredFilesTests(unittest.TestCase):
    def test_shipped_batch_files_go_and_the_players_files_stay(self):
        with tempfile.TemporaryDirectory() as folder:
            install = Path(folder)
            tests = install / 'pruebas-amd'
            tests.mkdir()
            for name in ('1-normal.bat', '_prueba.bat', 'LEEME.txt'):
                (tests / name).write_text('x')
            (install / 'NewSnapLauncher.exe').write_text('launcher')
            self.assertEqual(sorted(remove_retired_files(install)),
                             ['pruebas-amd/1-normal.bat', 'pruebas-amd/LEEME.txt', 'pruebas-amd/_prueba.bat'])
            self.assertFalse(tests.exists())
            self.assertTrue((install / 'NewSnapLauncher.exe').is_file())
            # a file the player added keeps the folder; nothing outside the retired folders is touched
            tests.mkdir()
            (tests / 'old.bat').write_text('x')
            (tests / 'captura.png').write_text('mine')
            (tests / 'sub').mkdir()
            (tests / 'sub' / 'keep.bat').write_text('mine')
            self.assertEqual(remove_retired_files(install), ['pruebas-amd/old.bat'])
            self.assertTrue((tests / 'captura.png').is_file())
            self.assertTrue((tests / 'sub' / 'keep.bat').is_file())
            self.assertEqual(remove_retired_files(install), [])
            self.assertEqual(remove_retired_files(install / 'missing'), [])


    def test_dlss_frame_generation_needs_dlss_as_the_upscaler(self):
        self.assertEqual(settings.validate_settings({'frame_gen': 'dlss'}), {'frame_gen': 'dlss'})
        settings.validate_video_combination({'upscaling': 'dlss', 'frame_gen': 'dlss'})
        settings.validate_video_combination({'upscaling': 'dlss', 'frame_gen': 'dlss', 'upscaling_quality': 'native',
                                             'render_scale': '150'})
        for upscaling in ('off', 'auto', 'fsr3', 'fsr4'):
            with self.assertRaises(ValueError):
                settings.validate_video_combination({'upscaling': upscaling, 'frame_gen': 'dlss'})
        with self.assertRaises(ValueError):
            settings.validate_settings({'frame_gen': 'dlssg'})


if __name__ == '__main__':
    unittest.main()
