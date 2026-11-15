# Handoff for 0.9.7 — 2026-11-15

Written when the owner moved to another PC. `main` holds everything described under "Integrated"; nothing
described under "Open" is fixed. The owner's plan: **one release, 0.9.7, with every open item below, the HD shadows
feature included.** No 0.9.5 or 0.9.6 is planned. The version in `newsnap/version.py` is still 0.9.4.

Board: [PENDIENTES.md](PENDIENTES.md). Timing background: [HIGH_FPS.md](HIGH_FPS.md).

## Rules the owner has given (not all are in AGENTS.md)

- Commit and publish as `MatyMeatBoy`. Work without asking, decide, take the hard items first.
- When a release is asked for: short verification, then publish. Do not chain long RTX routes.
- Visual or pacing changes: compare real screenshot series against a 60 fps run before publishing. Counters and
  traces alone let the broken 0.9.3 through.
- The owner's problems are on AMD (RX 6900 XT, 144 Hz FreeSync). The test PC here is an RTX 4060 laptop; say which
  GPU every piece of evidence comes from.
- Never touch the owner's saves, photos, imports or keys; test on copies under `build/`; no game data or derived
  executables in git or releases.

## Integrated in `main` after 0.9.4 (not released)

| ID | What | Checked | Not checked |
| --- | --- | --- | --- |
| LAUNCH-FG-01 | Launcher saves FSR frame generation one setting at a time | Unit tests | Launcher window; owner's PC |
| — | `pruebas-amd` removed from git and the package; installed copies deleted by the updater and at launcher start | Unit tests | An installed 0.9.4 updating |
| VRR-02 | `fps = vrr`: cap at `refresh − refresh²/3600` (144 Hz → 138.24) | RTX: log `frame rate: 138 fps cap` at 144.063 Hz, interface still 60 steps a second | A VRR display; AMD |
| ESCALADO-01 | Automatic is the default upscaler with Native quality; launcher wording: «Escalado», «Calidad del escalado», «Resolución interna» (list centred on 100 %), «Límite de FPS» with «Según la pantalla» and «VRR» | Unit tests | Launcher window; the in-game menu wording is unchanged |
| CONSOLE-02 | The game hides a console window that exists only for it (`snap_console.c`) | Compiles, runs | Whether the window is actually gone when started from the launcher |
| PKG-01 | Tcl time zones, Tcl/Tk messages and demo images dropped from the launcher package (about 770 files) | — | **A launcher built this way has not been started.** Build it and open every tab before releasing |
| — | Observers `NEWSNAP_PAD_TRACE=1` (pad update, interface events) and `tools/dev/` (below) | Used for INPUT-HZ-01 | — |

Suite on this PC before the observers were added: 507 run, 506 pass (the other is this PC's CRLF checkout of an SVG).

## Open, in the owner's priority order

### 1. INPUT-HZ-01 — a press in the middle of a dialogue line skips it above 60 fps (regression of 0.9.4)

**Symptom (owner, RX 6900 XT, 144 fps).** Pressing A while a line is being typed should complete the line, and a
second press should go to the next one. Often one press does both, "as if A were pressed twice".

**Reproduced (RTX 4060).** Route: A every 40 ticks (0.67 s), held 6 ticks, from tick 900; opening dialogue with the
professor. `tools/dev/shots.py pages`:

| Run | Presses during the dialogue |
| --- | --- |
| 60 fps | complete, advance, complete, advance… |
| 144 fps, 0.9.4 interface pacing on | advance on almost every press; the run ends 6 s ahead of the 60 fps one |
| 144 fps, `AC_SNAP_UI_PACE_PATCH=0` | complete, advance… as at 60 fps |
| 90 fps, pacing on | mostly alternating, an occasional skip |

**So the cause is UI-HZ-01 itself**, not something older: gating the interface handler to 60 steps a second leaves
it out of step with code that still runs on every frame.

**Ruled out, with evidence.**

- Typing speed: brightness of the text box every 0.1 s is the same curve at 60 and 144 fps.
- The pad: `main+0x925b60` (pad update; object `+0x44` buttons, `+0x48` pressed, `+0x4c` released, `+0x50` previous)
  runs once per presented frame and a press lasts exactly one update. A 33 ms press skips as well, so key repeat
  and hold length are not involved.
- Presses are not lost either: every scripted press is acted on within two frames.

**What is known about the path.** The events the handler raises (`main+0x7a9a70`, `w1` = event) on a page change
are 16, 8, 18, 10, then 21, 12, then 5, 6, 7 for the new page. They are state transitions of the interface
object's state machine (state names compared as strings around `main+0x7935xx`), not input events. A press that
only completes the line raises none. The requested state lives at object `+0x4b8`; the function that sets it is
`main+0x79bd90` (virtual; its only reference is a data slot). The dialogue script itself is not in `main`
(no strings): the decision "still typing or ready" is taken by game code that asks for the state change.

**Working hypothesis.** A game-side controller runs every frame (144 a second) and keeps a frame count or a
one-frame handshake with the interface logic (60 a second), so it believes the line is finished early.
The Start menu pointer (item 2) points at the same layer.

**Next step.** In a private build, add an observer at `main+0x79bd90` that walks the guest frame-pointer chain
(`x29`, saved `x30` at `[x29+8]`) and logs the return addresses when a press is followed by the request; that names
the controller. Then either (a) step that controller on the same due frames as the handler, keeping the pad's
pressed bits from the frames in between so no press is lost, or (b) give it real elapsed time. Whatever is chosen
has to be compared against 60 fps with `shots.py pages` and with screenshot series, at 90, 120 and 144 fps.

**Do not** gate the pad update itself to 60 a second: gameplay code reads it every frame and would see each press
two or three times.

### 2. FPS-02 — pointer and other game logic that counts frames

Owner, 144 fps: the pointer of the Start (pause) menu moves much faster than at 60 fps; the camera pointer feels
about right. Not reproduced here yet (no route opens that menu). Also not audited: item throws in later stages,
cooldowns, input repeat. The game's timer (`main+0x6abea0`) reports all three channels in measured-time mode
(mode 0) at 144 fps, so the fixed-step channel is not what speeds things up; look for per-frame constants in the
menu controllers. Expect it to share its cause with item 1.

### 3. HD shadows — an Enhancements option, not a separate mod

Owner's definition: improve every shadow that is not a character's (plants, scenery: visibly lower quality than
the character shadows) with upscaling, so they look smooth and high definition.

Findings so far, **none confirmed**:

- Scene draws sample two 1024×1024 D32F shadow maps the game renders itself (one rendered every frame, the other
  not rendered in the dumped frame). `shadow_scale` already enlarges square depth maps.
- The level also samples many single-level BC6H textures (128×128 and 512×512) and BC3 512×512 textures that look
  like baked lighting. Hypothesis: the low-quality scenery shadows are baked into these, which is why
  `shadow_scale` does not help them.
- The in-level dumps taken so far landed on a white fade, so no texture has been matched to a shadow on screen.

Plan: (1) dump a frame inside a level (`AC_DUMP`, `AC_DUMP_KEY`) and match the blocky shadow on screen to a texture;
(2) if it is baked: extend TEXPACK-01 (`snap_texpack.c`, `tools/texpack.py`, today RGBA8/BC only) to dump and
replace BC6H, upscale with a model suited to lighting data rather than photographs, and ship the result as a
generated pack the player builds from their own game (no game data in releases); (3) if it is the second depth
map: raise its resolution and filter it; (4) one Enhancements row, off by default until compared with the original
image. Keep the game's colour and post-processing unchanged.

### 4. Launcher redesign

The owner wants it to resemble the open-source Recompia (Pokopia) launcher: sidebar, hero art, a Play button,
status chips, adapted to our options. Not started. Check its licence before copying code; do not reuse its art or
logo. The launcher is Tk (`newsnap/launcher.py`), packaged by `tools/build_launcher.py`.

### 5. Smaller items

- **Supersampling choices fitted to the display**: the list is now centred on 100 %; offering only the steps that
  make sense for the detected display is not done.
- **One vocabulary everywhere**: the launcher is done; the in-game Screen/Enhancements menu and the docs still say
  "reconstruction" in places. VRR is the chosen word for FreeSync / G-SYNC.
- **Tidier package**: about 770 files fewer; the top level still shows many loose files. Aim: the launcher and a
  few folders.
- **Releases**: assets of 0.7 to 0.9.4 still contain `pruebas-amd`; 0.9.3 is marked as defective. Decide with the
  owner whether to delete old pre-releases.
- **HD photo thumbnails**: the owner reports them working well on AMD in 0.9.4; only the first one loads a little
  slowly. Minor; a compressed upload format was the idea if it is ever worth doing.
- **CONSOLE-02 / PKG-01**: verify as listed in the table above.

## Releasing 0.9.7

Bump `newsnap/version.py` and `assets/windows-version.txt`, add a capability if the runtime must be rebuilt, write
`docs/releases/0.9.7.md`, then the recipe at the bottom of [PENDIENTES.md](PENDIENTES.md). State in the notes what
was not run on AMD.

## Tools (`tools/dev/`)

- `inspect_main.py <exefs/main> dis|callers|imports|strings|refs|addimm …` — read-only static inspection.
- `route_run.py` — plays a scripted input route on copies of a runtime and a profile, with any `AC_*`/`NEWSNAP_*`
  setting; `AC_SHOTS=w14-108:0.5` takes a picture every half second of game time.
- `shots.py lead|sheet|pages` — compares two runs of one route.
- Traces: `NEWSNAP_PAD_TRACE=1`, `NEWSNAP_UI_PACE_TRACE=1`, `NEWSNAP_UI_TRACE=1`, `NEWSNAP_TIMER_TRACE=1`.

A candidate runtime is built with `python -m newsnap.maintenance --worker --data <GameData> --work <dir> --sdk
<kit sdk> --source-revision x` (needs the FSR SDK, `NEWSNAP_FSR_SDK`). Compile errors are not in `compile.log`:
run ninja from `<work>/source` with `-f ../updated/build.ninja`.

Evidence of this session (shots, logs, routes) is private under `build/a2-*`, `build/a3-*`, `build/a4-*` on the
RTX test PC and is not in git.
