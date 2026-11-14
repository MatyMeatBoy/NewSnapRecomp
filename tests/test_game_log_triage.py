import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

import triage_game_log as triage

HEADER = '''[host] cfg: no settings file at C:\\Users\\Persona Real\\Juegos\\GameData\\astralchain.ini
[host] vk: gpu 0: AMD Radeon RX 6900 XT (type 2, api 1.4.300)
[host] vk: using gpu 0: AMD Radeon RX 6900 XT
[host] vk_pipeline: driver shader cache: 1002:73bf:00000000 abcdef "25.10.2" exe C:/Users/Persona Real/Juegos/newsnap.exe
[host] perf: frame 600: something noisy
[host] gfx: window gained the focus at 2026-11-13 22:30:00 local time
[host] kernel: frame 20100: asynchronous preemption: 1 interrupted
'''
KEYBOARD = '[host] swkbd: from main+0x69ac24: "Please enter a nickname for yourself." (1-12 units) -> "Local"\n'
CRASH = '''FATAL: access violation (0xc0000005) at host 00007FF6A1B2C3D4 (astralchain+0x2c3d4), reading address 0x18
  in lifted function f_7000538c40 = main+0x538c40
  host frame  0: astralchain+0x1234
  x0  0000000000000000  x1  0000000000000001
  sp  0000003d9edff940
  pc  0000007000538c68  lr main+0x538c6c
  guest frame  0: main+0x53b7f0
  guest frame  1: main+0x1f2a90
'''
SERVICE = '''FATAL: sm: service "acc:u0" is not implemented
[host] fatal: memory commit: this process 2600 MB, the system 12000 of 48000 MB
'''


class TriageTests(unittest.TestCase):
    def classify(self, text):
        return triage.triage_lines(text.splitlines())

    def test_host_exception_is_reported_with_guest_context(self):
        report = self.classify(HEADER + KEYBOARD + CRASH)
        self.assertEqual((report['verdict'], report['expected_exit_code']), ('excepción-host', 71))
        fatal = report['fatal']
        self.assertEqual((fatal['what'], fatal['code']), ('access violation', '0xc0000005'))
        self.assertIn('f_7000538c40', fatal['lifted_function'])
        self.assertEqual(fatal['guest_frames'], ['guest frame  0: main+0x53b7f0', 'guest frame  1: main+0x1f2a90'])
        self.assertEqual(report['gpu'], 'AMD Radeon RX 6900 XT')
        self.assertEqual(report['driver'], '25.10.2')
        self.assertEqual(report['last_frame'], 20100)
        self.assertEqual(len(report['keyboard']), 1)
        self.assertTrue(report['hints'])

    def test_unimplemented_service_is_a_runtime_fatal_with_its_name(self):
        report = self.classify(HEADER + SERVICE)
        self.assertEqual((report['verdict'], report['expected_exit_code']), ('fatal-runtime', 70))
        self.assertEqual(report['fatal']['service'], 'acc:u0')
        self.assertIn('acc:u0', report['hints'][0])

    def test_other_runtime_fatals(self):
        report = self.classify(HEADER + 'FATAL: ipc: nifm:u command 4 is not implemented\n')
        self.assertEqual(report['verdict'], 'fatal-runtime')
        self.assertNotIn('service', report['fatal'])
        report = self.classify(HEADER + 'FATAL: nn::swkbd::ShowKeyboard: CreateWindowEx (error 1400)\n')
        self.assertIn('entrada de texto', report['hints'][0])

    def test_window_close_restart_timed_and_unfinished(self):
        closed = self.classify(HEADER + KEYBOARD + '[host] gfx: window closed; exiting\n')
        self.assertEqual((closed['verdict'], closed['expected_exit_code']), ('ventana-cerrada', 0))
        self.assertTrue(closed['hints'])   # keyboard seen before an orderly close
        restart = self.classify(HEADER + '[host] gfx: window closed; restarting\n')
        self.assertEqual((restart['verdict'], restart['expected_exit_code']), ('reinicio-solicitado', 75))
        timed = self.classify(HEADER + 'boot: frames 4182 presented\nboot: passed (1 SVCs)\n')
        self.assertEqual(timed['verdict'], 'fin-programado')
        cut = self.classify(HEADER)
        self.assertEqual((cut['verdict'], cut['expected_exit_code']), ('sin-marca-final', None))

    def test_fatal_wins_over_a_later_close_line(self):
        report = self.classify(HEADER + SERVICE + '[host] gfx: window closed; exiting\n')
        self.assertEqual(report['verdict'], 'fatal-runtime')

    def test_dialog_lines_are_collected_and_noise_is_dropped(self):
        text = (HEADER + '[host] err: game application error dialog 2162 from main+0x5087f4: "a" / "b"\n'
                '[host] nifm: network request from main+0x53579c: rejected, the host is offline\n'
                '[host] fps: 120 frames in 2.000 s\n')
        report = self.classify(text)
        self.assertEqual(len(report['dialogs']), 2)
        self.assertFalse(any('perf:' in line or 'fps:' in line or 'kernel:' in line for line in report['tail']))
        self.assertEqual(len(report['focus']), 1)

    def test_user_paths_are_redacted_everywhere(self):
        report = self.classify(HEADER + CRASH.replace('astralchain+0x1234', 'D:\\Users\\Otra\\x.dll+0x1'))
        dumped = json.dumps(report, ensure_ascii=False)
        self.assertNotIn('Persona', dumped)
        self.assertNotIn('Otra', dumped)
        self.assertIn('[PRIVATE PATH LINE]', dumped)

    def test_unknown_external_paths_with_spaces_are_not_ready_to_paste(self):
        report=self.classify(HEADER + '\nloaded profile E:\\Private Family\\Holiday Album\\save\\user-name\n'
                             'loaded C:\\Users\\Alice Smith\\private\n'
                             'loaded /home/alice smith/Private Album\n')
        dumped=json.dumps(report,ensure_ascii=False)
        for private in ('Private Family','Holiday Album','user-name','Alice Smith','alice smith'):
            self.assertNotIn(private,dumped)

    def test_corrupt_deep_launcher_record_does_not_hide_real_fatal(self):
        text='[newsnap_launcher] '+('{"event":"start","runtime":'+ '['*50000+'0'+']'*50000+'}')
        report=self.classify(text+'\nFATAL: actual runtime failure\n')
        self.assertEqual(report['verdict'],'fatal-runtime')
        self.assertIsNone(report['launch_identity'])

    def test_newest_log_in_folder_and_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            old = folder / 'launcher-game-20261113-100000-aaaaaaaa-001.log'
            new = folder / 'launcher-game-20261113-223000-bbbbbbbb-001.log'
            old.write_text(HEADER + '[host] gfx: window closed; exiting\n', encoding='utf-8')
            new.write_text(HEADER + SERVICE, encoding='utf-8')
            os.utime(old, (1_000_000, 1_000_000))
            os.utime(new, (2_000_000, 2_000_000))
            (folder / 'launcher-prepare-x.log').write_text('ignored', encoding='utf-8')
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            report = triage.triage(folder)
            self.assertEqual((report['file'], report['verdict']), (new.name, 'fatal-runtime'))
            output = io.StringIO()
            output.reconfigure = lambda **_: None
            with patch('sys.stdout', output):
                self.assertEqual(triage.main([str(old)]), 0)
            self.assertIn('ventana-cerrada', output.getvalue())
            self.assertNotIn('Persona', output.getvalue())
            self.assertEqual({p.name: p.read_bytes() for p in folder.iterdir()}, before)   # read-only

    def test_direct_launch_logs_are_found_too(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name, stamp, body in (('launcher-game-20261113-100000-aaaaaaaa-001.log', 1_000_000, HEADER),
                                      ('totk.1.log', 2_000_000, HEADER + SERVICE),
                                      ('astralchain.log', 3_000_000, HEADER + KEYBOARD + CRASH),
                                      ('runtime-rebuild.log', 4_000_000, 'not a session')):
                (folder / name).write_text(body, encoding='utf-8')
                os.utime(folder / name, (stamp, stamp))
            report = triage.triage(folder)
            self.assertEqual((report['file'], report['verdict']), ('astralchain.log', 'excepción-host'))
            self.assertEqual(triage.triage(folder / 'totk.1.log')['verdict'], 'fatal-runtime')

    def test_runtime_generation_is_read_from_start_lines(self):
        base = '[host] cfg: read D:\\Games\\Port\\astralchain.ini: 19 keys\n'
        cases = (('snap_render on', False, '0.1.x (anterior a 0.2)'),
                 ('snap_render on, snap_supersample on', False, '0.2 a 0.4'),
                 ('snap_render on, snap_supersample on', True, '0.5 o posterior'),
                 ('snap_render on, snap_supersample on, snap_random_range on', True, '0.5 o posterior'))
        for patches, color, expected in cases:
            text = base + f'[host] patches: {patches} (page 0x7002891000)\n'
            text += '[host] vk: final SDR byte transfer: source 43, destination 44\n' if color else ''
            report = self.classify(text)
            self.assertEqual(report['runtime']['generation'], expected, patches)
            self.assertEqual(report['runtime']['folder'], '[PRIVATE PATH LINE]')
            self.assertEqual(any('no la 0.5' in hint for hint in report['hints']), expected != '0.5 o posterior')
        self.assertEqual(self.classify(HEADER)['runtime']['generation'], 'desconocida')

    def test_new_product_logs_keep_generation_as_an_inference(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            (folder/'newsnap.log').write_text(
                '[host] cfg: read D:\\Games\\Port\\newsnap.ini: 19 keys\n'
                '[host] patches: snap_render on (page 0x7002891000)\n'
                'FATAL: example failure\n', encoding='utf-8')
            report=triage.triage(folder)
            self.assertEqual(report['file'], 'newsnap.log')
            self.assertEqual(report['runtime']['folder'], '[PRIVATE PATH LINE]')
            self.assertEqual(report['runtime']['identity_basis'], 'log-inference-not-executable-hash')
            self.assertTrue(any('hash' in hint for hint in report['hints']))

    def test_known_jpeg_longjmp_fatal_of_old_runtimes(self):
        text = ('[host] patches: snap_render on (page 0x7002891000)\n'
                '[host] vk caps: AMD Radeon RX 6900 XT, vendor 0x1002 device 0x73af, driver AMD proprietary driver '
                '"26.10.1 (AMD proprietary shader compiler)" (id 1, version 2.0.353, raw 0x800161), api 1.4.315\n'
                'FATAL: rt_dispatch: no function at guest pc 0x7002c73060 (sdk+0x273060): not a function start '
                '(lr 0x7002c73060 (sdk+0x273060))\n')
        report = self.classify(text)
        self.assertEqual((report['verdict'], report['fatal']['known'], report['fatal']['guest_pc']),
                         ('fatal-runtime', 'jpeg-longjmp', 'sdk+0x273060'))
        self.assertIn('26.10.1', report['driver'])
        self.assertTrue(any('anteriores a 0.3' in hint for hint in report['hints']))
        self.assertTrue(any('0.1.x' in hint for hint in report['hints']))
        other = self.classify('FATAL: rt_dispatch: no function at guest pc 0x7000001234 (main+0x1234): not a function start\n')
        self.assertNotIn('known', other['fatal'])
        self.assertEqual(other['fatal']['guest_pc'], 'main+0x1234')

    def test_missing_logs_are_an_argument_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                triage.main([temporary])

    def test_large_logs_keep_the_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'launcher-game-big-001.log'
            with patch.object(triage, 'MAX_BYTES', 4096):
                path.write_text('[host] perf: filler line\n' * 2000 + SERVICE, encoding='utf-8')
                report = triage.triage(path)
            self.assertEqual(report['verdict'], 'fatal-runtime')
            self.assertGreater(report['bytes'], 4096)


if __name__ == '__main__':
    unittest.main()
