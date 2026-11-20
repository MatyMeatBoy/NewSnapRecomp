# Related recompilation research (2026-11-20)

The owner suggested Longshot/Hookshot commit histories. Read-only primary-source
review; no donor code was copied or executed. Hookshot's original API/page returned
404 during this review, so the accessible Longshot history is the evidence below.
That does not establish why Hookshot is unavailable.

[Longshot development guide at fa2cc03](https://github.com/Recomper/Longshot/blob/fa2cc03aa5c2/docs/development.md)
describes ARM64 lifted to C, native Horizon services, NVN2 and Vulkan replay.
Snap also recompiles ARM64 and replays graphics through Vulkan, but uses the pinned
Astral runtime/NVN implementation rather than Longshot's Switch 2 NVN2 renderer.
Shared bottleneck classes are useful; renderer structures and shader binaries are
not interchangeable. Longshot's guide states GPL-3.0-or-later and identifies its
translator dependencies. Licensing must be checked before any code reuse.

| Pinned change | Applicable question for Snap | Current decision |
| --- | --- | --- |
| [8a8ac27: opt-in replay recorder](https://github.com/Recomper/Longshot/commit/8a8ac27a218c6e92849ad6c511504e9399842308) | Can CPU replay overlap submission? | Snap already has a recorder, disabled by default on AMD because of known faults. Do not enable it globally or count it as an AMD fix. |
| [c7c88fa: flush only the FSR uniform slice](https://github.com/Recomper/Longshot/commit/c7c88fa2044c0e63e632222b6f4a3e7c03772170) | Are uploads/flushing larger than necessary? | Useful audit target for FSR-enabled runs; cannot explain the measured run with upscaling/FG off. Preserve noncoherent alignment and in-flight ownership. |
| [556deca: complete failed background jobs](https://github.com/Recomper/Longshot/commit/556decaa1bf3221073247c83938769dbe3f6cd5e) | Can a failed asynchronous shader job strand a consumer? | Relevant lifecycle check for future worker changes. Snap's new metadata queue has synchronous fallback and explicit preparation/exit drains. Different job system; no transplant. |
| [5e4e211: shipped pipeline list](https://github.com/Recomper/Longshot/commit/5e4e2113d857) | Can known states be prepared before gameplay? | Snap already records/prepares its own states. OoT pipeline lists do not describe Snap and are not reused. Wider Snap coverage needs matching settings and game-specific evidence. |
| [f4e6fdd: streaming stores made opt-in](https://github.com/Recomper/Longshot/commit/f4e6fddec3c42c888dcee1e849747521d1e14f03) | Does a low-level copy optimization improve actual pacing? | Their matched trials reported worse stalls despite similar capture time. Keep regular copies unless Snap's own equivalent workloads demonstrate a benefit. |

The next local change follows Snap's profile rather than copying a donor: when
HD photos already require scale handling, short-circuit that fact before querying
the upscaler/internal-resolution configuration at every draw. This preserves live
settings and introduces no stale configuration cache. Native coverage exercises
the actual adapted gate, its truth table and next-draw changes. Whole-frame gains
require separate matched measurements; reduced calls alone are not an FPS claim.
