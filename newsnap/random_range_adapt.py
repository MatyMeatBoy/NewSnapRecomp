"""Verified, reversible entry bridge for one Snap 2.0.1 integer operation."""
import hashlib
from pathlib import Path
import struct

from .upstream import ROOT

MAIN_SHA256 = 'ef20d6317d909bde106fec0958b58ccfdf4c46f36d9fa5ef8785ce54fff75443'
BUILD_ID = 'ddb900ff04a912ed42430508389853cfaf1accce'
OFFSET, LENGTH = 0x5ec660, 0x1a0
SPAN_SHA256 = 'c6464b70510a63ad4decfc4336e75fa4ed37fb72e5292a9e8e2d5c3973276c23'
PATCH_NAME = 'snap-2.0.1-random-range.txt'
PATCH_SHA256 = 'c80764ab15fd85b33cc94307a57dfb334c49d4568a23dee0baa79018ee6da004'


def verify_original(exefs, *, patch_file=None):
    """Run before generation/cache lookup; no original file is ever written."""
    patch_file = Path(patch_file) if patch_file is not None else ROOT/'patches'/PATCH_NAME
    # Git checkout newline conversion must not change the recipe's meaning.
    if hashlib.sha256(patch_file.read_text(encoding='utf-8').encode()).hexdigest() != PATCH_SHA256:
        raise ValueError('Random-range patch differs from the verified recipe')
    raw = (Path(exefs)/'main').read_bytes()
    if hashlib.sha256(raw).hexdigest() != MAIN_SHA256:
        raise ValueError('Random-range bridge requires the verified main SHA256')
    if len(raw) < 0x100 or raw[:4] != b'NSO0' or raw[0x40:0x60].rstrip(b'\0').hex() != BUILD_ID:
        raise ValueError('Random-range bridge main build ID differs')
    file_offset, memory_offset, size = struct.unpack_from('<III', raw, 0x10)
    compressed_size = struct.unpack_from('<I', raw, 0x60)[0]
    text = raw[file_offset:file_offset+compressed_size]
    if struct.unpack_from('<I', raw, 0xc)[0] & 1:
        import lz4.block
        text = lz4.block.decompress(text, uncompressed_size=size)
    offset = OFFSET-memory_offset
    if (len(text) != size or offset < 0 or offset+LENGTH > len(text) or
            hashlib.sha256(text[offset:offset+LENGTH]).hexdigest() != SPAN_SHA256):
        raise ValueError('Random-range bridge original code span differs')


# A second guard belongs to the generator itself: direct generator invocations
# must not apply a trusted first-word replacement to an unverified body, or
# combine it with another alternative/site inside the original function.
GENERATOR_GUARD = f'''
def snap_random_range_verify(mod, table, name, path):
    import hashlib
    expected_set = ('snap_random_range', 'AC_SNAP_RANDOM_RANGE', 1)
    matching = [i for i, item in enumerate(table.sets) if item[0] == expected_set[0]]
    uses_helper = any(isinstance(w, tuple) and len(w) == 2 and
                      w[0] in ('fn', 'fnz') and w[1] == 'snap_random_range'
                      for sites in table.sites.values() for alts in sites.values()
                      for _index, words, _original in alts for w in words)
    if not matching and not uses_helper:
        return
    if len(matching) != 1 or table.sets[matching[0]] != expected_set:
        raise ValueError('Random-range bridge unexpected patch set')
    expected = [(matching[0], [('fn', 'snap_random_range'), 0xd65f03c0], 0xf81b0ff9)]
    if table.sites.get('main', {{}}).get({OFFSET}) != expected:
        raise ValueError('Random-range bridge unexpected entry patch')
    for module_name, sites in table.sites.items():
        for offset, alternatives in sites.items():
            if module_name == 'main' and {OFFSET} < offset < {OFFSET+LENGTH}:
                raise ValueError('Random-range bridge original body has another patch')
            for _index, words, _original in alternatives:
                for word in words:
                    if (isinstance(word, tuple) and len(word) == 2 and
                            word[0] in ('fn', 'fnz') and word[1] == 'snap_random_range' and
                            (module_name != 'main' or offset != {OFFSET})):
                        raise ValueError('Random-range bridge helper used at an unexpected site')
    for back_edge, head in table.spins.get('main', {{}}).items():
        if ({OFFSET} <= back_edge < {OFFSET+LENGTH} or
                {OFFSET} <= head < {OFFSET+LENGTH}):
            raise ValueError('Random-range bridge original function has a spin gate')
    # Validate the global table before any module-specific return. SDK-only
    # generation must neither hide a foreign helper site nor bypass main pins.
    main_path = Path(path) if name == 'main' else Path(path).parent / 'main'
    if hashlib.sha256(main_path.read_bytes()).hexdigest() != '{MAIN_SHA256}':
        raise ValueError('Random-range bridge original main/build/span differs')
    verified = mod if name == 'main' else Module('main', main_path, 0, 'c')
    if (verified.nso.build_id != '{BUILD_ID}' or
            hashlib.sha256(verified.image[{OFFSET}:{OFFSET+LENGTH}]).hexdigest() != '{SPAN_SHA256}'):
        raise ValueError('Random-range bridge original main/build/span differs')

'''


def edits():
    return {
        'recomp/gen.py': [
            ('class Emitter:', GENERATOR_GUARD+'class Emitter:'),
            ('        patches.check(table, mod, name)',
             '        patches.check(table, mod, name)\n'
             '        snap_random_range_verify(mod, table, name, path)'),
        ],
        'runtime/cpu.h': [
            ('// ---- dynamic frame-rate patch helpers',
             'void snap_random_range(Cpu *cpu); // verified integer-operation entry bridge\n\n'
             '// ---- dynamic frame-rate patch helpers'),
        ],
        'runtime/patches.c': [
            ('        n += (size_t)snprintf(list + n, sizeof list - n, "%s%s %s", i ? ", " : "", sets[i].name,',
             '        // Function-entry profiling retains every original recursive callback.\n'
             '        if (g_fnprof && !strcmp(sets[i].name, "snap_random_range")) rt_patch_on[i] = 0;\n'
             '        n += (size_t)snprintf(list + n, sizeof list - n, "%s%s %s", i ? ", " : "", sets[i].name,'),
        ],
    }
