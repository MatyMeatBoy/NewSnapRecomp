import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class TimeTests(unittest.TestCase):
    def test_device_rule_roundtrip_and_invalid_rules(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            path = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(path) if path.exists() else None
        if not compiler:
            self.skipTest('clang is needed for the time fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            shutil.copyfile(ROOT / 'newsnap/overlays/snap_time.c', folder / 'snap_time.c')
            (folder / 'host.h').write_text('''#include <stdint.h>
typedef struct { uint64_t x[31]; } Cpu;
static inline void *arg_p(Cpu *c,int n) { return (void *)(uintptr_t)c->x[n]; }
void rt_fatal(const char *, ...);
#define HOST_OVERRIDE(name, fn)
''')
            (folder / 'test.c').write_text('''#include <stdlib.h>
#include "snap_time.c"
static int converted;
void rt_fatal(const char *s, ...) { (void)s; exit(3); }
void ov_time_location(char out[0x24]) { memset(out,0,0x24); memcpy(out,"Etc/GMT+4",9); }
void ov_time_calendar(Cpu *c) { converted++; c->x[0]=0; }
int main(void) {
 unsigned char location[0x25], rule[0x4001];
 memset(location,0xcc,sizeof location); memset(rule,0xcc,sizeof rule);
 Cpu c={0}; c.x[0]=(uintptr_t)location; snap_device_location(&c);
 if (location[0x24]!=0xcc || strcmp((char *)location,"Etc/GMT+4")) return 1;
 c.x[0]=(uintptr_t)rule; c.x[1]=(uintptr_t)location; snap_load_time_rule(&c);
 if (c.x[0] || rule[0x4000]!=0xcc) return 1;
 c.x[3]=(uintptr_t)rule; snap_to_calendar_rule(&c);
 if (c.x[0] || converted!=1) return 1;
 rule[0]^=1; snap_to_calendar_rule(&c);
 if (!c.x[0] || converted!=1) return 1;
 c.x[0]=(uintptr_t)rule; location[0]='X'; c.x[1]=(uintptr_t)location;
 snap_load_time_rule(&c); if (!c.x[0]) return 1;
 c.x[0]=0; snap_load_time_rule(&c); if (!c.x[0]) return 1;
 c.x[0]=1; snap_network_accuracy(&c); return c.x[0]!=0;
}
''')
            exe = folder / ('time.exe' if os.name == 'nt' else 'time')
            subprocess.run([compiler, str(folder / 'test.c'), '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
