# Handoff: debugging directly on the RX 6900 XT

2026-11-14 · For the session working on the AMD PC. Summarises what is already known and what
to do first, so tests are not repeated. Detail and evidence in `amd-photo-gpu-fault.md` and
`integration-07.md`.

## What fails (only on the RX 6900 XT, driver 26.10.1, RDNA 1/2 branch)

1. **The photo thumbnail inside the level** with fixed-pattern black bands: 1 in 4 runs
   with image, the same in different photos. Saved photos come out the same.
2. **Strips in the interface:** the professor's portrait, the name plate, the viewfinder
   frame. With `fifo` presentation the portrait comes out fine.
3. **Squares** that GPU-WRITE-01 had fixed in the tutorial, back again.
4. **Closes** with `vk: device fault … write invalid`: three logs, all three with FSR 4 Native
   AA on, one of them with shadow on.

On the RTX 4060 none of this happens with the same runtime.

## Already ruled out (do not repeat)

| Hypothesis | How it was ruled out |
|---|---|
| Host-pointer import | `shadow = 1` on AMD: same look and another fault |
| Wrong fence when reading the photo | The game uses `QueueFenceSync`; trace on RTX |
| ASTC without native support, by itself | The RTX lacks it too and uses the same decoder |
| Image aliasing with pool memory | Snap uses neither physical nor virtual pools |
| FSR 4 as the cause of the bands | With the upscaler off the thumbnail is still broken |

Not reproduced on RTX forcing the AMD path (does not count as ruled out on AMD): `AC_GPL=0`
with an empty pipeline cache; FSR 3.1 Native AA; the complete conservative combination.

## First step on AMD: frame dump

This is the missing data. With the defect visible:

```
set AC_DUMP_KEY=1
set AC_DUMP_N=2
newsnap.exe        (F12 with the broken thumbnail on screen)
```

`dump/passes.txt` lists each pass, its targets, textures (address, mirror state, number of
uploads) and the shaders; the PNGs show which pass already produces the broken image. Look
for the photo's 1080×720 RGBA8 texture: if the PNG of the pass that draws it already has
bands, the failure is in that pass (shader, pipeline, target); if it comes out complete and
the one sampled later does not, it is in between (copy, alias, upload from memory).

`AC_DUMP_DRAWS=<seq>` splits that pass draw by draw. `AC_TRACE=gfx` gives one line per frame
with passes, draws, copies and dispatches.

## Second step: ruling out by settings (`tools/pruebas-amd/`)

Six `.bat` files in order. The first applies every suspicion at once; if it still fails with
it, none of them is the cause and only the dump remains. Each log carries an `amd_diag:` line
with the effective settings.

Suspicions, from most to least likely according to the screenshots (estimate, not measured):

1. A race with replay on its own thread (`AC_REPLAY_ASYNC=0`).
2. Draws skipped while their pipeline compiles: on RDNA 2 the pipeline library is off and
   `AC_PIPE_SKIP=fullscreen` skips instead of waiting (`AC_PIPE_SKIP=strict`). Also try
   `AC_GPL=1`, which is the NVIDIA path.
3. The compute ASTC decoder (`AC_ASTC=cpu`), for the interface strips.
4. The game's compute shaders: inside the level there are 10–40 dispatches per frame. On AMD
   the translator uses subgroups of 64 (32 fixed in compute) and storage buffers with
   alignment 4; on NVIDIA 32 and 16. No setting of its own: check in the dump the images and
   buffers they write.
5. FSR 4 only for the closes (`AC_UPSCALING=fsr3`).

## Reproducing without playing the tutorial by hand

`tests/routes/photo-tutorial-expedition.txt` goes through the tutorial, registration of two
photos, evaluation and the first expedition (540 s at 60 fps) with scripted input. It needs a
**copied** profile that has already passed initial setup:

```
set AC_INPUT=none
set AC_INPUT_SCRIPT=<path to the route file>
set AC_FPS=60
set AC_VK_PRESENT=fifo
newsnap.exe --exefs <GameData>\exefs --romfs <GameData>\romfs --profile <profile copy> --seconds 540
```

The photos are registered around frames 20178 and 20988; the expedition starts around 21170.
`AC_SHOTS=w330-535:5` with `AC_SHOTS_DIR` saves screenshots (they slow the game down: not
useful to measure pacing).

## Rules still in force

- Do not touch the owner's saves, photos, imports or keys: work on copies in `build/`. Do not
  upload game data, dumps or executables.
- Do not change game logic to skip steps.
- A test on AMD does not validate NVIDIA or vice versa; always note GPU, driver and the
  `amd_diag:` line.
- One GPU test at a time.
