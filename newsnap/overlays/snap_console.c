// CONSOLE-02: started by a double click, the game is a console program and Windows opens a console window for it
// alone. That window is hidden. A console the game shares with whoever started it (a terminal, a batch file) is left
// as it is, and so is the launcher's case, which starts the game without a console. Output handles are untouched:
// the log file and any redirection keep working.
#ifdef _WIN32
#include <windows.h>
void snap_hide_own_console(void) {
    HWND window = GetConsoleWindow();
    if (!window) return;
    DWORD processes[2];
    if (GetConsoleProcessList(processes, 2) == 1) ShowWindow(window, SW_HIDE);   // only this process is attached
}
#else
void snap_hide_own_console(void) {}
#endif
