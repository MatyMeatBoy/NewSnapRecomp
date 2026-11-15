#include "smaa_common.glsl"
layout(binding = 0) uniform sampler2D edgesTex;
layout(binding = 1) uniform sampler2D areaTex;     // bilinear
layout(binding = 2) uniform sampler2D searchTex;   // point
layout(binding = 3, rgba8) uniform writeonly image2D weightsOut;
void main() {
    vec2 uv;
    ivec2 p = smaa_pixel(uv);
    if (smaa_outside(p)) return;
    vec2 pixcoord;
    vec4 offset[3];
    SMAABlendingWeightCalculationVS(uv, pixcoord, offset);
    imageStore(weightsOut, p, SMAABlendingWeightCalculationPS(uv, pixcoord, offset, edgesTex, areaTex, searchTex, vec4(0.0)));
}
