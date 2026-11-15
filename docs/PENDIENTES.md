# Work board: RTX tester + MatyMeatBoy

Read this before taking work. History and the previous Spanish board:
[PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). Rules: [CONTRIBUTING.md](../CONTRIBUTING.md).

## Current state (2026-11-14, after 0.9.0 stable): read first

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
| — | — | — | — | No open rows (2026-11-15, after 0.9.7). Closed rows and their evidence: [PENDIENTES-HECHOS.md](PENDIENTES-HECHOS.md). A row closes when it is published and verified on the owner's hardware or by its route; an issue or an owner report reopens it here. |

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
