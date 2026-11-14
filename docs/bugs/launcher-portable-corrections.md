# Portable fixes after 0.5 alpha

Integrated into main: `47be383`. Does not modify the published 0.5 alpha assets. The ZIP the
owner tested is still the published one, without these fixes. The next delivery needs a freeze,
the exact kit and validation of the complete package on an installation without GitHub
credentials.

## Cause and changes

Rebuilding from the launcher downloaded the kit when it needed a compatible runtime. The private
repository answers 404 without access; the authenticated development PC did not cover that case.
The Windows package now requires and includes the exact public kit (version, full revision, API,
capabilities, donor, inventory and hashes). The client verifies the size/hash pinned in MANIFEST
before extracting the local kit into its own cache; with a valid bundle it does not query GitHub.
Without a bundle it keeps the verified download and explains the 404. No credentials are included
and an incompatible runtime is never forced to run.

Detection prefers complete imports over old missing selections and folders with only a marker. It
checks only known direct, nested and sibling layouts; it does not walk the disk or change the
saved preference. A missing installation does not adopt its parent's data. Presence does not
replace verification of the original data.

The consoles of redirected Python/Ninja producers and native helpers are hidden. Re-exec/restart
keep an explicit console for CLI use and stay console-less when the launcher has none. Pipes,
output, return codes, suspension, Job and cancellation are kept. Other programs' CMD windows are
not closed.

## Verification and limits

72 targeted tests pass: local/remote acquisition, rejection of a broken or unpinned bundle,
cancellation, 404, public packaging, discovery, maintenance, native processes and the joint
application of overlays. Private evidence: `build/launcher-portable-final.log`. Independent review
of the bundle without new blockers. Not a physical confirmation on the RX 6900 XT or of the new
EXE.

Pre-existing P2 pending: a corrupt local cache is rejected before trying the valid bundle.
Recovery must isolate only that cache generation and verify another extraction; never delete the
user's imports or runtime.
