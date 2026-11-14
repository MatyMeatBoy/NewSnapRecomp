/* Included inside vk_dlaa.c, after its private scene/camera types. */
static struct {
    SnapFsrSdk *probe;
    SnapFsrProvider providers[32];
    uint32_t count;
    int tried;
    uint64_t generation;
    struct { VkImage output; SnapFsrSdk *sdk; uint64_t generation, after; int retired, hdr, ml; } entries[24];
} snap_sdk;

static SnapFsrDevice snap_fsr_device(void) {
    const VkCtx *c=vk_ctx();
    return (SnapFsrDevice){c->device,c->phys,vkGetDeviceProcAddr};
}

static uint64_t snap_fsr_provider(int ml) {
    if(!snap_sdk.tried) {
        snap_sdk.tried=1; snap_sdk.probe=snap_fsr_sdk_open();
        SnapFsrDevice d=snap_fsr_device();
        snap_sdk.count=snap_fsr_sdk_query(snap_sdk.probe,&d,snap_sdk.providers,32);
        for(uint32_t i=0;i<snap_sdk.count;i++) rt_log("Snap official FSR SDK provider: %s (%016llx)",snap_sdk.providers[i].name,(unsigned long long)snap_sdk.providers[i].id);
    }
    for(uint32_t i=0;i<snap_sdk.count;i++) {
        const char *name=snap_sdk.providers[i].name;
        /* SDK API guide also documents driver-provided names such as "FSR 4.1.2 *". */
        if(!strncmp(name,"FSR ",4)) name+=4;
        if(!strncmp(name,ml?"4.":"3.1.",ml?2:4)) return snap_sdk.providers[i].id;
    }
    return 0;
}

static int snap_fsr_runtime_available(int ml) {
    return (!ml || snap_fsr_sdk_int8_enabled) && snap_fsr_provider(ml)!=0;
}

static void snap_fsr_runtime_sweep(int all) {
    uint64_t done=vk_sync_fence_done();
    for(unsigned i=0;i<24;i++) if(snap_sdk.entries[i].sdk && (all || (snap_sdk.entries[i].retired && snap_sdk.entries[i].after<=done))) {
        snap_fsr_sdk_close(snap_sdk.entries[i].sdk); memset(&snap_sdk.entries[i],0,sizeof snap_sdk.entries[i]);
    }
}

static void snap_fsr_runtime_retire(VkImage output) {
    uint64_t issued=vk_sync_issued();
    for(unsigned i=0;i<24;i++) if(snap_sdk.entries[i].sdk && snap_sdk.entries[i].output==output && !snap_sdk.entries[i].retired) {
        snap_sdk.entries[i].retired=1;
        if(issued>snap_sdk.entries[i].after) snap_sdk.entries[i].after=issued;
    }
}

static void snap_fsr_runtime_shutdown(void) {
    snap_fsr_runtime_sweep(1); snap_fsr_sdk_close(snap_sdk.probe); memset(&snap_sdk,0,sizeof snap_sdk);
}

static SnapFsrImage snap_fsr_target(const VkExecTarget *t,uint64_t generation) {
    return (SnapFsrImage){.image=t->image,.format=t->format,.layout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        .usage=t->img->usage,.width=t->width,.height=t->height,.samples=t->samples,.layers=t->img->layers,.mips=t->img->levels,.generation=generation};
}

static int snap_fsr_runtime_evaluate(VkCommandBuffer cb,const VkExecTarget *color,const VkExecTarget *depth,
    struct Size *e,float jx,float jy,float dt,int hdr,int reset,int ml,uint64_t fence) {
    /* The API creates its own image views; only complete, single-level 2D images are valid here. */
    if(!D.proj_ok || !isfinite(D.proj[5]) || D.proj[5]<=0 || !isfinite(D.proj[11]) || D.proj[11]<=0 ||
        !snap_fsr_runtime_available(ml) || !color->img || !depth->img || color->level || color->base_layer || depth->level || depth->base_layer ||
        color->img->layers!=1 || depth->img->layers!=1 || color->img->levels!=1 || depth->img->levels!=1) return 0;
    snap_fsr_runtime_sweep(0);
    unsigned slot=24;
    for(unsigned i=0;i<24;i++) if(snap_sdk.entries[i].sdk && !snap_sdk.entries[i].retired && snap_sdk.entries[i].output==e->out) {
        if(snap_sdk.entries[i].hdr==hdr && snap_sdk.entries[i].ml==ml) slot=i;
        else snap_fsr_runtime_retire(e->out);
        break;
    }
    if(slot==24) {
        for(unsigned i=0;i<24;i++) if(!snap_sdk.entries[i].sdk) { slot=i;break; }
        if(slot==24) return 0; /* bounded retirement queue: keep native output rather than stall every frame */
        SnapFsrSdk *sdk=snap_fsr_sdk_open(); if(!sdk) return 0;
        uint64_t generation=++snap_sdk.generation;
        SnapFsrConfig c={.render_width=e->w,.render_height=e->h,.output_width=e->ow,.output_height=e->oh,
            .generation=generation,.hdr=hdr,.inverted_depth=1,.infinite_depth=1,.auto_exposure=1,.device_contract_verified=1};
        SnapFsrDevice d=snap_fsr_device();
        if(!snap_fsr_sdk_create(sdk,&d,&c,snap_fsr_provider(ml))) { snap_fsr_sdk_close(sdk); return 0; }
        snap_sdk.entries[slot].sdk=sdk; snap_sdk.entries[slot].output=e->out;
        snap_sdk.entries[slot].generation=generation; snap_sdk.entries[slot].hdr=hdr; snap_sdk.entries[slot].ml=ml;
        rt_log("Snap official FSR %s context: %ux%u -> %ux%u reverse-infinite Z",ml?"4":"3.1",e->w,e->h,e->ow,e->oh);
        uint64_t total,aliasable;
        if(snap_fsr_sdk_memory_usage(sdk,&total,&aliasable))
            rt_log("Snap official FSR context memory query: total=%llu bytes, aliasable=%llu bytes (SDK effect only)",(unsigned long long)total,(unsigned long long)aliasable);
        else rt_log("Snap official FSR context memory query: unknown (provider query unavailable)");
    }
    uint64_t generation=snap_sdk.entries[slot].generation;
    SnapFsrFrame f={.command_buffer=cb,.color=snap_fsr_target(color,generation),.depth=snap_fsr_target(depth,generation),
        .motion={.image=e->mv,.format=VK_FORMAT_R16G16_SFLOAT,.layout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            .usage=VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT,.width=e->w,.height=e->h,.samples=1,.layers=1,.mips=1,.generation=generation},
        .output={.image=e->out,.format=VK_FORMAT_R16G16B16A16_SFLOAT,.layout=VK_IMAGE_LAYOUT_GENERAL,
            .usage=VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT,.width=e->ow,.height=e->oh,.samples=1,.layers=1,.mips=1,.generation=generation},
        .jitter_x=jx,.jitter_y=jy,.motion_scale_x=1,.motion_scale_y=1,.delta_ms=dt,.pre_exposure=1,
        .camera_near=.01f,.camera_far=1000000,.meters_factor=1,.reset=reset,.scene_contract_verified=1};
    float unused_near,unused_far; camera_planes(&unused_near,&unused_far,&f.vertical_fov);
    f.camera_near=D.proj[11];
    /* Drain the asynchronous recorder before direct SDK Vulkan commands and restore GENERAL after them. */
    rec_drain();
    VkImageMemoryBarrier barriers[3];
    const SnapFsrImage *inputs[]={&f.color,&f.depth,&f.motion};
    for(unsigned i=0;i<3;i++) barriers[i]=(VkImageMemoryBarrier){.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .srcAccessMask=VK_ACCESS_MEMORY_WRITE_BIT|VK_ACCESS_MEMORY_READ_BIT,.dstAccessMask=VK_ACCESS_SHADER_READ_BIT,
        .oldLayout=VK_IMAGE_LAYOUT_GENERAL,.newLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        .srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.image=inputs[i]->image,
        .subresourceRange={i==1?VK_IMAGE_ASPECT_DEPTH_BIT:VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1}};
    vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,0,NULL,0,NULL,3,barriers);
    rec_drain();
    /* issued excludes the submission currently being recorded: retain through its explicit fence too. */
    snap_sdk.entries[slot].after=fence;
    int ok=snap_fsr_sdk_dispatch(snap_sdk.entries[slot].sdk,&f);
    if(ok) snap_fg_prepare(cb,&f,e->w,e->h,e->ow,e->oh); /* FG-01: inputs still SHADER_READ_ONLY here */
    for(unsigned i=0;i<3;i++) {
        barriers[i].oldLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;barriers[i].newLayout=VK_IMAGE_LAYOUT_GENERAL;
        barriers[i].srcAccessMask=VK_ACCESS_SHADER_READ_BIT;barriers[i].dstAccessMask=VK_ACCESS_MEMORY_READ_BIT|VK_ACCESS_MEMORY_WRITE_BIT;
    }
    vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,0,0,NULL,0,NULL,3,barriers);
    /* SDK bound its own descriptors/pipeline; the donor recorder must rebind its cached state. */
    vk_exec_draw_new_cb();
    return ok;
}
