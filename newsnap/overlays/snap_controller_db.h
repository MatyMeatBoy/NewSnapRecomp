// Optional local SDL mappings. Called after SDL gamepad init, before either startup scan.
// SDL paths are UTF-8 (including Windows); the executable directory is independent of cwd.
#pragma once

static void snap_controller_db_load(void) {
    static SDL_AtomicInt loaded;
    if (!SDL_CompareAndSwapAtomicInt(&loaded, 0, 1)) {
        while (SDL_GetAtomicInt(&loaded) == 1) SDL_Delay(1);
        return;
    }
    // An explicit SDL database hint already participates in SDL initialization.
    const char *explicit_file = SDL_GetHint(SDL_HINT_GAMECONTROLLERCONFIG_FILE);
    const char *base = SDL_GetBasePath();
    if ((!explicit_file || !*explicit_file) && base) {
        char *path = NULL;
        if (SDL_asprintf(&path, "%sgamecontrollerdb.txt", base) >= 0) {
            SDL_PathInfo info;
            if (SDL_GetPathInfo(path, &info)) {
                const char *custom = SDL_GetHint(SDL_HINT_GAMECONTROLLERCONFIG);
                char *copy = custom && *custom ? SDL_strdup(custom) : NULL;
                if (custom && *custom && !copy) {
                    rt_log("input: skipping controller database: cannot preserve explicit SDL mappings");
                    SDL_free(path);
                    SDL_SetAtomicInt(&loaded, 2);
                    return;
                }
                int added = SDL_AddGamepadMappingsFromFile(path);
                if (added < 0) rt_log("input: controller database %s failed (%s)", path, SDL_GetError());
                else rt_log("input: controller database %s: %d mappings", path, added);
                // Disk mappings must never displace explicit per-device user overrides.
                if (copy) {
                    char *line = copy;
                    while (line) {
                        char *next = SDL_strchr(line, '\n');
                        if (next) *next++ = 0;
                        size_t length = SDL_strlen(line);
                        if (length && line[length - 1] == '\r') line[length - 1] = 0;
                        if (*line && SDL_AddGamepadMapping(line) < 0)
                            rt_log("input: explicit SDL controller mapping failed (%s)", SDL_GetError());
                        line = next;
                    }
                    SDL_free(copy);
                }
            }
            SDL_free(path);
        }
    }
    SDL_SetAtomicInt(&loaded, 2);
}
