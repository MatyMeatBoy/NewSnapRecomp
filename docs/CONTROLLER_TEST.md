# Local controller test

The test shows the identity SDL detects, its GUID, whether it has a gamepad mapping, the
live buttons/axes and the capabilities the device reports. A joystick without a mapping
still appears with its raw controls. A rumble capability means SDL declares it; the test
does not trigger it.

To check the controller on the second PC:

1. Close the game and open the launcher's controller test.
2. Connect the controller and check name, GUID and recognition. With several, check each
   ID separately.
3. Press the buttons and move both sticks and triggers. Buttons must return to rest when
   released. Axes are shown as raw SDL values: sticks about −32768 to 32767, mapped
   triggers 0 to 32767.
4. Disconnect and reconnect the controller. The old entry must disappear; the new
   connection may get another ID.
5. Close the test before opening the game, importing data or rebuilding the runtime. Then
   check the same controls in the game.

If it is not recognised as a gamepad, note the name/GUID and the raw buttons/axes. The
optional `gamecontrollerdb.txt` goes next to the runtime's `SDL3.dll` (`GameData` in a
normal installation). The game's precedence applies: an explicit
`SDL_GAMECONTROLLERCONFIG_FILE` suppresses that local file; when the local file is loaded,
the inline mappings of `SDL_GAMECONTROLLERCONFIG` are applied again to keep explicit
preferences.

The diagnostic writes no saves, profiles or controller databases; it sends no input and
does not turn on sensors, LEDs or rumble. It needs no Vulkan window and does not start SDL
video/audio/haptics. The launcher keeps incompatible operations locked while the
diagnostic owns SDL.

## Launcher backend

`newsnap.controller_probe.Session(runtime_dir, env=None)` initialises the SDL shipped in that
runtime. Use the constructor/context manager, `pump()`, `snapshot()` and `close()` from the
Tk main thread; SDL requires the main thread to
[initialise subsystems](https://wiki.libsdl.org/SDL3/SDL_Init) and
[process events](https://wiki.libsdl.org/SDL3/SDL_PumpEvents).

```python
with Session(runtime_dir, env=controller_environment) as session:
    controllers = session.snapshot()  # also pumps
```

The UI must own its busy state and `ProfileLock` for the whole session and schedule
snapshots with `after`, without moving them to a worker. `snapshot()` returns a
JSON-serialisable list with `id`, `name`, `guid`, `vendor`, `product`, `recognized`,
`virtual`, `connected`, `mapping`, `buttons`, `axes`, `raw_buttons`, `raw_axes`, `hats`,
`capabilities` and `error`. An empty list means no devices are enumerated. A disconnect
that coincides with a read can appear once with `connected=false`; the next snapshot closes
its handle. Global problems raise `ProbeError`; mapping warnings are in `session.warnings`
and the version in `session.sdl_version`.

An absolute path to `SDL3.dll` is opened with Windows' safe dependency search. Only
`SDL_INIT_GAMEPAD` (which implies joystick and events) is acquired. Every open handle is
closed, temporary hints are restored, the subsystem reference is released and finally the
DLL is unloaded so the runtime can be replaced. Global `SDL_Quit` is not used.

## Automated evidence

```powershell
python -m unittest tests.test_controller_probe -v
```

The native tests use temporary copies of the shipped DLL and SDL's local virtual
joysticks. They check a mapped gamepad and an unknown joystick, button/axis/hat reads,
several devices, disconnection, mapping precedence and DLL unloading. Another test compiles
the shipped headers and compares the ABI of `bool`, GUID, ID and the virtual descriptor with
ctypes. Failure tests check cleanup of initialisation/hints/handles and the thread rule.

Runtime verified during development: SDL **3.4.18**, DLL SHA-256
`2b4b128d8d510cc2d442693cf848c050d700d43dc667afe9e5fd82b0570d667e`. This virtual evidence
does not confirm physical compatibility of the second PC's controller; that acceptance
depends on the real test and its USB or Bluetooth transport.
