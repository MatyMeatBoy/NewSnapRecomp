# Handoff POINTER-03: menu pointer hover above 60 FPS

**Update, 0.9.22 (2026-11-16).** The owner clarified the reference behavior: yellow outside a selectable option,
orange over one at 60 FPS; above 60 FPS that selection state alternated. The shared pointer comparison now samples
hover only on interface updates while movement and rendering continue every frame. The owner reports the tested
144 FPS candidate no longer appears to blink on RX 6900 XT. Cause, regression, review and submenu evidence:
[menu-pointer-color.md](bugs/menu-pointer-color.md). The earlier investigation below is historical; its inference
that this was only a seven-second active ring is superseded by the owner's corrected reproduction.

## Historical investigation (before the corrected reproduction)

Owner's report (0.9.21, 2026-11-16): in the camp menu and in photo selection («Elige qué fotos quieres mostrarle al
profesor») the ring of the pointer blinks very fast at 144 FPS. Everything else in the menus is fine. The owner wants
it **fixed properly**: no frame-rate cap on those screens, and the rest of the menu improvements kept as they are.

## How to reproduce (hidden, muted, on copies)

- Save: the owner's advanced save, left for tests at `D:\01Claude\NewSnapRecomp\save\725fd1719498a464f911299fafbe8d75`
  (pass it with `--save`; it starts in the camp menu). Never touch the owner's install.
- Route: title, then one stick nudge so the pointer shows, held the **same real time** at both rates:
  60 fps `900 A 6` + `3000 LSTICK 0.3 0.3 8`; 144 fps `900 A 6` + `7200 LSTICK 0.3 0.3 19` (the nudge then lands at
  about the same world second, 50 s, at both rates; it matters).
- `tools/dev/route_run.py ... --seconds 70 AC_FPS=60|144 "AC_SHOTS=w49-57:0.03" AC_SHOTS_DEFER=1` (60 fps run:
  `w51-59`). The pointer rests on «Exploración»; crop `(162, 232, 210, 280)` of the 1920x1080 shots.
- Measure: count samples where the ring holds orange (`R > 200, 60 < G < 150, B < 90` on the ring annulus, radius
  13-21 px around the crop centre). Reference at 60 fps: **orange in 240 of 267 samples** (about 7.2 s after the
  nudge, then white). 0.9.21 at 144 fps: orange in **3 to 7 of 267** (isolated flashes = the blink).

## What the orange ring is

Not "over a button": it is the pointer's **active** state, about 7 s after it moves, shown while it rests on a
selectable option. At 60 fps it holds steadily; at 144 fps it is lost between interface steps and only flashes.

## What the code does (Snap 2.0.1 main)

- The menu pointer: `main+0x643a70` (object in `x21`; early exit `643ac0 cbz x21 -> 6455e8`). It runs **every game
  frame**. It reads a word the menu leaves at `x21+0x110` (OR'ed with the pad's held bits, `643ad0..643ad4`, then
  clears it), moves the pointer with the frame time (`643cc8`, FPS-02 already gives it the real time), queues its
  position by name (vtable `+0xc0`, `643dd8`), and at the end calls **the interface handler `main+0x7835d0` once
  more for each button** (`6441ec blr x9`, `x0` button object, `w1` state, `x3 x22`, `x4 x23`, `x5 sp+0x118`).
- Those button objects never reach the "started" state (`+0xc0 = 0`), so `snap_ui_pace_enter` runs them as written
  on every frame. The pointer's calls are also **what draws the buttons**: skip a call and the button is not drawn.
- The interface pacing (UI-HZ-01) runs the menu's logic, timelines and the per-frame **event 22** (`794b90`) 60 times
  a second; the pointer keeps running 144.

## Measured (144 fps unless said; all in the camp menu with the save above)

| Attempt | Orange samples (of 267) | Other effect |
| --- | --- | --- |
| 0.9.21 as is | 3-7 | — |
| Interface pacing off (`AC_SNAP_UI_PACE_PATCH=0`) | steady | everything 2.4x fast |
| `ui_motion` off; per-frame positions off (`AC_SNAP_UI_POSITIONS_PATCH=0`) | 3-5 | — |
| Both off together | 188 | ring spins 4x, pointer fades in a loop |
| Event 22 raised on every frame for **all** objects | 186 | ring spins 11x, pointer fades in a loop |
| Event 22 every frame only for the pointer's button calls | 7 | — |
| Skip the button calls between steps | — | buttons vanish |
| Button calls drawn only between steps | 1 | — |
| Hold only the buttons' movie advance between steps | 0-7 | — |
| Latch the menu's word `+0x110` between steps | 3 | — |
| Pointer on steps only + its button calls repeated between steps (draw only / as written) | — | **crash** (draw section needs the logic's locals; arguments point into changing data) |

So: the orange needs the per-frame event 22 **in step with** the pointer's logic, as at 60 fps; making them meet by
running more of either per frame speeds the ring and the pointer's fade cycle up; running the pointer less loses the
buttons' drawing.

## Ideas not tried yet

1. Find what event 22 does for the cursor (`cursor_mc` / `show_cursor_child_active` labels; `onEnterFrame`-style
   script on the cursor clip) and what clears the active state: a hardware watch (`NEWSNAP_UI_POS_WATCH=<clip>`,
   `NEWSNAP_UI_POS_WATCH_AT`) on the clip that holds the orange arc, or on the pointer object's fields near
   `+0x110..0x130`, at 60 vs 144 fps.
2. Raise event 22 every frame only for the object that owns `cursor_mc`, and hold that object's movie advance
   between steps (a narrower version of the "all objects" row, which showed the orange).
3. If the active state is a frame counter in the pointer object (about 430 frames = 7.2 s at 60), scale it by real
   time like FPS-02 did for the movement.

## State of the code

- Branch `fix/pointer-blink`: only the Spanish, French, German, Italian, Japanese, Korean and Traditional Chinese text
  for «Menús e interfaz fluidos» (it showed in English) and the board. The failed attempts were removed; their
  commits are in the branch history.
- Nothing released. No 60 FPS cap on those screens (owner: no).
