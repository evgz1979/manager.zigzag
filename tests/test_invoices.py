from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import subprocess
import uuid
import unittest
from unittest.mock import patch

import invoices
import test_server as fixtures

manager = fixtures.manager


class InvoiceTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/2026-00-00 - Заказ"

    def store(self):
        return manager.invoice_store()

    def draft(self, **changes):
        manager.order_store().add(self.path, {"status": "new", "title": "Вывеска"})
        row = self.store().create({"id": str(uuid.uuid4()), "path": self.path})
        row["data"].update(buyer_name="ООО Покупатель", buyer_inn="7701234560",
                           items=[{"name": "Объёмные буквы", "quantity": "14", "unit": "шт", "price": "4200"}])
        row["data"].update(changes)
        return self.save(row)

    def save(self, row, **changes):
        return self.store().save({"path": row["path"], "id": row["id"], "revision": row["revision"], "data": row["data"], **changes})

    def issue(self, row):
        # Compile once outside disposable fixture databases, as with image reports.
        binary = invoices.renderer(manager.APP_DIR, manager.APP_DIR / "data")
        with patch.object(invoices, "renderer", return_value=binary):
            return self.store().issue({"path": row["path"], "id": row["id"], "revision": row["revision"]})

    def test_decimal_rounding_is_per_line_and_not_float(self):
        row = self.draft(items=[{"name": "A", "quantity": "0,005", "unit": "м", "price": "1,00"},
                                {"name": "B", "quantity": "0.005", "unit": "м", "price": "1"}])
        self.assertEqual(row["data"]["total"], 2)
        self.assertEqual([x["amount"] for x in row["data"]["items"]], [1, 1])
        for qty in ("NaN", "Infinity", "-1", "0.0001", "1e9999"):
            row["data"]["items"][0]["quantity"] = qty
            with self.assertRaises(ValueError):
                self.save(row)

    def test_list_status_survives_draft_edits_and_issue_and_new_copy_is_unmarked(self):
        draft = self.draft()
        marked = self.store().save_list_status({**draft, 'value': 'later'})
        marked['data']['note'] = 'Правка текста черновика'
        marked['data']['_list_status'] = 'sent'  # Only the partial status endpoint may change this field.
        saved = self.save(marked)
        self.assertEqual(saved['list_status'], 'later')
        issued = self.issue(saved)
        self.assertEqual(issued['list_status'], 'later')
        pdf = self.store().pdf(self.path, issued['id'])
        sent = self.store().save_list_status({**issued, 'value': 'sent'})
        self.assertEqual(sent['list_status'], 'sent')
        self.assertEqual(self.store().pdf(self.path, issued['id']), pdf)
        copy = self.store().create({'path': self.path, 'id': str(uuid.uuid4()), 'source': sent['id']})
        self.assertEqual(copy['list_status'], 'none')
        self.assertEqual(copy['data']['note'], saved['data']['note'])

    def test_create_is_idempotent_numbering_is_annual_and_concurrent(self):
        first = self.draft()
        self.assertEqual(self.store().create({"id": first["id"], "path": self.path})["id"], first["id"])
        with patch.object(invoices, "today", return_value=date(2026, 10, 20)):
            def create(_):
                return self.store().create({"id": str(uuid.uuid4()), "path": self.path})
            with ThreadPoolExecutor(max_workers=4) as pool:
                rows = list(pool.map(create, range(6)))
            self.assertEqual(len({r["number"] for r in rows}), 6)
        with patch.object(invoices, "today", return_value=date(2027, 1, 1)):
            self.assertEqual(create(0)["number"], "1")

    def test_manual_numbers_duplicates_stale_revisions_and_seller_defaults(self):
        first, second = self.draft(), self.draft()
        second["data"]["number"] = first["number"]
        with self.assertRaises(invoices.InvoiceConflict):
            self.save(second)
        first["data"]["number"] = "П-25/1"
        first["data"]["seller"]["bank"] = "Новый банк"
        current = self.save(first, remember_seller=True)
        with self.assertRaises(invoices.InvoiceConflict):
            self.save(first)
        new = self.store().create({"id": str(uuid.uuid4()), "path": self.path})
        self.assertEqual(new["data"]["seller"]["bank"], "Новый банк")
        self.assertEqual(current["number"], "П-25/1")
        with self.store().connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM invoice_history WHERE id=?", (first["id"],)).fetchone()[0], 2)

    def test_save_and_issue_use_database_with_documents_offline(self):
        row = self.draft()
        before = manager.order_store().get(self.path)
        self.root.rename(self.base / "offline")
        row["data"]["note"] = "Без iCloud"
        row = self.save(row)
        issued = self.issue(row)
        self.store().sync()
        failed = self.store().get(self.path, row["id"])
        self.assertTrue(failed["sync_pending"])
        self.assertTrue(failed["sync_error"])
        self.assertTrue(self.store().pdf(self.path, row["id"])[0].startswith(b"%PDF-"))
        self.assertEqual(manager.order_store().get(self.path), before)
        (self.base / "offline").rename(self.root)
        self.store().sync()
        ready = self.store().get(self.path, row["id"])
        self.assertFalse(ready["sync_pending"])
        self.assertEqual((self.root / ready["pdf_path"]).read_bytes(), self.store().pdf(self.path, row["id"])[0])
        self.assertTrue(list((self.root / ".folder-layout-history").glob("*/.journal.jsonl")))
        self.assertNotEqual(issued["revision"], row["revision"])

    def test_issued_pdf_is_immutable_copying_and_retry_do_not_change_it(self):
        row = self.draft()
        issued = self.issue(row)
        original, name = self.store().pdf(self.path, row["id"])
        again = self.issue(row)
        self.assertEqual(again["revision"], issued["revision"])
        with self.assertRaises(invoices.InvoiceConflict):
            self.save(issued)
        copied = self.store().create({"id": str(uuid.uuid4()), "path": self.path, "source": row["id"]})
        self.assertNotEqual(copied["number"], row["number"])
        self.assertEqual(copied["data"]["items"], row["data"]["items"])
        self.assertEqual(self.store().pdf(self.path, row["id"]), (original, name))

    def test_existing_modified_file_and_symlinks_are_never_overwritten(self):
        row = self.issue(self.draft())
        self.file(row["pdf_path"], b"external edit")
        self.store().sync()
        self.assertEqual((self.root / row["pdf_path"]).read_bytes(), b"external edit")
        self.assertTrue(self.store().get(self.path, row["id"])["sync_error"])
        (self.root / row["pdf_path"]).unlink()
        (self.root / row["pdf_path"]).symlink_to(self.root / self.path / "Фото" / "файл%2F #.txt")
        self.store().sync()
        self.assertTrue((self.root / row["pdf_path"]).is_symlink())
        self.assertTrue(self.store().get(self.path, row["id"])["sync_pending"])

    def test_restart_after_publish_before_ack_recognizes_exact_bytes(self):
        row = self.issue(self.draft())
        self.file(row["pdf_path"], self.store().pdf(self.path, row["id"])[0])
        original = (self.root / row["pdf_path"]).stat().st_mtime_ns
        self.store().sync()
        self.assertFalse(self.store().get(self.path, row["id"])["sync_pending"])
        self.assertEqual((self.root / row["pdf_path"]).stat().st_mtime_ns, original)

    def test_contract_requires_dates_and_renders_one_page(self):
        row = self.draft(kind="contract")
        with self.assertRaises(ValueError):
            self.issue(row)
        row["data"].update(work_start=row["data"]["date"], work_end=row["data"]["due_date"])
        issued = self.issue(self.save(row))
        body, _ = self.store().pdf(self.path, issued["id"])
        pdf = self.base / "contract.pdf"; pdf.write_bytes(body)
        info = json.loads(subprocess.check_output([str(manager.pdf_renderer()), str(pdf), "info"]))
        self.assertEqual(info["pages"], 1)

    def test_oversize_fails_without_partial_pdf_or_issued_state(self):
        row = self.draft(items=[{"name": "Очень длинное наименование " * 15, "quantity": "1", "unit": "шт", "price": "10"} for _ in range(40)])
        with self.assertRaisesRegex(ValueError, "одну страницу"):
            self.issue(row)
        current = self.store().get(self.path, row["id"])
        self.assertEqual(current["state"], "draft")
        self.assertFalse((self.root / self.path / "# bills").exists())
        self.assertEqual(current["data"]["items"], row["data"]["items"])

    def test_rename_and_undo_preserve_invoices_pdf_and_outbox(self):
        row = self.issue(self.draft())
        view = manager.folder_rename.preview(manager.order_store(), self.path)
        result = manager.folder_rename.rename(manager.order_store(), {**view, "name": "2026-00-00 - Новое имя"})
        new = self.store().get(result["path"], row["id"])
        self.assertEqual(new["data"], row["data"])
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().save({"path": self.path, "id": row["id"], "revision": row["revision"], "data": row["data"]})
        manager.folder_rename.restore.undo(self.root / result["journal"], True)
        self.assertEqual(self.store().get(self.path, row["id"])["data"], row["data"])
        self.store().sync()
        self.assertFalse(self.store().get(self.path, row["id"])["sync_pending"])

    def test_edit_during_pdf_render_cancels_issue_without_losing_either_draft(self):
        row = self.draft()
        def changed(*args):
            row["data"]["note"] = "Более свежая правка"
            self.save(row)
            return b"%PDF-test"
        with patch.object(invoices, "render", side_effect=changed):
            with self.assertRaises(invoices.InvoiceConflict):
                self.store().issue({"path": self.path, "id": row["id"], "revision": row["revision"]})
        record = self.store().get(self.path, row["id"])
        self.assertEqual(record["state"], "draft")
        self.assertEqual(record["data"]["note"], "Более свежая правка")

    def test_bill_folder_symlink_and_unregistered_issuance_are_blocked(self):
        row = self.issue(self.draft())
        outside = self.base / "outside"; outside.mkdir()
        (self.root / self.path / "# bills").symlink_to(outside, target_is_directory=True)
        self.store().sync()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertTrue(self.store().get(self.path, row["id"])["sync_pending"])
        order = manager.order_store().get(self.path)
        manager.order_store().remove({"path": self.path, "revision": order["revision"], "confirmed": True})
        self.assertEqual(self.store().list(self.path)[0]["id"], row["id"])
        with self.assertRaises(ValueError):
            self.store().create({"path": self.path, "id": str(uuid.uuid4())})
        manager.order_store().add(self.path, {"status": "new"})
        self.assertEqual(self.store().list(self.path)[0]["id"], row["id"])

    def test_http_draft_issue_and_database_pdf_with_path_binding(self):
        row = self.draft()
        status, _, body = self.http(self.url("/api/invoices", self.path))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["items"][0]["id"], row["id"])
        issued = self.issue(row)
        status, headers, body = self.http(self.url("/api/invoice-pdf", self.path) + "&id=" + row["id"])
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/pdf")
        self.assertTrue(body.startswith(b"%PDF-"))
        status, _, _ = self.http(self.url("/api/invoice-pdf", "Клиент") + "&id=" + row["id"])
        self.assertEqual(status, 400)
        self.assertTrue(issued["sync_pending"])


if __name__ == "__main__":
    unittest.main()
