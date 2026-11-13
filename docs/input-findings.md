# Snap input investigation (2026-11-13)

Base: Astral `248e0b2`, read from the pristine `third_party/astral` tree.

## Confirmed correction

`runtime/input_map.c` inherited Astral's `KEY_MOUSE_L -> B_Y`. Snap's
photo action is A. The source overlay changes that default to A; right click
remains ZL (zoom). It changes the default table itself, so reset and
`key:default` use Snap defaults. Explicit `AC_BIND_*` values still run through
the original configure/bind code and replace defaults as before. Existing
user bindings are not rewritten or migrated. Keyboard E remains A.

The native fixture compiles the real staged `input_map.c`, presses each mouse
button, checks the resulting Switch button bits, applies an explicit custom A
binding, and resets. Before the overlay it failed with `left click must take
photo (A)`; after it the fixture passes.

## What the displaced aim circle does and does not establish

The original game allows the small aim circle to move inside its larger frame.
Its displacement alone does not prove a defect in the host input. The runtime
does not know or set the circle's HUD coordinates. No camera or HUD centering
change has been made.

Data flow inspected:

* `input_win.c`: WM_INPUT accepts relative raw mouse counts only. It uses
  atomic accumulation and exchange when consumed. Cursor capture clips/hides
  the OS pointer; there is no SetCursorPos/recentering loop to inject a
  synthetic recenter delta. Beginning capture clears pending raw counts.
* `input_map.c`: raw counts become right-stick velocity with up mapped to +Y,
  radial limiting, and zero output for zero counts. It is not an absolute
  pointer and does not maintain an accumulated target position.
* `input.c::mouse_camera`: one sample is held over all HID polls in a presented
  frame. The next presented frame consumes new counts, including zero. With
  presentations stalled for over 100 ms, the held deflection becomes zero.
  Not captured drains counts and clears the held sample.
* The right-stick merge picks the larger vector of gamepad, keyboard and mouse;
  input scripts run afterwards and can replace either stick.
* `ov_input.c::six_fill`: without live motion samples it writes zero gyro and
  angles with identity direction and resting acceleration (0,0,-1). That path
  is distinct from mouse-to-stick. `motion_fusion.c` consumes physical pad
  gyro/accelerometer samples, never mouse counts.

The local `build/research/time-tutorial.log` reports no gamepad and no
six-axis start/live/rest log. It also contains scripted LSTICK and RSTICK
deflections and focus changes. This does not identify the source of the
reported visual offset, and it is insufficient to justify a gyro or camera
coordinate correction.

## Bounded diagnostic capture

Set the environment variable `NEWSNAP_INPUT_TRACE=1` before launch. Unset or
any other value disables these logs. The variable is read through cfg_get's
non-AC environment pass-through; no new saved setting is introduced.

`snap input: mouse(dx,dy,stickx,sticky)` records consumed raw counts and the
result of mouse-to-stick conversion, before cam_speed_applied compensation.
`snap input: merged(Lx,Ly,Rx,Ry)` records the merged sticks and ordinary
buttons, including scripted input, before menu/text blocking and before
stick-direction button bits are added. Each lane records at most one sample
per presented frame, only on changes or a 60-frame heartbeat, and stops after
512 records. Logging occurs under the existing input lock. It does not alter
the values or the frame cache.

For a useful comparison, reproduce the same tutorial/scene twice:

1. `AC_INPUT=none`, a known deterministic `AC_INPUT_SCRIPT`, and tracing enabled
   isolates physical input. Scripted stick input still works by design.
2. Normal input with no input script: let the mouse rest before entering the
   aiming view, move it once, and rest again. Compare raw counts, converted
   samples, merged right stick and the game's visible circle at each step.

Neutral trace values with a displaced circle would move the investigation
into game camera state, scene/rendering or expected game behavior; persistent
nonzero merged input would instead identify an input source to inspect.
Same-frame changes after the first logged poll are intentionally not captured.
The trace is diagnostic evidence, not a claim that the visual issue is fixed.
