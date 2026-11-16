# Third-party notices

The selected base is captainj-sparrow/astral-chain-pc-recomp at
`248e0b29f308ca84a2d2092019cc60e7fc50ae85`, retained in `third_party/astral`.
Its MIT license and full dependency notices are retained there without alteration:

- `third_party/astral/LICENSE`
- `third_party/astral/THIRD_PARTY_NOTICES.md`

That project builds on valentderah/totk-pc-recomp, LAS Recomp, MacNativeGames,
Ryujinx and the libraries identified by its notices. Their licenses still apply.

`newsnap/importer.py` calls the pinned upstream extractor and adapts its title
selection and import workflow. The upstream's NCA/IVFC/BKTR reader credits
MacNativeGames contributors (MIT, 2026) and TotK Recomp; those credits are preserved
in the submodule. Runtime/lifter patches, when present, modify that upstream and
retain its original file notices.

The separately downloaded Astral Chain setup supplies local build tools only.
It is ignored by Git. Its hactool is by SciresM and contributors; its license
ships with that distribution. Python dependencies retain their own licenses.

Witch Time was consulted as a research reference; no Witch Time source is copied.

`newsnap/drp.py` adapts the DRPF format and XorShift description in
[kwsch/NewSnap](https://github.com/kwsch/NewSnap) at
`2da13570960124f263e439994064d00c1a48788d` (ISC; Copyright 2021 SciresM and Kaphotics).
The complete notice is in `licenses/NewSnap-ISC.txt`. The reader indexes metadata
without distributing or invoking the proprietary Oodle DLL.

`newsnap/saves.py` also follows that project's photo-container format. Save
decryption material is reconstructed locally from the owner's verified code;
no game keys or images are included in this repository.

The launcher and original icon generator use [Pillow](https://python-pillow.github.io/),
distributed under the HPND license. Pillow's package retains its license and
dependency notices. Icon artwork in `assets/icons` is original to this project.

The launcher's typeface is [Nunito](https://github.com/googlefonts/nunito) (Copyright 2014 The Nunito Project
Authors), under the SIL Open Font License 1.1. `assets/fonts/Nunito[wght].ttf` is the unmodified variable font
from Google Fonts' repository (`google/fonts`, `ofl/nunito`, commit `8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5`);
the complete licence is `licenses/Nunito-OFL.txt` and its provenance is in `assets/fonts/README.md`. The launcher
loads it for its own process only. The launcher's textures, shadows and interface icons are drawn by its own code
(`newsnap/artwork.py`) and are original to this project.

Windows launcher releases bundle CPython, Tcl/Tk and their runtime dependencies.
Their notices are preserved under `licenses/runtime` in that release.
The launcher uses the [PyInstaller](https://pyinstaller.org/) bootloader under
its GPL license with the exception permitting distribution of bundled applications.
Its full notice is included with the executable.

The NACP field layout was checked against switchbrew/libnx `nx/include/switch/nacp.h`.

Version 0.4 optionally uses the official AMD FSR SDK 2.4.0 Vulkan binaries and
headers, pinned to `7539ae8b6568ad29ed78a753404351daf3b5cca7`. Their complete
license and third-party notice accompany `upscalers/`; component-specific terms
apply independently of this repository's MIT license. The public precompiled
native FSR shader header derives from AMD's MIT-licensed FidelityFX SDK 1.1.4;
its license accompanies the build kit/runtime.

The optional NVIDIA DLSS Super Resolution 310.9.16 binary is pinned to NVIDIA's
`9981c6350dc58c0ce21f024fd65e31e851c31689` distribution. It is proprietary under
the NVIDIA RTX SDKs license, retained as `licenses/NVIDIA-DLSS.txt` together with
its version/hash receipt. NVIDIA and DLSS are NVIDIA Corporation trademarks.
The launcher credits these providers and displays their complete terms.
These providers accompany this application, rather than standalone SDK products.
No game data or generated game code is included in the build kit.

`newsnap/nushdb.py` follows the SSBH shader-library layout documented in
[ultimate-research/ssbh_lib](https://github.com/ultimate-research/ssbh_lib)
at `c1149c2822b857a351ed1c130aef2c6ec7430094` (MIT; Copyright 2020 Smash Ultimate
Research Group). Its full notice is retained in `licenses/ssbh_lib-MIT.txt`.
Shader seed layouts and runtime hashes follow the pinned Astral tools/runtime.

The anti-aliasing (`newsnap/overlays/shaders/SMAA.hlsl`, `smaa_area_tex.h`, `smaa_search_tex.h`) is SMAA from
[iryoku/smaa](https://github.com/iryoku/smaa) (MIT; Copyright 2013 Jorge Jimenez, Jose I. Echevarria, Belen Masia,
Fernando Navarro and Diego Gutierrez), converted to UTF-8 with LF line endings. Its notice is retained in
`licenses/SMAA-MIT.txt`.
# Official promotional artwork used by the launcher

The owner requested New Pokémon Snap imagery in the launcher. Files under
`assets/launcher/` are unmodified promotional images from the official website:
https://newpokemonsnap.pokemon.com/en-us/ . Exact source URLs, SHA256 and image
dimensions are recorded in `assets/launcher/source-pins.json`.

©1995–2021 Nintendo / Creatures Inc. / GAME FREAK inc.
©1999 Nintendo / HAL Laboratory, Inc. Developed by BANDAI NAMCO Studios Inc.
Pokémon and Nintendo Switch are trademarks of Nintendo. These images retain
their respective owners' rights and are not covered by this project's MIT
license. Their inclusion does not imply endorsement or a redistribution license
from the rights holders. No private player photographs or extracted game data
are used for the launcher artwork.


The BFE/BFI semantic patch and zero-funnel precedent derive from
[TotK Recomp c0e66fe4c1d532e728444c3ade6ff390f734151b](https://github.com/valentderah/totk-pc-recomp/commit/c0e66fe4c1d532e728444c3ade6ff390f734151b).
The corresponding native translator retains its Ryujinx/MacNativeGames/donor
notices as well as this additional notice:

MIT License

Copyright (c) 2026 Valiantsin Dzerakh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
