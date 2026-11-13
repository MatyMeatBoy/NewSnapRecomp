// Only the verified libc save/restore instructions manipulate guest jump buffers.
// These scopes own live native return points and are private to one Cpu/fiber.
#include "snap_jump.h"
#include "host.h"
#include <stdlib.h>
#include <string.h>

struct SnapJumpScope {
    struct SnapJumpScope *previous;
    SnapJumpCheckpoint *checkpoints;
    Cpu *cpu;
};

// Cpu's reserved padding is zeroed by thread/fiber initialization. Keep every
// published guest-state offset, vector offset and sizeof(Cpu) unchanged.
_Static_assert(offsetof(Cpu, _pad) == 344 && sizeof(((Cpu *)0)->_pad) >= sizeof(void *),
               "reserved Cpu storage changed; audit guest jump ownership");

static SnapJumpScope *head(Cpu *c) {
    SnapJumpScope *scope;
    memcpy(&scope, c->_pad, sizeof scope);
    return scope;
}

static void set_head(Cpu *c, SnapJumpScope *scope) { memcpy(c->_pad, &scope, sizeof scope); }

static int depth(Cpu *c) {
    if (!c->thread) return 0;  // Synthetic/loader probes have no running guest thread.
    if (!kern_host_track) rt_fatal("guest jump: host-service depth tracking is required");
    return __atomic_load_n(kern_host_depth(c->thread), __ATOMIC_RELAXED);
}

static void drop(SnapJumpScope *scope) {
    SnapJumpCheckpoint *point = scope->checkpoints;
    while (point) {
        SnapJumpCheckpoint *next = point->next;
        free(point);
        point = next;
    }
    free(scope);
}

SnapJumpScope *snap_jump_scope_enter(Cpu *c) {
    SnapJumpScope *scope = calloc(1, sizeof *scope);
    if (!scope) rt_fatal("guest jump: cannot allocate caller scope");
    scope->cpu = c;
    scope->previous = head(c);
    set_head(c, scope);
    return scope;
}

void snap_jump_scope_cleanup(SnapJumpScope **slot) {
    SnapJumpScope *scope = *slot;
    if (!scope) return;
    if (head(scope->cpu) != scope) rt_fatal("guest jump: caller scopes returned out of order");
    set_head(scope->cpu, scope->previous);
    drop(scope);
    *slot = NULL;
}

SnapJumpCheckpoint *snap_jump_arm(SnapJumpScope *scope, Cpu *c, uint64_t return_pc) {
    if (!scope || scope->cpu != c || head(c) != scope || c->x[30] != return_pc)
        rt_fatal("guest jump: invalid native save caller");
    SnapJumpCheckpoint *point = scope->checkpoints;
    while (point && !(point->buffer == c->x[0] && point->pc == return_pc)) point = point->next;
    if (!point) {
        point = calloc(1, sizeof *point);
        if (!point) rt_fatal("guest jump: cannot allocate checkpoint");
        point->next = scope->checkpoints;
        scope->checkpoints = point;
    }
    point->buffer = c->x[0];
    point->pc = return_pc;
    point->sp = c->sp;
    point->host_depth = depth(c);
    return point;
}

void snap_jump_check_save(Cpu *c) {
    SnapJumpScope *scope = head(c);
    for (SnapJumpCheckpoint *point = scope ? scope->checkpoints : NULL; point; point = point->next)
        if (point->buffer == c->x[0] && point->pc == c->x[30] && point->sp == c->sp) return;
    rt_fatal("guest jump: setjmp reached without an instrumented live caller");
}

_Noreturn void snap_jump_resume(Cpu *c) {
    SnapJumpScope *target = head(c);
    SnapJumpCheckpoint *point = NULL;
    for (; target && !point; target = point ? target : target->previous)
        for (SnapJumpCheckpoint *candidate = target->checkpoints; candidate; candidate = candidate->next)
            if (candidate->pc == c->pc && candidate->sp == c->sp) { point = candidate; break; }
    if (!target || !point) rt_fatal("guest jump: stale or unregistered native continuation");
    if (point->host_depth != depth(c))
        rt_fatal("guest jump: nonlocal return across a host-service boundary is unsupported");
    while (head(c) != target) {
        SnapJumpScope *younger = head(c);
        set_head(c, younger->previous);
        drop(younger);
    }
    plat_jmp_go(&point->native);
}

void snap_jump_clear(Cpu *c) {
    if (!c) return;
    while (head(c)) {
        SnapJumpScope *scope = head(c);
        set_head(c, scope->previous);
        drop(scope);
    }
}
