# Private candidate 0.5.0-dev.1

Producer: `555d6258d982b0fd5ab3432bc1f1d9f7c6224c1c`.
Executable SHA256: `76f08005b1ffca903e5cab8fdaa5b2f46fe48c818499cd8cc2e51a7885bb527a`.
There is no 0.5 tag or release. The 0.4 release stays immutable.

## Verification

- Windows suite: 299 tests pass. After adjusting the test directory in a clean checkout, ten
  RNG tests pass; Linux CI green for the final producer. Private or Windows-only cases do not
  become physical Linux/AMD acceptance from that result.
- Native build: generation and 279 objects verified, link correct; clean sources and
  identity recorded before/after. Frozen launcher: 1103 manifest files and ZIP verified,
  fingerprints equal to the sources, original sprite intact and a test start with a minimal
  PATH correct.
- Install and repair over the same version: 1104 files replaced in each operation on an
  isolated installation; three data, configuration and preference sentinels kept. The
  repaired launcher starts OK.
- Private close: 15 runtime files including a new marker; `--selftest` and `--probe-loader`
  probes correct. Launcher, kit and runtime identities match. The isolated evaluation needs
  no rebuild; acquisition of the exact local kit with verified inventory and zero network
  requests.

## Photos from the final executable

Normal 540 s run on an RTX 4060, without `--shot`, Original and 100 % scale;
`AC_SNAP_RANDOM_RANGE=1`. Exit 0, final frame 32302. The profile is copied from an initial
backup without photos; game progress or logic is never edited.

Two new photos (Pikachu and Vivillon) of 1080×720 and two 240×200 thumbnails, without black
rows and checked visually. The confirmed banks and transaction match. Four GPU source/buffer
pairs are byte-identical; the JPEG difference is the expected compression, not a
byte-identical JPEG comparison.

The later evaluation/tutorial and the first expedition were observed. The 75 protected
profile/backup files stayed intact. There were 103 graphics pipeline skips and zero shader
translation skips; global async was not turned off. Packaging, repair and CPU probes ran
concurrently: this run does not measure performance.

The focus samples `cpu-read-01-f13180-source.png` and `cpu-read-02-f13777-source.png` show
the reticle/name legible at 1920×1080, without the reported bands. They are two local visual
controls; they do not certify all motion/zoom or the physical AMD path.

Private evidence: `build/v05-rng-positive-control-normal540/acceptance.json`,
`photo-evidence.json`, `profile-guard.json`, screenshots and banks. The separate
performance A/B is documented in `cpu-asset-workers.md` and `GPU_MATRIX.md`.

## Pending physical gate

The reports have not been validated on the RX 6900 XT, its controller, monitor or FreeSync.
The reticle in motion/zoom, the camera at rest/reconnection, colour and photos are checked
with the `v05-owner-validation.md` protocol. An isolated local spike of 107.692 ms remains in
the A/B; not all stutter is declared gone.

The private packages contain no owner imports, keys or profiles. The rebuilt runtime does
contain game-derived code: do not upload it to GitHub. The kit and the launcher keep their
separate public inventories. Use a complete copy of GameData and also check the profile
path in Home before playing.

Local test package: `build/NewSnapValidation-0.5.0-dev.1-555d6258-private.zip`.
SHA256 `779fc5a90d2551e4c62bcabc30ed9f5dd534f50304917c493e290d23187f07bf`. It contains 8420
files: launcher 1104, private runtime 15, kit 7298 and instructions 3. Inventories,
independent copies, triple identity, sizes and the ZIP's CRC verified. The start command only
selects the local kit and opens the launcher; the instructions require copying data/profile
and checking their paths before launching.
