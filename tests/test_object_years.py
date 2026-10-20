import ctypes
import json
import sqlite3
import subprocess
import sys
import unittest
import uuid
from unittest.mock import Mock, patch

import test_database_storage as storage_fixtures
import folder_layout as layout
import folder_rename_undo as restore
import object_years
import order_folders
from event_folder_undo import EventRenamePending

manager=storage_fixtures.manager


class ObjectYearsTests(unittest.TestCase):
    setUp=storage_fixtures.DatabaseStorageTests.setUp
    tearDown=storage_fixtures.DatabaseStorageTests.tearDown
    folder=storage_fixtures.DatabaseStorageTests.folder
    file=storage_fixtures.DatabaseStorageTests.file
    http=storage_fixtures.DatabaseStorageTests.http
    url=storage_fixtures.DatabaseStorageTests.url
    parent='Клиент/Объект'

    def populate(self):
        order=self.store.add(self.order,{'status':'rework','note':'Карточка','financial_status':'partial','amount':12500,
            'extra_blocks':{'Задачи':'- [ ] Сделать','Избранное':'Да','Особое':'Не менять'}})
        notes=manager.folder_note_store();record=notes.read(self.event)
        notes.save({'path':self.event,'revision':record['revision'],'note':'Заметка события','todo_items':[{'text':'Задача события','done':False}]})
        self.file(self.event+'/a.jpg',b'original bytes')
        self.meta.save_comment(self.root/self.event/'a.jpg','Комментарий','missing')
        self.meta.put('print',self.event+'/draft.txt',{'title':'Задание'},'missing')
        self.meta.publish(self.event+'/draft.txt','version1',self.root/self.event,'issued.txt',b'issued')
        invoice=manager.invoice_store().create({'path':self.order,'id':str(uuid.uuid4())})
        with self.store.connect() as db:
            db.execute("UPDATE invoices SET state='issued',pdf=?,filename='issued.pdf',exported=0 WHERE id=?",(b'PDF unchanged',invoice['id']))
        return order,invoice

    def apply(self):
        view=object_years.preview(self.store,self.parent)
        return object_years.group(self.store,{'path':self.parent,'revision':view['revision'],'confirmed':True})

    def test_object_creation_in_normal_and_grouped_clients_with_portable_undo(self):
        for client in ('Клиент','03 - Группа/Азер'):
            self.folder(client)
            created=order_folders.create_object(self.root,client,'Инициативная')
            self.assertEqual(manager.folder_role(self.root,created['path'])['folderKind'],'object')
            self.assertEqual(list((self.root/created['path']).iterdir()),[])
            session=self.root/created['journal']
            subprocess.run([sys.executable,str(session/'.folder-layout.py'),'undo',str(session),'--apply'],check=True,capture_output=True)
            self.assertFalse((self.root/created['path']).exists())
        self.assertEqual(self.store.list(),[])

    def test_object_creation_rejects_other_roles_names_conflicts_and_links(self):
        for relative in ('',self.parent,self.order,self.event,'# docs'):
            with self.assertRaises(ValueError):order_folders.create_object(self.root,relative,'Адрес')
        for name in ('','2026','2026-10-20 - Работа','01 - Объект','# bills','.hidden','a/b','a\\b','a\n'):
            with self.assertRaises(ValueError):order_folders.create_object(self.root,'Клиент',name)
        self.file('Клиент/Занято',b'preserve')
        with self.assertRaises(order_folders.OrderFolderConflict):order_folders.create_object(self.root,'Клиент','Занято')
        (self.root/'Ссылка').symlink_to(self.root/'Клиент')
        with self.assertRaises(ValueError):order_folders.create_object(self.root,'Ссылка','Адрес')

    def test_http_roles_and_creating_object(self):
        self.assertTrue(manager.read_folder('Клиент')['canCreateObjectFolder'])
        self.assertFalse(manager.read_folder(self.parent)['canCreateObjectFolder'])
        self.assertTrue(manager.read_folder(self.parent)['canGroupOrdersByYear'])
        self.assertFalse(manager.read_folder(self.order)['canGroupOrdersByYear'])
        status,_,body=self.http('/api/object-folder-create','POST',json.dumps({'path':'Клиент','title':'Другой адрес'}))
        self.assertEqual(status,201)
        self.assertTrue((self.root/json.loads(body)['path']).is_dir())

    def test_group_preserves_every_metadata_identity_and_invoice_queue(self):
        order,invoice=self.populate()
        result=self.apply();new=self.parent+'/2026/'+self.order.split('/')[-1]
        moved=self.store.get(new)
        for field in ('id','status','title','note','financial_status','amount','extra_blocks'):
            self.assertEqual(moved[field],order[field])
        self.assertEqual(len(self.store.list()),1)
        event=new+'/00 - Замеры'
        self.assertEqual(manager.folder_note_store().get(event)['parent_order'],new)
        self.assertEqual(manager.folder_note_store().get(event)['note'],'Заметка события')
        self.assertEqual(self.meta.comment(self.root/event/'a.jpg')['comment'],'Комментарий')
        self.assertEqual(self.meta.get('print',event+'/draft.txt')['title'],'Задание')
        self.meta.sync();self.assertEqual((self.root/event/'issued.txt').read_bytes(),b'issued')
        with self.store.connect() as db:
            row=db.execute('SELECT path,pdf,exported FROM invoices WHERE id=?',(invoice['id'],)).fetchone()
            self.assertEqual(tuple(row),(new,b'PDF unchanged',0))
        self.assertFalse((self.root/self.order).exists())
        self.assertEqual((self.root/event/'a.jpg').read_bytes(),b'original bytes')
        self.assertEqual(result['moved'],1)

    def test_multiple_years_partial_dates_short_years_and_undated_orders(self):
        for name in ('2025-00-00 - Заказ','26 00 00 - Ещё','00001 - Без даты','1800-01-01 - Старое','# media'):
            self.folder(self.parent+'/'+name)
        view=object_years.preview(self.store,self.parent)
        self.assertEqual({p['year'] for p in view['mappings']},{'2025','2026'})
        self.assertIn('00001 - Без даты',view['skipped'])
        self.assertIn('1800-01-01 - Старое',view['skipped'])
        result=self.apply()
        self.assertEqual(result['moved'],3)
        self.assertTrue((self.root/self.parent/'00001 - Без даты').is_dir())
        self.assertTrue((self.root/self.parent/'# media').is_dir())
        self.assertEqual(object_years.preview(self.store,self.parent)['mappings'],[])

    def test_stale_preview_missing_confirmation_and_existing_destination_never_overwrite(self):
        view=object_years.preview(self.store,self.parent)
        with self.assertRaises(ValueError):object_years.group(self.store,{'path':self.parent,'revision':view['revision']})
        self.folder(self.parent+'/2025-10-20 - Новое')
        with self.assertRaises(object_years.YearGroupConflict):object_years.group(self.store,{'path':self.parent,'revision':view['revision'],'confirmed':True})
        self.folder(self.parent+'/2026/'+self.order.split('/')[-1])
        view=object_years.preview(self.store,self.parent)
        self.assertTrue(view['conflicts'])
        with self.assertRaises(object_years.YearGroupConflict):self.apply()
        self.assertTrue((self.root/self.order).is_dir())

    def test_existing_annual_work_or_saved_destination_metadata_blocks_grouping(self):
        self.folder(self.parent+'/2026/# cdr')
        self.assertTrue(object_years.preview(self.store,self.parent)['conflicts'])
        (self.root/self.parent/'2026/# cdr').rmdir();(self.root/self.parent/'2026').rmdir()
        self.meta.put('comment',self.parent+'/2026/orphan.jpg',{'comment':'Сохранить'},'missing')
        self.assertTrue(object_years.preview(self.store,self.parent)['conflicts'])

    def test_new_orders_route_to_existing_year_groups_and_create_new_year(self):
        self.folder(self.parent+'/2025')
        result=order_folders.create(self.root,self.parent,'2026-10-20','Новый')
        self.assertEqual(result['path'],self.parent+'/2026/2026-10-20 - Новый')
        self.assertTrue(manager.read_folder(self.parent+'/2026')['canCreateOrderFolder'])
        direct=order_folders.create(self.root,self.parent+'/2025','2025-01-20','В году')
        self.assertIn('/2025/2025-01-20',direct['path'])
        with self.assertRaises(ValueError):order_folders.create(self.root,self.parent+'/2025','2026-01-20','Не тот год')
        self.assertEqual(self.store.list(),[])

    def test_empty_object_can_start_year_groups_without_registering_any_order(self):
        other='Клиент/Пустой объект';self.folder(other)
        view=object_years.preview(self.store,other)
        self.assertEqual(len(view['created_years']),1)
        result=object_years.group(self.store,{'path':other,'revision':view['revision'],'confirmed':True})
        self.assertEqual(result['moved'],0)
        self.assertTrue((self.root/view['created_years'][0]).is_dir())
        subprocess.run([sys.executable,str(self.root/result['journal']/'.restore.py'),str(self.root/result['journal']),'--apply'],check=True,capture_output=True)
        self.assertFalse((self.root/view['created_years'][0]).exists())

    def test_standalone_undo_preserves_later_edits_and_new_orders_in_year(self):
        order,invoice=self.populate();result=self.apply()
        new=self.parent+'/2026/'+self.order.split('/')[-1]
        record=self.store.get(new)
        self.store.save({**record,'note':'Поздняя правка','amount':'125','costs':None,'paid':None})
        self.file(new+'/new.txt',b'new data')
        created=order_folders.create(self.root,self.parent,'2026-11-01','Другой заказ')
        year_note=manager.folder_note_store().read(self.parent+'/2026')
        manager.folder_note_store().save({'path':year_note['path'],'revision':year_note['revision'],'note':'Заметка года'})
        session=self.root/result['journal']
        subprocess.run([sys.executable,str(session/'.restore.py'),str(session),'--apply'],check=True,capture_output=True)
        self.assertEqual(self.store.get(self.order)['note'],'Поздняя правка')
        self.assertEqual((self.root/self.order/'new.txt').read_bytes(),b'new data')
        self.assertTrue((self.root/created['path']).is_dir())
        self.assertEqual(self.meta.comment(self.root/self.event/'a.jpg')['comment'],'Комментарий')
        self.assertEqual(manager.folder_note_store().get(year_note['path'])['note'],'Заметка года')

    def test_failure_after_files_move_restores_original_database_and_folders(self):
        order,invoice=self.populate()
        real=layout.apply
        def fail(session):
            real(session)
            raise OSError('Failure before SQLite path commit')
        with patch('folder_layout.apply',side_effect=fail):
            with self.assertRaises(object_years.YearGroupConflict):self.apply()
        self.assertEqual(self.store.get(self.order)['id'],order['id'])
        self.assertTrue((self.root/self.order).is_dir())
        self.assertEqual(self.meta.comment(self.root/self.event/'a.jpg')['comment'],'Комментарий')
        self.assertFalse((self.root/self.parent/'2026').exists())

    def test_interrupted_undo_is_blocked_until_retry_and_preserves_all_data(self):
        self.populate();self.folder(self.parent+'/2025-00-00 - Второй')
        result=self.apply();session=self.root/result['journal']
        real=ctypes.CDLL(None,use_errno=True).renamex_np;count=0
        def fail(source,destination,flags):
            nonlocal count
            count+=1
            if count==2:raise OSError('Interrupted undo')
            return real(source,destination,flags)
        with patch('ctypes.CDLL',return_value=Mock(renamex_np=Mock(side_effect=fail))):
            with self.assertRaises(OSError):restore.undo(session,True)
        with self.assertRaises(EventRenamePending):manager.folder_note_store().get(self.event)
        subprocess.run([sys.executable,str(session/'.restore.py'),str(session),'--apply'],check=True,capture_output=True)
        self.assertTrue((self.root/self.order).is_dir())
        self.assertEqual(self.meta.comment(self.root/self.event/'a.jpg')['comment'],'Комментарий')

    def test_http_preview_and_confirmed_grouping(self):
        status,_,body=self.http(self.url('/api/object-years',self.parent))
        self.assertEqual(status,200)
        view=json.loads(body)
        with patch.object(manager,'schedule_order_sync'),patch.object(manager,'schedule_todo_refresh'):
            status,_,body=self.http('/api/object-years','POST',json.dumps({'path':self.parent,'revision':view['revision'],'confirmed':True}))
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['moved'],1)
        for relative in ('Клиент',self.event,'# docs'):
            with self.assertRaises((ValueError,FileNotFoundError)):object_years.preview(self.store,relative)
