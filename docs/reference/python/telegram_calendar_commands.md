# telegram_calendar_commands.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [telegram_calendar_commands.py:1](../../../telegram_calendar_commands.py#L1).

Durable, single-attempt calendar requests from the configured private chat.

Импорты Python, включая локальные: `json`, `local_metadata`, `telegram_calendar`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## decode

[telegram_calendar_commands.py:15](../../../telegram_calendar_commands.py#L15) · `function`.

```python
def decode(row):
```

Разбирает сохранённый строгий формат записи протокола.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `json.loads`, `isinstance`, `type`, `data.get`, `all`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
data
```

## enqueue

[telegram_calendar_commands.py:27](../../../telegram_calendar_commands.py#L27) · `function`.

```python
def enqueue(db, bot, chat, message):
```

Сохраняет новый запрос календаря с устойчивой идентичностью сообщения.

Работает с таблицами metadata_records, metadata_settings.

Непосредственные вызовы: `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `db.execute`, `decode`, `str`, `uuid5`, `json.dumps`.

## update

[telegram_calendar_commands.py:42](../../../telegram_calendar_commands.py#L42) · `function`.

```python
def update(db, row, data):
```

Меняет состояние существующего запроса с проверкой версии.

Работает с таблицами metadata_records.

Непосредственные вызовы: `audit`, `db.execute`, `json.dumps`, `time.time`.

## process

[telegram_calendar_commands.py:50](../../../telegram_calendar_commands.py#L50) · `function`.

```python
def process(store, data_dir, sender):
```

Обрабатывает ожидающий запрос календаря без автоматического повтора sending.

Работает с таблицами metadata_records.

Непосредственные вызовы: `telegram.SEND_LOCK.acquire`, `telegram.settings`, `token.split`, `MetadataStore(store).connect`, `MetadataStore`, `db.commit`, `db.execute`, `db.execute('SELECT * FROM metadata_records WHERE kind=? ORDER BY updated,id', (KIND,)).fetchall`, `decode`, `update`, `sender`, `str`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND id=?', (KIND, selected['id'])).fetchone`, `telegram.bot_api`, `telegram.SEND_LOCK.release`.
