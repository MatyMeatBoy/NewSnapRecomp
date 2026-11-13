// Snap 2.0.1 main ddb900ff04a912ed42430508389853cfaf1accce only.
// Called before main+0x5cc0b0's original load. Select the engine's existing
// render graph/resource family, never resize a Vulkan image or the display.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "cfg.h"
#include "host.h"

void snap_render_select(Cpu *c) {
    static int warned_choice, warned_memory;
    static unsigned trace_lines;
    static uint32_t last_before = UINT32_MAX, last_after = UINT32_MAX, last_mode = UINT32_MAX;
    const char *choice = cfg_value("AC_RENDER_SCALE");
    const char *trace = getenv("NEWSNAP_RENDER_TRACE");
    int tracing = trace && !strcmp(trace, "1");
    int selected = -1;
    if (!choice || !strcmp(choice, "game")) {
        if (!tracing) return;  // default: no guest reads or writes
    } else {
        static const char *options[] = {"100", "90", "80", "70", "60", "50"};
        for (int i = 0; i < 6; i++) if (!strcmp(choice, options[i])) selected = i;
        if (selected < 0) {
            if (!warned_choice) {
                warned_choice = 1;
                rt_log("snap render: unsupported AC_RENDER_SCALE=%s; supported: game, 50, 60, 70, 80, 90, 100; keeping the game's level", choice);
            }
            return;
        }
    }
    // The verified instruction dereferences x0+0xce8. Validate the two fields
    // before adding a host write; never thaw memory or change permissions here.
    uint64_t object = c->x[0];
    RtMemoryInfo m;
    if (!object || object > UINT64_MAX - 0xcf0 ||
        mem_query(object + 0xce8, &m) || (m.perm & 3) != 3 ||
        object + 0xce8 < m.base || m.size < 8 || object + 0xce8 - m.base > m.size - 8) {
        if (!warned_memory) {
            warned_memory = 1;
            rt_log("snap render: renderer fields are not writable guest memory; keeping the game's level");
        }
        return;
    }
    uint32_t before, mode;
    memcpy(&before, (void *)(uintptr_t)(object + 0xce8), 4);
    memcpy(&mode, (void *)(uintptr_t)(object + 0xcec), 4);
    if (before > 5 || mode > 1) {
        if (!warned_memory) {
            warned_memory = 1;
            rt_log("snap render: renderer level/mode outside the verified 0..5/0..1 contract; keeping the game's level");
        }
        return;
    }
    uint32_t after = selected < 0 ? before : (uint32_t)selected;
    if (selected >= 0) memcpy((void *)(uintptr_t)(object + 0xce8), &after, 4);
    if (tracing && trace_lines < 64 &&
        (trace_lines == 0 || before != last_before || after != last_after || mode != last_mode)) {
        unsigned width = mode ? 1280 : 1920, height = mode ? 720 : 1080;
        // Same float table and truncation as the original engine's parameters.
        static const float factors[] = {1.0f, 0.9f, 0.8f, 0.7f, 0.6f, 0.5f};
        unsigned scene_w = width - (width / 10) * after;
        unsigned scene_h = (unsigned)((float)height * factors[after]);
        rt_log("snap render: native level %u -> %u, %s, engine scene %ux%u, output %ux%u (configuration, not GPU measurement)",
               before, after, mode ? "handheld" : "docked", scene_w, scene_h, width, height);
        last_before = before; last_after = after; last_mode = mode; trace_lines++;
    }
}
