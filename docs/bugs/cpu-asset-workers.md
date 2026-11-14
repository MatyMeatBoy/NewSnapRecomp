# CPU resource workers and intro frame spikes

Status: verified resource bridge integrated and shipped in the limited 0.5 alpha;
local A/B and final public-kit/photo acceptance are recorded below and in
`v05-alpha-acceptance.md`. Residual core waits remain under investigation after
publication. No AMD performance conclusion; old-profile recovery is out of scope.

## Observed cause and limits

Matched normal-mode RTX 4060 Laptop GPU runs, without `--shot`, compare the
original 0.4 executable against the earlier 06a8d9df candidate. Both average
about 17 ms per game-side present; the new candidate does not demonstrate an
overall pacing improvement. Full-run p99 is 34.78 versus 42.52 ms. GPU busy is
about 1.2 ms, with no runtime shader/pipeline blocking or skipped draws in these
warm measurements. This excludes sustained GPU saturation here, not CPU deadline
misses. The runtime's reported game-thread busy time is residual wall time after
pacing, not measured CPU execution time.

The early spikes are real late game arrivals: for example a 110.4 ms frame has
zero pacing/fence/pipeline/translation wait and only 0.27 ms replay-drain time.
The host present can report little target lateness because its pacer restarts
the phase after falling a whole period behind. This does not make the preceding
frame punctual. Shader/pipeline prewarming before guest entry is separate.

A separately authorized sampling run identifies three resource workers running
the integer operation at `main+0x5ec660`, called by the block-transform worker at
`main+0x5ec890`. The worker XORs its generated words into resource blocks before
signalling completion. The presenting thread mostly waits for guest
synchronization or a virtual core; the Vulkan replay thread is mostly idle.
Some spikes also contain positional RomFS reads. The sampler suspends threads,
so its timings are attribution evidence, not comparable p99 measurements.

A subsequent 10-second run with existing `AC_CORE_DIAG=1` and no sampler confirms
that virtual-core starvation also contributes. Presenting-thread ready waits
classified as game-owner waits are 50.16 ms in a 90.6 ms frame, 41.79 ms in a
76.9 ms frame, and 68.73 ms in a 110.4 ms frame. Higher-priority ready threads
repeatedly wait for lower-priority workers executing this operation; several
preemption waits last 2–3 ms, with larger outliers. Whole-thread accounting sums
can exceed a frame and must not be interpreted as CPU utilization.

Required resource work and scheduling latency are distinct. This change only
reduces lifting overhead for the same integer operation. It does not claim to
resolve starvation, all frame spikes, field model jitter, photographs or AMD
behavior. No checkpoint, priority, worker, IPC, validation, progress or 30/60
simulation change is included.

## Verified bridge

`snap_random_range.c` implements the same four-word state progression, inclusive
bounded result, arithmetic shifts, rejection and recursive range construction.
The large-bound case retains two state advances even for `UINT32_MAX`; replacing
it with one superficially equivalent random draw would change the stream. State
stores retain the original word order and intermediate large-bound advances.
Unaligned words use `memcpy`; arithmetic shifts use defined unsigned operations.

The bridge publishes the original final values of all caller-clobbered
registers as well as its result and state. Safety therefore does not rely on
assuming that local callers ignore AAPCS volatile registers. It leaves all other
`Cpu` fields unchanged. It does not reproduce up to 160 bytes of dead guest
stack scratch below the restored SP. Tests bound the original's scratch writes
and require the bridge to write no guest memory outside its 16-byte state.
The function restores SP and returns no pointer into that dead scratch. Direct
caller inspection finds no below-SP reads; this is not a general alias proof for
arbitrary indirect callers or debugger inspection.

All generated main chunks were searched. Besides two recursive sites, direct
calls occur in `main+0x4d5300` (two), `main+0x5e4770` (nine), and the observed
worker (one). The first private inventory missed the two sites in another
chunk; the complete inventory supersedes it. Boundary and random-bound tests
cover the operation beyond the observed worker's `UINT32_MAX` use.

The only hook is an existing generator patch alternative at the function entry:
one `@fn:snap_random_range` followed by return. The original path remains intact;
`AC_SNAP_RANDOM_RANGE=0` selects it. Initial function-entry profiling disables
the bridge to retain the original recursive profiling callbacks.

Before generation **or cache lookup**, the build must call
`random_range_adapt.verify_original(exefs)` and include the new patch in its
combined patch recipe. This checks the exact original main SHA256, build ID,
entire 0x1a0-byte function span, and the patch text hash, normalized only for
checkout line endings. The injected generator guard independently verifies
those pins and the exact entry alternative. It rejects other patches inside
the function and any use of this helper at another site or module, including
SDK-only generation. It also rejects any main-module spin gate whose head or
back-edge falls inside the half-open verified span. A spin changes scheduler
behavior in the original path, so the entry bridge cannot silently bypass it.
An unsupported recipe fails closed.

## Evidence and verification

The private prototype passes 98,304 differential calls and a 65,536-call mixed
stream with synthetic XOR data, with equal full `Cpu` state, result and PRNG
state. Its isolated microbenchmark retains about 5.65× lower cost after copying
the exact final register values: roughly 24.59 versus 4.35 ns per call with both
bodies at `-O1`. These short CPU batches measure lifting overhead; they are not
an FPS or production-helper performance claim.

The production tests additionally compile the actual donor generator's entry
alternative and compare the enabled bridge, disabled original path and direct
helper against the actual private generated-C oracle. All 1,024 `Cpu` bytes and
state match in 8,192 cases. An independent Python integer reference covers
4,096 cases. Tests include edge/random bounds, high incoming register bits,
unaligned state, rejection, original/hash/span/patch mismatch, unexpected
module sites, and real patch-initialization opt-out/profiling behavior.

Independent review found a missing spin-table check. The regression uses the
real parser and original branch at back-edge `0x5ec6fc` to head `0x5ec6d0`:
`patches.check` accepts it and the actual emitter adds `rt_spin_gate`. The old
guard incorrectly accepted both main and SDK-only invocations. The corrected
guard rejects both before input/module-specific handling. Boundary tests cover
either endpoint, inclusive start, exclusive end and unrelated SDK-module spins.

```powershell
.venv/Scripts/python.exe -B -m unittest tests.test_random_range -v
```

Native tests require clang and donor headers. The actual original-C oracle test
uses existing verified local inputs and skips when those private inputs are
unavailable; no game body or original data is committed as a fixture. All its
derived native files stay in temporary directories under `build/`.

Local evidence remains in `build/v05-normal-pacing-ab/`,
`build/v05-normal-pacing-profile/`, `build/v05-normal-pacing-corediag/` and
`build/v05-prng-prototype/`. It must not be uploaded. Original owner GameData
remains on 0.4; saves, photos, imports and keys are unchanged.

Independent review, final native compilation, a matched application A/B and
photograph regression testing remain required before claiming this bridge
improves the game or shipping 0.5.

## Controlled application A/B after integration

The integrated executable SHA256 is
`5b6671c92aa1776d1e99ab898a2e5503416f85e105554900c19006a176e40645`.
A subsequent normal-mode experiment uses this **same executable and path**
with only `AC_SNAP_RANDOM_RANGE=0` or `1`. Both settings receive one 40-second
warmup, then two measured 40-second pairs in reversed order: OFF→ON, ON→OFF.
Each run starts from an identical copied profile and input route. After both
warmups, a common application-cache snapshot is restored before every measured
run; complete cache-file SHA256 inventories are verified identical. The patch
state is confirmed in each process log. Root CPU builds/tests were stopped
during these six serial GPU runs.

Settings are Original, docked render 100%, cap 60; no `--shot`, sampling profiler
or core diagnostic. Flight thumbnails are disabled. The game present image is
1920×1080 and the actual window/swapchain is 1920×1055 in all four measurements.
Device: RTX 4060 Laptop GPU, driver 616.92. Global OS/driver caches and thermal
state cannot be made identical; individual warmups and reversed order reduce
those confounds. These are two pairs on one device, not broad hardware evidence.

Full-window game-side present intervals, in milliseconds:

| Run | Samples | Mean | p50 | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Pair 1 OFF | 2,351 | 17.059 | 16.658 | 19.370 | 42.314 | 113.669 |
| Pair 1 ON | 2,389 | 16.718 | 16.677 | 18.898 | 26.498 | 71.928 |
| Pair 2 ON | 2,386 | 16.754 | 16.657 | 19.085 | 24.203 | 107.692 |
| Pair 2 OFF | 2,345 | 17.117 | 16.656 | 19.196 | 47.384 | 143.893 |

Pooling the two full windows per setting gives p99 42.970 ms OFF versus
25.469 ms ON, approximately 40.7% lower. Frames over 50 ms fall from 40 to 14;
over 100 ms from 7 to 1. Medians remain near 16.67 ms. The reduction repeats in
both orders and supports a tail-latency improvement for this intro workload.
It is measured application evidence, separate from the isolated CPU ratio.

All six runs exit successfully with their requested patch state; all four
measured runs report zero validation errors, shader failures, unimplemented NVN
calls and skipped draws. Runtime pipeline/translation blocking is zero in their
flight records. GPU busy averages 1.10–1.16 ms. The owner profile, INI and original
0.4 executable remain byte-identical by before/after SHA256 inventories.

A 107.692 ms maximum remains with the bridge enabled. Its cause was not sampled
in this experiment. The separate scheduler policy was not changed or revalidated
here; the earlier core-starvation finding must not be declared fixed merely
because resource work is faster. This intro result does not validate field
model jitter, photograph behavior, tutorial completion or the owner's AMD GPU.
PACE-01 and release 0.5 therefore remain open pending the relevant follow-up.

Exact arguments, environment, cache/profile inventories, logs, flight TSVs and
statistics are retained privately in `build/v05-rng-pacing-ab/`; see
`comparison.json` and its reproducible `benchmark.py`/`summarize.py`. Do not upload
this directory or the copied runtime/profile data.
