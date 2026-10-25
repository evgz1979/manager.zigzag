import json
import unittest
import unicodedata
from unittest.mock import patch

from folder_structure import order_location
from orders import OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderLocationTests(unittest.TestCase):
    def test_objects_years_nested_containers_and_direct_orders_without_filesystem(self):
        cases = {
            "Клиент/Адрес/2026-10-20 - Заказ": ("Клиент", "Адрес", "Клиент/Адрес"),
            "Клиент/Адрес/2026/2026-10-20 - Заказ": ("Клиент", "Адрес", "Клиент/Адрес"),
            "Клиент/Адрес/Корпус/2025/00001 - Заказ": ("Клиент", "Адрес / Корпус", "Клиент/Адрес/Корпус"),
            "Клиент/Адрес/00 - Группа/00001 - Заказ": ("Клиент", "Адрес", "Клиент/Адрес"),
            "Клиент/2026/2026-10-20 - Заказ": ("Клиент", "", ""),
            "Клиент/2026-10-20 - Заказ": ("Клиент", "", ""),
            "01 - Группа/Покупатель/Адрес/2026/2026-10-20 - Заказ":
                ("01 - Группа/Покупатель", "Адрес", "01 - Группа/Покупатель/Адрес"),
            "02 - Архив/2026/2026-10-20 - Заказ": ("02 - Архив", "", ""),
            "# work/# laser/2026-10-20 - Заказ": ("# work", "", ""),
        }
        with patch("folder_structure.os.scandir", side_effect=AssertionError("No iCloud access")):
            for path, expected in cases.items():
                with self.subTest(path=path):
                    result = order_location(path)
                    self.assertEqual((result["client_path"], result["object"], result["object_path"]), expected)

    def test_canonical_keys_keep_distinct_paths_with_the_same_object_name(self):
        path = "Новый клиент/Первый объект/2026-10-20 - Заказ"
        self.assertEqual(order_location(unicodedata.normalize("NFD", path)), order_location(path))
        first = order_location("01 - Группа/Клиент/Адрес/2026-10-20 - Заказ")
        second = order_location("02 - Группа/Клиент/Адрес/2026-10-20 - Заказ")
        self.assertEqual(first["object"], second["object"])
        self.assertNotEqual(first["client_path"], second["client_path"])
        self.assertNotEqual(first["object_path"], second["object_path"])


class OrderLocationApiTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)

    def test_order_api_uses_stored_path_offline_without_changing_rows(self):
        path = "01 - Группа/Покупатель/Адрес/2026/2026-10-20 - Заказ"
        self.folder(path)
        store = manager.order_store()
        record = store.add(path, {"status": "new", "note": "Сохранить", "extra_blocks": {"Особое": "Данные"}})
        with store.connect() as db:
            before = [tuple(row) for row in db.execute("SELECT * FROM orders")]
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folder access")), \
                patch("folder_structure.os.scandir", side_effect=AssertionError("No enumeration")):
            status, _, body = self.http("/api/orders")
            rows = store.list()
        self.assertEqual(status, 200)
        row = json.loads(body)["orders"][0]
        self.assertEqual(row["object"], "Адрес")
        self.assertEqual(row["object_path"], "01 - Группа/Покупатель/Адрес")
        self.assertEqual(row["client_path"], "01 - Группа/Покупатель")
        self.assertEqual((row["id"], row["path"], row["revision"]), (record["id"], path, record["revision"]))
        self.assertEqual(rows[0]["object"], "Адрес")
        with store.connect() as db:
            self.assertEqual([tuple(row) for row in db.execute("SELECT * FROM orders")], before)
