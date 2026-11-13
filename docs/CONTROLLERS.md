# Controllers in v0.3

The runtime reads controllers through SDL3's gamepad interface. Xbox, PlayStation,
Nintendo and third-party devices can work when SDL recognizes their hardware and
provides a mapping. USB/Bluetooth connection, drivers and available controls vary
by device; recognition is not a guarantee that every controller or accessory works.
Only the first available gamepad is used. The runtime rescans when disconnected
(approximately once per second), so connecting or reconnecting a recognized pad
does not require restarting.

## An unrecognized generic controller

v0.3 optionally reads `gamecontrollerdb.txt` beside **the running game executable**,
before both the initial prompt detection and normal input startup. Launching from
another working directory does not change this location. Paths use SDL's UTF-8
file APIs, including on Windows. The loader is synchronized and runs once per
process; restart after editing the file.

Supply SDL-compatible mapping lines for your controller's GUID and platform. Each
line in this file must include the correct platform field, such as
`platform:Windows,`. The runtime does not download mappings or guess raw joystick
button numbers. No database is bundled or fetched by this change. A missing file
leaves SDL's built-in mappings active; a present database logs the number of
mappings SDL accepted, or its load error. A malformed or platform-incompatible
line may be ignored by SDL (zero accepted mappings).

SDL's explicit `SDL_GAMECONTROLLERCONFIG_FILE` hint takes precedence: when set,
the optional adjacent database is skipped. `SDL_GAMECONTROLLERCONFIG` mapping
lines are reapplied after the local file so that explicit user mappings win.
These SDL mappings translate the device's raw inputs; they do not reset the game's
saved button bindings. Keep any downloaded database's license and attribution
with that file if distributing it separately.

## Button layout and bindings

The inherited mapper offers Nintendo, Xbox and PlayStation layouts. In Auto,
PlayStation identification selects its layout, an east button labelled A selects
Nintendo, and other mapped controllers select Xbox. Manual layout selection is
available through the existing controller settings. A loaded prompt modification
can force the layout it was drawn for; prompt asset availability and visual
correctness in New Pokémon Snap still require separate in-game verification.

| Physical face button | Nintendo action | Xbox action | PlayStation action |
| --- | --- | --- | --- |
| South | B | A | A |
| East | A | B | B |
| West | Y | X | Y |
| North | X | Y | X |

The remaining defaults map shoulders to L/R, triggers to ZL/ZR, stick clicks to
L/R stick, Start/Back to Plus/Minus and D-pad to its matching directions. In Snap,
A is the photo action and ZL is zoom. Existing custom `bind_` settings remain in
effect across controller families. For example, an explicit `pad:lpaddle1` binding
refers to that physical SDL control in every layout; it only works on devices
that expose that paddle. The mapper applies radial stick deadzones, supports
separate left/right values and clamps configured percentages to 0–50.

Rumble, trigger rumble and motion sensors depend on SDL and the device reporting
those capabilities. Devices exposing only a raw joystick need a suitable SDL
mapping; steering wheels, flight sticks and specialty devices are not promised
as fully supported gamepads. Unknown identity does not add a new generic glyph
set; the inherited prompt fallback is Nintendo.

## Verification and limits

`python -m unittest tests.test_controllers tests.test_snap_input -v` checks:

- The exact pinned runtime source receives the loader before both detection paths.
- The bundled real SDL3 DLL initially rejects an unmapped virtual generic joystick,
  then recognizes it after loading the optional file; real SDL button and axis
  reads match that mapping. Disconnect/reconnect retains the mapping.
- Missing/invalid files, explicit user override lines (including blank lines and
  CRLF), simultaneous loader calls and repeated startup calls behave safely.
- A Unicode executable directory works while the process has a different cwd.
- Compiled real host mapping code produces every default button action for all
  three layouts, retains custom paddle bindings, and handles stick direction,
  radial deadzone, full deflection, diagonal scaling and configured deadzone limits.
- Existing photo/zoom mouse defaults and explicit user key overrides still work.

These are automated native regressions using a virtual joystick and the actual
SDL/mapper implementations. They are **not physical Xbox, PlayStation, Nintendo,
Bluetooth, rumble or sensor tests**, nor in-game tutorial/glyph verification.
The native SDL fixture currently uses the bundled Windows toolchain and skips on
other systems; the pure mapping fixture is portable when a C compiler is present.
