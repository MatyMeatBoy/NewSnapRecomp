# DIAG-HISTORY-01: newest logs after long session histories

Status: ready for independent review for 0.6; published 0.5.1 artifacts unchanged.

The diagnostics exporter stopped `scandir(logs/)` after 256 directory entries.
That limit counted unrelated files and depended on filesystem enumeration order.
A newer session later in the directory was silently excluded even when the ZIP
had room. A synthetic export with 600 unrelated entries followed by the newest
valid session reproduced the missing log before this change.

`diagnostics._recent_history()` now streams the entire immediate log directory.
It tests the exact existing session-log/display filename expressions before
requesting file metadata. Two min-heaps retain at most four launcher logs and
two display observations, ranked by modification time in nanoseconds with path
as a deterministic tie-breaker. Selection uses constant memory and O(N) directory
enumeration; it never materializes the directory or recursively walks owner data.
The previous `MAX_DIRECTORY_ENTRIES` cutoff is removed. No existing test or
consumer uses that constant.

Cancellation is checked before the scan and for every entry, including unrelated
files. Already-disappeared matching entries are skipped to tolerate concurrent
log rotation. Filesystem calls themselves remain subject to normal OS latency;
this is cooperative cancellation between entries, not an interruptible filesystem
operation. Export runs on the launcher's existing worker thread.

The retained candidates still pass the existing link checks, bounded reads,
redaction, display validation and ZIP size budgets. The exporter neither removes
nor rotates old logs, and it never modifies imports, profiles or other sources.
Output publication retains the existing atomic no-replace behavior.

Verification, 2026-11-14:

- New tests reproduced missing-last-log and missed cancellation after entry256
  before the fix; both pass afterward.
- Actual ZIP contains the newest allowed log placed after 600 unrelated entries;
  unrelated payloads stay absent and source bytes stay unchanged.
- Forty matching files verify the exact newest four logs/two observations, with
  instrumentation confirming the heaps never grow beyond their fixed capacity.
- Metadata access is permitted only for exact allowlisted names. A patched
  `Path.rglob` fails if any recursive walk is attempted.
- Cancellation after entry300 produces no ZIP/staging output and preserves the
  source log. Existing privacy/redaction/atomic publication tests still pass.

Command: `python -m unittest tests.test_diagnostic_history tests.test_diagnostics`.
Result: 15 tests OK, including one existing symlink-permission skip; the existing
Windows reparse-attribute test executes separately and passes. No GPU, native
build, network or game-data write was performed. This corrects evidence selection,
not the unresolved AMD rendering symptoms.
