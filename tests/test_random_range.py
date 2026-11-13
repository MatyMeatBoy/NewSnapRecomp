"""Pinning plus actual native/generator differential checks, without GPU."""
import ctypes
import contextlib
import _ctypes
import copy
import hashlib
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

from newsnap.random_range_adapt import edits, verify_original, MAIN_SHA256, GENERATOR_GUARD

ROOT = Path(__file__).resolve().parents[1]


class RandomRangeTests(unittest.TestCase):
    def test_sdk_only_guard_rejects_foreign_helper_before_reading_originals(self):
        namespace = {'Path':Path}
        exec(GENERATOR_GUARD, namespace)
        table = types.SimpleNamespace(
            sets=[('snap_random_range','AC_SNAP_RANDOM_RANGE',1)],
            sites={'main':{0x5ec660:[(0,[('fn','snap_random_range'),0xd65f03c0],0xf81b0ff9)]},
                   'sdk':{4:[(0,[('fn','snap_random_range'),0xd65f03c0],0)]}})
        for kind in ['fn','fnz']:
            table.sites['sdk'][4][0][1][0] = (kind,'snap_random_range')
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'unexpected site'):
                namespace['snap_random_range_verify'](None,table,'sdk',Path('nonexistent')/'sdk')

    def test_guard_rejects_either_spin_endpoint_within_the_half_open_span(self):
        namespace = {'Path':Path}
        exec(GENERATOR_GUARD, namespace)
        table = types.SimpleNamespace(
            sets=[('snap_random_range','AC_SNAP_RANDOM_RANGE',1)],
            sites={'main':{0x5ec660:[(0,[('fn','snap_random_range'),0xd65f03c0],0xf81b0ff9)]}},
            spins={})
        for edge,head in [(0x5ec660,0x4000),(0x4000,0x5ec660),
                          (0x5ec7fc,0x4000),(0x4000,0x5ec7fc)]:
            table.spins={'main':{edge:head}}
            for name in ['main','sdk']:
                with self.subTest(edge=edge,head=head,module=name), self.assertRaisesRegex(ValueError,'spin'):
                    namespace['snap_random_range_verify'](None,table,name,Path('nonexistent')/name)
        # The upper bound is exclusive, and another module's unrelated spins
        # are not inside main's verified function. Both proceed to input pins.
        for spins in [{'main':{0x5ec800:0x5ec65c}}, {'sdk':{0x5ec6fc:0x5ec6d0}}]:
            table.spins=spins
            with self.assertRaises(FileNotFoundError):
                namespace['snap_random_range_verify'](None,table,'sdk',Path('nonexistent')/'sdk')

    def test_nonmatching_main_is_rejected_before_decompression(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'main').write_bytes(b'unsupported original')
            with self.assertRaisesRegex(ValueError, 'main SHA'):
                verify_original(folder)

    def test_changed_patch_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            altered = Path(folder)/'patch.txt'
            altered.write_text('set snap_random_range wrong 1\n')
            with self.assertRaisesRegex(ValueError, 'patch'):
                verify_original(folder, patch_file=altered)

    def test_patch_newline_conversion_preserves_the_verified_recipe(self):
        import newsnap.random_range_adapt as bridge
        with tempfile.TemporaryDirectory() as folder:
            patch_file = Path(folder)/'patch.txt'
            patch_file.write_bytes((ROOT/'patches'/bridge.PATCH_NAME).read_text().replace('\n','\r\n').encode())
            (Path(folder)/'main').write_bytes(b'wrong main')
            with self.assertRaisesRegex(ValueError, 'main SHA'):
                verify_original(folder, patch_file=patch_file)

    def test_adapter_anchors_match_the_complete_donor_sources(self):
        for relative, changes in edits().items():
            text = (ROOT/'third_party/astral'/relative).read_text(encoding='utf-8')
            for old, new in changes:
                self.assertEqual(text.count(old), 1, old[:100])
                text = text.replace(old, new, 1)
            compile(text, relative, 'exec') if relative.endswith('.py') else None

    def test_header_and_span_mismatches_are_rejected(self):
        import newsnap.random_range_adapt as bridge
        # Synthetic uncompressed NSO text, with no original game bytes.
        raw = bytearray(0x120)
        raw[:4] = b'NSO0'
        raw[0x40:0x44] = b'test'
        struct.pack_into('<III', raw, 0x10, 0x100, bridge.OFFSET, 0x20)
        struct.pack_into('<I', raw, 0x60, 0x20)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'main'
            path.write_bytes(raw)
            with patch.object(bridge, 'MAIN_SHA256', hashlib.sha256(raw).hexdigest()):
                with self.assertRaisesRegex(ValueError, 'build ID'):
                    verify_original(folder)
                with patch.object(bridge, 'BUILD_ID', '74657374'):
                    with self.assertRaisesRegex(ValueError, 'span'):
                        verify_original(folder)

    @staticmethod
    def compiler():
        sdk = ROOT/'toolchain/astral-release/Astral Chain-Setup'
        cc = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(sdk/'llvm/bin/clang.exe')
        if not (Path(cc).is_file() or shutil.which(cc)):
            raise unittest.SkipTest('clang required for native operation test')
        return cc

    def _build_library(self, folder, extra_sources=()):
        cc = self.compiler()
        runtime = ROOT/'third_party/astral/runtime'
        overlays = ROOT/'newsnap/overlays'
        if not (runtime/'cpu.h').is_file():
            self.skipTest('pinned donor headers required')
        stub = folder/'stubs.c'
        stub.write_text('''#include <stdlib.h>
#include "cpu.h"
volatile int g_fnprof;
void fnprof_hit(uint64_t a,uint64_t b,uint64_t d){}
void rt_udf(Cpu*c,uint64_t pc){abort();}
uint64_t snap_cpu_size(void){return sizeof(Cpu);}
uint8_t rt_patch_on[1]={1};
''')
        objects = []
        for index, (source, optimization) in enumerate([
                (overlays/'snap_random_range.c', '-O2'), (stub, '-O2'), *extra_sources]):
            obj = folder/f'{index}.o'
            result = subprocess.run([cc, optimization, '-fno-strict-aliasing', '-fPIC',
                '-I'+str(runtime), '-I'+str(overlays), '-c', str(source), '-o', str(obj)], capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            objects.append(str(obj))
        library = folder/('random.dll' if os.name == 'nt' else 'random.so')
        command = [cc, '-shared', *objects, '-o', str(library)]
        if os.name == 'nt':
            command.append('-Wl,--export-all-symbols')
        result = subprocess.run(command, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        dll = ctypes.CDLL(str(library))
        dll.snap_cpu_size.restype = ctypes.c_uint64
        self.assertEqual(dll.snap_cpu_size(), 1024)
        return dll

    @contextlib.contextmanager
    def native_library(self, folder, extra_sources=()):
        dll = self._build_library(folder, extra_sources)
        try:
            yield dll
        finally:
            if os.name == 'nt':
                _ctypes.FreeLibrary(dll._handle)
            else:
                _ctypes.dlclose(dll._handle)

    def test_native_results_against_independent_integer_reference(self):
        def step(state):
            a,b,c,d = state
            def signed(value):
                return value if value < 0x80000000 else value-0x100000000
            temporary = (d ^ (d<<11)) & 0xffffffff
            value = (a ^ (signed(a)>>19) ^ temporary ^ (signed(temporary)>>8)) & 0xffffffff
            return value & 0x7fffffff, [value,a,b,c]

        def reference(state, bound):
            if bound == 0:
                return 0, state
            while True:
                first, state = step(state)
                if bound < 0x80000000:
                    result = first // (0x80000000//(bound+1))
                else:
                    second, state = step(state)
                    result = first + (second//0x40000000)*0x80000000
                if result <= bound:
                    return result, state

        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
            with self.native_library(Path(temporary)) as dll:
                dll.snap_random_range.argtypes = [ctypes.c_void_p]
                context = ctypes.create_string_buffer(1024)
                memory = ctypes.create_string_buffer(64)
                cpu, address = ctypes.addressof(context), ctypes.addressof(memory)
                rng = random.Random(660)
                bounds = [0,1,2,3,255,65535,0x7ffffffe,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
                for case in range(4096):
                    state = [rng.getrandbits(32) for _ in range(4)]
                    if case < len(bounds):
                        state = [0x7ffff000,0,0,0]  # forces rejection for selected bounds
                    bound = bounds[case%len(bounds)] if case < 2048 else rng.getrandbits(32)
                    expected, final = reference(state, bound)
                    initial = bytearray(rng.randbytes(1024))
                    alignment = case%4
                    struct.pack_into('<Q', initial, 0, address+16+alignment)
                    struct.pack_into('<Q', initial, 8, (rng.getrandbits(32)<<32)|bound)
                    ctypes.memmove(cpu, bytes(initial), 1024)
                    ctypes.memset(address, 0xA7, 64)
                    ctypes.memmove(address+16+alignment, struct.pack('<4I', *state), 16)
                    dll.snap_random_range(cpu)
                    self.assertEqual(ctypes.c_uint64.from_address(cpu).value, expected)
                    self.assertEqual(ctypes.string_at(address+16+alignment, 16), struct.pack('<4I', *final))
                    self.assertEqual(ctypes.string_at(cpu+19*8, 1024-19*8), bytes(initial[19*8:]))
                    self.assertEqual(ctypes.string_at(address, 16+alignment), b'\xA7'*(16+alignment))
                    self.assertEqual(ctypes.string_at(address+32+alignment, 32-alignment), b'\xA7'*(32-alignment))

    def test_private_actual_generator_entry_and_full_cpu_oracle(self):
        original = ROOT/'newsnapGameData/exefs/main'
        if not original.is_file():
            self.skipTest('optional private verified original unavailable')
        if hashlib.sha256(original.read_bytes()).hexdigest() != MAIN_SHA256:
            self.skipTest('private original is another version')
        verify_original(original.parent)
        # Import the actual generator; emit just this one verified function.
        import types
        generator_path = ROOT/'third_party/astral/recomp/gen.py'
        namespace = {'__file__':str(generator_path), '__name__':'random_range_generator_fixture'}
        text = generator_path.read_text()
        for old,new in edits()['recomp/gen.py']:
            self.assertEqual(text.count(old), 1)
            text = text.replace(old,new,1)
        exec(compile(text,str(generator_path),'exec'),namespace)
        module = namespace['Module']('main', original, 0x7000000000)
        table = namespace['patches'].load(ROOT/'patches/snap-2.0.1-random-range.txt', [('main', module.base, module.nso.size)])
        namespace['snap_random_range_verify'](module,table,'main',original)
        namespace['snap_random_range_verify'](None,table,'sdk',original.with_name('sdk'))
        bad = copy.deepcopy(table)
        bad.sites['main'][0x5ec664] = bad.sites['main'][0x5ec660]
        with self.assertRaisesRegex(ValueError, 'body'):
            namespace['snap_random_range_verify'](module,bad,'main',original)
        bad = copy.deepcopy(table)
        bad.sites['main'][0x5ec660][0][1][-1] = 0
        with self.assertRaisesRegex(ValueError, 'entry'):
            namespace['snap_random_range_verify'](module,bad,'main',original)
        wrong_id = types.SimpleNamespace(image=module.image, nso=types.SimpleNamespace(build_id='wrong'))
        with self.assertRaisesRegex(ValueError, 'main/build/span'):
            namespace['snap_random_range_verify'](wrong_id,table,'main',original)
        changed_image = bytearray(module.image)
        changed_image[0x5ec670] ^= 1
        wrong_span = types.SimpleNamespace(image=changed_image, nso=module.nso)
        with self.assertRaisesRegex(ValueError, 'main/build/span'):
            namespace['snap_random_range_verify'](wrong_span,table,'main',original)
        # Real parser/check accepts this branch: the original emitted path has
        # a scheduler gate that an entry bridge would otherwise silently skip.
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
            spin_patch = Path(temporary)/'with-spin.txt'
            spin_patch.write_text((ROOT/'patches/snap-2.0.1-random-range.txt').read_text()+
                                  '\nspin main 5ec6d0 5ec6fc\n')
            spin_table = namespace['patches'].load(spin_patch,[('main',module.base,module.nso.size)])
            namespace['patches'].check(spin_table,module,'main')
            spin_emitter = namespace['Emitter'](module,{module.base+0x5ec660},
                spin_table.for_module('main',module.base),spins=spin_table.spins_for('main',module.base))
            spin_lines,_ = spin_emitter.function(module.base+0x5ec660,module.base+0x5ec800)
            self.assertIn('rt_spin_gate','\n'.join(spin_lines))
            for name in ['main','sdk']:
                with self.subTest(spin_generation=name), self.assertRaisesRegex(ValueError,'spin'):
                    namespace['snap_random_range_verify'](module,spin_table,name,original.with_name(name))
        emitter = namespace['Emitter'](module, {module.base+0x5ec660}, table.for_module('main',module.base))
        lines, _ = emitter.function(module.base+0x5ec660,module.base+0x5ec800)
        hook = '\n'.join(lines).replace('f_70005ec660','hook_rng')
        # A production regeneration adds the bridge to generated/updated, so
        # that mutable output cannot serve as an independent original oracle.
        # Emit the pinned original bytes again with no patch alternatives or
        # spin gates. Preserve the pre-bridge body pin, not the new hook digest.
        original_emitter = namespace['Emitter'](module, {module.base+0x5ec660}, patched={})
        original_lines, _ = original_emitter.function(module.base+0x5ec660,module.base+0x5ec800)
        body = '\n'.join(original_lines).rstrip() + '\n\n'
        self.assertNotIn('snap_random_range(', body)
        self.assertNotIn('rt_patch_on', body)
        self.assertNotIn('rt_spin_gate(', body)
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), '26e300ede3ed966c7ec1775c6240c9ddc86d201432f08953bc25e3e0f03fbba8')
        oracle = body.replace('f_70005ec660','oracle_rng')
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
            folder = Path(temporary)
            hook_file, oracle_file = folder/'hook.c', folder/'oracle.c'
            hook_file.write_text('#include "snap_random_range.h"\nextern uint8_t rt_patch_on[];\nvoid hook_rng(Cpu*);\n'+hook)
            oracle_file.write_text('#include "cpu.h"\n'+oracle)
            with self.native_library(folder, [(hook_file,'-O1'),(oracle_file,'-O1')]) as dll:
                for name in ['snap_random_range','hook_rng','oracle_rng']:
                    getattr(dll,name).argtypes = [ctypes.c_void_p]
                gate = (ctypes.c_uint8*1).in_dll(dll,'rt_patch_on')
                arena_buffer = ctypes.create_string_buffer(1040)
                cpu_buffer = ctypes.create_string_buffer(1040)
                arena = (ctypes.addressof(arena_buffer)+15)&~15
                cpu = (ctypes.addressof(cpu_buffer)+15)&~15
                rng = random.Random(0x660)
                bounds=[0,1,2,3,255,65535,0x7ffffffe,0x7fffffff,0x80000000,0xfffffffd,0xfffffffe,0xffffffff]
                for case in range(8192):
                    memory, context = rng.randbytes(1024), bytearray(rng.randbytes(1024))
                    bound = bounds[case%len(bounds)] if case < 4096 else rng.getrandbits(32)
                    struct.pack_into('<Q',context,0,arena+32+case%4)
                    struct.pack_into('<Q',context,8,(rng.getrandbits(32)<<32)|bound)
                    struct.pack_into('<Q',context,256,arena+768)
                    def execute(function, enabled):
                        gate[0]=enabled
                        ctypes.memmove(cpu,bytes(context),1024)
                        ctypes.memmove(arena,memory,1024)
                        function(cpu)
                        return ctypes.string_at(cpu,1024),ctypes.string_at(arena,1024)
                    expected, expected_memory = execute(dll.oracle_rng,0)
                    for function,enabled in [(dll.snap_random_range,1),(dll.hook_rng,1),(dll.hook_rng,0)]:
                        actual, actual_memory = execute(function,enabled)
                        self.assertEqual(actual,expected, ('fullCpu',case,enabled))
                        self.assertEqual(actual_memory[32+case%4:48+case%4],expected_memory[32+case%4:48+case%4])
                        self.assertEqual(actual_memory[16:32+case%4],memory[16:32+case%4])
                        self.assertEqual(actual_memory[48+case%4:608],memory[48+case%4:608])
                        self.assertEqual(actual_memory[768:],memory[768:])

    def test_actual_patch_initialization_keeps_profiling_and_opt_out_on_original(self):
        text = (ROOT/'third_party/astral/runtime/patches.c').read_text()
        for old,new in edits()['runtime/patches.c']:
            self.assertEqual(text.count(old),1)
            text = text.replace(old,new,1)
        fixture = r'''
#include "host.h"
#include "cfg.h"
#include <stdlib.h>
volatile int g_fnprof;
static const char *setting;
const char *cfg_get(const char *name){return setting;}
const CfgMeta *cfg_meta(const char *name){return NULL;}
int cfg_bool(const char *name){return 1;}
int plat_mem_commit(uint64_t address,size_t size){return 1;}
void rt_log(const char *format,...){}
void rt_fatal(const char *format,...){abort();}
extern uint8_t rt_patch_on[];
int main(void){
 rt_patches_init();if(!rt_patch_on[0]||!rt_patch_on[1])return 1;
 setting="0";rt_patches_init();if(rt_patch_on[0])return 2;
 setting="1";g_fnprof=1;rt_patches_init();if(rt_patch_on[0]||!rt_patch_on[1])return 3;
 g_fnprof=0;rt_patches_init();return rt_patch_on[0]?0:4;
}
'''
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
            folder = Path(temporary)
            (folder/'patched.c').write_text(text)
            (folder/'fixture.c').write_text(fixture)
            (folder/'patches.h').write_text('#define RT_PATCH_COUNT 2\n#define RT_PATCH_PAGE 0x10000ull\n'
                '#define RT_PATCH_SETS(X) X(0,snap_random_range,"AC_SNAP_RANDOM_RANGE",1) X(1,other,"OTHER",1)\n')
            binary = folder/('fixture.exe' if os.name == 'nt' else 'fixture')
            result = subprocess.run([self.compiler(), '-I'+str(ROOT/'third_party/astral/runtime'),
                str(folder/'patched.c'),str(folder/'fixture.c'),'-o',str(binary)],capture_output=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
            result = subprocess.run([str(binary)],capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,'patch init fixture exit '+str(result.returncode))
