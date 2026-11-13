// Same bounded integer operation as the verified guest routine. See
// docs/bugs/cpu-asset-workers.md for provenance, equivalence and limitations.
#include "snap_random_range.h"
#include <stdint.h>
#include <string.h>

typedef struct { uint32_t a, b, c, d; } SnapRandomState;

static uint32_t arithmetic_right(uint32_t value, unsigned shift) {
    return (value >> shift) | ((0u - (value >> 31)) << (32u - shift));
}

static uint32_t random_step(SnapRandomState *state) {
    uint32_t temporary = state->d ^ (state->d << 11);
    uint32_t result = state->a ^ arithmetic_right(state->a, 19) ^
                      temporary ^ arithmetic_right(temporary, 8);
    state->d = state->c;
    state->c = state->b;
    state->b = state->a;
    state->a = result;
    return result & UINT32_C(0x7fffffff);
}

static void store_state(void *memory, const SnapRandomState *state) {
    // Keep the original store order and intermediate high-range advances.
    // memcpy also supports the guest's unaligned word accesses without C UB.
    memcpy((uint8_t *)memory + 8, &state->c, 4);
    memcpy((uint8_t *)memory + 12, &state->d, 4);
    memcpy(memory, &state->a, 4);
    memcpy((uint8_t *)memory + 4, &state->b, 4);
}

void snap_random_range(Cpu *cpu) {
    void *memory = (void *)(uintptr_t)cpu->x[0];
    uint32_t bound = (uint32_t)cpu->x[1];
    if (!bound) {
        cpu->x[0] = 0;
        return;
    }
    SnapRandomState state;
    memcpy(&state, memory, sizeof state);
    uint32_t result;
    if (bound == UINT32_C(0x7fffffff)) {
        uint32_t a = state.a, b = state.b, temporary = state.d ^ (state.d << 11);
        result = random_step(&state);
        cpu->x[8] = state.a;
        cpu->x[9] = temporary;
        cpu->x[10] = a;
        cpu->x[11] = b;
        cpu->x[12] = a ^ arithmetic_right(a, 19) ^ temporary;
        store_state(memory, &state);
    } else if (bound < UINT32_C(0x80000000)) {
        uint32_t scale = UINT32_C(0x80000000) / (bound + 1), a, b, c;
        do {
            a = state.a;
            b = state.b;
            c = state.c;
            result = random_step(&state) / scale;
        } while (result > bound);
        cpu->x[8] = b;
        cpu->x[9] = c;
        cpu->x[10] = state.a;
        cpu->x[11] = scale;
        cpu->x[12] = a;
        cpu->x[13] = a;
        cpu->x[14] = result;
        store_state(memory, &state);
    } else {
        uint32_t first, high;
        do {
            uint32_t low = random_step(&state);
            first = state.a;
            store_state(memory, &state);
            // The recursive range construction consumes TWO advances, even
            // for UINT32_MAX. Retain its rejection and final volatile values.
            high = random_step(&state) / UINT32_C(0x40000000);
            store_state(memory, &state);
            result = low + high * UINT32_C(0x80000000);
        } while (result > bound);
        cpu->x[1] = 1;
        cpu->x[8] = 0;
        cpu->x[9] = 1;
        cpu->x[10] = result;
        cpu->x[11] = UINT32_C(0x40000000);
        cpu->x[12] = first;
        cpu->x[13] = first;
        cpu->x[14] = high;
    }
    cpu->x[0] = result;
}
