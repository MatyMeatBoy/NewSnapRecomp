# RecompLauncher and next-release implementation plan

Goal: integrate RecompLauncher, investigate camera-turn stutters and stale transition imagery, publish the next verified candidate.
Architecture: reuse import, data verification, build-kit, runtime rebuild, profile lock and restart supervision. Add one opt-in adapter; normal launcher dispatch remains unchanged. Settings are opt-in command-line overrides validated by the existing settings module so external GameData folders work without a second configuration format.
Base: origin/main b67a36a (0.9.23); shared checkout and unrelated dirty work remain untouched.

## Constraints
- No game data, private keys, saves or derived executables enter public artifacts.
- Never skip progression/tutorial/photography rules; preserve original colour.
- Runtime improvements require a demonstrated cause and regression evidence; no AMD claim from NVIDIA tests.
- GPU tests serial; copy profiles; preserve published releases and tags.
- RecompLauncher SDK rules apply to its integration; separately requested renderer fixes remain separate commits.

## Tasks
- [ ] Adapter: tests first for untouched normal startup, folder/raw-dump preparation, explicit keys/update, failed setup, isolated profile, setting validation, Big Picture/controller hints, logging, locking and reserved exit75 supervision. Implement newsnap/recomplauncher.py and opt-in dispatch in tools/launcher_entry.py.
- [ ] Manifest/packaging: inputs for existing extracted folders or NSP/NSZ/XCI/XCZ plus required keys/update for encrypted containers; headless prepare/play; video/input settings through arguments, declared saves/logs. Validate against exact supplied JSON schema. Include manifest in frozen inputs, launcher folder and updater allowlist if needed. Badge uses catalog match. Never invent dump hashes; report missing NUP support and >64MB save-backup limit.
- [ ] Camera/transition diagnosis: reproduce 144 FPS first-day course with repeat fast rotation and deferred transition captures. Profile texture/shader/upload and simulation/present timing, inspect resource reuse. Cite related emulator/recomp implementations before changing runtime. Add targeted native regression for the confirmed cause; compare before/after on copies at matched conditions.
- [ ] Release: independent review, full suite, frozen launcher selftest, default startup, SDK manifest validation and public archive scan; bump next version, build closed kit/launcher/archive, publish only verified claims. Document physical acceptance gaps.

## Review focus
Malformed options cannot reach runtime; missing setup input cannot be marked ready; optional absent placeholders do not consume another argument; profile writes/backups never target imports; cache or target reuse must include resource identity; no frame or game-logic skips conceal a visual fault.
