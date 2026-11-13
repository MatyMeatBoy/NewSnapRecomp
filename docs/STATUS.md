# Bring-up evidence — 2026-11-13

The intended deliverable remains a playable native New Pokémon Snap recompilation with shader preparation and measured optimization. It is not yet complete.

## Verified locally

- Base title `0100F4300BF2C000`, cumulative update title `0100F4300BF2C800`; NACP confirms display version 2.0.1.
- Both ExeFS packages verified by block hashes. Updated RomFS merged with the selected upstream's hactool and all six IVFC levels verified: 7,316,217,452 bytes, 3,310 files.
- 1,125 DRPF archives indexed: 82,127 members, 71,868 compressed members and 3,138 `nushdb` entries. This is an archive inventory, not a count of fully prepared shader variants.
- All 3,138 shader libraries decoded through the original, SHA-bound game decoder; every decoded resource passed its size and CRC32 checks. SSBH inventory: 3,076 vertex, 3,146 fragment, three compute and two geometry stages; 3,480 distinct supported programs by runtime hash.
- Library defaults plus 70 recorded variants produced 3,493 unique prepared variants (1,646 vertex, 1,843 fragment, four compute), zero translation failures and zero driver-preparation failures on RTX 4060/driver 616.92. Translation took 20.6 seconds and driver-cache preparation 8.7 seconds. Geometry stages remain unsupported; unseen texture answers and pipeline combinations remain unverified.
- A repeat 25-second autosave/language-menu sequence prebuilt 38 recorded pipelines before guest execution, with zero failures. One before/after pair had mixed frame-time results; it establishes preloading, not an overall performance improvement or gameplay FPS.
- 62,961 functions translated across main and sdk, no unsupported-instruction reports. Generated C remains private.
- clang 23/x64-v3 private executable builds. Initial clean compile: 179.2 seconds, process-tree peak about 1,259 MiB. These are build measurements, not gameplay performance gains.
- Runtime memory/dispatch selftest and loader probe pass. No strong unresolved imports. Boot reaches the first NVN call.
- Initial stable 15-second rendering probe displays the autosave notice with text/icons and emits audio. That run reported zero shader failures and zero validation errors. This does not establish later gameplay, photography evaluation, save round-tripping, timing or long-session correctness.
- Local-name mode, explicitly selected by the owner, bypasses loading Nintendo's profanity dictionary by reporting the real missing-content error before entering the SDK mount. The PC keyboard retains length, disabled-character and cancellation handling. A scripted `Snap` name (1–12 UTF-16 units required by the game) reaches character confirmation, with zero shader failures and zero validation errors. The filter object remains uninitialized; its original destructor is retained.
- The equivalent confirmation sequence, after the OE binding fix, completes its initial save transaction (five changed files) and reaches the rendered title scene. The 60-second scripted run exits successfully: 3,312 presents, zero unimplemented NVN calls, zero validation errors, zero shader failures and zero skipped draws. The final eight-second frame-time sample is only the title scene; it is not gameplay performance evidence.
- The fetched Astral Chain upstream `main` is identical to the selected commit. Release 1.14.0's source is already included. `docs/UPSTREAM.md` distinguishes included infrastructure from unverified Snap engine features.
- Source fixtures cover wrong titles, damaged containers, stale imports, control metadata tampering, stale/generated-source tampering and CMIF/domain framing. An independent review identified three provenance defects; fixes now verify all imported outputs and bind generated C to its input hashes and source recipe.

## Adaptations

- Remove the inherited fixed-address RomFS layout and game instruction patches.
- Match Snap's actual NPDM main stack and SDK initialization export.
- Parse the domain header before CMIF; provide the domain root id.
- Add the missing persistent local-account/save-capacity queries, touchscreen `<6>`, neutral gesture/assignment state and required NVN getters/debug switch.
- Permit validated writable module-data pages as thread-stack mapping sources.
- Keep shader control metadata owned by each NVN program until finalization. The previous borrowed pointers produced missing/invalid stages and a white image; copying them changed the observed output to the correct startup UI. Broader rendering correctness remains unverified.

## Remaining work

### v0.3 alpha evidence

The fixed native-size replay completed nine minutes and 32,263 presents, captured
Pikachu and displayed a 2,600 point evaluation, then passed the formerly failing
font SDK setjmp/longjmp continuation and entered the first route. Seven save files
changed; the album decoded two real 1080×720 originals and their thumbnails.
Originals were opened/exported with identical bytes and thumbnail duplicates are
grouped. A complete course and its in-game photo reload remain unverified.

Controller mapping changes pass real SDL virtual-device/native mapper tests and
the rebuilt private executable's selftest/loader checks. Physical controller
models remain unverified. Stable-channel updater code passes private API download
and exact frozen-package upgrade/repair with preserved owner-data sentinels.
These updater checks establish the launcher scope independently of the runtime.
The detailed queue and evidence are in [V03.md](V03.md).

Latest adaptation block (2026-11-13): device timezone conversion now passes the
240-second tutorial probe (14,177 presents, no unsupported NVN calls, validation
errors, shader failures or skipped draws). This reaches Pikachu camera training;
it does not establish a complete route or photographic evaluation. The launcher
adds detailed video settings, original icons and a bounded read-only album.
Photo extraction has synthetic-image and real empty-bank coverage only. Album
refresh and expeditions share a profile lock; menu restarts preserve that lock
through an explicit parent-supervised protocol. Snap-native render levels have
initial 3D GPU evidence in [VIDEO_COMPATIBILITY.md](VIDEO_COMPATIBILITY.md).
Higher frame rates remain an investigation in [HIGH_FPS.md](HIGH_FPS.md).

- Verify title, initial setup and a complete playable route, including identifying/evaluating photographed Pokémon.
- Validate close/restart during actual protected work. OE enter/leave now maintain nested host exit sections; window closure defers until holders leave, then blocks new sections through the final save flush. Native fixtures cover nesting, deferred closure and underflow; real concurrent closure remains untested. Independent review found no confirmed defects in these additions.
- Check remaining SDK/NVN paths and save/reload behavior; online network services currently report unavailable.
- Resolve geometry-stage support and verify actual texture-answer variants and complete pipelines across routes; measure misses with cold and warm caches.
- Compare equivalent workloads before selecting performance changes. Do not treat startup UI FPS as gameplay evidence.
- Recheck rendering and lifetimes across scene changes and longer sessions. Earlier experimental runs included crashes and blank output; one successful startup run does not erase those coverage limits.

Private evidence lives under `build/research/`, including import/module inventories, run logs, screenshots and GPU pass dumps. Do not commit those files or any game-derived binaries.
