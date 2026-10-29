"""Переход сверок, единственное назначение и сохранность исходных данных."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import folder_layout
import folder_rename
import folder_rename_undo
import order_creation
import order_document
import reconciliations
import test_server as fixtures
from test_deploy import remote

manager = fixtures.manager


class ReconciliationTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    section = '# moneys/# reconciliations'
    source_order = 'Клиент/2026-00-00 - Заказ'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        manager.DATABASE_ONLY = True
        self.folder(self.section)
        self.store = manager.order_store()
        self.service = reconciliations.Reconciliations(self.store)

    def reconciliation(self, name='Сверка'):
        path = self.section + '/' + name
        self.folder(path)
        return self.service.open(path)

    def invoice(self):
        self.store.add(self.source_order, {'status': 'new', 'title': 'Исходный заказ', 'note': 'Сохранить'})
        return manager.invoice_store().create({'id': str(uuid.uuid4()), 'path': self.source_order})

    def assign(self, invoice, target, revision=0):
        return self.service.assign(manager.invoice_store(), {'path': invoice['path'], 'id': invoice['id'],
            'invoice_revision': invoice['revision'], 'revision': revision,
            'reconciliation_id': target['id'] if target else '', 'target_revision': target['revision'] if target else None})

    def post(self, route, payload, headers=None):
        return self.http(route, 'POST', json.dumps(payload), headers or {'Content-Type': 'application/json', 'X-Manager-Reconciliations': '1'})

    def test_existing_three_records_migrate_notes_and_todos_without_changing_originals(self):
        originals = []
        old_section = '# moneys/# reports'
        for index in range(3):
            path = old_section + '/' + str(index + 1)
            self.folder(path)
            blocks = order_document.write_todos({'Неизвестный блок': 'Сохранить'}, [{'text': 'Задача ' + str(index), 'done': bool(index)}])
            self.store.add(path, {'title': 'Сверка ' + str(index), 'note': 'Прежняя заметка ' + str(index), 'status': 'done', 'amount': 12345, 'extra_blocks': blocks})
        with self.store.connect() as db:
            originals = [tuple(row) for row in db.execute('SELECT * FROM orders ORDER BY path')]
        (self.root / self.section).rmdir()
        (self.root / old_section).rename(self.root / self.section)
        folder = manager.read_folder(self.section)
        self.assertFalse(folder['warnings'])
        self.assertEqual(len(self.service.catalog()), 3)
        self.assertFalse(self.store.list())
        for index in range(3):
            record = self.service.get(self.section + '/' + str(index + 1))
            self.assertEqual(record['note'], 'Прежняя заметка ' + str(index))
            self.assertEqual(record['todo_items'], [{'text': 'Задача ' + str(index), 'done': bool(index)}])
        with self.store.connect() as db:
            self.assertEqual([tuple(row) for row in db.execute('SELECT * FROM orders ORDER BY path')], originals)
        self.assertTrue(list((self.store.database.parent / 'backups').glob('*before-reconciliations.sqlite3')))

    def test_creation_is_not_an_order_has_no_events_or_service_folders_and_safe_undo(self):
        status, _, body = self.post('/api/order-folder-create', {'path': self.section, 'date': '2026-10-29', 'title': 'Новая сверка'})
        self.assertEqual(status, 201, body)
        created = json.loads(body)
        self.assertEqual(list((self.root / created['path']).iterdir()), [])
        record = self.service.get(created['path'])
        folder = manager.read_folder(created['path'])
        self.assertEqual(folder['reconciliation']['id'], record['id'])
        self.assertFalse(folder['canRegisterOrder'])
        self.assertFalse(folder['canCreateOrderFolder'])
        self.assertFalse(folder['canCreateEventFolder'])
        self.assertNotIn('order', folder)
        self.assertIsNone(self.store.get(created['path']))
        for route, payload in [('/api/order-add', {'path': created['path']}), ('/api/event-folder-create', {'path': created['path'], 'title': 'Событие'})]:
            self.assertEqual(self.post(route, payload)[0], 400)
        with self.assertRaisesRegex(ValueError, 'Сверка сохранена'):
            folder_layout.undo(self.root / created['journal'], True)

    def test_folder_note_migrates_and_unknown_todos_never_get_replaced(self):
        old = '# moneys/# reports/01'
        self.folder(old)
        notes = manager.folder_note_store()
        previous = notes.read(old)
        notes.save({'path': old, 'revision': previous['revision'], 'note': 'Заметка без регистрации',
                    'todo_items': [{'text': 'Выполненная задача', 'done': True}]})
        with self.store.connect() as db:
            original = tuple(db.execute('SELECT * FROM folder_notes WHERE path=?', (old,)).fetchone())
        (self.root / self.section).rmdir()
        (self.root / '# moneys/# reports').rename(self.root / self.section)
        record = self.service.open(self.section + '/01')
        self.assertEqual(record['note'], 'Заметка без регистрации')
        self.assertEqual(record['todo_items'], [{'text': 'Выполненная задача', 'done': True}])
        with self.store.connect() as db:
            self.assertEqual(tuple(db.execute('SELECT * FROM folder_notes WHERE path=?', (old,)).fetchone()), original)
        invalid = self.section + '/02'
        self.folder(invalid)
        with self.store.connect() as db:
            db.execute('INSERT INTO orders (path,id,title,status,note,revision,updated,extra_blocks) VALUES (?,?,?,\'new\',\'\',1,0,?)',
                       (invalid, str(uuid.uuid4()), 'Не менять', json.dumps({'Задачи': 'Неизвестный формат'})))
        with self.assertRaisesRegex(ValueError, 'Неизвестный формат To-do'):
            self.service.open(invalid)
        with self.store.connect() as db:
            self.assertIsNone(db.execute('SELECT 1 FROM reconciliations WHERE path=?', (invalid,)).fetchone())
            self.assertEqual(json.loads(db.execute('SELECT extra_blocks FROM orders WHERE path=?', (invalid,)).fetchone()[0]), {'Задачи': 'Неизвестный формат'})

    def test_original_order_pages_cannot_save_into_the_new_entity(self):
        target = self.reconciliation()
        for path in (target['path'], target['path'].replace('# reconciliations', '# reports')):
            for route in ('/api/order-save', '/api/folder-note-save', '/api/status', '/api/note'):
                self.assertEqual(self.post(route, {'path': path, 'note': 'Старая вкладка', 'revision': 1})[0], 400)
        self.assertEqual(self.service.get(target['path'])['note'], '')

    def test_pending_creation_recovers_the_same_reconciliation(self):
        with patch.object(reconciliations, 'insert', side_effect=ValueError('Временный сбой')):
            status, _, _ = self.post('/api/order-folder-create', {'path': self.section, 'date': '2026-10-29', 'title': 'Повтор'})
        self.assertEqual(status, 409)
        with self.store.connect() as db:
            data = json.loads(db.execute("SELECT data FROM metadata_records WHERE kind='order_creation'").fetchone()[0])
        order_creation.recover(self.store)
        record = self.service.get(self.section + '/2026-10-29 - Повтор')
        self.assertEqual(record['id'], data['order_id'])
        self.assertEqual(len(self.service.catalog()), 1)
        self.assertFalse(self.store.list())

    def test_one_assignment_is_atomic_and_preserves_invoice_and_order(self):
        invoice, first, second = self.invoice(), self.reconciliation('Первая'), self.reconciliation('Вторая')
        with self.store.connect() as db:
            before_invoice = tuple(db.execute('SELECT * FROM invoices WHERE id=?', (invoice['id'],)).fetchone())
            before_order = tuple(db.execute('SELECT * FROM orders WHERE path=?', (invoice['path'],)).fetchone())
        def attempt(target):
            try:
                return self.assign(invoice, target)
            except reconciliations.ReconciliationConflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, [first, second]))
        accepted = [value for value in results if value]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(sum(len(self.service.get(item['path'])['invoices']) for item in [first, second]), 1)
        target = second if accepted[0]['id'] == first['id'] else first
        link = self.assign(invoice, target, accepted[0]['revision'])
        self.assertEqual(link['id'], target['id'])
        self.assign(invoice, None, link['revision'])
        with self.store.connect() as db:
            self.assertEqual(tuple(db.execute('SELECT * FROM invoices WHERE id=?', (invoice['id'],)).fetchone()), before_invoice)
            self.assertEqual(tuple(db.execute('SELECT * FROM orders WHERE path=?', (invoice['path'],)).fetchone()), before_order)
            self.assertEqual(db.execute("SELECT count(*) FROM metadata_history WHERE entity='reconciliation_invoices'").fetchone()[0], 2)

    def test_invoice_and_target_versions_and_plans_are_checked(self):
        invoice, target = self.invoice(), self.reconciliation()
        stale = {**invoice, 'revision': invoice['revision'] - 1}
        with self.assertRaises(reconciliations.ReconciliationConflict):
            self.assign(stale, target)
        with self.assertRaises(reconciliations.ReconciliationConflict):
            self.assign(invoice, {**target, 'revision': True})
        plan = manager.invoice_store().plan({'path': invoice['path'], 'id': str(uuid.uuid4()), 'date': '2026-10-29', 'operation': 'invoice'})
        with self.assertRaisesRegex(ValueError, 'не план'):
            self.assign(plan, target)
        self.assertFalse(self.service.get(target['path'])['invoices'])

    def test_save_conflicts_unknown_format_and_http_page_protection(self):
        target = self.reconciliation()
        payload = {**target, 'client': 'Поставщик', 'note': 'Новая заметка', 'todo_items': [{'text': 'Проверить', 'done': False}]}
        status, _, body = self.post('/api/reconciliation-save', payload)
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body)['client'], 'Поставщик')
        self.assertEqual(self.post('/api/reconciliation-save', payload)[0], 409)
        self.assertEqual(self.post('/api/reconciliation-save', payload, {'Content-Type': 'application/json'})[0], 403)
        self.assertEqual(self.post('/api/reconciliation-save', payload, {'Content-Type': 'application/json', 'X-Manager-Reconciliations': '1', 'Origin': 'http://foreign.example'})[0], 403)
        with self.store.connect() as db:
            db.execute('UPDATE reconciliations SET data=? WHERE id=?', (json.dumps({'version': 99, 'unknown': 'Не менять'}), target['id']))
        with self.assertRaisesRegex(ValueError, 'Неизвестный формат'):
            self.service.save({**payload, 'revision': target['revision'] + 1})
        with self.store.connect() as db:
            self.assertEqual(json.loads(db.execute('SELECT data FROM reconciliations WHERE id=?', (target['id'],)).fetchone()[0]), {'version': 99, 'unknown': 'Не менять'})

    def test_polling_works_offline_and_rename_undo_keeps_assignment(self):
        invoice, target = self.invoice(), self.reconciliation()
        self.assign(invoice, target)
        preview = folder_rename.preview(self.store, target['path'])
        renamed = folder_rename.rename(self.store, {**preview, 'name': 'Новое имя', 'confirmed': True})
        current = self.service.get(renamed['path'])
        self.assertEqual(current['id'], target['id'])
        self.assertEqual(current['invoices'][0]['id'], invoice['id'])
        folder_rename_undo.undo(self.root / renamed['journal'], True)
        self.root.rename(self.base / 'Документы временно недоступны')
        with patch.object(self.store, 'target', side_effect=AssertionError('Опрос читает документы')):
            self.assertEqual(self.service.get(target['path'])['invoices'][0]['id'], invoice['id'])
            self.assertEqual(len(self.service.catalog()), 1)

    def test_rollback_without_reconciliations_is_blocked(self):
        self.reconciliation()
        release = self.base / 'old-release'
        release.mkdir()
        (release / 'local_metadata.py').write_text('# SQLite')
        with self.assertRaisesRegex(RuntimeError, 'сверки'):
            remote.check_event_rename_compatibility(self.store.database, release)
        (release / 'reconciliations.py').write_text('RECONCILIATIONS_VERSION = 1')
        remote.check_event_rename_compatibility(self.store.database, release)
