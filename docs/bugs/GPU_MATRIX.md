# Graphics and input evidence matrix · 0.5

Date: 2026-11-13. A review document; it does not authorise publishing 0.5 or change the owner's
acceptance status. The 0.4 release is immutable.

## How to read the states

- **Observed**: a result recorded in an identified run/screenshot.
- **Inferred**: a plausible explanation that still needs the causal control.
- **Fixed in code**: a change implemented; not equivalent to physical validation.
- **CPU verified**: real native functions with controlled dependencies.
- **GPU verified**: only the stated device, binary, mode and route.
- **Pending**: that test is missing; it is not replaced by another GPU or a fixture.

The local machine is an **NVIDIA GeForce RTX 4060 Laptop GPU**; the normal A/B records driver
**616.92**. The owner reported failures on an **AMD RX 6900 XT**, **Original** mode, FreeSync
monitor. Do not infer an AMD driver, HDR state or real VRR without their record. Other GPU
models are not validated by these results.

## Contracts and coverage

| Contract | Cause/state of the change | CPU/native control | Local RTX 4060 | Owner's RX 6900 XT |
| --- | --- | --- | --- | --- |
| Presentation SDR colour | **Fixed**: the sRGB base format alone does not describe the transfer used when writing the final bytes. Choose a compatible view by source **and target**, without touching the game's grade. | RGBA/BGRA × UNORM/sRGB matrix; equivalent pairs without a copy, float/unknown keep their semantics. | **Observed**: at exactly 1920×1080, `f01114` against the presentation has MAE=0 and max=0 in `v05-final-color-coherence-1to1`. Binary `f6d92250…`. Neighbouring frames differ in time; not all are exact matches. | **Pending**: the reported oversaturation/contrast is not physically fixed by an NVIDIA comparison. |
| Host memory import | **Fixed**: the donor's selection can return a compatible type that lacks the requested properties. The direct import path requires `HOST_VISIBLE` and `HOST_COHERENT`; without both it picks existing managed storage. Its flush/barrier/fence paths were audited in source; that fallback was not validated on GPU. No per-vendor exception. | Negative: a visible/cached non-coherent type picked by the old selector. Positives: chosen flags, coherent import kept, fallback by pool/tracking and a controlled invalidate call. `shadow_sync_pool` is a counting stub: it does not test flush, GPU visibility or completion. | **Observed**: the final normal run records type 2, properties `0x6` (visible/coherent), keeping the direct path. It does not run or validate AMD's physical fallback. | **Pending**: neither the memory type actually selected nor the cause of its bands is established with AMD bytes/trace. |
| Graphics draws with storage writes | **Fixed**: skipping a draw with a written SSBO/image store because its pipeline is pending skips a functional operation, even if its render target is recent. Translation/reflection and pipeline are awaited for those effects. | The donor fails the negative; VS/PS, SSBO/image store, read-only, unknown translation, several waits and real failure tests. | Integrated runtime `06a8d9df…` built and run in the normal A/B; that warm route had no skips. This does not show which draw caused the bands/reticle. | **Pending**: the local reflection of a storage shader shows the class is used, not the AMD report's causality. |
| Compute dispatch | **Observed in source**: `op_dispatch`/`op_dispatch_ind` request translation without pending and a synchronous compute pipeline. | The hypothesis that they go through the graphics skip is **ruled out**. No compute patch based on that assumption was added. | Not an independent acceptance of every dispatch. | No specific test; do not attribute the defect to compute from the look of the bands. |
| Capture → buffer → JPEG → thumbnail → evaluation | Bounded opt-in diagnostics compare transfers keeping pitch/format/lifetime. The original selection/evaluation/tutorial logic is kept. | Fixtures instrument real transfers with controlled APIs; the independent CPU audit of the bank/JPEG has its own pending review. | **Observed**: separate normal 540 s controls with `f6d92250…` and `06a8d9df…`, each exit 0, two new photos and two thumbnails without black rows, four identical GPU source/buffer transfers and tutorial progress recorded. The earlier one also identifies a first-expedition capture. The final evidence is its own, not inherited from the earlier one. | **Pending**: the owner's screenshot shows bands and a selection rejection; it does not prove the bands cause that rejection or where they come from. AMD bytes are missing. |
| Mouse, focus and sensors | **Fixed**: capture epoch; fusion reset when the source changes/is lost; no enabling sensors with motion off; partial rollback; removal of the non-atomic shared cache of the live setting. | 19 native scenarios; the donor shows eleven failures. Two Win32 threads reproduce an old read that contaminated the new setting. Three complete units pass syntax. | Integrated binary built; fixtures do not activate hardware. Not equivalent to acceptance of the physical mouse/controller. | **Pending**: a camera that aims by itself can have other causes, including unmeasured physical drift. Do not change sensitivity/deadzone to hide it. |
| VRR | The probe separates observation/capability/unknown state. FIFO/mailbox do not certify VRR. | Specific contracts and parser, separated from hardware. | The A/B used mailbox and a 1920×1055 swapchain; this **does not show VRR**. | The monitor's FreeSync is the report's context, not a measurement of the swapchain's variable cadence. |

## Reproducible local evidence

Links under `build/` point to existing private artifacts. Do not upload screenshots, photos,
saves, imports, keys, derived caches or executables.

| Evidence | Scope and limit |
| --- | --- |
| `build/v05-original-color-fixed-1to1/pixel-comparison.json` | First exact digital pair `f01108`: MAE/max/RMS=0; wrong sRGB decoding ≈49.47 MAE. |
| `build/v05-final-color-coherence-1to1/{run.json,pixel-comparison.json}` | Fix with a source/target matrix; best pair `f01114`, 1920×1080, MAE/max=0, binary `f6d92250c57917e37ac8ab0bfc02792896feeb56df69ccceca6265019f034eba`. Not a physical HDR validation or an sRGB-only fallback. |
| `build/v05-import-coherence-proof/proof.c` | Minimal proof of the selector accepting a non-coherent type; complement with `tests/test_photo_readback.py` and the adapter, do not confuse with an AMD trace. |
| [Graphics effects](graphics-side-effects.md) | Cause, changes, negative/positive and limits of `tests/test_graphics_effects.py`. |
| `build/v05-positive-control-normal540/{run.json,photo-evidence.json}` | Binary `f6d92250…`, exit 0, final frame 32272; 1080×720 photos, 240×200 thumbnails. The `save`/`save-tx` copies are not independent photos. There was real async activity: do not confuse with a warm benchmark without skips. |
| `build/v05-final-positive-control-normal540/{run.json,photo-evidence.json}` | A different run with binary `06a8d9dfee5d8ee5c6d3cfe72beccf3d4e5d3f1d553ea7187cd7231be52b722d`: exit 0, final frame 32252, originals/profile/backups intact, four transfers with zero differences and two new photos/two thumbnails without black rows. Records 98 pending-pipeline skips and zero shader-translation skips; it does not prove a draw with storage effects was skipped. Concurrent PyInstaller/tests: not a clean benchmark. |
| [Bank audit](photo-bands-cpu.md), [review](photo-audit-review.md) | The 150 historical banks contain duplicates: only two unique photos from one route. An audit parser/verdict also needs damage and source-protection tests. |
| [Input](camera-input.md), `build/v05-camera-input-results.json` | CPU/threads and build; physical acceptance pending. |

## Performance: separate results

[The normal A/B](../../build/v05-normal-pacing-ab/REPORT.md) compares one measured 40 s run per
binary, each after 40 s of warm-up, with a serialised GPU, the same profile/cache seed,
Original, cap 60, render 100 % and the same effective 1920×1055 swapchain. It uses neither
`--shot` nor active flight captures.

| Whole game interval | 0.4 | Integrated `06a8d9df…` |
| --- | ---: | ---: |
| Samples | 2355 | 2354 |
| Mean, ms | 17.003 | 17.004 |
| p50, ms | 16.654 | 16.662 |
| p95, ms | 19.661 | 19.301 |
| p99, ms | 34.781 | 42.523 |
| Max, ms | 104.370 | 110.373 |

**No global pacing gain is shown.** Mean/median are equivalent and the tails are mixed. The
later segment improves some tails, but it does not replace the complete result. Zero runtime
translations/skips/waits in this window does not attribute the remaining spikes to a specific
mechanism. Start-up/prewarm is measured separately; a single run does not establish
repeatability or causal regression. The photo runs had declared CPU concurrency and are no use
as a clean pacing comparison.

The generation cache is another cost: `build/v05-generation-cache-real/evidence.json` records
generation + receipt **86.820 s**, publication **3.351 s**, restore **3.044 s** and
verification **0.265 s**; 150 outputs/287,542,127 identical bytes, independent copies and the
same owner path. Originals were verified on both runs. No native code was compiled and no GPU
was used in that test: **it does not measure FPS**.

## Pending gates

### Review and measurement updates

- Claude's PR #1 integrated in `4f421cf`: the CPU audit of banks/photos and its three review
  fixes are approved (25 tests). Auditing the bytes of the affected photos on AMD is still
  pending; the implementation state does not replace that evidence. See
  `photo-audit-review.md`.
- `build/v05-managed-shadow-positive-control/` adds a real 540 s run with `AC_SHADOW=1`, binary
  `06a8d9df…`: four exact GPU pairs, two clean photos and two clean thumbnails,
  tutorial/first expedition and 75 protected files intact. It runs the real managed path on
  RTX; it does not validate the automatic fallback choice by pool or a non-coherent physical
  flush on AMD.
- `build/v05-rng-pacing-ab/comparison.json` compares the verified integer bridge on/off in the
  **same** binary `5b6671c9…`, with two reversed 40 s pairs, separate warm-up, the same
  seed/restored cache, Original and a 1920×1055 swapchain. The pooled p99 drops from **42.970
  to 25.469 ms**; both pairs improve that tail. Mean 17.088→16.736 ms, median ≈16.67 ms;
  frames >50 ms: 40→14. There is still a 107.692 ms spike with the bridge on. GPU busy ≈1.1 ms
  in both. This is a bounded local improvement on that RTX route, not the removal of every
  hitch or an AMD measurement. The earlier 0.4→`06a8d9df…` evidence is still valid for those
  binaries: it is not retroactively replaced by this comparison of a later change.
- The private candidate is identified as `0.5.0-dev.1`; that identity is not a release. Its
  acceptance uses its own final hash, without inheriting the photo acceptance of earlier
  binaries. Physical protocol in `v05-owner-validation.md`.
- The final executable `76f08005…`, producer `555d6258…`, completed its own normal 540 s run:
  two clean photos and two clean thumbnails, four exact GPU pairs, evaluation/tutorial and the
  first expedition. The 75 protected profile/backup files stay intact. Evidence source and
  limits in `v05-dev1-acceptance.md`; AMD/controller/FreeSync acceptance still pending.
- `v0.5.0-alpha` was published with producer `e314751d…`. The real rebuild of its public kit
  produced `e0dcac87…`, which completed a new 540 s control, photos/thumbnails and
  tutorial/first expedition. Download, install, repair and kit acquisition were checked from
  the published release. See `v05-alpha-acceptance.md`; do not inherit physical AMD acceptance
  or declare the pending pacing spikes gone by closing this limited alpha.

Keep the AMD items, physical input acceptance, reticle/focus and uncovered photo scenarios
pending. The final 540 s run gives bounded local acceptance of that route; a green fixture or a
contract fix does not allow marking the whole report solved. Do not skip validation, change
progress flags or fabricate scores.
