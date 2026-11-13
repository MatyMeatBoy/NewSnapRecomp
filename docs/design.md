# NewSnapRecomp

User direction (2026-11-13): build a native Windows recompilation of New Pokémon Snap using captainj-sparrow/astral-chain-pc-recomp, which the owner has personally tested. Import the owner's base and cumulative update; prepare shaders before play; optimize while preserving game logic and saves.

The selected upstream is pinned as a submodule at 248e0b29f308ca84a2d2092019cc60e7fc50ae85. Keep its MIT notices and dependencies intact. Witch Time is a research reference only; its repository uses GPL-3.0, so do not silently copy it into the MIT codebase.

Approach: retain the upstream source as a reproducible reference; put game-specific import, analysis and generation tools in this repository. Never use Astral Chain's fixed RomFS address, offsets, function hooks or frame-rate patches on Snap. Select module addresses from Snap's actual metadata before a runnable build. A translated CPU module alone is not a playable port.

Initial executable deliverable: verified base/update import and a reproducible module/SDK/shader inventory. Then adapt the lifter and runtime boundary to the measured binary. Windows x64/Vulkan is the first target. Generated C, game binaries, resources, shader programs, caches, keys and saves stay local and outside Git.

Shader goal: enumerate game shaders and observed variants, translate ahead of play, prepare driver-specific pipelines, and persist compatible caches. Rebuild incompatible cache entries after translator, GPU or driver changes. Record runtime misses; zero first-use compilation is a goal to verify across routes, not a claim justified by a progress bar.

Optimization acceptance: compare the same route and settings with cold and warm caches, recording startup latency, frame p50/p95/p99, stalls, RAM/VRAM and shader/pipeline misses. Preserve photography evaluation, events, camera motion, audio timing and save behavior. Establish correctness before changing simulation rate or compiler flags.
