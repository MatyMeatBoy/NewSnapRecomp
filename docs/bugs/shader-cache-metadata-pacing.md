# Shader metadata on the render path

Owner report (RX 6900 XT, 144 FPS): fast repeated camera turns in a course can
stutter. This change removes a measured contributor on the local RTX 4060 Laptop;
it does not establish that every reported AMD or warm-cache hitch has this cause.

## Cause and change

On a shader cache miss, `gfx_shader.c` synchronously translates a shader, flushes
its SPIR-V/resource files, renames the output, writes a `.use` mask and writes an
`.in` replay-input snapshot. The last two use atomic writes with disk synchronization
and write-through rename. The render/replay caller waits for these regenerable
metadata writes before it can use the already translated shader.

The Snap overlay queues **owned copies** of only those `.use`/`.in` writes. The
existing pipeline autosave thread drains them outside the enqueue lock. Atomic
file writing is retained; SPIR-V/resource flushing is unchanged. An 8 MiB pending
queue limit, oversized input or allocation failure falls back to serialized
synchronous writing after draining earlier jobs. No new worker, scheduling
priority, game logic, rendering output or save/configuration format changes.

Explicit flushes also precede cache-memory drops, bracket prewarm, precede the
standalone preparation completion marker, and participate in normal forced
record flushing at exit. Standalone shader preparation has no autosave thread;
that boundary must not rely on a future background poll.

Prior art: the pinned Astral renderer already saves pipeline keys/recordings on
its autosave thread to avoid blocking rendering. Dolphin's
[ShaderCache.cpp](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/VideoCommon/ShaderCache.cpp)
appends shader binaries to its disk cache and synchronizes when closing caches;
it likewise separates cache persistence from shader semantics. This overlay
reuses Astral's thread and preserves its atomic writer.

## Evidence

Private evidence: `build/next-release-20261120/` in the shared repository; never
commit its inputs, profiles, generated code, shader snapshots, captures or executables.

- Baseline runtime compiled from 0.9.23, selftest and module-loader probe pass.
- The first-day course and fast right/left camera rotations were reached using
  controller scripts and copies of the supplied save, without editing progression.
- One matched before/after pair: same executable pathname, 144 FPS cap, 1920x1080
  internal scene, same settings, route and initial save; separate initially empty
  shader/pipeline caches. Both runs translated **239** shaders and exited 0.
- Private instrumentation measures translation service, SPIR-V flush and the
  remaining metadata phase separately. Metadata median **17.785 -> 5.481 ms**;
  p95 **23.702 -> 11.032 ms**. Its cumulative caller time was 4197.881 -> 1420.949 ms.
- SPIR-V flush median increased 2.147 -> 6.127 ms; disk contention remains possible.
  Translation service timings also differ and the driver's own persistent cache
  was not independently reset. These numbers demonstrate the metadata-path
  reduction, not a universal FPS or whole-frame improvement.
- Native fixture: owned path/data snapshots, allocation failure, oversized records,
  queue pressure, FIFO per producer and concurrent draining of 4000 records.
  Overlay checks cover all five persistence boundaries and retain SPIR-V flushes.
- Independent review caught missing standalone-preparation/cache-drop drains;
  these were added before acceptance. Final review and runtime checks are recorded
  in the work board and release notes.

## Limits

First-time shader translation and GPU compilation still cost time. This does not
claim zero stutter, 144 FPS on every CPU, AMD acceptance, or a fix for the separate
transient image at course entry. A crash can lose queued regenerable metadata;
missing metadata is rebuilt on a later run. The game's saves never use this queue.
The translator and shader results are unchanged, so `SHADER_EPOCH` stays unchanged
and existing verified shader caches should be kept across this update.
