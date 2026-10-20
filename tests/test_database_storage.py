"""Production SQLite storage: migration, offline metadata and recoverable file operations."""
import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import test_server as fixtures
from test_server import manager
import file_comments
import file_trash
import folder_rename
import folder_rename_undo
import event_folders
import event_folder_undo
import order_document as document
from local_metadata import MetadataStore
from mobile_sync import MobileBridge


class DatabaseStorageTests(unittest.TestCase):
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    tearDown = fixtures.ManagerTests.tearDown

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager,'DATABASE_ONLY',True)
        mode.start(); self.patches.append(mode)
        self.order = 'Клиент/Объект/2026-10-20 - Заказ'
        self.event = self.order+'/00 - Замеры'
        self.folder(self.event)
        self.store = manager.order_store()
        self.meta = MetadataStore(self.store)

    def register(self):
        self.store.import_folder(self.order)
        return self.store.get(self.order)

    def test_comments_import_once_preserve_bytes_and_work_without_cloud(self):
        path = self.root/self.event/'IMG.MOV'; path.write_bytes(b'movie')
        old = file_comments.save(path,'Прежний текст','missing')
        sidecar = file_comments.paths(path)[3]; original = sidecar.read_bytes()
        imported = self.meta.comment(path)
        self.assertEqual(imported['comment'],'Прежний текст')
        with patch('icloud_access.read_bytes',side_effect=OSError('offline')):
            saved = self.meta.save_comment(path,'Новый\nтекст',imported['revision'])
            self.assertEqual(MetadataStore(manager.order_store()).comment(path),saved)
            with self.assertRaises(file_comments.FileCommentConflict):
                self.meta.save_comment(path,'stale',imported['revision'])
        self.assertEqual(sidecar.read_bytes(),original)
        with self.meta.connect() as db:
            self.assertEqual(db.execute('SELECT body FROM legacy_documents').fetchone()[0],original)
            self.assertIn('Прежний текст',db.execute("SELECT data FROM metadata_history WHERE entity='metadata_records'").fetchone()[0])

    def test_failed_import_retries_without_replacing_text(self):
        path=self.root/self.event/'IMG.MOV';path.write_bytes(b'original')
        file_comments.save(path,'Ценный текст','missing')
        with patch('icloud_access.read_bytes',side_effect=OSError(11,'iCloud unavailable')):
            with self.assertRaises(OSError): self.meta.comment(path)
            with self.assertRaises(OSError): self.meta.save_comment(path,'','missing')
        self.assertTrue(self.meta.status()['errors'])
        self.assertEqual(self.meta.comment(path)['comment'],'Ценный текст')
        self.assertFalse(self.meta.status()['errors'])

    def test_all_folder_notes_are_database_only_and_stale_files_do_not_win(self):
        for relative in ('Клиент','Клиент/Объект',self.event,'# docs/Внутри'):
            with self.subTest(relative=relative):
                target=self.root/relative
                document.atomic_write(target/'!.txt',document.render({'note':'Старая','extra_blocks':{'Неизвестно':'не менять'}},manager.STATUS_LABELS))
                original=(target/'!.txt').read_bytes()
                notes=manager.folder_note_store();record=notes.read(relative)
                with patch('icloud_access.read_bytes',side_effect=OSError('offline')):
                    saved=notes.save({'path':relative,'revision':record['revision'],'note':'Новая'})
                    notes.sync()
                    self.assertEqual(notes.read(relative)['note'],'Новая')
                self.assertEqual(saved['extra_blocks']['Неизвестно'],'не менять')
                self.assertFalse(saved['sync_pending'])
                self.assertEqual((target/'!.txt').read_bytes(),original)
        self.assertEqual(self.store.list(),[])

    def test_registered_card_and_tasks_do_not_write_metadata_files(self):
        order=self.register()
        with patch('icloud_access.read_bytes',side_effect=AssertionError('no cloud')):
            saved=self.store.save({**order,'revision':order['revision'],'note':'База','todo_items':[{'text':'Задача','done':False}]})
            self.store.sync()
            self.assertEqual(self.store.get(self.order)['note'],'База')
            self.assertFalse(saved['sync_pending'])
        self.assertFalse((self.root/self.order/'!.txt').exists())

    def test_print_draft_and_idempotent_issued_document(self):
        relative='# work/# print';self.folder(relative)
        task=manager.create_print_task(relative,'https://example.com','Размеры','Печать')
        self.assertFalse((self.root/task['path']).exists())
        with patch('icloud_access.read_bytes',side_effect=AssertionError('no cloud')):
            saved=manager.save_print_task(task['path'],'https://example.com','Новый текст',task['revision'],'Название')
            self.assertEqual(manager.read_print_task(task['path'])['description'],'Новый текст')
        first=self.meta.publish(saved['path'],saved['revision'],self.root/relative,'Выпущено.txt',b'issued')
        self.meta.sync()
        second=self.meta.publish(saved['path'],saved['revision'],self.root/relative,'Другой.txt',b'issued')
        self.assertEqual(first['path'],second['path']);self.assertFalse(second['pending'])
        self.assertEqual((self.root/first['path']).read_bytes(),b'issued')
        manager.read_folder(relative)
        with self.meta.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM metadata_records WHERE kind='print'").fetchone()[0],1)

    def test_print_publication_collision_is_retained_in_queue(self):
        target=self.root/self.event/'issued.txt';target.write_bytes(b'existing')
        self.meta.publish('draft','1',target.parent,target.name,b'new')
        self.meta.sync()
        self.assertEqual(target.read_bytes(),b'existing')
        self.assertEqual(self.meta.status()['pending_documents'],1)
        self.assertTrue(self.meta.status()['document_errors'])

    def test_folder_rename_and_standalone_undo_preserve_comments(self):
        self.register()
        path=self.root/self.event/'a.jpg';path.write_bytes(b'photo')
        self.meta.save_comment(path,'Комментарий','missing')
        note=manager.folder_note_store().read(self.event)
        manager.folder_note_store().save({'path':self.event,'revision':note['revision'],'note':'Заметка'})
        result=folder_rename.rename(self.store,{**folder_rename.preview(self.store,self.order),'name':'2026-10-20 - Новое','confirmed':True})
        new=result['path']+'/00 - Замеры/a.jpg'
        self.assertEqual(self.meta.comment(self.root/new)['comment'],'Комментарий')
        subprocess.run([sys.executable,str(self.root/result['journal']/'.restore.py'),str(self.root/result['journal']),'--apply'],check=True,capture_output=True)
        self.assertEqual(self.meta.comment(path)['comment'],'Комментарий')
        self.assertEqual(manager.folder_note_store().read(self.event)['note'],'Заметка')

    def test_file_trash_and_standalone_restore_keep_database_comment(self):
        path=self.root/self.event/'a.jpg';path.write_bytes(b'photo')
        self.meta.save_comment(path,'Комментарий','missing')
        preview=file_trash.preview(self.root,self.event,[self.event+'/a.jpg'])
        removed=file_trash.remove(self.root,self.event,preview['files'],True,database=self.store.database)
        self.assertFalse(removed['error'])
        with self.meta.connect() as db:
            self.assertIsNone(db.execute("SELECT 1 FROM metadata_records WHERE path=?",(self.event+'/a.jpg',)).fetchone())
        session=file_trash.session_path(self.root,removed['session'])
        restored=json.loads(subprocess.run([sys.executable,str(session/'.restore.py')],check=True,capture_output=True).stdout)
        self.assertFalse(restored['error'])
        self.assertEqual(self.meta.comment(path)['comment'],'Комментарий')

    def event_rename_fixture(self):
        self.register()
        old=self.order+'/Фото без номера'
        self.folder(old)
        path=self.root/old/'a.jpg';path.write_bytes(b'photo')
        self.meta.save_comment(path,'Комментарий','missing')
        record=manager.folder_note_store().read(old)
        manager.folder_note_store().save({'path':old,'revision':record['revision'],'note':'Новая заметка'})
        view=event_folders.preview(self.root,self.order,manager.folder_note_store())
        payload={'path':self.order,'revision':view['revision'],'confirmed':True,
            'names':[{'source':item['source'],'title':item['title'] or 'Фото'} for item in view['suggestions']]}
        return old,path,payload

    def test_event_rename_and_standalone_undo_preserve_database_metadata(self):
        old,path,payload=self.event_rename_fixture()
        self.meta.put('print',old+'/draft.txt',{'title':'Черновик'},'missing')
        self.meta.publish(old+'/draft.txt','v1',self.root/old,'issued.txt',b'issued')
        result=event_folders.rename(manager.folder_note_store(),payload)
        new=next(pair['destination'] for pair in result['renamed'] if pair['source']==old)
        self.assertEqual(self.meta.comment(self.root/new/'a.jpg')['comment'],'Комментарий')
        self.meta.sync();self.assertEqual((self.root/new/'issued.txt').read_bytes(),b'issued')
        subprocess.run([sys.executable,str(self.root/result['journal']/'.restore.py'),str(self.root/result['journal']),'--apply'],check=True,capture_output=True)
        self.assertEqual(self.meta.comment(path)['comment'],'Комментарий')
        self.assertEqual(self.meta.get('print',old+'/draft.txt')['title'],'Черновик')

    def test_event_rename_database_failure_rolls_files_back(self):
        old,path,payload=self.event_rename_fixture()
        helper=event_folder_undo.metadata_paths
        def fail(db,source,destination,**kwargs):
            if kwargs.get('apply'): raise ValueError('Simulated database failure')
            return helper(db,source,destination,**kwargs)
        with patch('event_folder_undo.metadata_paths',side_effect=fail):
            with self.assertRaises(event_folders.EventFolderConflict):
                event_folders.rename(manager.folder_note_store(),payload)
        self.assertTrue(path.exists())
        self.assertEqual(self.meta.comment(path)['comment'],'Комментарий')

    def test_previous_restoration_helper_is_archived_before_upgrade(self):
        old,path,payload=self.event_rename_fixture()
        result=event_folders.rename(manager.folder_note_store(),payload)
        helper=self.root/result['journal']/'.restore.py'
        previous=helper.read_bytes()+b'\n# previous release\n'
        helper.write_bytes(previous)
        self.meta.upgrade_restoration()
        self.assertEqual(helper.read_bytes(),Path(event_folder_undo.__file__).read_bytes())
        with self.meta.connect() as db:
            self.assertEqual(db.execute('SELECT body FROM legacy_documents WHERE path=?',(self.meta.key(helper),)).fetchone()[0],previous)

    def test_trash_restore_rejects_new_comment_at_old_path(self):
        path=self.root/self.event/'a.jpg';path.write_bytes(b'photo')
        self.meta.save_comment(path,'Прежний','missing')
        preview=file_trash.preview(self.root,self.event,[self.event+'/a.jpg'])
        removed=file_trash.remove(self.root,self.event,preview['files'],True,database=self.store.database)
        self.meta.put('comment',self.event+'/a.jpg',{'comment':'Новый'},'missing')
        restored=file_trash.restore(self.root,removed['session'])
        self.assertTrue(restored['error']);self.assertFalse(path.exists())
        with self.meta.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM metadata_records WHERE kind='comment'").fetchone()[0],2)

    def test_interrupted_trash_is_visible_and_restores_staged_comment(self):
        path=self.root/self.event/'a.jpg';path.write_bytes(b'photo')
        self.meta.save_comment(path,'Сохранить','missing')
        preview=file_trash.preview(self.root,self.event,[self.event+'/a.jpg'])
        with patch('file_trash.rename',side_effect=OSError('interrupted')):
            removed=file_trash.remove(self.root,self.event,preview['files'],True,database=self.store.database)
        self.assertTrue(removed['error'])
        self.assertEqual(file_trash.list_sessions(self.root)[0]['count'],1)
        with self.assertRaises(ValueError): self.meta.comment(path)
        self.assertFalse(file_trash.restore(self.root,removed['session'])['error'])
        self.assertEqual(self.meta.comment(path)['comment'],'Сохранить')

    def test_reregister_preserves_newer_database_card(self):
        order=self.register()
        saved=self.store.save({**order,'note':'Актуальная заметка','revision':order['revision']})
        self.store.remove({'path':self.order,'revision':saved['revision'],'confirmed':True})
        notes=manager.folder_note_store().read(self.order)
        manager.folder_note_store().save({'path':self.order,'revision':notes['revision'],'note':'Отдельная заметка'})
        self.store.import_folder(self.order)
        self.assertEqual(self.store.get(self.order)['note'],'Отдельная заметка')

    def test_backup_is_consistent_and_contains_comments(self):
        self.meta.put('comment',self.event+'/a.jpg',{'comment':'Резерв'},'missing')
        backup=self.meta.backup('test')
        with sqlite3.connect(backup) as db:
            self.assertEqual(db.execute('PRAGMA quick_check').fetchone()[0],'ok')
            self.assertIn('Резерв',db.execute('SELECT data FROM metadata_records').fetchone()[0])

    def test_migration_preserves_legacy_history_and_skips_attachments(self):
        path=self.root/self.event/'a.jpg';path.write_bytes(b'photo')
        old=file_comments.save(path,'v1','missing')
        file_comments.save(path,'v2',old['revision'])
        reader=manager.order_document.icloud_access.read_bytes
        def checked(file,*args,**kwargs):
            self.assertNotEqual(Path(file),path)
            return reader(file,*args,**kwargs)
        with patch('icloud_access.read_bytes',side_effect=checked): self.meta.migrate(manager)
        self.assertEqual(self.meta.comment(path)['comment'],'v2')
        with self.meta.connect() as db:
            self.assertGreaterEqual(db.execute('SELECT count(*) FROM legacy_documents').fetchone()[0],2)
        self.assertFalse(self.meta.status()['errors'])

    def test_mobile_is_paused_and_cannot_be_enabled(self):
        bridge=MobileBridge(self.store)
        with self.store.connect() as db: bridge.put_meta(db,'enabled','1')
        bridge.run()
        self.assertTrue(bridge.status()['paused']);self.assertFalse(bridge.status()['enabled'])
        with self.assertRaises(ValueError): bridge.configure(True)
        self.assertFalse((self.root/'.mobile-sync').exists())
        with self.store.connect() as db: self.assertEqual(bridge.get_meta(db,'enabled'),'1')

    def test_api_keeps_file_binding_and_legacy_writes_are_disabled(self):
        path=self.event+'/a.jpg';self.file(path,b'photo')
        key=file_comments.binding(self.root/path)
        status,_,body=self.http('/api/file-comment','POST',json.dumps({'path':path,'comment':'x','revision':'missing','comment_key':'wrong'}))
        self.assertEqual(status,409)
        status,_,body=self.http('/api/file-comment','POST',json.dumps({'path':path,'comment':'x','revision':'missing','comment_key':key}))
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['comment'],'x')
        status,_,_=self.http('/api/note','POST',json.dumps({'path':self.event,'note':'old API'}))
        self.assertEqual(status,400)
