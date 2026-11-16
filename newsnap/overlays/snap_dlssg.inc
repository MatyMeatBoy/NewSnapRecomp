// FG-DLSS (snap_dlssg.h): included at the end of vk_dlaa.c, for its NGX core (N), parameter accessors and camera.
// Parameter names: NVIDIA/DLSS v310.9.16 include/nvsdk_ngx_defs_dlssg.h and nvsdk_ngx_helpers_dlssg_vk.h.
#include "snap_dlssg.h"

#define NGX_FEATURE_FRAME_GENERATION 11

double snap_dlssg_c2p[16];   // mv_pass: this frame's clip space to last frame's (previous view-projection x inverse)
int snap_dlssg_c2p_ok;

static PlatMutex ngx_lock = PLAT_MUTEX_INIT;
void snap_ngx_lock(void) { plat_mutex_lock(&ngx_lock); }
void snap_ngx_unlock(void) { plat_mutex_unlock(&ngx_lock); }

static struct {
    NgxHandle *feat;
    NgxParam *params;
    uint32_t w, h, rw, rh;
    VkFormat fmt;
    int checked, available, fails, frames;
} FG;

static void transpose16(const double m[16], float o[16]) {
    for (int r = 0; r < 4; r++)
        for (int k = 0; k < 4; k++) o[r * 4 + k] = (float)m[k * 4 + r];
}

void snap_dlssg_camera(SnapDlssgCamera *out) {
    static const double identity[16] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    double p[16], pi[16], c2p[16], p2c[16];
    memset(out, 0, sizeof *out);
    for (int i = 0; i < 16; i++) p[i] = D.proj_ok ? D.proj[i] : identity[i];
    if (!inv4(p, pi)) memcpy(p, identity, sizeof p), memcpy(pi, identity, sizeof pi);
    memcpy(c2p, snap_dlssg_c2p_ok ? snap_dlssg_c2p : identity, sizeof c2p);
    if (!inv4(c2p, p2c)) memcpy(c2p, identity, sizeof c2p), memcpy(p2c, identity, sizeof p2c);
    transpose16(p, out->view_to_clip), transpose16(pi, out->clip_to_view);
    transpose16(c2p, out->clip_to_prev), transpose16(p2c, out->prev_to_clip);
    camera_planes(&out->near_z, &out->far_z, &out->fov_y);
}

static int dlssg_fail(const char *what, NgxResult r) {
    if (FG.fails++ < 4) rt_log("frame generation: DLSS %s failed (%08x)%s", what, (unsigned)r, FG.fails == 4 ? ": off" : "");
    return 0;
}

static int dlssg_available(void) {
    if (FG.checked) return FG.available;
    FG.checked = 1;
    if (!N.inited) {
        rt_log("frame generation: DLSS needs NVIDIA DLSS as the upscaler on an RTX 40 or 50 series GPU (NGX is not up)");
        return 0;
    }
    NgxParam *caps = NULL;
    int avail = 0, driver = 0, init = 0;
    unsigned major = 0, minor = 0, multi = 0;
    if (NGX_OK(N.caps(&caps)) && caps) {
        p_geti(caps, "FrameGeneration.Available", &avail);
        p_geti(caps, "FrameGeneration.NeedsUpdatedDriver", &driver);
        p_geti(caps, "FrameGeneration.FeatureInitResult", &init);
        p_getu(caps, "FrameGeneration.MinDriverVersionMajor", &major);
        p_getu(caps, "FrameGeneration.MinDriverVersionMinor", &minor);
        p_getu(caps, "DLSSG.MultiFrameCountMax", &multi);
    }
    FG.available = avail != 0;
    if (FG.available) rt_log("frame generation: DLSS available (NGX; multi-frame limit %u, one generated frame is used)", multi);
    else
        rt_log("frame generation: DLSS NOT available (init result %08x%s; minimum driver %u.%u). It needs an RTX 40 or 50 "
               "series GPU and nvngx_dlssg.dll next to newsnap.exe", (unsigned)init, driver ? ", the driver needs an update" : "",
               major, minor);
    return FG.available;
}

int snap_dlssg_generate(VkCommandBuffer cb, const SnapDlssgFrame *f) {
    if (FG.fails > 3) return 0;
    int ok = 0;
    snap_ngx_lock();
    if (!dlssg_available()) goto out;
    if (!FG.params && (!NGX_OK(N.alloc_params(&FG.params)) || !FG.params)) {
        FG.params = NULL;
        dlssg_fail("parameter allocation", 0);
        goto out;
    }
    NgxParam *p = FG.params;
    if (FG.feat && (FG.w != f->backbuffer.w || FG.h != f->backbuffer.h || FG.rw != f->depth.w || FG.rh != f->depth.h ||
                    FG.fmt != f->backbuffer.format)) {
        vk_queue_lock();
        vkDeviceWaitIdle(vk_ctx()->device);
        vk_queue_unlock();
        N.release(FG.feat);
        FG.feat = NULL;
    }
    if (!FG.feat) {
        p_setu(p, "CreationNodeMask", 1);
        p_setu(p, "VisibilityNodeMask", 1);
        p_setu(p, "Width", f->backbuffer.w);
        p_setu(p, "Height", f->backbuffer.h);
        p_setu(p, "DLSSG.Width", f->backbuffer.w);
        p_setu(p, "DLSSG.Height", f->backbuffer.h);
        p_setu(p, "DLSSG.BackbufferFormat", (unsigned)f->backbuffer.format);   // a VkFormat on Vulkan
        p_setu(p, "DLSSG.InternalWidth", f->depth.w);
        p_setu(p, "DLSSG.InternalHeight", f->depth.h);
        p_setu(p, "DLSSG.DynamicResolution", 0);
        uint64_t t0 = plat_now_ns();
        NgxResult r = N.create(cb, NGX_FEATURE_FRAME_GENERATION, p, &FG.feat);
        if (!NGX_OK(r) || !FG.feat) {
            FG.feat = NULL;
            dlssg_fail("feature creation", r);
            goto out;
        }
        FG.w = f->backbuffer.w, FG.h = f->backbuffer.h, FG.rw = f->depth.w, FG.rh = f->depth.h, FG.fmt = f->backbuffer.format;
        rt_log("frame generation: DLSS feature %ux%u (depth and motion %ux%u, format %d), in %.1f ms", FG.w, FG.h, FG.rw,
               FG.rh, (int)FG.fmt, (plat_now_ns() - t0) / 1e6);
    }
    NgxResourceVK bb = res_image(f->backbuffer.view, f->backbuffer.image, f->backbuffer.format, f->backbuffer.w,
                                 f->backbuffer.h, VK_IMAGE_ASPECT_COLOR_BIT, 0);
    NgxResourceVK mv = res_image(f->mv.view, f->mv.image, f->mv.format, f->mv.w, f->mv.h, VK_IMAGE_ASPECT_COLOR_BIT, 0);
    NgxResourceVK z = res_image(f->depth.view, f->depth.image, f->depth.format, f->depth.w, f->depth.h,
                                VK_IMAGE_ASPECT_DEPTH_BIT, 0);
    NgxResourceVK hud = res_image(f->hudless.view, f->hudless.image, f->hudless.format, f->hudless.w, f->hudless.h,
                                  VK_IMAGE_ASPECT_COLOR_BIT, 0);
    NgxResourceVK o = res_image(f->out.view, f->out.image, f->out.format, f->out.w, f->out.h, VK_IMAGE_ASPECT_COLOR_BIT, 1);
    p_setp(p, "DLSSG.Backbuffer", &bb);
    p_setp(p, "DLSSG.MVecs", &mv);
    p_setp(p, "DLSSG.Depth", &z);
    p_setp(p, "DLSSG.HUDLess", f->hudless.image ? &hud : NULL);   // the table keeps what it was given: cleared when absent
    p_setp(p, "DLSSG.UI", NULL);
    p_setp(p, "DLSSG.UIAlpha", NULL);
    p_setp(p, "DLSSG.BidirectionalDistortionField", NULL);
    p_setp(p, "DLSSG.OutputInterpolated", &o);
    NgxResourceVK real = res_image(f->real.view, f->real.image, f->real.format, f->real.w, f->real.h, VK_IMAGE_ASPECT_COLOR_BIT, 1);
    p_setp(p, "DLSSG.OutputReal", f->real.image ? &real : NULL);
    p_setp(p, "DLSSG.OutputDisableInterpolation", NULL);
    p_setu(p, "DLSSG.Reset", f->reset ? 1 : 0);
    p_setu(p, "DLSSG.DepthInverted", 1);          // Snap: 1.0 is near (the same depth DLSS Super Resolution takes)
    p_setf(p, "DLSSG.MvecScaleX", 1.0f);          // render pixels, this frame to the last, as given to Super Resolution
    p_setf(p, "DLSSG.MvecScaleY", 1.0f);
    p_setu(p, "DLSSG.ColorBuffersHDR", 0);
    p_setu(p, "DLSSG.CameraMotionIncluded", 1);
    p_setu(p, "DLSSG.MvecDilated", 0);
    p_setu(p, "DLSSG.MvecJittered", 0);
    p_setu(p, "DLSSG.NotRenderingGameFrames", 0);
    p_setu(p, "DLSSG.OrthoProjection", 0);
    p_setu(p, "DLSSG.MenuDetectionEnabled", 0);
    p_setu(p, "DLSSG.MultiFrameCount", 1);
    p_setu(p, "DLSSG.MultiFrameIndex", 1);
    p_setp(p, "DLSSG.CameraViewToClip", (void *)f->cam.view_to_clip);
    p_setp(p, "DLSSG.ClipToCameraView", (void *)f->cam.clip_to_view);
    p_setp(p, "DLSSG.ClipToPrevClip", (void *)f->cam.clip_to_prev);
    p_setp(p, "DLSSG.PrevClipToClip", (void *)f->cam.prev_to_clip);
    static const float lens[16] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    p_setp(p, "DLSSG.ClipToLensClip", (void *)lens);
    static const char *const axis[3] = {"X", "Y", "Z"};
    for (int a = 0; a < 3; a++) {
        char name[40];
        snprintf(name, sizeof name, "DLSSG.CameraPos%s", axis[a]), p_setf(p, name, f->cam.pos[a]);
        snprintf(name, sizeof name, "DLSSG.CameraUp%s", axis[a]), p_setf(p, name, f->cam.up[a]);
        snprintf(name, sizeof name, "DLSSG.CameraRight%s", axis[a]), p_setf(p, name, f->cam.right[a]);
        snprintf(name, sizeof name, "DLSSG.CameraFwd%s", axis[a]), p_setf(p, name, f->cam.fwd[a]);
    }
    p_setf(p, "DLSSG.CameraNear", f->cam.near_z);
    p_setf(p, "DLSSG.CameraFar", f->cam.far_z);
    p_setf(p, "DLSSG.CameraFOV", f->cam.fov_y);   // radians
    p_setf(p, "DLSSG.CameraAspectRatio", f->backbuffer.h ? (float)f->backbuffer.w / (float)f->backbuffer.h : 1.0f);
    p_setf(p, "DLSSG.JitterOffsetX", f->depth.w ? 2.0f * f->jitter_x / (float)f->depth.w : 0.0f);   // clip space
    p_setf(p, "DLSSG.JitterOffsetY", f->depth.h ? -2.0f * f->jitter_y / (float)f->depth.h : 0.0f);
    p_setf(p, "DLSSG.CameraPinholeOffsetX", 0.0f);
    p_setf(p, "DLSSG.CameraPinholeOffsetY", 0.0f);
    NgxResult r = N.evaluate(cb, FG.feat, p, NULL);
    if (!NGX_OK(r)) {
        dlssg_fail("evaluation", r);
        goto out;
    }
    FG.frames++;
    ok = 1;
out:
    snap_ngx_unlock();
    return ok;
}

void snap_dlssg_release(void) {
    snap_ngx_lock();
    if (FG.feat) N.release(FG.feat), FG.feat = NULL;
    if (FG.params && N.destroy_params) N.destroy_params(FG.params), FG.params = NULL;
    snap_ngx_unlock();
}
