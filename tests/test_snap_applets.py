import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / 'newsnap/overlays/snap_applets.c'

EXPECTED = {
    '_ZN2nn3err20ShowApplicationErrorERKNS0_19ApplicationErrorArgE',
    '_ZN2nn3err9ShowErrorERKNS0_18ErrorResultVariantE',
    '_ZN2nn4nifm27SubmitNetworkRequestAndWaitEv',
    '_ZN2nn4nifm31HandleNetworkRequestErrorResultEv',
    '_ZN2nn4nifm20CancelNetworkRequestEv',
    '_ZN2nn4nifm26GetCurrentPrimaryIpAddressEP7in_addr',
    '_ZN2nn4nifm22GetCurrentProxySettingEPNS0_12ProxySettingE',
    '_ZN2nn7account32IsNetworkServiceAccountAvailableEPbRKNS0_10UserHandleE',
    '_ZN2nn7friends10InitializeEv',
    '_ZN2nn7friends18ShowUserDetailInfoERKNS_7account3UidERKNS1_23NetworkServiceAccountIdERKNS0_15InAppScreenNameESA_',
    '_ZN2nn5album10InitializeEv',
    '_ZN2nn5album8FinalizeEv',
    '_ZN2nn5album14SaveScreenshotEPKvmNS0_9ImageSizeENS0_16ImageOrientationENS0_17AlbumReportOptionE',
}

HOST_H = r'''#include <stdint.h>
#include <stddef.h>
typedef struct { uint64_t x[31]; uint64_t sp; } Cpu;
typedef void (*GuestFn)(Cpu *);
static inline uint64_t arg_x(const Cpu *c, int i) { return c->x[i]; }
static inline void *arg_p(const Cpu *c, int i) { return (void *)(uintptr_t)c->x[i]; }
static inline void ret_x(Cpu *c, uint64_t v) { c->x[0] = v; }
#define RT_RESULT(module, desc) ((uint32_t)(module) | ((uint32_t)(desc) << 9))
void rt_log(const char *fmt, ...);
void rt_fatal(const char *fmt, ...);
const char *ldr_describe(uint64_t a, char *buf, int n);
void test_register(const char *name, GuestFn fn);
#define RT_CAT2(a, b) a##b
#define RT_CAT(a, b) RT_CAT2(a, b)
#define HOST_OVERRIDE_AT(sym, fn, id) \
    __attribute__((constructor)) static void RT_CAT(test_reg_, id)(void) { test_register(sym, fn); }
#define HOST_OVERRIDE(sym, fn) HOST_OVERRIDE_AT(sym, fn, __COUNTER__)
'''

TEST_C = r'''#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snap_applets.c"

static struct { const char *name; GuestFn fn; } table[64];
static int entries, logs, unreadable;
static uint64_t readable_limit = UINT64_MAX;
static char last[2048];
void test_register(const char *name, GuestFn fn) {
    for (int i = 0; i < entries; i++) if (!strcmp(table[i].name, name)) exit(10);   // duplicate override
    table[entries].name = name, table[entries++].fn = fn;
}
void rt_log(const char *fmt, ...) { va_list a; va_start(a, fmt); vsnprintf(last, sizeof last, fmt, a); va_end(a); logs++; }
void rt_fatal(const char *fmt, ...) { (void)fmt; exit(3); }
const char *ldr_describe(uint64_t a, char *buf, int n) { snprintf(buf, n, "main+%#llx", (unsigned long long)a); return buf; }
int plat_mem_readable(uint64_t addr, uint64_t n) { (void)addr; return !unreadable && n <= readable_limit; }
static GuestFn find(const char *part) {
    GuestFn fn = NULL;
    for (int i = 0; i < entries; i++) if (strstr(table[i].name, part)) { if (fn) exit(11); fn = table[i].fn; }
    if (!fn) exit(12);
    return fn;
}
#define CHECK(cond) do { if (!(cond)) { fprintf(stderr, "line %d: %s\nlast log: %s\n", __LINE__, #cond, last); return 1; } } while (0)

int main(int argc, char **argv) {
    Cpu c = {0};
    c.x[30] = 0x1238;
    if (argc > 1 && !strcmp(argv[1], "names")) { for (int i = 0; i < entries; i++) puts(table[i].name); return 0; }
    if (argc > 1 && !strcmp(argv[1], "null-linked")) { find("IsNetworkServiceAccountAvailable")(&c); return 1; }

    // Application error: number and both texts reach the log, control characters neutralised.
    static uint8_t arg[0x1014 + 16];
    uint32_t number = 2162;
    memcpy(arg + 8, &number, 4);
    strcpy((char *)arg + 0x14, "Save data\nis damaged.");
    strcpy((char *)arg + 0x814, "Full\tscreen text");
    c.x[0] = (uint64_t)(uintptr_t)arg, c.x[1] = 77;
    find("ShowApplicationError")(&c);
    CHECK(logs == 1 && strstr(last, "dialog 2162 from main+0x1234"));
    CHECK(strstr(last, "\"Save data is damaged.\" / \"Full screen text\""));
    CHECK(c.x[0] == (uint64_t)(uintptr_t)arg && c.x[1] == 77);   // void: registers left alone

    // A text without terminator is cut at the field (0x800) and at the log cap; nothing past it is read.
    memset(arg + 0x14, 'A', 0x800);
    memset(arg + 0x814, 'B', 0x800);
    memset(arg + 0x1014, 'Z', 16);
    find("ShowApplicationError")(&c);
    CHECK(strstr(last, "AAAA") && strstr(last, "BBBB") && !strchr(last, 'Z') && strlen(last) < 700);

    // Unreadable argument: still a log line, no dereference.
    unreadable = 1;
    find("ShowApplicationError")(&c);
    CHECK(strstr(last, "dialog 0 from") && strstr(last, "\"\" / \"\""));
    find("ErrorResultVariant")(&c);
    CHECK(strstr(last, "variant 00000000 00000000"));
    unreadable = 0;
    uint32_t variant[3] = {1, 0x1234, 0};
    readable_limit = sizeof variant;
    c.x[0] = (uint64_t)(uintptr_t)variant;
    find("ErrorResultVariant")(&c);
    CHECK(strstr(last, "variant 00000001 00001234"));
    readable_limit = UINT64_MAX;

    // A dialog repeated every frame is logged 16 times at most.
    int before = logs;
    c.x[0] = 0;
    for (int i = 0; i < 100; i++) find("ShowApplicationError")(&c);
    CHECK(logs - before == 16 - 3);   // three application errors were logged above; the variant counts apart
    c.x[0] = 0;

    // Network: bool false means no retry; the address/proxy Result remains a synthetic host failure.
    c.x[0] = 0xabc;
    find("SubmitNetworkRequestAndWait")(&c);
    CHECK(c.x[0] == 0xabc && strstr(last, "rejected"));
    find("HandleNetworkRequestErrorResult")(&c);
    // Pinned SDK sdk+32e950 normalizes this API to bool, and all three
    // main callers branch on bit0. Require both legal bool value and consistent
    // control flow for a C nonzero gate and the actual lifted bit gate.
    CHECK(c.x[0] == 0);
    int retry_bit_gate = (int)(c.x[0] & 1);
    int retry_value_gate = c.x[0] != 0;
    CHECK(!retry_bit_gate && retry_bit_gate == retry_value_gate);
    find("CancelNetworkRequest")(&c);
    uint32_t address = 0x0100007f;
    c.x[0] = (uint64_t)(uintptr_t)&address;
    find("GetCurrentPrimaryIpAddress")(&c);
    CHECK(address == 0 && (c.x[0] & 0x1ff) == 110);
    c.x[0] = 0;   // null output tolerated
    find("GetCurrentPrimaryIpAddress")(&c);
    CHECK((c.x[0] & 0x1ff) == 110);
    uint8_t proxy[8] = {9, 9, 9, 9, 9, 9, 9, 9};
    c.x[0] = (uint64_t)(uintptr_t)proxy;
    find("GetCurrentProxySetting")(&c);
    CHECK((c.x[0] & 0x1ff) == 110 && proxy[0] == 9 && proxy[7] == 9);

    // Account query only: one-byte false, success querying the local host state.
    // Speculative ensure/id/token overrides are intentionally NOT registered.
    uint8_t linked[4] = {1, 7, 7, 7};
    c.x[0] = (uint64_t)(uintptr_t)linked;
    find("IsNetworkServiceAccountAvailable")(&c);
    CHECK(c.x[0] == 0 && linked[0] == 0 && linked[1] == 7);   // one bool written, not an int
    // Friends and album.
    c.x[0] = 5;
    find("friends10Initialize")(&c);
    CHECK(c.x[0] == 5);
    find("ShowUserDetailInfo")(&c);
    CHECK(c.x[0] == 0);
    c.x[0] = 5;
    find("album10Initialize")(&c);
    find("album8Finalize")(&c);
    CHECK(c.x[0] == 5);
    c.x[1] = 3686400;
    find("SaveScreenshot")(&c);
    CHECK(c.x[0] != 0 && (c.x[0] & 0x1ff) == 206 && strstr(last, "3686400 bytes"));
    return 0;
}
'''


def compiler():
    found = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
    if not found:
        for base in (ROOT, Path(os.environ.get('NEWSNAP_ROOT', ROOT))):
            path = base / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            if path.exists():
                return str(path)
    return found


class SnapAppletTests(unittest.TestCase):
    def test_overlay_declares_exactly_the_reviewed_symbols(self):
        text = OVERLAY.read_text(encoding='utf-8')
        declared = re.findall(r'HOST_OVERRIDE\(\s*"([^"]+)"', text)
        self.assertEqual(len(declared), len(set(declared)))
        self.assertEqual(set(declared), EXPECTED)

    def test_no_other_source_overrides_the_same_symbols(self):
        # Two HOST_OVERRIDE entries for one symbol would make the binding depend on link order.
        others = [p for p in (ROOT / 'newsnap/overlays').glob('*') if p.is_file() and p != OVERLAY]
        others += list((ROOT / 'third_party/astral/runtime').glob('*.c'))
        for path in others:
            if path.name.endswith('_probe.c') or path.name == 'ov_probe.c':
                continue   # probes list symbols they call, they do not override them
            text = path.read_text(encoding='utf-8', errors='replace')
            for symbol in EXPECTED:
                self.assertNotIn(f'"{symbol}"', text, f'{symbol} also appears in {path.name}')

    def test_overlay_changes_no_game_state(self):
        text = OVERLAY.read_text(encoding='utf-8')
        for forbidden in ('fopen', 'plat_file', 'save', 'photo_', 'rt_patch', 'memset(', 'ST64', 'ST32'):
            self.assertNotIn(forbidden, text.replace('SaveScreenshot', '').replace('snap_album_save', '')
                             .replace("game's own photo banks", '').replace('photographs or saves', '')
                             .replace('saves:', ''), forbidden)

    def test_native_behaviour(self):
        cc = compiler()
        if not cc:
            self.skipTest('clang is needed for the applet fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            shutil.copyfile(OVERLAY, folder / 'snap_applets.c')
            (folder / 'platform').mkdir()
            (folder / 'host.h').write_text(HOST_H)
            (folder / 'platform/platform.h').write_text('int plat_mem_readable(uint64_t addr, uint64_t n);\n')
            (folder / 'test.c').write_text(TEST_C)
            exe = folder / ('applets.exe' if os.name == 'nt' else 'applets')
            built = subprocess.run([cc, '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', str(folder / 'test.c'),
                                    '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            names = subprocess.run([str(exe), 'names'], capture_output=True, text=True, check=True).stdout.split()
            self.assertEqual(set(names), EXPECTED)
            self.assertEqual(subprocess.run([str(exe), 'null-linked'], capture_output=True).returncode, 3)


if __name__ == '__main__':
    unittest.main()
