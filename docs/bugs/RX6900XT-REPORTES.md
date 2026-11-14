# Owner reports after publishing 0.5 alpha

Hardware confirmed by the owner: RX 6900 XT. Uses the public 0.5 ZIP from GitHub, not the
private dev1 package. The version/hash of the executable actually started still has to be
bound: the launcher gives a 404 error and the start has to be forced. Do not assume that the
launcher's version certifies the runtime's.

## Critical items and split

| ID | Concrete observation | Next work |
| --- | --- | --- |
| LAUNCH-404 | Running returns 404 and the start must be forced. | Codex: acquisition/local kit/private repository authentication, without skipping validation. |
| AUTO-DATA | GameData is in the port's folder and is not detected automatically. | Codex: portable paths, old preferences and presence without a marker. |
| FOTO-01/02 | Selection: the big photo and both thumbnails have black bands. Later evaluation: a Pikachu photo does show complete. | Codex/Claude: compare paths, slots, buffers and the saved JPEG. A correct view does not prove that every persisted byte is valid. |
| KEYBOARD-CRASH | Right after the shown registration/evaluation, the Windows keyboard opens and the game closes. | **Free for Claude**: applet/name entry/callback/return; tell an exception from a normal exit with the logs. Do not skip game steps. |
| COLOR-01 | The owner still sees overly saturated colours. | Check runtime, effective data/configuration and transfer on AMD; do not compensate by changing the game's grade. |
| HEAD-INTRO | Stutter localised on the head when walking in before the logo. | **Free for Claude**: analyse animation/transforms and cadence; do not blame general pacing without proof. |
| CONSOLE-01 | A CMD keeps running in the background. | Codex: identify our own process/origin and creation flags; keep diagnostics. |
| HOME-PROFILE | Asks to remove «Elegir perfil» (Choose profile) from Home. | Codex: move advanced selection to Options, keep profile and defaults. |

The repository is private (GitHub query confirmed). A download working on the development
PC with an authenticated gh does not vouch for a PC without those credentials. Do not put
tokens/credentials in packages or change the repository's visibility.

The owner also notices different smoothness between the local test and the 6900
XT/FreeSync; Astral Chain is their reference. Follow-up and comparison:
`docs/bugs/presentation-amd-nvidia.md`. Compare effective cadence, not just FPS.

## Screenshots and limits of inference

Private copies in `build/user-reports/rx6900xt-0.5/`, with SHA256 and original path in
`evidence.json`: `album-bands-amd.png` and `evaluation-good-amd.png`. Do not upload the
images, banks, photos or other game data to GitHub.

The HUD shows RX 6900 XT / i9-10850K, a 2560×1440 window, a 1920×1080 image, a 1600×900
scene and «AMD FSR 1, sharpness 80%». It is a hint to identify the effective
runtime/configuration; by itself it does not show which version ran or that this filter
explains the bands. Do not declare photos fixed from one screen's correct image.

**Independent positive confirmation:** the owner says the photo square now looks right on
the 6900 XT. That closes the reported visual defect of that box; it does not close saved
photos, colour, animation or the keyboard.

They could select the Pikachu/Vivillon folders and continue. Do not recover the previous
profile: the owner explicitly excluded it. Keep the subject, evaluation, tutorial and save
logic; do not fabricate progress or scores.

Take tasks and reserve files in `docs/PENDIENTES.md` before editing. Deliver a themed PR
from an isolated worktree; Codex integrates and tests. The published 0.5 alpha release stays
immutable; these observations reopen the affected cases.
