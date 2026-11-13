#pragma once
#include "cpu.h"

// Verified Snap 2.0.1 bounded integer PRNG; no worker/IPC/progress changes.
void snap_random_range(Cpu *cpu);
