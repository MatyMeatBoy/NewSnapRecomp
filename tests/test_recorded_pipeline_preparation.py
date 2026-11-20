import unittest

from newsnap import adapt
from newsnap.upstream import UPSTREAM


class RecordedPipelinePreparationTests(unittest.TestCase):
    def test_standalone_prepares_recorded_whole_pipelines_only_without_gpl(self):
        filename = 'runtime/vk_pipeline.c'
        source = (UPSTREAM / filename).read_text(encoding='utf-8')
        for before, after in adapt.recorded_pipeline_preparation_edits()[filename]:
            self.assertEqual(source.count(before), 1, before)
            source = source.replace(before, after, 1)

        prepare = source.split('int snap_prepare_recorded_pipelines(void) {', 1)[1]
        prepare = prepare.split('\n}', 1)[0]
        self.assertLess(prepare.index('K.read_only = K.warm ='), prepare.index('ensure_init()'))
        self.assertIn('P.gpl || !K.file_n', prepare)
        self.assertLess(prepare.index('prewarm_recorded(0)'), prepare.index('save_pipeline_cache()'))
        self.assertIn('void vk_pipeline_prewarm(void) { prewarm_recorded(1); }', source)
        self.assertIn('if (!K.read_only) gfx_shader_record_at(K.path);', source)
        self.assertIn('if (!K.read_only && !K.header_ok && K.file_n)', source)

    def test_gpl_settings_round_trip_and_default(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from newsnap.launcher_settings import load_settings, save_settings

        with TemporaryDirectory() as temp:
            path = Path(temp) / 'newsnap.ini'
            self.assertEqual(load_settings(path)['gpl'], '')
            for value in ('1', '0', ''):
                save_settings(path, {'gpl': value})
                self.assertEqual(load_settings(path)['gpl'], value)
