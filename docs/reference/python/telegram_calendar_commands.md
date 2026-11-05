# telegram_calendar_commands.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [telegram_calendar_commands.py](../../../telegram_calendar_commands.py).

Durable, single-attempt calendar requests from the configured private chat.

Импорты Python, включая локальные: `json`, `local_metadata`, `telegram_calendar`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-decode"></a>

## decode

[telegram_calendar_commands.py](../../../telegram_calendar_commands.py) · `function`.

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

<a id="symbol-enqueue"></a>

## enqueue

[telegram_calendar_commands.py](../../../telegram_calendar_commands.py) · `function`.

```python
def enqueue(db, bot, chat, message):
```

Сохраняет новый запрос календаря с устойчивой идентичностью сообщения.

Работает с таблицами metadata_records, metadata_settings.

Непосредственные вызовы: `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `db.execute`, `decode`, `str`, `uuid5`, `json.dumps`.

<a id="symbol-process"></a>

## process

[telegram_calendar_commands.py](../../../telegram_calendar_commands.py) · `function`.

```python
def process(store, data_dir, sender):
```

Обрабатывает ожидающий запрос календаря без автоматического повтора sending.

Работает с таблицами metadata_records.

Непосредственные вызовы: `telegram.SEND_LOCK.acquire`, `telegram.settings`, `token.split`, `MetadataStore(store).connect`, `MetadataStore`, `db.commit`, `db.execute`, `db.execute('SELECT * FROM metadata_records WHERE kind=? ORDER BY updated,id', (KIND,)).fetchall`, `decode`, `update`, `sender`, `str`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND id=?', (KIND, selected['id'])).fetchone`, `telegram.bot_api`, `telegram.SEND_LOCK.release`.

<a id="symbol-update"></a>

## update

[telegram_calendar_commands.py](../../../telegram_calendar_commands.py) · `function`.

```python
def update(db, row, data):
```

Меняет состояние существующего запроса с проверкой версии.

Работает с таблицами metadata_records.

Непосредственные вызовы: `audit`, `db.execute`, `json.dumps`, `time.time`.
