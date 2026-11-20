"""Move regenerable shader metadata persistence off the live translation path."""


def edits():
    return {'runtime/gfx_shader.c': [
        ('#include "platform/platform.h"',
         '#include "platform/platform.h"\n#include "snap_shader_cache_io.h"'),
        ('    plat_file_write_atomic(p, f, sizeof f);',
         '    snap_shader_cache_write(p, f, sizeof f);'),
        ('    plat_file_write_atomic(p, buf, n);',
         '    snap_shader_cache_write(p, buf, n);'),
        ('void gfx_shader_record_flush(int force) {',
         'void gfx_shader_record_flush(int force) {\n    snap_shader_cache_flush();'),
        ('void gfx_shader_drop_memory(void) {',
         'void gfx_shader_drop_memory(void) {\n    snap_shader_cache_flush();'),
        ('void gfx_shader_prewarm(const uint8_t (*iids)[32], size_t n, const GfxShader **out, int threads, int procs) {',
         'void gfx_shader_prewarm(const uint8_t (*iids)[32], size_t n, const GfxShader **out, int threads, int procs) {\n'
         '    snap_shader_cache_flush();'),
        ('    free(w.other);\n}', '    free(w.other);\n    snap_shader_cache_flush();\n}'),
        ("    RecHeader h = {{'A', 'C', 'S', 'P', 'R', 'P'}, PRP_VERSION, PRP_REC};",
         "    snap_shader_cache_flush(); // standalone preparation: metadata precedes its completion marker\n"
         "    RecHeader h = {{'A', 'C', 'S', 'P', 'R', 'P'}, PRP_VERSION, PRP_REC};"),
    ]}
