#include "smaa_common.glsl"
layout(binding = 0) uniform sampler2D colorTex;   // the tonemapped picture, gamma-encoded (UNORM view)
layout(binding = 1, rgba8) uniform writeonly image2D edgesOut;
void main() {
    vec2 uv;
    ivec2 p = smaa_pixel(uv);
    if (smaa_outside(p)) return;
    vec4 offset[3];
    SMAAEdgeDetectionVS(uv, offset);
    imageStore(edgesOut, p, vec4(SMAALumaEdgeDetectionPS(uv, offset, colorTex), 0.0, 0.0));
}
