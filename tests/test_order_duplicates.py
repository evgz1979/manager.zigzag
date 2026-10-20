import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

from scripts.archive_order_duplicate import archive
import test_server as fixtures

manager = fixtures.manager


class OrderDuplicateTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file

    def original(self):
        source = "Клиент/2026-00-00 - Заказ"
        store = manager.order_store()
        record = store.add(source, {"status": "process", "note": "", "extra_blocks": {"Задачи": "- [ ] Сохранить задачу"}})
        store.sync()
        record = store.get(source)
        return store, source, record

    def old_duplicate(self):
        store, source, old = self.original()
        destination = "Клиент/2026-00-00 - Переименовано"
        (self.root / source).rename(self.root / destination)
        raw = (self.root / destination / "!.txt").read_bytes()
        proof = Path('.order-history') / hashlib.sha256(raw).hexdigest() / '!.txt'
        (self.root / destination / proof).parent.mkdir(parents=True)
        (self.root / destination / proof).write_bytes(raw)
        current = store.add(destination, {"title": "Позднее название", "status": "done_but", "note": "Поздняя заметка",
                                          "extra_blocks": {"Задачи": "- [ ] Сохранить задачу\n- [ ] Новая задача"}})
        store.sync()
        current = store.get(destination)
        return store, source, destination, proof.as_posix(), old, current

    def test_finder_rename_cannot_create_second_uuid_or_overwrite_pending_data(self):
        store, source, record = self.original()
        destination = "Клиент/2026-00-00 - Новое имя"
        (self.root / source).rename(self.root / destination)
        with self.assertRaisesRegex(manager.OrderConflict, "прежнему пути"):
            store.import_folder(destination)
        self.assertEqual(len(store.list()), 1)
        self.assertIsNone(store.get(destination))
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual(progress["added"], 0)
        self.assertEqual(len(store.list()), 1)
        self.assertTrue(progress["errors"])
        with patch.object(store, "target", return_value=self.root / destination):
            store.save({**record, "note": "Невыгруженная правка", "amount": None, "costs": None, "paid": None})
        with self.assertRaises(manager.OrderConflict):
            store.import_folder(destination)
        self.assertEqual(store.get(source)["note"], "Невыгруженная правка")

    def test_real_copy_while_original_exists_remains_a_distinct_order(self):
        store, source, record = self.original()
        destination = "Клиент/2026-00-00 - Копия"
        shutil.copytree(self.root / source, self.root / destination)
        copied = store.import_folder(destination)
        self.assertNotEqual(copied["id"], record["id"])
        self.assertEqual(copied["todo_items"], record["todo_items"])
        self.assertEqual(len(store.list()), 2)

    def test_archive_proven_duplicate_preserves_current_data_and_can_undo_without_snapshot_restore(self):
        store, source, destination, proof, old, current = self.old_duplicate()
        before = {path.relative_to(self.root / destination).as_posix(): path.read_bytes()
                  for path in (self.root / destination).rglob('*') if path.is_file()}
        result = archive(store, source, destination, proof, perform=True)
        self.assertEqual(store.list(), [store.get(destination)])
        self.assertEqual(store.get(destination), current)
        self.assertIsNone(store.get(source, include_unregistered=True))
        self.assertEqual({path.relative_to(self.root / destination).as_posix(): path.read_bytes()
                          for path in (self.root / destination).rglob('*') if path.is_file()}, before)
        with store.connect() as db:
            saved = json.loads(db.execute("SELECT record FROM order_duplicate_archive").fetchone()[0])
            self.assertEqual(saved["id"], old["id"])
        moved = store.save({**current, "note": "Ещё более поздняя правка", "amount": None, "costs": None, "paid": None})
        session = Path(result["journal"])
        self.assertTrue((session / ".before.sqlite3").is_file())
        subprocess.run([sys.executable, str(session / ".restore.py"), "--undo", str(session), "--apply"], check=True, capture_output=True)
        self.assertEqual(store.get(destination)["note"], moved["note"])
        self.assertEqual(store.get(source), old)

    def test_missing_history_unique_tasks_or_pending_queue_block_archiving(self):
        store, source, destination, proof, old, current = self.old_duplicate()
        with self.assertRaises(ValueError):
            archive(store, source, destination, '.order-history/missing.txt', perform=True)
        with store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (json.dumps({"Задачи": "- [ ] Отдельная задача"}), old["id"]))
        with self.assertRaisesRegex(ValueError, "отдельные задачи"):
            archive(store, source, destination, proof, perform=True)
        with store.connect() as db:
            db.execute("UPDATE orders SET revision=revision+1 WHERE id=?", (old["id"],))
        with self.assertRaisesRegex(ValueError, "невыгруженные"):
            archive(store, source, destination, proof, perform=True)
        self.assertEqual(len(store.list()), 2)
        self.assertFalse((self.root / ".folder-layout-history").exists())

    def test_archived_uuid_is_not_silently_imported_again(self):
        store, source, destination, proof, old, current = self.old_duplicate()
        archive(store, source, destination, proof, perform=True)
        other = "Клиент/2026-00-00 - Старая копия"
        self.folder(other)
        shutil.copyfile(self.root / destination / proof, self.root / other / '!.txt')
        with self.assertRaisesRegex(manager.OrderConflict, "сохранённому дублю"):
            store.import_folder(other)
        self.assertEqual(len(store.list()), 1)


if __name__ == '__main__':
    unittest.main()
