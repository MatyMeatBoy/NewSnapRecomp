# PR #2: applet contract fixes

Review for the 0.6 integration from `732671b`. It does not validate AMD or change the JPEG
continuation, fixed separately since 0.3. Nor does it identify the origin of the Windows
keyboard. Progress, photos and saves were not touched.

## Provenance and the network boolean

Local inspection of the private Snap 2.0.1 inputs, without copying them to Git:

- Main build ID `ddb900ff04a912ed42430508389853cfaf1accce`.
- SDK build ID `0617f669301f922a811886048dd7b41a249cc1b3`, SHA-256
  `86cbb6d9f9e2d83dca0fed1f2081ff3adb88ad5b663b6d05b551927769505574`.

`nn::nifm::HandleNetworkRequestErrorResult` at SDK `+0x32e950` normalises the return to bit 0
on both exits: it is a **bool**, not a `Result`. The member at `+0x330170` returns false on
intermediate failures; at the end it returns true only if its internal result is zero or
`0x17c6e`. The offline host policy now returns exactly `false`, without asking for a retry.

The three main callers `+0x537a00`, `+0x537a2c`, `+0x53b7ec` use PLT `+0xa383a0`, GOT
`+0xcc7278`, and test bit 0 in the next instruction. The old value 622 had that bit clear,
so it accidentally matched these callers' false branch; it was not shown to change that
branch in this dump. It was, however, an invalid boolean, and a non-zero test would give a
contradictory answer. The fixture requires exactly zero and agreement between both gates;
it fails against the original C and passes once fixed.

## Account: do not substitute unknown descriptions

The SDK wrappers `+0x15550`, `+0x15580`, `+0x15650` delegate to account services or
clients. Their code alone does not give the exact result of a console without a linked
account. No alternative description is invented.

The callers **do distinguish descriptions**, besides module/success:

- Main `+0x538cac..0x538cc4` and `+0x538d50..0x538d68` classify module 124, descriptions
  200–269, as state 3.
- `+0x538e34..0x538e5c` also distinguishes 430–499.
- `+0x1f2b10..0x1f2b28` uses 430–499 for a path with bounded retries.

The old 124/100 fell outside those ranges and reached the common handler `+0x5443d0`; that
path was not shown to be an equivalent safe cancellation. Only the four speculative
ensure/id/token overrides were removed. The original SDK still serves those calls,
**without guaranteed host support**: they can fail on unimplemented services or an
uninitialised client.

`IsNetworkServiceAccountAvailable` is kept: a successful query of the local state with a
single false byte; it creates no account, ID, token or async context. The fixture checks
that the adjacent byte is untouched and the exact list of 13 registrations, preventing the
four removed overrides from coming back by accident.

## Other limits reviewed

`ApplicationErrorArg` uses a u32 number at +8 and texts at +0x14/+0x814, checked in the SDK
constructors `+0x15c650/+0x15c670`. The copies for the log are bounded.
`ErrorResultVariant` checks a 4-byte tag and a payload of at most 8 at +4 (constructors
`+0x15ca00/+0x15ca20`): the log reads only those 12 bytes. A fixture with exactly 12
readable bytes fails before that fix and passes after.

The synthetic `nifm` 110/1 and `album` 206/1 failures are explicit host policy; their console
descriptions are not derived. The reviewed callers of IP address `main+0x179df0`, proxy
`+0x2475c0` and save capture `+0x7d5844` take failure branches on non-zero results. The
fixture keeps outputs without inventing a connection, proxy or saved capture. This does not
replace an integrated test of those paths or guarantee a message identical to the console's.

## Validation and pending acceptance

`python -m unittest tests.test_snap_applets -v`: four focused tests, C fixture compiled with
`-Wall -Wextra -Werror`. The overlay also passes `clang -fsyntax-only -Wall -Wextra -Werror`
with the donor's real `host.h`. The duplicate scan was also run against the donor and the
integration checkout's overlays, because the isolated worktree lacks the initialised
submodule.

No GPU or full suite was run. Earlier RTX tests belong to the original 17-registration PR and
do not validate this revised C; an integrated build and acceptance of the new paths are
missing. The user's AMD report stays open.
