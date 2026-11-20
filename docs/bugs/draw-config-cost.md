# Redundant configuration work during draw replay

A warm-course sampling profile found repeated Windows CRT environment lookup
chains through `cfg_get` / `cfg_upscaling` into `support_scales`. That function
checks whether scaled-image shader support is required on each draw.

With HD photo thumbnails enabled (the default), scale support is required even
at native scene resolution. Previously the gate computed the host scale first:
engine/handheld mode, legacy upscaler, selected upscaler/quality, render scale and
possibly display size. All of those queries were then discarded because HD
photos already require continuing. The gate now checks HD photos first.

This is Boolean short-circuit reordering of read-only predicates. The mip-skip
case, scale buffers, shader output and live configuration semantics are unchanged.
No configuration cache, worker priority change or extra allocation is introduced.
The native fixture exercises the actual adapted expression, all predicate cases,
avoided scale calls and settings changed between adjacent draws. It failed before
the change and passed afterward. Independent review found no blockers.

GPU comparison uses the same executable pathname, scripted course and camera
turns, copied initial save, settings and independently copied warm shader/pipeline
caches. Raw timings/captures stay private under build/next-release-20261120.
The initial pair overlapped part of the unit-suite run and is exploratory only;
a reverse-order repeat without concurrent CPU tests is the acceptance measurement.


Acceptance repeat (reverse order, no concurrent unit suite/compiler): RTX 4060
Laptop, 144 FPS cap, 1280x720 window / 1920x1080 internal, upscaling/FG/HD shadows
off; identical scripted right/left turns during world seconds 40–60. Both runs
exit 0. Per-present intervals: median 7.66 → 7.04 ms, p95 12.82 → 9.37 ms,
p99 16.52 → 11.96 ms. Frames above 16.67 ms: 22/2393 → 4/2653. There were two
candidate outliers above 25 ms (max 27.16), versus none in the baseline (max
24.34): this is not a zero-stutter claim. Whole-game/AMD results and HD-on defaults
are separate from this deliberately feature-equivalent comparison.
