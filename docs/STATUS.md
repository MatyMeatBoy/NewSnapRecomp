# Bring-up evidence — 2026-11-13

The intended deliverable remains a playable native New Pokémon Snap recompilation with shader preparation and measured optimization. It is not yet complete.

## Verified locally

- Base title `0100F4300BF2C000`, cumulative update title `0100F4300BF2C800`; NACP confirms display version 2.0.1.
- Both ExeFS packages verified by block hashes. Updated RomFS merged with the selected upstream's hactool and all six IVFC levels verified: 7,316,217,452 bytes, 3,310 files.
- 1,125 DRPF archives indexed: 82,127 members, 71,868 compressed members and 3,138 `nushdb` entries. This is an archive inventory, not a count of fully prepared shader variants.
- 62,961 functions translated across main and sdk, no unsupported-instruction reports. Generated C remains private.
- clang 23/x64-v3 private executable builds. Initial clean compile: 179.2 seconds, process-tree peak about 1,259 MiB. These are build measurements, not gameplay performance gains.
- Runtime memory/dispatch selftest and loader probe pass. No strong unresolved imports. Boot reaches the first NVN call.
- Initial stable 15-second rendering probe displays the autosave notice with text/icons and emits audio. That run reported zero shader failures and zero validation errors. This does not establish later gameplay, photography evaluation, save round-tripping, timing or long-session correctness.
- Source fixtures cover wrong titles, damaged containers, stale imports, control metadata tampering, stale/generated-source tampering and CMIF/domain framing. An independent review identified three provenance defects; fixes now verify all imported outputs and bind generated C to its input hashes and source recipe.

## Adaptations

- Remove the inherited fixed-address RomFS layout and game instruction patches.
- Match Snap's actual NPDM main stack and SDK initialization export.
- Parse the domain header before CMIF; provide the domain root id.
- Add the missing persistent local-account/save-capacity queries, touchscreen `<6>`, neutral gesture/assignment state and required NVN getters/debug switch.
- Permit validated writable module-data pages as thread-stack mapping sources.
- Keep shader control metadata owned by each NVN program until finalization. The previous borrowed pointers produced missing/invalid stages and a white image; copying them changed the observed output to the correct startup UI. Broader rendering correctness remains unverified.

## Remaining work

- Verify title, initial setup and a complete playable route, including identifying/evaluating photographed Pokémon.
- Check remaining SDK/NVN paths and save/reload behavior; online network services currently report unavailable.
- Complete offline shader extraction/translation and driver pipeline preparation, then measure misses with cold and warm caches.
- Compare equivalent workloads before selecting performance changes. Do not treat startup UI FPS as gameplay evidence.
- Recheck rendering and lifetimes across scene changes and longer sessions. Earlier experimental runs included crashes and blank output; one successful startup run does not erase those coverage limits.

Private evidence lives under `build/research/`, including import/module inventories, run logs, screenshots and GPU pass dumps. Do not commit those files or any game-derived binaries.
