# OptiPort · verifiable proposals from NewSnapRecomp

**PROMOTED after review:** OptiPort commit `9673006504bf6712b320da70965bc3f65f2dd41a`
(2026-11-13). The seven reviewed references were published in the canonical repository and
installed in Codex; `SKILL.md` stays identical. The active checkout kept its branch/HEAD and its
index; Claude's copy, with unrelated local changes, was kept without being overwritten. Local
receipt: `build/optiport-lessons-candidate/promotion.json`. The review remarks about the scope of
the memory fixture and the round trip without an artifact were fixed before promoting.

**ISOLATED CANDIDATE, pending review of its diff.** Codex approved the seven topics and their
limits. The paragraphs were materialised in a copy under `build/optiport-lessons-candidate/`,
without installing or publishing. Neither the installed skill nor the canonical checkout was
edited. Keep this project's paths and tests here; promote only the generalisable contracts,
without the owner's private content or identifiers.

## Source and freshness

On 2026-11-13 the installed skill was read and `git fetch origin main` was run on the existing
clone of [MatyMeatBoy/OptiPort](https://github.com/MatyMeatBoy/OptiPort). `origin/HEAD` points to
`origin/main`, whose checked revision is `a948b71af2ead649b56f3cdc6e4190f77afda492`. The checkout
stayed at `384fb79c132de3a4612ffd46d3c0a25a58adc561`: no switch/reset, file changes, new branch or
new checkout. The fetch only updated remote references.

The installed copy was compared with `git show origin/main:<path>`, normalising CRLF/LF.
`SKILL.md` and these seven relevant modules matched:

- `references/graphics-memory.md`
- `references/runtime-adaptation.md`
- `references/reproduction-harnesses.md`
- `references/control-layouts.md`
- `references/profiling.md`
- `references/verified-lessons.md`
- `references/software-general.md`

There is no content difference to synchronise in those files. It is not claimed that every unused
module of an installation is up to date.

## Evidence base and limits

The [local matrix](GPU_MATRIX.md) keeps the devices, binaries, runs and results. The
colour/import/storage/input contracts have native negatives and positives; some also have an
NVIDIA observation. There is no physical AMD validation of the fixes or a shown cause for its
bands.

The passed normal 540 s photo controls use `f6d92250…` and `06a8d9df…`, each with its own
process, transfer and JPEG evidence. The second is not credited by inheritance from the first.
Neither a simultaneous subject rejection nor the periodic look of a screenshot shows which
consumer or copy failed. Do not turn 150 duplicated banks into 150 independent photos or runs.

The proposals below extend existing sections; do not duplicate the whole method in `SKILL.md`.
The recommended order is to review the graphics contracts, harness, input and provenance, and
finally add short links to the catalogue.

## 1. Digital colour transfer

**Target:** `references/graphics-memory.md`, after the «Close the chain of resources and
coordinates» table.

**Proposed paragraphs:**

> Separate the pixels' encoded values, the resource's base format, the view its producer used and
> the target's transfer. A resource with an sRGB base format may have been written through a
> UNORM alias; a copy/blit that consults the base format may decode bytes already prepared for
> the screen a second time. Fix the shown transfer boundary, without compensating with
> saturation, contrast or artistic gamma.
>
> The fix also depends on the target: an sRGB swapchain applies its own encoding and can turn a
> fix valid for UNORM into a double encode. Test the source/target classes actually supported,
> swizzle, mips, layers, usage, barriers and the lifetime of compatible views; keep float/HDR
> paths and formats whose contract is not established separate. Compare the digital bytes of the
> same frame, size and crop before attributing differences to the screen. An exact match on one
> GPU does not certify the others.

Primary reference added to the candidate:
[blit and sRGB conversion in Vulkan](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdBlitImage.html).

**What it decides:** it avoids modifying the original grade and avoids fixing only the UNORM case.
The sRGB-only fallback failed in the first proposal and was fixed after review. The format matrix
is CPU; the 1920×1080 digital equality is NVIDIA.

## 2. Imported host memory and coherence

**Target:** `references/graphics-memory.md`, in «Budget the memory actually used», after the
paragraph on requirements and ownership.

**Proposed paragraphs:**

> When an API returns compatible types or a selector has a fallback, check the properties of the
> type finally chosen: binding compatibility does not guarantee visibility/coherence for the
> host's access. Document who owns map/flush/invalidate, alignment, ranges and GPU completion.
> Memory imported through an external pointer does not automatically inherit the protocol of an
> allocation managed by the runtime.
>
> If direct access requires coherence the type does not offer, keep it only where the contract
> holds and pick managed storage with explicit flush, invalidate and synchronisation where it is
> missing. Trigger the fallback by the resource's real capability, not by vendor, and do not
> globally disable a valid path. Inject compatible non-coherent types, import failures and a
> coherent control. The fixture shows that policy; attributing a GPU's failure to it requires
> observing its real selection and transfers.

Primary reference added to the candidate:
[host pointer import in Vulkan](https://docs.vulkan.org/refpages/latest/refpages/source/VkImportMemoryHostPointerInfoEXT.html).

**What it decides:** the original selector returned a non-coherent candidate despite the property
request. The fixture checks flags, fallback by pool, tracking and a controlled invalidate call;
`shadow_sync_pool` is a counting stub and does not validate flush, GPU visibility or completion.
The existing flush/barrier/fence paths were audited in source. The fallback is not an «if AMD»
patch; NVIDIA keeps its coherent import and the physical fallback is still untested.

## 3. Functional effects of asynchronous draws

**Target:** `references/runtime-adaptation.md`, at the end of «Graphics preloading: four distinct
units», before «Transitive provenance…».

**Proposed paragraphs:**

> Before allowing graphics work to be skipped while a pipeline compiles, establish its observable
> effects. A draw can write SSBOs or storage images that capture, evaluation, simulation or export
> read; a recent render target does not make those writes optional. If reflection requires
> finishing a still-pending translation, do not classify the unknown stage as pure. Tell a real
> write from a read-only access and from coherence flags that do not imply a store.
>
> For mandatory operations, use the pipeline's real wait/publication contract, including jobs
> already queued and partial timeouts. A wrapper called synchronous can return pending if no wait
> is requested. Keep the terminal error and tell it apart from «still pending»; running out of a
> wait slice does not allow discarding the required operation. A cancellation or a controlled
> error must abort the operation or session according to its contract, with bounded cleanup; do
> not simulate partial success or keep consuming missing data. Keep async and its policies valid
> for work that really is optional. Audit compute dispatch separately: do not automatically carry
> a hypothesis about graphics draws over to it.

**What it decides:** it keeps effects without turning async off globally. The fixture fails before
and passes after on preflight/reflection/wait; the real use of the SSBO class does not yet
identify a specific photo or reticle from the report.

## 4. The observer can change execution

**Target:** `references/reproduction-harnesses.md`, after the negative/positive control; link
from «Deep view of hitches» in `profiling.md`.

**Proposed paragraphs:**

> Check whether screenshot, headless, trace or deterministic modes change the product's async,
> waits, timing, caches or captures. Record the effective policy from the code and the process
> that ran; a called initialisation does not prove its state query is still enabled. A correct
> diagnostic image does not validate a normal path that skips work because of a pending build.
> Separate visual equivalence, functional acceptance and performance measurement.
>
> For each control, restore an identified copy of the same initial state, including
> transactional/backup variants when the product can recover from them. Record hashes and
> generation; do not edit progress to force the checkpoint. For an image → buffer → encoder →
> thumbnail → selection/evaluation chain, observe each boundary and repeat the original consumer.
> A clean JPEG does not prove identification; a corrupt thumbnail and a simultaneous rejection do
> not prove causality. Count unique content, not copies of the bank.

**What it decides:** `--shot` changes the effective async policy in this runtime. The normal
controls restored the same backup and completed the flow without fake flags/scores. The JPEG
audit must not be used as a substitute for the original acceptance or a test of the final binary.

## 5. Input continuity and concurrent configuration

**Target:** `references/control-layouts.md`, a new subsection after «Device change and
presentation», before «Relevant validation».

**Proposed paragraphs:**

> A relative sample held per frame must also belong to the capture/device generation that
> produced it. Release and recapture between two polls can happen without a frame change: a
> boolean observed at the end does not reveal the discontinuity. Propagate an epoch from the
> capture's owner and invalidate earlier samples. Test rest, a known delta, the same frame, lost/
> regained focus and a stopped frame, keeping sensitivity and binding.
>
> Reset fused samples/orientation when the source changes or is lost, sensors are turned off or
> their read is interrupted, according to the contract. Check the setting before enabling hardware
> and revert partial enables; a mock test must not turn on physical sensors. Do not duplicate a
> live configuration that is already published safely with non-atomic statics: an old read can
> finish after the new one and leave an old value under a new version. Reproduce that interleaving
> with coordinated threads and check the later state, not only the value each reader returns.

**What it decides:** held samples, inherited fusion and a real race in the `on/seen` cache were
shown. The mechanism does not allow re-centring the HUD or enlarging the dead zone to hide
unmeasured physical drift. A controller view by physical positions must not promise the game's
effective binding either.

## 6. Producer provenance and safe reuse

**Target:** `references/runtime-adaptation.md`, «Transitive provenance of imports and generated
code», after the first paragraph; reference from «Memory and cache» in
`references/software-general.md`.

**Proposed paragraphs:**

> Also identify the environment and dependencies the producer actually runs, not those remembered
> by name. If a loader uses an external decompressor, its relevant identity must be part of the
> reusable recipe along with the interpreter, generator and flags. An extra module on disk can
> change the layout even if it is not in the manifest: reject unexpected inputs the generator
> consumes, or verify them and include them in the identity before the hit.
>
> A cache copy must be independent and verified after copying; checking only the source does not
> detect an altered copy. Limit entries and bytes, validate ownership and resolved paths, and
> reject symlinks/reparse points before recursive cleanup. Do not turn an unknown object into cache
> property to meet the budget. Corrupt/unavailable means a miss and fresh generation; do not reuse
> native executables/objects just because their generated sources passed. Verify originals on the
> warm path too.

**What it decides:** the review found LZ4 left out and extra ExeFS modules that changed the layout
without changing the key; both were fixed with regressions. The real run measured 86.820 s of
generation against 3.044 s of restore + 0.265 s of verification, with identical outputs. It is
preparation time; not an FPS measurement.

## 7. A measured summary without hiding adverse results

**Target:** `references/profiling.md`, at the end of the percentiles paragraph.

**Proposed paragraph:**

> Keep the complete route as the main result if it was the agreed window. A later segment can
> diagnose warm-up, but it does not replace a worse complete tail or turn mixed results into a
> global gain. Keep denominators, repetitions and concurrent activity; separate generation,
> compilation/prewarm, input time, game intervals, presentation and GPU busy. A build-cache
> improvement does not vouch for more FPS, and a zero wait counter does not identify all remaining
> spikes by exclusion.

**What it decides:** the complete A/B has an equivalent mean and a worse new p99; it is not
promoted as a global optimisation. One run per binary does not allow attributing a start-up
difference to a confirmed cause either.

## Proposed lesson catalogue

**Target:** `references/verified-lessons.md`, new rows with internal links to the modules above;
avoid including private paths/builds/photos.

| Trigger | Mechanism and useful check | Limit that must go with it |
| --- | --- | --- |
| SDR changes contrast when presented | Base source/view and target transfer do not match; class matrix and byte comparison of the same frame. | Does not validate monitor/HDR/another GPU. |
| Host import accepts non-coherent memory | A compatible selector relaxed required properties; check the real flags and a managed fallback by capability. | Do not attribute to a vendor without a trace of the resource. |
| A skipped draw loses functional data | Written storage makes the draw mandatory even if its colour can be discarded; reflection and a real pipeline wait. | A preflight fixture does not identify the report's draw. |
| A diagnostic capture passes and normal mode fails | The observer changes async or the initial state; a normal control and an equivalent backup. | Do not edit progress or confuse a visible photo with an accepted evaluation. |
| The camera keeps moving after recapture | A per-frame sample without capture identity; an epoch and source/fusion invalidation. | Physical drift and free aiming need a different measurement. |
| A live setting stays stale after a change | A redundant shared cache mixes an old value/new version; a test with two interleaved readers. | Review the configuration provider's safety before removing the cache. |
| The cache reuses an incomplete recipe | A dependency that runs, or an extra module outside the key; verify the real consumer, environment and inventory. | Generation savings do not measure gameplay or certify the SDK. |

## Review before promoting

The coordinator must check that each paragraph changes a decision already covered by evidence,
resolve duplicates with upstream and review the limits matrix. The later promotion needs a review
of its concrete diff; this draft neither synchronises nor publishes the skill. Do not carry
game-specific figures, thresholds, formats or policies over as universal defaults.

## Isolated application of the approved paragraphs

The copy keeps `baseline.json` of the eight files read at `a948b71`. `SKILL.md` and its
frontmatter are identical to upstream; the candidate changes only the seven existing references.
Context copies of Markdown and LICENSE from the same commit were added to validate the links; they
are not proposed changes.

Local review artifacts:

- [Unified diff](../../build/optiport-lessons-candidate/lessons.diff).
- [Files and hashes](../../build/optiport-lessons-candidate/changed-files.json).
- [Validation](../../build/optiport-lessons-candidate/validation.json).
- [Oracles and limits](../../build/optiport-lessons-candidate/VALIDATION.md).

Relevant CPU re-run: 40 colour/readback/storage/input/cache tests passed. RED→GREEN is tied to the
native oracles and controls already observed, including the eleven input baseline failures and the
graphics preflight that goes from exit 1 to exit 0. This vouches for the mechanisms behind the
text; no behavioural test of agents complying with the new wording is claimed. The independent
review of the candidate and its eventual installation/promotion stay with the coordinator. There
was no new GPU test or global edit.

The later review narrowed the import evidence: the shadow fixture does not vouch for GPU
flush/completion. The claim of a 256-code round trip was also removed from the matrix, since no
saved artifact backed it. The review adds the primary Khronos references and the
cancellation/error contract without partial success; it keeps the earlier CPU log, without
repeating tests for text changes.
