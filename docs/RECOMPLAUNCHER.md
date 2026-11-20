# RecompLauncher

The release includes `recomplauncher.json` beside `NewSnapLauncher.exe`.
Project page: https://recomplauncher.com/game/newsnaprecomp.
SDK reference: https://recomplauncher.com/sdk-files/recomplauncher-agent.md (read 2026-11-20).

## Setup and play

Easy Setup accepts an imported **2.0.1 GameData folder**, or your own base
NSP/NSZ/XCI/XCZ plus the **2.0.1 update** and your **prod.keys**, or a decrypted
**NUP v1** containing the complete supported 2.0.1 content. NUP needs no keys. The update
is optional in the form because an imported folder needs neither update nor
keys; a base container requires both and reports an error if either is missing.
No game files or keys are distributed.

The opt-in `--recomplauncher-prepare` mode reuses the existing import, verification
and runtime rebuilding tools. It prints `progress` lines, exits nonzero on failure,
and writes `recomplauncher-ready.json` only on success. It uses the exact bundled
public build kit or a verified explicit developer kit; it never silently downloads
missing tools. Keep the whole release together. Container imports use
`GameData-import/updated`, as the normal installer does. Existing GameData folders
are selected in place when writable. A protected public installation relocates its
verified public files to a per-user LocalAppData directory. Read-only game data
is copied into a new writable folder with verified hashes; the GUI asks for a
destination and consent. Original files are preserved. Updates rebuild from retained imported data without
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
promise to include Snap's large photo/save archives.

The local launcher's **profile backup** option is independent of that service:
choose a folder managed by your own sync provider, then opt in. It streams the
whole committed save, photos and account identity into verified ZIP64 archives,
including files above 64 MB, retaining three successful copies. The provider
handles upload. Restore creates a new profile and never replaces an existing
one. Saves pending native recovery cause an explicit refusal rather than a stale
backup. This does not lift RecompLauncher's external cloud limit.

External Looks are disabled: Snap preserves its original colour/post-processing
and external filters have not been validated. No `game.dumps` CRC32/size is
invented: the project's verified extracted-module/RomFS SHA-256 recipes are
different from authoritative whole-container CRC32 values.

## 0.9.25 additions and remaining limits

- **NUP input:** bounded raw/Zstandard NUP v1 import validates the supported main
  NSO build ID, every ExeFS module and all 3,310 RomFS file hashes. The normalized
  runtime image has a separately pinned whole-image SHA-256. Corrupt, incomplete,
  ambiguous and unsupported inputs fail before publication. A private real-game
  roundtrip verifies the production importer; no game data enters the release.
- **Linux/Steam Deck and macOS (large):** only Windows x64 is packaged/tested.
- **Controller local setup:** the launcher includes its own pinned SDL runtime,
  focus navigation, modal file/folder pickers and confirmation dialogs before
  GameData is installed. Input is restricted to the foreground launcher and
  handed off before game startup. New arbitrary text, such as account tokens,
  still needs text input; physical-controller acceptance remains separate from
  automated navigation and virtual-device tests.
- **Verified dump badges (small once authoritative data exists):** use only
  independently verified No-Intro/Redump sizes and CRC32 values. Content hashes
  and NUP build-ID validation do not establish a whole-container CRC badge.
- **Original appearance:** a new optional preset selects 30 FPS, native resolution
  and filtering, original shadows/photos, neutral colour and no frame generation
  or menu interpolation. Existing defaults and saved settings remain unchanged;
  it applies only when explicitly selected. It does not claim pixel-identical
  console output.
- **Recomp Achievements:** the pinned official SDK runs on a bounded worker only
  with a launcher session. The verified save-commit event has an inactive bonus
  draft. Hosted activation is blocked: the owner hub rejects Switch metadata and
  requires a genuine game-completion achievement. No completion offsets,
  leaderboards or live unlocks are fabricated. See [status](ACHIEVEMENTS.md).

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
