# Graphics storage writes and asynchronous pipeline skipping

Status: independent review approved and integrated runtime compiled. No claim that this
alone explains the RX 6900 XT photograph bands or the tutorial softlock.

## Confirmed contract failure

The donor `runtime/vk_exec_draw.c` permits `prepare_draw` to return zero while a
graphics shader or pipeline builds asynchronously. Its skip decision consults
only whether colour/depth targets were recently rendered. A fragment or vertex
shader may also write storage buffers or storage images; target recency does not
make those writes optional. The pending return precedes resource binding and
SSBO write tracking, so neither the operation nor its write-back registration
occurs for the discarded draw.

Local private cache reflection contains a fragment shader beginning `e8aafa7b`
with a written SSBO at slot 0, address in constant buffer 0 at offset 328. This
shows that the application uses the affected resource class. It does not prove
which photograph/reticle operation the shader implements, or that a particular
GPU trace actually discarded it.

The compute-dispatch hypothesis was inspected and **discarded**: `op_dispatch`
and `op_dispatch_ind` request shaders with `pending=NULL`, then call synchronous
`vk_pipeline_compute`. They do not use the graphics pending-skip path.

## Bounded correction

`newsnap/graphics_effects_adapt.py` changes the draw preflight as follows:

- Await pending VS/PS translation before permitting a discard. Reflection only
  exists after translation; an unknown shader cannot be assumed free of writes.
- Classify actual reflected SSBO `flags & 1` and image-store `flags & 4` for
  both graphics stages. Read-only buffers and coherent-only images do not force
  a pipeline wait.
- For a draw with those effects, reuse the existing async pipeline promotion and
  condition wait in 30-second slices until `pending=0`. A pending entry already
  queued on a worker is covered. Expiring a wait slice cannot discard the draw.
- Preserve the donor's actual failure path: a null pipeline with `pending=0`
  reports creation failure rather than retrying forever.
- Retain asynchronous pipeline compilation and the existing discard policy for
  shaders whose reflection establishes no such storage effects.

Calling `vk_pipeline_graphics` alone would be insufficient: an already-building
entry returns without waiting when `wait_ms=0`, even through that synchronous
wrapper. The correction therefore uses the existing explicit wait contract.

No game validation, score, tutorial, save, colour or readback code changes.
Unknown shader translations can now stall the submitting thread; this is a
correctness tradeoff. Pipeline compilation remains asynchronous, and verified
pure draws can still be discarded while their pipelines build. A permanently
stuck driver/compiler remains a separate failure; required operations cannot
safely become optional because of a timeout.

## CPU evidence and limits

`tests/test_graphics_effects.py` extracts the actual donor `prepare_draw`
preflight through its pending and pipeline-failure checks, applies the adapter,
and compiles it with the real runtime/Vulkan type declarations. Vulkan command
recording and GPU execution are deliberately outside this fixture. Translation,
reflection and pipeline APIs are controlled stubs.

Before the change, the native regression exits with case 1: the ready fragment
shader with a written SSBO is discarded for a pending pipeline and recent
render target. A separate ignored diagnostic in
`build/review-pipeline-side-effects/` also records zero reflection queries and
zero waiting for this case, and a pending untranslated PS discarded without
awaiting it.

After the change, native cases cover VS/PS storage writes, image stores,
read-only resources preserving async discard, unknown VS/PS translations,
pending work spanning multiple wait slices, actual translation failure and
actual pipeline creation failure. Run:

```powershell
.venv/Scripts/python.exe -B -m unittest tests.test_graphics_effects -v
```

The native fixture used no GPU. The coordinator compiled the integrated runtime
`06a8d9df…`; its normal-mode 40-second warmup and measured run exited successfully
on RTX 4060. Comparative pacing is recorded separately in
`build/v05-normal-pacing-ab/REPORT.md`; it demonstrates no overall pacing gain.
Final photograph/reticle acceptance and AMD confirmation remain open. The earlier
540-second successful photo run used `f6d92250…`, before this graphics correction,
so it must not be mislabeled as acceptance of the final integrated executable.
