# Kit recovery and session identity

## Reproduced failures and fixes

A cache with a damaged tool was rejected before the valid bundle was tried. Now only an
integrity failure starts a local recovery: the exact bundle is verified, the complete
candidate is extracted/verified and its publication is serialised with an operating-system
lock. The failed cache goes to its own quarantine. Cancellation/permissions are not turned
into a download, and imports/profiles are not modified; a publication failure restores the
previous slot. An independent review and rollback/concurrent publication tests pass.
Quarantines are kept for diagnosis, with no automatic cleanup.

Logs from earlier launches did not allow automatically checking the executable against the
launcher's version. Each new attempt records the SHA256 it read, the marker's separate
claims, a mismatch if any, and the real exit code. The hash is computed in the worker, not
in Tk. A marker's claim does not replace that hash. Valid upper-case hex does not produce
false mismatches.

The CPU triage of PR #2 is integrated separately from the applet overlay, still in review.
It recognises new/legacy names, keeps the classification and marks generation as an
inference from the log. Paths with spaces and nested/corrupt JSON were hardened; accepted
identity data are bounded scalars. The ZIP includes a readable JSON analysis per session,
besides redacted text and a summary. It needs no agents, network or external utilities on
the test PC.

## Evidence and limits

387 complete tests before the new identity, one skipped for symlink privileges; the
reparse-attribute checks run. Private evidence: build/pending-investigation-full.log,
portable-observability-reviewed.log, diagnostics-reviewed-final.log. Rejecting a cache
without a bundle is kept; kits of other versions/revisions are never used to rescue it.

Runtime 8ff756d was compiled from scratch and passed selftest/loader. Isolated 20-second
RTX Vulkan test: exit 0, boot passed, legacy INI intact; SHA256
d733b8c8d805fd73a523e297b520347752b017afef2d85c228137adfd2ef6968. The cold cache shows
spikes with shader translation, including 685.5 ms with 593.3 ms of aggregated
translation; the counters overlap and must not be added. This alone does not explain the
earlier 107 ms spike, nor does it verify photos/AMD.

The earlier build and test do not include the new presentation and pool traces; they need
their integrated verification and a delivery with its own identity.
