# Integration after 0.6: local verification

2026-11-14. PRs 6, 7, 8, 9 and 10 integrated into main. Not a new release: the published 0.6
assets/tag keep their bytes. The new public kit and physical AMD acceptance are still
pending.

## Changes and evidence

- Maintenance: runtime hashes and inventory, and the absence of the five cache paths, are
  checked before the commit. Recovery verifies what was restored before discarding the
  backup; copying without nested links/junctions. PR 7 and independent review. See
  runtime-replacement-verification.md.
- Photos: bounded, best-effort diagnostics, no PNG by default, at most 24 captures and
  64 MiB of pending payload. The default imports were kept; shadow stays opt-in. PR 6 with
  review fixes. This does not close the RX 6900 XT bands or faults.
- Translator: BFE/BFI/SHF defined, the original 12 patches preserved, 14 exact. 655,360
  bitfield cases and 262,080 funnel-shift cases pass against the real C# methods. NativeAOT
  compiled normally; 18 public synthetic shaders pass Vulkan 1.2 and match the managed
  translator byte for byte. Binary pin and ID checked before build, copy and packaging. PR 9
  and independent review; see xlate-semantics.md.
- Video: a single scrollable surface, no Basic/Advanced. All controls, preset, presentation,
  fullscreen, tooltips and callbacks kept. Hidden Tk check: 1 canvas, 0 inner notebooks,
  11 comboboxes with tooltips, Ultra/Custom preset and persistence correct. Independent AST
  review and PR 10's CI approved. No new interactive visual inspection.

Full Windows suite after integrating PR 9: 465 tests, 1 skip, 86.540 s, exit 0. It includes
native tests with the real headers/compiler, .NET 10 and the SPIR-V validator. PR 10 only
changes the widget layout; besides its review and Tk check, both of its full CI runs pass.

Private runtime built from PR 9 head b593c2d800026a4e1a05224d8dca8f2441ae1258, which already
includes PR 6/7/8: selftest and probe-loader pass. Its SHA256 is
`d66ad3f413cf8c043fc726ee1751a80cc71809d97e49c7977a92d8f9c4f19763`. Installing that real
candidate over an independent fixture confirms hashes, removal of the five caches and the
backup, keeping synthetic profile and recording sentinels. No original save/photo/import was
modified. Artifacts and receipts stay private in build/integration-07/. The build and probes
are CPU; they do not vouch for gameplay or AMD stability.

## New RX 6900 XT report with shadow

The owner's third log confirms shadow active despite the unknown-key SHADOW warning. It still
ends with another invalid GPU write; the last temporal mode recorded was FSR 4 Native AA.
That refutes that turning shadow on is enough to avoid this close on that route/runtime. It
does not check how the photos look: it has neither PR 6's diagnostics nor new images. Nor
does it show that FSR 4, its changes, SMAA or the import cause the fault. The translator it
records predates the new pin, and it does not identify this new private executable.

It also records that it does not recognise the SMAA point and keeps SMAA over the temporal
AA: a separate lead to investigate, not a confirmed cause of the close. The original log, an
identical copy, SHA and detailed analysis stay in build/; the private log is not uploaded.
FOTO-01 and QA-AMD-01 stay open.

The interactive launcher test was stopped with Escape. Window control was not resumed and no
GPU test ran concurrently with Claude.
