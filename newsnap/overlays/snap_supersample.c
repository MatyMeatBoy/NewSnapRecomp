// Experimental Snap 2.0.1 docked engine resize (AC_SS_MODE=engine only, SS-02).
// Native settings are unchanged; handheld resizing is deliberately excluded.
// The original BL is replayed AFTER this helper by the generator.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "cfg.h"
#include "host.h"

static int readable_span(uint64_t address, uint64_t size, uint32_t permissions) {
    RtMemoryInfo memory;
    return size && address <= UINT64_MAX - (size - 1) &&
           !mem_query(address, &memory) && (memory.perm & permissions) == permissions &&
           address >= memory.base && memory.size >= size && address - memory.base <= memory.size - size;
}

void snap_supersample_resize(Cpu *c) {
    const char *choice = cfg_value("AC_RENDER_SCALE");
    unsigned percentage = choice && !strcmp(choice, "125") ? 125 :
                          choice && !strcmp(choice, "150") ? 150 :
                          choice && !strcmp(choice, "200") ? 200 : 0;
    if (!percentage) return; // game/native/unknown settings leave Cpu entirely untouched
    // SS-02: the default host mode enlarges the render targets on the host and
    // leaves the engine at its own size; only AC_SS_MODE=engine resizes it.
    const char *mode = cfg_get("AC_SS_MODE");
    if (!mode || strcmp(mode, "engine")) return;
    uint64_t width = c->x[2], height = c->x[3], flags = c->x[4];
    // Handheld groups are not resize-eligible in these constructors. Changing
    // its output alone produced mismatched geometry despite zero API errors.
    if (flags != 2 || width != 1920 || height != 1080) return;

    // Validate the known context layout, but preserve the window's eligibility:
    // fixed output resources lack the config needed by the engine resize path.
    uint64_t context = c->x[1], resource;
    if (!context || context > UINT64_MAX - 0xc8 || !readable_span(context + 0xc8, 8, 1)) return;
    memcpy(&resource, (const void *)(uintptr_t)(context + 0xc8), 8);
    if (!resource || resource > UINT64_MAX - 0x14 || !readable_span(resource + 0x14, 1, 3)) return;
    uint8_t *eligible = (uint8_t *)(uintptr_t)(resource + 0x14);
    if (*eligible > 1) return;

    // Output backing is handled by the DISPLAY-only Vulkan adaptation. Never
    // force a native window resource into an unsupported reconstruction path.
    // Exact arithmetic for the docked pair and these three percentages.
    // flag 1: resize-enabled draw parameters; 2: output; 4: resize-enabled resource groups.
    c->x[2] = width * percentage / 100;
    c->x[3] = height * percentage / 100;
    c->x[4] = 7;

    const char *trace = getenv("NEWSNAP_SUPERSAMPLE_TRACE");
    static unsigned trace_lines;
    if (trace && !strcmp(trace, "1") && trace_lines < 32) {
        trace_lines++;
        rt_log("snap supersample: engine resize %llux%llu flags 2 -> %llux%llu flags 7; native window ownership retained (configuration)",
               (unsigned long long)width, (unsigned long long)height,
               (unsigned long long)c->x[2], (unsigned long long)c->x[3]);
    }
}
