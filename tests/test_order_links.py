import json
import unittest
import uuid
from unittest.mock import patch

import object_orders
import order_links
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderLinksTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.store = manager.order_store()
        self.links = order_links.OrderLinks(self.store)
        self.a = self.add("Клиент/Объект/2026-10-28 - Первый")
        self.b = self.add("Клиент/Объект/2025/2025-10-28 - Второй", status="done")
        self.c = self.add("Клиент/Объект/2026-10-28 - Третий")

    def add(self, path, **changes):
        self.folder(path)
        return self.store.add(path, {"title": path.rsplit("/", 1)[-1], "status": "process", "financial_status": "partial",
            "note": "Заметка", "amount": 10000, "costs": 2000, "paid": 5000,
            "extra_blocks": {"Особое": "Сохранить", "Избранное": "Да", "Задачи": "- [ ] Позвонить"}, **changes})

    def payload(self, source=None, target=None, **changes):
        source, target = source or self.a, target or self.b
        return {"path": source["path"], "id": source["id"], "revision": source["revision"],
                "target_id": target["id"], "target_revision": target["revision"], "linked": True, **changes}

    def test_symmetric_partial_offline_write_history_idempotence_and_removal(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No iCloud reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No document reads")):
            result = self.links.save(self.payload(note="Не заменять", amount="999", status="new"))
            self.assertEqual(len(result["records"]), 2)
            a, b = self.store.get(self.a["path"]), self.store.get(self.b["path"])
            for old, new, other in ((self.a, a, b), (self.b, b, a)):
                self.assertEqual(new["related_order_ids"], [other["id"]])
                self.assertEqual(new["revision"], old["revision"] + 1)
                for key in old.keys() - {"status", "revision", "extra_blocks", "related_order_ids", "primary_related_order_ids", "primary_related_orders"}:
                    self.assertEqual(new[key], old[key], key)
                self.assertEqual({key: value for key, value in new["extra_blocks"].items() if key not in {order_links.BLOCK, order_links.PRIMARY_BLOCK}}, old["extra_blocks"])
            self.assertEqual(a["primary_related_order_ids"], [b["id"]])
            self.assertEqual(a["primary_related_orders"][0]["title"], b["title"])
            self.assertEqual(b["primary_related_order_ids"], [])
            self.assertEqual((a["status"], b["status"]), (self.a["status"], 'related'))
            self.assertEqual(self.links.save(self.payload(a, b))["records"], [])
            self.assertEqual(self.store.get(a["path"]), a)
            linked = self.links.save(self.payload(a, self.c))["order"]
            self.assertEqual(set(linked["related_order_ids"]), {b["id"], self.c["id"]})
            self.assertEqual(self.store.get(b["path"])["related_order_ids"], [a["id"]])
            self.assertEqual(self.links.read(b["path"])["order"]["id"], a["id"])
            removed = self.links.save(self.payload(linked, b, linked=False))["order"]
            self.assertEqual(removed["related_order_ids"], [self.c["id"]])
            self.assertEqual(self.store.get(b["path"])["related_order_ids"], [])
            self.assertEqual(self.store.get(b["path"])["status"], 'new')
        with self.store.connect() as db:
            histories = {row[0] for row in db.execute("SELECT identity FROM metadata_history WHERE entity='orders'")}
            self.assertTrue({a["id"], b["id"]} <= histories)
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='client_order_links'").fetchone()[0], '1')
        self.assertFalse((self.base / "offline" / a["path"] / "!.txt").exists())

    def test_full_client_and_object_scopes_across_years(self):
        excluded = [self.add(path) for path in [
            "Клиент/Другой объект/2026-10-28 - Другой",
            "Другой клиент/Объект/2026-10-28 - Другой",
            "01 - Группа/Клиент/Объект/2026-10-28 - Другой",
            "Клиент/2026-10-28 - Без объекта",
            "# work/# glass/2026-10-28 - Поставщик"]]
        data = self.links.read(self.a["path"])
        self.assertEqual({item["id"] for item in data["candidates"]}, {self.b["id"], self.c["id"]})
        self.assertNotIn(self.a["id"], {item["id"] for item in data["candidates"]})
        for other in excluded:
            with self.subTest(path=other["path"]), self.assertRaises(ValueError):
                self.links.save(self.payload(target=other))
        self.assertEqual(self.store.get(self.a["path"]), self.a)
        self.assertFalse(excluded[-1]["can_link_orders"])
        self.assertFalse(excluded[-2]["can_link_orders"])

    def test_versions_identities_and_strict_payload_validation(self):
        first = self.links.save(self.payload())
        a, b = first["order"], self.store.get(self.b["path"])
        for payload in (self.payload(), self.payload(a, self.b), self.payload(self.a, b),
                        self.payload(a, b, id=str(uuid.uuid4()))):
            with self.subTest(payload=payload), self.assertRaises(OrderConflict):
                self.links.save(payload)
        for changes in ({"revision": True}, {"revision": None}, {"target_revision": True}, {"target_revision": "2"},
                        {"linked": 1}, {"linked": "true"}, {"id": ""}, {"target_id": ""}, {"target_id": a["id"]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.links.save(self.payload(a, b, **changes))
        with self.assertRaises(OrderConflict):
            self.links.save(self.payload(a, b, target_revision=None))
        self.assertEqual(self.store.get(a["path"]), a)
        self.assertEqual(self.store.get(b["path"]), b)

    def test_unknown_formats_and_capacity_do_not_partially_change_other_order(self):
        for bad in ('{"version":2,"order_ids":[]}', '{"version":1,"order_ids":[],"future":true}', '{"version":1,"order_ids":["bad"]}'):
            with self.store.connect() as db:
                db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE id=?", (json.dumps({order_links.BLOCK: bad}), self.b["id"]))
            b = self.store.get(self.b["path"])
            self.assertIsNone(b["related_order_ids"])
            with self.assertRaises(ValueError):
                self.links.save(self.payload(target=b))
            self.assertEqual(self.store.get(self.a["path"]), self.a)
            self.assertEqual(self.store.get(b["path"]), b)
        full = order_links.write({}, [str(uuid.uuid4()) for _ in range(order_links.MAX_LINKS)])
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE id=?", (json.dumps(full), self.b["id"]))
        b = self.store.get(self.b["path"])
        with self.assertRaises(ValueError):
            self.links.save(self.payload(target=b))
        self.assertEqual(self.store.get(self.a["path"]), self.a)
        self.assertEqual(self.store.get(b["path"]), b)

    def test_registration_path_changes_and_general_card_edits_preserve_links(self):
        a = self.links.save(self.payload())["order"]
        b = self.store.get(self.b["path"])
        edited = self.store.save({**a, "note": "Новый текст", "amount": "100", "costs": "20", "paid": "50"})
        self.assertEqual(edited["related_order_ids"], [b["id"]])
        self.store.remove({"path": b["path"], "revision": b["revision"], "confirmed": True})
        item = self.links.read(a["path"])["items"][0]
        self.assertFalse(item["available"])
        self.assertEqual(item["id"], b["id"])
        restored = self.store.import_folder(b["path"])
        self.assertEqual(restored["id"], b["id"])
        self.assertEqual(restored["related_order_ids"], [a["id"]])
        new_path = "Клиент/Объект/2025/2025-10-28 - Переименованный"
        with self.store.connect() as db:
            db.execute("UPDATE orders SET path=?,revision=revision+1 WHERE id=?", (new_path, b["id"]))
        self.assertEqual(self.links.read(a["path"])["items"][0]["path"], new_path)
        self.assertEqual(order_links.OrderLinks(OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)).read(a["path"])["linked_ids"], [b["id"]])

    def test_http_roundtrip_main_and_object_rows_and_unknown_source(self):
        object_orders.ObjectOrders(self.store).refresh("Клиент/Объект")
        route = self.url("/api/order-links", self.a["path"])
        self.assertEqual(self.http(route)[0], 200)
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-links", "POST", json.dumps(self.payload()))
        self.assertEqual(status, 200, body)
        saved = json.loads(body)
        self.assertEqual(saved["linked_ids"], [self.b["id"]])
        self.assertEqual(self.http("/api/order-links", "POST", json.dumps(self.payload()))[0], 409)
        for route in ("/api/orders", self.url("/api/object-orders", "Клиент/Объект")):
            rows = json.loads(self.http(route)[2])["orders"]
            row = next(item for item in rows if item["id"] == self.a["id"])
            self.assertEqual(row["related_order_ids"], [self.b["id"]])
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE id=?", (json.dumps({order_links.BLOCK: 'future'}), self.a["id"]))
        unknown = self.store.get(self.a["path"])
        self.assertIsNone(self.links.read(unknown["path"])["linked_ids"])
        with self.assertRaises(ValueError):
            self.links.save(self.payload(unknown, self.store.get(self.b["path"])))
        self.assertEqual(self.store.get(unknown["path"]), unknown)

    def test_moved_or_missing_target_can_only_be_unlinked_without_rebinding(self):
        a = self.links.save(self.payload())["order"]
        moved = "Другой клиент/Объект/2025-10-28 - Второй"
        with self.store.connect() as db:
            db.execute("UPDATE orders SET path=?,revision=revision+1 WHERE id=?", (moved, self.b["id"]))
        b = self.store.get(moved)
        data = self.links.read(a["path"])
        self.assertFalse(data["items"][0]["available"])
        with self.assertRaises(ValueError):
            self.links.save(self.payload(a, b))
        a = self.links.save(self.payload(a, b, linked=False))["order"]
        self.assertEqual(a["related_order_ids"], [])
        self.assertEqual(self.store.get(moved)["related_order_ids"], [])
        a = self.links.save(self.payload(a, self.c))["order"]
        with self.store.connect() as db:
            db.execute("DELETE FROM orders WHERE id=?", (self.c["id"],))
        missing = self.links.read(a["path"])["items"][0]
        self.assertIsNone(missing["revision"])
        self.assertIsNone(missing["path"])
        a = self.links.save(self.payload(a, self.c, target_revision=None, linked=False))["order"]
        self.assertEqual(a["related_order_ids"], [])

    def test_restore_does_not_revive_link_removed_while_unregistered(self):
        a = self.links.save(self.payload())["order"]
        b = self.store.get(self.b["path"])
        removed = self.store.remove({"path": b["path"], "revision": b["revision"], "confirmed": True})
        a = self.links.save(self.payload(a, removed, linked=False))["order"]
        self.assertEqual(a["related_order_ids"], [])
        restored = self.store.import_folder(b["path"])
        self.assertEqual(restored["id"], b["id"])
        self.assertEqual(restored["related_order_ids"], [])
        self.assertEqual(self.links.read(restored["path"])["items"], [])

    def test_legacy_star_is_initialized_once_as_a_whole_group(self):
        with self.store.connect() as db:
            for source, ids in ((self.a, [self.b['id'], self.c['id']]), (self.b, [self.a['id']]), (self.c, [self.a['id']])):
                blocks = order_links.write(source['extra_blocks'], ids)
                db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), source['id']))
        data = self.links.read(self.b['path'])
        self.assertEqual(data['order']['id'], self.a['id'])
        self.assertTrue(data['needs_primary'])
        payload = {'path': self.a['path'], 'id': self.a['id'], 'revision': self.a['revision'], 'initialize': True, 'versions': data['versions']}
        with self.assertRaises(OrderConflict):
            self.links.save({**payload, 'versions': {**data['versions'], self.b['id']: 999}})
        self.assertEqual(self.store.get(self.b['path'])['status'], self.b['status'])
        result = self.links.save(payload)
        self.assertFalse(result['needs_primary'])
        self.assertEqual(result['order']['status'], self.a['status'])
        self.assertEqual(set(result['order']['primary_related_order_ids']), {self.b['id'], self.c['id']})
        for child in (self.b, self.c):
            record = self.store.get(child['path'])
            self.assertEqual(record['status'], 'related')
            self.assertEqual(record['related_order_ids'], [self.a['id']])
            self.assertEqual(record['primary_related_order_ids'], [])
        with self.assertRaises(ValueError):
            self.links.save({**payload, 'revision': result['order']['revision'], 'versions': result['versions']})

    def test_primary_unknown_blocks_are_preserved_and_block_partial_writes(self):
        a = self.links.save(self.payload())["order"]
        b = self.store.get(self.b["path"])
        for bad in ('future', '{"version":2,"order_ids":[]}', json.dumps({"version": 1, "order_ids": [str(uuid.uuid4())]})):
            with self.store.connect() as db:
                db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE id=?", (json.dumps({**b["extra_blocks"], order_links.PRIMARY_BLOCK: bad}), b["id"]))
            b = self.store.get(b["path"])
            self.assertIsNone(b["primary_related_order_ids"])
            for changes in ({"linked": False}, {"make_primary": True}):
                with self.subTest(bad=bad, changes=changes), self.assertRaises(ValueError):
                    self.links.save(self.payload(a, b, **changes))
            self.assertEqual(self.store.get(a["path"]), a)
        for changes in ({"make_primary": 1}, {"make_primary": "true"}, {"make_primary": True, "linked": False}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.links.save(self.payload(a, b, **changes))

    def test_primary_card_items_resolve_renames_and_removed_roles_do_not_return(self):
        a = self.links.save(self.payload())["order"]
        b = self.store.get(self.b["path"])
        with self.store.connect() as db:
            db.execute("UPDATE orders SET title='Переименованный',revision=revision+1 WHERE id=?", (b["id"],))
        a_now = self.store.get(a["path"])
        self.assertEqual(a_now["revision"], a["revision"])
        self.assertEqual(a_now["primary_related_orders"][0]["title"], 'Переименованный')
        removed = self.store.remove({"path": a["path"], "revision": a["revision"], "confirmed": True})
        b = self.store.get(b["path"])
        self.links.save(self.payload(b, removed, linked=False))
        restored = self.store.import_folder(a["path"])
        self.assertEqual(restored["primary_related_order_ids"], [])
        self.assertEqual(restored["primary_related_orders"], [])

    def test_child_unlink_always_returns_it_to_new_and_keeps_main_status(self):
        a = self.links.save(self.payload())["order"]
        b = self.store.get(self.b["path"])
        result = self.links.save(self.payload(b, a, linked=False))
        self.assertEqual(result['order']['id'], a['id'])
        self.assertEqual(result['order']['status'], a['status'])
        self.assertEqual(result['order']['updated'], a['updated'])
        b_after = self.store.get(b['path'])
        self.assertEqual(b_after['status'], 'new')
        self.assertEqual(b_after['revision'], b['revision'] + 1)
        self.assertEqual(b_after['updated'], b['updated'])
        self.assertEqual(b_after['related_order_ids'], [])
        for key in ('amount', 'costs', 'paid', 'financial_status', 'note'):
            self.assertEqual(b_after[key], b[key])

    def test_second_main_chains_cycles_and_role_switch_are_rejected(self):
        a = self.links.save(self.payload())["order"]
        b = self.store.get(self.b["path"])
        for payload in (self.payload(self.c, b), self.payload(b, self.c), self.payload(self.c, a), self.payload(b, a, make_primary=True)):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.links.save(payload)
        self.assertEqual(self.store.get(a['path']), a)
        self.assertEqual(self.store.get(b['path']), b)
        self.assertEqual(self.links.read(self.c['path'])['candidates'], [])
        self.assertEqual(self.links.read(b['path'])['order']['id'], a['id'])
        a = self.links.save(self.payload(a, self.c))['order']
        self.assertEqual({item['id'] for item in self.links.read(b['path'])['items']}, {b['id'], self.c['id']})
        self.assertEqual(a['status'], self.a['status'])

    def test_main_status_is_never_changed_for_any_production_stage(self):
        a, b = self.a, self.b
        for status in manager.STATUS_LABELS:
            a = self.store.save_status({'path': a['path'], 'revision': a['revision'], 'status': status})
            before = a
            a = self.links.save(self.payload(a, b))['order']
            self.assertEqual((a['status'], a['updated']), (status, before['updated']))
            b = self.store.get(b['path'])
            self.assertEqual(b['status'], 'related')
            a = self.links.save(self.payload(a, b, linked=False))['order']
            self.assertEqual((a['status'], a['updated']), (status, before['updated']))
            b = self.store.get(b['path'])
            self.assertEqual(b['status'], 'new')

    def test_existing_status_backfill_is_offline_atomic_and_runs_once(self):
        with self.store.connect() as db:
            for source, target, primary in ((self.a, self.b, [self.b['id']]), (self.b, self.a, [])):
                blocks = order_links.write(source['extra_blocks'], [target['id']], primary)
                db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), source['id']))
        before = self.store.get(self.b['path'])
        with patch('order_links.assert_unlocked', side_effect=ValueError('Перенос не завершён')):
            with self.assertRaises(ValueError):
                self.links.migrate_statuses()
        self.assertEqual(self.store.get(self.b['path']), before)
        self.root.rename(self.base / 'offline')
        with patch.object(OrderStore, 'target', side_effect=AssertionError('No iCloud reads')):
            self.assertEqual(self.links.migrate_statuses(), 1)
            after = self.store.get(self.b['path'])
            self.assertEqual(after['status'], 'related')
            self.assertEqual(after['revision'], before['revision'] + 1)
            for key in before.keys() - {'status', 'revision'}:
                self.assertEqual(after[key], before[key], key)
            self.assertEqual(self.store.get(self.a['path'])['status'], self.a['status'])
            self.assertEqual(self.store.get(self.c['path'])['status'], self.c['status'])
            self.assertEqual(self.links.migrate_statuses(), 0)
            self.assertEqual(self.store.get(self.b['path']), after)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='client_order_link_status'").fetchone()[0], '1')
            old = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.b['id'],))]
            self.assertTrue(any(row['status'] == self.b['status'] for row in old))

    def test_existing_links_without_known_primary_keep_their_statuses(self):
        with self.store.connect() as db:
            for source, target in ((self.a, self.b), (self.b, self.a)):
                blocks = order_links.write(source['extra_blocks'], [target['id']])
                db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), source['id']))
        self.assertEqual(self.links.migrate_statuses(), 0)
        self.assertEqual(self.store.get(self.a['path'])['status'], self.a['status'])
        self.assertEqual(self.store.get(self.b['path'])['status'], self.b['status'])


if __name__ == "__main__":
    unittest.main()
