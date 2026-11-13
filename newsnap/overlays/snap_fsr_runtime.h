#pragma once
#include "snap_fsr_sdk.h"
static int snap_fsr_runtime_available(int ml);
static void snap_fsr_runtime_retire(VkImage output);
static void snap_fsr_runtime_sweep(int all);
static void snap_fsr_runtime_shutdown(void);
