# Optional trace of presentation waits

The AMD evidence received asked for mailbox but got FIFO; the local NVIDIA A/B got mailbox.
The existing counters lump fence waits and replay draining together and can add intervals
from several threads. They do not allow attributing a specific hitch to acquisition,
presentation, GPU or swapchain rebuild.

`AC_SNAP_PRESENT_TRACE=1` enables per-process observations. It is read once through the
runtime's constructor, before threads start; any other value leaves it off. It is not an INI
preference or a synchronisation policy. The launcher can pass it explicitly to a test's
process. This change does not modify the launcher or turn the flag on by default.

## What it measures

The `present_trace_adapt.py` adapter uses eleven exact anchors in `runtime/gfx_present.c`. A
`plat_now_ns()` pair surrounds the real operations:

- `acquire`: every `vkAcquireNextImageKHR`, including the retry after
  `VK_ERROR_OUT_OF_DATE_KHR`.
- `fence`: the wait before the slot and the extra wait used when capturing. Both are added to
  the same category; to compare pacing, do not take captures.
- `queue_present`: `vkQueuePresentKHR`. The interval excludes taking/releasing the queue
  lock; the log is written after releasing it.
- `rebuild`: the whole existing creation/rebuild function, from its entry to each return,
  including the pending flush, queries, device-idle wait and resource creation/release. Its
  result is the original boolean, not a `VkResult`. The duration can include a present call
  also measured separately: **do not add the categories as exclusive times**.

`snap_present_trace: operation=...` lines contain count, sum, minimum and maximum in
nanoseconds, the number of non-success results and the last sample's result. For Vulkan,
success means `VK_SUCCESS` (0); `SUBOPTIMAL`, timeout and other results count as
`other_results`, without treating them all as fatal failures. For rebuild, success means 1.
The counters accumulate from process start; they are not percentiles or a sliding window.

The first sample of each category is emitted. After that, at most one line per second and
category, after about 120 calls; at 60 FPS that is about two seconds. Infrequent rebuilds do
not wait for 120 calls but keep the one-second limit. Final samples that do not reach the next
threshold are not flushed on close. Storage is fixed: four buckets, no frame lists, helper
threads or new files.

A swapchain line reports the requested/effective mode, the enumerated modes as Vulkan values,
the reported/captured count, that query's result, requested/real images, the image query's
result and the extent. It reuses the queries the donor already runs; it adds no GPU queries.
The enumeration keeps the existing limit of 16 modes. If the image query does not end in
success, `images_actual=0` means unknown. These snapshots are limited to one line per second:
they are not an exhaustive history of rapid changes. VRR, FreeSync, monitor support or
physical presentation are not deduced from FIFO, mailbox, CPU times or the image count.

## Contract without policy changes

Off, the wrappers only check the flag and call neither the clock, the logger nor the
aggregation functions. Timeouts, retries, results, the image counts the donor uses,
priorities, sleeps, cap, queues and the order of Vulkan calls are not changed. Every point is
serialised by the existing `g_pl`; the helper adds no locks. The flag is initialised before
the threads and never changed live. Attributions and the original donor stay intact.

`python -m unittest tests.test_present_trace` runs three CPU tests:

- The helper's native fixture: exact opt-in, zero time queries/logs when off, known
  aggregates, negative/positive Vulkan results, boolean rebuild counting and emission limits.
- Anchors over the real donor: both acquisitions and fences are still present, without
  duplicating calls or changing exit/retry conditions.
- The real adapted mode-selection, flip and rebuild-wrapper functions with simulated Vulkan:
  they keep the fallback, lock order, codes/dirty flags and returns both off and on. The
  present test deliberately adds time to the unlock and checks it stays outside the measured
  interval.

Before the implementation the opt-in and the missing seams failed. All three tests pass after
the change. No GPU or game is run. Missing: the coordinator's integration, a complete
`adapt_sources`, the build and a serialised GPU run.

## Minimal follow-up experiment

Use the same binary, a known short route, resolution, cache state and copied profile. Lock a
supported effective mode during each run, without changing it live or capturing frames.
Record drivers and requested/real mode. Compare acquisition, fence, queue-present and rebuilds
separately along with the existing frametimes; the accumulated values allow count/sum
differences, but their maxima are not p99. Require repeatable queue improvements without
errors, changes in game cadence or photo regressions. The trace has a diagnostic cost when
on: do not present its result as a clean benchmark or as AMD validation because it was tested
on NVIDIA.
