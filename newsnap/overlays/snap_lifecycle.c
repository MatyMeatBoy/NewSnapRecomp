// OE's exit-request sections protect in-progress application work. The host
// owns OE initialization, so these calls must not dereference SDK service state.
#include "host.h"
#include "platform/platform.h"

static PlatMutex exit_lock = PLAT_MUTEX_INIT;
static unsigned exit_sections;
static int close_pending;
extern void gfx_window_request_close(void);

static void snap_exit_enter(Cpu *c) {
    (void)c;
    plat_mutex_lock(&exit_lock);
    if (exit_sections == (unsigned)-1) rt_fatal("OE exit section overflow");
    exit_sections++;
    plat_mutex_unlock(&exit_lock);
}

static void snap_exit_leave(Cpu *c) {
    (void)c;
    plat_mutex_lock(&exit_lock);
    if (!exit_sections) rt_fatal("OE exit section underflow");
    int request = !--exit_sections && close_pending;
    plat_mutex_unlock(&exit_lock);
    if (request) gfx_window_request_close();
}

// Called on the window thread before flushing host saves. Deferring keeps the
// window/event loop alive while the guest finishes the protected work. Once
// closing starts with no holders, retain the lock until process termination:
// no new protected work can begin between this check and the final save flush.
int snap_exit_begin_close(void) {
    plat_mutex_lock(&exit_lock);
    if (exit_sections) {
        close_pending = 1;
        plat_mutex_unlock(&exit_lock);
        return 0;
    }
    return 1;
}

HOST_OVERRIDE("_ZN2nn2oe31EnterExitRequestHandlingSectionEv", snap_exit_enter);
HOST_OVERRIDE("_ZN2nn2oe31LeaveExitRequestHandlingSectionEv", snap_exit_leave);
