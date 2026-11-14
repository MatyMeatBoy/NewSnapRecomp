# Home and updates · 0.5 review

2026-11-13 · integrated work, 0.5 not published.

Home shows GameData loading/verification, version, profile and launch. Without data, starting
opens the selector and cancelling keeps Home; it no longer navigates to Updates. The constructor
does not create GameData or scan the album. The main actions stay visible at 125 % Windows
scaling.

The independent review found, and these were fixed:

- Closing a failed controller test could release the busy state of a later operation. The window
  now releases only its own acquisition, once, even on cleanup errors.
- Selecting GameData again replaced the custom profile with the default one. It now loads the
  selected folder's preference.
- Missing shader libraries could block the rebuild of an old runtime. The check happens after
  evaluating its rebuild.
- An expired display observation left the previous monitor's data visible. It is now removed when
  it expires or the game closes. A Vulkan error cannot validate fixed/variable presentation.

The regression tests reproduce the failures without opening the game or modifying original data.
Real Tk build and visual check in `build/launcher-audit-v05/verification.json` and
`after-home.jpg`.

Real network/transaction test in `build/v05-updater-manual-smoke-bb54b438/verification.json`:

- Automatic query: no stable available, without inventing one.
- Manual catalogue: published 0.4, 0.3 and 0.2 alphas with a verifiable launcher.
- Real 0.4 download from the repository, checksum and manifest verified.
- Install and reinstall of the same version in an isolated folder.
- 1102 files installed; GameData/profile/save sentinels and launcher preferences kept. No real
  owner data modified.

This is not a 0.5 delivery or a physical controller/AMD validation. The install test exercises
the updater's API; restarting the frozen executable will be checked again when packaging the
final candidate.

The development launcher was also frozen and its `--selftest-launcher` ended with code 0 using a
PATH without an installed Python. The source fingerprints match and the included controller PNG
keeps its original SHA. Evidence: `build/launcher-audit-v05/frozen-verification.json`. This
executable was not published; its identity stays at 0.4 while the 0.5 exit gate is open.

The controller's visual test, with synthetic input and no physical sensors, is in
`build/launcher-audit-v05/controller-switch-after.jpg`. Choosing between controllers,
disconnection and exclusive release of the busy state have regressions.
