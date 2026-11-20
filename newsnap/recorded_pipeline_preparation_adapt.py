"""Warm recorded whole graphics pipelines in an isolated Vulkan process."""


SAVE_START = '''    if (!P.ready || !P.cache || !P.cache_path[0]) return;
    // Not under P.lock:'''
SAVE_BODY = '''    if (vkGetPipelineCacheData(P.device, P.cache, &size, NULL) == VK_SUCCESS && size && (data = malloc(size)) &&
        vkGetPipelineCacheData(P.device, P.cache, &size, data) == VK_SUCCESS) {
        if (!plat_file_write_atomic(P.cache_path, data, size)) rt_log("vk_pipeline: cannot write %s", P.cache_path);
    }
    free(data);
    plat_mutex_unlock(&save_lock);
}'''


def edits():
    return {
        'runtime/main.c': [
            ('    if (!strcmp(mode, "--prepare-shaders")) return vk_pipeline_prepare_shaders();',
             '    if (!strcmp(mode, "--prepare-shaders")) return vk_pipeline_prepare_shaders();\n'
             '    if (!strcmp(mode, "--prepare-recorded-pipelines")) return snap_prepare_recorded_pipelines();'),
        ],
        'runtime/host.h': [
            ('int vk_pipeline_prepare_shaders(void);',
             'int vk_pipeline_prepare_shaders(void);\nint snap_prepare_recorded_pipelines(void);'),
        ],
        'runtime/vk_pipeline.c': [
            ('    int warm;                          // vk_pipeline_prewarm owns the file (prebuild_start leaves it)',
             '    int warm;                          // vk_pipeline_prewarm owns the file (prebuild_start leaves it)\n'
             '    int read_only;                     // standalone preparation consumes existing recordings only'),
            ('    if (!A.on || !K.path[0]) return;', '    if (!A.on || !K.path[0] || K.read_only) return;'),
            ('    if (!A.on || !P.cache_path[0]) return;',
             '    if (!A.on || !P.cache_path[0] || (K.read_only && P.gpl)) return;'),
            ('    gfx_shader_record_at(K.path);   // shader-answers.bin next to it (gfx_shader.c)',
             '    if (!K.read_only) gfx_shader_record_at(K.path);'),
            ('    if (!K.header_ok && K.file_n) {',
             '    if (!K.read_only && !K.header_ok && K.file_n) {'),
            ('void vk_pipeline_prewarm(void) {', 'static void prewarm_recorded(int boot) {'),
            ('        if (ensure_init()) lb_start(pr_hist, fs_hist);',
             '        if (boot && ensure_init()) lb_start(pr_hist, fs_hist);'),
            ('        if (P.ready) lb_start(pr_hist, fs_hist);',
             '        if (boot && P.ready) lb_start(pr_hist, fs_hist);'),
            ('    lb_start(pr_hist, fs_hist);\n}',
             '    if (boot) lb_start(pr_hist, fs_hist);\n}\n\n'
             'void vk_pipeline_prewarm(void) { prewarm_recorded(1); }'),
            (SAVE_START, '    (void)save_pipeline_cache();\n}\n\n'
             'static int save_pipeline_cache(void) {\n'
             '    if (!P.ready || !P.cache || !P.cache_path[0]) return 0;\n'
             '    // Not under P.lock:'),
            ('void vk_pipeline_save(void) {', 'static int save_pipeline_cache(void);\n\nvoid vk_pipeline_save(void) {'),
            ('        plat_mutex_unlock(&save_lock);\n        return;\n    }\n    size_t size = 0;',
             '        plat_mutex_unlock(&save_lock);\n        return 0;\n    }\n    size_t size = 0;'),
            (SAVE_BODY, '''    int ok = vkGetPipelineCacheData(P.device, P.cache, &size, NULL) == VK_SUCCESS && size &&
             (data = malloc(size)) && vkGetPipelineCacheData(P.device, P.cache, &size, data) == VK_SUCCESS &&
             plat_file_write_atomic(P.cache_path, data, size);
    if (!ok) rt_log("vk_pipeline: cannot save %s", P.cache_path);
    free(data);
    plat_mutex_unlock(&save_lock);
    return ok;
}

int snap_prepare_recorded_pipelines(void) {
    vk_pipeline_async_enable();
    if (!A.on || !cfg_bool("AC_PIPE_PREBUILD")) return 0;
    K.read_only = K.warm = 1;
    if (!ensure_init()) return 1;
    if (P.gpl || !K.file_n) return 0;
    prewarm_recorded(0);
    if (!P.stats.graphics) return P.stats.failures != 0;
    if (!save_pipeline_cache()) return 1;
    puts("prepare-shaders: recorded graphics cache saved");
    return 0;
}'''),
        ],
    }
