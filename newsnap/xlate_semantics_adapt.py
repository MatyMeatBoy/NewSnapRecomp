"""Stage two Maxwell/SPIR-V semantic fixes without changing the pinned donor.

BFE/BFI derived from TotK c0e66fe4c1d532e728444c3ade6ff390f734151b
(MIT). SHF additionally bounds every intermediate shift, including select arms.
No unwritten-register/local initialization policy is changed.
"""
from pathlib import Path

from .upstream import ROOT

ORIGINAL_PATCHES = (
    '0001-keep-call-arguments-in-variables.patch',
    '0002-keep-live-call-sources-when-removing-dead-node.patch',
    '0003-keep-side-effect-assignments-in-the-ast-optimizer.patch',
    '0004-no-else-if-flattening.patch',
    '0005-declare-storage-image-write-without-format.patch',
    '0006-initialise-unlinked-vertex-outputs.patch',
    '0007-position-always-invariant.patch',
    '0008-point-size-from-support-buffer.patch',
    '0009-round-d16-array-compare-reference.patch',
    '0010-pcss-for-cascade-compares.patch',
    '0011-shadow-filter-spread.patch',
    '0012-motion-previous-position.patch',
)
SEMANTIC_PATCHES = ('0013-bitfield-defined-ranges.patch', '0014-funnel-defined-shifts.patch')
EXPECTED_PATCHES = ORIGINAL_PATCHES + SEMANTIC_PATCHES


def edits():
    before = '''    if len(patches) != 12:
        sys.exit(f"expected 12 patches, found {len(patches)}")'''
    after = f'''    expected = {EXPECTED_PATCHES!r}
    if tuple(p.name for p in patches) != expected:
        sys.exit("expected exact 14 Snap translator patches; unexpected or missing patch")'''
    return {'tools/build_xlate.py': [(before, after)]}


def stage_patches(destination):
    """Copy only our two patches after donor tool staging; reject unknown extras."""
    target = Path(destination) / 'tools/xlate/patches'
    present = {p.name for p in target.glob('*.patch')}
    if not set(ORIGINAL_PATCHES).issubset(present) or present - set(EXPECTED_PATCHES):
        raise ValueError('Unexpected or missing donor translator patches')
    for name in SEMANTIC_PATCHES:
        source = ROOT / 'patches/xlate' / name
        data = source.read_text(encoding='utf-8')
        (target / name).write_text(data, encoding='utf-8', newline='\n')
