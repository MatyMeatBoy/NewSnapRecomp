// Snap 2.0.1 camera c3: measured on consecutive first-course frames.
// Stored matrices are column-major: view, inverse view, projection,
// inverse projection, view-projection, inverse view-projection.
#pragma once
#include <math.h>
#include <stddef.h>

#ifdef NEWSNAP_TEMPORAL_CONFIG
#include <string.h>
#include "cfg.h"
static inline unsigned snap_temporal_percent(void) {
    const char *backend=cfg_upscaling();
    if(strcmp(backend,"off")) {
        const char *quality=cfg_upscaling_quality();
        return !strcmp(quality,"quality")?70:!strcmp(quality,"balanced")?60:
               !strcmp(quality,"performance")?50:100;
    }
    const char *scale=cfg_value("AC_RENDER_SCALE");
    return !strcmp(scale,"50")?50:!strcmp(scale,"60")?60:!strcmp(scale,"70")?70:
           !strcmp(scale,"80")?80:!strcmp(scale,"90")?90:100;
}
static inline void snap_temporal_output(unsigned out[2]) {
    int handheld=!strcmp(cfg_value("AC_OPERATION_MODE"),"handheld");
    out[0]=handheld?1280:1920;out[1]=handheld?720:1080;
}
#endif

static inline void snap_camera_matrix(const float *source, float *out) {
    for (int r=0;r<4;r++) for (int c=0;c<4;c++) out[r*4+c]=source[c*4+r];
}
static inline int snap_matrix_product(const float *a,const float *b,const float *expected) {
    for(int r=0;r<4;r++) for(int c=0;c<4;c++) {
        double v=0, magnitude=0;
        for(int k=0;k<4;k++) { double term=(double)a[r*4+k]*b[k*4+c];v+=term;magnitude+=fabs(term); }
        double target=expected?expected[r*4+c]:(r==c);
        if(!isfinite(v)||!isfinite(target)||fabs(v-target)>0.00015*(1+magnitude+fabs(target)))return 0;
    }
    return 1;
}
// Normalized row-major layout consumed by the portable reprojection code.
// Reject unknown camera blocks instead of accumulating incorrect history.
static inline int snap_camera_decode(const float *raw,size_t bytes,float out[64]) {
    if(bytes!=0x2e8)return 0;
    float inverse_projection[16], inverse_vp[16];
    snap_camera_matrix(raw,out);
    snap_camera_matrix(raw+16,out+48);
    snap_camera_matrix(raw+32,out+16);
    snap_camera_matrix(raw+48,inverse_projection);
    snap_camera_matrix(raw+64,out+32);
    snap_camera_matrix(raw+80,inverse_vp);
    for(int i=0;i<64;i++)if(!isfinite(out[i]))return 0;
    const float *p=out+16;
    // Verified right-handed reversed infinite-Z projection, near=0.01.
    if(p[0]<=0||p[5]<=0||fabsf(p[10])>1e-6f||fabsf(p[14]+1)>1e-6f||
       p[11]<=0||fabsf(p[15])>1e-6f)return 0;
    return snap_matrix_product(out,out+48,0)&&snap_matrix_product(out+16,inverse_projection,0)&&
           snap_matrix_product(out+16,out,out+32)&&snap_matrix_product(out+32,inverse_vp,0);
}
