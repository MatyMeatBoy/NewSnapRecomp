# AMD / Vulkan — bounded investigation of Switch emulation

Date: 2026-11-14. Read-only; no GPU, ROM, keys, profiles or production changes. Primary sources
linked per mechanism; the GET queries and ancestry checks are kept locally in `build/`.
Performance claimed by authors is not our measurement. The RX 6900 XT is still pending.

## Useful result

1. **CPU priority: the CFG of the vendored Ryujinx translator.** An unconditional CAL call can
   lose its return block. The pattern is in our tree; it needs a fixture of the real decoder
   before changing it. It is independent of the reserved capture/fault-log work.
2. **Vulkan enumeration robustness:** our runtime ignores VkResult in both calls and does not
   retry VK_INCOMPLETE. It is a concrete initialisation risk reproducible with stubs, distinct
   from Eden's TOCTOU. It does not by itself explain a corruption that appears during play.
3. The experimental matrix, DCC and query-wait fixes do not justify a global AMD policy: several
   do not apply to RDNA2/Windows or to Snap's native architecture. No universal improvement is
   shown.

## Scope and families: do not count forks as independent engines

- [Official Eden mirror](https://github.com/eden-emulator/mirror): Yuzu lineage, Switch 1. The
  mirror keeps its forge's commits and Reviewed-on; I checked the ancestry of the four commits
  used against master.
- [Lichii nx2](https://github.com/zortos293/Lichii/tree/nx2),
  [Eglantine Community nx2](https://github.com/Eglantine-Community/Eglantine/tree/nx2): code that
  presents itself explicitly as **very experimental Switch 2**, derived from the Eden/Yuzu
  lineage; not a validation equivalent to hardware or a test of every game.
- [Aubepine](https://github.com/pattex67/Aubepine/releases/tag/aubepine-2026-11-10): an
  experimental fork of Lichii nx2 bcb37c49f7, release 837d899184, tested by its author on an
  RX 9070 XT/proprietary driver and short sessions. It includes Lichii PR573 although that PR is
  closed without an upstream merge. Do not confuse with **Eglantine PR573**, which is about
  ProCon motion and not AMD.
- [Ryubing](https://github.com/Ryubing/Issues) / Ryujinx: a different lineage, relevant because
  we use its translator. The git.ryujinx.app forge was not reachable from this session; I do not
  attribute merges to a third-party mirror. Its stutter and failure issues remain reports, not
  tested fixes. The documentation recommends Vulkan for AMD, but that does not show it fixes
  Snap.
- Citron/Neo: Switch 1. References to RDNA2 classification were found, but the PR URLs could not
  be retrieved; they do not count as confirmed fixes. Vita is not Switch and is out of scope. No
  emulators were downloaded.

## Eight fixes with a verifiable state

### 1. Eden: the same extension snapshot to decide and validate

[Commit ef4113aeaade8a7055fbedb386837554aead254f](https://github.com/eden-emulator/mirror/commit/ef4113aeaade8a7055fbedb386837554aead254f),
2026-06-15; integrated into master, Reviewed-on PR4072.
[Report 414](https://github.com/eden-emulator/Issue-Reports/issues/414): AMD Vega iGPU/Windows;
two independent enumerations could disagree when selecting optional extensions. The
implementation shares a single snapshot. Do not confuse with mirror PR7, closed **without a
merge**: the integrated fix has another commit.

**Snap:** `build/source/runtime/vk_device.c:52–60,123–132,248–252` and `vk_caps.c:93–96` do
count/fill without checking results. Eden's exact decide/validate circuit against two lists does
not exist. Separate candidate: a bounded helper handling ERROR/VK_INCOMPLETE and memory; a
fixture with count changes and a fill failure, no GPU. Acceptance: no over-read, no extension
enabled from partial data, an explicit failure once retries run out. No FPS benefit expected.

### 2. Eden: synchronisation and query-cycle repair after a regression

[Commit 3d19743d95f973ec0c322a0e8703387513ee0c66](https://github.com/eden-emulator/mirror/commit/3d19743d95f973ec0c322a0e8703387513ee0c66),
2026-06-02; integrated, PR3953. The change repairs stage masks and stops resetting queries
prematurely. The message credits the recovery of FFTactics/Windows AMD and Luigi's Mansion 3's
black pause; it also includes fixes for other platforms, so no figure can be attributed to a
single setting. It publishes no AMD model/driver or controlled test.

**Snap:** `vk_exec_xfer.c` manages a different ring of occlusion queries, resolved and reset by
completion after a fence; `vk_sync.c:149` gets timestamps without WAIT_BIT. The adapted
`vk_exec_xfer.c:216–217` also uses availability without WAIT_BIT for occlusion after a fence;
it is not a new improvement to import. Do not copy Eden's partial masks or change the reset
blindly. The external change reinforces the need to tie the reset to the last read; it does not
prove a local bug. The capture code belongs to MatyMeatBoy and was not touched.

### 3. Eden: repeated NonUniform annotations in shaders

[Commit 5ea24621cf8e75fe20ff35c4e41a05baf9497be8](https://github.com/eden-emulator/mirror/commit/5ea24621cf8e75fe20ff35c4e41a05baf9497be8),
2026-05-29; integrated, PR3997. It de-duplicates decorated IDs on dynamic texture accesses and
moves capabilities to setup; the author links it to LM3/Tomodachi AMD, without a model or a
detailed physical test. The commit also changes an upload barrier: do not attribute every
improvement to de-duplication.

**Snap:** we use Ryujinx's SPIR-V backend, not Yuzu's. `Instructions.cs:590–604` declares
capabilities once but applies NonUniform to objects; this does not show duplicates of the same
ID, since the objects can differ. Secondary CPU candidate: a synthetic shader with a shared
index, save the SPIR-V, count decorations per ID and run spirv-val. Do not remove necessary
decorations by analogy.

### 4. Lichii: gating cooperative matrix on AMD RDNA2

[PR657](https://github.com/zortos293/Lichii/pull/657), merged 2026-11-07,
**89440b29a90708c0fefc126b2bd8c7a64a996bdd**. It avoids HMMA on proprietary AMD drivers that
advertise cooperative_matrix without suitable hardware, using the mixed-signedness packed
integer-dot property as an RDNA3+ proxy. It answers a prebuild crash in amdvlk64.dll after
d549411. **The author says it was not tested physically on AMD and asks for an RDNA2 tester.**
Do not confuse an advertised extension with a useful model/shape or speed.

**Snap:** `newsnap/upscaler_adapt.py:17–44` enables the queried SDK extensions; it does not lower
the game's HMMA instructions to cooperative matrix. `snap_fsr_sdk.c` leaves selection/create to
the official provider. Do not transplant the RDNA3 proxy or alter Original mode. Useful to check
that provider errors leave an explicit fallback, not to declare FSR 4 solved on the 6900 XT.

### 5. Lichii: workgroup coherence when using the Vulkan memory model

[PR1698](https://github.com/zortos293/Lichii/pull/1698), merged 2026-11-14,
**ca063c0a801cb27471fce9d16240b32959499af2**. The cooperative path emitted shared
accesses/barriers with GLSL450 semantics despite selecting the Vulkan memory model. It adds
visibility/availability operands and NonPrivatePointer. CPU evidence: tests, module comparison,
spirv-val and offline RADV compilation for gfx1100/gfx1201; no physical game test with the fix.
Declared scope: NVIDIA RTX and AMD RDNA3/4 that take that lowering.

**Snap:** the vendored translator does not contain that new cooperative HMMA path. Supporting
cooperative_matrix for the SDK does not by itself introduce the same IR. Not applicable as a
direct patch; check the memory model of real shaders before proposing extra barriers.

### 6. Lichii: keeping SSBO pointer classification when re-translating an evicted pipeline

[PR1143](https://github.com/zortos293/Lichii/pull/1143), merged 2026-11-09,
**d2eaae4f3abca636b030b726f107bace06f61079**. A pipeline recreated with a temporarily null/lost
slot went on reading zeros for the rest of the session. It keeps the keys of known slots, a map
bounded at 8192 and limited diagnostics. CPU/syntax tests; physical evidence of the long case
pending. The author excludes a different case of an already saved disk record with a null slot.

**Snap:** `newsnap/adapt.py:121–143` already introduces a program-owned copy of control metadata
for deferred execution. That prevents metadata lifetime problems; it is not equivalent to the
classification fix. Lichii's EvictedPointerSlots machinery was not found; conceptual test
candidate: reuse exactly the shader/metadata after destroying the original program and vary the
binding. Do not declare the Lichii defect present here.

### 7. Lichii: performing a deferred clear before a copy/blit outside the render pass

[PR185](https://github.com/zortos293/Lichii/pull/185), merged 2026-11-06,
**f99fb8ab7b604f60d3b25cae3a8c39f1ae258c09**. A deferred clear was materialised after a copy and
erased the freshly copied data. The clear and the original order are kept; no draw/clear is
suppressed to hide a symptom. Evidence: suite 672/674, two earlier failures declared, **no
GPU/gameplay from the author**. Not AMD-exclusive.

**Snap:** `build/source/runtime/vk_exec.c:711–789` emits the clear when processing the command;
there is no Scheduler::deferred_clear. `barrier_to` orders passes/clear/copy/dispatch. No port
applicable; a good CPU oracle for future clear fusions: clear→copy→sample must keep the copy. Do
not introduce fusion before having it.

### 8. Historical Yuzu, preserved in Eden: linear pitch with a non-zero origin

[Fix 4c68fc6ea720e2639c57f97bc9228e5de69596ad](https://github.com/eden-emulator/mirror/commit/4c68fc6ea720e2639c57f97bc9228e5de69596ad),
2024-01-31; [merge 7e5d50c3806291f167ea29445cb931113c1b5de8](https://github.com/eden-emulator/mirror/commit/7e5d50c3806291f167ea29445cb931113c1b5de8),
2024-02-01, old PR12875. The loop confused y0 with the number of rows and used the absolute y for
compact output. It separates the local row from `(y+y0)*pitch`. It is a mathematical fix for all
GPUs, **not evidence of an AMD-specific failure**.

**Snap:** `nvn_tex.c:140–143` computes an explicit stride; `vk_exec_xfer.c` has different
region-copy paths. It does not use that SoftwareBlitEngine. Minimal transferable case: width 3,
height 2, non-zero x0/y0, padded pitch and sentinels; compare the round trip without touching
the padding. MatyMeatBoy owns the photo diagnostics: carry over only the oracle, do not attribute the
bands' causality by resemblance.

## Negative sources that prevent false fixes

- [Lichii PR573](https://github.com/zortos293/Lichii/pull/573) is **closed/unmerged**. Do not use
  its test merge_commit_sha as an integrated commit. Aubepine does declare carrying it: its
  official release shows it. The author's local measurements are on an RX 9070 XT; the change
  combines query availability, an unoptimised specific shader, batch 512 and parallel
  unswizzle. It admits that an earlier gain attributed to the texture cap was shader warm-up. No
  figure justifies a global batch 512 in Snap or a fabricated query read as exact.
- [Lichii PR950](https://github.com/zortos293/Lichii/pull/950), merged 2026-11-14
  **d58753224d78fb4038989475974ccad2538b0ade**: avoids DCC on pre-GFX10 RADV. Measured on RX 580/
  Mesa 26.2.5; Vega not tested, not RDNA2/Windows. Our 6900 XT is out of scope. Do not disable
  compression globally.
- Eden mirror PR5 and PR7 are closed **without a merge**; closing them is no proof of a fix.
  Issue 322, closed, about D24 in XC2, does not include a fix either: the author attributes it
  to the driver.

## Priority native candidate: CAL and return

Primary source:
[dwk001's comment of 2026-11-05](https://github.com/Lucas-blip-png/dkb-pc-recomp/issues/45#issuecomment-6646311080)
and [the owner's review](https://github.com/Lucas-blip-png/dkb-pc-recomp/issues/45#issuecomment-6648101483),
a search for `IsUnconditionalBranch` in the private primary record. The author dwk001 documents
a local fix, not a merged PR: exclude InstName.Cal from IsUnconditionalBranch. The author's
declared test is on an RTX 3070 Ti Laptop, driver 617.42; do not carry the visual result over to
Snap. The owner later withdrew a claim that it fixed the cutscene crash: the wall and the
crash's causality are separate pieces of evidence.

Here
`third_party/astral/tools/vendor/ryujinx/src/Ryujinx.Graphics.Shader/Decoders/Decoder.cs:146–157`
registers the callee, but adds the next block only if !IsUnconditionalBranch. The function at
501–504 returns IsUnconditional && Bra without a CAL exception. This pattern does match the
report; `InstTable.cs:55` confirms CAL with InstProps.Bra | InstProps.NoPred. A fixture of the
real decoder is missing to check scope and return in this revision.

Minimal experiment before a patch: a synthetic module with an unconditional call, a function that
returns, an observable instruction right after and a predicated control call. Run the real
decoder; check successors/predecessors and that the later instruction reaches the IR/SPIR-V.
Control: an unconditional BRA must still have no fall-through. Then test the output against an
interpreter/CPU and spirv-val. No GPU needed. If it is really red, a minimal translator change and
shader regeneration with a new identity; original+AMD GPU only after the CPU gate and
coordination. Do not change sensitivity, game logic or math precision to mask NaN.

## Identity and limits of this review

NewSnap tree read: 8ed155a400ec1475d75659ef50d62f899243944a; donor submodule
248e0b29f308ca84a2d2092019cc60e7fc50ae85. The existing adapted `build/source/runtime` was also
checked; it was not regenerated or compiled. The build/source line numbers describe that local
snapshot, not a guarantee for a future HEAD. No CPU benchmark or GPU test was run. There is no
new physical RX 6900 XT test, universal FPS gain or new photo fix. The eight fixes above are two
main lineages with experimental forks, not eight independent engines.
