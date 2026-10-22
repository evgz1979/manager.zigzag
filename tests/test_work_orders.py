import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import event_folders
import file_uploads
import folder_rename
import order_folders
import work_orders
from folder_structure import folder_role, is_service_folder
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class WorkOrderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    parent = '# work/2026-10-21 - Общий заказ'
    supplier = '# work/# newtek/2026-10-21 - Профиль'

    def add(self, path, blocks=None):
        self.folder(path)
        return manager.order_store().add(path, {'title': path.split('/')[-1], 'status': 'process',
            'financial_status': 'partial', 'note': 'Сохранить заметку', 'amount': 10000, 'costs': 2000, 'paid': 5000,
            'extra_blocks': blocks or {'Особое': 'Не менять', 'Задачи': '- [ ] Проверить размеры'}})

    def test_supplier_heading_uses_the_actual_section_without_document_reads(self):
        cases = {
            self.supplier: 'newtek', self.supplier + '/00 - Событие': 'newtek',
            self.supplier + '/# bills/Глубже': 'newtek',
            '#work/#antares/Любое имя/01 - Событие': 'antares',
            '# work/Новый поставщик/Без даты/Событие': 'Новый поставщик',
            '# work/2026-06 июнь/Заказ': '2026-06 июнь',
            '# work': '', '#work/#newtek': '', self.parent: '',
            self.parent + '/00 - Событие': '',
            '#work/26-10-21 - Общий/Событие': '',
            '#work/2026-00-00 - Общий/# bills/Глубже': '',
            '# moneys/#newtek/Заказ/Событие': '',
            '# glass/Заказ/Событие': '', 'Клиент/Объект/Заказ/Событие': '',
        }
        with patch('folder_structure.os.scandir', side_effect=AssertionError('No iCloud reads')):
            for path, expected in cases.items():
                with self.subTest(path=path):
                    self.assertEqual(work_orders.supplier_name(path), expected)

    def test_supplier_is_available_on_the_sqlite_order_and_event_page(self):
        self.add(self.supplier)
        event = self.supplier + '/00 - Событие'
        self.folder(event)
        with patch('folder_structure.os.scandir', side_effect=AssertionError('No iCloud reads')):
            self.assertEqual(manager.order_store().get(self.supplier)['work_supplier'], 'newtek')
        self.assertEqual(manager.read_folder(self.supplier)['workSupplier'], 'newtek')
        self.assertEqual(manager.read_folder(event)['workSupplier'], 'newtek')

    def save_links(self, parent, identities):
        return manager.order_store().save_work_links({'path': parent['path'], 'revision': parent['revision'], 'order_ids': identities})

    def test_create_direct_work_order_events_uploads_and_standalone_undo(self):
        for root in ('# work', '#work'):
            self.folder(root)
            view = manager.read_folder(root)
            self.assertTrue(view['canCreateOrderFolder'])
            self.assertFalse(view['canRegisterOrder'])
            self.assertTrue(view['noteOnly'])
            created = order_folders.create(self.root, root, '2026-10-21', 'Обычный заказ')
            path = created['path']
            self.assertEqual(folder_role(self.root, path)['folderKind'], 'order')
            self.assertFalse(is_service_folder(path))
            view = manager.read_folder(path)
            self.assertTrue(view['canRegisterOrder'])
            self.assertTrue(view['canCreateEventFolder'])
            self.assertTrue(view['canRenameFolder'])
            self.assertEqual(view['filesScope'], 'events')
            self.assertFalse(file_uploads.available(self.root, path))
            preview = event_folders.preview(self.root, path)
            event = event_folders.create(self.root, {'path': path, 'revision': preview['revision'], 'title': 'Задание'})
            self.assertTrue(manager.read_folder(event['path'])['eventFolder'])
            self.assertTrue(file_uploads.available(self.root, event['path']))
            self.folder(event['path'] + '/# docs')
            self.assertTrue(file_uploads.available(self.root, event['path'] + '/# docs'))
            self.assertFalse(folder_role(self.root, event['path'])['canRegisterOrder'])
            empty = order_folders.create(self.root, root, '2026-10-21', 'Откат создания')
            session = self.root / empty['journal']
            subprocess.run([sys.executable, str(session / '.folder-layout.py'), 'undo', str(session), '--apply'], check=True, capture_output=True)
            self.assertFalse((self.root / empty['path']).exists())

    def test_root_orders_do_not_change_existing_sections_or_financial_root(self):
        cases = {'# work/# newtek': 'work_section', '# work/Сборка': 'work_section',
                 '# work/Сборка/Без даты': 'order', '# work/2026-06 июнь': 'work_section',
                 '# moneys/2026-10-21 - Раздел': 'moneys_section',
                 self.parent + '/00 - Событие': 'event', self.parent + '/# bills': 'service'}
        for path, kind in cases.items():
            self.folder(path)
            self.assertEqual(folder_role(self.root, path)['folderKind'], kind)
        with self.assertRaises(ValueError):
            order_folders.create(self.root, self.parent, '2026-10-21', 'Вложенный заказ')
        self.folder('# moneys')
        with self.assertRaises(ValueError):
            order_folders.create(self.root, '# moneys', '2026-10-21', 'Нельзя')

    def test_linking_is_versioned_offline_partial_and_audited_without_file_changes(self):
        manager.DATABASE_ONLY = True
        parent, supplier = self.add(self.parent), self.add(self.supplier)
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*'))
        with patch.object(OrderStore, 'target', side_effect=AssertionError('No iCloud')), patch('folder_structure.os.scandir', side_effect=AssertionError('No document walks')):
            linked = self.save_links(parent, [supplier['id']])
            result = manager.order_store().work_links(self.parent)
        self.assertEqual(result['linked_ids'], [supplier['id']])
        self.assertEqual(result['items'][0]['path'], self.supplier)
        self.assertEqual(linked['revision'], parent['revision'] + 1)
        for field in ('id', 'title', 'status', 'financial_status', 'note', 'amount', 'costs', 'paid', 'todo_items', 'purchase_items', 'is_favorite'):
            self.assertEqual(linked[field], parent[field], field)
        self.assertEqual(before, sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*')))
        with manager.order_store().connect() as db:
            history = json.loads(db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=? ORDER BY seq DESC LIMIT 1", (parent['id'],)).fetchone()[0])
        self.assertEqual(history['revision'], parent['revision'])
        with self.assertRaises(OrderConflict):
            self.save_links(parent, [])
        cleared = self.save_links(linked, [])
        self.assertEqual(work_orders.read_links(cleared['extra_blocks']), [])

    def test_links_follow_supplier_and_parent_renames_and_independent_undo(self):
        manager.DATABASE_ONLY = True
        parent, supplier = self.add(self.parent), self.add(self.supplier)
        self.save_links(parent, [supplier['id']])
        store = manager.order_store()
        renamed = folder_rename.rename(store, {**folder_rename.preview(store, self.supplier), 'name': '2026-10-21 - Новое имя'})
        self.assertEqual(store.work_links(self.parent)['items'][0]['path'], renamed['path'])
        parent_renamed = folder_rename.rename(store, {**folder_rename.preview(store, self.parent), 'name': '2026-10-21 - Группа заказов'})
        self.assertEqual(store.work_links(parent_renamed['path'])['linked_ids'], [supplier['id']])
        for result in (parent_renamed, renamed):
            session = self.root / result['journal']
            subprocess.run([sys.executable, str(session / '.restore.py'), str(session), '--apply'], check=True, capture_output=True)
        self.assertEqual(store.work_links(self.parent)['items'][0]['path'], self.supplier)

    def test_unregistered_links_are_preserved_and_reregistered_with_same_identity(self):
        manager.DATABASE_ONLY = True
        parent, supplier = self.add(self.parent), self.add(self.supplier)
        linked = self.save_links(parent, [supplier['id']])
        store = manager.order_store()
        store.remove({'path': supplier['path'], 'revision': supplier['revision'], 'confirmed': True})
        view = store.work_links(self.parent)
        self.assertFalse(view['items'][0]['registered'])
        self.assertEqual(view['candidates'], [])
        linked = self.save_links(linked, [supplier['id']])
        restored = store.import_folder(self.supplier)
        self.assertEqual(restored['id'], supplier['id'])
        self.assertTrue(store.work_links(self.parent)['items'][0]['registered'])
        store.remove({'path': self.parent, 'revision': linked['revision'], 'confirmed': True})
        restored_parent = store.import_folder(self.parent)
        self.assertEqual(restored_parent['id'], parent['id'])
        self.assertEqual(store.work_links(self.parent)['linked_ids'], [supplier['id']])

    def test_invalid_and_unknown_links_do_not_replace_existing_data(self):
        parent, supplier = self.add(self.parent), self.add(self.supplier)
        ordinary = self.add('Клиент/2026-10-21 - Заказ')
        other_group = self.add('# work/2026-10-21 - Другая группа')
        for ids in ([supplier['id'], supplier['id']], [ordinary['id']], [parent['id']], [other_group['id']], ['missing'], None, 'bad', [False], [str(i) for i in range(201)]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.save_links(parent, ids)
        self.assertEqual(manager.order_store().get(self.parent)['revision'], parent['revision'])
        with self.assertRaises(ValueError):
            self.save_links(supplier, [ordinary['id']])
        unknown = self.add('# work/2026-10-21 - Будущий формат', {work_orders.LINKS_BLOCK: 'Будущие данные'})
        self.assertIsNone(manager.order_store().work_links(unknown['path'])['linked_ids'])
        with self.assertRaises(ValueError):
            self.save_links(unknown, [])
        self.assertEqual(manager.order_store().get(unknown['path'])['extra_blocks'][work_orders.LINKS_BLOCK], 'Будущие данные')

    def test_http_links_are_deduplicated_and_production_stays_out_of_main_list(self):
        parent, supplier = self.add(self.parent), self.add(self.supplier)
        payload = {'path': self.parent, 'revision': parent['revision'], 'order_ids': [supplier['id']]}
        with patch.object(manager, 'schedule_order_sync'):
            status, _, body = self.http('/api/work-order-links', 'POST', json.dumps(payload))
            self.assertEqual(status, 200, body)
            self.assertEqual(self.http('/api/work-order-links', 'POST', json.dumps(payload))[0], 409)
        result = json.loads(self.http(self.url('/api/work-order-links', self.parent))[2])
        self.assertEqual([item['id'] for item in result['items']], [supplier['id']])
        listed = json.loads(self.http('/api/orders')[2])['orders']
        self.assertEqual(listed, [])
        self.assertEqual({item['id'] for item in manager.order_store().list()}, {parent['id'], supplier['id']})

    def test_main_list_excludes_all_work_paths_but_preserves_favorites_and_cards(self):
        ordinary = self.add('Клиент/2026-10-21 - Обычный заказ')
        production = [self.add(path) for path in (self.parent, self.supplier,
            '#work/2026-10-21 - Без пробела', '# WORK/Раздел/2026-10-21 - Другой поставщик')]
        store = manager.order_store()
        starred = store.save_favorite({'path': self.parent, 'revision': production[0]['revision'], 'is_favorite': True})
        with patch.object(OrderStore, 'target', side_effect=AssertionError('List must not read iCloud')):
            result = json.loads(self.http('/api/orders')[2])
        self.assertEqual([item['id'] for item in result['orders']], [ordinary['id']])
        self.assertEqual([item['id'] for item in result['favorites']], [starred['id']])
        for order in production:
            self.assertEqual(json.loads(self.http(self.url('/api/order', order['path']))[2])['id'], order['id'])
        self.assertEqual(len(store.list()), 5)
        self.assertEqual(work_orders.in_work('Клиент/2026-10-21 - #work'), False)

    def test_work_unregistration_does_not_leak_into_main_pending_list(self):
        order = self.add(self.parent)
        store = manager.order_store()
        store.remove({'path': order['path'], 'revision': order['revision'], 'confirmed': True})
        self.assertTrue(store.pending_unregistrations())
        self.assertEqual(manager.listed_orders()['unregistrations'], [])
