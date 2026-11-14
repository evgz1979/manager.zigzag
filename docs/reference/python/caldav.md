# caldav.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [caldav.py](../../../caldav.py).

CalDAV transport for the manager's free events and read-only order schedule.

Импорты Python, включая локальные: `base64`, `binascii`, `caldav_events`, `datetime`, `hashlib`, `hmac`, `json`, `orders`, `re`, `secrets`, `sqlite3`, `urllib.parse`, `uuid`, `xml.etree`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-CalendarDAV"></a>

## CalendarDAV

[caldav.py](../../../caldav.py) · `class`.

```python
class CalendarDAV:
```

Маршрутизирует свойства и отчёты для аутентифицированного аккаунта.

Запрашивает SQLite только для нужного календаря и ограничивает запрос глубиной 0 или 1.

<a id="symbol-CalendarDAV.__init__"></a>

## CalendarDAV.__init__

[caldav.py](../../../caldav.py) · `function`.

```python
def __init__(self, events, read_orders, public_host):
```

Передаёт рабочие события, источник заказов и защищённый внешний адрес.

Функция read_orders читает только зарегистрированные доступные заказы.

Прямые присваивания полям/свойствам: `self.events`, `self.read_orders`, `self.public_host`.

<a id="symbol-CalendarDAV.propfind"></a>

## CalendarDAV.propfind

[caldav.py](../../../caldav.py) · `function`.

```python
def propfind(self, handler, path):
```

Выдаёт свойства коллекций и их непосредственных членов.

При глубине 1 читает только ресурсы календаря или ctag запрошенных календарей.

Непосредственные вызовы: `parse_xml`, `read_body`, `DavError`, `request.find`, `list`, `dict.fromkeys`, `handler.headers.get`, `xml.Element`, `add_response`, `properties`, `multistatus`, `split_resource`, `self.resources(collection).get`, `self.resources`, `sorted`, `items.items`.

Явные исключения: `DavError`.

<a id="symbol-CalendarDAV.report"></a>

## CalendarDAV.report

[caldav.py](../../../caldav.py) · `function`.

```python
def report(self, handler, path):
```

Обслуживает calendar-query и calendar-multiget для коллекции.

Применяет фильтр интервала VEVENT и возвращает 404 для исчезнувших ресурсов.

Непосредственные вызовы: `DavError`, `parse_xml`, `read_body`, `request.find`, `list`, `dict.fromkeys`, `self.resources`, `xml.Element`, `request.findall`, `route_for`, `href.startswith`, `split_resource`, `items.get`, `add_response`, `properties`, `len`, `filters[0].get`, `filters[0].find`, `event_filter.get`, `any`, `event_filter.find`, `datetime.min.replace`, `datetime.max.replace`, `interval.get`, `datetime.strptime(interval.get('start'), caldav_events.UTC_FORMAT).replace`, `datetime.strptime`, `datetime.strptime(interval.get('end'), caldav_events.UTC_FORMAT).replace`, `sorted`, `items.items`, `max`, `timedelta`, `multistatus`.

Явные исключения: `DavError`.

<a id="symbol-CalendarDAV.resources"></a>

## CalendarDAV.resources

[caldav.py](../../../caldav.py) · `function`.

```python
def resources(self, collection):
```

Генерирует представления ресурсов одного календаря для текущего запроса.

Сопоставляет каждое имя с телом VEVENT и временем.

Непосредственные вызовы: `event_resources`, `caldav_events.order_resources`, `self.read_orders`.

Выражения возврата (ветки читаются в исходнике):

```python
event_resources(self.events)
{item.name: item for item in caldav_events.order_resources(self.read_orders(), self.public_host)}
```

<a id="symbol-CalendarDAV.serve"></a>

## CalendarDAV.serve

[caldav.py](../../../caldav.py) · `function`.

```python
def serve(self, handler, path, writes_allowed):
```

Обрабатывает разрешённые методы CalDAV и нормализует протокольные ошибки.

Записи блокируются при переключении рабочего сервера.

Непосредственные вызовы: `handler.reply`, `self.propfind`, `self.report`, `split_resource`, `self.resources(collection).get`, `self.resources`, `DavError`, `handler.headers.get`, `writes_allowed`, `put`, `delete`, `send_error`.

Явные исключения: `DavError`.

<a id="symbol-DavError"></a>

## DavError

[caldav.py](../../../caldav.py) · `class`.

```python
class DavError(ValueError):
```

Передаёт HTTP-статус и необязательное условие CalDAV клиенту.

Исключение прерывает операцию до фиксации изменений SQLite.

<a id="symbol-DavError.__init__"></a>

## DavError.__init__

[caldav.py](../../../caldav.py) · `function`.

```python
def __init__(self, status, tag=None):
```

Сохраняет статус и необязательный XML-тег precondition.

Параметр tag содержит полное имя элемента с пространством имён.

Непосредственные вызовы: `super().__init__`, `super`.

Прямые присваивания полям/свойствам: `self.status`, `self.tag`.

<a id="symbol-add_response"></a>

## add_response

[caldav.py](../../../caldav.py) · `function`.

```python
def add_response(root, path, values, requested, *, propname=False):
```

Добавляет один ответ в DAV multistatus.

Недоступные свойства имеют отдельный propstat со статусом 404.

Непосредственные вызовы: `xml.SubElement`, `values.keys`, `list`, `isinstance`, `element.extend`.

<a id="symbol-authorized"></a>

## authorized

[caldav.py](../../../caldav.py) · `function`.

```python
def authorized(handler, events, gate, document):
```

Проверяет отдельный Basic-пароль календаря с постоянным временем сравнения.

Пароль хранится только в устройстве, SQLite содержит его проверочное значение.

Непосредственные вызовы: `handler.headers.get_all`, `len`, `headers[0].partition`, `scheme.lower`, `base64.b64decode(encoded, validate=True).partition`, `base64.b64decode`, `USERNAME.encode`, `re.fullmatch`, `events.store.connect`, `db.execute('SELECT value FROM metadata_settings WHERE key=?', (CREDENTIAL,)).fetchone`, `db.execute`, `bool`, `hmac.compare_digest`, `credential_digest`.

Выражения возврата (ветки читаются в исходнике):

```python
False
bool(stored) and hmac.compare_digest(stored[0], credential_digest(gate, document, password))
```

<a id="symbol-credential_digest"></a>

## credential_digest

[caldav.py](../../../caldav.py) · `function`.

```python
def credential_digest(gate, document, password):
```

Вычисляет проверочное значение пароля, ограниченное текущим внешним профилем.

Смена пароля менеджера отзывает и отдельный пароль календаря.

Непосредственные вызовы: `hmac.new(gate.key(document), b'caldav:' + password, 'sha256').hexdigest`, `hmac.new`, `gate.key`.

Выражения возврата (ветки читаются в исходнике):

```python
hmac.new(gate.key(document), b'caldav:' + password, 'sha256').hexdigest()
```

<a id="symbol-delete"></a>

## delete

[caldav.py](../../../caldav.py) · `function`.

```python
def delete(handler, events, name):
```

Удаляет одно свободное событие через прежнюю корзину и проверку версии.

Чтение ETag и чтение revision берутся из одной записи.

Непосредственные вызовы: `events.connect`, `caldav_events.schema`, `db.execute('SELECT * FROM calendar_dav_objects WHERE name=?', (name,)).fetchone`, `db.execute`, `db.execute('SELECT * FROM calendar_events WHERE id=? AND deleted=0', (identity,)).fetchone`, `db.execute('SELECT 1 FROM calendar_dav_objects WHERE event_id=?', (identity,)).fetchone`, `precondition`, `caldav_events.event_resource`, `events.set_deleted`, `handler.reply`.

<a id="symbol-event_resources"></a>

## event_resources

[caldav.py](../../../caldav.py) · `function`.

```python
def event_resources(events):
```

Возвращает свободные события и их CalDAV-свойства из одного снимка SQLite.

Неизвестные форматы не публикуются и остаются в рабочей базе.

Непосредственные вызовы: `events.connect`, `caldav_events.schema`, `db.execute`, `db.execute('SELECT * FROM calendar_dav_objects').fetchall`, `db.execute('SELECT * FROM calendar_events WHERE deleted=0').fetchall`, `events.validate`, `caldav_events.event_resource`, `indexed.get`.

Выражения возврата (ветки читаются в исходнике):

```python
resources
```

<a id="symbol-manage_credentials"></a>

## manage_credentials

[caldav.py](../../../caldav.py) · `function`.

```python
def manage_credentials(handler, store, gate, document):
```

Создаёт или отзывает пароль CalDAV из штатного окна настроек.

Любое новое значение немедленно заменяет старое и возвращается в браузер один раз.

Непосредственные вызовы: `handler.headers.get_all`, `handler.headers.get_content_type`, `DavError`, `json.loads`, `read_body`, `isinstance`, `payload.get`, `gate.valid`, `store.connect`, `db.execute`, `secrets.token_urlsafe`, `credential_digest`, `password.encode`.

Явные исключения: `DavError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-multistatus"></a>

## multistatus

[caldav.py](../../../caldav.py) · `function`.

```python
def multistatus(handler, root):
```

Сериализует результат PROPFIND или REPORT в протокольный XML.

Экранирует имена, свойства и полное содержимое VEVENT стандартной библиотекой.

Непосредственные вызовы: `handler.reply`, `xml.tostring`.

<a id="symbol-parse_xml"></a>

## parse_xml

[caldav.py](../../../caldav.py) · `function`.

```python
def parse_xml(body):
```

Разбирает XML запроса без пользовательских сущностей и деклараций DTD.

Пустой запрос свойств означает PROPFIND allprop.

Непосредственные вызовы: `body.decode`, `DavError`, `xml.fromstring`.

Явные исключения: `DavError`.

Выражения возврата (ветки читаются в исходнике):

```python
None
xml.fromstring(text)
```

<a id="symbol-precondition"></a>

## precondition

[caldav.py](../../../caldav.py) · `function`.

```python
def precondition(handler, resource, *, deleting=False):
```

Проверяет точный ETag операции записи.

Для удаления и замены требуется совпадение версии, для создания допускается If-None-Match.

Непосредственные вызовы: `handler.headers.get`, `DavError`, `tag.strip`, `match.split`.

Явные исключения: `DavError`.

<a id="symbol-privileges"></a>

## privileges

[caldav.py](../../../caldav.py) · `function`.

```python
def privileges(writable):
```

Строит XML-значение DAV-привилегии для конкретного ресурса.

Календарь заказов никогда не получает прав создания и удаления.

Непосредственные вызовы: `xml.Element`, `xml.SubElement`, `result.append`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-properties"></a>

## properties

[caldav.py](../../../caldav.py) · `function`.

```python
def properties(path, item, resources, requested):
```

Собирает доступные свойства коллекции или отдельного VEVENT.

ctag меняется при создании, переносе, правке или исчезновении любого ресурса.

Непосредственные вызовы: `str`, `len`, `privileges`, `path.startswith`, `item.body.decode`, `xml.Element`, `types.append`, `xml.SubElement`, `reports.append`, `values.update`, `hashlib.sha256('\n'.join((name + item.etag for (name, item) in sorted(resources.items()))).encode()).hexdigest`, `hashlib.sha256`, `'\n'.join((name + item.etag for (name, item) in sorted(resources.items()))).encode`, `'\n'.join`, `sorted`, `resources.items`.

Выражения возврата (ветки читаются в исходнике):

```python
{DAV + 'resourcetype': (), DAV + 'getcontenttype': 'text/calendar; charset=utf-8', DAV + 'getcontentlength': str(len(item.body)), DAV + 'getetag': item.etag, DAV + 'current-user-privilege-set': privileges(path.startswith(EVENTS)), CAL + 'calendar-data': item.body.decode() if CAL + 'calendar-data' in requested else ''}
values
```

<a id="symbol-put"></a>

## put

[caldav.py](../../../caldav.py) · `function`.

```python
def put(handler, events, name):
```

Создаёт или заменяет одно свободное событие со свойствами CalDAV.

Имя, UID, ревизия и даты проверяются в транзакции рабочей базы.

Непосредственные вызовы: `handler.headers.get_content_type`, `DavError`, `read_body`, `caldav_events.parse`, `caldav_events.placement`, `caldav_events.unescape`, `events.connect`, `caldav_events.schema`, `db.execute`, `db.execute('SELECT * FROM calendar_dav_objects WHERE name=?', (name,)).fetchone`, `str`, `uuid.UUID`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `db.execute('SELECT 1 FROM calendar_dav_objects WHERE event_id=?', (identity,)).fetchone`, `caldav_events.event_resource`, `precondition`, `db.execute('SELECT 1 FROM calendar_dav_objects WHERE uid=?', (uid,)).fetchone`, `db.execute('SELECT 1 FROM calendar_events WHERE id=?', (uid,)).fetchone`, `uuid.uuid4`, `events.save_in_transaction`, `body.decode`, `handler.reply`.

Явные исключения: `DavError`.

<a id="symbol-read_body"></a>

## read_body

[caldav.py](../../../caldav.py) · `function`.

```python
def read_body(handler, *, optional=False, limit=256 * 1024):
```

Читает ограниченное тело запроса с однозначной длиной.

Тело без Content-Length допускается только для пустого PROPFIND.

Непосредственные вызовы: `handler.headers.get_all`, `handler.headers.get`, `DavError`, `len`, `re.fullmatch`, `int`, `handler.rfile.read`.

Явные исключения: `DavError`.

Выражения возврата (ветки читаются в исходнике):

```python
b''
body
```

<a id="symbol-route_for"></a>

## route_for

[caldav.py](../../../caldav.py) · `function`.

```python
def route_for(path, method):
```

Распознаёт только пространство CalDAV и необязательное обнаружение на корне.

GET корня по-прежнему обслуживает браузерный вход менеджера.

Непосредственные вызовы: `urlsplit`, `ROOT.rstrip`, `path.startswith`, `unquote`, `any`, `decoded.split`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
WELL_KNOWN
path
decoded + '/' if decoded + '/' in COLLECTIONS else decoded
None
```

<a id="symbol-send_error"></a>

## send_error

[caldav.py](../../../caldav.py) · `function`.

```python
def send_error(handler, error):
```

Передаёт ошибку CalDAV, включая именованное предусловие RFC.

Тело лишено внутренних данных и содержит только безопасный XML.

Непосредственные вызовы: `xml.Element`, `xml.SubElement`, `handler.reply`, `xml.tostring`.

<a id="symbol-split_resource"></a>

## split_resource

[caldav.py](../../../caldav.py) · `function`.

```python
def split_resource(path):
```

Преобразует путь в пару календарь и имя ресурса.

Имя не используется как имя файла на диске.

Непосредственные вызовы: `path.rpartition`, `NAME.fullmatch`, `name.startswith`, `DavError`.

Явные исключения: `DavError`.

Выражения возврата (ветки читаются в исходнике):

```python
(collection, name)
```
