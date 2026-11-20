#pragma once

// The producers never perform SDK/IPC work. Named game events must only be
// called from independently verified hooks; this bridge invents no unlocks.
void snap_achievements_init(void);
void snap_achievements_frame(void);
void snap_achievements_save_loaded(void);
void snap_achievements_casual(void);
void snap_achievements_event(const char *name);
void snap_achievements_shutdown(void);
