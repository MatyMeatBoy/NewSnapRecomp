import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
import zipfile

from newsnap.diagnostics import export_diagnostics
from newsnap.maintenance import MaintenanceCancelled


class DiagnosticsTests(unittest.TestCase):
    def test_export_contains_readable_session_diagnosis_without_paths(self):
        (self.logs/'newsnap.log').write_text(
            '[host] patches: snap_render on (page 0x7002891000)\n'
            'FATAL: rt_dispatch: no function at guest pc 0x7002c73060 (sdk+0x273060): not a function start\n'
            '[newsnap_launcher] {"event":"exit","exit_code":70}\n')
        export_diagnostics(self.root,self.destination)
        contents=self.read_zip()
        analysis=json.loads(contents['analysis/newsnap.log.json'])
        self.assertEqual(analysis['verdict'],'fatal-runtime')
        self.assertEqual(analysis['fatal']['known'],'jpeg-longjmp')
        self.assertEqual(analysis['observed_exit_code'],70)
        self.assertEqual(analysis['runtime']['identity_basis'],'log-inference-not-executable-hash')
        self.assertNotIn(str(self.root),json.dumps(analysis))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'private-user'/'project'
        self.runtime=self.root/'GameData'
        self.logs=self.runtime/'logs'
        self.logs.mkdir(parents=True)
        (self.runtime/'newsnap-game.json').write_text('{"runtime_version":"0.5.0-alpha"}')
        (self.runtime/'newsnap.exe').write_bytes(b'private binary fixture')
        (self.runtime/'newsnap.ini').write_text('[display]\nvk_present=fifo\nupscaling=off\ncolor_saturation=100\npassword=privatepw\n')
        (self.root/'MANIFEST.json').write_text(json.dumps({'version':'0.5.0-alpha','source_revision':'a'*40,'files':{'private':'omit'}}))
        self.destination=Path(self.temp.name)/'report.zip'

    def read_zip(self):
        with zipfile.ZipFile(self.destination) as archive:
            return {name:archive.read(name).decode() for name in archive.namelist()}

    def test_allowlisted_logs_and_summary_without_owner_payloads(self):
        (self.logs/'newsnap.log').write_text('GPU driver observed here\n')
        (self.logs/'newsnap.1.log').write_text('older runtime\n')
        (self.logs/'astralchain.log').write_text('legacy runtime\n')
        (self.logs/'totk.2.log').write_text('legacy rotation\n')
        (self.logs/'launcher-game-20261113-120000-abcdef01-001.log').write_text('launcher stderr\n')
        for folder in ['profile/save','profile/photos','exefs','romfs']:
            (self.runtime/folder).mkdir(parents=True,exist_ok=True)
            (self.runtime/folder/'never.txt').write_text('PRIVATE OWNER CONTENT')
        (self.logs/'unrelated.log').write_text('PRIVATE OWNER CONTENT')
        (self.logs/'dump.dmp').write_bytes(b'PRIVATE OWNER CONTENT')
        before={path:path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(export_diagnostics(self.root,self.destination),self.destination)
        contents=self.read_zip()
        joined='\n'.join(contents.values())
        self.assertIn('GPU driver observed here',joined)
        self.assertIn('legacy rotation',joined)
        self.assertIn('launcher stderr',joined)
        self.assertNotIn('PRIVATE OWNER CONTENT',joined)
        self.assertNotIn('private binary fixture',joined)
        self.assertNotIn('privatepw',joined)
        summary=json.loads(contents['summary.json'])
        self.assertEqual(summary['runtime']['sha256'],hashlib.sha256(b'private binary fixture').hexdigest())
        self.assertEqual(summary['settings']['values']['vk_present'],'fifo')
        self.assertEqual(before,{path:path.read_bytes() for path in before})

    def test_tokens_secret_lines_and_private_paths_redacted(self):
        (self.logs/'newsnap.log').write_text('hello ghp_'+'x'*36+'\nBearer opaquevalue\n'
            'secret=PRIVATE\napi_key=PRIVATE\npath='+str(self.root/'GameData/profile/save')+'\n'
            r'C:\Users\Alice\Documents\game\file.txt'+'\n/home/alice/game/file.txt\n'
            'sk-proj-'+'y'*30+'\n')
        export_diagnostics(self.root,self.destination)
        joined='\n'.join(self.read_zip().values())
        for private in ['ghp_','opaquevalue','PRIVATE','private-user','Alice','/home/alice','sk-proj-']:
            self.assertNotIn(private,joined)

    def test_actual_zip_redacts_entire_external_paths_with_spaces(self):
        lines=[r'loaded profile E:\Private Family\Holiday Album\save\user-name',
               r'loaded profile "E:\Private Family\Holiday Album\save\user-name"',
               r'loaded profile \\Family Server\Private Share\Holiday Album\save\user-name',
               'loaded profile /home/Family User/Holiday Album/save/user-name',
               'loaded profile "/opt/Private Family/Holiday Album/save/user-name"',
               'safe driver observation remains']
        (self.logs/'newsnap.log').write_text('\n'.join(lines))
        export_diagnostics(self.root,self.destination)
        contents='\n'.join(self.read_zip().values())
        for fragment in ['Private Family','Holiday Album','Family Server','Private Share','Family User','user-name']:
            self.assertNotIn(fragment,contents)
        self.assertIn('safe driver observation remains',contents)

    def test_bounds_and_tail_preserved(self):
        from newsnap import diagnostics
        (self.logs/'newsnap.log').write_text('START\n'+'x'*100000+'\nEND\n')
        with patch.object(diagnostics,'MAX_TEXT_BYTES',1024),patch.object(diagnostics,'MAX_TOTAL_BYTES',8192):
            export_diagnostics(self.root,self.destination)
        contents=self.read_zip()
        self.assertLessEqual(sum(len(value.encode()) for value in contents.values()),8192)
        log=next(value for name,value in contents.items() if name.endswith('newsnap.log'))
        self.assertIn('START',log)
        self.assertIn('END',log)
        self.assertLessEqual(len(log.encode()),1024)

    def test_existing_destination_and_source_alias_never_overwritten(self):
        self.destination.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):export_diagnostics(self.root,self.destination)
        source=self.logs/'newsnap.log'
        source.write_bytes(b'KEEP LOG')
        with self.assertRaises(FileExistsError):export_diagnostics(self.root,source)
        self.assertEqual(source.read_bytes(),b'KEEP LOG')
        self.assertEqual(self.destination.read_bytes(),b'KEEP')

    def test_failure_and_cancellation_leave_no_partial_output(self):
        from newsnap import diagnostics
        with patch.object(diagnostics,'_publish',side_effect=OSError('publication failed')):
            with self.assertRaises(OSError):export_diagnostics(self.root,self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.glob('.newsnap-diagnostics-*')),[])
        event=threading.Event();event.set()
        with self.assertRaises(MaintenanceCancelled):export_diagnostics(self.root,self.destination,cancel_event=event)
        self.assertFalse(self.destination.exists())

    def test_linked_logs_or_destination_parent_are_rejected(self):
        outside=Path(self.temp.name)/'outside';outside.mkdir()
        link=self.logs/'newsnap.log'
        target=outside/'secret';target.write_text('SECRET')
        try:link.symlink_to(target)
        except OSError:self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):export_diagnostics(self.root,self.destination)
        link.unlink()
        parent=Path(self.temp.name)/'linked';parent.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):export_diagnostics(self.root,parent/'report.zip')
        self.assertFalse((outside/'report.zip').exists())

    def test_windows_reparse_attribute_is_rejected_without_symlink_privilege(self):
        from newsnap import diagnostics
        source=self.logs/'newsnap.log';source.write_text('KEEP')
        original=Path.lstat
        def stat_path(path,*args,**kwargs):
            if path==source:
                return types.SimpleNamespace(st_mode=0o100644,st_file_attributes=0x400)
            return original(path,*args,**kwargs)
        with patch.object(Path,'lstat',stat_path):
            with self.assertRaises(ValueError):export_diagnostics(self.root,self.destination)
        self.assertFalse(self.destination.exists())

    def test_cancellation_during_log_collection_and_destination_race(self):
        from newsnap import diagnostics
        (self.logs/'newsnap.log').write_text('KEEP')
        event=threading.Event()
        original=diagnostics._text_log
        def read_log(*args):
            value=original(*args)
            event.set()
            return value
        with patch.object(diagnostics,'_text_log',side_effect=read_log):
            with self.assertRaises(MaintenanceCancelled):export_diagnostics(self.root,self.destination,cancel_event=event)
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.destination.parent.glob('.newsnap-diagnostics-*')))
        publish=diagnostics._publish
        def race(source,target):
            Path(target).write_bytes(b'CONCURRENT OWNER FILE')
            return publish(source,target)
        with patch.object(diagnostics,'_publish',side_effect=race):
            with self.assertRaises(FileExistsError):export_diagnostics(self.root,self.destination)
        self.assertEqual(self.destination.read_bytes(),b'CONCURRENT OWNER FILE')

    def test_publisher_selects_windows_noreplace_rename_and_posix_link(self):
        from newsnap import diagnostics
        for system,selected in [('nt','rename'),('posix','link')]:
            with self.subTest(system=system),patch.object(diagnostics.os,'name',system),\
                    patch.object(diagnostics.os,'rename') as rename,\
                    patch.object(diagnostics.os,'link') as link,\
                    patch.object(diagnostics.os,'replace',side_effect=AssertionError('must never replace')):
                diagnostics._publish('temporary','destination')
                (rename if selected=='rename' else link).assert_called_once_with('temporary','destination')
                (link if selected=='rename' else rename).assert_not_called()
                operation=rename if selected=='rename' else link
                operation.side_effect=FileExistsError('existing destination')
                with self.assertRaises(FileExistsError):diagnostics._publish('temporary','destination')

    def test_structured_redaction_and_historical_display_observation(self):
        (self.root/'MANIFEST.json').write_text(json.dumps({'version':'password=do-not-export','source_revision':'b'*40}))
        value={'format':'newsnap-display-status-v1','version':1,'process_id':123,
            'generation':1,'observed_monotonic_ns':1,'refresh_duration_ns':16666667,
            'refresh_interval_ns':16666667,'source':'vulkan_ext_present_timing',
            'presentation':'fixed','timing_api_available':True,'vk_result':0,
            'display_support':'unknown','driver_enabled':'unknown','monitor_id':'display1',
            'monitor_name':'Test panel','actual_present_mode':'fifo','reason':'observed',
            'private_extra':'DO NOT EXPORT'}
        path=self.logs/'launcher-display-20261113-120000-abcdef01-001.json'
        path.write_text(json.dumps(value))
        os.utime(path,(time.time()-3600,time.time()-3600))
        export_diagnostics(self.root,self.destination)
        contents=self.read_zip()
        summary=json.loads(contents['summary.json'])
        self.assertNotIn('do-not-export',contents['summary.json'])
        observation=summary['display_observations'][0]
        self.assertTrue(observation['historical_snapshot'])
        self.assertGreater(observation['age_seconds'],3500)
        self.assertEqual(observation['display_support'],'unknown')
        self.assertNotIn('private_extra',observation)


if __name__=='__main__':unittest.main()
