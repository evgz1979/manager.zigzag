import concurrent.futures
import io
import http.client
import json
import os
import socket
from pathlib import Path
import urllib.parse
import unittest
import uuid
from unittest.mock import patch

import file_uploads
import test_database_storage as fixtures

manager = fixtures.manager


class FileUploadTests(unittest.TestCase):
    setUp = fixtures.DatabaseStorageTests.setUp
    tearDown = fixtures.DatabaseStorageTests.tearDown
    folder = fixtures.DatabaseStorageTests.folder
    file = fixtures.DatabaseStorageTests.file
    http = fixtures.DatabaseStorageTests.http
    url = fixtures.DatabaseStorageTests.url

    def upload(self, name='original.bin', body=b'original\x00\xffbytes', path=None, source=None, token=None):
        path = path or self.event
        return file_uploads.receive(self.store, path, token or file_uploads.options(self.root,path)['token'],
                                    name, source or io.BytesIO(body), len(body))

    def assert_clean(self, *paths):
        for path in paths or (self.root/self.event,):
            self.assertEqual(list(Path(path).glob('.upload-*.part')), [])

    def test_streams_exact_bytes_in_chunks_without_changing_metadata(self):
        record=self.store.add(self.order,{'status':'rework','note':'Keep order'})
        note=manager.folder_note_store().read(self.event)
        manager.folder_note_store().save({'path':self.event,'revision':note['revision'],'note':'Keep event'})
        body=os.urandom(file_uploads.CHUNK*2+113)
        class Reader(io.BytesIO):
            def read(reader,size):
                self.assertLessEqual(size,file_uploads.CHUNK)
                self.assertFalse((self.root/self.event/'original.bin').exists())
                return super(Reader,reader).read(size)
        saved=self.upload(body=body,source=Reader(body))
        self.assertEqual((self.root/saved['path']).read_bytes(),body)
        self.assertEqual(saved['size'],len(body))
        self.assertEqual(self.store.get(self.order),record)
        self.assertEqual(manager.folder_note_store().get(self.event)['note'],'Keep event')
        self.assert_clean()
        self.assertFalse((self.root/self.event/'!.txt').exists())

    def test_existing_files_directories_and_links_are_not_overwritten(self):
        self.file(self.event+'/photo.jpg',b'old')
        self.folder(self.event+'/photo (2).jpg')
        (self.root/self.event/'photo (3).jpg').symlink_to(self.root/self.event/'photo.jpg')
        saved=self.upload('photo.jpg',b'new')
        self.assertEqual(saved['name'],'photo (4).jpg')
        self.assertEqual((self.root/self.event/'photo.jpg').read_bytes(),b'old')
        self.assertTrue((self.root/self.event/'photo (2).jpg').is_dir())
        self.assertTrue((self.root/self.event/'photo (3).jpg').is_symlink())
        self.assertEqual((self.root/saved['path']).read_bytes(),b'new')
        self.assert_clean()

    def test_concurrent_same_names_preserve_both_files(self):
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(self.upload,'same.pdf',body) for body in (b'first',b'second')]
            saved=[future.result() for future in futures]
        self.assertEqual({item['name'] for item in saved},{'same.pdf','same (2).pdf'})
        self.assertEqual({(self.root/item['path']).read_bytes() for item in saved},{b'first',b'second'})
        self.assert_clean()

    def test_missing_files_with_comments_and_queued_documents_keep_their_names(self):
        self.file(self.event+'/photo.jpg',b'old')
        self.meta.save_comment(self.root/self.event/'photo.jpg','Old comment','missing')
        (self.root/self.event/'photo.jpg').unlink()
        self.meta.publish(self.event+'/draft.txt','version',self.root/self.event,'issued.txt',b'issued document')
        photo=self.upload('photo.jpg',b'new photo')
        issued=self.upload('issued.txt',b'new document')
        self.assertEqual(photo['name'],'photo (2).jpg')
        self.assertEqual(issued['name'],'issued (2).txt')
        self.assertEqual(self.meta.comment(self.root/photo['path'])['comment'],'')
        self.meta.sync()
        self.assertEqual((self.root/self.event/'issued.txt').read_bytes(),b'issued document')
        self.assertEqual((self.root/issued['path']).read_bytes(),b'new document')

    def test_missing_issued_invoice_copy_is_not_occupied_by_upload(self):
        self.store.add(self.order,{'status':'new'})
        invoice=manager.invoice_store().create({'path':self.order,'id':str(uuid.uuid4())})
        with self.store.connect() as db:
            db.execute("UPDATE invoices SET state='issued',filename='invoice.pdf',pdf=?,exported=0 WHERE id=?",(b'original PDF',invoice['id']))
        bills=self.order+'/# bills';self.folder(bills)
        saved=self.upload('invoice.pdf',b'incoming PDF',path=bills)
        self.assertEqual(saved['name'],'invoice (2).pdf')
        self.assertFalse((self.root/bills/'invoice.pdf').exists())

    def test_normalizes_names_and_allows_empty_files(self):
        saved=self.upload('Прое\u0308м.txt',b'')
        self.assertEqual(saved['name'],'Проём.txt')
        self.assertEqual((self.root/saved['path']).read_bytes(),b'')

    def test_only_event_and_material_folders_are_available(self):
        for relative in ('', 'Клиент', 'Клиент/Объект', self.order, '# docs/Внутри'):
            self.assertFalse(file_uploads.available(self.root,relative))
            with self.assertRaises((ValueError,FileNotFoundError)):
                file_uploads.target(self.root,relative)
        for relative in (self.event,self.event+'/More',self.order+'/# cdr','# work/# glass/2026-10-21 - Glass/00 - Delivery'):
            self.folder(relative)
            self.assertTrue(file_uploads.available(self.root,relative))
            saved=self.upload(path=relative)
            self.assertTrue((self.root/saved['path']).is_file())

    def test_uploads_to_events_of_all_dynamic_work_sections_and_nested_hash_folders(self):
        paths = (
            '#work/#newtek/2026-10-21 - Сборный/00 - Задание',
            '# work/# future-provider/Без даты/01 - Event/Deep/# files',
            '#work/New supplier/2026-10-21 - Order/00 - Event',
            '# work/# razbor/# newtek/00 - Event',
            '#work/#print/2026-10-21 - Print/00 - Event',
        )
        for relative in paths:
            with self.subTest(path=relative):
                self.folder(relative)
                status,_,body=self.http(self.url('/api/folder',relative))
                self.assertEqual(status,200,body)
                folder=json.loads(body)
                self.assertEqual(folder['filesScope'],'folder')
                self.assertIsNotNone(folder['upload'])
                route=self.url('/api/file-upload',relative,name='input.bin',token=folder['upload']['token'])
                status,_,body=self.http(route,'POST',b'exact incoming bytes',{'Content-Type':'application/octet-stream','X-Manager-Upload':'1'})
                self.assertEqual(status,201,body)
                self.assertEqual((self.root/json.loads(body)['path']).read_bytes(),b'exact incoming bytes')
        for relative in ('#work','#work/#newtek','#work/#newtek/2026-10-21 - Сборный','# work/# razbor/# newtek'):
            self.assertFalse(file_uploads.available(self.root,relative),relative)
            self.assertIsNone(manager.read_folder(relative)['upload'])
        self.assertEqual(self.store.list(),[])

    def test_rejects_unsafe_names_paths_and_service_cards(self):
        for name in ('', '../outside.txt', '/tmp/outside.txt','a/b','a\\b','a:b','bad\n.txt','.hidden','!.txt','!STATUS.TXT','status.txt','x'*256):
            with self.subTest(name=name),self.assertRaises(ValueError):self.upload(name)
        (self.root/'Link').symlink_to(self.root/self.event,target_is_directory=True)
        self.assertFalse(file_uploads.available(self.root,'Link'))
        for relative in ('../outside','/tmp','Link',self.order+'/.hidden'):
            with self.assertRaises(ValueError):file_uploads.target(self.root,relative)
        self.assert_clean()

    def test_stale_folder_token_rejects_recreated_folder(self):
        token=file_uploads.options(self.root,self.event)['token']
        (self.root/self.event).rename(self.root/self.order/'Old event')
        self.folder(self.event)
        with self.assertRaises(file_uploads.UploadConflict):self.upload(token=token)
        self.assertEqual(list((self.root/self.event).iterdir()),[])
        self.assert_clean(self.root/self.order/'Old event')

    def test_folder_moved_during_stream_is_rejected_and_temporary_is_cleaned(self):
        destination=self.root/self.order/'Renamed event'
        class Reader(io.BytesIO):
            def read(reader,size):
                (self.root/self.event).rename(destination)
                return super(Reader,reader).read(size)
        with self.assertRaises(FileNotFoundError):self.upload(source=Reader(b'original\x00\xffbytes'))
        self.assertEqual(list(destination.iterdir()),[])

    def test_partial_stream_read_errors_and_publication_failure_leave_no_file(self):
        with self.assertRaises(ValueError):self.upload(source=io.BytesIO(b'short'))
        with patch('file_uploads.folder_layout.rename_exclusive',side_effect=OSError('disk failed')):
            with self.assertRaises(OSError):self.upload()
        class Broken:
            def read(self,size):raise OSError('connection lost')
        with self.assertRaises(OSError):self.upload(source=Broken())
        self.assertEqual(list((self.root/self.event).iterdir()),[])

    def test_limits_and_pending_rename_do_not_read_stream(self):
        class Unreadable:
            def read(self,size):raise AssertionError('body was read')
        with self.assertRaises(file_uploads.UploadTooLarge):
            file_uploads.receive(self.store,self.event,'bad','a.bin',Unreadable(),file_uploads.MAX_BYTES+1)
        from event_folder_undo import EventRenamePending
        with patch('file_uploads.guard_database',side_effect=EventRenamePending('pending')):
            with self.assertRaises(EventRenamePending):self.upload(source=Unreadable())
        self.assert_clean()

    def test_http_raw_upload_and_folder_capability(self):
        status,_,raw=self.http(self.url('/api/folder',self.event))
        capability=json.loads(raw)['upload'];self.assertEqual(status,200)
        url=self.url('/api/file-upload',self.event,name='Фото.pdf',token=capability['token'])
        body=b'%PDF-1.4\x00exact bytes'
        headers={'Content-Type':'application/octet-stream','X-Manager-Upload':'1','Origin':'http://127.0.0.1:'+str(self.server.server_port)}
        status,_,raw=self.http(url,'POST',body,headers)
        self.assertEqual(status,201,raw)
        self.assertEqual((self.root/json.loads(raw)['path']).read_bytes(),body)
        status,_,raw=self.http(self.url('/api/folder',self.event))
        self.assertIn('Фото.pdf',[item['name'] for item in json.loads(raw)['files']])
        self.assert_clean()

    def test_http_rejects_cross_origin_bad_headers_and_oversized_body(self):
        token=file_uploads.options(self.root,self.event)['token']
        url=self.url('/api/file-upload',self.event,name='x.bin',token=token)
        headers={'Content-Type':'application/octet-stream','X-Manager-Upload':'1'}
        for changed,expected in (({'X-Manager-Upload':'no'},403),({'Origin':'https://other.example'},403),
                ({'Content-Type':'text/plain'},403),({'Content-Length':str(file_uploads.MAX_BYTES+1)},413),
                ({'Content-Length':'-1'},400),({'Transfer-Encoding':'chunked'},400)):
            with self.subTest(headers=changed):
                status,_,raw=self.http(url,'POST',b'',{**headers,**changed})
                self.assertEqual(status,expected,raw)
        self.assertEqual(list((self.root/self.event).iterdir()),[])

    def test_interrupted_network_transfer_never_publishes_partial_file(self):
        self.http('/api/health')
        token=file_uploads.options(self.root,self.event)['token']
        route=self.url('/api/file-upload',self.event,name='partial.mov',token=token)
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            connection.request('POST',route,b'short',{'Content-Length':'100000','Content-Type':'application/octet-stream','X-Manager-Upload':'1'})
            connection.sock.shutdown(socket.SHUT_WR)
            response=connection.getresponse()
            self.assertEqual(response.status,400,response.read())
        finally:connection.close()
        self.assertEqual(list((self.root/self.event).iterdir()),[])
