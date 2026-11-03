"""Durable, single-attempt calendar requests from the configured private chat."""
import json
import time
from uuid import NAMESPACE_URL, uuid5

from local_metadata import MetadataStore, audit
import telegram_calendar as telegram

TELEGRAM_CALENDAR_COMMANDS_VERSION = 1
KIND = 'telegram_calendar_request'


# Разбирает сохранённый строгий формат записи протокола.
# При недопустимом состоянии возбуждает ValueError.
def decode(row):
    data = json.loads(row['data'])
    if (not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1
            or data.get('state') not in {'pending', 'sending', 'complete', 'failed'}
            or not all(isinstance(data.get(field), str) for field in ['bot_id', 'chat_id', 'error'])
            or type(data.get('message_id')) is not int or data['message_id'] <= 0):
        raise ValueError('Неизвестный формат запроса календаря. Данные сохранены')
    return data


# Сохраняет новый запрос календаря с устойчивой идентичностью сообщения.
# Работает с таблицами metadata_records, metadata_settings.
def enqueue(db, bot, chat, message):
    path = f"telegram-calendar:{bot}:{chat}:{message['message_id']}"
    existing = db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone()
    if existing:
        decode(existing)
        return
    data = {'version': 1, 'state': 'pending', 'bot_id': bot, 'chat_id': chat,
            'message_id': message['message_id'], 'error': ''}
    db.execute('INSERT INTO metadata_records VALUES (?,?,?,?,1,?)',
               (str(uuid5(NAMESPACE_URL, path)), KIND, path, json.dumps(data), message['date']))
    db.execute("INSERT OR REPLACE INTO metadata_settings VALUES ('telegram_calendar_commands','1')")


# Меняет состояние существующего запроса с проверкой версии.
# Работает с таблицами metadata_records.
def update(db, row, data):
    audit(db, 'metadata_records')
    db.execute('UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE id=? AND revision=?',
               (json.dumps(data, ensure_ascii=False), time.time(), row['id'], row['revision']))


# Обрабатывает ожидающий запрос календаря без автоматического повтора sending.
# Работает с таблицами metadata_records.
def process(store, data_dir, sender):
    if not telegram.SEND_LOCK.acquire(blocking=False):
        return
    try:
        token, chat = telegram.settings(data_dir)
        bot = token.split(':', 1)[0]
        with MetadataStore(store).connect() as db:
            db.commit()
            db.execute('BEGIN IMMEDIATE')
            selected = None
            for row in db.execute('SELECT * FROM metadata_records WHERE kind=? ORDER BY updated,id', (KIND,)).fetchall():
                data = decode(row)
                if data['state'] != 'pending':
                    continue
                if data['bot_id'] != bot or data['chat_id'] != chat:
                    update(db, row, {**data, 'state': 'failed', 'error': 'Настройка бота или чата изменилась'})
                    continue
                selected = row
                update(db, row, {**data, 'state': 'sending'})
                break
        if selected is None:
            return
        error = ''
        try:
            sender()
        except (telegram.TelegramError, ValueError) as problem:
            error = str(problem)
        except Exception:
            error = 'Не удалось отправить календарь. Проверь чат перед повтором /calendar'
        with MetadataStore(store).connect() as db:
            db.commit()
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM metadata_records WHERE kind=? AND id=?', (KIND, selected['id'])).fetchone()
            data = decode(row)
            update(db, row, {**data, 'state': 'failed' if error else 'complete', 'error': error})
        if error:
            # This is an error reply to the explicit command, never a retry of the PNG.
            try:
                telegram.bot_api(token, 'sendMessage', {'chat_id': chat, 'text': error})
            except telegram.TelegramError:
                pass
    finally:
        telegram.SEND_LOCK.release()
