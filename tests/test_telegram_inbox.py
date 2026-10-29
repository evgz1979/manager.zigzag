import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from file_comments import FileCommentConflict
from local_metadata import MetadataStore
from orders import OrderStore
import telegram_inbox as inbox
import test_server as fixtures


def message(update=10, text="Позвонить клиенту\n\nЗаказать материал", chat=42, **fields):
    return {"update_id": update, "message": {"message_id": 7, "date": 1793260800,
            "from": {"id": chat, "is_bot": False}, "chat": {"id": chat, "type": "private"},
            "text": text, **fields}}


class TelegramInboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.store = OrderStore(self.base / "documents", self.base / "data", {})

    def tearDown(self):
        self.temp.cleanup()

    def test_split_lines_keeps_order_and_identical_tasks_without_cloud(self):
        with patch.object(self.store, "target", side_effect=AssertionError("No cloud")):
            self.assertEqual(inbox.ingest(self.store, "123456", "42", [message(text="  Один  \r\n \nДва\nОдин")]), 3)
            items = inbox.items(self.store)
        self.assertEqual([item["text"] for item in items], ["Один", "Два", "Один"])
        self.assertEqual(len({item["id"] for item in items}), 3)
        self.assertFalse((self.base / "documents").exists())

    def test_replay_after_restart_preserves_completion_and_history(self):
        inbox.ingest(self.store, "123456", "42", [message()])
        item = inbox.items(self.store)[0]
        saved = inbox.complete(self.store, {**item, "completed": True})
        self.assertEqual(saved["revision"], 2)
        self.assertTrue(saved["completed"])
        restarted = OrderStore(self.store.root, self.base / "data", {})
        self.assertEqual(inbox.ingest(restarted, "123456", "42", [message(), message(update=12)]), 0)
        self.assertEqual(inbox.items(restarted)[0], saved)
        with MetadataStore(self.store).connect() as db:
            old = json.loads(db.execute("SELECT data FROM metadata_history WHERE entity='metadata_records' AND identity=?", (item["id"],)).fetchone()[0])
        self.assertFalse(json.loads(old["data"])["completed"])
        with self.assertRaises(FileCommentConflict):
            inbox.complete(self.store, {**item, "completed": False})
        restored = inbox.complete(self.store, {**saved, "completed": False})
        self.assertEqual((restored["text"], restored["completed"], restored["revision"]), (item["text"], False, 3))

    def test_many_lines_and_messages_with_same_timestamp_keep_numeric_order(self):
        lines = [f"Задача {n}" for n in range(14)]
        earlier = message(text="\n".join(lines), message_id=9)
        later = message(11, text="Следующее сообщение", message_id=10)
        inbox.ingest(self.store, "123456", "42", [later, earlier])
        self.assertEqual([item["text"] for item in inbox.items(self.store)], lines + ["Следующее сообщение"])

    def test_delete_keeps_tombstone_and_history_and_replay_cannot_restore_task(self):
        inbox.ingest(self.store, "123456", "42", [message()])
        item, other = inbox.items(self.store)
        completed = inbox.complete(self.store, {**item, "completed": True})
        removed = inbox.set_deleted(self.store, completed, True)
        self.assertEqual((removed["revision"], removed["deleted"], removed["completed"]), (3, True, True))
        self.assertEqual(inbox.items(self.store), [other])
        with self.assertRaises(FileCommentConflict):
            inbox.set_deleted(self.store, completed, True)
        with self.assertRaises(FileCommentConflict):
            inbox.complete(self.store, {**removed, "completed": False})
        restarted = OrderStore(self.store.root, self.base / "data", {})
        inbox.ingest(restarted, "123456", "42", [message(12)])
        self.assertEqual(inbox.items(restarted), [other])
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='telegram_inbox_delete'").fetchone()[0], '1')
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='metadata_records' AND identity=?", (item["id"],))]
        self.assertTrue(any(json.loads(row["data"]).get("completed") is True for row in history))
        restored = inbox.set_deleted(restarted, removed, False)
        self.assertEqual((restored["id"], restored["text"], restored["completed"], restored["revision"]),
                         (item["id"], item["text"], True, 4))
        self.assertEqual(inbox.items(restarted), [restored, other])

    def test_unknown_delete_format_and_invalid_versions_remain_untouched(self):
        inbox.ingest(self.store, "123456", "42", [message()])
        item = inbox.items(self.store)[0]
        for revision in (None, True, "1", 0):
            with self.assertRaises(ValueError):
                inbox.set_deleted(self.store, {**item, "revision": revision}, True)
        with MetadataStore(self.store).connect() as db:
            row = db.execute("SELECT data FROM metadata_records WHERE id=?", (item["id"],)).fetchone()
            data = {**json.loads(row[0]), "deleted": "unknown"}
            db.execute("UPDATE metadata_records SET data=? WHERE id=?", (json.dumps(data), item["id"]))
        with self.assertRaises(ValueError):
            inbox.set_deleted(self.store, item, True)
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(json.loads(db.execute("SELECT data FROM metadata_records WHERE id=?", (item["id"],)).fetchone()[0]), data)

    def test_only_original_messages_from_configured_private_sender(self):
        foreign = message(11, chat=99)
        bot = message(12, **{"from": {"id": 42, "is_bot": True}})
        group = message(13)
        group["message"]["chat"]["type"] = "group"
        edited = {"update_id": 14, "edited_message": message()["message"]}
        command = message(15, text="/start")
        blank = message(16, text="  \n ")
        caption = message(17, text=None, caption="Подпись")
        del caption["message"]["text"]
        self.assertEqual(inbox.ingest(self.store, "123456", "42", [foreign, bot, group, edited, command, blank, caption]), 1)
        self.assertEqual(inbox.items(self.store)[0]["text"], "Подпись")
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(inbox.cursor(db, "123456"), 18)

    def test_poll_acks_only_durable_offset_and_has_no_outgoing_messages(self):
        calls = []
        def api(token, method, payload):
            calls.append((method, payload.copy()))
            with MetadataStore(self.store).connect() as db:
                self.assertEqual(inbox.cursor(db, "123456"), payload.get("offset"))
            return [message()] if len(calls) == 1 else []
        with patch.object(inbox.telegram, "settings", return_value=("123456:secret", "42")), patch.object(inbox.telegram, "bot_api", side_effect=api):
            self.assertEqual(inbox.poll(self.store, self.base), 2)
            self.assertEqual(inbox.poll(self.store, self.base), 0)
        self.assertEqual(calls, [("getUpdates", {"timeout": 0, "limit": 20}), ("getUpdates", {"timeout": 0, "limit": 20, "offset": 11})])

    def test_failure_does_not_advance_cursor_or_overwrite_unknown_format(self):
        inbox.ingest(self.store, "123456", "42", [message()])
        with MetadataStore(self.store).connect() as db:
            db.execute("UPDATE metadata_records SET data=? WHERE kind=?", ('{"version":99}', inbox.KIND))
        with self.assertRaises(ValueError):
            inbox.ingest(self.store, "123456", "42", [message(12)])
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(inbox.cursor(db, "123456"), 11)
            self.assertEqual(db.execute("SELECT data FROM metadata_records WHERE kind=?", (inbox.KIND,)).fetchone()[0], '{"version":99}')
        for updates in ([message(13), {"update_id": True}], {}, [{"update_id": -1}]):
            with self.assertRaises(ValueError):
                inbox.ingest(self.store, "123456", "42", updates)
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(inbox.cursor(db, "123456"), 11)

    def test_bot_identity_keeps_independent_offsets(self):
        inbox.ingest(self.store, "123456", "42", [message()])
        inbox.ingest(self.store, "654321", "42", [message(1)])
        self.assertEqual(len(inbox.items(self.store)), 4)
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(inbox.cursor(db, "123456"), 11)
            self.assertEqual(inbox.cursor(db, "654321"), 2)


class TelegramInboxHTTPTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    http = fixtures.ManagerTests.http
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file

    def test_remove_and_undo_use_own_page_and_expected_revision(self):
        store = fixtures.manager.order_store()
        inbox.ingest(store, "123456", "42", [message()])
        item = inbox.items(store)[0]
        headers = {"Content-Type": "application/json", "X-Manager-Inbox": "1"}
        for route in ("/api/inbox-remove", "/api/inbox-restore"):
            self.assertEqual(self.http(route, "POST", json.dumps(item))[0], 403)
            self.assertEqual(self.http(route, "POST", json.dumps(item), {**headers, "Origin": "https://example.com"})[0], 403)
            self.assertEqual(self.http(route, "POST", json.dumps({"id": item["id"]}), headers)[0], 400)
        status, _, body = self.http("/api/inbox-remove", "POST", json.dumps(item), headers)
        self.assertEqual(status, 200)
        removed = json.loads(body)
        self.assertTrue(removed["deleted"])
        self.assertNotIn(item["id"], [entry["id"] for entry in json.loads(self.http("/api/inbox")[2])["items"]])
        self.assertEqual(self.http("/api/inbox-restore", "POST", json.dumps(item), headers)[0], 409)
        self.assertEqual(self.http("/api/inbox-restore", "POST", json.dumps(removed), headers)[0], 200)
        self.assertEqual(inbox.items(store)[0]["id"], item["id"])

    def test_list_and_partial_completion_with_origin_and_revision_checks(self):
        store = fixtures.manager.order_store()
        inbox.ingest(store, "123456", "42", [message()])
        status, _, body = self.http("/api/inbox")
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertFalse(result["configured"])
        self.assertNotIn("bot_token", body.decode())
        item = result["items"][0]
        payload = json.dumps({**item, "completed": True})
        headers = {"Content-Type": "application/json", "X-Manager-Inbox": "1"}
        self.assertEqual(self.http("/api/inbox-complete", "POST", payload)[0], 403)
        self.assertEqual(self.http("/api/inbox-complete", "POST", payload, {**headers, "Origin": "https://example.com"})[0], 403)
        self.assertEqual(self.http("/api/inbox-complete", "POST", json.dumps({**item, "completed": 1}), headers)[0], 400)
        self.assertEqual(self.http("/api/inbox-complete", "POST", payload, headers)[0], 200)
        self.assertEqual(self.http("/api/inbox-complete", "POST", payload, headers)[0], 409)
        self.assertTrue(inbox.items(store)[0]["completed"])


if __name__ == "__main__":
    unittest.main()
