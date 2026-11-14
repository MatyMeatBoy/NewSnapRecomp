# Presentation smoothness: RX 6900 XT and RTX 4060

Status: open, linked to PACE-01 / QA-AMD-01. Owner report of 13/11/2026: the local test
feels different from the GitHub ZIP run on the RX 6900 XT with a FreeSync monitor. Astral
Chain is their smoothness reference.

## What was checked in code and screenshots

- The launcher starts with `mailbox`; the AMD screenshot shows VSync. Neither proves an
  identical configuration or effective presentation.
- `vrr_adapt.py` queries and publishes status when the extension is available; it does not
  change the queue policy or turn FreeSync on by itself. The HUD's VSync name does not
  certify active VRR on the monitor either.
- The inherited pacer computes slots and availability in `nvn_api_obj.c`; Snap's overlay
  keeps the original interval and applies the host cap without Astral Chain's
  simulation-specific patches.
- A 60 FPS average or a 16.7 ms interval does not identify duplicates, dropped frames or the
  real output cadence of the compositor/monitor.

## Comparison needed to close

Use the same route, automatically identified runtime version, resolution, scale, native
preset, cache state and cap on both machines. Record the requested and effective swapchain
mode, monitor/refresh, observed or unknown VRR state, window/fullscreen mode and monitor
changes. Compare FIFO/mailbox where supported, without changing other settings at the same
time. Keep the host's p50/p95/p99, maximum and number/duration of spikes; complement with
observed presentation times when available. Separate CPU/GPU work, pacer wait,
acquire/present blocking and loads.

The intro head has its own task, HEAD-INTRO: a localised animation defect is not explained
by a global spike without correlated evidence. Do not copy Astral Chain's animation
addresses/patches or change speed, logic, simulation frames or colours to hide differences.

No physical AMD/NVIDIA comparison has been run in this review. Do not declare AMD
smoothness improved until there is a comparable measurement and the owner's confirmation.
GPU tests in the checkout are serialised with the keyboard/photo reproductions in progress.

## Update 0.8.6 (PACE-AMD-01)

The owner's monitor (Samsung C27HG7x) runs at 144 Hz. At 60 fps with FIFO and no active
VRR, frames alternate 2 and 3 refreshes (13.9/20.8 ms), which is the camera-turn judder.
The AMD driver does not expose `VK_EXT_present_timing`, so the game cannot tell whether
FreeSync is active. `AC_FPS=display` (launcher «Según la pantalla») caps at an exact
fraction of the refresh (72 at 144 Hz) and moves each present to the middle of its refresh
interval (DWM vblank timing, like Special K's Latent Sync). Measured: 100 % of presents
13.9 ms apart at 72 fps; the panel itself was not measured.
