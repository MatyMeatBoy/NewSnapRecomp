import ctypes as C
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from newsnap import controller_probe as probe

ROOT = Path(__file__).resolve().parents[1]
DLL = ROOT / 'build/updated/SDL3.dll'
if not DLL.is_file():
    DLL = ROOT / 'toolchain/astral-release/Astral Chain-Setup/bin/SDL3.dll'


class VirtualJoystickDesc(C.Structure):
    # SDL3 bundled SDL_joystick.h: version is sizeof(desc), not SDL version.
    _fields_ = [('version', C.c_uint32)] + [(n, C.c_uint16) for n in
        ('type', 'padding', 'vendor_id', 'product_id', 'naxes', 'nbuttons', 'nballs', 'nhats', 'ntouchpads', 'nsensors')] + [
        ('padding2', C.c_uint16 * 2), ('button_mask', C.c_uint32), ('axis_mask', C.c_uint32),
        ('name', C.c_char_p), ('touchpads', C.c_void_p), ('sensors', C.c_void_p),
        ('userdata', C.c_void_p)] + [(n, C.c_void_p) for n in
        ('Update', 'SetPlayerIndex', 'Rumble', 'RumbleTriggers', 'SetLED', 'SendEffect', 'SetSensorsEnabled', 'Cleanup')]


class ProbeLifecycleTests(unittest.TestCase):
    def test_cleanup_attempts_all_handles_hints_and_unload_after_error(self):
        fake = Mock()
        fake.SDL_GetVersion.return_value = 3004018
        fake.SDL_GetHint.return_value = None
        fake.SDL_InitSubSystem.return_value = True
        fake.SDL_CloseGamepad.side_effect = RuntimeError('synthetic close failure')
        with patch.object(probe, '_load', return_value=fake), patch.object(probe, '_bind'), \
                patch.object(probe, '_unload') as unload:
            session = probe.Session('controlled', env={'SDL_GAMECONTROLLERCONFIG': 'test'})
            session._handles = {1: (10, 20), 2: (11, 21)}
            with self.assertRaisesRegex(probe.ProbeError, 'synthetic close failure'):
                session.close()
            session.close()
        self.assertEqual(fake.SDL_CloseGamepad.call_count, 2)
        self.assertEqual(fake.SDL_CloseJoystick.call_count, 2)
        fake.SDL_QuitSubSystem.assert_called_once_with(probe.GAMEPAD)
        fake.SDL_ResetHint.assert_called_once_with(b'SDL_GAMECONTROLLERCONFIG')
        unload.assert_called_once_with(fake)
        self.assertIsNone(probe._active)

    def test_initialization_failure_releases_ownership_and_library(self):
        fake = Mock()
        fake.SDL_GetVersion.return_value = 3004018
        fake.SDL_InitSubSystem.return_value = False
        fake.SDL_GetError.return_value = b'synthetic init failure'
        with patch.object(probe, '_load', return_value=fake), patch.object(probe, '_bind'), \
                patch.object(probe, '_unload') as unload:
            with self.assertRaisesRegex(probe.ProbeError, 'synthetic init failure'):
                probe.Session('controlled')
        fake.SDL_QuitSubSystem.assert_called_once_with(probe.GAMEPAD)
        unload.assert_called_once_with(fake)
        self.assertIsNone(probe._active)

    def test_missing_export_is_reported_and_loaded_library_is_released(self):
        fake = Mock()
        with patch.object(probe, '_load', return_value=fake), \
                patch.object(probe, '_bind', side_effect=AttributeError('SDL required export missing')), \
                patch.object(probe, '_unload') as unload:
            with self.assertRaisesRegex(probe.ProbeError, 'required export missing'):
                probe.Session('controlled')
        unload.assert_called_once_with(fake)
        fake.SDL_QuitSubSystem.assert_not_called()
        self.assertIsNone(probe._active)

    def test_abi_failure_and_hint_failure_cleanup_without_quitting_unowned_subsystem(self):
        for version, hint_ok in ((2000000, True), (3004018, False)):
            with self.subTest(version=version):
                fake = Mock()
                fake.SDL_GetVersion.return_value = version
                fake.SDL_GetHint.return_value = b'previous override'
                fake.SDL_SetHintWithPriority.return_value = hint_ok
                with patch.object(probe, '_load', return_value=fake), patch.object(probe, '_bind'), \
                        patch.object(probe, '_unload') as unload:
                    with self.assertRaises(probe.ProbeError):
                        probe.Session('controlled', env={'SDL_GAMECONTROLLERCONFIG': 'synthetic'})
                fake.SDL_QuitSubSystem.assert_not_called()
                unload.assert_called_once_with(fake)
                self.assertIsNone(probe._active)

    def test_background_thread_is_rejected_before_loading_sdl(self):
        errors = []
        def run():
            try:
                probe.Session('controlled')
            except probe.ProbeError as error:
                errors.append(str(error))
        with patch.object(probe, '_load') as loader:
            thread = threading.Thread(target=run)
            thread.start()
            thread.join()
        self.assertEqual(len(errors), 1)
        loader.assert_not_called()


@unittest.skipUnless(os.name == 'nt' and DLL.is_file(), 'bundled Windows SDL3 required for native virtual-controller tests')
class NativeControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name)
        shutil.copy2(DLL, self.runtime / 'SDL3.dll')
        self.session = probe.Session(self.runtime, env={'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS': '1',
                                                       'SDL_GAMECONTROLLERCONFIG': '', 'SDL_GAMECONTROLLERCONFIG_FILE': ''})
        self.addCleanup(self.session.close)
        self.sdl = self.session._sdl
        for name, result, args in (
            ('SDL_AttachVirtualJoystick', C.c_uint32, [C.POINTER(VirtualJoystickDesc)]),
            ('SDL_DetachVirtualJoystick', C.c_bool, [C.c_uint32]),
            ('SDL_GetJoystickFromID', C.c_void_p, [C.c_uint32]),
            ('SDL_SetJoystickVirtualAxis', C.c_bool, [C.c_void_p, C.c_int, C.c_int16]),
            ('SDL_SetJoystickVirtualButton', C.c_bool, [C.c_void_p, C.c_int, C.c_bool]),
            ('SDL_SetJoystickVirtualHat', C.c_bool, [C.c_void_p, C.c_int, C.c_uint8]),
        ):
            function = getattr(self.sdl, name)
            function.restype, function.argtypes = result, args
        self.ids = []
        self.addCleanup(self.detach_all)

    def detach_all(self):
        if self.session._closed:
            return
        for instance in self.ids:
            self.sdl.SDL_DetachVirtualJoystick(instance)
        self.ids.clear()

    def attach(self, gamepad=True, name=b'NewSnap automated virtual controller'):
        self.assertEqual(C.sizeof(VirtualJoystickDesc), 136)
        desc = VirtualJoystickDesc(version=C.sizeof(VirtualJoystickDesc), type=1 if gamepad else 0,
                                   vendor_id=0x1209, product_id=0x5050 if gamepad else 0x5051,
                                   naxes=6 if gamepad else 2, nbuttons=26 if gamepad else 3, nhats=1,
                                   button_mask=(1 << 26) - 1 if gamepad else 0,
                                   axis_mask=63 if gamepad else 0, name=name)
        instance = self.sdl.SDL_AttachVirtualJoystick(C.byref(desc))
        self.assertNotEqual(instance, 0, self.session._error())
        self.ids.append(instance)
        return instance

    def test_actual_abi_mapped_and_unknown_devices_live_states_hotplug_and_cleanup(self):
        first = self.attach()
        second = self.attach(False, b'NewSnap unmapped virtual joystick')
        rows = {r['id']: r for r in self.session.snapshot()}
        self.assertEqual(len(rows[first]['guid']), 32)
        self.assertEqual(rows[first]['vendor'], 0x1209)
        self.assertTrue(rows[first]['recognized'])
        self.assertTrue(rows[first]['mapping'])
        self.assertFalse(rows[second]['recognized'])
        self.assertIsNone(rows[second]['mapping'])
        joystick = self.sdl.SDL_GetJoystickFromID(first)
        self.assertTrue(self.sdl.SDL_SetJoystickVirtualAxis(joystick, 0, 16384))
        self.assertTrue(self.sdl.SDL_SetJoystickVirtualButton(joystick, 0, True))
        raw = self.sdl.SDL_GetJoystickFromID(second)
        self.assertTrue(self.sdl.SDL_SetJoystickVirtualButton(raw, 2, True))
        self.assertTrue(self.sdl.SDL_SetJoystickVirtualHat(raw, 0, 1))
        rows = {r['id']: r for r in self.session.snapshot()}
        self.assertEqual(rows[first]['axes']['leftx'], 16384)
        self.assertTrue(rows[first]['buttons']['south'])
        self.assertTrue(rows[second]['raw_buttons'][2])
        self.assertEqual(rows[second]['hats'][0], 1)
        self.assertFalse(rows[first]['capabilities']['rumble'])
        json.dumps(list(rows.values()))
        self.assertTrue(self.sdl.SDL_DetachVirtualJoystick(first))
        self.ids.remove(first)
        after = self.session.snapshot()
        self.assertNotIn(first, [r['id'] for r in after])
        self.assertNotIn(first, self.session._handles)
        self.assertIn(second, self.session._handles)
        self.detach_all()
        self.assertEqual(self.session.snapshot(), [])
        self.session.close()
        self.session.close()
        self.assertFalse(self.session._handles)
        self.assertIsNone(probe._active)
        # Proves the SDL DLL is unloaded, so runtime replacement is not blocked.
        (self.runtime / 'SDL3.dll').rename(self.runtime / 'SDL3.closed.dll')
        with self.assertRaisesRegex(probe.ProbeError, 'cerrado'):
            self.session.snapshot()

    def test_ctypes_layout_matches_compiled_bundled_headers(self):
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        compiler = shutil.which('clang') or str(sdk / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for SDL header ABI comparison')
        include = sdk / 'runtime/deps/include'
        if not include.exists():
            self.skipTest('bundled SDL headers unavailable')
        source = self.runtime / 'abi.c'
        source.write_text('''#include <stddef.h>
#include <stdio.h>
#include <SDL3/SDL_joystick.h>
int main(void) {
 printf("%zu %zu %zu %zu %zu %zu %d", sizeof(bool), sizeof(SDL_GUID),
        sizeof(SDL_JoystickID), sizeof(SDL_VirtualJoystickDesc),
        offsetof(SDL_VirtualJoystickDesc,name), offsetof(SDL_VirtualJoystickDesc,Cleanup), SDL_VERSION);
 return 0;
}
''', encoding='utf-8')
        # SDL_VERSION is in its own header; prototypes above remain from bundled headers.
        source.write_text('#include <SDL3/SDL_version.h>\n' + source.read_text(), encoding='utf-8')
        executable = self.runtime / 'abi.exe'
        result = subprocess.run([compiler, '-I', str(include), str(source), '-o', str(executable)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        actual = list(map(int, subprocess.check_output([str(executable)]).split()))
        self.assertEqual(actual[:6], [C.sizeof(C.c_bool), C.sizeof(probe.GUID), C.sizeof(C.c_uint32),
                                     C.sizeof(VirtualJoystickDesc), VirtualJoystickDesc.name.offset,
                                     VirtualJoystickDesc.Cleanup.offset])
        self.assertEqual(self.sdl.SDL_GetVersion(), actual[6])

    def test_mapping_precedence_matches_native_optional_database(self):
        instance = self.attach()
        row = next(r for r in self.session.snapshot() if r['id'] == instance)
        guid = row['guid']
        mapping = guid + ',Local test,a:b0,b:b1,leftx:a0,lefty:a1,platform:Windows,'
        (self.runtime / 'gamecontrollerdb.txt').write_text(mapping + '\n', encoding='utf-8')
        inline = (guid + ',Explicit override,a:b1,b:b0,leftx:a0,lefty:a1,platform:Windows,').encode()
        self.sdl.SDL_SetHintWithPriority(b'SDL_GAMECONTROLLERCONFIG', inline, 2)
        self.session._mappings(self.runtime)
        mapped = next(r for r in self.session.snapshot() if r['id'] == instance)
        self.assertIn('a:b1', mapped['mapping'])
        self.assertIn('Explicit override', mapped['mapping'])
        # Explicit-file hint suppresses the optional adjacent database entirely.
        self.sdl.SDL_SetHintWithPriority(b'SDL_GAMECONTROLLERCONFIG_FILE', b'explicit-file', 2)
        (self.runtime / 'gamecontrollerdb.txt').write_text('invalid database content', encoding='utf-8')
        self.session._mappings(self.runtime)
        self.assertEqual(self.session.warnings, [])


if __name__ == '__main__':
    unittest.main()
