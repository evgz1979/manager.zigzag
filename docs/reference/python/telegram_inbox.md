# telegram_inbox.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [telegram_inbox.py](../../../telegram_inbox.py).

Durable Telegram intake. Acknowledge updates only after the SQLite commit.

Импорты Python, включая локальные: `file_comments`, `json`, `local_metadata`, `telegram_calendar`, `telegram_calendar_commands`, `threading`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-change"></a>

## change

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def change(store, payload, field, value):
```

Применяет частичное изменение задачи Inbox с проверкой UUID и версии.

Работает с таблицами metadata_records, metadata_settings.

Непосредственные вызовы: `payload.get`, `isinstance`, `type`, `ValueError`, `MetadataStore(store).connect`, `MetadataStore`, `db.commit`, `db.execute`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND id=?', (KIND, identity)).fetchone`, `FileNotFoundError`, `decode`, `FileCommentConflict`, `current.get`, `json.loads`, `audit`, `json.dumps`.

Явные исключения: `ValueError`, `FileNotFoundError`, `FileCommentConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
decode(db.execute('SELECT * FROM metadata_records WHERE kind=? AND id=?', (KIND, identity)).fetchone())
```

<a id="symbol-complete"></a>

## complete

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def complete(store, payload):
```

Меняет выполнение задачи Inbox по её UUID и ожидаемой версии.

Возвращает `change(store, payload, 'completed', payload.get('completed'))`.

Непосредственные вызовы: `change`, `payload.get`.

Выражения возврата (ветки читаются в исходнике):

```python
change(store, payload, 'completed', payload.get('completed'))
```

<a id="symbol-cursor"></a>

## cursor

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def cursor(db, bot):
```

Читает сохранённую позицию получения сообщений Telegram.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `db.execute('SELECT value FROM metadata_settings WHERE key=?', ('telegram_inbox_offset:' + bot,)).fetchone`, `db.execute`, `int`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
None
value
```

<a id="symbol-decode"></a>

## decode

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def decode(row):
```

Разбирает сохранённый строгий формат записи протокола.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `json.loads`, `isinstance`, `type`, `data.get`, `data['text'].strip`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**data, 'id': row['id'], 'revision': row['revision']}
```

<a id="symbol-ingest"></a>

## ingest

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def ingest(store, bot, chat, updates):
```

Фиксирует полученные сообщения и курсор в одной транзакции без дублей.

Работает с таблицами metadata_records, metadata_settings.

Непосредственные вызовы: `isinstance`, `any`, `type`, `update.get`, `ValueError`, `MetadataStore(store).connect`, `MetadataStore`, `db.commit`, `db.execute`, `cursor`, `sorted`, `message.get`, `recipient.get`, `str`, `sender.get`, `message.get('text', '').strip`, `calendar_commands.enqueue`, `text.lstrip().startswith`, `text.lstrip`, `enumerate`, `text.splitlines`, `text_line.strip`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `decode`, `uuid5`, `json.dumps`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
added
```

<a id="symbol-items"></a>

## items

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def items(store):
```

Читает сохранённые элементы очереди или каталога модуля.

Работает с таблицами metadata_records.

Непосредственные вызовы: `MetadataStore(store).connect`, `MetadataStore`, `decode`, `db.execute`, `sorted`, `item.get`.

Выражения возврата (ветки читаются в исходнике):

```python
sorted((item for item in result if not item.get('deleted', False)), key=lambda item: (item['created_at'], item['message_id'], item['line'], item['id']))
```

<a id="symbol-poll"></a>

## poll

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def poll(store, data_dir):
```

Получает следующую порцию сообщений Telegram и передаёт их устойчивому приёму.

Возвращает `added`.

Непосредственные вызовы: `telegram.settings`, `token.split`, `MetadataStore(store).connect`, `MetadataStore`, `cursor`, `telegram.bot_api`, `ingest`, `STATUS.update`, `time.time`.

Выражения возврата (ветки читаются в исходнике):

```python
added
```

<a id="symbol-set_deleted"></a>

## set_deleted

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def set_deleted(store, payload, deleted):
```

Меняет признак корзины, сохраняя саму запись и её историю.

Возвращает `change(store, payload, 'deleted', deleted)`.

Непосредственные вызовы: `change`.

Выражения возврата (ветки читаются в исходнике):

```python
change(store, payload, 'deleted', deleted)
```

<a id="symbol-snapshot"></a>

## snapshot

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def snapshot(store, data_dir):
```

Собирает текущее наблюдаемое состояние для проверки или показа.

Возвращает `{'items': items(store), **telegram.status(data_dir), **STATUS}`.

Непосредственные вызовы: `items`, `telegram.status`.

Выражения возврата (ветки читаются в исходнике):

```python
{'items': items(store), **telegram.status(data_dir), **STATUS}
```

<a id="symbol-worker"></a>

## worker

[telegram_inbox.py](../../../telegram_inbox.py) · `function`.

```python
def worker(store, data_dir, stop, calendar_sender=None):
```

Выполняет фоновый цикл обработки с контролем остановки или паузами.

Передаёт работу `stop.is_set`, `telegram.status`, `poll`.

Непосредственные вызовы: `stop.is_set`, `telegram.status`, `poll`, `calendar_commands.process`, `STATUS.update`, `str`, `stop.wait`.
