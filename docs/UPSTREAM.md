# Astral Chain feature compatibility

Checked on 2026-11-13 against `captainj-sparrow/astral-chain-pc-recomp`.
The selected submodule HEAD and fetched `origin/main` are both
`248e0b29f308ca84a2d2092019cc60e7fc50ae85`. The latest published release is
[1.14.0](https://github.com/captainj-sparrow/astral-chain-pc-recomp/releases/tag/1.14.0),
published 2026-11-13 01:15:51 UTC (2026-11-12 in Chile). There is no newer
upstream revision to merge at this check. The pristine submodule is preserved;
`newsnap/adapt.py` stages Snap's changes and fails if an expected source seam drifts.

Having a feature's code in the runtime is distinct from making that feature work
with Snap's engine. Neither the Astral Chain frame timer nor its camera addresses,
shader signatures and render-target layouts can establish Snap compatibility.

| Feature family | Integration in Snap | Evidence / remaining work |
| --- | --- | --- |
| Vulkan replay/recorder, viewport/scissor recording | Current upstream runtime retained | Startup UI renders; no complete route validated |
| Shader caching, translator use masks, driver preparation, recorded-pipeline prewarm | Retained, plus Snap's DRPF/SSBH reader | 3,493 prepared variants and 38 setup pipelines; unseen variants and two geometry-stage entries remain open |
| ASTC decoding, texture caches, memory-pressure handling | Current upstream implementation retained | Startup texture rendering validated; VRAM pressure, full scenes and long sessions unverified |
| Audio renderer, Opus, host input/controller support | Current upstream implementation retained | Startup audio/input observed; no complete route or sustained synchronization result |
| Ambient occlusion and larger sun shadows (1.14.0) | Code retained, compatibility unverified | Astral-specific scene/shader identification must be replaced and checked against Snap captures |
| DLSS / XeSS / FSR 3 and temporal antialiasing | Code retained, compatibility unverified | Needs Snap scene identification, motion vectors, history and quality checks; no functioning Snap upscaler claimed |
| Ultrawide, HUD placement, camera FOV and HUD toggle | Astral instruction patches deliberately not applied | Requires Snap-specific camera/UI analysis, including photography framing |
| 60 FPS, cutscene/movie timing fixes (including 1.13.0) | Host pacing infrastructure retained; Astral game hooks not applied | Native timing retained until Snap's counters, event order, audio and photography evaluation can be compared |
| Installer update UI (1.14.0) | Upstream source retained; not a Snap installer | Snap currently uses its verified command-line importer/build tools |

## Naming-service comparison

TotK was inspected at `7a37fc3c346cd6f2b3c80637effb27b880ce817b`, particularly
`runtime/swkbd.c` and `runtime/ov_system.c`. Its PC keyboard handles length,
disabled characters, encoding and cancellation. Its shared firmware fonts are
needed for Chinese/Korean text; that is a separate dependency from Snap's naming
dictionary.

Witch Time was inspected at `13c2afbaa8e98f942ed8e172de59cdddb5b14b8b`, including
26 runtime service/import files. No reusable `nn::ngc::ProfanityFilter`
implementation was found there. A comment grouping `nn::ngc` in `nnmisc.c` has
no corresponding handler. This is a source-search result, not a runtime test of
Bayonetta or proof that no optional code path can ever use system content.

Snap 2.0.1's setup calls the filter initializer before the keyboard even for the
tested English setup. Its SDK asks for system data `0100000000000823`.
The inherited filesystem proxy returned success without an IStorage object,
causing a null dereference. Returning TargetNotFound exposes the real SDK abort;
it does not provide a fallback on its own.

The owner chose local names without Nintendo's word filter. `snap_names.c`
therefore reports the missing dictionary at initialization and preserves the
SDK constructor's uninitialized state. The PC keyboard does not call Nintendo's
text-check callback. This mode changes word-filter behavior intentionally; it
does not claim equivalent filtering or dictionary availability. The original
object finalizer/destructor remain in use.

The initial setup sequence was repeated after this change and the OE lifecycle
binding: the name is accepted, the initial save is committed and the rendered
title scene is reached without system firmware. Complete gameplay remains unverified.
