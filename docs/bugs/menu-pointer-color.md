# POINTER-COLOR-03: main-menu hover flicker above 60 FPS

Owner reproduction (2026-11-16, RX 6900 XT): at 60 FPS the pointer is orange over a selectable item and yellow away from one. At 90 FPS or higher it flickers, as if returning to the previous colour. This is distinct from the pointer-position stepping recorded under POINTER-02. Do not cap rendering at 60 FPS.

## Investigation

Base: feature/reticle-hz `2687bb1`, which contains the 0.9.21 interface changes. The shared checkout main is older; it was not switched or updated.

Read-only inspection of the supported main module finds exactly one reference each to `selectable` (main+0x644364) and `unselectable` (0x6443b4). In main+0x643a70, the pointer update sets a local result byte at sp+0x118 to zero (0x643e84), calls the registered screen adapters (0x6441ec), then compares that result with pointer-object+0x128 (0x644340..0x644350). A change queues one of those two commands through interface vtable+0x58. This establishes the producer of the colour transition, not the reason for a false transition.

## Cause and correction

With a copy of the owner's advanced save, the pre-fix 144 FPS run reports 44 transitions from selectable to unselectable on frames where the interface did not update. The adapters' local result byte is reset each pointer update, but the interface supplies its selectable result on interface steps only. Consuming the intervening zero as a fresh miss queues alternating `selectable` / `unselectable` commands. This also reproduced on the new-character selection screens (429 false leaves), so it is not restricted to AMD.

At main+0x644344, after the original result load and before its comparison, `snap_ui_pointer_hover` uses the previous hover operand (w9) on frames without an interface step. On a step it preserves the new operand exactly, including a real leave. No persistent cache is introduced: the state is the game's existing byte. Only w8 changes. Pointer movement and drawing remain per game frame; original colour commands, timelines, game logic and presentation rate are retained. The site belongs to `snap_ui_pace`, so disabling interface pacing also removes this correction. No rendering cap is added.

Reference checked before the correction: the pinned Astral input implementation (`third_party/astral/runtime/input.c`, commit 248e0b2) provides host input and scripted routes but no equivalent Flash-interface hover patch. The relevant local precedent is INPUT-HZ-01 in [HIGH_FPS.md](../HIGH_FPS.md): sampling a consumer on the same interface decision as its producer while drawing every frame. No emulator patch was transplanted.

`NEWSNAP_POINTER_HOVER_TRACE=1` reports old, raw and effective operands (bounded to 20,000 samples). It is off by default.

## Validation and limits

- Native regression first failed with return code 2 against the read-only observer, then passed after correction. It drives the captured hit/empty pattern at 60/90/120/144 FPS, checks enter and real leave, and checks every other CPU byte is preserved.
- `python -m unittest tests.test_ui_pace tests.test_ui_motion -q`, NEWSNAP_CC = bundled clang: 8 tests pass.
- Full candidate compilation, selftest and owner-module loader: passed, zero failures.
- RTX 4060 Laptop, same 45-second route, resolution 1280x720, 144 FPS cap, copies of the supplied advanced save: before, 44 off-step false leaves in 172 samples; after, zero in 367 samples, with four genuine step transitions retained. The number/timing of samples differs; this is functional evidence, not a pacing benchmark. Sparse screenshots identify menu/course screens; they do not establish pixel-perfect colour stability on every present.
- Owner, RX 6900 XT (2026-11-16), tested the supplied 144 FPS BAT: reports it no longer appears to blink and authorizes release. This is the observed pointer case, not exhaustive acceptance of every screen.
- Independent code review: no blocking issues. The strengthened native fixture also drives the real pad-frame decision, changes the presented counter between handler and hover calls within one game frame, and covers forced full-handler flags while event22 remains globally paced.
- Shared-submenu run, RTX 4060 Laptop: camp -> exploration map -> camp -> laboratory -> camp at 144 FPS, 75 seconds. Screenshot-identified screens and trace summary: `build/pointer-color-submenus144/`. 7,442 samples, zero off-step false leaves, seven true step transitions retained. The hook belongs to the shared pointer routine. Not an exhaustive visual audit of all submenus.

Private evidence: `build/pointer-color-owner144-before/`, `build/pointer-color-owner144-after/`, `build/pointer-color-diag/` in the shared repository. No game files, saves or generated executables are committed.

## Owner test

`build/pointer-color-test-144/PROBAR-PUNTERO-144.bat` launches the candidate at a 144 FPS cap in a foreground window with input enabled, Original/off upscaling and interface motion on. It uses its own profile containing an unmodified copy of the supplied save; it never writes to the supplied save or installed profile. It does not change the monitor refresh rate. Hover selectable options, hold still, move away and return; expect orange while selectable, yellow outside. Log: `prueba-144.log` beside the BAT.

- Additional 85-second RTX run at 144 FPS reaches laboratory -> Fotodex categories -> Pokemon grid, then My Space with Album/Research Titles/Statistics/Adventure Record. Screenshots identify each screen. 7471 hover samples, zero off-step false leaves, 10 true step transitions retained. Private evidence: `build/pointer-color-fotodex144/`. Photo evaluation and every individual album/detail screen were not exhaustively traversed.
