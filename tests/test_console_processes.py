"""Actual donor launch functions, with deterministic process/pipe API stubs."""
import ast
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest.mock import Mock

from newsnap.console_adapt import edits

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'toolchain/astral-release/Astral Chain-Setup'


def adapted(relative):
    source = (ROOT / 'third_party/astral' / relative).read_text(encoding='utf-8')
    for old, new in edits().get(relative, []):
        if source.count(old) != 1:
            raise AssertionError((relative, old, source.count(old)))
        source = source.replace(old, new, 1)
    return source


def function(source, signature):
    start = source.index(signature)
    return source[start:source.index('\n}', start) + 2]


class ConsoleProcessTests(unittest.TestCase):
    def compiler(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(SDK / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native console-process fixture')
        return compiler

    def test_actual_reexec_restart_and_probe_preserve_process_and_pipe_contracts(self):
        source = adapted('runtime/platform/win32.c')
        prelude = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <setjmp.h>
#define _wcsdup fixture_wcsdup
typedef void *HANDLE;typedef void *HWND;typedef unsigned long DWORD;typedef int BOOL;
typedef struct {unsigned nLength;void *lpSecurityDescriptor;int bInheritHandle;} SECURITY_ATTRIBUTES;
typedef struct {unsigned cb,dwFlags;HANDLE hStdInput,hStdOutput,hStdError;} STARTUPINFOW;
typedef struct {HANDLE hProcess,hThread;} PROCESS_INFORMATION;
#define TRUE 1
#define FALSE 0
#define CREATE_NO_WINDOW 0x08000000ul
#define STARTF_USESTDHANDLES 0x100
#define HANDLE_FLAG_INHERIT 1
#define STD_INPUT_HANDLE ((DWORD)-10)
#define WAIT_OBJECT_0 0
#define WAIT_TIMEOUT 258
#define INFINITE 0xfffffffful
#define RESTART_WAIT "AC_RESTART_WAIT"
static int console,create_fail,timeout_once,closes,terminated,environment_set,environment_clear,waits;
static DWORD flags,exit_code,last_timeout;static int inherit;static STARTUPINFOW startup;
static char pipe_data[]="hello\r\n";static size_t read_at;static jmp_buf ended;
static HWND GetConsoleWindow(void){return console?(HWND)1:NULL;}
static wchar_t *GetCommandLineW(void){return L"fixture.exe --unchanged";}
static wchar_t *_wcsdup(const wchar_t *s){size_t n=(wcslen(s)+1)*sizeof *s;wchar_t *p=malloc(n);memcpy(p,s,n);return p;}
static DWORD GetLastError(void){return 5;}
static BOOL CreateProcessW(void*a,wchar_t*b,void*c,void*d,BOOL inh,DWORD f,void*g,void*h,STARTUPINFOW*si,PROCESS_INFORMATION*pi){
 if(wcscmp(b,L"fixture.exe --unchanged"))abort();
 flags=f;inherit=inh;startup=*si;pi->hProcess=(HANDLE)11;pi->hThread=(HANDLE)12;return !create_fail;
}
static BOOL CloseHandle(HANDLE h){if(h!=(HANDLE)11&&h!=(HANDLE)12&&h!=(HANDLE)13&&h!=(HANDLE)14)abort();closes++;return 1;}
static DWORD WaitForSingleObject(HANDLE h,DWORD ms){waits++;last_timeout=ms;if(timeout_once){timeout_once=0;return WAIT_TIMEOUT;}return WAIT_OBJECT_0;}
static BOOL GetExitCodeProcess(HANDLE h,DWORD *code){*code=37;return 1;}
static void ExitProcess(DWORD code){exit_code=code;longjmp(ended,1);}
static BOOL TerminateProcess(HANDLE h,unsigned code){terminated++;return 1;}
static BOOL CreatePipe(HANDLE *r,HANDLE*w,SECURITY_ATTRIBUTES*s,DWORD n){*r=(HANDLE)13;*w=(HANDLE)14;return 1;}
static BOOL SetHandleInformation(HANDLE h,DWORD mask,DWORD value){return 1;}
static HANDLE GetStdHandle(DWORD n){return (HANDLE)15;}
static BOOL ReadFile(HANDLE h,void *out,DWORD n,DWORD *got,void *overlapped){
 size_t left=strlen(pipe_data)-read_at;if(n>left)n=(DWORD)left;memcpy(out,pipe_data+read_at,n);read_at+=n;*got=n;return 1;
}
static BOOL SetEnvironmentVariableA(const char*n,const char*v){if(v)environment_set++;else environment_clear++;return 1;}
static void plat_setenv(const char*n,const char*v){SetEnvironmentVariableA(n,v);}
static DWORD GetCurrentProcessId(void){return 123;}
static HANDLE GetCurrentProcess(void){return (HANDLE)1;}
static uint64_t process_created(HANDLE h){return 456;}
static void reset(void){
 create_fail=timeout_once=closes=terminated=environment_set=environment_clear=waits=0;
 flags=exit_code=last_timeout=0;inherit=-1;memset(&startup,0,sizeof startup);read_at=0;
}
'''
        main = r'''
int main(void){
 for(console=0;console<=1;console++){
  reset();if(!setjmp(ended))plat_reexec();
  if(flags!=(console?0:CREATE_NO_WINDOW)||inherit!=TRUE)return 1;
  if(exit_code!=37||closes!=1||waits!=1||last_timeout!=INFINITE)return 2;
  reset();create_fail=1;if(!setjmp(ended))plat_reexec();
  if(exit_code!=70||closes||waits)return 3;
  reset();if(!plat_restart())return 4;
  if(flags!=(console?0:CREATE_NO_WINDOW)||inherit!=FALSE||closes!=2||waits)return 5;
  if(environment_set!=1||environment_clear!=1)return 6;
  reset();create_fail=1;if(plat_restart()||closes||waits||environment_clear!=1)return 7;
  char out[32];
  reset();if(plat_run_self("probe","1",out,4,123)!=37||strcmp(out,"hel"))return 8;
  if(flags!=CREATE_NO_WINDOW||inherit!=TRUE||startup.dwFlags!=STARTF_USESTDHANDLES||
    startup.hStdInput!=(HANDLE)15||startup.hStdOutput!=(HANDLE)14||startup.hStdError!=(HANDLE)14)return 9;
  if(read_at!=7||closes!=4||waits!=1||last_timeout!=123||environment_clear!=1)return 10;
  reset();timeout_once=1;
  if(plat_run_self("probe","1",out,sizeof out,123)!=37||strcmp(out,"hello\r\n")||terminated!=1||waits!=2||last_timeout!=INFINITE||closes!=4)return 11;
  reset();create_fail=1;if(plat_run_self("probe","1",out,sizeof out,123)!=-1||closes!=2||waits||environment_clear!=1)return 12;
 }
 return 0;
}
'''
        selected = '\n'.join(function(source, signature) for signature in (
            'void plat_reexec(', 'int plat_run_self(', 'int plat_restart('))
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fixture = folder / 'console.c'
            fixture.write_text(prelude + selected + main, encoding='utf-8')
            executable = folder / ('console.exe' if os.name == 'nt' else 'console')
            result = subprocess.run([self.compiler(), str(fixture), '-o', str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            result = subprocess.run([str(executable)], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, 'native launch/pipe contract exit ' + str(result.returncode))

    def test_actual_ninja_launcher_keeps_suspension_job_cleanup_and_exit(self):
        source = adapted('tools/build_game.py')
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_measured')
        constants = {target.id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     for target in n.targets if isinstance(target, ast.Name)
                     and target.id in ('CREATE_SUSPENDED', 'CREATE_NO_WINDOW')}
        for interrupted in (False, True):
            with self.subTest(interrupted=interrupted):
                k32, ntdll = Mock(), Mock()
                k32.CreateJobObjectW.return_value = 11
                k32.AssignProcessToJobObject.return_value = True
                info = types.SimpleNamespace(BasicLimitInformation=types.SimpleNamespace(LimitFlags=0),
                                             PeakProcessMemoryUsed=71, PeakJobMemoryUsed=92)
                process = Mock(_handle=123)
                process.wait.side_effect = KeyboardInterrupt if interrupted else None
                process.wait.return_value = 37
                popen = Mock(return_value=process)
                namespace = {'WIN': True, 'ROOT': ROOT, **constants,
                    'JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE': 0x2000,
                    'JOB_OBJECT_EXTENDED_LIMIT_INFORMATION': 9, 'ExtendedLimits': lambda: info,
                    'ctypes': types.SimpleNamespace(WinDLL=lambda name, **kw: k32 if name == 'kernel32' else ntdll,
                                                   byref=lambda value: value, sizeof=lambda value: 1,
                                                   c_void_p=int, c_int=int),
                    'wt': types.SimpleNamespace(HANDLE=int, LPCWSTR=str, BOOL=int, DWORD=int),
                    'subprocess': types.SimpleNamespace(Popen=popen),
                    'time': types.SimpleNamespace(monotonic=Mock(side_effect=(1.0, 2.25)))}
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual run_measured>', 'exec'), namespace)
                command, env = ['ninja.exe', '-f', 'build.ninja'], {'fixture': 'unchanged'}
                if interrupted:
                    with self.assertRaises(KeyboardInterrupt):
                        namespace['run_measured'](command, env)
                else:
                    self.assertEqual(namespace['run_measured'](command, env), (37, 1.25, 71, 92))
                popen.assert_called_once_with(command, cwd=ROOT, env=env, creationflags=0x08000004)
                k32.AssignProcessToJobObject.assert_called_once_with(11, 123)
                ntdll.NtResumeProcess.assert_called_once_with(123)
                k32.CloseHandle.assert_called_once_with(11)
                self.assertEqual(info.BasicLimitInformation.LimitFlags, 0x2000)

    @unittest.skipUnless(os.name == 'nt', 'full Windows translation unit requires Windows compiler headers')
    def test_complete_adapted_windows_unit_compiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'win32.c'
            source.write_text(adapted('runtime/platform/win32.c'), encoding='utf-8')
            result = subprocess.run([self.compiler(), '-fsyntax-only', '-I'+str(ROOT/'third_party/astral/runtime'),
                '-I'+str(ROOT/'third_party/astral/runtime/platform'), str(source)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
