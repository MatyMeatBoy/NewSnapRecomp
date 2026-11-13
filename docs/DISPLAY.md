# Display and VRR observations

Version 0.5 reports the presentation engine's timing separately from the game's
synchronization setting. FIFO, mailbox and immediate describe queue behavior;
none by itself establishes that FreeSync, G-SYNC or another VRR mode is active.
The native 30/60 FPS settings and neutral SDR rendering are preserved.

## What is observed

The optional native backend uses `VK_EXT_present_timing` on the game's existing
swapchain. It queries `vkGetSwapchainTimingPropertiesEXT` after a real present,
while the existing `g_pl` lock excludes swapchain replacement/destruction.

| Result | Report |
| --- | --- |
| `VK_SUCCESS`, nonzero duration, interval equal to duration | `fixed` |
| `VK_SUCCESS`, nonzero duration, interval `UINT64_MAX` | `variable` |
| `VK_NOT_READY`, a zero timing value, unavailable API, failed query or unclassified values | `unknown` |

These meanings come directly from the [Khronos timing-property contract](https://docs.vulkan.org/refpages/latest/refpages/source/VkSwapchainTimingPropertiesEXT.html).
A variable observation describes this swapchain's presentation engine. It does
not identify a monitor certification, enable a driver option or establish that
every frame was scanned out without repetition. A fixed observation can reflect
compositor policy; it is not evidence that the monitor lacks VRR hardware.
Monitor identity is the Windows window monitor's GDI device name, accompanied by
the operating system's display description when available. Empty names mean
identity was unavailable; the adapter does not invent a monitor name or use the
rendering GPU's vendor as the display owner's identity.

## Optional negotiation and fallback

The backend enables the advertised instance extension
`VK_KHR_get_surface_capabilities2` when a slot is available. Device negotiation
requires the complete advertised dependency bundle: `VK_EXT_present_timing`,
`VK_KHR_present_id2`, `VK_KHR_calibrated_timestamps` and `VK_KHR_swapchain`.
It queries the optional feature structures before device creation. The feature
chain is inserted before the donor's removable graphics-pipeline-library tail.
The negotiated `presentTiming` feature and resolved query entry point are both
required before issuing a query. Missing dependencies, feature support or entry
points retain ordinary presentation and report unknown.

Absolute/relative present-scheduling features and present-ID emission are disabled.
No timing-result queue is allocated, no present-timing swapchain flag is added,
and no scheduling metadata is attached to `vkQueuePresentKHR`. The query's
[valid usage](https://docs.vulkan.org/refpages/latest/refpages/source/vkGetSwapchainTimingPropertiesEXT.html)
does not require these queues/flags. Extension dependencies are documented by
[Khronos](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_present_timing.html).

The adapter does not change Windows, driver or monitor configuration. It does not
request exclusive fullscreen. Display hardware support and driver enablement
remain explicit unknown facts: this backend provides neither a vendor control
panel query nor a guessed interpretation of the selected present mode.

## Local status contract

The launcher supplies a fresh absolute `NEWSNAP_DISPLAY_STATUS` destination for
each owned game attempt. An unset or relative destination disables file output.
The runtime queues a single bounded JSON object to an owned writer thread, which
uses the existing atomic file replacement helper. This helper flushes data to disk;
those writes and flushes run outside the presentation thread and its locks.
The queue holds one replaceable pending blob, in addition to the writer's current
immutable blob; newer queued observations replace older ones without growing a
backlog. Shutdown joins the writer after queuing the stopped observation. The
worker owns no Vulkan or window references and acquires no presentation/queue lock.
No worker starts when the destination is unset or relative. Write failures produce
one bounded log warning, discard queued observations and make later reports unknown.
Normal polling/publication is limited to once per second;
initialization, invalidation and presentation errors can publish immediately.
Display descriptions are cached until monitor identity changes.

The format is `newsnap-display-status-v1`, with numeric `version: 1`:

- `source`: `vulkan_ext_present_timing` for a classified timing observation,
  otherwise `none`.
- `presentation`: `unknown`, `fixed` or `variable`.
- `display_support`, `driver_enabled`: `unknown`; kept separate from observations.
- `timing_api_available`: whether the optional device query was enabled/resolved.
- `generation`: monotonically increases on initialization, swapchain replacement,
  detected monitor changes and shutdown, including device recreation in one process.
- `observed_monotonic_ns`: opaque process-side observation timestamp, not UTC.
- `process_id`: identifies the publishing runtime.
- `monitor_id`, `monitor_name`: bounded GDI identity/description, or empty.
- `actual_present_mode`: the mode actually selected by the swapchain code.
- `vk_result`, `reason`: diagnostic result and bounded reason.
- `refresh_duration_ns`, `refresh_interval_ns`: queried values, cleared on errors.

Swapchain recreation and monitor changes clear the previous timing observation
before further queries. Shutdown publishes unknown/stopped. Failed or not-ready
queries never retain an older variable result. The launcher should validate the
format, owned process, fresh attempt path and file age; it must not compare the
opaque native timestamp to a different process's clock. A stopped/crashed process
must not leave a green active status merely because an old file remains.

## Verification and limits

`python -m unittest tests.test_vrr -v` executes the actual native adapter and JSON
serializer with a mocked Vulkan query and file sink. It covers fixed/variable/
unknown classification, query failure, unavailable extension, zero values,
swapchain invalidation, bounded polling, JSON escaping/capacity and dependency
negotiation. An actual native worker test blocks its file sink while publishing
99 newer observations, verifies only the latest pending blob is written, checks
shutdown drains the queue, and exercises writer failure/recovery and absent paths.
Exact source seams protect the lock-owned integration and optional
feature-chain ordering. The new C files and isolated adapted `vk_device.c`/
`gfx_present.c` compile with the pinned LLVM/Vulkan toolchain and `-Wall -Werror`.

On 2026-11-13, read-only physical-device enumeration on the available NVIDIA
GeForce RTX 4060 Laptop GPU advertised `VK_EXT_present_timing` revision 3,
`VK_KHR_present_id2` revision 1 and `VK_KHR_calibrated_timestamps` revision 1.
This inventory created no swapchain or rendering workload and does not establish
an observed VRR mode. Actual game observations, AMD target-device behavior,
monitor transitions and hardware VRR acceptance are separate evidence.
