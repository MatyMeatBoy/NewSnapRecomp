# Runtime replacement and cache-cleanup verification

CACHE-VERIFY-07, 2026-11-14. Reviewed independently before integration.

A successful filesystem call previously counted as success without checking its
result. Fault injection reproduced silent stale pipeline-cache retention and
post-rename executable corruption. The installation now checks the activated
marker, executable digest, runtime file inventory and absence of all five
allowlisted cache paths before committing; failures restore the old generation.

Recovery had two additional defects: copying a cache directory followed nested
Windows junctions into unrelated owner folders, and corrupted restored bytes
could cause the good backup to be discarded. Recursive copying now rejects
reparse points/links before descending. Recovery verifies restored file hashes,
directory inventories and expected absences before removing its journal.

Only the allowlisted runtime/cache files are replaced. Profiles, photos, input
data and shader recordings remain outside this operation. The transaction backup
and this build's staging directory are removed and their absence checked. Three
repeated installations leave one active runtime. A cleanup failure is reported;
if the generation is already committed, retry cleans the residual backup without
reverting it. Global driver caches are not deleted.

The rebuild result and log record the executable hash, paths checked, caches
actually present before removal, and cleanup postconditions. The launcher reports
verified cleanup only when all three postconditions are true. An optional log
write failure is reported separately from an already successful activation.

Validation: 79 focused unittest cases pass, two private-toolchain fixtures skip
in the isolated checkout. New fault-injection tests first reproduced the two
recovery failures. Native Windows junction rejection was exercised. Independent
source review approved the five implementation/test files. No GPU test applies
to these filesystem checks; this does not establish the cause of photo bands.
Directory metadata flushing remains best effort and does not promise recovery
from every power-loss/filesystem failure or external concurrent path replacement.
