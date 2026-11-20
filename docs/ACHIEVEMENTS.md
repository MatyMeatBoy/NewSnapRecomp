# Recomp Achievements integration status

The native game includes the official Recomp Achievements SDK pinned to
`faf094acdf1efb57d8db7c8187b4b47aa1501805`. Without `RL_SESSION`, the bridge
does not start a worker or initialize the SDK. With a session, one worker owns
all SDK/pipe calls; the game only updates coalesced ticks, classification flags
and a bounded event queue. Queue overflow marks subsequent reporting Casual.

The bridge reports successful save mounts as a conservative `save_loaded`
boundary and enabling runtime cheats as Casual. These messages do not claim
story progress. The native events-only connection uses console `""`, as the
SDK documents; it does not pretend the game is another console title.

## Verified event and inactive draft

`save_committed` means **only** that changed save data completed a commit in
the live game process. It is queued after the changed-data transaction has
published its durable ready directory, attempted the atomic swap, and passed
the final transaction-failure check. A committed directory waiting for a
Windows handle to release is valid committed data. No event is emitted from
startup recovery, an unchanged commit, a failed copy/rename, a simulated crash,
or the transaction failure path.

The draft [achievement list](../assets/achievements/newsnaprecomp.json) contains
one 5-point bonus, **Field Notes Recorded**. It describes only this action,
has no `progression` or `win` type, and makes no Beaten/Mastered claim.
The event can occur from an autosave or settings change; it does not prove a
photo was taken, a research level reached, or a course/story completed.

**External activation is blocked, not complete.** On 2026-11-20 the owner hub,
authenticated as the owner of `newsnaprecomp`, rejected the truthful draft:

- `console: "switch"` is outside its accepted console enumeration
  (`n64`, `snes`, `gb`, `gba`, `psx`, `ps2`, `xbox`, `x360`, `dc`, `ps3`).
- The service requires at least one achievement of type `win` (finishing the
  game), which this verified save-data action cannot honestly supply.

No list was stored and **Live for testers remained off**. Do not substitute a
different console or label saving as finishing the game to bypass validation.
Publishing requires service support for truthful Switch/events metadata and a
bonus-only set, or independently verified real completion hooks and acceptance
of their actual platform. The draft is retained for future activation.

## Validation and limits

`tests/test_achievements.py` stages and compiles the pinned SDK with the native
bridge. An isolated fake Windows pipe checks the actual JSON protocol and
executes the adapted save-transaction function against a virtual store. It
exercises changed-success, unchanged, copy failure, rename failure, simulated
crash, failed finalization and committed-waiting paths. Separate tests cover
standalone inert operation, worker-only SDK ownership, overflow classification,
coalesced frames and bounded shutdown during a blocked SDK operation.

These tests do not connect a real player session, inspect or modify owner
saves, unlock real achievements, or establish physical gameplay acceptance.
Public kwsch/NewSnap container structures and NewSnap's existing JPEG reader
do not establish story/research/Photodex field offsets; no such milestones are
inferred or reported.
