# FOTO-02 · CPU audit of saved photos (black bands)

Status: **REVIEW** · Owner: MatyMeatBoy · 2026-11-13
Audit hardware: RTX 4060 Laptop (the same as the RTX tester's). **No bytes generated on the owner's
RX 6900 XT are on this machine**; see Limits.

## Question

Are the black bands in photos and thumbnails in the saved bytes (capture → readback → JPEG) or
only in the preview (texture/presentation)?

## Summary

| Claim | Class | Evidence |
|---|---|---|
| Locally saved photos and thumbnails (NVIDIA) are clean in bytes | **Observed** | 150 banks in 14 profile copies, 0 bands, 0 black blocks, correct CRC/Adler/JPEG structure |
| The owner's failure (AMD) appears on the selection screen **before saving** | **Observed** | Screenshot `b8af3c5e`: preview and the strip's 2 thumbnails with bands; message «You can't select a photo without a clearly visible subject» |
| The AMD bands are not full-width bands: they are contiguous valid runs in the order of 48-row strips | **Observed** (measured on the screenshot) | Geometry below |
| The banded AMD photos probably never reached bank 3/4 | **Inferred** | The game did not let them be selected; no save after 16:53 exists on this machine |
| The defect is upstream of the JPEG (uncompressed texture/readback) | **Unchecked hypothesis** | Preview and thumbnails show the same corruption and the subject rejection coincides. The coincidence does not show that the evaluation reads those pixels, nor exclude presentation, pitch or JPEG |
| Whether the saved AMD JPEG contains the bands | **Undetermined** | Needs the tool run on a copy of an AMD save |

## Tool

`tools/audit_saved_photos.py` (read-only, CPU):

- Opens banks 3 (`00c31e53dde3ac51`, photos) and 4 (`4f342de95be7450e`, thumbnails) with
  `shared_read`; computes the file's SHA-256 before and after (`unchanged_after_read`).
- Per slot: magic, lengths, Adler-32 and CRC-32 separately, metadata, padding after EOI.
  Unlike `saves.saved_jpegs`, it does not stop at the first damaged entry.
- Per JPEG: segment walk (SOF, sampling, DRI, RST sequence, EOI), full decode with Pillow,
  SOF vs. decoded dimensions.
- Pixels: black rows/columns (≥98 % with max channel ≤24) classed `edge`/`interior` and their
  8/16 alignment; the share of fully black 16×16 blocks (`black_block_fraction`, suspicious at
  ≥1 %) for partial-width bands.
- Verdict: `bandas-en-bytes-de-foto` (bands in photo bytes),
  `bandas-solo-en-miniaturas-guardadas` (bands only in saved thumbnails),
  `incompleto-o-dañado` (incomplete or damaged), `bytes-limpios` (clean bytes) or `sin-fotos`
  (no photos). `bytes-limpios` requires complete evidence: every bank read, consistent sizes,
  valid checksums, every JPEG decoded and no structure problems. Any exception is kept in
  `summary.incidencias`. Exit code: 0 clean, 1 with bands, 2 incomplete.
- A malformed JPEG or a per-entry error does not stop the rest of the bank.
- Outputs: never match an input bank (same path, symbolic link or hardlink), never land in an
  input bank's folder, never use a save file name, and never go into `save`, `save-tx`,
  `save-backup`, `GameData` or `newsnapGameData`. This is checked before reading and again when
  writing each file. The JSON report contains no images; `--export-flagged` copies only the
  flagged JPEGs to a local folder.

```
.venv\Scripts\python -X utf8 tools\audit_saved_photos.py <profile-copy> --out build\photo-audit\report.json --export-flagged build\photo-audit\flagged
```

## Local results (NVIDIA)

Command: every profile with `save/` under `build/` plus their `save-tx/work` →
`build/photo-audit/all-build-copies.json` (1 min 34 s).

- 150 banks read, 0 header errors, 0 inconsistent sizes, 0 files modified by reading.
- 136 banks with only empty slots (954 photo slots, 252 thumbnail slots).
- 14 profiles (`v03-final-native-smoke` … `v05-original-pacing-warm-02`) share the same 2
  photos from 0.3's tutorial route:

| Bank | Slot | SHA-256 (16) | Size | JPEG | Bytes | Bands | Black blocks |
|---|---|---|---|---|---|---|---|
| photos | 0 | `8c17e804a8352074` | 1080×720 | baseline 4:2:0, no DRI | 379 697 | none | 0 % |
| photos | 1 | `62553a0656964a2c` | 1080×720 | baseline 4:2:0, no DRI | 434 350 | none | 0 % |
| thumbnails | 0 | `5cf214065a29b1ea` | 240×200 | baseline 4:2:0, no DRI | 39 984 | none | 0 % |
| thumbnails | 1 | `505f067149be2290` | 240×200 | baseline 4:2:0, no DRI | 38 395 | none | 0 % |

Visual inspection of photo 1 and its thumbnail: complete, coherent image.
`newsnapGameData/profile` (read-only, untouched) has empty banks, unchanged since 04:26; the
photos from the owner's report (16:53:29) are not on this machine.

## Geometry of the bands in the AMD screenshot

Screenshot `build/user-reports/clipboard-b8af3c5e-….png` (1600×901; the preview covers
601×401 px ≈ 1080×720 × 0.556):

- Vertical transitions every ≈26.7 screen px = **48 photo rows** (15 strips). No cuts in the
  middle of a strip.
- Inside a strip the horizontal cut falls at x ≈ 215, 285, 503, 573, 791, 861 photo px (not a
  tile grid in X).
- Walking the image as 15 concatenated 1080×48 strips, the **valid** runs are ≈[70, 1080),
  [4102, 5112), [8134, 9144), [12166, 13176): about **1010 valid px every 4032**, i.e. ≈1 in 4
  contiguous runs; the rest is pure black (max channel ≤6).
- 15×15 map (`.` valid, `#` black, `?` mixed/covered by the UI):

```
.........?.....
??############?
###############
############...
...........####
###############
###############
########.......
.......########
###############
?##############
?###...........
...############
#??############
###??##########
```

Reading (a hypothesis to guide FOTO-01 tests, **not a determined cause**): the valid content
seems to be in its place and the rest black, with a periodicity in a 48-row strip order. A
compatible explanation is a chunked copy/upload/readback in which only part of the chunks
arrives (buffer ranges, dirty pages, incomplete parallel jobs). The measurement comes from a
rescaled screenshot and does not by itself exclude pitch, presentation or JPEG errors.
Suggested test: find in the renderer what walks the 1080×720 image in 48-row strips or
≈1008×48 px chunks (≈193 536 bytes in RGBA8) and dump the capture texture.

## Relation to other tasks

- **FOTO-01**: suggested point to instrument first: the uncompressed capture texture and its
  readback on AMD, before the JPEG encoder.
- **TUTO-01**: the «without a clearly visible subject» message appears with the same corrupt
  photos. It is only an observed coincidence; there is no proof the evaluation reads those
  pixels.
- The report's photo↔thumbnail comparison is only indicative: thumbnails are 6:5 crops with a
  different horizontal offset per photo (120 and 192 px in the two samples), not a reduction
  of the photo.

## Tests

```
.venv\Scripts\python -X utf8 -m unittest tests.test_photo_audit tests.test_photos
```

25 tests OK (20 in `tests/test_photo_audit.py`: interior/edge/column bands after JPEG, a
partial-width strip, all black, structure and truncation, a clean bank left unmodified, bands
in a photo, bands only in a thumbnail, an entry with an invalid checksum without hiding the
rest, a wrong key, refusal to write inside the save, and the review's regressions).

## Answer to the RTX tester's review (`photo-audit-review.md`)

1. **Output over input (P1)** — fixed: `check_output`/`safe_write` compare each output with
   every discovered bank. Regressions: `--out` equal to the bank, in its folder, a hardlink to
   the bank, a bank name in another folder, an export inside the input folder.
2. **Malformed JPEG aborts (P2)** — fixed: minimum SOF/DRI lengths, a protected parser and
   errors kept per entry. Regressions with SOF C0 and DRI of length 2, alone and inside a bank
   with another valid photo.
3. **Clean verdict with an unreadable JPEG (P1)** — fixed: verdict `incompleto-o-dañado` and
   exit 2. Regression with the review's exact JPEG.
4. **Strength of the inferences** — lowered to hypotheses in this report.

After the fixes the audit was repeated on three representative profiles (`v03-jump-fixed`,
`v05-original-color-chain`, `v04-production-neutral-fsr31`): `bytes-limpios`, complete
evidence.

## Limits

- No byte generated on AMD has been audited. The «clean bytes» verdict holds only for the
  NVIDIA RTX 4060 and 2 photos from a single route.
- The AMD geometry is measured on a rescaled screenshot (±2 photo px); the chunk sizes are
  approximate.
- Black-block detection can flag legitimately very dark scenes (caves, night);
  `--export-flagged` exists to review them by eye.
- `saves.py`, `photos.py` and every integration point were left unchanged.

## Proposed next step (owner, AMD)

1. With the game closed, copy the profile to a working folder and run the tool on the copy. If
   the save has photos, the verdict decides between capture (bytes) and preview.
2. If no photo got saved (tutorial softlock), the decisive test is a dump of the capture
   texture from the renderer (FOTO-01).
