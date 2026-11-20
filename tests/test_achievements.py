import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import json
import threading
import uuid

from newsnap.upstream import ROOT, UPSTREAM


class AchievementAdaptTests(unittest.TestCase):
    def test_save_event_only_follows_changed_commit_success(self):
        text = adapted_save_source()
        commit = commit_function(text)
        marker = 'snap_achievements_event("save_committed")'
        self.assertEqual(text.count(marker), 1)
        self.assertEqual(commit.count(marker), 1)
        self.assertLess(commit.index('files, none changed'), commit.index(marker))
        self.assertLess(commit.index('move_dir(new_root, ready'), commit.index(marker))
        self.assertLess(commit.rindex('if (tx_dead) return FS_R_INVALID_ARGUMENT;'), commit.index(marker))
        recovery = text.split('static void save_recover(void)', 1)[1].split('// The first save mount:', 1)[0]
        self.assertNotIn('snap_achievements_event', recovery)

    def test_bonus_list_describes_only_live_changed_commit(self):
        draft = json.loads((ROOT/'assets/achievements/newsnaprecomp.json').read_text())
        self.assertEqual((draft['format'], draft['game'], draft['source'], draft['console']),
                         (1, 'newsnaprecomp', 'events', 'switch'))
        self.assertEqual(draft['versions'], '>=0.9.25')
        self.assertNotIn('leaderboards', draft)
        self.assertEqual(len(draft['achievements']), 1)
        achievement = draft['achievements'][0]
        self.assertTrue(achievement['bonus'])
        self.assertEqual(achievement['event'], 'save_committed')
        self.assertEqual(achievement['points'], 5)
        self.assertNotIn('type', achievement)
        self.assertEqual(achievement['description'], 'Complete a changed save-data commit during live play.')

    def test_exact_hooks_and_sdk_staging(self):
        from newsnap.achievements_adapt import edits, stage_sdk
        for name, changes in edits().items():
            text = (UPSTREAM / name).read_text(encoding='utf-8')
            for before, after in changes:
                self.assertEqual(text.count(before), 1, (name, before))
                text = text.replace(before, after, 1)
        with tempfile.TemporaryDirectory() as folder:
            stage_sdk(folder)
            root = Path(folder)
            self.assertTrue((root/'runtime/rlach/sdk/src/rl_achievements.c').is_file())
            self.assertTrue((root/'runtime/snap_rlach_rl_achievements.c').is_file())
            self.assertTrue((root/'runtime/rl_achievements.h').is_file())
            self.assertIn('Recomp Achievements License', (root/'runtime/rlach/LICENSE').read_text())

    def test_vendor_pin_and_license_are_explicit(self):
        vendor = ROOT/'third_party/recomp_achievements'
        self.assertEqual((vendor/'VERSION').read_text().strip(), 'faf094acdf1efb57d8db7c8187b4b47aa1501805')
        self.assertIn('Launchers need our written permission', (vendor/'LICENSE').read_text())


def adapted_save_source():
    from newsnap.achievements_adapt import edits
    text = (UPSTREAM/'runtime/fs_host.c').read_text(encoding='utf-8')
    for before, after in edits()['runtime/fs_host.c']:
        if text.count(before) != 1: raise AssertionError('save source seam changed')
        text = text.replace(before, after, 1)
    return text


def commit_function(text):
    return 'static uint32_t save_commit_locked(void)' + text.split(
        'static uint32_t save_commit_locked(void)', 1)[1].split('// The background commit:', 1)[0]


PLATFORM = r'''
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include "platform/platform.h"
struct PlatThread { HANDLE handle; PlatThreadFn fn; void *arg; };
static int threads_started;
static HANDLE join_gate;
static DWORD WINAPI run_thread(void *value) {
    struct PlatThread *t = value; t->fn(t->arg); return 0;
}
PlatThread *plat_thread_new(PlatThreadFn fn, void *arg, const char *name) {
    (void)name;
    struct PlatThread *t = calloc(1, sizeof *t);
    t->fn = fn; t->arg = arg; t->handle = CreateThread(NULL, 0, run_thread, t, 0, NULL);
    if (!t->handle) { free(t); return NULL; }
    threads_started++; return t;
}
int plat_thread_join_ns(PlatThread *t, uint64_t ns) {
    if (join_gate) SetEvent(join_gate);
    if (WaitForSingleObject(t->handle, (DWORD)(ns / 1000000)) != WAIT_OBJECT_0) return 0;
    CloseHandle(t->handle); free(t); return 1;
}
void plat_thread_detach(PlatThread *t) { CloseHandle(t->handle); /* thread owns t until process exit */ }
void plat_sleep_ms(uint32_t ms) { Sleep(ms); }
'''

# Execute the actual adapted transaction function against a virtual store. No
# owner data, filesystem commit, game key or save content enters this fixture.
COMMIT_STORAGE = r'''
#include <string.h>
#define FS_R_INVALID_ARGUMENT 1u
#define MOVE_TRIES 3
static const char *new_root = "new", *work_root = "work", *tx_root = "tx";
static char ready_root[1100];
static unsigned ready_seq;
static int tx_step, tx_dead, storage_case;
static int32_t save_dirty;
uint64_t plat_now_ns(void) { return 0; }
static const char *newest_save(void) { return "save"; }
static int exists(const char *p) { return 1; }
static int remove_tree(const char *p) { return 0; }
static int copy_tree(const char *a, const char *b, const char *base, int links,
                     int *count, int *linked, uint64_t *bytes) {
    *count = 2; *linked = storage_case == 6 ? 2 : 1; *bytes = 42;
    return storage_case == 1;
}
static int crashed(void) { return storage_case == 2; }
static int same_tree(const char *a, const char *b) { return storage_case == 6; }
static int move_dir(const char *a, const char *b, int tries) { return storage_case == 3; }
static int swap_in(void) { tx_dead = storage_case == 4; return storage_case == 5; }
void rt_log(const char *format, ...) { }
'''


class AchievementNativeTests(unittest.TestCase):
    def compile(self, source, *, sdk=False):
        cc = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if os.name != 'nt' or not cc:
            self.skipTest('Windows native compiler fixture')
        from newsnap.achievements_adapt import stage_sdk
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name); stage_sdk(root)
        runtime = root/'runtime'
        for name in ('snap_achievements.c', 'snap_achievements.h'):
            shutil.copy2(ROOT/'newsnap/overlays'/name, runtime/name)
        fixture = root/'fixture.c'; fixture.write_text(PLATFORM + source, encoding='utf-8')
        executable = root/'fixture.exe'
        sources = [fixture, runtime/'snap_achievements.c']
        if sdk: sources.extend(sorted(runtime.glob('snap_rlach_*.c')))
        command = [cc, '-std=c11', '-O1', '-I', str(runtime), '-I', str(UPSTREAM/'runtime'),
                   *map(str, sources), '-o', str(executable)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return executable

    def test_shutdown_drains_pending_commit_and_classification_without_frame_pump(self):
        exe = self.compile(r'''
#include "snap_achievements.h"
#include "rl_achievements.h"
static int events_seen, casuals, saves, frames, stopped, wrong_order;
void rl_ach_set_info(const char *game, const char *version) { (void)game; (void)version; }
int rl_ach_init(const char *console, rl_ach_read_fn read, void *ud) {
    (void)console; (void)read; (void)ud;
    // The platform fixture opens this gate only after shutdown has set stop.
    return WaitForSingleObject(join_gate, 2000) == WAIT_OBJECT_0;
}
void rl_ach_frame(void) { frames++; }
void rl_ach_save_loaded(void) { saves++; }
void rl_ach_casual(const char *reason) { (void)reason; casuals++; }
void rl_ach_event(const char *name) {
    if (!saves || !casuals || strcmp(name, "save_committed")) wrong_order = 1;
    events_seen++;
}
void rl_ach_shutdown(void) { stopped++; }
int main(void) {
    join_gate = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (!join_gate) return 1;
    snap_achievements_init();
    snap_achievements_save_loaded(); snap_achievements_casual();
    snap_achievements_frame(); snap_achievements_event("save_committed");
    ULONGLONG start = GetTickCount64();
    snap_achievements_shutdown();
    if (GetTickCount64() - start > 500) return 2;
    if (events_seen != 1 || wrong_order || frames || stopped != 1) return 3;
    CloseHandle(join_gate);
    return 0;
}
''')
        env = dict(os.environ, RL_SESSION='fixture-never-connects')
        result = subprocess.run([str(exe)], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_session_is_inert_and_bounded_queue_preserves_classification(self):
        exe = self.compile(r'''
#include "snap_achievements.h"
static HANDLE gate;
static DWORD caller, owner;
static volatile LONG calls, casuals, saves, events_seen, wrong_thread, first_event_casual;
static int slow_init;
static void check(void) {
    DWORD id = GetCurrentThreadId();
    if (!owner) owner = id;
    if (owner != id || id == caller) wrong_thread = 1;
    InterlockedIncrement(&calls);
}
void rl_ach_set_info(const char *game, const char *version) { check(); }
int rl_ach_init(const char *console, void *read, void *ud) { check(); WaitForSingleObject(gate, INFINITE); return 1; }
void rl_ach_shutdown(void) { check(); }
void rl_ach_frame(void) { check(); }
void rl_ach_save_loaded(void) { check(); InterlockedIncrement(&saves); }
void rl_ach_casual(const char *reason) { check(); InterlockedIncrement(&casuals); }
void rl_ach_event(const char *name) {
    check(); if (!events_seen) first_event_casual = casuals; InterlockedIncrement(&events_seen);
}
int main(int argc, char **argv) {
    caller = GetCurrentThreadId(); gate = CreateEvent(NULL, TRUE, FALSE, NULL);
    snap_achievements_init();
    if (argc == 1) {
        snap_achievements_frame(); snap_achievements_save_loaded(); snap_achievements_casual();
        snap_achievements_event("test"); snap_achievements_shutdown();
        return threads_started || calls;
    }
    if (!strcmp(argv[1], "blocked")) {
        ULONGLONG start = GetTickCount64();
        snap_achievements_shutdown();
        return GetTickCount64() - start > 500 ? 5 : 0;
    }
    for (int i = 0; i < 10000; i++) snap_achievements_frame();
    snap_achievements_save_loaded(); snap_achievements_casual();
    for (int i = 0; i < 100; i++) snap_achievements_event("fixture_verified_event");
    SetEvent(gate);
    for (int i = 0; i < 100 && events_seen < 64; i++) Sleep(10);
    snap_achievements_shutdown();
    if (wrong_thread || !first_event_casual || !saves || events_seen != 64 || threads_started != 1) return 4;
    printf("worker-only, no-session inert, overflow classified before %ld events\n", events_seen);
    return 0;
}
''')
        env = dict(os.environ); env.pop('RL_SESSION', None)
        inert = subprocess.run([str(exe)], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(inert.returncode, 0, inert.stdout + inert.stderr)
        env['RL_SESSION'] = 'fixture-never-connects'
        active = subprocess.run([str(exe), 'active'], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(active.returncode, 0, active.stdout + active.stderr)
        blocked = subprocess.run([str(exe), 'blocked'], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(blocked.returncode, 0, blocked.stdout + blocked.stderr)

    def test_actual_sdk_named_pipe_protocol_without_real_player(self):
        exe = self.compile(COMMIT_STORAGE + commit_function(adapted_save_source()) + r'''
#include "snap_achievements.h"
int main(void) {
    snap_achievements_init();
    Sleep(100);
    snap_achievements_save_loaded(); snap_achievements_casual();
    for (storage_case = 0; storage_case <= 6; storage_case++) {
        uint32_t result = save_commit_locked();
        int should_fail = storage_case >= 1 && storage_case <= 4;
        if ((result != 0) != should_fail) return 7;
    }
    for (int i = 0; i < 30; i++) { snap_achievements_frame(); Sleep(10); }
    snap_achievements_shutdown();
    return 0;
}
''', sdk=True)
        import _winapi
        pipe_name = r'\\.\pipe\newsnap-achievement-fixture-' + uuid.uuid4().hex
        handle = _winapi.CreateNamedPipe(pipe_name, 3, 0, 1, 65536, 65536, 0, 0)
        received = []; failures = []
        def serve():
            try:
                _winapi.ConnectNamedPipe(handle)
                pending = b''
                while True:
                    chunk, status = _winapi.ReadFile(handle, 65536)
                    if not chunk: break
                    pending += chunk
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        received.append(json.loads(line))
                        if received[-1]['t'] == 'hello':
                            _winapi.WriteFile(handle, b'{"t":"quiet"}\n')
            except OSError as error:
                if error.winerror not in (109, 232): failures.append(error)
            finally:
                _winapi.CloseHandle(handle)
        server = threading.Thread(target=serve, daemon=True); server.start()
        env = dict(os.environ, RL_SESSION=pipe_name)
        process = subprocess.run([str(exe)], env=env, capture_output=True, text=True, timeout=15)
        server.join(3)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertFalse(server.is_alive(), 'fixture pipe did not close')
        self.assertEqual(failures, [])
        self.assertEqual(received[0]['t'], 'hello')
        self.assertEqual(received[0]['game'], 'newsnaprecomp')
        self.assertFalse(received[0]['memory'])
        self.assertEqual(received[0]['console'], '')
        types = [message['t'] for message in received]
        self.assertIn('save_loaded', types)
        self.assertIn('casual', types)
        events = [message for message in received if message['t'] == 'event']
        self.assertEqual([message['name'] for message in events], ['save_committed', 'save_committed'])
        self.assertLess(types.index('save_loaded'), types.index('event'))
        self.assertLess(types.index('casual'), types.index('event'))
        self.assertNotIn('unlock', types)
