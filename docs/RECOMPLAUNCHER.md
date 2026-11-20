# RecompLauncher

The release includes `recomplauncher.json` beside `NewSnapLauncher.exe`.
Project page: https://recomplauncher.com/game/newsnaprecomp.
SDK reference: https://recomplauncher.com/sdk-files/recomplauncher-agent.md (read 2026-11-20).

## Setup and play

Easy Setup accepts an imported **2.0.1 GameData folder**, or your own base
NSP/NSZ/XCI/XCZ plus the **2.0.1 update** and your **prod.keys**. The update
is optional in the form because an imported folder needs neither update nor
keys; a base container requires both and reports an error if either is missing.
No game files or keys are distributed.

The opt-in `--recomplauncher-prepare` mode reuses the existing import, verification
and runtime rebuilding tools. It prints `progress` lines, exits nonzero on failure,
and writes `recomplauncher-ready.json` only on success. It uses the exact bundled
public build kit or a verified explicit developer kit; it never silently downloads
missing tools. Keep the whole release together. Container imports use
`GameData-import/updated`, as the normal installer does. Existing GameData folders
are selected in place. Updates rebuild from retained imported data without
asking again for original containers.

`--recomplauncher-play` waits for the game, holds its profile lock through exit75
restarts and propagates its final exit status. Big Picture defaults to fullscreen;
desktop defaults to windowed. Explicit choices win. Xbox/PlayStation hints apply
when the saved layout is Automatic. Background controller input is disabled in
this integration. No console window is opened.

Settings use validated `--set=KEY=VALUE` arguments for that session only; they do
not rewrite the runtime INI. RecompLauncher remembers its own choices. Invalid
combinations, such as FSR frame generation without temporal FSR, are rejected
rather than changed silently. Session and setup logs are under the installation's
`logs` folder. Without the new mode arguments, the normal NewSnap launcher,
installer, saved preferences and existing command-line modes remain unchanged.

## Saves and verification limits

The adapter uses the existing profile, including custom/external profiles.
The manifest deliberately omits `saves`: the SDK's default write tracking discovers
the files actually used, instead of incorrectly declaring a fixed portable path.
RecompLauncher excludes files over **64 MB**, so its backup/cloud feature cannot
promise to include Snap's large photo/save archives. Keep your own full backup.

External Looks are disabled: Snap preserves its original colour/post-processing
and external filters have not been validated. No `game.dumps` CRC32/size is
invented: the project's verified extracted-module/RomFS SHA-256 recipes are
different from authoritative whole-container CRC32 values.

## Standards still worth improving

- **NUP input (medium):** NSP/NSZ/XCI/XCZ work; NUP needs a validated reader/importer.
- **Linux/Steam Deck and macOS (large):** only Windows x64 is packaged/tested.
- **Unwritable-install fallback (medium):** portable data/preferences need writable
  locations; there is no complete per-user fallback for every file.
- **Complete save/cloud coverage (medium, with RecompLauncher):** its 64 MB limit
  excludes large archives. Do not change or split existing saves to bypass it.
- **Controller-only local setup (medium):** SDL3/remapping cover game input;
  traditional local file pickers still require desktop input. Easy Setup handles
  setup outside that UI.
- **Verified dump badges (small once authoritative data exists):** use only
  independently verified No-Intro/Redump sizes and CRC32 values.
- **Console-look defaults (small, product decision):** existing defaults use
  display-resolution scaling, SMAA and 16x filtering. The adapter preserves them.
- **Recomp Achievements (medium):** achievements, Beaten/Mastered games and
  leaderboards need integration with https://github.com/elripalda/RecompAchievements.

A free developer account at https://recomplauncher.com/dev (GitHub sign-in) lets
the maintainer claim the project, manage art/statistics/player reports and receive
the Verified developer badge once approved.


## 0.9.24 shadows and preparation

HD shadows is one setting for baked scenery maps and 4x realtime maps. In the
desktop launcher, missing maps prompt once with the conservative size/time estimate
(up to 6 GB / about 35 minutes); No remembers Off. Explicit On in RecompLauncher
consents to the initial public-tools download and local preparation before play.
Game setting with no previous consent uses original shadows for that headless
session. The offline build-kit guarantee covers recompilation, not the optional
Real-ESRGAN tool download. New generated DDS files use lossless filesystem
compression where supported. Existing imported inputs and photo/save files are
not compressed or changed by this feature.
