# INPUT-01 · Camera and sensor continuity

Status: proposal for independent review. Owner: RTX tester, 2026-11-13.

## Causes reproduced in the donor's functions

1. `mouse_camera` keeps `held[2]` during the same presented frame. The backends clear the
   mouse deltas on recapture, but the consumer does not know there was a release/recapture
   if both happened between two game reads. It then reuses the previous tilt, even with the
   mouse still.
2. `motion_main` calls `sensors_ready` before checking `AC_MOTION`. So it can turn sensors on
   with motion off. If the gyro is enabled and enabling the accelerometer fails, it leaves the
   gyro partially enabled.
3. Disconnecting/changing controller, turning motion off or losing a read does not reset the
   fusion. The ring keeps samples up to 200 ms and a new controller inherits the previous
   angle/orientation. This is not a wrong sensor calibration: the fixture reproduces the
   defect with exact synthetic samples.
4. `input_motion_enabled` duplicates the configuration cache with two unsynchronised statics
   (`on`, `seen`) shared between the gyro thread and the game's readers. A paused old read
   can finish after a read of the new configuration and leave the old `on` with the new
   `seen`: motion stays enabled even though the current configuration says off.

These causes are verified on CPU; the owner's camera has not been causally attributed to
them. Physical gyro drift or a stick outside its configured dead zone still need evidence
from their device.

## Proposed fix

`newsnap/camera_input_adapt.py` adds targeted edits:

- The Win32 and SDL backends count each effective capture transition; the camera invalidates
  its held sample when that counter changes, even without a frame change. The original
  motion accumulation/conversion is kept.
- Polling checks `AC_MOTION` before enabling/reading sensors. When it is turned off, the
  previously started sensors are disabled. A partial enable is reverted.
- The real fusion resets when the source is lost/changed, after closing/reopening the same
  identifier and when a read fails after valid samples. The next read starts a new reference;
  it does not integrate across that discontinuity. The change is seen at the next 4 ms poll.
- `input_motion_enabled` queries `cfg_bool` directly, whose publication is already atomic,
  without adding a second shared cache that can go stale.

Sensitivity, defaults, dead zones, axes, simulation and the fusion algorithm are not changed.
The controller keeps its background input behaviour; the mouse fix follows the cursor's
transitions.

## Tests and evidence

```
.venv\Scripts\python -X utf8 -m unittest tests.test_camera_input -v
```

Six tests compile/run the real C functions with simulated platform/SDL APIs. They include
both capture backends, recapture without a frame change, initial rest, legitimate holding
within the frame, a still next frame, release and a stopped frame; motion off from the start,
off/on, disconnect/reconnect, changing controller, reopening the same ID, partial sensor
failure, read failure, rest and continuous turning; and the original dead zone with a neutral
stick, noise inside the configured zone and deliberate full-amplitude input. The fusion comes
entirely from `motion_fusion.c`, not from a Python reimplementation. An extra test uses two
real Win32 threads and events to stop an old read, apply/turn off and read the new setting,
then complete the old read; the later call must still return off. The donor fails exactly at
that last check. Sensors stay simulated and SDL is not started. The syntax of the complete
`input.c`, `input_win.c` and `input_sdl.c` is also checked with the toolchain's
SDL/Vulkan/Win32 headers.

`NEWSNAP_INPUT_BASELINE=1` skips the adapter in the same tests: eleven sub-cases fail on the
donor. With the adapter they pass. Local logs: `build/v05-camera-input-red.txt` and
`build/v05-camera-input-green.txt`.

No real SDL, physical sensor/rumble, game or GPU test was started. No owner data or
configuration was modified.

## Integration and limits

The coordinator added `camera_input_adapt.edits` to `newsnap/adapt.py` and built the
integrated runtime `06a8d9df…`. The independent review of locks, capture and the sensor cycle
approved the changes; its remark about `input_motion_enabled`'s shared cache was also fixed
with a two-real-thread regression. Acceptance with the owner's physical mouse/controller is
pending. Do not attribute the owner's case just because the fixtures pass.
