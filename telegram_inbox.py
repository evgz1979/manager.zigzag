"""Durable Telegram intake. Acknowledge updates only after the SQLite commit."""
import json
import threading
import time
from uuid import NAMESPACE_URL, uuid5

from file_comments import FileCommentConflict
from local_metadata import MetadataStore, audit
import telegram_calendar as telegram

TELEGRAM_INBOX_VERSION = 1
TELEGRAM_INBOX_DELETE_VERSION = 1
KIND = "telegram_inbox_todo"
POLL_LOCK = threading.Lock()
STATUS = {"error": "", "checked_at": None}


def decode(row):
    data = json.loads(row["data"])
    if (not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1
            or not isinstance(data.get("text"), str) or not data["text"].strip()
            or type(data.get("completed")) is not bool
            or ("deleted" in data and type(data["deleted"]) is not bool)
            or type(data.get("created_at")) is not int or data["created_at"] <= 0
            or type(data.get("message_id")) is not int or data["message_id"] <= 0
            or type(data.get("line")) is not int or data["line"] < 0):
        raise ValueError("Неизвестный формат Inbox. Записи сохранены без изменений")
    return {**data, "id": row["id"], "revision": row["revision"]}


def items(store):
    with MetadataStore(store).connect() as db:
        result = [decode(row) for row in db.execute(
            "SELECT * FROM metadata_records WHERE kind=?", (KIND,))]
    return sorted((item for item in result if not item.get("deleted", False)),
                  key=lambda item: (item["created_at"], item["message_id"], item["line"], item["id"]))


def complete(store, payload):
    return change(store, payload, "completed", payload.get("completed"))


def set_deleted(store, payload, deleted):
    return change(store, payload, "deleted", deleted)


def change(store, payload, field, value):
    identity, revision = (payload.get(key) for key in ("id", "revision"))
    if (not isinstance(identity, str) or type(revision) is not int or revision < 1
            or type(value) is not bool or field not in {"completed", "deleted"}):
        raise ValueError("Передай задачу Inbox, её версию и корректное изменение")
    with MetadataStore(store).connect() as db:
        db.commit()  # Finish schema initialization also in legacy compatibility mode.
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND id=?", (KIND, identity)).fetchone()
        if row is None:
            raise FileNotFoundError("Задача Inbox не найдена")
        current = decode(row)
        if row["revision"] != revision:
            raise FileCommentConflict("Задача Inbox изменилась в другом окне. Обнови список и повтори")
        if field == "completed" and current.get("deleted", False):
            raise FileCommentConflict("Задача уже удалена из Inbox. Обнови список")
        if current.get(field, False) != value:
            data = json.loads(row["data"])
            data[field] = value
            audit(db, "metadata_records")
            db.execute("UPDATE metadata_records SET data=?,revision=revision+1 WHERE kind=? AND id=?",
                       (json.dumps(data, ensure_ascii=False), KIND, identity))
            if field == "deleted":
                db.execute("INSERT OR REPLACE INTO metadata_settings VALUES ('telegram_inbox_delete','1')")
        return decode(db.execute("SELECT * FROM metadata_records WHERE kind=? AND id=?", (KIND, identity)).fetchone())


def cursor(db, bot):
    row = db.execute("SELECT value FROM metadata_settings WHERE key=?", ("telegram_inbox_offset:" + bot,)).fetchone()
    if row is None:
        return None
    try:
        value = int(row[0])
        if value < 0:
            raise ValueError()
        return value
    except (ValueError, TypeError):
        raise ValueError("Неизвестный формат позиции Inbox. Данные сохранены без изменений") from None


def ingest(store, bot, chat, updates):
    if (not isinstance(updates, list) or any(not isinstance(update, dict)
            or type(update.get("update_id")) is not int or update["update_id"] < 0 for update in updates)):
        raise ValueError("Telegram вернул некорректные сообщения Inbox")
    with MetadataStore(store).connect() as db:
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        offset = cursor(db, bot)
        added = 0
        for update in sorted(updates, key=lambda entry: entry["update_id"]):
            if offset is not None and update["update_id"] < offset:
                continue
            message = update.get("message")
            if isinstance(message, dict):
                sender, recipient = message.get("from", {}), message.get("chat", {})
                text = message.get("text", message.get("caption"))
                if (isinstance(sender, dict) and isinstance(recipient, dict)
                        and recipient.get("type") == "private" and str(recipient.get("id")) == chat
                        and str(sender.get("id")) == chat and sender.get("is_bot") is False
                        and type(message.get("message_id")) is int and message["message_id"] > 0
                        and type(message.get("date")) is int and message["date"] > 0
                        and isinstance(text, str) and not text.lstrip().startswith("/")):
                    for line, text_line in enumerate(text.splitlines()):
                        text_line = text_line.strip()
                        if not text_line:
                            continue
                        path = f"telegram:{bot}:{chat}:{message['message_id']}:{line}"
                        data = {"version": 1, "text": text_line, "completed": False,
                                "created_at": message["date"], "bot_id": bot, "chat_id": chat,
                                "message_id": message["message_id"], "line": line}
                        row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone()
                        if row:
                            decode(row)  # Preserve completed tasks and reject unknown formats.
                        else:
                            db.execute("INSERT INTO metadata_records VALUES (?,?,?,?,1,?)",
                                       (str(uuid5(NAMESPACE_URL, path)), KIND, path,
                                        json.dumps(data, ensure_ascii=False), message["date"]))
                            added += 1
            offset = update["update_id"] + 1
        if offset is not None:
            db.execute("INSERT OR REPLACE INTO metadata_settings VALUES (?,?)", ("telegram_inbox_offset:" + bot, str(offset)))
            db.execute("INSERT OR REPLACE INTO metadata_settings VALUES ('telegram_inbox','1')")
        return added


def poll(store, data_dir):
    with POLL_LOCK:
        token, chat = telegram.settings(data_dir)
        bot = token.split(":", 1)[0]
        with MetadataStore(store).connect() as db:
            offset = cursor(db, bot)
        payload = {"timeout": 0, "limit": 20}
        if offset is not None:
            payload["offset"] = offset
        # No webhook or allowed_updates changes. An existing webhook yields a safe error.
        updates = telegram.bot_api(token, "getUpdates", payload)
        added = ingest(store, bot, chat, updates)
        STATUS.update(error="", checked_at=time.time())
        return added


def snapshot(store, data_dir):
    return {"items": items(store), **telegram.status(data_dir), **STATUS}


def worker(store, data_dir, stop):
    while not stop.is_set():
        try:
            if telegram.status(data_dir)["configured"]:
                poll(store, data_dir)
            else:
                STATUS.update(error="", checked_at=None)
        except telegram.TelegramError as error:
            STATUS["error"] = str(error)
        except Exception:
            # Never expose tokens, URLs, message contents or database exception details.
            STATUS["error"] = "Не удалось получить сообщения Inbox. Повторим автоматически"
        stop.wait(5 if not STATUS["error"] else 30)
