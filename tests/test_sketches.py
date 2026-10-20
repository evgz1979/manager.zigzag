import base64
import hashlib
import json
from pathlib import Path
import shutil
import struct
import unittest
from unittest.mock import patch
import zipfile

import sketches
import folder_rename
from folder_notes import FolderNoteConflict
import test_server as fixtures

manager = fixtures.manager
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jL1sAAAAASUVORK5CYII=')


class SketchTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = "Клиент/2026-00-00 - Заказ"

    def cdr(self, name='01.cdr', folder=None, preview=PNG):
        folder = folder or self.order + '/# cdr'
        self.folder(folder)
        path = self.root / folder / name
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('previews/thumbnail.png', preview)
            archive.writestr('content/riffData.cdr', b'Untouched Corel document data')
        return path

    def files(self):
        return manager.read_folder(self.order)['sketches']

    def save(self, item, state):
        return manager.folder_note_store().save_sketch_relevance({
            'path': item['path'], 'key': item['key'], 'revision': item['relevance']['revision'], 'value': state})

    def test_only_direct_cdr_sketches_are_listed_backups_and_links_are_excluded_without_extracting(self):
        for name in ('01.cdr', 'Резервная_копия_01.cdr', 'Backup_of_01.cdr', 'AutoBackup_of_01.cdr', '~01.cdr', '.01.cdr', '01.bak', '01_backup.cdr'):
            self.cdr(name)
        self.cdr('02.CDR', self.order + '/#cdr')
        self.cdr('Глубокий.cdr', self.order + '/# cdr/Глубже')
        self.cdr('Событие.cdr', self.order + '/Фото/#cdr')
        self.file(self.order + '/# cdr/экспорт.pdf', b'pdf')
        self.file(self.order + '/Прямой.cdr', b'not a sketch')
        (self.root / self.order / '# cdr/Ссылка.cdr').symlink_to(self.root / self.order / '# cdr/01.cdr')
        with patch.object(manager.os, 'walk', side_effect=AssertionError('No recursive attachment walk')), patch.object(sketches.zipfile, 'ZipFile', side_effect=AssertionError('Previews load separately')):
            listing = manager.read_folder(self.order)
        self.assertEqual([item['name'] for item in listing['sketches']], ['01.cdr', '02.CDR'])
        self.assertTrue(all(item['relevance']['value'] == 'none' for item in listing['sketches']))
        self.assertEqual(listing['files'], [])
        self.assertEqual(manager.read_folder(self.order + '/Фото')['sketches'], [])

    def test_embedded_thumbnail_and_cache_do_not_change_cdr_and_fallback_page_is_supported(self):
        path = self.cdr()
        original, modified = path.read_bytes(), path.stat().st_mtime_ns
        preview = sketches.preview(path, manager.DATA_DIR)
        self.assertEqual(preview.read_bytes(), PNG)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(path.stat().st_mtime_ns, modified)
        with patch.object(sketches, 'embedded_preview', side_effect=AssertionError('Cached PNG')):
            self.assertEqual(sketches.preview(path, manager.DATA_DIR), preview)
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('previews/page1.png', PNG)
        self.assertNotEqual(sketches.preview(path, manager.DATA_DIR), preview)

    def test_corrupt_unsupported_or_oversized_preview_is_not_served_as_an_image(self):
        path = self.cdr(preview=b'bad image')
        with self.assertRaises(ValueError): sketches.embedded_preview(path)
        path.write_bytes(b'RIFF legacy document without supported preview')
        with self.assertRaises(ValueError): sketches.embedded_preview(path)
        raw = bytearray(PNG)
        raw[16:24] = struct.pack('>II', 20000, 20000)
        self.cdr(preview=raw)
        with self.assertRaises(ValueError): sketches.embedded_preview(path)
        self.cdr(preview=PNG)
        with patch.object(sketches, 'MAX_PREVIEW', 30):
            with self.assertRaises(ValueError): sketches.embedded_preview(path)

    def test_states_are_independent_preserve_note_todos_other_blocks_and_parent(self):
        self.cdr('01.cdr'); self.cdr('02.cdr')
        card = self.root / self.order / '# cdr/!.txt'
        card.write_text(manager.order_document.render({'note':'Заметка эскизов','extra_blocks':{'Материал':'Плёнка','Задачи':'- [ ] Проверить размер'}},manager.STATUS_LABELS))
        store = manager.order_store()
        store.add(self.order, {'status':'process','financial_status':'paid','note':'Карточка заказа'})
        store.sync(); parent = store.get(self.order)
        first = self.files()[0]
        record = self.save(first, 'active')
        with self.assertRaises(FolderNoteConflict): self.save(self.files()[1] | {'relevance':first['relevance']}, 'check')
        second = self.files()[1]
        record = self.save(second, 'check')
        states = {item['name']:item['relevance']['value'] for item in self.files()}
        self.assertEqual(states, {'01.cdr':'active','02.cdr':'check'})
        self.assertEqual(record['note'], 'Заметка эскизов')
        self.assertEqual(record['todo_items'], [{'text':'Проверить размер','done':False}])
        self.assertEqual(record['extra_blocks']['Материал'], 'Плёнка')
        self.assertEqual(store.get(self.order), parent)
        manager.folder_note_store().sync()
        self.assertIn('"01.cdr": Актуально', card.read_text())
        shutil.rmtree(manager.DATA_DIR)
        self.assertEqual({item['name']:item['relevance']['value'] for item in self.files()}, states)

    def test_offline_saving_and_polling_use_database_queue_survives_failure_and_restart(self):
        self.cdr()
        first = self.files()[0]
        self.root.rename(self.base / 'offline')
        with patch.object(manager.order_document, 'load', side_effect=AssertionError('No cloud reads')):
            saved = self.save(first, 'check')
            status, _, body = self.http(self.url('/api/sketch-relevance', self.order))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[first['folder']]['states']['01.cdr'], 'check')
        manager.folder_note_store().sync()
        self.assertTrue(manager.folder_note_store().get(first['folder'])['sync_error'])
        (self.base / 'offline').rename(self.root)
        manager.folder_note_store().sync()
        self.assertFalse(manager.folder_note_store().get(first['folder'])['sync_pending'])
        self.assertEqual(self.files()[0]['relevance']['value'], 'check')

    def test_unknown_status_text_and_external_conflicts_preserve_both_versions(self):
        self.cdr()
        card = self.root / self.order / '# cdr/!.txt'
        raw = manager.order_document.render({'note':'Текст','extra_blocks':{sketches.BLOCK:'Неизвестный прежний текст'}},manager.STATUS_LABELS)
        card.write_text(raw)
        item = self.files()[0]
        self.assertIsNone(item['relevance']['value'])
        self.assertTrue(item['relevance']['error'])
        with self.assertRaisesRegex(ValueError, 'неизвестный текст'): self.save(item, 'active')
        self.assertEqual(card.read_text(), raw)
        card.write_text(manager.order_document.render({'note':'Текст','extra_blocks':{}},manager.STATUS_LABELS))
        self.save(self.files()[0], 'active')
        card.write_text(manager.order_document.render({'note':'Внешний текст','extra_blocks':{sketches.BLOCK:'"01.cdr": Неактуально'}},manager.STATUS_LABELS))
        manager.folder_note_store().sync()
        self.assertTrue(manager.folder_note_store().get(item['folder'])['sync_error'])
        self.assertIn('Внешний текст', card.read_text())
        self.assertEqual(self.files()[0]['relevance']['value'], 'active')

    def test_binding_rejects_foreign_files_and_rename_moves_statuses_with_the_folder(self):
        self.cdr('01.cdr'); self.cdr('02.cdr')
        first, second = self.files()
        with self.assertRaises(FolderNoteConflict): self.save({**first,'path':second['path']}, 'active')
        self.save(first, 'inactive')
        store = manager.order_store()
        result = folder_rename.rename(store,{**folder_rename.preview(store,self.order),'name':'2026-00-00 - Другое имя'})
        listing = manager.read_folder(result['path'])['sketches']
        self.assertEqual(listing[0]['relevance']['value'], 'inactive')
        self.assertNotEqual(first['key'], listing[0]['key'])
        with self.assertRaises(FolderNoteConflict): self.save(first, 'active')

    def test_http_embedded_preview_and_direct_corel_open_validate_scope_key_and_backups(self):
        path = self.cdr()
        item = self.files()[0]
        status, headers, raw = self.http(self.url('/api/sketch-preview', item['path']))
        self.assertEqual((status, headers['Content-Type'], raw), (200,'image/png',PNG))
        with patch.object(sketches, 'corel_app', return_value='/Applications/CorelDRAW.app'), patch.object(sketches.subprocess,'run') as launch:
            status, _, body = self.http('/api/sketch-open','POST',json.dumps({'path':item['path'],'key':item['key']}))
            self.assertEqual(status,200,body)
            self.assertEqual(launch.call_args.args[0], ['/usr/bin/open','-a','/Applications/CorelDRAW.app',str(path)])
            self.assertEqual(self.http('/api/sketch-open','POST',json.dumps({'path':item['path'],'key':'wrong'}))[0],409)
            self.assertEqual(launch.call_count,1)
        backup = self.cdr('Резервная_копия_01.cdr')
        self.assertEqual(self.http(self.url('/api/sketch-preview', backup.relative_to(self.root).as_posix()))[0],400)
        self.cdr('other.cdr', self.order+'/Фото/#cdr')
        self.assertEqual(self.http(self.url('/api/sketch-preview',self.order+'/Фото/#cdr/other.cdr'))[0],400)

    def test_http_status_versions_and_scope_do_not_touch_cdr(self):
        path = self.cdr(); item = self.files()[0]; original = path.read_bytes()
        payload = {'path':item['path'],'key':item['key'],'revision':item['relevance']['revision'],'value':'check'}
        with patch.object(manager,'schedule_order_sync'):
            status, _, body = self.http('/api/sketch-relevance','POST',json.dumps(payload))
        self.assertEqual(status,200,body)
        result = json.loads(body)
        self.assertEqual((result['path'],result['key']), (item['path'],item['key']))
        self.assertEqual(self.http('/api/sketch-relevance','POST',json.dumps(payload))[0],409)
        self.assertEqual(path.read_bytes(),original)
        self.cdr('deep.cdr',self.order+'/Фото/#cdr')
        notes = manager.folder_note_store(); record = notes.read(self.order+'/Фото/#cdr')
        deep = self.root / self.order / 'Фото/#cdr/deep.cdr'
        with self.assertRaisesRegex(ValueError,'непосредственно'):
            notes.save_sketch_relevance({'path':deep.relative_to(self.root).as_posix(),'key':manager.file_comments.binding(deep),'revision':record['revision'],'value':'active'})


if __name__ == '__main__':
    unittest.main()
