"""CRISTAL-01: Switch-like NaN behaviour for translated shaders on AMD.

Two independent rewrites of each game shader module before vkCreateShaderModule:

1. AC_SPIRV_NMINMAX: GLSL.std.450 FMin/FMax/FClamp -> NMin/NMax/NClamp. Maxwell's
   FMNMX returns the operand that is not NaN and .SAT turns NaN into 0; FMin/FMax/
   FClamp leave a NaN operand undefined. NVIDIA returns the other operand, AMD can
   return the NaN (Lichii #325/#432, Savage Wind #153, ocarina-recomp patch 0031).
2. AC_SPIRV_DOMAIN_CLAMP: Sqrt/InverseSqrt/Log2 take NMax(x, 0). A value NVIDIA
   computes as exactly 0 can come out a hair below 0 on AMD; sqrt/log2 of it is NaN
   (ocarina-recomp #49: black silhouettes fixed by Sqrt(NMax(x, 0))). Snap's
   Crystabloom shader takes log2(fma(dot(n, l), 0.5, 0.5)) of normalized vectors.

On the owner's RX 6900 XT the Crystabloom's crystal drew black: one transparent
draw left ~55k NaN pixels in the F12 dump. Both default on for AMD, off elsewhere,
so NVIDIA output stays bit-exact. The translator and its shader cache are untouched.
"""

BEFORE = '''static VkShaderModule make_module(const uint32_t *w, uint64_t words) {
    uint64_t fixed_n = 0;
    uint32_t *fixed = spirv_fixup(w, words, &fixed_n);
    if (fixed) w = fixed, words = fixed_n;
    VkShaderModuleCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO, .codeSize = (size_t)words * 4, .pCode = w};
    VkShaderModule m = VK_NULL_HANDLE;
    VkResult r = vkCreateShaderModule(P.device, &ci, NULL, &m);
    free(fixed);
    return r == VK_SUCCESS ? m : VK_NULL_HANDLE;
}'''

AFTER = '''// NewSnap CRISTAL-01: Switch-like NaN behaviour on AMD (the Crystabloom's crystal drew black on an RX 6900 XT).
//  - AC_SPIRV_NMINMAX: GLSL.std.450 FMin/FMax/FClamp -> NMin/NMax/NClamp. Maxwell's FMNMX returns the operand that
//    is not NaN and .SAT turns NaN into 0; FMin/FMax/FClamp leave a NaN operand undefined (NVIDIA returns the other
//    operand, AMD can return the NaN).
//  - AC_SPIRV_DOMAIN_CLAMP: Sqrt/InverseSqrt/Log2 take NMax(x, 0): a value NVIDIA computes as exactly 0 can come out a
//    hair below 0 on AMD, and sqrt/log2 of it is NaN.
// Both default on for AMD, off elsewhere. NULL when nothing changes; *out_n is the new word count.
static void snap_nan_knobs(int *minmax, int *domain) {
    static volatile int mm = -1, dc = -1;
    if (mm < 0 || dc < 0) {
        int a = rt_knob("SPIRV_NMINMAX", vk_caps.amd ? "1" : "0"), b = rt_knob("SPIRV_DOMAIN_CLAMP", vk_caps.amd ? "1" : "0");
        rt_log("vk_pipeline: shader NaN semantics: min/max/clamp %s (AC_SPIRV_NMINMAX=%d), sqrt/rsqrt/log2 %s "
               "(AC_SPIRV_DOMAIN_CLAMP=%d)", a ? "NaN-safe" : "as translated", a, b ? "clamped at 0" : "as translated", b);
        mm = a, dc = b;
    }
    *minmax = mm, *domain = dc;
}

static uint32_t *snap_spirv_nan_safe(const uint32_t *w, uint64_t n, uint64_t *out_n) {
    enum { OP_EXT_INST_IMPORT = 11, OP_EXT_INST = 12, OP_CONSTANT_NULL = 46, OP_FUNCTION = 54, LOG2 = 30, SQRT = 31,
           RSQRT = 32, FMIN = 37, FMAX = 40, FCLAMP = 43, NMIN = 79, NMAX = 80, NCLAMP = 81, MAX_TYPES = 16 };
    int minmax, domain;
    if (n < 5) return NULL;
    snap_nan_knobs(&minmax, &domain);
    if (!minmax && !domain) return NULL;
    uint32_t glsl = 0, bound = w[3], types[MAX_TYPES], zeros[MAX_TYPES];
    uint64_t fn_at = 0, swaps = 0, clamps = 0;
    int ntypes = 0;
    for (uint64_t i = 5; i < n;) {
        uint32_t op = w[i] & 0xffff, l = w[i] >> 16;
        if (!l || i + l > n) return NULL;
        if (op == OP_EXT_INST_IMPORT && l >= 3 && !strncmp((const char *)(w + i + 2), "GLSL.std.450", (size_t)(l - 2) * 4))
            glsl = w[i + 1];
        if (op == OP_FUNCTION && !fn_at) fn_at = i;
        if (op == OP_EXT_INST && l >= 5 && glsl && w[i + 3] == glsl) {
            uint32_t ins = w[i + 4];
            if (minmax && (ins == FMIN || ins == FMAX || ins == FCLAMP)) swaps++;
            if (domain && l == 6 && (ins == SQRT || ins == RSQRT || ins == LOG2)) {
                int k = 0;
                while (k < ntypes && types[k] != w[i + 1]) k++;
                if (k == ntypes) {
                    if (ntypes == MAX_TYPES) return NULL;
                    types[ntypes++] = w[i + 1];
                }
                clamps++;
            }
        }
        i += l;
    }
    if (!glsl || !fn_at || (!swaps && !clamps)) return NULL;
    uint64_t total = n + (uint64_t)ntypes * 3 + clamps * 7;
    uint32_t *o = malloc(total * 4), *p = o;
    if (!o) return NULL;
    for (int k = 0; k < ntypes; k++) zeros[k] = bound++;
    memcpy(p, w, 5 * 4), p[3] = bound + (uint32_t)clamps, p += 5;
    memcpy(p, w + 5, (fn_at - 5) * 4), p += fn_at - 5;
    for (int k = 0; k < ntypes; k++) *p++ = 3u << 16 | OP_CONSTANT_NULL, *p++ = types[k], *p++ = zeros[k];
    for (uint64_t i = fn_at; i < n;) {
        uint32_t op = w[i] & 0xffff, l = w[i] >> 16;
        if (op == OP_EXT_INST && l >= 5 && w[i + 3] == glsl) {
            uint32_t ins = w[i + 4];
            if (domain && l == 6 && (ins == SQRT || ins == RSQRT || ins == LOG2)) {
                int k = 0;
                while (types[k] != w[i + 1]) k++;
                uint32_t safe = bound++;
                *p++ = 7u << 16 | OP_EXT_INST, *p++ = w[i + 1], *p++ = safe, *p++ = glsl, *p++ = NMAX, *p++ = w[i + 5],
                *p++ = zeros[k];
                memcpy(p, w + i, 5 * 4), p[5] = safe, p += 6;
                i += l;
                continue;
            }
            memcpy(p, w + i, l * 4);
            if (minmax) p[4] = ins == FMIN ? NMIN : ins == FMAX ? NMAX : ins == FCLAMP ? NCLAMP : ins;
            p += l, i += l;
            continue;
        }
        memcpy(p, w + i, l * 4), p += l, i += l;
    }
    *out_n = (uint64_t)(p - o);
    static volatile int logged;
    if (!logged) logged = 1, rt_log("vk_pipeline: first shader made NaN-safe: %llu min/max/clamp, %llu sqrt/rsqrt/log2",
                                    (unsigned long long)(minmax ? swaps : 0), (unsigned long long)clamps);
    return o;
}

static VkShaderModule make_module(const uint32_t *w, uint64_t words) {
    uint64_t fixed_n = 0, safe_n = 0;
    uint32_t *fixed = spirv_fixup(w, words, &fixed_n);
    if (fixed) w = fixed, words = fixed_n;
    uint32_t *nan_safe = snap_spirv_nan_safe(w, words, &safe_n);
    if (nan_safe) w = nan_safe, words = safe_n;
    VkShaderModuleCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO, .codeSize = (size_t)words * 4, .pCode = w};
    VkShaderModule m = VK_NULL_HANDLE;
    VkResult r = vkCreateShaderModule(P.device, &ci, NULL, &m);
    free(nan_safe);
    free(fixed);
    return r == VK_SUCCESS ? m : VK_NULL_HANDLE;
}'''


def edits():
    return {
        'runtime/vk_pipeline.c': [(BEFORE, AFTER)],
        'runtime/cfg.c': [('"SPIN", "SPIN_HANDOFF_US",', '"SPIN", "SPIN_HANDOFF_US", "SPIRV_DOMAIN_CLAMP", "SPIRV_NMINMAX",')],
    }
