# Closing v0.5.0-alpha

[Published release](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.5.0-alpha).
Sources/tag: `e314751d10f4c51e575443d0d72c466dc94980b7`. Later closing documentation does not
change that producer or its artifacts. Limited delivery authorised: prerelease, not Latest stable;
physical AMD RX 6900 XT/controller/FreeSync acceptance still pending.

## Checks performed

- 299 Windows tests pass and CI green for the producer. Delta review: between dev1 and alpha only
  the version and Windows metadata texts change in the production inputs; API 3, capabilities and
  runtime logic intact.
- Public launcher: 1103 manifest files plus the manifest, hashes of every file and ZIP member,
  CRC, exclusions and 106 fingerprints verified independently. Original sprite intact; frozen
  self-test with a clean PATH correct. Public kit: 7297 manifest files plus the manifest, with the
  same identity, hashes/members/CRC and exclusions verified.
- A real rebuild from the final public kit, with independent physical copies of ExeFS/RomFS and
  the previous runtime: fresh generation, 279 objects and link correct. Both CPU probes pass, 14
  runtime hashes match and the later evaluation needs no further rebuild. Original inputs,
  profile, configuration and 0.4 runtime intact; the copy's sentinels kept.
- Rebuilt runtime SHA256: `e0dcac87a708d1f5f7c5a0cf880525784a8ae077f06c1b37c67f4166045b8db4`. It
  is private and not distributed on GitHub.
- That executable completed its own normal 540 s run on an RTX 4060, Original 100 %, exit 0/frame
  32083: two new Pikachu/Vivillon photos and two clean thumbnails. Confirmed banks and
  transactions match; four exact GPU pairs; tutorial evaluation and first expedition checked
  visually. The 75 protected profile/backup files stay intact. Async on, 122 pipeline skips and
  zero shader-translation skips. Not a performance benchmark.
- After publishing: real manual catalogue, download/checksum/stage from GitHub, install and repair
  of the same version after controlled damage to the launcher. The 1103 files, three sentinels
  and a start with a clean PATH are verified. The kit is downloaded/extracted/verified from the
  release and reused without network. This installation uses synthetic data; the game build is
  vouched for by the earlier independent run, not by those sentinels.
- Remote review: correct tag, non-draft/prerelease publication, four assets by
  name/size/digest and exact UTF-8 notes. The latest-stable endpoint stays without a stable: the
  alpha triggers no automatic notices. The 0.4 tag and its four assets intact.

## Immutable public artifacts

| Asset | SHA256 |
| --- | --- |
| `NewSnapRecomp-0.5.0-alpha-windows-e314751d.zip` | `0b96dc37d261eb18f5c37d903c6a101f2763cad1f05d32410c4d678cd15f8f5a` |
| `NewSnapBuildKit-0.5.0-alpha-e314751d.zip` | `abc02b465885af99987a4f3b2c3f3a1fbcbc065768aba44f361dd3092f73411f` |

Their two `.zip.sha256` sidecars complete the four assets. No GameData, keys, photos, profiles,
caches, generated game code or game-derived executables were uploaded.

## Local evidence and limits

Private receipts under `build/`: `v05-alpha-public-artifact-review.json`,
`v05-alpha-public-kit-rebuild/verification.json`,
`v05-alpha-public-kit-photo540/acceptance.json`, `v05-alpha-postpublish-smoke/verification.json`
and `v05-alpha-published-remote-review.json`.

The test does not verify AMD, every controller, FreeSync, a complete route, every scale or more
than 60 FPS. The resource-bridge A/B keeps its separate evidence and the remaining local spike of
107.692 ms; not all stutter is declared gone. Already saved damaged photos are not regenerated and
progress, subject evaluation or the tutorial are not modified. See the `v05-owner-validation.md`
protocol.
