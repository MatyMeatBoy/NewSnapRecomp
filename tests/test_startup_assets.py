from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from newsnap import launcher_settings as settings


class StartupAssetsTests(unittest.TestCase):
    def test_hd_shadows_default_on_and_explicit_off_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            ini = Path(temporary) / 'newsnap.ini'
            self.assertEqual(settings.load_settings(ini)['hd_shadows'], '1')
            ini.write_text('[display]\nHD_SHADOWS=0\n')
            self.assertEqual(settings.load_settings(ini)['hd_shadows'], '0')

    def test_prepares_missing_maps_once_and_skips_completed_or_disabled(self):
        from newsnap.startup_assets import prepare_hd_shadows
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch('newsnap.game_textures.image_key', return_value='image'), \
                 patch('newsnap.game_textures.complete', side_effect=[False, True, True]), \
                 patch('newsnap.game_textures.install', return_value=(4, 1, 0)) as install, \
                 patch('newsnap.hdshadows.ensure_esrgan') as tools:
                prepare_hd_shadows(root, {'AC_HD_SHADOWS': '1'}, explicit=True)
                prepare_hd_shadows(root, {'AC_HD_SHADOWS': '1'}, explicit=True)
                prepare_hd_shadows(root, {'AC_HD_SHADOWS': '0'})
                self.assertEqual(install.call_count, 1)
                tools.assert_called_once()

    def test_incomplete_generation_cannot_silently_start_game(self):
        from newsnap.startup_assets import prepare_hd_shadows
        with tempfile.TemporaryDirectory() as temporary:
            with patch('newsnap.game_textures.image_key', return_value='image'), \
                 patch('newsnap.game_textures.complete', return_value=False), \
                 patch('newsnap.game_textures.install', return_value=(3, 0, 1)), \
                 patch('newsnap.hdshadows.ensure_esrgan'):
                with self.assertRaisesRegex(RuntimeError, 'HD'):
                    prepare_hd_shadows(Path(temporary), {'AC_HD_SHADOWS': '1'}, explicit=True)

    def test_saved_off_does_not_download_or_ask(self):
        from newsnap.startup_assets import prepare_hd_shadows
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            from newsnap.paths import runtime_dir
            runtime_dir(root).mkdir(parents=True)
            settings.save_settings(runtime_dir(root)/'newsnap.ini', {'hd_shadows':'0'})
            with patch('newsnap.hdshadows.ensure_esrgan') as tool:
                env={}
                prepare_hd_shadows(root, env, ask=lambda text: self.fail('must not ask'))
                self.assertEqual(env['AC_HD_SHADOWS'],'0')
                tool.assert_not_called()

    def test_decline_is_remembered_and_has_no_download(self):
        from newsnap.startup_assets import prepare_hd_shadows
        from newsnap.paths import runtime_dir
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); questions=[]
            with patch('newsnap.game_textures.image_key',return_value='image'), \
                 patch('newsnap.game_textures.complete',return_value=False), \
                 patch('newsnap.hdshadows.ensure_esrgan') as tool:
                def ask(text): questions.append(text); return False
                prepare_hd_shadows(root,{},ask=ask)
                prepare_hd_shadows(root,{},ask=ask)
                self.assertEqual(len(questions),1)
                self.assertIn('6 GB',questions[0])
                self.assertEqual(settings.load_settings(runtime_dir(root)/'newsnap.ini')['hd_shadows'],'0')
                tool.assert_not_called()

    def test_cancel_keeps_consent_and_prevents_success(self):
        import threading
        from newsnap.startup_assets import prepare_hd_shadows
        from newsnap.paths import runtime_dir
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); cancel=threading.Event()
            def install(*args, **kwargs):
                self.assertIs(kwargs['cancel'],cancel)
                cancel.set();return (2,0,0)
            with patch('newsnap.game_textures.image_key',return_value='image'), \
                 patch('newsnap.game_textures.complete',return_value=False), \
                 patch('newsnap.game_textures.install',side_effect=install), \
                 patch('newsnap.hdshadows.ensure_esrgan'):
                with self.assertRaisesRegex(RuntimeError,'cancelled'):
                    prepare_hd_shadows(root,{},ask=lambda _: True,cancel=cancel)
                self.assertTrue((runtime_dir(root)/'hdshadows/startup-consent.json').is_file())

    def test_installed_dds_packs_are_warmed_without_opening_other_assets(self):
        from newsnap.paths import runtime_dir
        from newsnap.startup_assets import warm_hd_assets

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = runtime_dir(root)
            files = [('texpack', '0000000000000001.dds'), ('hdshadows', '0000000000000002.dds'),
                     ('texpack', 'readme.dds'), ('texpack/src', '0000000000000003.dds')]
            for folder, name in files:
                path = runtime / folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'DDS ' + bytes(12))
            reports = []
            with patch('newsnap.startup_assets.HD_WARM_BYTES_PER_PACK', 10):
                self.assertEqual(warm_hd_assets(root, {'AC_HD_SHADOWS': '1'}, reports.append), (10, 10))
                self.assertEqual(len(reports), 1)
                self.assertEqual(warm_hd_assets(root, {'AC_TEX_PACK': '0', 'AC_HD_SHADOWS': '0'}), (0, 0))
                settings.save_settings(runtime / 'newsnap.ini', {'tex_pack': '0'})
                self.assertEqual(warm_hd_assets(root, {'AC_HD_SHADOWS': '1'}, reports.append), (0, 10))
                self.assertEqual(warm_hd_assets(root, {'AC_TEX_PACK': '1'}, reports.append), (10, 0))

    def test_cancelling_hd_warm_aborts_startup(self):
        from threading import Event
        from newsnap.paths import runtime_dir
        from newsnap.startup_assets import warm_hd_assets

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = runtime_dir(root) / 'texpack'
            pack.mkdir(parents=True)
            (pack / '0000000000000001.dds').write_bytes(b'DDS ' + bytes(12))
            cancel = Event()
            cancel.set()
            with self.assertRaisesRegex(RuntimeError, 'cancel'):
                warm_hd_assets(root, {}, cancel=cancel)
