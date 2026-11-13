import os
from pathlib import Path
from newsnap.adapt import adapt_sources
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class NativeFrameTests(unittest.TestCase):
    def test_missing_system_storage_never_returns_success_without_object(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang is needed for the native service fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = adapt_sources(folder / 'source') / 'runtime/ov_fsp.c'
            shutil.copyfile(source, folder / 'ov_fsp.c')
            (folder / 'host.h').write_text('void rt_log(const char *, ...);\n')
            (folder / 'ov.h').write_text('')
            (folder / 'ipc.h').write_text('''#include <stdint.h>
typedef struct { int unused; } IpcSession;
typedef struct { unsigned cmd, data_size, ncopy, nmove; } IpcRequest;
typedef struct { uint32_t result; unsigned nmove, data_size; uint8_t data[256]; } IpcResponse;
void ipc_out(IpcResponse *, const void *, uint32_t);
#define IPC_OUT(rs, v) ipc_out(rs, &(v), sizeof(v))
''')
            # The real staged handler runs against a minimal transport, not a duplicate policy.
            (folder / 'test.c').write_text('''#include <string.h>
#include "ipc.h"
void rt_log(const char *s, ...) { (void)s; }
void ipc_out(IpcResponse *r, const void *p, uint32_t n) { memcpy(r->data,p,n); r->data_size=n; }
void fsp_srv_handler(IpcSession *, const IpcRequest *, IpcResponse *);
int main(void) {
 IpcSession s={0}; IpcRequest q={.cmd=202}; IpcResponse r={0};
 fsp_srv_handler(&s,&q,&r);
 if (!r.result || r.nmove || r.data_size) return 1;
 q.cmd=1005; memset(&r,0,sizeof r); fsp_srv_handler(&s,&q,&r);
 return r.result || r.data_size != 4 || r.data[0];
}
''')
            exe = folder / ('fsp-test.exe' if os.name == 'nt' else 'fsp-test')
            subprocess.run([compiler, str(folder / 'ov_fsp.c'), str(folder / 'test.c'),
                            '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_domain_framing_accepts_valid_and_rejects_invalid_messages(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang is needed for the native framing fixture')
        with tempfile.TemporaryDirectory() as temporary:
            exe = Path(temporary) / ('ipc-test.exe' if os.name == 'nt' else 'ipc-test')
            subprocess.run([compiler, str(ROOT / 'tests/ipc_frame.c'), '-I', str(ROOT / 'newsnap/overlays'),
                            '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
