"""Frontendless catalog and startup checks never take ownership of gameplay."""
import queue
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
from newsnap import update_ui,maintenance_ui


class ImmediateThread:
    def __init__(self,target,**kwargs):self.target=target
    def start(self):self.target()


class Widget:
    def __init__(self,*args,**kwargs):self.options=dict(kwargs);self.index=-1;self.bindings={}
    def pack(self,*args,**kwargs):pass
    def configure(self,**kwargs):self.options.update(kwargs)
    def current(self,index=None):
        if index is not None:self.index=index
        return self.index
    def set(self,value):self.value=value
    def bind(self,event,callback):self.bindings[event]=callback


def release(tag):return SimpleNamespace(tag_name=tag,version=tag.removeprefix('v'))


def panel():
    value=update_ui.UpdatePanel.__new__(update_ui.UpdatePanel)
    value.root=SimpleNamespace(after=Mock(),destroy=Mock())
    value.launcher=SimpleNamespace(root=value.root,busy=False,project=Path('fixture'),
        _set_busy=Mock(),save_options=Mock(return_value=True),notify_update=Mock(),
        status=SimpleNamespace(set=Mock()),tabs=SimpleNamespace(select=Mock()))
    value.events=queue.Queue()
    value.release=None
    value.catalog=[]
    value.working=False
    value.checking_stable=False
    value.installing=False
    value.check,value.install,value.status,value.selector=Widget(),Widget(),Widget(),Widget()
    return value


class AutomaticNoticeTests(TestCase):
    def test_only_strictly_newer_stable_notifies_without_selecting_or_installing(self):
        for tag,expected in [('v0.6.0',True),('v0.5.0',False),('v0.4.0',False),(None,False)]:
            with self.subTest(tag=tag):
                value=panel()
                value.launcher.busy=True
                chosen=release('v0.7.0-alpha')
                value.release=chosen
                value.download=Mock()
                incoming=release(tag) if tag else None
                with patch.object(update_ui,'VERSION','0.5.0'),\
                     patch.object(update_ui.updater,'check_stable',return_value=incoming),\
                     patch.object(update_ui.threading,'Thread',ImmediateThread):
                    value.check_stable()
                    value.poll()
                self.assertEqual(value.launcher.notify_update.call_count,int(expected))
                self.assertIs(value.release,chosen)
                value.download.assert_not_called()
                value.launcher._set_busy.assert_not_called()
                value.launcher.status.set.assert_not_called()
                value.launcher.tabs.select.assert_not_called()
                self.assertTrue(value.launcher.busy)

    def test_automatic_failure_cannot_release_a_concurrent_download_or_change_footer(self):
        value=panel()
        value.working=value.installing=value.launcher.busy=True
        with patch.object(update_ui.updater,'check_stable',side_effect=OSError('offline')),\
             patch.object(update_ui.threading,'Thread',ImmediateThread):
            value.check_stable()
            value.poll()
        self.assertTrue(value.working)
        self.assertTrue(value.installing)
        value.launcher._set_busy.assert_not_called()
        value.launcher.status.set.assert_not_called()
        value.launcher.tabs.select.assert_not_called()

    def test_same_new_stable_is_not_repeated_as_multiple_notifications(self):
        value=panel()
        with patch.object(update_ui,'VERSION','0.5.0'):
            value.events.put(('stable',release('v0.6.0')))
            value.events.put(('stable',release('v0.6.0')))
            value.poll()
        value.launcher.notify_update.assert_called_once()


class ManualCatalogTests(TestCase):
    def test_manual_catalog_defaults_newest_alpha_and_can_select_same_version_for_repair(self):
        value=panel()
        alpha,current=release('v0.6.0-alpha'),release('v0.5.0')
        with patch.object(sys,'frozen',True,create=True),\
             patch.object(update_ui.updater,'list_releases',return_value=[alpha,current]) as fetch,\
             patch.object(update_ui.threading,'Thread',ImmediateThread):
            value.check_catalog()
            value.poll()
            self.assertIs(value.release,alpha)
            self.assertEqual(value.selector.options['values'],(alpha.tag_name,current.tag_name))
            self.assertEqual(value.install.options['state'],'normal')
            value.selector.current(1)
            value.select_release()
            self.assertIs(value.release,current)
            self.assertEqual(value.install.options['state'],'normal')
        fetch.assert_called_once_with()
        value.launcher.notify_update.assert_not_called()
        value.launcher.tabs.select.assert_not_called()

    def test_download_uses_selected_alpha_and_confirmation_does_not_call_it_stable(self):
        value=panel()
        value.release=release('v0.6.0-alpha')
        with tempfile.TemporaryDirectory() as temporary,patch.object(sys,'frozen',True,create=True),\
             patch.object(update_ui.settings,'validate_runtime_data',side_effect=ValueError('old runtime')),\
             patch.object(update_ui.messagebox,'askyesno',return_value=True) as confirm,\
             patch.object(update_ui.tempfile,'mkdtemp',return_value=temporary),\
             patch.object(update_ui.updater,'stage_update',return_value=Path(temporary)) as stage,\
             patch.object(update_ui.threading,'Thread',ImmediateThread):
            value.download()
        self.assertIs(stage.call_args.args[0],value.release)
        self.assertNotIn('estable',' '.join(confirm.call_args.args).lower())
        self.assertIn(value.release.tag_name,' '.join(confirm.call_args.args))
        value.launcher.save_options.assert_not_called()
        value.launcher._set_busy.assert_called_once_with(True)


class StartupOwnershipTests(TestCase):
    def test_maintenance_constructor_schedules_only_poll_and_never_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'GameData').mkdir()
            (root/'GameData/newsnap-game.json').write_text('{}')
            launcher=SimpleNamespace(project=root,root=SimpleNamespace(after=Mock()),busy=False)
            with patch.object(maintenance_ui.ttk,'Frame',Widget),patch.object(maintenance_ui.ttk,'Button',Widget):
                value=maintenance_ui.RuntimeMaintenance(launcher,Widget(),Widget())
            callbacks=[call.args[1] for call in launcher.root.after.call_args_list]
            self.assertEqual(callbacks,[value.poll])
            self.assertFalse(value.active)
            self.assertFalse(list((root/'GameData').glob('.runtime-*')))

class ConstructorIsolationTests(TestCase):
    def test_opening_updates_with_no_gamedata_never_creates_it_or_schedules_a_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            project=Path(temporary)
            launcher=SimpleNamespace(project=project,root=SimpleNamespace(after=Mock()),busy=False)
            with patch.object(update_ui.ttk,'Label',Widget),patch.object(update_ui.ttk,'Frame',Widget),\
                 patch.object(update_ui.ttk,'Button',Widget),patch.object(update_ui.ttk,'Combobox',Widget),\
                 patch.object(update_ui.threading,'Thread',ImmediateThread),patch.object(sys,'frozen',True,create=True):
                value=update_ui.UpdatePanel(launcher,Widget())
            self.assertEqual(list(project.iterdir()),[])
            callbacks=[call.args[1] for call in launcher.root.after.call_args_list]
            self.assertEqual(callbacks,[value.maintenance.poll,value.poll,value.check_stable])
            self.assertEqual(value.check.options['command'],value.check_catalog)

    def test_stale_maintenance_events_cannot_release_another_busy_operation(self):
        value=maintenance_ui.RuntimeMaintenance.__new__(maintenance_ui.RuntimeMaintenance)
        value.events=queue.Queue()
        value.events.put(('progress','late progress'))
        value.events.put(('error','late failure'))
        value.active=False
        value.resume_game=False
        value.status,value.repair,value.cancel=Mock(),Mock(),Mock()
        value.launcher=SimpleNamespace(root=SimpleNamespace(after=Mock()),_set_busy=Mock(),
            busy=True,status=SimpleNamespace(set=Mock()))
        value.poll()
        value.launcher._set_busy.assert_not_called()
        value.launcher.status.set.assert_not_called()

class CatalogSelectionOwnershipTests(TestCase):
    def test_automatic_notice_cannot_replace_manual_selection_status(self):
        value=panel()
        chosen=release('v0.7.0-alpha')
        value.catalog=[chosen]
        value.release=chosen
        value.status.configure(text='Versión elegida: v0.7.0-alpha')
        with patch.object(update_ui,'VERSION','0.5.0'):
            value.events.put(('stable',release('v0.6.0')))
            value.poll()
        self.assertEqual(value.status.options['text'],'Versión elegida: v0.7.0-alpha')
        self.assertIs(value.release,chosen)
        value.launcher.notify_update.assert_called_once()


class MaintenanceCompletionTests(TestCase):
    def test_verified_cleanup_reports_checked_routes_and_actual_removed_count(self):
        result={'rebuilt':True,'replacement':{'cache_absence_verified':True,
            'transaction_removed':True,'build_temporaries_removed':True,
            'invalidated':['a','b','c','d','e'],'removed_existing':['a','b'],'log_recorded':True}}
        message=maintenance_ui.completion_message(result)
        self.assertIn('5/5',message)
        self.assertIn('2 retiradas',message)
        self.assertIn('sin copias temporales',message)

    def test_absent_or_incomplete_receipt_never_claims_cleanup(self):
        for replacement in ({},{'cache_absence_verified':True,'transaction_removed':False}):
            message=maintenance_ui.completion_message({'rebuilt':True,'replacement':replacement})
            self.assertIn('sin comprobante de limpieza',message)
            self.assertNotIn('5/5',message)

    def test_log_write_failure_does_not_hide_successful_runtime_activation(self):
        result={'rebuilt':True,'replacement':{'cache_absence_verified':True,
            'transaction_removed':True,'build_temporaries_removed':True,
            'invalidated':['a'],'removed_existing':[],'log_recorded':False}}
        message=maintenance_ui.completion_message(result)
        self.assertIn('verificado',message)
        self.assertIn('no se pudo guardar',message)
