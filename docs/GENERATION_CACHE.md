# Private generation cache

Owner-runtime rebuilds can reuse generated C, headers and JSON from
`%LOCALAPPDATA%/NewSnapRecomp/generated-cache`. These are private, owner-derived
files. They are never included in launcher/source-kit releases or uploaded.

A cache hit requires the same canonical owner-data path, verified original ExeFS
and RomFS hashes, complete generation recipe, Python implementation/cache tag and
exact version, and NumPy/Capstone/LZ4 package versions. Missing package identity is
recorded explicitly. Original imports are still verified on every build.

The existing generation receipt and every generated file hash are checked before
copying and again on the independent snapshot. No hardlinks, native executables
or compiler objects are reused. Native compilation and candidate validation run
on every rebuild.

Only the two most recently published snapshots are retained, with a 1 GiB budget
for managed entries. Eviction checks the dedicated root marker, entry ownership,
resolved paths and all links/reparse points before deleting anything. Unknown
objects or unsafe paths disable cache writes; imports, profiles and unrelated
paths are preserved. Corruption or cache permission failures fall back to fresh
generation. A readable corrupt owned snapshot can be replaced after regeneration.

Set `NEWSNAP_GENERATION_CACHE=0` to disable caching. Tests and private acceptance
can inject a dedicated temporary `generation_cache_root` into `build()` or
`rebuild_runtime()` without touching the user's default cache.

`GameData/logs/generation-cache.json` records whether generation ran or a verified
snapshot was restored, the generator environment, and lookup/generation/publish
times. Runtime rebuild results retain this receipt after staging cleanup.
Generation time avoided is separate from native compilation and gameplay frame
rate; no gameplay performance improvement is claimed by this cache.
