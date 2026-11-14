# Work board: RTX tester + MatyMeatBoy

Read this before taking work. History and the previous Spanish board:
[PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). Rules: [CONTRIBUTING.md](../CONTRIBUTING.md).

## Current state (2026-11-14, after 0.8.6-tester): read first

- `main` = 0.8.6-tester (FPS «display» with mid-refresh presents, PACE-AMD-01; repo docs all in English; 0.8.5 added NSP/NSZ/XCI/XCZ import): AMD RDNA 1/2 fixes (FOTO-01, CRISTAL-01), gyro (GYRO-01/02), windowed
  present (PRESENT-WIN-01), internal resolution by host scaling (SS-02), high FPS 90/120/144
  (FPS-01, RTX tester), FSR frame generation off by default with refresh fallback (FG-01/02).
- Owner hardware: RX 6900 XT, Samsung C27HG7x 144 Hz monitor, FreeSync. RTX tester: RTX 4060.
- Open queue: SS-03 photos (needs an RTX comparison), ULTRAWIDE-01 (photo capture and HUD
  sites, see [ULTRAWIDE.md](ULTRAWIDE.md)), HUD-less image for FSR FG, DLSS-G (needs RTX 40/50),
  loading times in the extended modes.
- Release recipe: bottom of this file.

## Tasks

States: FREE, IN PROGRESS, REVIEW (evidence given, awaiting independent review/physical
acceptance), DONE (moved to the history file).

| ID | P | State | Owner | Summary |
|---|---|---|---|---|
| SS-03 | P1 | IN PROGRESS | MatyMeatBoy | Higher-resolution photos. CPU reads of enlarged colour average (box filter). `AC_SS_PHOTO=1` (off) enlarges 1080×720/360×240/240×200 colour targets, but the big photo on the selection screen comes from the 360×240 **BC1** thumbnail, which cannot be enlarged; on the RX 6900 XT its 4×4 blocks look almost flat, which may be the FOTO-01 stand-in path (90×60 block view) rather than the game. Next: RTX comparison with `AC_BLOCK_VIEWS=1`, then decide whether to point that screen at the 1080×720 photo. |
| IMPORT-01/02 | P1 | REVIEW | MatyMeatBoy | Launcher "Importar NSP/XCI/NSZ…": base NSP/NSZ/XCI/XCZ + update NSP/NSZ + prod.keys through `newsnap import` on the build kit's Python and a bundled hactool (`tools/build_hactool.py`). NSZ/XCZ/XCI are rebuilt as a temporary NSP by `newsnap/container.py` (nsz's NCZ format, NCA hash check). Synthetic tests only; not tested end to end (no dump on the owner's disk). |
| PACE-AMD-01 | P1 | REVIEW | MatyMeatBoy | Judder on fixed-refresh displays: 60 fps on the owner's 144 Hz FIFO display alternates 2/3 refreshes. `fps = display` caps at refresh/n (72 at 144 Hz) and presents mid-refresh from DWM vblank timing (`snap_latent_sync.h`, as Special K's Latent Sync). Trace: 100 % of presents 13.9 ms apart; the panel itself not measured (AMD lacks present timing). Owner's eye test pending. |
| FG-01/02 | P2 | REVIEW | MatyMeatBoy | FSR frame generation (SDK 2.4, no FFX swapchain), `frame_gen = fsr`, off by default, FSR 3.1/4 only; pauses when real fps > 0.55 × refresh. No HUD-less image (HUD trails possible). Not done: DLSS-G, VRR pacing. |
| SS-02 | P1 | REVIEW | MatyMeatBoy | Host-scaled internal resolution 125–300 % and "display"; 16:9 chain; `shadow_scale` for Snap's sun maps. RX 6900 XT verified at 60/120 fps. Missing: RTX, photo score comparison. [SUPERSAMPLING.md](SUPERSAMPLING.md). |
| FPS-01 | P1 | REVIEW | RTX tester | 90/120/144 FPS caps without timing patches. RTX verified; RX 6900 XT 120 fps at 200 % verified by MatyMeatBoy. [HIGH_FPS.md](HIGH_FPS.md). |
| VRR-01 | P1 | REVIEW | RTX tester/MatyMeatBoy | Present-timing status (unknown/fixed/variable). Drivers, not the game, turn VRR on; borderless fullscreen can flip independently. Guidance in [DISPLAY.md](DISPLAY.md). FreeSync physical check pending (owner's monitor OSD). |
| GYRO-01/02 | P1 | REVIEW | MatyMeatBoy | Six-axis IPC answered; `gyro_sens` (2.5). Physical controller test pending. |
| CRISTAL-01 | P1 | REVIEW | MatyMeatBoy | NaN-safe SPIR-V on AMD. A/B attribution and RTX control pending. |
| FOTO-01 | P0 | REVIEW | MatyMeatBoy | RDNA 1/2 BC block-view stand-ins. More levels/album and RTX control pending. |
| PRESENT-WIN-01, PIPE-MO-01 | P1/P2 | REVIEW | MatyMeatBoy | Windowed immediate without mailbox; motion pipeline prewarm. |
| PACE-01, CPU-WORKER-07, POOL-BOUNDS-01, HEAD-INTRO | P1/P2 | REVIEW | RTX tester/MatyMeatBoy | Pacing and CPU investigations; details in the archived board. |
| KEYBOARD-CRASH, TUTO-01, INPUT-01, GPU-WRITE-01, COLOR-01, PAD-01, MENU-01, LAUNCH-POSTBUILD-06, QA-AMD-01 | P0/P1 | REVIEW | RTX tester | Integrated fixes awaiting physical acceptance; details in the archived board. |

## Ideas after 0.8.6

- DLSS frame generation (needs RTX 40/50 to test). HUD-less image for FSR FG (needs a
  tone-mapped pre-HUD copy).
- Ultrawide: 3D widening works (`main+0x29641c`), backed out because photos are captured from the
  widened frame and the HUD stretches. [ULTRAWIDE.md](ULTRAWIDE.md).

## Release recipe (owner's PC)

Clone at `D:\Dev\NewSnapRecomp\repo` (`core.autocrlf=false`, `core.eol=lf`), `.venv` with
Python 3.12 and `requirements-release`; SDK root `D:\Dev\NewSnapRecomp\sdkroot`.
Merge the PR → `python -m tools.package_build_kit --sdk-root <sdkroot>` →
`tools/build_launcher.py` → `python -m tools.package_windows_release` →
`gh release create` (build hactool once with `tools/build_hactool.py --sdk-root <sdkroot>`) → install with `updater.stage_update/apply_update` and
`maintenance.rebuild_runtime`. Candidate builds from the repo source: run
`newsnap.maintenance --worker` with the SDK root's Python (the kit's Python imports its own
`../source`). Delete test profiles, work folders and captures after use.
