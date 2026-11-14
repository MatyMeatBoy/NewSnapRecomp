# NewSnapRecomp coordination

The integration branch is `main`. Work arrives as themed pull requests (Claude, Codex or
others); do not recreate per-version branches. Prepare PRs in their own branch or worktree
without switching the shared checkout or carrying other authors' changes.

Read **[docs/PENDIENTES.md](docs/PENDIENTES.md)** before editing (the "read first" section is
the current state). To take a free task, mark it IN PROGRESS with owner and reserved files.
Respect other owners' reservations and coordinate shared integration points
(`launcher.py`, `adapt.py`, `build.py`, `maintenance.py`, `version.py`, packaging).

Published releases and tags are immutable. Prereleases are "tester" builds: never present
unverified AMD/NVIDIA/controller/FreeSync cases as solved. Do not change game logic to skip
validation, progress or tutorials. Keep Snap's original colour and post-processing. Keep
evidence per GPU: one GPU never validates another (owner: RX 6900 XT; Codex: RTX 4060).

Never commit the owner's saves, photos, imports, keys, game data or recompiled executables.
Test on copies; serialize GPU tests; compare performance on the same route, resolution and
cache state. Before implementing a fix, check how other recomps and emulators solved it
(Astral Chain, TotK, Weeping of the Empire, Witch Time, Lichii, yuzu/Ryujinx) and cite it.

Each author commits only their reserved files on their PR branch. To close a task, give
cause, changes, tests run and limits; ask for review before marking it DONE.
