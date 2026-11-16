# Handoff 0.9.15

State after 0.9.15 and what comes next. The board is [PENDIENTES.md](PENDIENTES.md); the previous handoff is
[HANDOFF-0.9.14.md](HANDOFF-0.9.14.md).

## Done in 0.9.15

### HD-SHADOW-02, point 1: every light map at install, without playing first

- `newsnap/game_textures.py` lists the baked shadow textures of every level archive
  (`nx/Pack/LevelComposite/master/LC_*.drp`, read through `romfs-index.bin` and `newsnap/drp.py`), hands them to the
  game's own Oodle decoder in requests of 400 members, has `newsnap/hdshadows.py` enlarge them and removes the
  intermediate pictures. `<GameData>/hdshadows/state.json` remembers the hash of each member, so a stopped build
  goes on where it was; `<GameData>/hdshadows/all-maps` says every level is built. With that file present the
  runtime saves nothing while playing (`snap_texpack.c`).
- Requests are version 2 (`newsnap/overlays/snap_decode.c`): a kind per member. 0 shader archive, 1 light map,
  2 painted shadows, 3 the member as it is (`<ordinal>.bin`, for tools). Kinds 1 and 2 write
  `<output>/export.txt` (ordinal, result, hash).
- `newsnap/overlays/snap_lightmap_export.c`: the light maps are **BC6H signed** (`.nutexb` 0xd8, NVN 0x4F), not
  unsigned as the previous handoff said; the decoder handles both. The block-linear storage is read with the
  runtime's own `nvn_tex_layout` / `nvn_deswizzle`, the code the upload uses.
- **Checked against the GPU (RTX 4060):** on `tests/routes/photo-tutorial-expedition.txt` with `AC_HD_SHADOWS=1`,
  the 201 light maps the game uploaded that the rule below selects were dumped by the GPU and exported offline:
  all 201 are identical half float by half float, and their hashes equal the upload hashes
  (`NEWSNAP_TEX_HASHLOG`). The other BC6H uploads of that run are the directional maps, which the mode leaves alone.

### HD-SHADOW-02, point 2: the shadows painted per mesh

- They are not in the ordinary colour textures of the models: every lit mesh of a level has its own texture,
  `<level>^<model>^<id>^<shape>^<n>^Shadow.nutexb`, BC3 sRGB (`.nutexb` 0xa5, NVN 72), 64 to 2048 texels, black
  colour and the sun shadow in alpha. 4 578 of them in the game, beside 4 578 light maps
  (`...^<n>^0^Lightmap.nutexb`; `^1^`, `^2^`, `^3^` are directional terms, 1 720 each).
- **The curated list is those two name rules** (`game_textures.RULES`), so it covers every level and needs no
  hashes kept in the project.
- `hdshadows.mask_prepare / mask_finish`: Real-ESRGAN (`realesr-animevideov3`) on the alpha, clamped to the local
  range of the original (the amount of shadow stays the game's), soft areas (half tones spread over an area) taken
  from a plain enlargement so foliage stays soft, BC3 with black colour and mips. Masks with colour, flat masks and
  results above 4096 texels are left as they are (`.skip`).
- The runtime attaches them from `hdshadows/` by hash like the light maps (`snap_texpack.c`, sRGB BC3 textures are
  looked up there before the texture pack). On the same route 208 of them had the hashes of the offline export.
- The upscaler now runs once per batch of 48 pictures (`hdshadows.upscale`, a folder in, a folder out) instead of
  once per picture.

### Launcher

- «Generar sombras HD» starts or stops the build (`hdshadows_ui.py`); saving the settings with the mode on, opening
  the launcher with levels left and closing the game start it by themselves (`launcher._build_hd_shadows`,
  `_auto_hd_shadows`). Starting the game or an update stops it (`_set_busy`); it goes on after the game.
- Measured on the RTX 4060 (Laptop), whole game: about 35 minutes (290 textures a minute), 8 206 HD textures and 677 left as they are out of 9 156 members, 6.3 GB, no failures.

### MENU-LANG-01

- `newsnap/overlays/ui_text_{fr,de,it,ja,ko,zh_hant}.inc`, included in `ui_text.c` in place of the keyboard-only
  rows (`snap_menu_adapt.py`). `tests/test_menu_languages.py` keeps every table equal to the Spanish one id for id
  and format specifier for format specifier. Translated from the Spanish table, not reviewed by native speakers.
  Descriptions that name an option whose label is hardcoded in English in `snap_menu_adapt.py` («Keep 16:9»,
  «Stretch») name it in the language of the table, as the Spanish one already did.

## Next

1. **HD-SHADOW-02 acceptance on the owner's RX 6900 XT:** turn the mode on, let the build finish, visit levels not
   played before. To look at: stairs and decks at the camp, plant shadows on the ground in the first courses, video
   memory in the largest levels (the HD masks of a ground mesh are 4096 texels, 22 MiB each).
2. **MENU-FPS-01 (experimental):** not started. See the previous handoff.
3. **README-01:** screenshots. New game pictures have to be pinned in `tools/check_content.py`.
4. **RTX-01:** HD photo thumbnails on RTX and DLSS frame generation. This PC has an RTX 4060, so it can be done
   here; not started.
5. Blocked: FPS-03 (needs a fluffruit save).

## How to check the HD shadows

    python -m newsnap.game_textures --runtime <GameData> [--data <GameData>] [--only LC_101_A]

then a route with `AC_HD_SHADOWS=1`; the log says `texpack: HD shadows on, N HD shadow textures` and
`N HD light maps in use` / `N HD painted shadows in use`. Without `all-maps` the runtime still dumps the light maps
it loads to `hdshadows/src` as RGBA16F, which is what the offline export was compared with.
