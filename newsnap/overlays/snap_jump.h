// Guest libc jumps return to an existing lifted caller, never a new dispatch frame.
#pragma once
#include "cpu.h"
#include "platform/platform.h"

typedef struct SnapJumpScope SnapJumpScope;
typedef struct SnapJumpCheckpoint {
    PlatJmp native;
    struct SnapJumpCheckpoint *next;
    uint64_t buffer, pc, sp;
    int host_depth;
} SnapJumpCheckpoint;

SnapJumpScope *snap_jump_scope_enter(Cpu *c);
void snap_jump_scope_cleanup(SnapJumpScope **scope);
SnapJumpCheckpoint *snap_jump_arm(SnapJumpScope *scope, Cpu *c, uint64_t return_pc);
void snap_jump_check_save(Cpu *c);
_Noreturn void snap_jump_resume(Cpu *c);
void snap_jump_clear(Cpu *c);
