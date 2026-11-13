#pragma once
#include "snap_vrr.h"
/* One immutable JSON blob in flight plus one replaceable pending blob; no Vulkan/window ownership. */
void snap_vrr_writer_start(void);
void snap_vrr_writer_publish(const SnapVrrStatus *);
void snap_vrr_writer_stop(void);
