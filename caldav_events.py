"""iCalendar representation of manager events, with one SQLite source of dates and text."""
import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import order_calendar
from order_deadlines import MOSCOW

PRODID = '-//Zigzag//Manager Calendar//RU'
DATE_FORMAT = '%Y%m%d'
TIME_FORMAT = '%Y%m%dT%H%M%S'
UTC_FORMAT = TIME_FORMAT + 'Z'
PROPERTY = re.compile(r'^([A-Z0-9-]+)((?:;[^:"]*(?:"[^"]*"[^:"]*)*)?):(.*)$', re.I)
EDITED_FIELDS = {'UID', 'SUMMARY', 'DESCRIPTION', 'DTSTAMP', 'LAST-MODIFIED', 'DTSTART', 'DTEND', 'DURATION'}


# Устанавливает таблицу свойств iCalendar рядом с рабочими событиями.
# Сопоставляет одно имя ресурса и UID одному UUID, включая удалённые записи.
def schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS calendar_dav_objects (
        event_id TEXT PRIMARY KEY REFERENCES calendar_events(id), name TEXT NOT NULL UNIQUE,
        uid TEXT NOT NULL UNIQUE, original_date TEXT NOT NULL, original_period TEXT NOT NULL,
        icalendar TEXT NOT NULL)""")


# Представляет один CalDAV-ресурс и его интервал для календарного запроса.
# ETag свободного события включает revision, в том числе при изменении внутренних отметок.
@dataclass(frozen=True)
class Resource:
    name: str
    body: bytes
    start: datetime
    end: datetime
    revision: int = 0

    # Считает сильный ETag представления и текущей ревизии рабочей записи.
    # Возвращает значение в кавычках для заголовков и DAV-свойств.
    @property
    def etag(self):
        digest = hashlib.sha256(self.body + str(self.revision).encode()).hexdigest()
        return '"' + digest + '"'


# Кодирует текстовое поле iCalendar с экранированием переносов и разделителей.
# Встроенные CR/LF приводятся к одному виду перед экранированием.
def escape(value):
    normalized = value.replace('\r\n', '\n').replace('\r', '\n')
    return normalized.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


# Декодирует только допустимые экранированные символы iCalendar TEXT.
# Сохраняет прочие символы исходного значения.
def unescape(value):
    return re.sub(r'\\([nN,;\\])', lambda match: '\n' if match[1].lower() == 'n' else match[1], value)


# Формирует RFC 5545 строки по 75 октетов с CRLF и продолжением.
# Делит только между символами UTF-8, чтобы клиент прочитал кириллицу без потерь.
def encode_lines(lines):
    result = []
    for line in lines:
        chunk = bytearray()
        for char in line:
            value = char.encode()
            if len(chunk) + len(value) > 75:
                result.append(bytes(chunk))
                chunk = bytearray(b' ')
            chunk.extend(value)
        result.append(bytes(chunk))
    return b'\r\n'.join(result) + b'\r\n'


# Разбирает дату или время свойства iCalendar.
# Время с TZID интерпретирует по известной IANA-зоне, плавающее время по Москве.
def parse_time(params, value):
    if re.fullmatch(r'[0-9]{8}', value):
        if params.upper() not in ('', ';VALUE=DATE'):
            raise ValueError('Некорректные параметры даты')
        return datetime.strptime(value, DATE_FORMAT).date()
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z?', value):
        raise ValueError('Некорректное время события')
    zone = timezone.utc if value.endswith('Z') else MOSCOW
    for param in params.lstrip(';').split(';'):
        key, _, name = param.partition('=')
        if key.upper() == 'TZID' and not value.endswith('Z'):
            zone = ZoneInfo(name.strip('"'))
        elif param and param.upper() != 'VALUE=DATE-TIME':
            raise ValueError('Некорректные параметры времени')
    return datetime.strptime(value.rstrip('Z'), TIME_FORMAT).replace(tzinfo=zone)


# Разбирает положительную длительность VEVENT в днях, неделях или времени.
# Поддерживает одну форму RFC 5545 с непустыми единицами и проверкой диапазона.
def parse_duration(value):
    match = re.fullmatch(r'\+?P(?:(\d{1,5})W|(?:(\d{1,5})D)?(?:T(?:(\d{1,5})H)?(?:(\d{1,5})M)?(?:(\d{1,5})S)?)?)', value)
    if not match or not any(match.groups()) or value.endswith('T'):
        raise ValueError('Некорректная длительность события')
    weeks, days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    duration = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    if duration <= timedelta():
        raise ValueError('Некорректная длительность события')
    return duration


# Разбирает структурные границы единственного обычного VEVENT.
# Возвращает данные и сохраняет исходные строки, включая часовой пояс и напоминания.
def parse(body):
    content = body.decode('utf-8-sig').replace('\r\n', '\n')
    if any(ord(char) < 32 and char not in '\n\t' or ord(char) == 127 for char in content):
        raise ValueError('Недопустимые символы iCalendar')
    lines = re.sub(r'\n[ \t]', '', content).strip('\n').split('\n')
    if lines[0].upper() != 'BEGIN:VCALENDAR' or lines[-1].upper() != 'END:VCALENDAR':
        raise ValueError('Ожидается VCALENDAR')
    stack = []
    fields = {}
    event_start = event_end = None
    for index, line in enumerate(lines):
        match = PROPERTY.fullmatch(line)
        if not match:
            raise ValueError('Повреждённая строка iCalendar')
        name, params, value = match.groups()
        name = name.upper()
        if name == 'BEGIN':
            component = value.upper()
            if stack == ['VCALENDAR'] and component == 'VEVENT' and event_start is None:
                event_start = index
            elif stack and (tuple(stack), component) not in {
                (('VCALENDAR',), 'VTIMEZONE'), (('VCALENDAR', 'VTIMEZONE'), 'STANDARD'),
                (('VCALENDAR', 'VTIMEZONE'), 'DAYLIGHT'), (('VCALENDAR', 'VEVENT'), 'VALARM')
            }:
                raise ValueError('Поддерживается одна запись VEVENT без повторений')
            stack.append(component)
        elif name == 'END':
            if not stack or stack.pop() != value.upper() or (not stack and index != len(lines) - 1):
                raise ValueError('Повреждена структура iCalendar')
            if value.upper() == 'VEVENT':
                event_end = index
        elif stack == ['VCALENDAR', 'VEVENT']:
            if name in {'RRULE', 'RECURRENCE-ID', 'RDATE', 'EXDATE', 'EXRULE', 'ATTENDEE', 'ORGANIZER'}:
                raise ValueError('Повторения и приглашения не поддерживаются')
            if name in EDITED_FIELDS:
                if name in fields:
                    raise ValueError('Свойство события указано дважды')
                fields[name] = (index, params, value)
        elif stack == ['VCALENDAR'] and name == 'METHOD':
            raise ValueError('Приглашения не поддерживаются')
    if stack or event_start is None or event_end is None:
        raise ValueError('Ожидается одна законченная запись VEVENT')
    try:
        uid = unescape(fields['UID'][2])
        title = order_calendar.validate_text(unescape(fields['SUMMARY'][2]))
        start = parse_time(*fields['DTSTART'][1:])
        if not uid.strip() or len(uid.encode()) > 512 or '\n' in uid or not title:
            raise ValueError('Нужны UID и название события')
        if 'DTEND' in fields and 'DURATION' in fields:
            raise ValueError('Укажи один способ задать окончание')
        end = (parse_time(*fields['DTEND'][1:]) if 'DTEND' in fields else
               start + parse_duration(fields['DURATION'][2]) if 'DURATION' in fields else
               start if isinstance(start, datetime) else start + timedelta(days=1))
        if type(start) is not type(end) or end < start or (type(start) is date and start == end):
            raise ValueError('Некорректный интервал события')
    except (KeyError, OverflowError, ZoneInfoNotFoundError) as exc:
        raise ValueError('Не удалось прочитать UID, название или дату события') from exc
    return lines, event_start, event_end, fields, uid, title, start, end


# Переводит интервал VEVENT в привязку, пригодную для календаря менеджера.
# Семь суток от понедельника считаются неделей; время привязано к дню Москвы.
def placement(start, end):
    if isinstance(start, datetime):
        return start.astimezone(MOSCOW).date().isoformat(), 'day'
    return start.isoformat(), 'week' if start.weekday() == 0 and (end - start).days == 7 else 'day'


# Возвращает границу календарного поиска в UTC.
# Событие на весь день использует гражданскую дату Москвы.
def instant(value):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.combine(value, datetime.min.time(), MOSCOW).astimezone(timezone.utc)


# Восстанавливает интервал строки из SQLite с учётом переноса в менеджере.
# При смене типа привязки использует стандартную длительность дня или недели.
def adjusted_interval(row, stored, start, end):
    target = date.fromisoformat(row['date'])
    if row['period'] != stored['original_period']:
        return target, target + timedelta(days=7 if row['period'] == 'week' else 1)
    offset = target - date.fromisoformat(stored['original_date'])
    if offset and isinstance(start, datetime):
        shifted_start = start.astimezone(MOSCOW) + offset
        shifted_end = instant(shifted_start) + (instant(end) - instant(start))
        return shifted_start, shifted_end
    return start + offset, end + offset


# Формирует обычные свойства времени VEVENT.
# Дату выводит без часового пояса, а точное время в UTC.
def time_lines(start, end):
    if isinstance(start, datetime):
        result = ['DTSTART:' + instant(start).strftime(UTC_FORMAT)]
        if end != start:
            result.append('DTEND:' + instant(end).strftime(UTC_FORMAT))
        return result
    return ['DTSTART;VALUE=DATE:' + start.strftime(DATE_FORMAT), 'DTEND;VALUE=DATE:' + end.strftime(DATE_FORMAT)]


# Генерирует VEVENT из актуальных полей менеджера и дополнительных полей клиента.
# Исходные времена и зона сохраняются до переноса записи в менеджере.
def event_resource(row, stored=None):
    start = date.fromisoformat(row['date'])
    end = start + timedelta(days=7 if row['period'] == 'week' else 1)
    lines, first, last, fields, name, uid = (
        ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:' + PRODID, 'BEGIN:VEVENT', 'END:VEVENT', 'END:VCALENDAR'],
        3, 4, {}, row['id'] + '.ics', row['id'])
    timing = time_lines(start, end)
    if stored:
        lines, first, last, fields, uid, _, original_start, original_end = parse(stored['icalendar'].encode())
        name = stored['name']
        start, end = adjusted_interval(row, stored, original_start, original_end)
        timing = (time_lines(start, end) if (start, end) != (original_start, original_end) else
                  [lines[index] for index in sorted(fields[key][0] for key in ('DTSTART', 'DTEND', 'DURATION') if key in fields)])
    replaced = {fields[key][0] for key in fields}
    stamp = datetime.fromtimestamp(row['updated'], timezone.utc).strftime(UTC_FORMAT)
    event = ['UID:' + escape(uid), 'DTSTAMP:' + stamp, 'LAST-MODIFIED:' + stamp,
             'SUMMARY:' + escape(row['text']), *timing]
    if row['comment']:
        event.append('DESCRIPTION:' + escape(row['comment']))
    content = lines[:first + 1] + event + [line for index, line in enumerate(lines[first + 1:last], first + 1) if index not in replaced] + lines[last:]
    return Resource(name, encode_lines(content), instant(start), instant(end), row['revision'])


# Проецирует сроки и текстовые события заказа в отдельный календарь.
# UID строится из UUID заказа, периода и даты, а ссылка открывает карточку.
def order_resources(orders, public_host):
    for order in orders:
        url = 'https://' + public_host + '/?' + urlencode({'path': order['path']})
        title = order['title'] or order['path']
        for period, field in [('day', 'calendar_events'), ('week', 'calendar_week_events')]:
            dates = dict(order[field] or {})
            if period == 'week':
                for key in order['deadline_weeks'] or []:
                    dates.setdefault(key, '')
            for key, comment in dates.items():
                start = date.fromisoformat(key)
                try:
                    end = start + timedelta(days=7 if period == 'week' else 1)
                except OverflowError:
                    continue
                uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f'zigzag/order/{order["id"]}/{period}/{key}'))
                stamp = datetime.fromtimestamp(order['updated'], timezone.utc).strftime(UTC_FORMAT)
                subject = ' · '.join(part for part in (order.get('work_supplier') or order.get('client'), title) if part)
                lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:' + PRODID, 'BEGIN:VEVENT',
                         'UID:' + uid, 'DTSTAMP:' + stamp, *time_lines(start, end), 'SUMMARY:' + escape(subject),
                         'URL:' + url, 'DESCRIPTION:' + escape(comment + '\n' + url if comment else url),
                         'END:VEVENT', 'END:VCALENDAR']
                yield Resource(uid + '.ics', encode_lines(lines), instant(start), instant(end))
