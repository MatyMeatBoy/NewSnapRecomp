# Work board: RTX tester + MatyMeatBoy

Read this before taking work. History and the previous Spanish board:
[PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). Rules: [CONTRIBUTING.md](../CONTRIBUTING.md).

## Current state (2026-11-14, after 0.9.0 stable): read first

- **Handoff (2026-11-15, after 0.9.20): [HANDOFF-0.9.20.md](HANDOFF-0.9.20.md).** Earlier: [0.9.15](HANDOFF-0.9.15.md), [0.9.14](HANDOFF-0.9.14.md), [0.9.12](HANDOFF-0.9.12.md).
- **0.9.7 (2026-11-15)** closes the handoff [HANDOFF-0.9.7.md](HANDOFF-0.9.7.md): dialogue and pointer above 60 fps, HD scenery shadows, launcher redesign. Notes: [releases/0.9.7.md](releases/0.9.7.md).

- `main` = 0.9.4 (stable line 0.9; UI-HZ-01 done properly, replacing the broken 0.9.3 change; MENU-03) (shader cache kept across updates with the same `SHADER_EPOCH` and translator; launcher presets with «Recomendado», «Mejoras» tab, in-game Screen/Enhancements rows, window auto, internal resolution by display, TEXPACK-01 runtime; 0.8.9 experimental ultrawide, ULTRAWIDE-01; 0.8.8 FSR frame generation with a HUD-less image, FG-02; 0.8.7 HD photo thumbnails and shadow «auto», SS-03; 0.8.6 FPS «display»; 0.8.5 NSP/NSZ/XCI/XCZ import): AMD RDNA 1/2 fixes (FOTO-01, CRISTAL-01), gyro (GYRO-01/02), windowed
  present (PRESENT-WIN-01), internal resolution by host scaling (SS-02), high FPS 90/120/144
  (FPS-01, RTX tester), FSR frame generation off by default with refresh fallback (FG-01/02).
- Owner hardware: RX 6900 XT, Samsung C27HG7x 144 Hz monitor, FreeSync. RTX tester: RTX 4060.
- Open queue: none. TEXPACK-01 pack generation shipped in 0.9.8 (launcher «Guardar texturas para el pack» +
  «Generar pack de texturas HD», BC1/BC3). Needing an NVIDIA RTX GPU, so not doable on the owner's PC: SS-03
  RTX check of HD thumbnails and DLSS-G (ideas below).
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
| OPTIONS-01 | P1 | DONE | MatyMeatBoy | 0.9.13: launcher and in-game menu show Resolución, Antialiasing, Escalado de rendimiento; A no longer changes values (MENU-05); area downscale above the window (AA-03). Former plan: Options as in other recomps (owner approved): Preset; Resolución; Antialiasing (Off / SMAA / FSR 4 / FSR 3.1 / DLSS Nativo, any resolution); Escalado de rendimiento (Calidad/Equilibrado/Rendimiento, only when wanted); Generación de fotogramas (only with FSR); Filtrado (juego/16×); Pantalla: modo, límite de FPS with VRR, VSync on/off (Vulkan modes only in advanced). Same names in the in-game menu. |
| AA-01 | P1 | DONE | MatyMeatBoy | 0.9.12: Native AA (FSR 4/3.1, DLSS) on top of internal resolution above 100 %; checked on RX 6900 XT, owner approved the look. |
| AA-04 | P1 | DONE | MatyMeatBoy | 0.9.14: SMAA 1x Low/Medium/High/Ultra before the HUD (High by default); upscaler off by default; console window gone (CONSOLE-03). [HANDOFF-0.9.14.md](HANDOFF-0.9.14.md). |
| TEXPACK-UI | P1 | DONE | MatyMeatBoy | Owner (2026-11-15): no colour textures redrawn by a generative upscaler, only shadows (abstract). «Texturas HD» is hidden in the launcher (`launcher.TEXTURE_PACKS_UI = False`) and, since 0.9.20, in the in-game menu and «Guardar texturas para el pack» is switched off; the runtime still loads a hand-made `texpack` folder. Do not bring it back without the owner asking. |
| LAUNCH-UI-02 | P1 | REVIEW | MatyMeatBoy | 0.9.20: own title bar, navigation buttons with icons, artwork drawn by code, Nunito, progress bars left to right and one for the HD shadows, window hidden when the game starts, «Verificar» / «Jugar». Left: the owner's look at it; Windows 10, display scaling and second monitor not checked. [HANDOFF-0.9.20.md](HANDOFF-0.9.20.md). |
| FAST-CHECK-01 | P1 | REVIEW | MatyMeatBoy | 0.9.20: files already verified are recognised by a receipt (size, time, file id, first and last MiB of large files) instead of being read again: game data, runtime, rebuild kit, HD shadows, prepared shaders. Explicit checks still read everything. Left: the shader skip on a GPU run after a driver update. [HANDOFF-0.9.20.md](HANDOFF-0.9.20.md). |
| MENU-FPS-01 | P2 | OPEN | — | Experimental: menus drawn at 120/144 fps with their logic at the original speed, like the pointers. See handoff. |
| HD-SHADOW-02 | P1 | REVIEW | MatyMeatBoy | 0.9.15: with the mode on the launcher builds the HD shadows of every level from the player's own `.drp` archives, no play-first step: the light maps (`^0^Lightmap`, BC6H signed) and the sun shadows painted per mesh (`^Shadow`, BC3, alpha); the two name rules are the curated list. Offline export identical to the GPU decode on 201 light maps (RTX 4060). Never ships enhanced textures. Left: the look and video memory on the RX 6900 XT. [HANDOFF-0.9.15.md](HANDOFF-0.9.15.md). |
| MENU-LANG-01 | P2 | REVIEW | MatyMeatBoy | 0.9.15: in-game menu in French, German, Italian, Japanese, Korean and Traditional Chinese (Spanish in 0.9.11). Tables checked id for id against the Spanish one; not reviewed by native speakers. |
| POINTER-02 | P1 | REVIEW | MatyMeatBoy | 0.9.11: real, averaged frame time on every pointer screen. If it still steps at 144 fps: position drawn only on interface steps (`cursor_mc`, see handoff). |
| README-01 | P2 | OPEN | — | Screenshots of the enhancements and the launcher for the README. |
| FPS-03 | P2 | OPEN | — | Throwable items above 60 fps: needs a save with fluffruit. |
| RTX-01 | P2 | REVIEW | MatyMeatBoy | HD photo thumbnails on RTX: verified by the owner. 0.9.20: DLSS frame generation (`frame_gen = dlss`, raw NGX feature 11), checked on an RTX 4060 Laptop GPU with saved generated frames. Left: RTX 50, the owner's look at it. [DLSS.md](DLSS.md). |

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
