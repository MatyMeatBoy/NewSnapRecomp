# PR #2 review: applets and close triage

Review of `732671b35668b4ed0d275e3c6e6da217107e64bb`.
PR: https://github.com/MatyMeatBoy/NewSnapRecomp/pull/2
CI Source checks pass. This review describes the original proposal and the contracts that
blocked its integration. They were resolved before the merge: canonical bool false, removal
of four speculative account overrides and a bounded read of ErrorResultVariant. Current
status and tests in [reviewed contracts](pr2-applet-contracts.md). The observations below
are kept as historical evidence, not as present defects of the overlay.

## Boolean return

`nn::nifm::HandleNetworkRequestErrorResult()` returns bool, not Result. The pinned SDK,
`sdk+0x32e950`, normalises the return with `and w0,w0,#1`. The three observed callers
(`main+0x537a04`, `main+0x537a30`, `main+0x53b7f0`) use `tbz w0,#0`. The overlay returns
RT_RESULT(110,1), 622: bit zero false, full value non-zero. Fix to `false` (0) and check the
canonical value and that both ways of testing a bool agree. The current callers take the
same false branch with 622; a wrong game branch was not shown in that dump. The ABI contract
is broken all the same.

Four original tests pass because they expect a Result's module. An independent native
fixture with the bool assertion fails on the proposed code: private evidence
`build/pr2-applet-review/bool-contract/`.

## Account errors

The comment «the game only checks success» is wrong. The callers at
`main+0x538cac..0x538cc4`, `+0x538d50..0x538d68`, `+0x538e34..0x538e5c` and
`+0x1f2b10..0x1f2b28` distinguish module 124 and description ranges 200–269 and/or
430–499. The synthetic error 124/100 falls outside. Before promising equivalence with an
offline console, the chosen contract must be justified and its consuming branch checked.
Do not substitute another guessed description or change progress to hide failures.

## Owner's log

SHA256 BDBB38B767C3295FFB06BE0C3EB611F20444BBE6AE744BDFDF438D5F39D8680B. The observed fatal
is `rt_dispatch sdk+0x273060`; inferring the generation from the log's lines/patches is
useful, but it does not cryptographically identify the executable or show what opened the
system keyboard. The package the owner downloaded was the GitHub ZIP; automatically
investigate the executable that may have started after the launcher's 404. Do not ask them
again to work out versions by hand, and do not close photos/colour/AMD without validation.

The launcher's new exporter includes hash and identity for future sessions. The later
integration keeps main's most recent triage. The integrated route and the physical AMD
acceptance are recorded separately; integrating the PR does not by itself establish the
keyboard's cause or the owner's sign-off.
