# High frame rate options and investigation

## FPS-01 implementation — 2026-11-14

The launcher and in-game video menu offer **30 / 60 / 90 / 120 / 144 FPS**.
60 remains the default; there is no unlimited or 240 FPS option. Higher limits
are experimental. They can be changed live because they alter pacing, without
recreating rendering resources. A new private runtime is required: its receipt
must advertise `high-fps-presets`, so a new launcher cannot silently use an old
runtime that still caps at 60.

`newsnap/high_fps_adapt.py` lifts the ordinary interval-1 NVN host ceiling. It
preserves authored intervals of 2 or more and never enables Astral's `fps60`
patch. The strict parser falls back to 60 for unsupported environment/INI values.
There is no vendor-specific rate policy: the BC block-view, shader-math and
presentation fixes from 0.8 remain in effect. RTX 4060 results do not validate
the RX 6900 XT or FreeSync.

The script's 60 Hz tick estimate previously advanced by one tick per present.
Above 60 it now uses the clamped presentation delta, avoiding 2x/2.4x playback
of frame-number scripts. This remains a presentation-derived script clock,
including the existing 66.7 ms clamp; it is not an independently observed game
clock. The inherited log now calls its estimate `presentation clock`, rather
than claiming measured simulation speed.

### Read-only observations

The exact main SHA-256/build ID below is checked by the owner build before
generation, and the patch table checks original instructions. The probes replay
the original store and leave all Cpu registers and guest memory unchanged:

| Probe | Exact main site / original word | Opt-in diagnostic |
| --- | --- | --- |
| Timer after its channel updates, before epoch store | `6ac134 / f9000668` | `NEWSNAP_TIMER_TRACE=1` |
| Rail progress after its real store | `4c1df0 / bd007261` | `NEWSNAP_RAIL_TRACE=1` |
| UI Player::SetState entry | `79a6d0 / d10403ff` | `NEWSNAP_UI_TRACE=1` |
| UI event callback entry | `6c1d90 / d10203ff` | `NEWSNAP_UI_TRACE=1` |

`NEWSNAP_TIMER_PATCH=0` disables all observation sites. Logging is off by
default. The timer reports float and integer sums, mode and pause counts. The
rail probe checks readable objects, finite progress/length and a valid range;
it logs at most 1,024 samples with monotonic timestamps and object/reset identity.
It does not set progress, change vehicle speed or skip a scene.

The UI probes accept bounded printable short/long libc++ strings, reject invalid
descriptors and record at most 2,048 events per thread. They read scene/state
identities and events 2/3/5/6/7; per-frame event 22 is deliberately omitted.
State dwell and entered-to-ready intervals can be compared in real seconds.
They are state observations, not proof of every visual tween or HUD blink.

`tools/check_fps_rail.py` compares crossings of the same progress interval using
monotonic timestamps interpolated between samples. It rejects incomplete runs,
changed source saves and mismatched executable, input route, seed, cache, GPU or
settings receipts. It does not bridge rail resets. For example, with private
run folders and receipts:

```text
python tools/check_fps_rail.py build/fps01/rail60a build/fps01/rail120 --to-progress 80
```

This measures rail speed only. It cannot certify animation phases, input repeat,
audio synchronization, pose/score equivalence, photo persistence or display cadence.

### Reference audit and boundaries

The [Snap reference investigation](https://github.com/finalpantasy/new-pokemon-snap-recomp/blob/839128e031eb224455f8715fce755cf3cf12b9f6/docs/high-fps-plan.md)
and its [rail observation](https://github.com/finalpantasy/new-pokemon-snap-recomp/blob/839128e031eb224455f8715fce755cf3cf12b9f6/host/mods/neofilm.cpp)
provided candidates, subsequently checked against the local original module.
The rail comment's `4c2df0` offset does **not** match this module: local inspection
finds the stated load/add/store at `4c1de8..4c1df0`. No speed/film/progression mod
from that reference is enabled or copied.

Both timer callers and their indirect callbacks remain under investigation.
The 14 ms sleep loop is separate from the other caller; there is no basis for
globally shortening SleepThread or changing the shared 1/60 constant. The observed
timer channels use mode 0, but other consumers cannot be inferred from that alone.
In particular, integer milliseconds truncate each update. A fractional carry
would change their consumers; no carry patch is applied without attribution.
Menu/HUD animation, blink, cooldown and button-repeat timing need separate checks.

Gyro polling/integration uses its own real-time clock. The FPS option does not
increase the sensor worker rate or multiply sensitivity. Audio's device clock is
also preserved. These code boundaries do not replace physical input/audio tests.

[TotK's frame timing implementation](https://github.com/valentderah/totk-pc-recomp/blob/main/runtime/frame_rate.c)
illustrates separate pacing and simulation contracts, rather than transferable
Snap offsets. The [Vulkan presentation specification](https://docs.vulkan.org/refpages/latest/refpages/source/VkPresentModeKHR.html)
explains why a requested cap is not an achieved display rate: FIFO waits for the
display; mailbox availability, immediate/tearing and VRR remain separate concerns.

### Current local evidence

Private evidence is under `build/fps01/`, excluded from source control. Preliminary
60/120/144 runs lasted 100 seconds, 90 lasted 120 seconds, and a 120 FPS run lasted
360 seconds and reached photo selection after the expedition. They exited 0 and
preserved the source profile. Screenshots show the scene, HUD and thumbnails;
photo submission/scoring/persistence were not established by those runs. They
use different intermediate builds and are **not** an equivalence comparison.

The final comparison uses one executable, copied profile, route and cache seed.
All five 180-second runs exited 0 without a fatal and left the source profile
unchanged. The exact private executable SHA-256 is
`2b43d2ee9a519fb19e2b7bfa307b990495b55c4e28713767103c13bb5656a3a6`.
Settings: RTX 4060 Laptop / NVIDIA 616.92, docked 100%, original/upscaling off,
640×360 window, immediate presentation, same warmed shader-cache seed. These
are functional timing checks, not comparative performance benchmarks.

| Private run | Requested cap | Rail progress 10→80, wall seconds | Difference from first 60 |
| --- | ---: | ---: | ---: |
| `matrix60a` | 60 | 87.970909 | reference |
| `matrix120` | 120 | 87.970181 | −0.00083% |
| `matrix144` | 144 | 87.969785 | −0.00128% |
| `matrix90` | 90 | 87.970683 | −0.00026% |
| `matrix60b` | 60 | 87.968725 | −0.00248% |

Each high-rate result lies inside the two 60 FPS measurements. Interpolated
crossings are estimates between logged samples; the extra decimal places are
not a claim of sub-frame physical measurement accuracy. The final 120-present
window reported 60/120/144/90/60 FPS respectively. This establishes achieved
guest presentation rates in those windows, not a guarantee for all frames or
the physical panel's display rate.

All reported timer modes remained `0/0/0`, with no fixed-mode or paused samples.
The scene sequence `loading → skit_directing → loading` was observed in every
run; the skit state dwell was 36.969–37.154 seconds. The named page states and
entered-to-ready events were **not** recovered in this scenario. This does not
validate every menu/HUD animation. Reviewed screenshots show complete scene,
HUD, subject label and thumbnails at all four caps, but differing dialogue/photo
counts at the same script-clock screenshot confirm that these replays are not
an exact photo/pose/score-equivalence test. No scoring/progression bypass was
introduced to make the selection succeed.

Verification: the local Windows suite passed 483 tests (16 tool/platform skips),
then the actual compiled in-game FPS row passed its additional native test for
all five values and invalid/default selection. GitHub CI passed 493 tests
(34 skips on Linux). Native build, exact patch-word checks, content-index check
and independent read-only reviews passed. FPS-01 remains **REVIEW**, not complete
hardware/gameplay acceptance. AMD/FreeSync, physical controls/audio, full photo
evaluation/persistence and broader UI/HUD timing remain open.

A separate warm-start
attempt (`rail120`) exited 70 before the first frame with
`SwitchToFiber(0): not an initialized fiber`. That is the guest fiber-token
validation, not Windows rejecting a host fiber and not an out-of-memory finding.
The cause and any relationship to FPS are unproven; do not turn null into a
successful fiber switch to hide it.
Four subsequent copied-profile boot controls (120, 60, 120, 144 FPS, three
seconds each after boot) exited 0. This does not identify or fix that isolated
failure; keep it visible during further testing.

## Historical static investigation — 2026-11-13

At the time of the investigation below, more than 60 presents/s with correct
game timing had not been demonstrated. The acceptance criteria remain useful;
the current implementation/evidence above supersedes historical status claims.

## Scope and provenance

Read-only static inspection used the owner's imported 2.0.1 `main`, build ID `ddb900ff04a912ed42430508389853cfaf1accce`, SHA-256 `ef20d6317d909bde106fec0958b58ccfdf4c46f36d9fa5ef8785ce54fff75443`. The build ID was read from the NSO and the file hash independently verified against the existing profile. Analysis used the NSO loader in `third_party/astral/recomp/nso.py` and selective AArch64 disassembly. Addresses below are **module-relative offsets in this exact main**, not donor addresses or stable patch interfaces. No module, generated C, disassembly dump or game assets belong in this document or a public commit.

The current runtime has reached a 240-second 3D tutorial probe according to the ongoing bring-up work. A complete route, photo submission/evaluation and save/reload comparison have not been established. This document adds static evidence and a validation strategy, not a high-FPS gameplay test.

## What the available code establishes

The upstream runtime's `frame_step_realtime()` returns zero. Its NVN pacer interprets interval 1 as 1/60 second, with an emulated 60 Hz presentation basis. A selected 30/60 host cap that takes the maximum of the native period and selected cap can slow presentation; it cannot authorize a faster guest update cadence. Removing that wait alone would leave the following timing questions unresolved.

The large upstream `runtime/frame_rate.c` contains Astral Chain-specific timer, counter, cinematic and movie adaptations. Its comments and hardcoded addresses describe that other game. They provide examples of failure categories, not evidence that Snap needs the same fixes. Do not enable its donor FPS patch set or transplant its offsets into Snap.

Snap imports both monotonic tick and frequency APIs. The identified PLT entries are:

| API | main offset |
| --- | --- |
| `nn::os::GetSystemTick()` | `0xa36ac0` |
| `nn::os::GetSystemTickFrequency()` | `0xa36a30` |
| `nn::os::ConvertToTimeSpan()` | `0xa37bd0` |
| `nn::vi::GetDisplayVsyncEvent()` | `0xa38dc0` |

The display-vsync import is called at `0x985f50`; its surrounding initialization supplies the string `VSync Count Thread`. This identifies another native timing surface to trace. It does not yet establish which simulation consumers use its counter.

### Snap timer candidate with variable and fixed modes

`main+0x6abea0` is a timer-update candidate with direct callers at `0x4e09bc` and `0x4e0f70`. Both callers obtain the object from the pointer slot at `main+0xcfc238`. Nearby dispatch calls pass the timer object as an argument to an indirect callback (`0x4e0bbc` and `0x4e0fc8`). These are promising instrumentation points, but their owning gameplay subsystem and actual call frequency remain unmeasured.

Static behavior in the candidate:

- It reads the system tick, subtracts an epoch, converts the elapsed duration to microseconds, and subtracts the previous sample at object offset `+0x08`.
- For a positive elapsed delta no greater than 500,000 microseconds, the variable path produces floating-point seconds using division by 1,000,000 and integer milliseconds using division by 1,000.
- A delta greater than 500,000 microseconds takes a recovery path with a 1/60-second float and integer value 16. This is a discontinuity/recovery policy, not an ordinary high-FPS lower clamp.
- Three channel groups store a float delta and an integer delta. Each has a mode and flags. **Mode equal to 1 uses a fixed 1/60-second step per call**, with an accumulated correction near the one-second boundary. Other ordinary paths store the measured delta. Pause-like flags can zero a channel. Their semantic names are not yet recovered.

| Candidate channel | Integer milliseconds | Float seconds | Mode | Accumulator | Zeroing flag |
| --- | --- | --- | --- | --- | --- |
| A | `+0x10` | `+0x1c` | `+0x18` | `+0x20` | `+0x24` |
| B | `+0x28` | `+0x34` | `+0x30` | `+0x38` | `+0x3c` |
| C | `+0x40` | `+0x4c` | `+0x48` | `+0x50` | `+0x54` |

This establishes that the binary contains both measured-time and fixed-step behavior. It **does not establish** that any channel is used by route movement, camera, animation, cinematics, scoring, or audio; nor does it establish their active modes. If a mode-1 channel advances once per present, 120 presents/s would advance it at twice the intended rate. If the owning scheduler keeps those calls at 60 Hz, that particular risk does not follow. Measure the relationship before choosing a patch.

There are also separate tick-to-millisecond helpers around `0x1662fc`, `0x1664a8` and `0x1664e4`, including an optional indirect clock provider. A tick-to-microsecond initialization path exists around `0x1d5498`. Multiple timing domains therefore need ownership tracing; changing a single timer cannot be assumed to cover the engine.

### Existing telemetry and scripted input limitations

The upstream `frame_step_present()` adds `interval / 60` to its `game_us` counter. With the Snap guest timer unhooked, that is a presentation-derived estimate, not an observed Snap simulation clock. A log line saying `speed 1.000` from this code is insufficient evidence of correct guest timing.

`AC_INPUT_SCRIPT` supports `@<milliseconds>` events and millisecond holds. However, the existing `frame_step_world_us()` clock starts on the first present and, with realtime stepping disabled, adds `min(present_delta, 1/15 second)`. A hitch longer than approximately 66.7 ms loses time in this script clock. It is not an independent monotonic wall clock or an established route-start clock. Untimed script lines advance on presentation-derived ticks as well. Changing present cadence can change input sampling even when event times use milliseconds.

Before using scripted input to prove equivalence, record both the intended host monotonic event time and actual guest sampling time. Use a measured scene/route-ready marker for the comparison epoch, preserve neutral input outside explicit holds, and report pauses/loading separately. For the current script system, report accumulated clamped time and event-delivery delay. Do not call a replay deterministic solely because its source text uses `@ms`.

## Strategy options

1. **Keep simulation at its measured native tick and decouple rendering.** First establish the real native tick, which may differ by subsystem. Preserve update, RNG, event, input and photography evaluation calls at that cadence. Render snapshots between ticks using a render-only interpolation factor. Interpolate camera, transforms and skeletal poses only after identifying ownership and discontinuities. Teleports, cuts, UI transitions and photo capture must use explicit snapshot rules. Extra render passes must not repeat callbacks, scoring, RNG, sound triggers or capture requests. At 120 Hz a 60 Hz tick has a simple 2:1 display ratio; at 144 Hz the display samples are fractional and require an accumulator/phase calculation. Unlimited rendering still needs bounded queues and simulation scheduling independent of display completion.

2. **Increase simulation frequency only after auditing consumers.** Instrument the candidate timer and its dispatch first. Recover its initialization, mode writes, channel consumers and relationship to presents. Establish which consumers use seconds, integer milliseconds, fixed counts, thresholds, smoothing factors or native-vsync counters. Then evaluate arbitrary dt versus a higher fixed tick with accumulated time. Per-frame integer counters require fractional carry or conversion to elapsed duration; exponential smoothing must preserve its time constant; threshold crossings need interval checks. Do not blindly replace every `60` constant or force every channel into variable mode.

3. **Frame generation/post-processing is a separate visual option.** It can synthesize display frames while leaving the native simulation intact, but it does not provide higher-frequency game input or photo evaluation. It needs its own image-quality and latency tests. It is not evidence of engine support for high FPS.

Option 1 is the lower-risk research direction for preserving gameplay semantics. It is not yet implemented, and render/simulation separation has not been proven feasible in this runtime. Duplicating an NVN present only repeats a picture; it does not perform transform interpolation.

## Required instrumentation before an FPS patch

At scene-ready anchors, collect host monotonic time, native tick count, presents, timer-candidate calls, all three channel modes/deltas, pause flags and native-vsync count. Collect samples without calling graphics/UI tools from the instrumentation path. Avoid logging every object every frame; aggregate timing and emit event markers.

Trace which timer channels reach:

- Route/vehicle movement and Pokémon position/behavior, RNG calls and scripted triggers.
- Animation clocks, blend factors, effect lifetimes, particles, cinematic cuts, dialogue reveal and movie decoding.
- Camera rotation/zoom, input edges, held-button repeat and any camera smoothing/acceleration.
- Shutter acceptance, cooldown, photo buffer creation, target/pose selection, occlusion/size/centering and evaluation.
- Audio device time, music/voice triggers, cinematic synchronization, pause/resume and loading recovery.

For every proposed guest change, bind the offset and original instruction bytes to the exact build/hash and fail closed on a mismatch. Keep private binary evidence outside source control. Publish findings and patch intent without redistributing generated module code.

## Equivalence test and release gates

Use an identical copied save and stable scene-ready anchor for a baseline at the native cadence, then 60, 120, 144 and unlimited presentation modes. Restore that save before each run. Pin RNG seed/state where recoverable; otherwise run repeated baselines to quantify natural variation before setting tolerances. Keep resolution, graphics, shader cache state and hardware identical. Record achieved simulation and presentation rates independently; a requested cap is not an achieved rate.

Replay neutral sections, fixed-duration stick holds, button presses/releases, zoom, scan/items and timed shutter events using monotonic milliseconds. Deliver input at a defined simulation sampling boundary and record quantization. The comparison concerns equivalent wall times and native simulation ticks, never equal present numbers. Test short pulses and sustained holds; a faster present loop must not create extra button edges or auto-repeat actions.

At matching route times, compare camera pose and vehicle/Pokémon transforms, animation phase and event order/count. Capture screenshots for visible equivalence, while using numerical/event traces to detect timing drift that still images miss. Complete at least one full route and its transitions. Run stationary and moving-camera shots, rapid shutter requests and simultaneous effects. For the same logical capture instant compare photo count, Pokémon identity, pose/star category, score components, total score, selected thumbnail and saved photograph metadata. Exact scores/categories are the default gate; any tolerance requires an explained source of baseline nondeterminism. Screenshot similarity alone does not establish evaluation correctness.

Check cinematic duration against host time and audio onset/cut/end markers; include movies, pause/resume and scene changes. Exercise hitches at 8/16/33/67/100/500+ ms and verify that catch-up policy neither accelerates game logic nor permanently desynchronizes sound. Repeat with a cold shader cache, a warm cache and under sustained load. Save, quit, reload and verify route/photo state. Run a longer session spanning several scenes after the full-route comparison passes.

120/144/unlimited can be described as supported only when the same event sequence, timing, photo evaluation and save state remain equivalent at their achieved rates. An FPS counter, a short tutorial, the absence of crashes, a present-derived speed log or a visually smooth camera cannot substitute for those gates. Until then, the established limit is **unverified timing above 60**, not a proof that it is impossible.
