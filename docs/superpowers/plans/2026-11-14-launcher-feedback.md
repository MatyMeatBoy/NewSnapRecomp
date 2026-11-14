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

- [ ] Regression: fresh valid rebuilt runtime + pending shader marker + no
  libraries/recordings reaches native launch. Preserve pending marker; errors
  from a preparer that actually ran still stop launch with a visible reason.
- [ ] Structured ProgressUpdate(stage,label,current,total), real Ninja/chunk
  counts propagated live through bounded log tails. Disk logs and cancellation
  tree cleanup remain intact. Unknown-duration phases are indeterminate.
- [ ] Persistent Home preparation card: phase, real phase percentage/units when
  known, activity bar otherwise, elapsed time, separate cold-start note. UI
  callbacks stay on Tk thread; reset on new operation and stop on completion.
- [ ] ReKHCoM-inspired cover/cards/clear CTA and official Snap promotional
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
