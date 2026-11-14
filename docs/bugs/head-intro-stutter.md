# HEAD-INTRO · The character's head vibrates when walking in during the intro

Status: **REVIEW** · Owner: MatyMeatBoy · 2026-11-14
Hardware: RTX 4060 Laptop, private diagnostic runtime derived from `e314751d`.
Measured SHA256: `6221080431d8c18ac1de5b30ebb1df6629e6408dee0ad33dfa8253100c53c08c`.
**Cause not identified; no fix.** This report narrows the problem with measurements of one
shot and one intervention on its timer. It does not rule out pacing, loading, driver or other
subsystem causes in general.

Provenance note: the original report was made on the RX 6900 XT with a 0.1.x-generation
runtime (see `keyboard-after-photo.md`). What is measured here is the behaviour of that
diagnostic binary on RTX, not a validation of the public executable or the physical AMD chain.

## Result

| Claim | Class | Evidence |
|---|---|---|
| In this RTX shot the head region moves unevenly | **Observed** | Index ≈0.25 on the head, ≈0.11 on the torso and ≈0.004 on the background; GPU independence not established |
| The recorded cadence averages close to 60 FPS in the measured window | **Observed** | Recorder intervals: mean ≈16.67 ms, deviation 1.0–1.7 ms, max 21.9 ms; not physical presentation timestamps |
| The measured background is more even than the head in these regions | **Observed** | Index ≈0.004 in four runs; does not exclude every camera contribution or calibrate the method's noise |
| Quantising the timer did not remove the measured irregularity in this shot | **Bounded intervention** | Step deviation drops to 0.02 ms; head index 0.248/0.246 against 0.248/0.248 unquantised |
| The four runs have similar indices | **Observed** | 0.2482 / 0.2479 / 0.2456 / 0.2482; this does not prove all trajectories equal or rule out loading, CRC or background work |
| An equivalent quantitative comparison at 30 FPS | **Pending** | An exploratory run exists; this tool's JSON with auditable window, regions and counts is missing |
| Both halves of the head show similar patterns | **Exploratory observation** | Not an independent calibration of the optical error, nor proof by itself of an animation cause |
| Which game subsystem produces it | **Undetermined** | See hypotheses |
| Whether the original console shows it the same | **Undetermined** | No reference capture from real hardware |

## What was measured

Shot: the character walks in, back to the camera, towards the lab, just before the logo
(presents ≈2775–2858 at 60 fps on a new profile with the `tests/routes/initial-setup.txt`
route).

Method (`tools/measure_region_motion.py`): the runtime's flight recorder (`AC_FLIGHT=1`) keeps
thumbnails per present in memory. Its diagnostic cost is not zero. Over consecutive frames the
sub-pixel displacement of three rectangles — head, torso and background (the lab, which only
reflects the camera) — and its regularity are measured:

- **irregularity**: each step's deviation from its 5-frame moving average, relative to the
  step size;
- **alternation**: the part of that deviation that flips sign every frame (what a component
  updated at half cadence would do).

Both indices are dimensionless. The original frame indices are kept: gaps and rejected pairs
split segments, without inventing adjacency or resetting the even/odd phase. `frames` counts
accepted pairs, `discarded` those rejected by residual, `segments` the contiguous sequences
and `analyzed_pairs` the interior pairs that take part in the metric after trimming the edges.
Segments that are too short give no verdict.

Full-size captures (`AC_SHOTS_FULL`) are no use for this: writing 8 MB per frame slows the game
and alters the motion. The thumbnails were taken at 640×360 from a 1280×720 window with a
private diagnostic runtime (the thumbnail size is a compile-time constant; at 320×180 the cap
has little texture and at 960×540 frames are lost).

| Run (`build/…`) | Cadence | Game time step (ms, dev.) | Head | Torso | Background |
|---|---|---|---|---|---|
| `head01-ab-off-1` | 60 | 16.69 ± 1.03 | 0.248 | 0.109 | 0.004 |
| `head01-ab-on-1` (exact time) | 60 | 16.68 ± 0.02 | 0.248 | 0.109 | 0.003 |
| `head01-ab-on-2` (exact time) | 60 | 16.68 ± 0.02 | 0.246 | 0.091 | 0.004 |
| `head01-ab-off-2` | 60 | 16.66 ± 1.71 | 0.248 | 0.109 | 0.004 |
| `head01-fps30` (exploratory) | 30 | Comparison pending | — | — | — |

Each `motion.json` of the four 60 FPS runs keeps the 2775–2858 window, 83 pairs per region
and zero discards. The counts and regions are part of the comparison; indices from different
methods or windows must not be mixed. The 30 FPS run keeps a `flow.json` from an earlier
exploratory analysis, but no equivalent `motion.json`. The old values 0.202/0.170/0.003 stay
out of this table until that report is regenerated and kept with an explicit window and
regions; they do not allow ruling out a cadence cause.

Example of consecutive horizontal head steps at 60 fps (px at 640×360): 2.00 · 1.29 · 1.81 ·
1.19 · 1.56 · 1.18 · 1.38 · 1.23, with the background at 1.07 · 1.09 · 1.10 · 1.11 · 1.13 ·
1.14 · 1.15 · 1.16 over the same frames. The high/low alternation comes in bursts
(≈2773–2784, 2789–2800, 2821–2832), not over the whole shot, which is why the global
alternation index is low (0.012) and the irregularity index high.

## Experiment: exact frame time

The game's frame timer (`main+0x6abea0`) measures real time between updates; its three
channels are always in «measured» mode (trace of 3,586 calls, a single call site). On the host
that time swings between ≈12 and ≈22 ms even though the mean is exact.

In a private runtime that update was given an earlier instant such that the measured step was
a whole number of 60 Hz periods, with an ideal clock that follows the real one without drift.
Effect on the step: deviation from 1.0–1.7 ms to 0.02 ms. It is not seen to remove the
irregularity of the measured region (table). The shot has similar indices across runs with
different rhythm variations, though not identical in every region. Bounded conclusion: this
intervention reduced the timer's variation without removing the optical irregularity of the
measured region. It does not show that presentation rhythm, the driver or all of the game's
timers and subsystems are unrelated to the symptom.

The experiment writes to a field of the game's timer; it is only a diagnostic instrument, not
a proposed fix, and it is not in this PR. It stays as a local patch in
`build/head01-diagnostic.patch` (the `snap_timer_trace` patch set, off by default, and larger
thumbnails).

## Remaining hypotheses (none checked)

1. **Secondary head animation** (a spring bone, the cap or gaze tracking) that answers each
   footstep with a fast oscillation. It fits the bursts ≈40 frames apart and the torso having
   less. It would be game behaviour; whether the console shows it the same is unknown.
2. **A numerical difference from the recompilation** in that calculation (NEON root/reciprocal
   estimates, FMA contraction): a stiff spring close to instability would amplify a small
   difference. No evidence confirms it or excludes other possible port defects.
3. **Animation data** keyed at another cadence and sampled without interpolation. The
   equivalent 30 FPS comparison is still pending; the exploratory run is not used to lower this
   hypothesis's likelihood.

## What is needed to close

- A real-hardware reference of the same shot (60 Hz video from the console): it decides
  between original behaviour and a port defect.
- If it is a defect: locate the subsystem by comparing the shot with the NEON estimates forced
  to exact arithmetic, or by tracing the head bone's matrix.
- Keep the original 30/60 simulation and logic. The current intervention does not justify
  proposing a timer change as a fix.

## Tool and tests

`tools/measure_region_motion.py` (read-only) + `tests/test_region_motion.py` (10): recovery of
sub-pixel translations, changed content detected by the residual, uniform/alternating/random/
accelerating series, an uneven subject over a uniform background in synthetic frames, gaps
never bridged, a CLI that does not write into the frame folder. The review regressions keep
parity and segments when rejecting one step of an alternating series of 40, and do not compute
metrics by joining individually insufficient segments. The earlier defect falsely lowered the
alternation from 0.24 to 0.0072 when rejecting a step; fixed, it gives ≈0.238, the small
difference coming from the new mean step. The four 60 FPS measurements discarded no pairs:
they are not invalidated by this defect, but their conclusions keep the earlier limits.

```
python tools\measure_region_motion.py <AC_FLIGHT dump> --first 2775 --last 2858 --box cabeza:284,116,384,208 --box torso:276,232,380,320 --box fondo:40,80,200,220
```

## Limits

- One shot, one GPU (RTX 4060) and one measurement resolution.
- The irregularity includes the natural acceleration of walking; that is why it is always
  compared with the torso and background of the same shot, not with zero.
- The rectangles are fixed; pairs whose residual indicates changed content are discarded.
- Not measured on the RX 6900 XT with a current runtime.
