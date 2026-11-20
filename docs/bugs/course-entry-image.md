# Course-entry transient image: investigation, 2026-11-20

Owner report: an unrelated image briefly appears while entering a course; the
first daytime course is a suggested reproduction. Historical TRANSITION-01 notes
describe a Swanna image. No cause or fix is established by this investigation.

Tests used an isolated runtime and independent copies of the supplied save,
normal controller inputs, 144 FPS, windowed 1280x720, 1920x1080 internal rendering,
upscaling/frame generation/HD shadows off, original Snap colour processing.
Hardware: NVIDIA RTX 4060 Laptop. This is not RX 6900 XT acceptance.

- First entry: 1,440 consecutive presented-frame thumbnails (frames 2791–4230),
  covering loading, white fade, teleport, vehicle and gameplay.
- Second entry: normal pause menu → restart route → level selection → confirm.
  3,000 consecutive presented-frame thumbnails (frames 5531–8530), covering the
  confirmation, fade, teleport, vehicle and resumed gameplay. The capture writer
  completed; the process exited 0.
- Reviewed overview contacts and neighboring frames for the strongest isolated
  visual changes. Observed changes were teleport animation and the blue route
  effect. No unrelated Pokémon photograph was observed in these captures.

This is **not reproduced on the tested RTX routes**, not a proof of absence on
every course/profile/GPU. No blanket clear, colour change, delayed gameplay or
progress bypass was added to hide an unexplained frame. TRANSITION-01 remains
open. Private captures are excluded from the public package and repository.
