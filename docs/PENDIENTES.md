# Work board: Codex + Claude (+ any model)

Read this before taking work. History and the previous Spanish board:
[PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). Rules: [AGENTS.md](../AGENTS.md).

## Current state (2026-11-14, after 0.8.2-tester): read first

- `main` = 0.8.2-tester: AMD RDNA 1/2 fixes (FOTO-01, CRISTAL-01), gyro (GYRO-01/02), windowed
  present (PRESENT-WIN-01), internal resolution by host scaling (SS-02), high FPS 90/120/144
  (FPS-01, Codex), FSR frame generation off by default with refresh fallback (FG-01/02).
- Owner hardware: RX 6900 XT, 100 Hz monitor, FreeSync. Codex: RTX 4060.
- Owner's queue for **0.8.3** (Claude, in this order, no questions needed): high-resolution
  photos mod (SS-03), pacing/loading in extended modes, ultrawide (if feasible), VRR,
  launcher import of NSP/NSZ/XCI/XCZ and extracted `exefs`/`romfs` folders, remaining docs in
  English.
- Release recipe: bottom of this file.

## Tasks

States: FREE, IN PROGRESS, REVIEW (evidence given, awaiting independent review/physical
acceptance), DONE (moved to the history file).

| ID | P | State | Owner | Summary |
|---|---|---|---|---|
| SS-03 | P1 | IN PROGRESS | Claude | Higher-resolution photos. CPU reads of enlarged colour now average (box filter); `AC_SS_PHOTO=1` (off) enlarges photo targets as an experiment. Next: find which texture the selection/album shows (the big photo is the 360×240 thumbnail) and whether saving/scoring is unchanged. |
| PACE-AMD-01 | P1 | FREE | — | Camera-turn judder on RX 6900 XT: 60 fps on a 100 Hz FIFO display alternates 10/20 ms. Measure with present trace at 120 Hz/FreeSync before changing present modes. |
| FG-01/02 | P2 | REVIEW | Claude | FSR frame generation (SDK 2.4, no FFX swapchain), `frame_gen = fsr`, off by default, FSR 3.1/4 only; pauses when real fps > 0.55 × refresh. No HUD-less image (HUD trails possible). Not done: DLSS-G, VRR pacing. |
| SS-02 | P1 | REVIEW | Claude | Host-scaled internal resolution 125–300 % and "display"; 16:9 chain; `shadow_scale` for Snap's sun maps. RX 6900 XT verified at 60/120 fps. Missing: RTX, photo score comparison. [SUPERSAMPLING.md](SUPERSAMPLING.md). |
| FPS-01 | P1 | REVIEW | Codex | 90/120/144 FPS caps without timing patches. RTX verified; RX 6900 XT 120 fps at 200 % verified by Claude. [HIGH_FPS.md](HIGH_FPS.md). |
| VRR-01 | P1 | REVIEW | Codex | Present-timing status (unknown/fixed/variable); no active VRR mode yet. FreeSync physical check pending. |
| GYRO-01/02 | P1 | REVIEW | Claude | Six-axis IPC answered; `gyro_sens` (2.5). Physical controller test pending. |
| CRISTAL-01 | P1 | REVIEW | Claude | NaN-safe SPIR-V on AMD. A/B attribution and RTX control pending. |
| FOTO-01 | P0 | REVIEW | Claude | RDNA 1/2 BC block-view stand-ins. More levels/album and RTX control pending. |
| PRESENT-WIN-01, PIPE-MO-01 | P1/P2 | REVIEW | Claude | Windowed immediate without mailbox; motion pipeline prewarm. |
| PACE-01, CPU-WORKER-07, POOL-BOUNDS-01, HEAD-INTRO | P1/P2 | REVIEW | Codex/Claude | Pacing and CPU investigations; details in the archived board. |
| KEYBOARD-CRASH, TUTO-01, INPUT-01, GPU-WRITE-01, COLOR-01, PAD-01, MENU-01, LAUNCH-POSTBUILD-06, QA-AMD-01 | P0/P1 | REVIEW | Codex | Integrated fixes awaiting physical acceptance; details in the archived board. |

## Ideas after 0.8.3

- DLSS frame generation (needs RTX 40/50 to test). HUD-less image for FSR FG (needs a
  tone-mapped pre-HUD copy).
- Ultrawide: the donor's `resolution.c` "wide" set widens the 16:9 lens; Snap needs its own
  camera and UI-camera sites, and photos must stay 16:9 so scoring is unchanged.

## Release recipe (owner's PC)

Clone at `D:\01Claude\NewSnapRecomp\repo` (`core.autocrlf=false`, `core.eol=lf`), `.venv` with
Python 3.12 and `requirements-release`; SDK root `D:\01Claude\NewSnapRecomp\sdkroot`.
Merge the PR → `python -m tools.package_build_kit --sdk-root <sdkroot>` →
`tools/build_launcher.py` → `python -m tools.package_windows_release` →
`gh release create` → install with `updater.stage_update/apply_update` and
`maintenance.rebuild_runtime`. Candidate builds from the repo source: run
`newsnap.maintenance --worker` with the SDK root's Python (the kit's Python imports its own
`../source`). Delete test profiles, work folders and captures after use.
