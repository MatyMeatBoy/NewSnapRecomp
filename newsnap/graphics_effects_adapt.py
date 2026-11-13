"""Preserve graphics storage writes while retaining async pure-draw pipelines.

Pending translation has no reflection yet. Resolve it before deciding whether a
draw may be discarded; SSBO/image stores must execute even for a recent target.
"""

SUPPORT = r'''
static int snap_shader_writes(const GfxShader *shader) {
    if (!shader) return 0;
    const GfxShaderRes *resources;
    int count = gfx_shader_resources(shader, GFX_RES_SSBO, &resources);
    for (int i = 0; i < count; i++)
        if (resources[i].flags & 1) return 1;
    count = gfx_shader_resources(shader, GFX_RES_IMG, &resources);
    for (int i = 0; i < count; i++)
        if (resources[i].flags & 4) return 1;
    return 0;
}

static VkPipeline snap_required_pipeline(const VkPipeState *state, const VkPipeInfo **info, int *pending) {
    VkPipeline pipeline;
    // Reuse the donor's promotion/condition wait, including an entry already
    // building asynchronously. A time slice expiring is not a compile failure
    // and must never discard an authoritative storage write.
    do {
        pipeline = vk_pipeline_graphics_async(state, info, pending, ONESHOT_WAIT_MS);
    } while (*pending);
    // NULL with pending=0 is an actual creation failure; keep donor reporting.
    return pipeline;
}

'''


def edits():
    return {'runtime/vk_exec_draw.c': [
        ('// Pass, shaders, pipeline, fixed state and resources for a draw. 0: the draw is skipped.',
         SUPPORT + '// Pass, shaders, pipeline, fixed state and resources for a draw. 0: the draw is skipped.'),
        ('    if (vs_wait || fs_wait) {\n'
         '        if (!(oneshot = !vk_exec_targets_recent(ex, skip >= 1))) return perf_count(PERF_CNT_SHADER_SKIP), 0;   // skipped until ready\n'
         '        perf_count(PERF_CNT_ONESHOT_WAIT);\n'
         '        if (vs_wait) vs = shader_for(ex, NVN_STAGE_VS, &has_vs, NULL, 1);\n'
         '        if (fs_wait) fs = shader_for(ex, NVN_STAGE_FS, &has_fs, NULL, 1);\n'
         '    }',
         '    // Until translation completes, storage effects are unknown.\n'
         '    // Recent colour/depth targets cannot establish that this draw is safe to skip.\n'
         '    if (vs_wait || fs_wait) {\n'
         '        oneshot = !vk_exec_targets_recent(ex, skip >= 1);\n'
         '        if (vs_wait) vs = shader_for(ex, NVN_STAGE_VS, &has_vs, NULL, 1);\n'
         '        if (fs_wait) fs = shader_for(ex, NVN_STAGE_FS, &has_fs, NULL, 1);\n'
         '    }'),
        ('    uint32_t fbl = feedback_prepare(ex, fs);',
         '    int storage_write = snap_shader_writes(vs) || snap_shader_writes(fs);\n'
         '    uint32_t fbl = feedback_prepare(ex, fs);'),
        ('    if (oneshot > 0) {\n        wait_ms = ONESHOT_WAIT_MS;',
         '    if (storage_write || oneshot > 0) {\n        wait_ms = ONESHOT_WAIT_MS;'),
        ('        p = vk_pipeline_graphics_async(&s, &info, &pending, wait_ms);',
         '        p = storage_write ? snap_required_pipeline(&s, &info, &pending)\n'
         '                          : vk_pipeline_graphics_async(&s, &info, &pending, wait_ms);'),
        ('        why = oneshot > 0 ? "one-shot, shader" : wait_ms ? "full-screen" : NULL;',
         '        why = storage_write ? "storage write" : oneshot > 0 ? "one-shot, shader" : wait_ms ? "full-screen" : NULL;'),
    ]}
