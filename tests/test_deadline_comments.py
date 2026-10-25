import json
import unittest
from unittest.mock import patch

import order_calendar
import order_deadlines
import object_orders
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class DeadlineCommentFormatTests(unittest.TestCase):
    def test_independent_comments_keep_marks_unknown_blocks_and_exact_text(self):
        blocks = order_deadlines.write({"Особое": "Сохранить"}, "2026-10-19", True)
        saved = order_deadlines.write_comment(blocks, "2026-10-19", '  Монтаж "фасада" <дверь>  ')
        self.assertEqual(saved[order_deadlines.BLOCK], blocks[order_deadlines.BLOCK])
        self.assertEqual(saved["Особое"], blocks["Особое"])
        self.assertEqual(order_deadlines.read_comments(saved), {"2026-10-19": '  Монтаж "фасада" <дверь>  '})
        removed = order_deadlines.write(saved, "2026-10-19", False)
        self.assertEqual(order_deadlines.read(removed), [])
        self.assertEqual(order_deadlines.read_comments(removed), order_deadlines.read_comments(saved))
        edited = order_deadlines.write_comment(removed, "2026-10-19", "Комментарий снятой недели")
        self.assertEqual(order_deadlines.read(edited), [])
        self.assertEqual(order_deadlines.read_comments(edited)["2026-10-19"], "Комментарий снятой недели")
        self.assertEqual(order_deadlines.read_comments(order_deadlines.write_comment(edited, "2026-10-19", "")), {})

    def test_unknown_and_invalid_comments_are_preserved_without_replacement(self):
        for value in ('[]', '{"version":2,"comments":{}}', '{"version":true,"comments":{}}',
                      '{"version":1,"comments":{},"future":true}', '{"version":1,"comments":{"2026-10-20":"Текст"}}',
                      '{"version":1,"comments":{"2026-10-19":42}}'):
            blocks = {order_deadlines.COMMENTS_BLOCK: value}
            with self.subTest(value=value):
                self.assertIsNone(order_deadlines.read_comments(blocks))
                with self.assertRaises(ValueError):
                    order_deadlines.write_comment(blocks, "2026-10-19", "Новый")
                self.assertEqual(blocks[order_deadlines.COMMENTS_BLOCK], value)
        for value in (None, 42, True, "Две\nстроки", "Две\rстроки", "Ноль\0", "x" * 1001):
            with self.subTest(comment=value), self.assertRaises(ValueError):
                order_deadlines.write_comment({}, "2026-10-19", value)


class DeadlineCommentApiTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/Объект/2026-10-20 - Заказ"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        blocks = order_deadlines.write({"Особое": "Сохранить", "Задачи": "- [ ] Позвонить"}, "2026-10-19", True)
        self.order = self.store.add(self.path, {"status": "process", "financial_status": "partial", "note": "Заметка",
            "amount": 10000, "costs": 2000, "paid": 5000, "extra_blocks": blocks})

    def payload(self, record=None, **changes):
        record = record or self.order
        return {"path": self.path, "id": record["id"], "revision": record["revision"],
                "week": "2026-10-19", "comment": "Монтаж двери", **changes}

    def test_comments_survive_unmark_restart_and_card_save_without_cloud_reads(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folder reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No originals")):
            saved = self.store.save_deadline_comment(self.payload(note="Не заменять", amount="999"))
            for field in self.order.keys() - {"deadline_comments", "calendar_week_events", "extra_blocks", "revision"}:
                self.assertEqual(saved[field], self.order[field], field)
            removed = self.store.save_deadline_week({**self.payload(saved), "selected": False})
            self.assertEqual(removed["deadline_weeks"], [])
            self.assertEqual(removed["deadline_comments"], {"2026-10-19": "Монтаж двери"})
            edited = self.store.save_deadline_comment(self.payload(removed, comment="Проверить размеры"))
            card = self.store.save({**edited, "note": "Новая заметка", "amount": "100", "costs": "20", "paid": "50"})
        self.assertEqual(card["deadline_comments"], {"2026-10-19": "Проверить размеры"})
        self.assertEqual(card["extra_blocks"][order_deadlines.BLOCK], removed["extra_blocks"][order_deadlines.BLOCK])
        self.assertEqual(card["extra_blocks"]["Особое"], "Сохранить")
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertEqual(restarted.get(self.path)["deadline_comments"], card["deadline_comments"])
        with self.store.connect() as db:
            old = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertTrue(any(order_deadlines.read_comments(json.loads(row["extra_blocks"])) == {"2026-10-19": "Монтаж двери"} for row in old))
        self.assertFalse((self.base / "offline" / self.path / "!.txt").exists())

    def test_http_lists_and_version_identity_validation(self):
        object_orders.ObjectOrders(self.store).refresh("Клиент/Объект")
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/order-deadline-comment", "POST", json.dumps(self.payload()))
            self.assertEqual(status, 200)
            schedule.assert_called_once()
        saved = json.loads(body)
        for route in ("/api/orders", self.url("/api/object-orders", "Клиент/Объект")):
            rows = json.loads(self.http(route)[2])["orders"]
            self.assertEqual(rows[0]["deadline_comments"], saved["deadline_comments"])
            self.assertEqual(rows[0]["updated"], self.order["updated"])
        with self.assertRaises(OrderConflict):
            self.store.save_deadline_comment(self.payload())
        with self.assertRaises(OrderConflict):
            self.store.save_deadline_comment(self.payload(saved, id="Чужой UUID"))
        for revision in (None, True, "2"):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.store.save_deadline_comment(self.payload(saved, revision=revision))
        self.assertEqual(self.store.get(self.path), saved)
        removed = self.store.remove({"path": self.path, "revision": saved["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_deadline_comment(self.payload(removed))
        restored = self.store.import_folder(self.path)
        self.assertEqual(restored["deadline_comments"], saved["deadline_comments"])

    def test_unknown_comment_format_does_not_block_week_marks_or_erase_itself(self):
        unknown = '{"version":2,"comments":{},"future":"Сохранить"}'
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?", (
                json.dumps({**self.order["extra_blocks"], order_deadlines.COMMENTS_BLOCK: unknown}), self.path))
        record = self.store.get(self.path)
        self.assertIsNone(record["deadline_comments"])
        with self.assertRaises(ValueError):
            self.store.save_deadline_comment(self.payload(record))
        marked = self.store.save_deadline_week({**self.payload(record), "week": "2026-10-26", "selected": True})
        self.assertEqual(marked["extra_blocks"][order_deadlines.COMMENTS_BLOCK], unknown)
