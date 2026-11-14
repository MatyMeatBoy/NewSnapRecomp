# Acceptance of the 0.6.0-alpha package

Final closed producer: `82e01064d673a0489304913575ec646da148887c`. The earlier private
candidate `8f4510ba4ab4613fe7597fd884f23245300931c5` was not published: the review found
bytecode with a local path and three unpinned SDK headers unrelated to the runtime. It was
kept intact and the producer was fixed. The historical sections below document that candidate
and its consumers; the final identity is detailed separately. Version `0.6.0-alpha`, API 3 and
nine capabilities, including `ieee-crc-slicing8`. A later commit of this document does not
change the artifacts' identity or attribute the binaries to another HEAD.

## Earlier private candidate, kept and immutable

| File | Bytes | SHA256 recorded in its sidecar |
|---|---:|---|
| NewSnapRecomp-0.6.0-alpha-windows-8f4510ba.zip | 285965741 | 3e6b1d94531f6c5b7bce5f77aa14dbbb388dfc7cabbf0dc4a05dee0b73bdb8da |
| NewSnapBuildKit-0.6.0-alpha-8f4510ba.zip | 253134472 | 84c2a1579cf871f518739bcee7c76ef557bc196995912c8288f849565892f40b |

Both have their ASCII `<name>.zip.sha256` file, of 114 and 108 bytes respectively. The
Windows package contains the kit and its sidecar under `build-kits/`, pinned by the outer
manifest. These bytes are closed; the complete independent check of inventories, hashes,
limits and nested pins is recorded as pending below, without anticipating its result.

## Source and real consumers verified

The source suite records 411 cases, result OK and one skip for symlink permissions
(`build/v06-full-tests.log`, 73.362 s). The producer's CI also passes. This is not physical
acceptance on every GPU or of the game's routes.

The isolated installation uses the closed ZIPs and the real updater consumer: stage,
install, repair of the same version and a check of the 1,105 manifest files. The bundled kit
is acquired and reused with network calls forbidden by the test. The two synthetic sentinels
are kept: a save and a legacy INI configuration. The public files stay unchanged.

The rebuild ran with the kit's portable Python 3.14.9, without reusing earlier generation:
106 main and 37 SDK chunks, 143/143 emitted. The log records 283 verified objects, zero
recompilations from hash mismatches and a complete link; compile 115.3 s and link 0.8 s. The
recorded generation takes 28.559 s. The worker runs `--selftest` and `--probe-loader` before
activating the candidate; the whole flow finished and the later evaluation returns
`needs_rebuild: false`.

SHA256 of the rebuilt and activated runtime:
`018d87d6485fcdd6261a099af2a9fc6bd2272b165e63a13afefd8640a9a58a7f`. Its marker matches the
launcher's version, revision, API and nine capabilities. The derived executable stays in the
private acceptance copy, not in the public assets.

Main private evidence: `build/v06-offline-package/verification.json`,
`build/v06-offline-package.log` and
`build/v06-offline-package/installed/GameData/logs/runtime-rebuild.log`. ExeFS was copied;
RomFS is a hardlink to an earlier independent private copy and was used read-only. The
original 0.4 installation and the published 0.4, 0.5 or 0.5.1 assets are not modified.

## Frozen launcher and diagnostic export

Independent check of the real installed launcher: `NewSnapLauncher.exe --selftest-launcher`,
with `PATH=C:\Windows\System32` and no `PYTHON*` variables. Exit 0 in 1.703 s; the empty log is
the expected behaviour of the windowed self-test, which builds and destroys a withdrawn Tk
window in a temporary project. No processes of the installed executable remained before or
after. No normal game session or GPU was started.

The launcher's hash matches its manifest pin:
`dea4938760a72def32b66678da880251b46bd06dd4364d31f665cee6d4f9f25b`. Private receipts:
`build/v06-frozen-selftest.json` and `build/v06-frozen-selftest.log`.

The real export test from the frozen GUI uses an isolated copy with 600 unrelated entries
before the recent log. The ZIP includes that log, a summary and a JSON analysis; the fixture's
paths and secrets are redacted and the source files are kept. The receipt
`build/v06-frozen-ui-verification.json` declares `frozen_ui_export_pass: true` and the
diagnostic ZIP has SHA256 `15d23bcfe6d5a5ce918f63742ee52a1ced488eb3ef9ffb5cfb3ff1d963db12b9`.
That synthetic ZIP stays private.

## Closing the native candidate's checks

- **Earlier audit:** found the two anomalies described at the start;
  `build/v06-independent-artifacts.json` keeps that result and those ZIPs were not published.
  They were not overwritten when fixed.
- **540 s functional:** completed with the native SHA above, RTX 4060, exit 0/boot passed/no
  fatal/33 screenshots. The Pikachu and Vivillon evaluation and the first expedition were
  observed, without changing the tutorial's logic or progress. The saved audit checks two
  1080×720 photos and two 240×200 thumbnails: valid checksum, structure and decoding, no
  bands/blocks detected. The protected original files keep their hashes. Private evidence
  `build/v06-final-photo540/{run.json,photo-audit.json}`.
- **CRC A/B:** two warm-ups and two reversed 20 s pairs, same SHA, equal profiles/route,
  restored caches, Original 100 %, FIFO 1920×1080, AC1/saver0. An independent review
  reproduces the metrics: pooled p99 39.903→32.037 ms, median 16.651→16.652 ms. The maximum
  worsens in the second pair and the phase after frame 600 does not improve uniformly. It does
  not prove perfect pacing or more FPS. `build/v06-crc-ab-fullscreen/comparison.json`,
  valid-complete. The first run with a 1920×1055 window was excluded and kept, without mixing
  its measurements.

## Final fixed artifacts, producer 82e01064

| File | Bytes | SHA256 |
|---|---:|---|
| NewSnapRecomp-0.6.0-alpha-windows-82e01064.zip | 285940050 | 6ff10edccd90b0cbb4e279e348afe30b9b174545873dff3dde2e9e1228c23e6b |
| NewSnapBuildKit-0.6.0-alpha-82e01064.zip | 253111153 | 55a94faaa918e1763fa63acf1461e539fcf691f300963d34034c8c1cf564d5f5 |

Independent audit **PASS with no findings**: `build/v06-r1-independent-artifacts.json`.
Inventories of 1105/7310 files, sidecars, the nested kit and 114 common fingerprints match.
The 788 source files agree with the pinned producer/donor (14 CRLF-only differences); ten
vendor files and two canonical receipts verified. No Python bytecode, SDK extras or unknown
sources.

The 7309 files common to both kits are identical. Only the pyc and the three unused headers
were removed, and a canonical FSR receipt was added. Recipes, toolchain, required
headers/DLLs and the native shader are identical. The final launcher SHA
`c9a627c21fbd61ed3a770511d9794c67bede9412b4cc8c0c8dcf0414ce59cb2a` is identical to the tested
one except for COFF/debug timestamps and the PE checksum, shown by comparing both ZIPs and
normalising only those typed fields. Its PYZ and all of the executable's code stay identical;
private evidence `build/v06-r1-frozen-equivalence.json` and an independent review.

The final 82e01064 suite passes 416 tests in 83.627 s (one symlink skip), and its CI passes.
Install/repair and offline acquisition of the final ZIP pass: 1105 hashes, two sentinels and
all public files kept. The kit generates 143 chunks from scratch with Python 3.14.9, compiles
283 objects in 112.1 s and links in 0.7 s; probes/activation pass and the evaluation does not
ask for a rebuild. Private receipt `build/v06-r1-offline-package/verification.json`.

Final derived runtime, producer 82e01064:
`24c014a53d76ad86c7002f697aeb0d4f717d6535b0113a9319a65dc1dc59cec9`. It differs from the
8f4510b binary: it is not presented as a bit-for-bit identity. The common native inputs are
identical according to the independent inventory; the long test and the A/B explicitly keep
the earlier producer and SHA. An extra real 60 s session with the final SHA loads a copy of the
post-tutorial profile and continues the dialogue: exit 0/boot passed/no fatal, five screenshots
and protected originals intact. It is not another A/B or a complete photo route;
`build/v06-r1-final-expedition60/run.json`.

The installed final launcher repeats the self-test with PATH System32 only and no PYTHON
variables: exit 0 in 0.828 s, no own processes left; `build/v06-r1-frozen-selftest.json`. The
launcher's typed equivalence allows keeping the earlier GUI test of the exporter; a second
export that was not run is not attributed to the final binary.

Bounded independent static review of the final runtime: `build/v06-r1-native-review.json`.
Section RVAs equal; the 59 differing code bytes are RIP displacements in 59 LEAs: 58 point to
equal strings and one relocates a table with the same six targets. Data/overlay sections and
compared regions match; local fallback paths and debug metadata differ. Not every DWARF field
was decoded, and global equivalence of the argument-less fallback is not claimed. The tests
and the launcher pass explicit paths; the final run remains separate evidence.

## Remote close

Published https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.6.0-alpha. Remote tag
82e01064 exact, draft=false/prerelease=true/Latest=false. The four remote assets match the
closed inventory by size/digest. The real updater downloads the published Windows ZIP and
validates its stage of 1105 files. The manual catalogue accepts 0.6.0-alpha and the stable
filter excludes it, with no automatic alpha notices; no stable is published. Private receipt
`build/v06-published-smoke/verification.json`. Later documentation commits do not change
producer 82e01064 or those assets' bytes.

The physical RX 6900 XT, FreeSync and controller tests and the reported AMD symptoms keep
their own limits. Adding portable CRC and log export does not prove a fix for photos, colour
or head vibration. No game, derived executables, photos, saves or keys are published.
