// AA-04: the official SMAA 1x (SMAA.hlsl, Jimenez et al., MIT) as compute passes for snap_smaa.c. Each pass file
// defines its preset (SMAA_PRESET_LOW / MEDIUM / HIGH / ULTRA) before including this.
#extension GL_GOOGLE_include_directive : require
layout(local_size_x = 8, local_size_y = 8) in;
layout(push_constant) uniform Metrics { vec4 metrics; } pc;   // 1/w, 1/h, w, h
#define SMAA_RT_METRICS pc.metrics
#define SMAA_GLSL_4 1
// Compute shaders cannot discard: the edge pass returns "no edge" instead, which is what a cleared target holds.
#define discard return vec2(0.0)
#include "SMAA.hlsl"
#undef discard

ivec2 smaa_pixel(out vec2 uv) {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    uv = (vec2(p) + 0.5) * pc.metrics.xy;
    return p;
}

bool smaa_outside(ivec2 p) { return any(greaterThanEqual(p, ivec2(pc.metrics.zw))); }
