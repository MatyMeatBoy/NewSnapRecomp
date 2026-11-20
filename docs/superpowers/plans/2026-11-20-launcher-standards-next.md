# Launcher standards implementation plan

**Goal:** deliver the next Windows release with broader setup, optional original presentation, complete large-save backup/restore and truthful achievement integration.

**Architecture:** preserve the current native runtime and save formats. Isolate public-package relocation from owner data; reuse SDL3 for launcher navigation and custom Tk modal pickers. Parse decrypted NUP with bounded streams, then validate supported ExeFS and every RomFS file before producing a deterministic runtime image. Treat external RecompLauncher limits and hosted achievement activation as explicit dependencies, never simulate them.

**Tech stack:** Python/Tk/ctypes/SDL3, pinned C runtime and achievement SDK, zstandard NUP decoding, streaming ZIP backups, existing release/manifest validators.

- [ ] Optional Aspecto original preset; preserve defaults and all saved values unless explicitly chosen. Native resolution/filtering, original shadows/photos, 30 FPS and no FG; do not invent unverified visual parity.
- [ ] Read-only install bootstrap: actual write probe, verified public-file relocation under LocalAppData, existing newer copy reuse, owner-data copy only through a visible selected-data migration flow. Test traversal, integrity, no original writes and forwarded modes.
- [ ] SDL navigation + accessible file/confirmation dialogs. Package pinned public SDL DLL. Main-thread ownership, foreground and neutral-input gates, diagnostics handoff; test first-run without GameData.
- [ ] Full profile backups to a user-selected synced directory, all file sizes, streamed manifest/hash verification and atomic publication. Restore into a new profile, never overwrite a live profile; preserve account identity. Explicitly retain the upstream 64 MB cloud limitation. Test >64 MB, interruptions, malicious archives, races and conflicts.
- [ ] NUP v1 reader + selected supported base/update overlay. Build trusted public per-file hashes from the already supported whole-image fingerprint; deterministic normalized RomFS blob/index accepted only after complete trusted verification. Keep existing binary-image path unchanged. Validate synthetic corruption cases and a private roundtrip.
- [ ] Verified dump identity using the supported main NSO build ID and SHA receipts. Never invent universal NSP/NSZ/NUP container CRC values.
- [ ] Pin/license RecompAchievements SDK; test fake-pipe lifecycle, copied-save/Casual behavior and no-launcher no-op. Verify genuine gameplay hooks and prepare hosted list for the already claimed title; no fabricated progression or unlocks from existing saves.
- [ ] Independent review; full/native tests; source-matched build kit/frozen launcher/package; publish next stable/latest only with accurate scope and explicit external activation status.

Worker ownership: spike_audit owns new controller modules/tests; shadow_storage owns new NUP reader/tests; review_recomplauncher owns new install_location module/tests. Root owns shared wiring, backup, preset, normalized image validation, achievements and release integration. Shared entrypoints are edited serially by root.
