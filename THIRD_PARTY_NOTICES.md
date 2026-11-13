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

The NACP field layout was checked against switchbrew/libnx `nx/include/switch/nacp.h`.

`newsnap/nushdb.py` follows the SSBH shader-library layout documented in
[ultimate-research/ssbh_lib](https://github.com/ultimate-research/ssbh_lib)
at `c1149c2822b857a351ed1c130aef2c6ec7430094` (MIT; Copyright 2020 Smash Ultimate
Research Group). Its full notice is retained in `licenses/ssbh_lib-MIT.txt`.
Shader seed layouts and runtime hashes follow the pinned Astral tools/runtime.
