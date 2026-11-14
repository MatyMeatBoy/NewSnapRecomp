# Acceptance of the 0.5 candidate on the RX 6900 XT

Version 0.5 is still in development. The RTX 4060 tests are local controls; they do not
close the defects the owner saw on AMD. Do not publish until the gates in
`docs/PENDIENTES.md` are complete.

## Preparation

- Use a complete copy of the portable folder and of GameData. Keep the original 0.4
  installation and its profile unchanged. Do not mix a candidate executable with the marker
  or launcher of a different recipe.
- Before launching, check in Home that data and profile point to that copy.
  `launcher.json` may keep an external absolute profile; use «Elegir perfil» (Choose
  profile) to select the copied profile and confirm the path shown.
- Record the executable's SHA256, the candidate revision, the AMD driver version,
  resolution, Windows scaling, display mode and HDR/FreeSync state.
- Start with Original, 100 % scale, TV mode, a 60 FPS cap and motion off. These settings
  isolate the reported failures; the other options are tested separately afterwards. Do not
  change saturation, contrast or gamma.
- Prepare shaders for that GPU through the launcher. Keep its log. Separate
  start-up/preparation from the measurement with a warm cache.

## Route and evidence

1. In Home, load the data, check the difference between loaded/verified, check
   version/profile and launch. Launching must not open Update.
2. In the intro, watch the protagonist walking: a stable camera at rest, no model vibration.
   Test mouse and controller separately, focus loss, recapture and reconnection; record
   which device produces any movement.
3. Aim at Pikachu still and moving, with and without zoom. Keep screenshots of the
   reticle/name and note whether the fragments follow the subject.
4. Take valid photos of Pikachu and Vivillon, check image and thumbnail, complete
   selection/evaluation and enter the first expedition through the original flow. Do not edit
   progress, subjects or scores to be able to continue.
5. Close normally and reopen the album. On a copy of the profile, run
   `tools/audit_saved_photos.py --help` and follow its audit options. Attach the report and,
   privately, the affected banks if bands persist. A screenshot alone does not locate
   whether the damage is in the JPEG.
6. Compare the colour with Snap's original output without the port's filters. Record whether
   the perceived difference remains; the local digital comparison does not validate the
   monitor or the physical AMD chain.
7. Measure the same route with a warm cache and without concurrent builds or diagnostic
   captures. Keep complete frametimes: p50/p95/p99/maximum as well as the average. Do not
   infer active FreeSync only from FIFO/mailbox.

Physical sensor changes are made explicitly. A test with one controller does not vouch for
all models; record model, connection and Switch mapping. FSR 3.1/4 and DLSS are validated
according to that GPU's real availability, without presenting an unsupported mode as on.

## If the tutorial block happens again

At the owner's direction, recovering the previous profile is out of scope and not an
acceptance requirement. The pending test focuses on new photos and the alpha's normal flow on
the RX 6900 XT.

If a new test blocks again, keep its log, banks and screenshots for investigation. The
owner's hypothesis is that mouse/gyro moved the camera; do not change the logic to accept
photos without a subject or edit progress to hide a failure.

## Result

Each case keeps device, binary, route and result: passed, failed or not run. Cases not run
stay pending. Audit reports, photos, profiles and derived executables stay private in
`build/`.
