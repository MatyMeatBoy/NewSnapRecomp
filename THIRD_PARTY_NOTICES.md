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
