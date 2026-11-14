"""Preserve explicit CLI consoles; keep redirected/background helpers hidden."""


def edits():
    return {
        'runtime/platform/win32.c': [
            ('    if (!cmd || !CreateProcessW(NULL, cmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {',
             '    // A direct CLI keeps its console; a consoleless launcher stays consoleless.\n'
             '    DWORD console_flags = GetConsoleWindow() ? 0 : CREATE_NO_WINDOW;\n'
             '    if (!cmd || !CreateProcessW(NULL, cmd, NULL, NULL, TRUE, console_flags, NULL, NULL, &si, &pi)) {'),
            ('    BOOL ok = cmdline && CreateProcessW(NULL, cmdline, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi);',
             '    BOOL ok = cmdline && CreateProcessW(NULL, cmdline, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);'),
            ('    BOOL ok = cmd && CreateProcessW(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);',
             '    DWORD console_flags = GetConsoleWindow() ? 0 : CREATE_NO_WINDOW;\n'
             '    BOOL ok = cmd && CreateProcessW(NULL, cmd, NULL, NULL, FALSE, console_flags, NULL, NULL, &si, &pi);'),
        ],
        'tools/build_game.py': [
            ('CREATE_SUSPENDED = 0x4', 'CREATE_SUSPENDED = 0x4\nCREATE_NO_WINDOW = 0x08000000'),
            ('    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, creationflags=CREATE_SUSPENDED)',
             '    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, creationflags=CREATE_SUSPENDED | CREATE_NO_WINDOW)'),
        ],
    }
