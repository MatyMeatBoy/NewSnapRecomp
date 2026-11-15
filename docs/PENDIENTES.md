# Work board: Codex + Claude (+ any model)

Read this before taking work. History and the previous Spanish board:
[PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). Rules: [AGENTS.md](../AGENTS.md).

## Current state (2026-11-14, after 0.8.9-tester): read first

- `main` = 0.8.9-tester (experimental ultrawide, ULTRAWIDE-01; 0.8.8 FSR frame generation with a HUD-less image, FG-02; 0.8.7 HD photo thumbnails and shadow «auto», SS-03; 0.8.6 FPS «display»; 0.8.5 NSP/NSZ/XCI/XCZ import): AMD RDNA 1/2 fixes (FOTO-01, CRISTAL-01), gyro (GYRO-01/02), windowed
  present (PRESENT-WIN-01), internal resolution by host scaling (SS-02), high FPS 90/120/144
  (FPS-01, Codex), FSR frame generation off by default with refresh fallback (FG-01/02).
- Owner hardware: RX 6900 XT, Samsung C27HG7x 144 Hz monitor, FreeSync. Codex: RTX 4060.
- Open queue: SS-03 RTX check of HD thumbnails, ULTRAWIDE-01 score check on a
  frame-exact shot ([ULTRAWIDE.md](ULTRAWIDE.md)), DLSS-G (needs RTX 40/50),
  loading times measured (below).
- Loading (2026-11-14, RX 6900 XT, 0.8.8, photo route 200 s, warm pipeline cache): 200 % internal
  resolution loads like 100 % (largest hitches: boot ≈350–375 ms, texture upload 312 ms at 100 %
  vs 203 ms at 200 %; after the first minute 0–1 frames over 25 ms at 200 %). The slow loads seen
  in extended modes come from the cold pipeline cache after a runtime rebuild or a resolution
  change; «Preparar gráficos» before playing removes them.
- Release recipe: bottom of this file.

## Tasks

States: FREE, IN PROGRESS, REVIEW (evidence given, awaiting independent review/physical
acceptance), DONE (moved to the history file).

| ID | P | State | Owner | Summary |
|---|---|---|---|---|
| SS-03 | P1 | REVIEW | Claude | HD photo thumbnails (`AC_HD_PHOTOS`, on): the 360×240 picture encoded to BC1 is drawn at 1080×720 and a copy replaces the BC1 thumbnail when sampled (`snap_hd_photo.c`, no vendor branch). Folder screen verified on RX 6900 XT; in-level preview and the big selection photo not opened by the route; RTX pending. Shadow option covers every square depth map and has `auto`. |
| IMPORT-01/02 | P1 | REVIEW | Claude | Launcher "Importar NSP/XCI/NSZ…": base NSP/NSZ/XCI/XCZ + update NSP/NSZ + prod.keys through `newsnap import` on the build kit's Python and a bundled hactool (`tools/build_hactool.py`). NSZ/XCZ/XCI are rebuilt as a temporary NSP by `newsnap/container.py` (nsz's NCZ format, NCA hash check). Synthetic tests only; not tested end to end (no dump on the owner's disk). |
| PACE-AMD-01 | P1 | REVIEW | Claude | Judder on fixed-refresh displays: 60 fps on the owner's 144 Hz FIFO display alternates 2/3 refreshes. `fps = display` caps at refresh/n (72 at 144 Hz) and presents mid-refresh from DWM vblank timing (`snap_latent_sync.h`, as Special K's Latent Sync). Trace: 100 % of presents 13.9 ms apart; the panel itself not measured (AMD lacks present timing). Owner's eye test pending. |
| FG-01/02 | P2 | REVIEW | Claude | FSR frame generation (SDK 2.4, no FFX swapchain), `frame_gen = fsr`, off by default, FSR 3.1/4 only; pauses when real fps > 0.55 × refresh. HUD-less image from the tonemapped scene before the interface pass (0.8.8). Not done: DLSS-G (needs RTX). |
| SS-02 | P1 | REVIEW | Claude | Host-scaled internal resolution 125–300 % and "display"; 16:9 chain; `shadow_scale` for Snap's sun maps. RX 6900 XT verified at 60/120 fps. Missing: RTX, photo score comparison. [SUPERSAMPLING.md](SUPERSAMPLING.md). |
| FPS-01 | P1 | REVIEW | Codex | 90/120/144 FPS caps without timing patches. RTX verified; RX 6900 XT 120 fps at 200 % verified by Claude. [HIGH_FPS.md](HIGH_FPS.md). |
| VRR-01 | P1 | REVIEW | Codex/Claude | Present-timing status (unknown/fixed/variable). Drivers, not the game, turn VRR on; borderless fullscreen can flip independently. Guidance in [DISPLAY.md](DISPLAY.md). FreeSync physical check pending (owner's monitor OSD). |
| GYRO-01/02 | P1 | REVIEW | Claude | Six-axis IPC answered; `gyro_sens` (2.5). Physical controller test pending. |
| CRISTAL-01 | P1 | REVIEW | Claude | NaN-safe SPIR-V on AMD. A/B attribution and RTX control pending. |
| FOTO-01 | P0 | REVIEW | Claude | RDNA 1/2 BC block-view stand-ins. More levels/album and RTX control pending. |
| PRESENT-WIN-01, PIPE-MO-01 | P1/P2 | REVIEW | Claude | Windowed immediate without mailbox; motion pipeline prewarm. |
| PACE-01, CPU-WORKER-07, POOL-BOUNDS-01, HEAD-INTRO | P1/P2 | REVIEW | Codex/Claude | Pacing and CPU investigations; details in the archived board. |
| KEYBOARD-CRASH, TUTO-01, INPUT-01, GPU-WRITE-01, COLOR-01, PAD-01, MENU-01, LAUNCH-POSTBUILD-06, QA-AMD-01 | P0/P1 | REVIEW | Codex | Integrated fixes awaiting physical acceptance; details in the archived board. |

## Ideas after 0.8.6

- DLSS frame generation (needs RTX 40/50 to test).
- Ultrawide shipped experimental in 0.8.9 (photos from the 16:9 view, HUD centred); its score
  equivalence still needs a frame-exact shot. [ULTRAWIDE.md](ULTRAWIDE.md).

## Release recipe (owner's PC)

Clone at `D:\01Claude\NewSnapRecomp\repo` (`core.autocrlf=false`, `core.eol=lf`), `.venv` with
Python 3.12 and `requirements-release`; SDK root `D:\01Claude\NewSnapRecomp\sdkroot`.
Merge the PR → `python -m tools.package_build_kit --sdk-root <sdkroot>` →
`tools/build_launcher.py` → `python -m tools.package_windows_release` →
`gh release create` (build hactool once with `tools/build_hactool.py --sdk-root <sdkroot>`) → install with `updater.stage_update/apply_update` and
`maintenance.rebuild_runtime`. Candidate builds from the repo source: run
`newsnap.maintenance --worker` with the SDK root's Python (the kit's Python imports its own
`../source`). Delete test profiles, work folders and captures after use.
