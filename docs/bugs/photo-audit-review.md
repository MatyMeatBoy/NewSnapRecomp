# Independent review of FOTO-02

2026-11-13 · Codex · **Fixes approved and integrated in PR #1**.

The review of commit `23f9d79` confirmed input protection, handling of malformed JPEGs and the
incomplete verdict on unverifiable data. The 20 audit tests and 5 photo tests pass. The AMD
evidence is still pending; approving the tool does not attribute the cause of the bands.

The initial findings are kept below for traceability.

The 17 existing tests passed, but three synthetic reproductions found:

1. **P1 — Output over input:** `main([bank, '--out', bank])` returns 0 and replaces the bank with
   JSON when the copy is in a folder without the protected names. Compare every output with every
   input discovered before writing; consider links/hardlinks and exports. Never overwrite an input
   bank, whatever its folder.
2. **P2 — A malformed JPEG aborts the audit:** SOI + SOF C0 of length 2 + EOI, and DRI of length
   2, raise `struct.error`. `audit_jpeg` calls the parser outside the decode block and `audit`
   only catches `ValueError`. Validate minimum lengths and keep errors per entry to carry on with
   the rest of the bank. Add both regression cases.
3. **P1 — Clean verdict with an unreadable JPEG:** a bank with a valid checksum and the JPEG `FF D8
   FF E0 00 10`, fourteen zeros and `FF D9` produces `bytes-limpios` even though
   `decodificación_fallida=1` and `estructura_con_problemas=1`. Emit an incomplete/damaged result;
   only declare clean with complete decoding evidence and valid checksums.

The report correctly notes that the 150 banks include copies and only two unique photos from one
NVIDIA route. Review the strength of its inferences: the bands coinciding with the subject
rejection does not by itself show that the evaluation reads those pixels, nor exclude
presentation, pitch or JPEG. Geometry measured on a rescaled screenshot guides tests; it does not
determine the cause.

The three cases were reproduced with synthetic data and now have regressions. Validation with real
AMD bytes must be done on a copy of the profile, without modifying the owner's save.
