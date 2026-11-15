# Handoff 0.9.14

State after 0.9.14 and what comes next, in priority order. The board is [PENDIENTES.md](PENDIENTES.md).

## Done in 0.9.14

- **AA-04 SMAA 1x with levels** (`newsnap/overlays/snap_smaa.c`, `newsnap/smaa_adapt.py`, `newsnap/overlays/shaders/`).
  Snap has no anti-aliasing of its own: a frame dump shows the scene, the bloom chain, one tonemap pass (3D LUT
  into an RGBA8 sRGB target of the game's size) and the HUD drawn straight over it. The old "SMAA" row came from
  the donor (Astral Chain) and did nothing in Snap. Now, at the start of the pass after that tonemap pass
  (`vk_exec_pass_begin`), the official SMAA (iryoku/smaa, MIT, `licenses/SMAA-MIT.txt`) runs in three compute passes:
  luma edges (UNORM view), blend weights (area and search textures), neighbourhood blending in linear light (sRGB
  view, encoded back). The result is copied over the picture and the HUD is drawn on it.
  Levels: `anti_aliasing = off | low | medium | high | ultra`, **High by default**; `smaa`, the value of earlier
  versions, reads as High. The SMAA steps aside while an upscaler (FSR or DLSS) resolves the scene.
  The SPIR-V headers (`newsnap/overlays/smaa_*_spv.h`) come from `third_party/astral/tools/build_shaders.py`'s
  `header_of`, compiled with the Vulkan SDK's glslc (`C:\VulkanSDK\1.4.363.0\Bin`). Re-run that after editing a
  `.comp` or `.glsl` file there.
- **The upscaler is off by default** and has its own row again ("Escalador (FSR / DLSS)"). FSR / DLSS as
  anti-aliasing on top of supersampling was a test; the owner prefers SMAA, as other emulators offer it (Ryujinx:
  SMAA Low to Ultra). Settings files from before 0.9.14 with the old default (Automatic) are read as Off once.
- **CONSOLE-03:** the game is linked as a windowed program (`-mwindows`, `newsnap/console_adapt.py`). Opened from
  Explorer, a shortcut or Steam, Windows 11 used to open a Windows Terminal tab titled NewSnap beside the game, which
  the old SW_HIDE trick could not hide. Logs still go to `newsnap.log`; pipes from the launcher and tools still work.
- **AA-03 (0.9.13):** internal resolution above the window is reduced by an area average, never bilinear.

## Next

1. **HD-SHADOW-02, the HD shadows mode built at install (main standing task).** Findings:
   - The game's files are `romfs/romfs.bin` + `romfs-index.bin` (ACRFS1). Textures are `.nutexb` members of the
     `.drp` archives (DRPF, extension CRC `5c156dbc`, 28 369 members, about 11 GB unpacked). `newsnap/drp.py`
     reads and decrypts them; `newsnap/overlays/snap_decode.c` (`NEWSNAP_OODLE_REQUESTS`) decodes them with the
     game's own Oodle decoder (tried on 1 355 textures, all CRC-verified).
   - Light maps are named `...^Lightmap.nutexb`: BC6H unsigned (`.nutexb` format `0xd8`), one level, 128 to 512.
   - **The runtime's texture hash can be computed offline:** `hash_bytes(nutexb data[:data_size], seed(w, h,
     NVN format))` equals the hash at upload. Format map seen so far (nutexb to NVN): 0xd8 to 79 (BC6H UF16),
     0x34 to 46, 0xa5 to 72, 0x85 to 70, 0x80 to 75 or 66 (the material decides: try both), 0xa0 to 68,
     0xd7 to 80?, 0xe5 to 78?, 0x35 to 41. Use `NEWSNAP_TEX_HASHLOG=<file>` (new diagnostic in snap_texpack.c,
     one line per upload: hash, w, h, NVN format, bytes, levels, vk format) to check more.
   - **Written, not wired yet:** `newsnap/overlays/snap_lightmap_export.c` (`.nutexb` footer, the same hash,
     Tegra block-linear deswizzle, CPU BC6H decoder for all 14 modes, RGBA16F DDS named by hash, as
     `hdshadows/src` expects) plus `snap_texpack_hash` / `snap_texpack_write_rgba16f`. To do:
     a. a request version 2 in `snap_decode.c` with a kind per member (1 = light map export into a folder);
     b. `newsnap/game_textures.py`: list the `^Lightmap.nutexb` members of every level, batch them (at most 10 000
        and 64 MiB per request), run `newsnap.exe` once (as `unpack.py` does), then `hdshadows.generate`;
     c. **verify the deswizzle and the BC6H modes against the GPU**: run a route with `AC_HD_SHADOWS=1` (the runtime
        dumps the same maps decoded by the GPU to `hdshadows/src`), export the same hashes offline and compare
        the half floats (they should be identical). The block-height rule and the mode bit layouts are the parts to check;
     d. the launcher builds the mode at install / update when «Modo Sombras HD» is on (no play-first step).
   - Then the curated list of colour textures with painted shadows (stairs, decks, rocks), by name, with the same
     export path (BC1/BC3/BC7 decoders needed, or GPU through the existing dump).
2. **MENU-FPS-01 (experimental, owner request):** menus drawn at 120/144 fps while their logic keeps the original
   speed, like the pointers (POINTER-02). Start from `snap_ui_pace.c`: the interface already steps at 60 Hz logic;
   what is missing is interpolating the drawn positions of menu elements between logic steps.
3. **MENU-LANG-01:** in-game menu in French, German, Italian, Japanese, Korean, Traditional Chinese.
4. **README-01:** screenshots (SMAA comparison, HD photos, launcher).
5. Blocked: FPS-03 (needs a fluffruit save), RTX-01 (needs an NVIDIA GPU).

## How to check SMAA

`AC_ANTI_ALIASING=off|high` on `tests/routes/photo-tutorial-expedition.txt` with `AC_SHOTS=w150-540:30
AC_SHOTS_FULL=1`; the log says `smaa: High on the WxH picture before the HUD`. The start menu (2D) shows almost no
difference; compare 3D frames.
