# NewSnapRecomp

Work in progress: a native Windows x64 recompilation of **New Pokémon Snap** using the infrastructure of [Astral Chain Recomp](https://github.com/captainj-sparrow/astral-chain-pc-recomp), which builds on [TotK Recomp](https://github.com/valentderah/totk-pc-recomp).

**Status:** the owner's base and update **2.0.1** import with verified integrity. A private Windows x64 executable builds, passes its memory/dispatch and loader checks, accepts a local character/name and commits the initial save. A nine-minute 1× replay captures/evaluates Pikachu (2,600 points), saves two real photographs and enters the first route. The SDK nonlocal-jump crash found after evaluation is corrected. A complete course and its photo save/reload remain unverified. No sustained gameplay FPS or stutter-free result is claimed.

The published [**0.6 alpha**](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.6.0-alpha)
integrates reviewed applet contracts, portable IEEE CRC32 acceleration, complete
recent-log selection and a checksum-bound portable build kit. Its final package
passes isolated install/repair/offline rebuild and 416 source tests (one symlink
permission skip). RTX photo/tutorial and final post-tutorial reload checks are
documented in the [0.6 notes](docs/releases/0.6-alpha.md); AMD photos/color,
FreeSync/controllers and the intro head-motion cause remain unverified.

The earlier **0.5 alpha** adds destination-aware SDR color transfer, stricter coherent
host-memory imports with managed fallback, preservation of graphics storage-write
draws, camera capture/sensor lifecycle fixes, a new Home/update flow and the
original ReKHCoM controller sprite with Switch labels. A bit-exact resource-worker
bridge reduced the local intro p99 from 42.970 to 25.469 ms in two reversed-order
pairs on RTX 4060; isolated spikes remain. See [0.5 alpha notes](docs/releases/0.5-alpha.md)
for acceptance and hardware limits. RX 6900 XT, physical controls and FreeSync
acceptance remain pending; this is a prerelease, not a stable compatibility claim.

The earlier **0.4 alpha** added official Vulkan FSR 3.1/FSR 4 provider integration,
DLSS Super Resolution and Native AA/DLAA presets, plus automatic owner-local
runtime rebuilding after updates. See the [0.4 work board](docs/V04.md) and
[updating guide](docs/UPDATING.md). FSR 3.1 and DLSS have executed in Snap on the
local RTX 4060; physical RX 6900 XT/FSR 4 verification remains pending.
The [0.3 work board](docs/V03.md) and [controller coverage](docs/CONTROLLERS.md)
retain earlier acceptance evidence. No full-course FPS or stutter-free result is claimed.

The upstream is pinned as a submodule. Snap-specific offsets, SDK bindings, shader formats and timing must be verified against Snap; Astral Chain patches are not interchangeable.

## Local import

Requires Python 3.12 and your own game files and console keys. None are included.

```powershell
git submodule update --init
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m newsnap import --base "path\base.nsp" --update "path\update.nsp" --keys "path\prod.keys" --hactool "path\hactool.exe"
```

Use the selected upstream's patched hactool (see its `tools/build_hactool.py`). `--exefs-only` imports code modules without merging RomFS. Outputs go to `build/extracted`, with verified hashes and receipts; a second run validates input and output hashes before reuse. A stale output is refused; use another `--work` directory to preserve the earlier import.

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

## Experimental build

Unpack the selected upstream's Windows setup release locally. Its `llvm/`, `runtime/deps/` and `bin/` directories provide the compiler, headers, libraries and translator. Install `glslc` and `spirv-val` for the host-side FSR shader build, then run:

```powershell
.venv\Scripts\python -m newsnap build --sdk-root "path\Astral Chain-Setup" --shader-tools "path\shader-tools" --jobs 8
build\updated\newsnap.exe --selftest
build\updated\newsnap.exe --probe-loader
build\updated\newsnap.exe --boot
```

The executable and all game-derived C stay local. The build verifies the imported modules, RomFS and index before compiling. `--no-generate` is allowed only when a receipt binds every generated source to the current modules and generator. Control metadata is rederived from the verified NACP; editing a cached JSON cannot inject compiler definitions.

The current bring-up exposes an offline network interface; online socket/TLS services report unavailable. Native game timing is retained: none of Astral Chain's instruction or FPS patches are applied.

## Local launcher

Windows alpha packages include `NewSnapLauncher.exe`, its dependencies and the
original camera icon. Extract the whole Windows release and place your own
`GameData` (or `newsnapGameData`) folder beside that executable. Python installation
is not required. The owner-data folder contains the imported assets, locally
generated native executable, shader inputs and profile; it is never a GitHub
asset. Keep its runtime compatible with the selected release. See
[0.3 alpha notes](docs/releases/0.3-alpha.md) for controls and tested limits.

From a development checkout:

```powershell
.venv\Scripts\python -m newsnap launcher
```

The Spanish launcher provides profile selection, shader preparation, video and
input settings, and a read-only photo album with export. Settings apply on the
next game launch. Unrelated INI settings and changes made through the runtime
menu are preserved. Window size, native docked/handheld output, internal render
scale and final presentation scaling are separate controls; see
[video compatibility](docs/VIDEO_COMPATIBILITY.md) for their limits.

The album reads explicit exports from the profile's `photos` directory and
committed photo containers in that profile's save. Refresh is deferred while an
expedition holds the launcher profile lock. It excludes transaction
folders and diagnostic screenshots. Parsing was tested with synthetic photos
and real saved tutorial photographs. Two original 1080×720 images were decoded
and exported byte-identically; slot-matched thumbnails are grouped with originals.

Mouse left-click maps to Snap's A/photo button by default; existing custom
bindings take precedence. See [input findings](docs/input-findings.md) for the
distinction between the game's free aim and an input drift defect.

The 30/60 presentation cap is independent of donor timing patches. Rates above
60 remain under [investigation](docs/HIGH_FPS.md): a timer candidate has fixed
1/60 modes whose active consumers have not yet been identified.

Snap's own render-level patch is bound to the verified 2.0.1 module and original
instruction. The patch table is part of generation provenance.

## Shader preparation and performance

The tools can decode the 3,138 shader libraries locally, using the original decoder in your verified executable. No proprietary decoder is included. To prepare their supported stages with default texture answers plus recorded variants:

```powershell
.venv\Scripts\python -m newsnap unpack-shaders
.venv\Scripts\python -m newsnap prepare --all
```

The latest local test prepared 3,520 variants in the RTX 4060 driver cache, with zero translation or driver-preparation failures. Two geometry-stage entries are explicitly unsupported by the current backend. Default answers cannot establish coverage for every unseen texture type or pipeline combination. `prepare` without `--all` uses only recorded variants; startup also rebuilds recorded pipelines before guest execution.

The current local-name mode uses the PC keyboard's length and character validation without Nintendo's profanity dictionary, as requested by the owner. It reaches character/name confirmation without firmware. This intentionally does not provide Nintendo's word filtering. No complete playable route or first-use coverage across the game is verified.

The selected base already includes release 1.14.0 and matches upstream `main` at the latest check. See [feature compatibility](docs/UPSTREAM.md) for what is inherited, what has been exercised and what needs Snap-specific adaptation.

Optimization will compare identical scenes and settings, preserving photography evaluation, event order, audio, camera motion and saves. Frame-time percentiles, startup time, memory use and compilation misses matter alongside FPS.

## Source and content boundaries

Only original tools, adaptation patches, tests, documentation and the upstream gitlink belong in this repository. NSPs, keys, ExeFS/RomFS, generated C, compiled games, shader binaries/caches and save files remain local. Do not upload your built game.

Original additions are MIT licensed. Upstream and third-party code retain their licenses and attribution; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
