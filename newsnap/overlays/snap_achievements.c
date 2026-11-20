// Game-side Recomp Achievements bridge. Every SDK call belongs to one worker:
// its Windows pipe connect/write can block, never the game/render thread.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "platform/platform.h"
#include "rl_achievements.h"
#include "snap_achievements.h"
#include "snap_achievements_config.h"

#define SNAP_ACH_EVENTS 64
#define SNAP_ACH_NAME 96
static char events[SNAP_ACH_EVENTS][SNAP_ACH_NAME];
static unsigned head, tail;
static volatile uint32_t queue_lock, active, stop, pending_save, pending_casual, overflow;
static volatile uint64_t ticks;
static PlatThread *worker;
static int initialized;

static int take_queue(void) {
    return !__atomic_exchange_n(&queue_lock, 1, __ATOMIC_ACQUIRE);
}
static void release_queue(void) { __atomic_store_n(&queue_lock, 0, __ATOMIC_RELEASE); }

static void classify(void) {
    // Overflow/lock contention must never silently lose Ranked safeguards.
    // This flag is separate from the bounded event queue and cannot overflow.
    if (__atomic_exchange_n(&overflow, 0, __ATOMIC_ACQ_REL)) rl_ach_casual("bridge_overflow");
    if (__atomic_exchange_n(&pending_casual, 0, __ATOMIC_ACQ_REL)) rl_ach_casual("cheats");
    if (__atomic_exchange_n(&pending_save, 0, __ATOMIC_ACQ_REL)) rl_ach_save_loaded();
}

static void achievements_main(void *unused) {
    (void)unused;
    rl_ach_set_info(SNAP_ACH_GAME, SNAP_ACH_VERSION);
    if (!rl_ach_init("", NULL, NULL)) {
        __atomic_store_n(&active, 0, __ATOMIC_RELEASE);
        rl_ach_shutdown();
        return;
    }
    uint64_t seen = 0;
    for (;;) {
        classify();
        // Ticks coalesce: a slow/blocked host cannot build an unbounded backlog.
        // No memory rules are registered; frame() pumps launcher messages only.
        uint64_t current = __atomic_load_n(&ticks, __ATOMIC_ACQUIRE);
        if (!__atomic_load_n(&stop, __ATOMIC_ACQUIRE) && current != seen) { rl_ach_frame(); seen = current; }
        for (unsigned i = 0; i < SNAP_ACH_EVENTS; i++) {
            char name[SNAP_ACH_NAME];
            int got = 0;
            if (take_queue()) {
                if (tail != head) {
                    memcpy(name, events[tail % SNAP_ACH_EVENTS], sizeof name);
                    tail++;
                    got = 1;
                }
                release_queue();
            }
            if (!got) break;
            classify();  // classifications precede every event, not just a batch
            rl_ach_event(name);
        }
        if (__atomic_load_n(&stop, __ATOMIC_ACQUIRE)) {
            // Finish accepted events (especially a final save commit) before
            // closing a healthy pipe. Never pump new frames during shutdown.
            // A blocked pipe still cannot extend the caller's 100ms join bound.
            int drained = 0;
            if (take_queue()) {
                drained = head == tail;
                release_queue();
            }
            if (drained) break;
            plat_sleep_ms(1);
        } else plat_sleep_ms(8);
    }
    classify();
    rl_ach_shutdown();
}

void snap_achievements_init(void) {
    // Called once before boot/guest threads. No session means no SDK init,
    // allocation, thread, synchronization primitive or environment changes.
    if (initialized) return;
    initialized = 1;
    const char *session = getenv("RL_SESSION");
    if (!session || !*session) return;
    __atomic_store_n(&active, 1, __ATOMIC_RELEASE);
    worker = plat_thread_new(achievements_main, NULL, "Snap achievements");
    if (!worker) __atomic_store_n(&active, 0, __ATOMIC_RELEASE);
}

void snap_achievements_frame(void) {
    if (__atomic_load_n(&active, __ATOMIC_ACQUIRE)) __atomic_add_fetch(&ticks, 1, __ATOMIC_RELEASE);
}
void snap_achievements_save_loaded(void) {
    if (__atomic_load_n(&active, __ATOMIC_ACQUIRE)) __atomic_store_n(&pending_save, 1, __ATOMIC_RELEASE);
}
void snap_achievements_casual(void) {
    if (__atomic_load_n(&active, __ATOMIC_ACQUIRE)) __atomic_store_n(&pending_casual, 1, __ATOMIC_RELEASE);
}
void snap_achievements_event(const char *name) {
    if (!__atomic_load_n(&active, __ATOMIC_ACQUIRE) || !name || !*name) return;
    // Reject overlong names instead of truncating into another valid event.
    size_t n = 0;
    while (n < SNAP_ACH_NAME && name[n]) n++;
    if (n == SNAP_ACH_NAME || !take_queue()) {
        __atomic_store_n(&overflow, 1, __ATOMIC_RELEASE);
        return;
    }
    if (head - tail == SNAP_ACH_EVENTS) __atomic_store_n(&overflow, 1, __ATOMIC_RELEASE);
    else {
        memcpy(events[head % SNAP_ACH_EVENTS], name, n + 1);
        head++;
    }
    release_queue();
}
void snap_achievements_shutdown(void) {
    __atomic_store_n(&active, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&stop, 1, __ATOMIC_RELEASE);
    PlatThread *thread = worker;
    worker = NULL;
    if (thread && !plat_thread_join_ns(thread, 100000000ull)) {
        // Static worker storage stays valid until process exit; never free it
        // while a host pipe call is blocked. The exit path waits at most 100ms.
        plat_thread_detach(thread);
    }
}
