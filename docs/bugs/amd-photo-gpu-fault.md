# FOTO-01 · Banded photos and «write invalid» closes on the RX 6900 XT (0.6)

Status: **REVIEW** · Owner: Claude · 2026-11-14
**Cause found and fixed (third round, below):** block views of 2D BC images in the AMD RDNA 1/2
driver. Tested physically on the RX 6900 XT in one session.

## Third round: cause and fix (RX 6900 XT, 0.7.0-tester, session on the owner's PC)

- **Test 1** (`1-todo-conservador`): still fails and ends in `device fault … write invalid`. None
  of the suspicions in the table below (async replay, skipped draws, ASTC, FSR 4, aliasing,
  prefetch, imported memory, fifo) is the cause.
- **Test 6** (F12 dump, `passes.txt`, last interface pass): the in-level thumbnail is a 360×240
  `VK_FORMAT_BC1_RGBA_UNORM_BLOCK` (vk133) texture with `gpu_owned 1, uploads 0`. The game
  **encodes it to BC1 by drawing** through an uncompressed view of its blocks (90×60, format 95
  RG32UI). The frame, the plate and the portrait are BC3 textures uploaded once (`uploads 1`)
  that nobody draws.
- The donor already documents (issue #5) that the AMD RDNA 2 driver writes **outside the
  memory** of a `BLOCK_TEXEL_VIEW_COMPATIBLE` image, which is why it draws 3D BC volumes into an
  intermediate image (`vk_exec.c bc_target`). 2D BC still used block views. This explains at once
  the «1 in 4 runs» thumbnail (4×4 block), the strips in neighbouring textures nobody draws and
  the `write invalid`s. The interface strip layers are a deduction from their joint
  disappearance, not an address measurement.

**Change** (`newsnap/bc_block_views_adapt.py`, `tests/test_bc_block_views.py`): a new
`AC_BLOCK_VIEWS` (`block_views` in the INI). By default it is `0` on the AMD RDNA 1/2 driver
branch (`vk_caps.amd_sc`) and `1` elsewhere, so nothing changes on NVIDIA. With `0`, 2D BC images
are created without block views. Their draws go to the donor's intermediate image, generalised
to 2D (one layer per texture layer). That image is refreshed from the texture at the start of
each pass and copied back at its end. A full clear outside a pass no longer lands only in the
intermediate image.

**Physical test** (RX 6900 XT, 26.10.1, FSR 4 Native AA, `mailbox`→`fifo`, shadow on, runtime
built with the 0.7.0-tester kit plus this adapter; the adapter produces byte for byte the same
tested sources): the log shows `vk: 2D BC textures are drawn through stand-ins (AC_BLOCK_VIEWS=0,
AMD RDNA 1/2 driver)` and `2D BC render target 360x240 (vk format 133) … 90x60 x 1 stand-in
(format 95)`. Complete thumbnail; frame, plate and portrait clean; the «Choose which photos to
show the professor» screen shows the 1080×720 photo and its thumbnail complete (owner's
screenshots); no `device fault` in the session.

**Limits:** one session; more levels, the album and the tutorial's «squares» are missing. Not run
on RTX (the default does not change there); suggested control: `AC_BLOCK_VIEWS=0` with the 540 s
photo route.

The sections below record the earlier rounds. At the time: **cause not established.** That
report left an opt-in experiment untested on AMD and an always-on log diagnostic to narrow the
next session on the RX 6900 XT. It does not change any GPU's default memory mode.

**Update, same day:** the host-pointer import hypothesis was refuted by the owner's test with
`shadow = 1`; see «Second round». Still no established cause or fix at that point.

## The owner's second round (RX 6900 XT, 0.6, 2026-11-14)

Local screenshots in `build/user-reports/rx6900xt-0.6/` (`level-*.webp`).

- With an already saved game there was no close, but the **photo thumbnail inside the level**
  comes out with the same bands, before anything is saved. The defect is in the photo's texture
  on the GPU, not in the copy when saving.
- With `shadow = 1` in `newsnap.ini` the result is the same. That session's log was not
  received, so the `mem: shadow storage…` line is still to be confirmed.
- The band pattern is **identical in different photos**: in memory order, one in four runs has
  image and three stay black. Fixed geometry.
- The professor's portrait, the Pokémon's name plate and the viewfinder frame also come out with
  strips. The «squares» GPU-WRITE-01 had fixed on the tutorial's Pikachu came back.
- With `fifo` presentation (instead of `fifo_relaxed`) the professor's portrait looks right and
  the rest is still wrong: at least part depends on the rhythm.
- With the upscaler off («Scaling bilinear») the thumbnail is still broken: FSR 4 is not needed
  for the defect.

On the RTX 4060, in the same level and with the same 0.6, thumbnail, portrait and plate come out
clean (`build/foto01-fsr3-540/shots/`). `AC_TRACE=gfx` trace of the expedition
(`build/foto01-trace-540/`): the in-level photo **uses no copies**; it is one more draw pass, and
the game launches 10 to 40 compute shaders per frame. None of this yet identifies the operation
failing on AMD.

### Test plan on the RX 6900 XT (no new binary, one at a time)

Each line goes in `newsnap.ini`; remove the previous one before testing the next.

| Setting | What it separates |
|---|---|
| `replay_async = 0` | Races between the game and replay on its own thread (suggested by the `fifo`/`fifo_relaxed` difference) |
| `tex_alias = 0` | New images that inherit another's content at the same address |
| `memory = import` | The VRAM mirror of pools used as buffers |
| `tex_prefetch = 0` | Texture uploads brought forward on a separate thread |
| `dump_key = 1` | Fixes nothing: with the defect on screen, F12 dumps the frame (`dump` folder next to the executable) with every pass and texture; it is the data that identifies the broken operation |

Since the second round's PR, the `amd_diag:` start-up line records in each log which combination
was tested.

## The owner's evidence (RX 6900 XT, real 0.6 runtime)

Local copies in `build/user-reports/rx6900xt-0.6/` (not uploaded):
`logs/newsnap.1cambieconfigs.log`, `logs/newsnap.nivel1tomefoto.log`, `album-bands-0.6.webp`.

- Both logs are from the 0.6 runtime (`snap_render`, `snap_supersample`, `snap_random_range`,
  official FSR providers, `log: …/logs/newsnap.log`), AMD driver 26.10.1 on the RDNA 1/2 branch.
  It is no longer the 0.1.x runtime of the `keyboard-after-photo.md` report.
- Both end the same way: `vk: device fault: "GPU fault"` with `write invalid at 0x…, precision
  0x1000`. The driver reports an invalid GPU write address with that precision; the message does
  not by itself identify the resource or show host pages without backing. It is not a CPU
  exception.
- Session 1: the owner changed graphics settings (FSR 3.1 → FSR 4, presentation mode) and the
  failure came later, following the tutorial. Session 2: no settings changed, FSR 4 on from the
  start; the failure came when taking the first photo of the first level, with the image already
  corrupt on screen.
- The album screenshot (same session 2, photos taken at 02:12) shows horizontal bands with real
  photo content and black in the rest; the bands start and end mid-row.
- There are no `pool_bounds:` lines: on that machine no image asked for more memory than its NVN
  storage. The lead in `amd-photo-bands-lead.md` is **ruled out for Snap**: besides, the game uses
  neither physical nor virtual pools (`physical 0 pools, virtual 0 pools`), so no image shares
  memory with a pool.

## What the game does when saving a photo (measured on RTX 4060, 0.6)

`AC_TRACE=gfx` trace of the photo route (`build/foto01-trace-gfx/`):

1. It creates a new pool over freshly reserved memory from the game's heap (`flags 0x24`,
   CPU_CACHED|GPU_CACHED): 0x5ef000 bytes for the photo and 0x5e000 for the thumbnail. It is the
   same pool object, initialised twice.
2. `nvnCommandBufferCopyTextureToBuffer` from the 1080×720 RGBA8 texture (and the 240×200 one)
   to that pool, in its own submission.
3. It waits with `nvnQueueFenceSync`/`nvnSyncWait`/`nvnQueueFinish` (it does not use
   `nvnCommandBufferFenceSync`), reads the bytes, encodes the JPEG and finalises the pool.

In the runtime that target is a **buffer imported by host pointer** (`VK_EXT_external_memory_host`)
over the game's pages, without a mirror: the new line confirms it on RTX («destination … through
the pool's own buffer»). The GPU writes directly to freshly reserved process memory pages.

## Ruled out with tests (all on RTX 4060; none counts as an AMD test)

| Hypothesis | Result | Evidence |
|---|---|---|
| The game reads before the copy ends because of a wrong fence | Ruled out | It uses `QueueFenceSync`, whose value covers the submission; trace `foto01-trace-gfx` |
| The temporal upscaler spoils the photo | Does not reproduce | 540 s route with FSR 3.1 Native AA: 4 copies with 0 differing bytes and 0 black rows, exit 0 (`foto01-fsr3-540`) |
| Draws skipped while the pipeline compiles (AMD mode) | Does not reproduce | `AC_GPL=0` and an empty pipeline cache: complete photo (`foto01-gpl0-cold`) |
| Images sharing memory with a pool | Ruled out for Snap | No physical/virtual pools; no `pool_bounds:` lines on AMD |
| ASTC without native support | Does not distinguish | The RTX lacks it too and uses the same GPU decoder; the photo is RGBA8 |

FSR 4 cannot run on the RTX (AMD's driver provides it), and both failing sessions had it on.
There is no evidence for or against its involvement.

## Working hypothesis at the time (unchecked)

AMD's Windows driver fails to write from the GPU to part of the pages of a buffer imported by
host pointer when those pages were just reserved. It would explain at once:

- the bands: 4 KiB pages ≈ one 1080 px RGBA row; runs of written and unwritten pages give bands
  that start and end mid-row;
- the `write invalid … precision 0x1000`: a GPU write to a page without backing;
- that it only happens on AMD and that the saved bytes already carry the bands.

The donor already avoids those imports on Linux and Wine («shadow storage», `AC_SHADOW`), for a
different problem with `amdgpu`. On native Windows they were active.

## Changes in this PR

`newsnap/photo_readback_adapt.py` (FOTO-01 reservation):

1. **Always-on log diagnostics, no settings.** Each photo-sized texture-to-buffer copy writes two
   lines (at most 24 copies per session):
   - `photo_log: copy …`: source texture (GPU ownership, uploads from memory, whether its storage
     was written afterwards), target, memory class, whether it goes through the pool's buffer or
     a mirror, and the active upscaler;
   - `photo_trace: gpu-t2b …`: differing bytes between the source image and what reached the
     buffer, black rows, **black 16 px tiles** in source/buffer and the buffer's first black runs
     (`y<row>:x<start>-<end>`).
   Cost: two copies to staging per accepted capture and CPU statistics after the fence. PNGs are
   still only written with `NEWSNAP_PHOTO_TRACE_DIR`.
2. **Opt-in memory experiment:** `AC_SHADOW=1` (or `shadow = 1` in `newsnap.ini`) turns on the
   donor's existing shadow storage; `AC_SHADOW=0` allows comparing the imports. The proposal to
   turn it on automatically per vendor is withdrawn: there is no AMD validation or controlled cost
   measurement to justify changing all its pools.
3. The diagnostic staging uses best-effort `vmaCreateBuffer`: if either allocation fails, what
   was already reserved is freed and the original operation is kept. It does not call
   `vk_staging`, which ends the process on failure. An atomic budget limits **pending diagnostic
   buffers to 64 MiB of requested bytes**; it is returned after destroying the buffers on
   completion. It does not include allocator overhead or the temporary CPU statistics buffer. If
   the budget is reached, that capture is skipped without using up the session limit. The game's
   copy is not changed.

## Tests run

- `python -m unittest tests.test_photo_readback`: 3 OK. The native fixture covers log-only mode,
  a partial band (`black_tiles16=0/7`, a `y32:x16-127` run) and the capture cap.
- Before the review fixes: private runtime built with the 0.6 kit (`build/foto01-build`): the
  candidate's selftest and loader OK.
- 400 s photo route on an RTX 4060 with that binary and no settings (`build/foto01-newbin`):
  exit 0, four pairs of lines, 0 differing bytes, 0 black tiles.
- 400 s photo route on an RTX 4060 with the published 0.6 and `AC_SHADOW=1`
  (`build/foto01-shadow1`): exit 0, photos without differences. It is the path the owner can test
  explicitly on AMD; it is not on by default.

### CPU review fixes (no new GPU test)

TDD was applied over the real generated C code. The regression first failed with exit 21 when a
failure was injected into the first allocation: the fatal path was still used. Afterwards the
three focused tests pass, including separate native processes covering failure of the
first/second allocation, partial cleanup, 24 captures without files (the 25th neither allocates
nor records commands), the 64 MiB limit with several uncompleted captures and budget recovery when
one completes. Eight threads also exercise 16,000 reservations/releases of the atomic budget
without exceeding it or leaving a pending balance. The earlier fixtures of padded rows, BGRA
channels and partial bands still pass. This tests CPU ownership and limits; it runs no GPU
barriers and does not validate the AMD driver. The binary with these last fixes still needs
building and integration by the coordinator.

## How to read the next RX 6900 XT log

| `photo_trace: gpu-t2b` line | Reading |
|---|---|
| `mismatch_bytes=0` and `black_tiles16=0/0` | Both GPU reads match; still to check: CPU visibility, shadow writeback, the bytes the game reads and encoding/loading |
| `mismatch_bytes>0`, black tiles only in the buffer | The GPU source and target reads differ; it narrows the path, but does not identify the import, driver or a specific cause |
| Black tiles already in the source | The source read already contains black; investigate production/synchronisation and check that this black is anomalous |

Immediate test on the installed 0.6, no new binary: add `shadow = 1` to `newsnap.ini` (or the
environment variable `AC_SHADOW=1`) and repeat the first level's photo. To separate FSR 4: also
repeat with the upscaler on FSR 3.1.

## Limits

- None of this was run on AMD. The shadow experiment may change nothing.
- Shadow mode copies memory on the CPU at every submission. On RTX the route kept ≈60 fps on
  average; no controlled performance comparison was made and there is no AMD measurement.
- `shadow = 1` in `newsnap.ini` applies even though the log notes it as an unknown key.
- Session 1's close did not happen when taking a photo; it is not shown to share a cause with
  session 2's.

## Batch tests (`tools/pruebas-amd/`)

Six `.bat` files, in elimination order. Each starts `newsnap.exe` with its settings through
environment variables (they override `newsnap.ini`, which is not modified) and copies the log to
`logs\pruebas\<name>.log` when the game closes.

| Test | Settings | Purpose |
|---|---|---|
| `1-todo-conservador` | `REPLAY_ASYNC=0`, `PIPE_SKIP=strict`, `ASTC=cpu`, `UPSCALING=off`, `TEX_ALIAS=0`, `TEX_PREFETCH=0`, `MEMORY=import`, `VK_PRESENT=fifo` | Decides: if it is still wrong, none of the suspicions is the cause and you go to 6 |
| `2-replay-sincrono` | `REPLAY_ASYNC=0` | Main suspicion: a race with the replay thread (the portrait changes with the presentation mode) |
| `3-sin-omitir-dibujos` | `PIPE_SKIP=strict` | RDNA 2's own path: draws skipped while their pipeline compiles |
| `4-astc-por-cpu` | `ASTC=cpu` | Interface textures on the CPU instead of the compute shader |
| `5-sin-fsr4` | `UPSCALING=fsr3` | Closes: all three logs with a GPU failure had FSR 4 on |
| `6-volcado-F12` | `DUMP_KEY=1`, `DUMP_N=2` | Dump of the frame with the defect on screen |

The order of suspicion is an estimate from the screenshots, not a result. They are copied next to
`newsnap.exe`. Dry-run checked with a placeholder executable (variables set, exit and log copy);
not run on AMD. The test version's packaging must include the folder: it is a Codex integration
point. (Since 0.8.2 the folder holds 1-normal, 2-volcado-F12, 3-interna-150 and 4-interna-200.)
