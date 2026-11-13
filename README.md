# NewSnapRecomp

Work in progress: a native Windows x64 recompilation of **New Pokémon Snap** using the infrastructure of [Astral Chain Recomp](https://github.com/captainj-sparrow/astral-chain-pc-recomp), which builds on [TotK Recomp](https://github.com/valentderah/totk-pc-recomp).

**Status:** the owner's base and update **2.0.1** import with verified integrity. A private Windows x64 executable builds, passes its memory/dispatch and loader checks, boots into `nnMain`, and displays the autosave notice with audio. Runtime adaptation is in progress. This is **not yet a verified playable port**; no gameplay FPS or stutter-free result is claimed.

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

## Shader preparation and performance

The target is to prepare shader variants and GPU pipelines before gameplay, persist compatible caches, and measure first-use misses across routes. Translation alone does not prove the GPU driver has compiled every pipeline. No complete Snap shader inventory or first-use coverage is claimed yet.

Optimization will compare identical scenes and settings, preserving photography evaluation, event order, audio, camera motion and saves. Frame-time percentiles, startup time, memory use and compilation misses matter alongside FPS.

## Source and content boundaries

Only original tools, adaptation patches, tests, documentation and the upstream gitlink belong in this repository. NSPs, keys, ExeFS/RomFS, generated C, compiled games, shader binaries/caches and save files remain local. Do not upload your built game.

Original additions are MIT licensed. Upstream and third-party code retain their licenses and attribution; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
