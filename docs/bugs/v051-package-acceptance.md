# Verification of the 0.5.1-alpha artifacts

Producer: e77393f4808ce558787a7381454ccbfe2dab345d. API 3, eight capabilities, version
0.5.1-alpha. Later documentation/analysis-tool commits do not change that identity or
attribute these binaries to another HEAD.

| Closed artifact | Size | SHA256 |
|---|---:|---|
| NewSnapRecomp-0.5.1-alpha-windows-e77393f4.zip | 285947743 | b812819005fc0eb67fff1a292d3b8b93d08c076b110ae3c47a3c96a1b30ea3e8 |
| NewSnapBuildKit-0.5.1-alpha-e77393f4.zip | 253117747 | 88845de14818b53519f22859e8b9f9cf6c2b93da80ebef9d33125bfef818b965 |

Their ASCII checksums are included. Independent review: all 1,105 files of the Windows
manifest and 7,308 of the kit, exact inventory, hashes, roots, limits, exclusion of owner
data and no links. The nested kit ZIP and sidecar match the standalone ones; 109 common
fingerprints match between the freeze and the kit. The updater's parser accepts the package
and the inherited selector identifies a single Windows asset.

## Real consumers

- Stage and install with the closed ZIPs; repair of the same version and a check of every
  hash. Two synthetic sentinels kept.
- Acquisition and reuse of the bundled kit with network calls forbidden by the test.
  Rebuild with that kit's portable Python 3.14.9: 143 new chunks, 280 objects compiled, CPU/
  loader probes and activation correct. The later evaluation needs no second rebuild.
- Resulting runtime: SHA256
  7af250585180f2beac30053c1d463c4ae269232b8532ff96b6045c307ba20e70.
- Self-test of the installed launcher with the system PATH and no external Python. Frozen
  GUI reviewed: Home without selector, profiles in Game, presets and tooltips. A real export
  from an isolated copy with a synthetic log produces a valid ZIP, summary, text and JSON
  analysis; it does not modify the public staging.
- Two 20 s Vulkan sessions on an RTX 4060, FIFO and Mailbox: exit 0/boot passed,
  requested/effective mode and four observed categories; 32 trace lines per session, legacy
  INI intact. They are telemetry acceptance, not a performance A/B or a FreeSync/AMD test.
  No excessive-pool candidates in those two sessions; this does not rule out the hypothesis
  on the photo route.

Private evidence: build/v051-independent-artifacts.json,
build/v051-offline-package/verification.json, clean-path-launcher.json,
build/v051-frozen-ui-verification.json and build/v051-final-trace-smoke/verification.json.
ExeFS was copied to the synthetic installation; RomFS is a hardlink to an earlier
independent private copy, used read-only. The original newsnapGameData installation and the
published 0.4/0.5 assets are not changed.

387 tests before the identity change and 80 focused ones after it pass, one skipped for
symlink privileges. The producer e77393f's CI also passes.

## Limits and status

Missing: physical RX 6900 XT/FreeSync/controller acceptance, the reported
photos/thumbnails/colour and the intro head. PR #2's applet overlay is still in review over
ABI/result contracts and is not part of this delivery. PR #3's investigation is
tooling/documentation, not an animation fix. No game, derived executable, photos, saves or
keys are published.

## Later remote close

Published https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.5.1-alpha. The remote
tag resolves exactly to e77393f4, draft=false and prerelease=true; published with
Latest=false. The four remote assets match by size/digest, both sidecars included. The real
updater consumer downloaded the published Windows asset and validated the stage/manifest of
1,105 files. The manual catalogue picks 0.5.1-alpha; the automatic stable filter excludes it
(no stable available). Private evidence build/v051-published-smoke/verification.json.

PR #3 was later integrated into main together with segment/parity fixes and conclusions:
tooling, tests and documentation only; it does not change the closed producer e77393f4 and
no packages are rewritten. PR #2 stays open for the overlay.
