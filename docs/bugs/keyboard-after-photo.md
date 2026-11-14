# KEYBOARD-CRASH · Windows keyboard and close after registering Pikachu

Status: **REVIEW** · Owner: MatyMeatBoy · 2026-11-13

## Result

The supplied log ends with `rt_dispatch sdk+0x273060`, consistent with the JPEG/longjmp defect
fixed since 0.3. Its patches and start-up lines suggest an earlier runtime, possibly 0.1.x;
there is no hash of that executable. It does not establish what opened the Windows keyboard or
exclude any other failure in another binary. The absence of `swkbd` only says that this log
records no call to that text entry.

The owner downloaded the GitHub ZIP and had to force the start after the 404. Identifying the
package and the executable separately is needed. AMD photos/colour still have to be repeated
with a recorded identity; this clue does not allow dismissing their symptoms or treating a
different version as verified.

## Evidence: the AMD session's log

Private copy: `build/user-reports/rx6900xt-0.5/logs/astralchain.log` (59 271 bytes, SHA-256
`bdbb38b7…d8680b`), provided by the owner. Not uploaded to Git. Output of
`tools/triage_game_log.py`:

| Item | Value in the log | Reading |
|---|---|---|
| Run folder | The owner's port folder (executable, `exefs`, `romfs` and `astralchain.ini` at the root) | Layout of the 0.1.x portable test, not `GameData` |
| Patch sets | `patches: snap_render on` | 0.2–0.4 also print `snap_supersample`; 0.5 adds `snap_random_range` |
| `vk: final SDR byte transfer` line | absent | Exists since 0.5's colour fix |
| Scaling | `dlaa: temporal anti-aliasing FSR 3 Native AA`, `FSR scales 1920x1080 to 2560x1440 (sharpness 80)` | Old configuration (`astralchain.ini`, 19 keys) active in that session |
| GPU / driver | AMD Radeon RX 6900 XT, proprietary driver 26.10.1 | — |
| Keyboard | no `swkbd:` line | The game did **not** open text entry in that session |
| End | `FATAL: rt_dispatch: no function at guest pc … (sdk+0x273060): not a function start (lr … sdk+0x273060)` after frame 26400 | Runtime fatal, exit 70 |
| Focus | loses focus 22:40:50–22:40:53, regains it 22:41:11, fatal right after | Matches leaving the game and coming back; no window close |

Checking the generation against local logs: those of 0.1.x
(`build/research/alpha-portable-boot.log`) print only `snap_render on`; those of 0.3 and 0.4
(`build/v03-jump-fixed`, `build/v04-production-neutral-fsr31`) add `snap_supersample`; those of
0.5 add `snap_random_range`. It is an inference from what the runtime prints at start-up, not a
hash of the executable.

## Cause of the close

`sdk+0x273060` is the instruction after a call to `setjmp` inside the SDK function that encodes
JPEG (it creates libjpeg version 80's compressor with a 0x240-byte structure and arms `setjmp`
for its errors). When libjpeg abandons encoding through `longjmp`, control returns to that
address, which is not a function start: a runtime without jump continuations cannot follow it
and ends with that fatal.

- **The same fatal reproduced locally with an old runtime:** `build/v03-tutorial-04/run.log`
  ends with the identical line (`sdk+0x273060`), on an RTX 4060. It is not a symptom seen only
  on AMD.
- **Fixed since 0.3** («live SDK jump continuations», `newsnap/jump_adapt.py`,
  `overlays/snap_jump.c`): the current generated code arms a native return point at that same
  call (`snap_jump_arm(…, 0x7002c73060)` in the generated C).
- **Verified on current runtimes:** the RTX tester's 540 s runs and this work's
  (`build/kbd01-applets-photo540`, exit 0) go through the Pikachu and Vivillon registration and
  save two photos and two thumbnails.

## The «Windows keyboard»

The log contains no call to `nn::swkbd::ShowKeyboard`. The touch keyboard appearing on a focus
change is a hypothesis; **it is not checked** what opened it, and activity that log does not
record cannot be excluded.

## Why an old runtime ran

Not determined here; it is LAUNCH-404 and AUTO-DATA work (RTX tester). What the log establishes: the
session started from the owner's port folder with the old portable layout. If the 0.5 launcher
could not download the kit (404) and was «forced to start», the executable already there was
launched. The launcher should refuse to start a runtime whose version is not the expected one,
or warn clearly; `tools/triage_game_log.py` already detects it after the fact.

## Keyboard audit (done before receiving the log)

- A single site calls `nn::swkbd::ShowKeyboard`: `main+0x69ac24`, the nickname in initial
  setup (1–12 UTF-16 units).
- The host's real window, previously used only with a forced answer, was run on RTX with
  `AC_SWKBD_TEST`:

| Run (`build/…`) | Variant | Result |
|---|---|---|
| `kbd01-window-ok` | Background window, OK | exit 0, nickname «Local», reaches the intro |
| `kbd01-window-cancel` | Cancel | exit 0; the game repeats the request (27 times) |
| `kbd01-fullscreen-ok` | Fullscreen with focus, OK | exit 0; loses and regains focus |
| `kbd01-applets-setup` | Runtime with `snap_applets.c`, OK | exit 0 |

  It does not cover a physical controller, the Windows touch keyboard or manual typing.

## Independent hardening: applets and return contracts

This overlay does not fix the reported JPEG close, whose continuation was handled separately
since 0.3. The new paths have not been seen during real play. The host policy logs dialogs
without UI and keeps the network and the console album unserved; it does not claim exact
equivalence with an offline console.

| Function | Reviewed host policy |
|---|---|
| `nn::err::ShowApplicationError` | Logs number and bounded texts; returns `void` |
| `nn::err::ShowError(ErrorResultVariant)` | Logs only the verified tag and payload (12 bytes); returns `void` |
| `nn::nifm::SubmitNetworkRequestAndWait`, `CancelNetworkRequest` | No real request; `void` |
| `nn::nifm::HandleNetworkRequestErrorResult` | **Exact boolean `false`: no retry**, not a `Result` |
| `GetCurrentPrimaryIpAddress`, `GetCurrentProxySetting` | Synthetic host failure, description not derived from a console |
| `nn::account::IsNetworkServiceAccountAvailable` | Successful query with a «not linked» byte; does not simulate linking |
| `nn::friends::Initialize`, `ShowUserDetailInfo` | No service; profile action closed per host policy |
| `nn::album::Initialize`, `Finalize`, `SaveScreenshot` | No service; saving returns a synthetic failure, never success |

The four account overrides `EnsureNetworkServiceAccountAvailable`, `GetNetworkServiceAccountId`,
`EnsureNetworkServiceAccountIdTokenCacheAsync` and `LoadNetworkServiceAccountIdTokenCache` were
removed: the exact offline or cancelled result could not be derived. Their paths keep the
original SDK and remain **without host support**; they may end in an unimplemented service or an
uninitialised client. They are not replaced by success and progress validation is not skipped.

The choice of description matters: several callers distinguish account error ranges. The
original PR's values 124/0 and 124/100 were not justified. Provenance, offsets, limits and
RED/GREEN evidence in [pr2-applet-contracts.md](pr2-applet-contracts.md).

## Tool: `tools/triage_game_log.py`

Read-only. From a session log (or the logs folder, picking the most recent) it reports:

- **How it ended:** `excepción-host` (71), `fatal-runtime` (70), `ventana-cerrada` (0),
  `reinicio-solicitado` (75), `fin-programado`, `sin-marca-final`.
- **Which runtime it was:** patch sets, inferred generation, run folder, and a warning if it is
  not from the 0.5 line.
- GPU and driver, last frame, keyboard calls, dialogs and services, focus, the fatal block with
  function and game frames, and the last relevant lines.
- It recognises the JPEG encoder fatal of pre-0.3 runtimes and unimplemented services, by name.

It replaces user-profile paths with `%USERPROFILE%` and copies no game data.

```
python tools\triage_game_log.py "<logs folder>"
```

Where the logs are: with the launcher, `GameData\logs\launcher-game-<session>-NNN.log`; with a
direct or forced start, `logs\astralchain.log` next to the executable, and the four previous
sessions in `totk.1.log` … `totk.4.log`.

## Tests

```
python -X utf8 -m unittest tests.test_snap_applets tests.test_game_log_triage
```

- `tests/test_snap_applets.py` (4): the exact list of 13 symbols; no other source replaces
  them; no file writes or patches; a native fixture with clang `-Wall -Wextra -Werror` that runs
  each answer and checks the exact boolean, the callers' bit/value gates and the read limited to
  the variant's 12 bytes.
- `tests/test_game_log_triage.py` (13): the six verdicts, a named service, the runtime
  generation, the known JPEG fatal, path redaction, picking the most recent log (launcher and
  direct start), read-only, large logs.
- The original PR's historical suite in the worktree: 316 tests; the only 2 failing are unrelated
  to the change and specific to the worktree (`toolchain/` missing for an SDL fixture and an SVG
  extracted with CRLF line endings).
- Historical evidence from the original PR, before these ABI fixes (not acceptance of the
  revised overlay): a runtime with the overlay (`build/kbd01-build`, 280 objects, selftest and
  load probe correct): initial setup with the nickname window (`kbd01-applets-setup`, exit 0)
  and the 540 s photo route (`kbd01-applets-photo540`, exit 0, 32 332 frames, 0 validation
  errors, 2 new 1080×720 photos and 2 new 240×200 thumbnails, `bytes-limpios` audit with
  complete evidence, original profile intact). RTX 4060 only.

## Limits

- The AMD runtime's generation is inferred from its start-up lines; there is no hash or version
  of that machine's executable.
- 0.5 has not been run on the RX 6900 XT: photos, colour and this step are still unvalidated
  there with the right runtime.
- The origin of the Windows keyboard is not identified.

## What is needed to close

1. The AMD machine actually running 0.5 (LAUNCH-404 / AUTO-DATA) and repeating selection →
   evaluation → registration.
2. From that session, the output of `tools\triage_game_log.py`: it must say «generation 0.5 or
   later».
3. the RTX tester's review of the overlay and the tool.
