from contextlib import nullcontext
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

from event_folder_undo import EventRenamePending
import file_trash
import object_move
import test_external_invoices as external
import test_server as fixtures

manager = fixtures.manager


class ObjectMoveTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    source = "Клиент/Объект"
    client = "02 - Группа/Клиент"
    destination = client + "/Объект"
    order_suffix = "/2026/2026-11-01 - Заказ"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        database_only = patch.object(manager, "DATABASE_ONLY", True)
        database_only.start()
        self.patches.append(database_only)

    def populate(self):
        self.file(self.source + self.order_suffix + "/# docs/Фото/схема.cdr", b"image")
        self.file(self.source + "/.скрытый", b"hidden")
        self.folder(self.source + self.order_suffix + "/# cutter")
        self.folder(self.client)
        self.folder("Другой клиент")
        self.folder("# work/# glass")
        (self.root / self.source / ".ссылка").symlink_to("../не существует")
        store = manager.order_store()
        path = self.source + self.order_suffix
        order = store.add(path, {"status": "rework", "note": "Заказ", "amount": 12345})
        manager.folder_note_store().read(self.source)
        note = manager.folder_note_store().read(path + "/# docs/Фото")
        manager.folder_note_store().save({**note, "note": "Фото", "todo_items": [{"text": "Задача", "done": True}]})
        activity = manager.object_activity_store().read(self.source)
        manager.object_activity_store().save({**activity, "inactive": True})
        metadata = manager.metadata_store()
        metadata.put("comment", path + "/# docs/Фото/схема.cdr", {"comment": "Чертёж"}, "missing")
        invoice_store = manager.invoice_store()
        invoice = invoice_store.create({"path": path, "id": "03e1eb40-d5b4-4ef1-a999-1bc0752392f1"})
        return store, order, invoice

    def payload(self, store, identity="a" * 32):
        view = object_move.preview(store, self.source)
        client = next(item for item in view["clients"] if item["path"] == self.client)
        return {"id": identity, "path": self.source, "revision": view["revision"], "client": client["path"],
                "client_revision": client["revision"], "confirmed": True}

    def test_moves_whole_object_and_rebinds_database_with_standalone_undo(self):
        with patch.object(manager, "DATABASE_ONLY", True):
            store, order, invoice = self.populate()
            result = object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
            self.assertFalse((self.root / self.source).exists())
            destination = self.root / self.destination
            self.assertEqual((destination / ".скрытый").read_bytes(), b"hidden")
            self.assertEqual(os.readlink(destination / ".ссылка"), "../не существует")
            self.assertEqual(result["files"], 2)
            self.assertEqual(result["bytes"], 11)
            path = self.destination + self.order_suffix
            self.assertTrue((self.root / path / "# cutter").is_dir())
            self.assertEqual(store.get(path)["id"], order["id"])
            self.assertEqual(store.get(path)["client_path"], self.client)
            note = manager.folder_note_store().get(path + "/# docs/Фото")
            self.assertEqual(note["parent_order"], path)
            self.assertEqual(note["todo_items"], [{"text": "Задача", "done": True}])
            self.assertTrue(manager.object_activity_store().get(self.destination)["inactive"])
            self.assertEqual(manager.metadata_store().get("comment", path + "/# docs/Фото/схема.cdr")["comment"], "Чертёж")
            self.assertEqual(manager.invoice_store().get(path, invoice["id"])["data"], invoice["data"])
            session = self.root / result["journal"]
            hashes = json.loads((session / ".verified-files.json").read_text())["sha256"]
            self.assertEqual(hashes[".скрытый"], hashlib.sha256(b"hidden").hexdigest())
            self.assertEqual(object_move.status(store, "a" * 32)["phase"], "complete")
            subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
            self.assertEqual(store.get(self.source + self.order_suffix)["id"], order["id"])
            self.assertFalse(destination.exists())

    def test_changed_target_bytes_reverse_rename_without_updating_sqlite(self):
        store, order, _ = self.populate()
        apply = object_move.layout.apply

        def change_content(session):
            apply(session)
            file = self.root / self.destination / ".скрытый"
            info = file.stat()
            file.write_bytes(b"edited")
            os.utime(file, ns=(info.st_atime_ns, info.st_mtime_ns))

        with patch.object(object_move.layout, "apply", side_effect=change_content):
            with self.assertRaisesRegex(object_move.FolderRenameConflict, "Содержимое файла изменилось"):
                object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
        self.assertEqual(store.get(order["path"])["revision"], order["revision"])
        self.assertEqual((self.root / self.source / ".скрытый").read_bytes(), b"edited")
        self.assertFalse((self.root / self.destination).exists())
        self.assertEqual(object_move.status(store, "a" * 32)["phase"], "failed")

    def test_file_trash_keeps_storage_and_restores_comment_to_current_path(self):
        store, order, _ = self.populate()
        suffix = self.order_suffix + "/# docs/Фото/схема.cdr"
        old = self.source + suffix
        old_parent = str((self.root / old).parent.relative_to(self.root))
        other = "Клиент/Другой объект/другой.txt"
        self.file(other, b"unrelated")
        files = file_trash.preview(self.root, "Клиент", [old, other])["files"]
        deleted = file_trash.remove(self.root, "Клиент", files, True, store.database)
        session = file_trash.session_path(self.root, deleted["session"])
        plan_bytes = (session / ".plan.json").read_bytes()
        legacy_helper = session / ".restore.py"
        legacy_helper.write_text("# Previous standalone helper\n", encoding="utf-8")
        moved = object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
        new = self.destination + suffix
        self.assertFalse((self.root / new).exists())
        self.assertEqual(file_trash.list_sessions(self.root)[0]["files"], [new, other])
        self.assertEqual((session / ".plan.json").read_bytes(), plan_bytes)
        result = subprocess.run([sys.executable, str(legacy_helper)], check=True, capture_output=True)
        restored = json.loads(result.stdout)
        self.assertFalse(restored["error"], restored)
        self.assertEqual((self.root / new).read_bytes(), b"image")
        self.assertEqual((self.root / other).read_bytes(), b"unrelated")
        self.assertEqual(manager.metadata_store().get("comment", new)["comment"], "Чертёж")
        self.assertFalse((self.root / old_parent).exists())
        move_session = self.root / moved["journal"]
        subprocess.run([sys.executable, str(move_session / ".restore.py"), str(move_session), "--apply"], check=True, capture_output=True)
        self.assertEqual((self.root / old).read_bytes(), b"image")
        self.assertEqual(manager.metadata_store().get("comment", old)["comment"], "Чертёж")

    def test_invoice_copy_stays_trashed_and_can_be_restored_after_move(self):
        store, order, _ = self.populate()
        invoices = manager.invoice_store()
        fixture = external.ExternalInvoiceTests()
        record = invoices.upload(fixture.payload(path=order["path"]))
        invoices.sync()
        record = invoices.get(order["path"], record["id"])
        deleted = invoices.remove({**record, "confirmed": True})
        invoices.sync()
        self.assertEqual(invoices.list(order["path"], trashed=True)[0]["trash"]["state"], "complete")
        object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
        new = self.destination + self.order_suffix
        trashed = next(row for row in invoices.list(new, trashed=True) if row["id"] == deleted["id"])
        self.assertEqual(trashed["trash"]["token"], deleted["trash"]["token"])
        self.assertTrue((self.root / new / "# bills/.trash" / deleted["trash"]["token"] / record["filename"]).is_file())
        result = invoices.restore(trashed)
        self.assertEqual(result["id"], record["id"])
        self.assertEqual((self.root / result["pdf_path"]).read_bytes(), external.ExternalInvoiceTests.pdf)

    def test_incomplete_file_trash_stops_before_moving_anything(self):
        store, order, _ = self.populate()
        old = order["path"] + "/# docs/Фото/схема.cdr"
        files = file_trash.preview(self.root, order["path"], [old])["files"]
        with patch.object(file_trash, "rename", side_effect=OSError("iCloud временно недоступен")):
            removed = file_trash.remove(self.root, order["path"], files, True, store.database)
        self.assertTrue(removed["error"])
        with self.assertRaisesRegex(ValueError, "в корзину или обратно прерван"):
            object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
        self.assertTrue((self.root / old).is_file())
        self.assertFalse((self.root / self.destination).exists())

    def test_undo_move_rebinds_files_still_in_trash(self):
        store, order, _ = self.populate()
        old = order["path"] + "/# docs/Фото/схема.cdr"
        files = file_trash.preview(self.root, order["path"], [old])["files"]
        deleted = file_trash.remove(self.root, order["path"], files, True, store.database)
        moved = object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
        session = self.root / moved["journal"]
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        self.assertEqual(file_trash.list_sessions(self.root)[0]["files"], [old])
        self.assertFalse((self.root / old).exists())
        self.assertFalse(file_trash.restore(self.root, deleted["session"])["error"])
        self.assertEqual(manager.metadata_store().get("comment", old)["comment"], "Чертёж")

    def test_destination_changed_or_saved_data_conflict_keeps_source(self):
        store, order, _ = self.populate()
        view = self.payload(store)
        parent = self.root / self.client
        parent.rename(parent.with_name("Бывший клиент"))
        parent.mkdir()
        with self.assertRaisesRegex(object_move.FolderRenameConflict, "изменилась"):
            object_move.move(store, view, lambda **_: None, nullcontext)
        manager.metadata_store().put("comment", self.destination.upper() + "/файл.txt", {"comment": "Данные"}, "missing")
        with self.assertRaisesRegex(object_move.FolderRenameConflict, "сохранённые данные"):
            object_move.move(store, self.payload(store), lambda **_: None, nullcontext)
        self.assertEqual(store.get(order["path"])["id"], order["id"])
        self.assertFalse((self.root / self.destination).exists())

    def test_http_reports_progress_during_stalled_target_read_and_protects_both_paths(self):
        store, order, _ = self.populate()
        pending, release = threading.Event(), threading.Event()
        digest = object_move.file_digest
        identity = "b" * 32

        def stalled_digest(*args):
            if (self.root / self.destination).exists():
                pending.set()
                if not release.wait(10):
                    raise RuntimeError("Test did not release the read")
            return digest(*args)

        headers = {"Content-Type": "application/json", "X-Manager-Object-Move": "1"}
        preview_route = self.url("/api/object-move", self.source)
        status_route = "/api/object-move-status?id=" + identity
        code, _, body = self.http(preview_route)
        self.assertEqual(code, 200, body)
        self.assertEqual({item["path"] for item in json.loads(body)["clients"]}, {self.client, "Другой клиент"})
        self.assertEqual(self.http(self.url("/api/object-move", order["path"]))[0], 400)
        payload = json.dumps(self.payload(store, identity))
        self.assertEqual(self.http("/api/object-move", "POST", payload)[0], 403)
        with patch.object(object_move, "file_digest", side_effect=stalled_digest), patch.object(manager, "refresh_after_object_move"):
            self.assertEqual(self.http("/api/object-move", "POST", payload, headers)[0], 202)
            try:
                self.assertTrue(pending.wait(10))
                code, _, body = self.http(status_route)
                self.assertEqual(code, 200, body)
                job = json.loads(body)
                self.assertEqual(job["phase"], "verifying")
                self.assertEqual(job["total_files"], 2)
                self.assertTrue(job["current"])
                self.assertEqual(self.http("/api/object-move", "POST", payload, headers)[0], 202)
                for scope in (self.source, self.destination):
                    with self.assertRaises(EventRenamePending):
                        store.get(scope + self.order_suffix)
            finally:
                release.set()
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    job = json.loads(self.http(status_route)[2])
                    if job["phase"] in ("complete", "failed"):
                        break
                    time.sleep(0.05)
        self.assertEqual(job["phase"], "complete", job)
        self.assertEqual(store.get(self.destination + self.order_suffix)["id"], order["id"])
