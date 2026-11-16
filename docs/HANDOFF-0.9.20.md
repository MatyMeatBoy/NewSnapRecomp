# Handoff 0.9.20

State after 0.9.20. The board is [PENDIENTES.md](PENDIENTES.md); the previous handoff is
[HANDOFF-0.9.15.md](HANDOFF-0.9.15.md). Owner decision that stands: no colour textures redrawn by a generative
upscaler, only shadows; «Texturas HD» is hidden in the launcher and in the in-game menu.

## Done in 0.9.20

### DLSS frame generation (RTX-01)

- `frame_gen = dlss` / `AC_FRAME_GEN=dlss`. Raw NGX feature 11 with `nvngx_dlssg.dll` 310.9.16 from the pinned NVIDIA
  DLSS commit (`tools/fetch_dlss.py`), as NVIDIA's DLSS-FG Programming Guide describes: no Streamline. Details and
  parameters: [DLSS.md](DLSS.md).
- `newsnap/overlays/snap_dlssg.inc` (included at the end of `vk_dlaa.c`) creates and evaluates the feature;
  `newsnap/overlays/snap_fsr_fg.c` keeps each frame's depth and motion vectors in a ring of three
  (`snap_fg_prepare_dlss`, called right after the Super Resolution evaluation) and generates on the present thread.
  One lock serialises NGX between the two threads.
- **The recorder rule that cost a device fault:** in the replay's command buffer only the calls `vk_rec.h` wraps are
  made in order by the recorder thread. `vkCmdPipelineBarrier` is not wrapped: called from the replay thread it is
  made at once, ahead of the copies queued before it. Use `vkCmdPipelineBarrier2` there (`replay_layout_general`,
  `replay_sync`). The HUD-less picture of FSR frame generation had the same fault and is fixed.
- Checked on an RTX 4060 Laptop GPU, driver 616.92: 500 s of `tests/routes/photo-tutorial-expedition.txt` with DLSS
  Native AA and frame generation, 59 fps real, no device fault; generated frames saved with
  `NEWSNAP_FG_SHOTS=<folder>` and looked at: clean in ordinary motion, the usual blur on fast limb movement.
  FSR frame generation run again after the recorder fix.
- Not done: RTX 50 multi-frame generation; Reflex (NGX does not require it; latency is one frame more).

### Launcher look (LAUNCH-UI-02)

- `newsnap/window_chrome.py`: the native window without its caption (resize, snap and taskbar kept), own bar, DWM
  colours, fallbacks to a tinted native bar and to a plain window. `newsnap/artwork.py`: every picture drawn with
  Pillow at run time. `newsnap/shell_ui.py`, `newsnap/sidebar_ui.py`, `newsnap/theme.py`, `newsnap/fonts.py`
  (Nunito, SIL OFL, `assets/fonts`, loaded privately, Segoe UI when it fails), `newsnap/progress_bar.py` (`SnapBar`).
- `Launcher._handle(event)` holds the event loop's body. The two `game_started` branches are one: the progress note
  ends and the window is withdrawn; it comes back on a failure and closes when the game ends.
- `newsnap/play_action.py`: the main button's label and action as a function of `home_state.state()`.
- Not checked: a real mouse drag, edge snapping, Windows 10, display scaling above 100 %, a second monitor.

### Files recognised without reading them again (FAST-CHECK-01)

- `newsnap/verified_files.py`: a receipt per file (size, modification time, volume and file id, the first and last
  MiB of files of 32 MiB or more, the SHA-256 that was computed). Stores: `<GameData>/newsnap-verified-files.json`
  and one beside each cached build kit. Known limit, stated in the module: a file rewritten in place with its size
  and time restored is only found by the full checks.
- Fast: the check before each start, the cached kit, the original data in a non-forced rebuild, the HD shadows when
  built (no archive scan), the shader preparation when nothing is new (`NEWSNAP_PREPARE_ALWAYS=1` forces it). Full:
  «Verificar datos», «Verificar / reconstruir juego», imports, downloaded kits and updates, rollback.
- Measured on this PC: saved kit check 18.9 s to 1.8 s; original data in a rebuild 7 s to 0.005 s; HD shadows
  already built 2.9 s to 0.009 s.

## Open

1. **A picture of another moment for one or two frames in the transition into a course** (owner, 0.9.15). Not
   reproduced yet: see the board.
2. **The frame over a subject above 60 fps** (owner request): being investigated on `feature/reticle-hz`.
3. MENU-FPS-01, README-01, FPS-03 as before.
