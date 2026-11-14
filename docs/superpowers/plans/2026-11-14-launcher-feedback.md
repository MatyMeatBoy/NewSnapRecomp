# Launcher startup and visible progress implementation plan

**Goal:** Launch a freshly rebuilt game without requiring shader recordings from
a session that has not happened yet; make preparation visible and give Home the
photographic presentation requested by the owner.

**Architecture:** Retain Tk/ttk and the existing portable launcher/kit. The owner
delegated implementation choices and asked to continue without confirmation.
Use ReKHCoM's cover/card/focus/primary-action patterns with Snap's cream/forest
green/amber identity. A framework rewrite adds dependencies without improving
the launch contract. Official promotional Snap imagery is used as requested,
with explicit provenance/copyright; no owner photos or extracted game data.

**Constraints:** Published 0.6 assets/tag stay immutable. Main remains the
integration checkout; changes use codex/launcher-feedback in a managed isolated
worktree. Original GameData/profile remain untouched. No changes to graphics,
simulation or saves. A patch delivery needs a new version/producer. No false
global percentage, fake elapsed-time estimate, or fabricated shader receipt.

- [x] Regression: fresh valid rebuilt runtime + pending shader marker + no
  libraries/recordings reaches native launch. Preserve pending marker; errors
  from a preparer that actually ran still stop launch with a visible reason.
- [x] Structured ProgressUpdate(stage,label,current,total), real Ninja/chunk
  counts propagated live through bounded log tails. Disk logs and cancellation
  tree cleanup remain intact. Unknown-duration phases are indeterminate.
- [x] Persistent Home preparation card: phase, real phase percentage/units when
  known, activity bar otherwise, elapsed time, separate cold-start note. UI
  callbacks stay on Tk thread; reset on new operation and stop on completion.
- [x] ReKHCoM-inspired cover/cards/clear CTA and official Snap promotional
  images. Aspect-preserving bounded redraw/cache; no decorative work during a
  game session. Include assets/provenance in freeze/fingerprints/public scope.
- [ ] Meaningful focused tests and independent review, then frozen GUI test:
  click actual Iniciar expedicion on an isolated rebuilt install without shader
  recordings and observe a real game window. Verify phase/percent UI.
- [ ] Integrate/push coherent blocks; archive completed board rows. Close new
  versioned immutable packages and verify delivery rather than replace 0.6.

Responsibilities: root owns launcher/home/maintenance UI/hero/assets integration;
progress worker owns progress.py, maintenance.py, build.py and telemetry tests;
asset worker owns assets/launcher only. GPU tests are serialized by root.

Integration supplement: PR4 mergedfe89dea and PR5 merged3ae0504. Real frozen
button acceptance found an additional independent defect: --boot is a bounded
probe exiting0 at the first NVN call, not interactive play. Commit34ab81d removes
it, preserving explicit profile/env/supervision; independent ABI/CLI review and
RED→GREEN command tests pass. The earlier frozen run is retained as failure
proof, not a successful interactive acceptance. Corrected freeze is built; real
window/frame acceptance is pending the serial GPU slot currently used by Claude.
Published0.6 assets remain unchanged. UI/telemetry completed rows are archived;
photo/fault/log work remains owned by Claude until its PR arrives.
