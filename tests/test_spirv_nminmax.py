"""CRISTAL-01: the NaN-safe min/max/clamp rewrite applies to the pinned donor and only touches GLSL.std.450 ops."""
from pathlib import Path
import struct
import unittest

from newsnap.spirv_nminmax_adapt import edits

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'third_party/astral'

FMIN, FMAX, FCLAMP, NMIN, NMAX, NCLAMP = 37, 40, 43, 79, 80, 81


def rewrite(words):
    """Python mirror of snap_spirv_nminmax, used to pin the opcode mapping."""
    glsl, i = 0, 5
    while i < len(words):
        op, length = words[i] & 0xffff, words[i] >> 16
        if op == 11 and struct.pack('<%dI' % (length - 2), *words[i + 2:i + length]).startswith(b'GLSL.std.450\0'):
            glsl = words[i + 1]
        if op == 54:
            break
        i += length
    out, i = list(words), 5
    while i < len(out):
        op, length = out[i] & 0xffff, out[i] >> 16
        if op == 12 and length >= 5 and out[i + 3] == glsl:
            out[i + 4] = {FMIN: NMIN, FMAX: NMAX, FCLAMP: NCLAMP}.get(out[i + 4], out[i + 4])
        i += length
    return out


def module(set_name, instruction):
    name = set_name.encode() + b'\0'
    name += b'\0' * (-len(name) % 4)
    name_words = list(struct.unpack('<%dI' % (len(name) // 4), name))
    words = [0x07230203, 0x10000, 0, 100, 0]
    words += [(2 + len(name_words)) << 16 | 11, 1] + name_words          # OpExtInstImport %1
    words += [3 << 16 | 54, 2, 3]                                          # OpFunction stub (scan stop)
    words += [7 << 16 | 12, 4, 5, 1, instruction, 6, 7]                     # OpExtInst %5 = set %1 instruction
    return words


class SpirvNminmaxAdapt(unittest.TestCase):
    def adapted(self, name):
        text = (RUNTIME / name).read_text(encoding='utf-8')
        for before, after in edits()[name]:
            self.assertEqual(text.count(before), 1, f'{name}: seam changed: {before[:60]!r}')
            text = text.replace(before, after, 1)
        return text

    def test_pipeline_module_creation_goes_through_the_rewrite(self):
        text = self.adapted('runtime/vk_pipeline.c')
        self.assertIn('rt_knob("SPIRV_NMINMAX", vk_caps.amd ? "1" : "0")', text)
        self.assertIn('rt_knob("SPIRV_DOMAIN_CLAMP", vk_caps.amd ? "1" : "0")', text)
        make = text[text.index('static VkShaderModule make_module('):]
        self.assertLess(make.index('snap_spirv_nan_safe(w, words, &safe_n)'), make.index('vkCreateShaderModule'))
        self.assertIn('if (nan_safe) w = nan_safe, words = safe_n;', make)
        self.assertIn('free(nan_safe);', make)
        for pair in ('FMIN = 37', 'FMAX = 40', 'FCLAMP = 43', 'NMIN = 79', 'NMAX = 80', 'NCLAMP = 81',
                     'LOG2 = 30', 'SQRT = 31', 'RSQRT = 32', 'OP_CONSTANT_NULL = 46'):
            self.assertIn(pair, text)

    def test_cfg_knows_the_key(self):
        text = self.adapted('runtime/cfg.c')
        self.assertIn('"SPIRV_NMINMAX"', text)
        self.assertIn('"SPIRV_DOMAIN_CLAMP"', text)

    def test_mapping_only_for_glsl_set(self):
        for source, target in ((FMIN, NMIN), (FMAX, NMAX), (FCLAMP, NCLAMP)):
            self.assertEqual(rewrite(module('GLSL.std.450', source))[-3], target)
        self.assertEqual(rewrite(module('GLSL.std.450', 31))[-3], 31)          # Sqrt untouched
        self.assertEqual(rewrite(module('NonSemantic.Other', FMIN))[-3], FMIN)  # another set untouched


if __name__ == '__main__':
    unittest.main()
