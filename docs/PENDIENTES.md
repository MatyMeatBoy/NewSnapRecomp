# Work board: RTX tester + MatyMeatBoy

Read this before taking work. History and the previous Spanish board:
[PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). Rules: [CONTRIBUTING.md](../CONTRIBUTING.md).

## Current state (2026-11-14, after 0.9.0 stable): read first

- `main` = 0.9.4 (stable line 0.9; UI-HZ-01 done properly, replacing the broken 0.9.3 change; MENU-03) (shader cache kept across updates with the same `SHADER_EPOCH` and translator; launcher presets with «Recomendado», «Mejoras» tab, in-game Screen/Enhancements rows, window auto, internal resolution by display, TEXPACK-01 runtime; 0.8.9 experimental ultrawide, ULTRAWIDE-01; 0.8.8 FSR frame generation with a HUD-less image, FG-02; 0.8.7 HD photo thumbnails and shadow «auto», SS-03; 0.8.6 FPS «display»; 0.8.5 NSP/NSZ/XCI/XCZ import): AMD RDNA 1/2 fixes (FOTO-01, CRISTAL-01), gyro (GYRO-01/02), windowed
  present (PRESENT-WIN-01), internal resolution by host scaling (SS-02), high FPS 90/120/144
  (FPS-01, RTX tester), FSR frame generation off by default with refresh fallback (FG-01/02).
- Owner hardware: RX 6900 XT, Samsung C27HG7x 144 Hz monitor, FreeSync. RTX tester: RTX 4060.
- Open queue: TEXPACK-01 pack generation (launcher button, BC7, Florio first), SS-03 RTX check of HD thumbnails,
  DLSS-G (needs RTX 40/50),
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
| SS-03 | P1 | REVIEW | MatyMeatBoy | HD photo thumbnails (`AC_HD_PHOTOS`, on): the 360×240 picture encoded to BC1 is drawn at 1080×720 and a copy replaces the BC1 thumbnail when sampled (`snap_hd_photo.c`, no vendor branch). Folder screen verified on RX 6900 XT; in-level preview and the big selection photo not opened by the route; RTX pending. Shadow option covers every square depth map and has `auto`. |
| IMPORT-01/02 | P1 | DONE | MatyMeatBoy | Launcher "Importar NSP/XCI/NSZ…": base NSP/NSZ/XCI/XCZ + update NSP/NSZ + prod.keys through `newsnap import` on the build kit's Python and a bundled hactool (`tools/build_hactool.py`). NSZ/XCZ/XCI are rebuilt as a temporary NSP by `newsnap/container.py` (nsz's NCZ format, NCA hash check). Synthetic tests only; not tested end to end (no dump on the owner's disk). **Accepted by the owner (2026-11-14) until an issue reports otherwise.** |
| PACE-AMD-01 | P1 | REVIEW | MatyMeatBoy | Judder on fixed-refresh displays: 60 fps on the owner's 144 Hz FIFO display alternates 2/3 refreshes. `fps = display` caps at refresh/n (72 at 144 Hz) and presents mid-refresh from DWM vblank timing (`snap_latent_sync.h`, as Special K's Latent Sync). Trace: 100 % of presents 13.9 ms apart; the panel itself not measured (AMD lacks present timing). Owner's eye test pending. |
| FG-01/02 | P2 | REVIEW | MatyMeatBoy | FSR frame generation (SDK 2.4, no FFX swapchain), `frame_gen = fsr`, off by default, FSR 3.1/4 only; pauses when real fps > 0.55 × refresh. HUD-less image from the tonemapped scene before the interface pass (0.8.8). Not done: DLSS-G (needs RTX). |
| SS-02 | P1 | REVIEW | MatyMeatBoy | Host-scaled internal resolution 125–300 % and "display"; 16:9 chain; `shadow_scale` for Snap's sun maps. RX 6900 XT verified at 60/120 fps. Missing: RTX, photo score comparison. [SUPERSAMPLING.md](SUPERSAMPLING.md). |
| LAUNCH-FG-01 | P1 | REVIEW | RTX tester | The launcher refused FSR frame generation with «needs reconstruction» even with a reconstruction selected, and dropped it when reading the file back. Cause: `validate_settings` applied the rules between two settings to a single setting (one changed value on save, one line on load), reading the missing upscaler as Original. Rules between settings are now judged only when both are present; whole combinations are still checked on save and launch. Automatic with an internal resolution above 100 % is accepted (MENU-03), and refused together with frame generation. `tests/test_launcher_fg.py`. Not run in the launcher window on the owner's PC. The RX 6900 XT test batch files (`pruebas-amd`) left the repository and the package; the updater and an installed launcher at start remove the shipped ones. Still open from the owner, for 0.9.5: Automatic as the default reconstruction (where Original is now) and recognised by frame generation; labels and terms as in other recomps («Escalado» / upscaling, as Longshot, Witch Time and the Astral Chain recomp use them) across launcher, menu and docs; one term for VRR/FreeSync/G-SYNC; a VRR frame cap a few fps under the refresh rate so the game stays inside the variable range (about 138 at 144 Hz); HD photo thumbnails appear late when first shown, try a compressed format as the game uses. |
| REL-095 | P1 | OPEN | — | Owner requests, moved to 0.9.5 when 0.9.4 became the hotfix (2026-11-15). **Priority: the HD mod.** **Supersampling options:** make the choices easier and fit them to the display. **HD shadows mod** shipped with them. **Clean repository and releases:** no test batch files (`pruebas-amd`) or other files a player does not need in the Windows package or the release assets. **Tidier package:** the extracted folder shows close to a thousand loose files; group them so the top level is the launcher and a few folders. Launcher video page: same internal-resolution scale as the in-game page (MENU-03). |
| FPS-02 | P1 | OPEN | — | Frame-counting game logic outside the interface at more than 60 fps (item throws in later stages, cooldowns, input repeat) has not been audited; UI-HZ-01 only covers the interface movies. Owner asks for every rate-dependent path to follow real time. |
| UI-HZ-01 | P1 | REVIEW | RTX tester | The interface (game interface objects driving Flash-style movies) counted frames: logic, timelines and the per-frame event 22 ran 2.4x at 144 fps. Above 60 fps the handler (`main+0x7835d0`) now branches to its drawing section on the frames that are not due, so all three run 60 times a second and the interface is drawn every frame (`snap-2.0.1-ui-pace.txt`, `snap_ui_pace.c`). The 0.9.3 version and three other attempts broke the interface; they are recorded in [HIGH_FPS.md](HIGH_FPS.md). RTX 4060: route to the expedition start at 144 fps matches 60 fps, watched live by the owner. Not run on AMD; screens outside the route not watched. |
| MENU-03 | P2 | REVIEW | RTX tester | In-game internal resolution as one scale around the game's 100 %; Automatic upscaler reads as Original while the internal resolution is above 100 % (`cfg_upscaling`). RTX: Auto + 150 % draws 2880x1620 without an upscaler, Auto + 100 % keeps DLAA. Launcher page not changed. |
| FPS-01 | P1 | REVIEW | RTX tester | 90/120/144 FPS caps without timing patches. RTX verified; RX 6900 XT 120 fps at 200 % verified by MatyMeatBoy. [HIGH_FPS.md](HIGH_FPS.md). |
| VRR-01 | P1 | REVIEW | RTX tester/MatyMeatBoy | Present-timing status (unknown/fixed/variable). Drivers, not the game, turn VRR on; borderless fullscreen can flip independently. Guidance in [DISPLAY.md](DISPLAY.md). FreeSync physical check pending (owner's monitor OSD). |
| GYRO-01/02 | P1 | DONE | MatyMeatBoy | Six-axis IPC answered; `gyro_sens` (2.5). Physical controller test pending. **Accepted by the owner (2026-11-14) until an issue reports otherwise.** |
| CRISTAL-01 | P1 | REVIEW | MatyMeatBoy | NaN-safe SPIR-V on AMD. A/B attribution and RTX control pending. |
| FOTO-01 | P0 | REVIEW | MatyMeatBoy | RDNA 1/2 BC block-view stand-ins. More levels/album and RTX control pending. |
| PRESENT-WIN-01, PIPE-MO-01 | P1/P2 | REVIEW | MatyMeatBoy | Windowed immediate without mailbox; motion pipeline prewarm. |
| PACE-01, CPU-WORKER-07, POOL-BOUNDS-01, HEAD-INTRO | P1/P2 | REVIEW | RTX tester/MatyMeatBoy | Pacing and CPU investigations; details in the archived board. |
| KEYBOARD-CRASH, TUTO-01, INPUT-01, GPU-WRITE-01, COLOR-01, PAD-01, MENU-01, LAUNCH-POSTBUILD-06, QA-AMD-01 | P0/P1 | REVIEW | RTX tester | Integrated fixes awaiting physical acceptance; details in the archived board. |

## Ideas after 0.8.6

- DLSS frame generation (needs RTX 40/50 to test).
- Ultrawide shipped experimental in 0.8.9 (photos from the 16:9 view, HUD centred); its score
  equivalence accepted by the owner (2026-11-14) until an issue reports otherwise.
  [ULTRAWIDE.md](ULTRAWIDE.md).

## Release recipe (owner's PC)

Clone at `D:\Dev\NewSnapRecomp\repo` (`core.autocrlf=false`, `core.eol=lf`), `.venv` with
Python 3.12 and `requirements-release`; SDK root `D:\Dev\NewSnapRecomp\sdkroot`.
Merge the PR → `python -m tools.package_build_kit --sdk-root <sdkroot>` →
`tools/build_launcher.py` → `python -m tools.package_windows_release` →
`gh release create` (build hactool once with `tools/build_hactool.py --sdk-root <sdkroot>`) → install with `updater.stage_update/apply_update` and
`maintenance.rebuild_runtime`. Candidate builds from the repo source: run
`newsnap.maintenance --worker` with the SDK root's Python (the kit's Python imports its own
`../source`). Delete test profiles, work folders and captures after use.
