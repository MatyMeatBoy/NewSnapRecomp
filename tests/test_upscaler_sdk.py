import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import fetch_upscaler_sdk as sdk
from newsnap.upscaler_adapt import edits, stage_sdk

ROOT = Path(__file__).resolve().parents[1]


class SdkIntegrityTests(unittest.TestCase):
    def test_download_failure_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'payload'
            target.write_bytes(b'previous')
            with patch.dict(sdk.FILES, {'payload': (4, 'wrong')}, clear=True):
                with self.assertRaisesRegex(ValueError, 'integrity'):
                    sdk.fetch(directory, opener=lambda *a, **kw: io.BytesIO(b'bad!'))
            self.assertEqual(target.read_bytes(), b'previous')

    def test_pins_are_full_commit_and_hashes(self):
        self.assertEqual(len(sdk.COMMIT), 40)
        self.assertEqual(len(sdk.FILES), 12)   # + FG-01 frame generation DLL and headers
        for name, (size, digest) in sdk.FILES.items():
            self.assertNotIn('..', Path(name).parts)
            self.assertGreater(size, 0)
            self.assertEqual(len(digest), 64)

    def test_staging_rejects_unverified_sdk(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'pinned'):
                stage_sdk(directory, Path(directory) / 'output')

    def test_build_seam_is_exact(self):
        for name, changes in edits().items():
            text = (ROOT / 'third_party/astral' / name).read_text(encoding='utf-8')
            for before, after in changes:
                self.assertEqual(text.count(before), 1)
                text = text.replace(before, after)
            if name.endswith('.py'):
                compile(text, name, 'exec')
            if name == 'runtime/vk_device.c':
                self.assertLess(text.index('CHAIN(fsr_derivatives,'), text.index('CHAIN(gpl,'))

    def test_resource_contract_and_sdk_compile(self):
        toolchain = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        compiler = toolchain / 'llvm/bin/clang.exe'
        include = toolchain / 'runtime/deps/include'
        if not compiler.is_file():
            self.skipTest('LLVM Vulkan SDK compiler unavailable')
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            fixture = directory / 'contract.c'
            fixture.write_text(r'''
#include "snap_fsr_sdk.h"
#include <assert.h>
#include <math.h>
#include <string.h>
static SnapFsrImage image(unsigned id, VkFormat format, int output) {
    return (SnapFsrImage){.image=(VkImage)(uintptr_t)id, .format=format,
        .layout=output ? VK_IMAGE_LAYOUT_GENERAL : VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        .usage=output ? VK_IMAGE_USAGE_STORAGE_BIT : VK_IMAGE_USAGE_SAMPLED_BIT,
        .width=output ? 1920 : 1280, .height=output ? 1080 : 720,
        .samples=1, .layers=1, .mips=1, .generation=7};
}
int main(void) {
    SnapFsrConfig c={.render_width=1280,.render_height=720,.output_width=1920,.output_height=1080,
        .generation=7,.auto_exposure=1,.device_contract_verified=1};
    SnapFsrFrame f={.command_buffer=(VkCommandBuffer)1,.scene_contract_verified=1,
        .delta_ms=16.67f,.pre_exposure=1,.camera_near=.1f,.camera_far=1000,.vertical_fov=1,.meters_factor=1,
        .motion_scale_x=1,.motion_scale_y=1};
    f.color=image(1,VK_FORMAT_R16G16B16A16_SFLOAT,0); f.depth=image(2,VK_FORMAT_D32_SFLOAT,0);
    f.motion=image(3,VK_FORMAT_R16G16_SFLOAT,0); f.output=image(4,VK_FORMAT_R16G16B16A16_SFLOAT,1);
    assert(snap_fsr_sdk_validate(&c,&f));
    f.scene_contract_verified=0; assert(!snap_fsr_sdk_validate(&c,&f)); f.scene_contract_verified=1;
    f.color.layout=VK_IMAGE_LAYOUT_GENERAL; assert(!snap_fsr_sdk_validate(&c,&f));
    f.color.layout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    f.depth.generation=8; assert(!snap_fsr_sdk_validate(&c,&f)); f.depth.generation=7;
    f.motion.samples=4; assert(!snap_fsr_sdk_validate(&c,&f)); f.motion.samples=1;
    f.output.image=f.color.image; assert(!snap_fsr_sdk_validate(&c,&f)); f.output.image=(VkImage)4;
    f.pre_exposure=NAN; assert(!snap_fsr_sdk_validate(&c,&f)); f.pre_exposure=1;
    c.auto_exposure=0; assert(!snap_fsr_sdk_validate(&c,&f)); c.auto_exposure=1;
    assert(snap_fsr_sdk_validate(&c,&f));
    assert(!snap_fsr_sdk_open()); assert(!snap_fsr_sdk_dispatch(0,&f)); snap_fsr_sdk_close(0);
    uint64_t total=123,aliasable=456;
    assert(!snap_fsr_sdk_memory_usage(0,&total,&aliasable)); assert(total==0 && aliasable==0);
    total=123; assert(!snap_fsr_sdk_memory_usage(0,&total,0)); assert(total==0);
    assert(!snap_fsr_sdk_memory_usage(0,0,0));
    return 0;
}
''', encoding='utf-8')
            # Execute the actual adapted auto selection, including simultaneous provider availability.
            donor = (ROOT / 'third_party/astral/runtime/vk_dlaa.c').read_text(encoding='utf-8')
            for before, after in edits()['runtime/vk_dlaa.c']:
                donor = donor.replace(before, after)
            policy = donor[donor.index('static int chosen(void) {'):donor.index('static int pick(void) {')]
            policy = '''enum { BK_NONE, BK_DLSS, BK_XESS, BK_FSR3, BK_FSR4 };
static unsigned mask;
static int can(int bk) { return (mask & (1u << bk)) != 0; }
static const char *cfg_upscaling(void) { return "auto"; }
''' + policy
            content = fixture.read_text(encoding='utf-8').replace('int main(void) {', policy + '''int main(void) {
    mask=1u<<BK_FSR3; assert(chosen()==BK_FSR3);
    mask=(1u<<BK_FSR3)|(1u<<BK_FSR4); assert(chosen()==BK_FSR4);
    mask=(1u<<BK_FSR3)|(1u<<BK_FSR4)|(1u<<BK_DLSS); assert(chosen()==BK_DLSS);
    mask=1u<<BK_FSR4; assert(chosen()==BK_FSR4);
''')
            fixture.write_text(content, encoding='utf-8')
            source = ROOT / 'newsnap/overlays/snap_fsr_sdk.c'
            common = [str(compiler), '-Wall', '-Werror', '-I', str(include), '-I', str(source.parent)]
            exe = directory / 'contract.exe'
            subprocess.run(common + [str(fixture), str(source), '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
            sdk_root = ROOT / 'toolchain/fsr-sdk-2.4.0'
            if sdk.verify(sdk_root):
                subprocess.run(common + ['-DNEWSNAP_FSR_SDK=1', '-I', str(sdk_root / 'Kits/FidelityFX'),
                    '-fsyntax-only', str(source)], check=True, capture_output=True)

    def test_fsr_only_retirements_are_polled_after_switching_off(self):
        text = (ROOT / 'third_party/astral/runtime/vk_dlaa.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/vk_dlaa.c']:
            text = text.replace(before, after)
        present = text[text.index('int vk_dlaa_frame(void) {'):]
        cleanup = present.index('if (D.sizes[i].out) free_size(&D.sizes[i]);')
        poll = present.index('    snap_fsr_runtime_sweep(0);')
        conditional_ngx = present.index('    if (N.loaded) features_sweep(0);')
        self.assertLess(cleanup, poll)
        self.assertLess(poll, conditional_ngx)

    def test_choice_state_uses_queried_fsr_providers(self):
        text = (ROOT / 'third_party/astral/runtime/vk_dlaa.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/vk_dlaa.c']:
            text = text.replace(before, after)
        choice = text[text.index('int vk_dlaa_choice_state('):text.index('const char *vk_dlaa_upscaler_name(')]
        self.assertIn('if (!strcmp(up, "fsr3")) return can(BK_FSR3) ? 0 : 2;', choice)
        self.assertIn('if (!strcmp(up, "fsr4")) return can(BK_FSR4) ? 0 : 2;', choice)
        self.assertNotIn('vk_fsr3_failed()', choice)


if __name__ == '__main__':
    unittest.main()
