# caldav_events.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [caldav_events.py](../../../caldav_events.py).

iCalendar representation of manager events, with one SQLite source of dates and text.

Импорты Python, включая локальные: `dataclasses`, `datetime`, `hashlib`, `order_calendar`, `order_deadlines`, `re`, `urllib.parse`, `uuid`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Resource"></a>

## Resource

[caldav_events.py](../../../caldav_events.py) · `class`.

```python
class Resource:
```

Представляет один CalDAV-ресурс и его интервал для календарного запроса.

ETag свободного события включает revision, в том числе при изменении внутренних отметок.

Непосредственные вызовы: `dataclass`.

<a id="symbol-Resource.etag"></a>

## Resource.etag

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def etag(self):
```

Считает сильный ETag представления и текущей ревизии рабочей записи.

Возвращает значение в кавычках для заголовков и DAV-свойств.

Непосредственные вызовы: `hashlib.sha256(self.body + str(self.revision).encode()).hexdigest`, `hashlib.sha256`, `str(self.revision).encode`, `str`.

Выражения возврата (ветки читаются в исходнике):

```python
'"' + digest + '"'
```

<a id="symbol-adjusted_interval"></a>

## adjusted_interval

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def adjusted_interval(row, stored, start, end):
```

Восстанавливает интервал строки из SQLite с учётом переноса в менеджере.

При смене типа привязки использует стандартную длительность дня или недели.

Непосредственные вызовы: `date.fromisoformat`, `timedelta`, `isinstance`, `start.astimezone`, `instant`.

Выражения возврата (ветки читаются в исходнике):

```python
(target, target + timedelta(days=7 if row['period'] == 'week' else 1))
(shifted_start, shifted_end)
(start + offset, end + offset)
```

<a id="symbol-encode_lines"></a>

## encode_lines

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def encode_lines(lines):
```

Формирует RFC 5545 строки по 75 октетов с CRLF и продолжением.

Делит только между символами UTF-8, чтобы клиент прочитал кириллицу без потерь.

Непосредственные вызовы: `bytearray`, `char.encode`, `len`, `result.append`, `bytes`, `chunk.extend`, `b'\r\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
b'\r\n'.join(result) + b'\r\n'
```

<a id="symbol-escape"></a>

## escape

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def escape(value):
```

Кодирует текстовое поле iCalendar с экранированием переносов и разделителей.

Встроенные CR/LF приводятся к одному виду перед экранированием.

Непосредственные вызовы: `value.replace('\r\n', '\n').replace`, `value.replace`, `normalized.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace`, `normalized.replace('\\', '\\\\').replace('\n', '\\n').replace`, `normalized.replace('\\', '\\\\').replace`, `normalized.replace`.

Выражения возврата (ветки читаются в исходнике):

```python
normalized.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')
```

<a id="symbol-event_resource"></a>

## event_resource

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def event_resource(row, stored=None):
```

Генерирует VEVENT из актуальных полей менеджера и дополнительных полей клиента.

Исходные времена и зона сохраняются до переноса записи в менеджере.

Непосредственные вызовы: `date.fromisoformat`, `timedelta`, `time_lines`, `parse`, `stored['icalendar'].encode`, `adjusted_interval`, `sorted`, `datetime.fromtimestamp(row['updated'], timezone.utc).strftime`, `datetime.fromtimestamp`, `escape`, `event.append`, `enumerate`, `Resource`, `encode_lines`, `instant`.

Выражения возврата (ветки читаются в исходнике):

```python
Resource(name, encode_lines(content), instant(start), instant(end), row['revision'])
```

<a id="symbol-instant"></a>

## instant

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def instant(value):
```

Возвращает границу календарного поиска в UTC.

Событие на весь день использует гражданскую дату Москвы.

Непосредственные вызовы: `isinstance`, `value.astimezone`, `datetime.combine(value, datetime.min.time(), MOSCOW).astimezone`, `datetime.combine`, `datetime.min.time`.

Выражения возврата (ветки читаются в исходнике):

```python
value.astimezone(timezone.utc)
datetime.combine(value, datetime.min.time(), MOSCOW).astimezone(timezone.utc)
```

<a id="symbol-order_resources"></a>

## order_resources

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def order_resources(orders, public_host):
```

Проецирует сроки и текстовые события заказа в отдельный календарь.

UID строится из UUID заказа, периода и даты, а ссылка открывает карточку.

Непосредственные вызовы: `urlencode`, `dict`, `dates.setdefault`, `dates.items`, `date.fromisoformat`, `timedelta`, `str`, `uuid.uuid5`, `datetime.fromtimestamp(order['updated'], timezone.utc).strftime`, `datetime.fromtimestamp`, `' · '.join`, `order.get`, `time_lines`, `escape`, `Resource`, `encode_lines`, `instant`.

<a id="symbol-parse"></a>

## parse

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def parse(body):
```

Разбирает структурные границы единственного обычного VEVENT.

Возвращает данные и сохраняет исходные строки, включая часовой пояс и напоминания.

Непосредственные вызовы: `body.decode('utf-8-sig').replace`, `body.decode`, `any`, `ord`, `ValueError`, `re.sub('\\n[ \\t]', '', content).strip('\n').split`, `re.sub('\\n[ \\t]', '', content).strip`, `re.sub`, `lines[0].upper`, `lines[-1].upper`, `enumerate`, `PROPERTY.fullmatch`, `match.groups`, `name.upper`, `value.upper`, `tuple`, `stack.append`, `stack.pop`, `len`, `unescape`, `order_calendar.validate_text`, `parse_time`, `uid.strip`, `uid.encode`, `parse_duration`, `isinstance`, `timedelta`, `type`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(lines, event_start, event_end, fields, uid, title, start, end)
```

<a id="symbol-parse_duration"></a>

## parse_duration

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def parse_duration(value):
```

Разбирает положительную длительность VEVENT в днях, неделях или времени.

Поддерживает одну форму RFC 5545 с непустыми единицами и проверкой диапазона.

Непосредственные вызовы: `re.fullmatch`, `any`, `match.groups`, `value.endswith`, `ValueError`, `int`, `timedelta`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
duration
```

<a id="symbol-parse_time"></a>

## parse_time

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def parse_time(params, value):
```

Разбирает дату или время свойства iCalendar.

Время с TZID интерпретирует по известной IANA-зоне, плавающее время по Москве.

Непосредственные вызовы: `re.fullmatch`, `params.upper`, `ValueError`, `datetime.strptime(value, DATE_FORMAT).date`, `datetime.strptime`, `value.endswith`, `params.lstrip(';').split`, `params.lstrip`, `param.partition`, `key.upper`, `ZoneInfo`, `name.strip`, `param.upper`, `datetime.strptime(value.rstrip('Z'), TIME_FORMAT).replace`, `value.rstrip`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
datetime.strptime(value, DATE_FORMAT).date()
datetime.strptime(value.rstrip('Z'), TIME_FORMAT).replace(tzinfo=zone)
```

<a id="symbol-placement"></a>

## placement

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def placement(start, end):
```

Переводит интервал VEVENT в привязку, пригодную для календаря менеджера.

Семь суток от понедельника считаются неделей; время привязано к дню Москвы.

Непосредственные вызовы: `isinstance`, `start.astimezone(MOSCOW).date().isoformat`, `start.astimezone(MOSCOW).date`, `start.astimezone`, `start.isoformat`, `start.weekday`.

Выражения возврата (ветки читаются в исходнике):

```python
(start.astimezone(MOSCOW).date().isoformat(), 'day')
(start.isoformat(), 'week' if start.weekday() == 0 and (end - start).days == 7 else 'day')
```

<a id="symbol-schema"></a>

## schema

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def schema(db):
```

Устанавливает таблицу свойств iCalendar рядом с рабочими событиями.

Сопоставляет одно имя ресурса и UID одному UUID, включая удалённые записи.

Непосредственные вызовы: `db.execute`.

<a id="symbol-time_lines"></a>

## time_lines

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def time_lines(start, end):
```

Формирует обычные свойства времени VEVENT.

Дату выводит без часового пояса, а точное время в UTC.

Непосредственные вызовы: `isinstance`, `instant(start).strftime`, `instant`, `result.append`, `instant(end).strftime`, `start.strftime`, `end.strftime`.

Выражения возврата (ветки читаются в исходнике):

```python
result
['DTSTART;VALUE=DATE:' + start.strftime(DATE_FORMAT), 'DTEND;VALUE=DATE:' + end.strftime(DATE_FORMAT)]
```

<a id="symbol-unescape"></a>

## unescape

[caldav_events.py](../../../caldav_events.py) · `function`.

```python
def unescape(value):
```

Декодирует только допустимые экранированные символы iCalendar TEXT.

Сохраняет прочие символы исходного значения.

Непосредственные вызовы: `re.sub`.

Выражения возврата (ветки читаются в исходнике):

```python
re.sub('\\\\([nN,;\\\\])', lambda match: '\n' if match[1].lower() == 'n' else match[1], value)
```
