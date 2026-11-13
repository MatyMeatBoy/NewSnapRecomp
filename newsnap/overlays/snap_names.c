// User-selected local name entry without Nintendo's profanity dictionary.
// The PC ShowKeyboard implementation validates length/disabled characters and
// cancellation. It does not execute the game's Nintendo text-check callback.
// Do not claim the original filter initialized: its missing content is a real
// error, and its constructor/destructor must retain their uninitialized state.
#include "host.h"

static void snap_names_filter_unavailable(Cpu *c) {
    static unsigned warned;
    if (!__atomic_exchange_n(&warned, 1, __ATOMIC_RELAXED))
        rt_log("Snap names: local PC input; Nintendo word filter unavailable (user-selected mode)");
    // The original Initialize would load missing system content. Its caller in
    // Snap 2.0.1 ignores the result; the PC keyboard doesn't invoke its callback.
    // Leaving the object untouched also keeps SDK Finalize/destruction safe.
    c->x[0] = 0x7d402u; // nn::fs::ResultTargetNotFound: dictionary not installed.
}
HOST_OVERRIDE("_ZN2nn3ngc15ProfanityFilter10InitializeEPvm", snap_names_filter_unavailable);
