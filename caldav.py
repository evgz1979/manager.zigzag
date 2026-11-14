"""CalDAV transport for the manager's free events and read-only order schedule."""
import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as xml

import caldav_events
from orders import OrderConflict

ROOT = '/caldav/'
PRINCIPAL = ROOT + 'manager/'
HOME = PRINCIPAL + 'calendars/'
EVENTS = HOME + 'events/'
ORDERS = HOME + 'orders/'
WELL_KNOWN = '/.well-known/caldav'
SETTINGS = '/api/manager-settings/caldav'
USERNAME = 'zigzag'
CREDENTIAL = 'caldav_credential_v1'
DAV = '{DAV:}'
CAL = '{urn:ietf:params:xml:ns:caldav}'
APPLE = '{http://apple.com/ns/ical/}'
CS = '{http://calendarserver.org/ns/}'
COLLECTIONS = {ROOT: (PRINCIPAL,), PRINCIPAL: (HOME,), HOME: (EVENTS, ORDERS), EVENTS: (), ORDERS: ()}
LABELS = {ROOT: 'Зигзаг', PRINCIPAL: 'Зигзаг', HOME: 'Календари Зигзага',
          EVENTS: 'Зигзаг · События', ORDERS: 'Зигзаг · Заказы'}
NAME = re.compile(r'[A-Za-z0-9_@.+~-]{1,200}\.ics')
METHODS = 'OPTIONS, GET, HEAD, PROPFIND, REPORT, PUT, DELETE'
for prefix, namespace in [('D', DAV), ('C', CAL), ('A', APPLE), ('CS', CS)]:
    xml.register_namespace(prefix, namespace[1:-1])


# Передаёт HTTP-статус и необязательное условие CalDAV клиенту.
# Исключение прерывает операцию до фиксации изменений SQLite.
class DavError(ValueError):
    # Сохраняет статус и необязательный XML-тег precondition.
    # Параметр tag содержит полное имя элемента с пространством имён.
    def __init__(self, status, tag=None):
        super().__init__(status)
        self.status = status
        self.tag = tag


# Распознаёт только пространство CalDAV и необязательное обнаружение на корне.
# GET корня по-прежнему обслуживает браузерный вход менеджера.
def route_for(path, method):
    path = urlsplit(path).path
    if path == WELL_KNOWN:
        return WELL_KNOWN
    if path == '/' and method in {'PROPFIND', 'OPTIONS'}:
        return path
    if path == ROOT.rstrip('/') or path.startswith(ROOT):
        decoded = unquote(path, errors='strict')
        if any(segment in {'.', '..'} for segment in decoded.split('/')):
            raise ValueError('Некорректный путь CalDAV')
        return decoded + '/' if decoded + '/' in COLLECTIONS else decoded
    return None


# Читает ограниченное тело запроса с однозначной длиной.
# Тело без Content-Length допускается только для пустого PROPFIND.
def read_body(handler, *, optional=False, limit=256 * 1024):
    lengths = handler.headers.get_all('Content-Length', [])
    if handler.headers.get('Transfer-Encoding') is not None:
        raise DavError(400)
    if not lengths and optional:
        return b''
    if len(lengths) != 1 or not re.fullmatch(r'[0-9]{1,9}', lengths[0]):
        raise DavError(400)
    size = int(lengths[0])
    if size > limit:
        raise DavError(413)
    body = handler.rfile.read(size)
    if len(body) != size:
        raise DavError(400)
    return body


# Разбирает XML запроса без пользовательских сущностей и деклараций DTD.
# Пустой запрос свойств означает PROPFIND allprop.
def parse_xml(body):
    if not body:
        return None
    text = body.decode('utf-8-sig')
    if '<!' in text or '\x00' in text:
        raise DavError(400)
    return xml.fromstring(text)


# Вычисляет проверочное значение пароля, ограниченное текущим внешним профилем.
# Смена пароля менеджера отзывает и отдельный пароль календаря.
def credential_digest(gate, document, password):
    return hmac.new(gate.key(document), b'caldav:' + password, 'sha256').hexdigest()


# Проверяет отдельный Basic-пароль календаря с постоянным временем сравнения.
# Пароль хранится только в устройстве, SQLite содержит его проверочное значение.
def authorized(handler, events, gate, document):
    headers = handler.headers.get_all('Authorization', [])
    if len(headers) != 1 or len(headers[0]) > 256:
        return False
    scheme, _, encoded = headers[0].partition(' ')
    if scheme.lower() != 'basic':
        return False
    try:
        username, _, password = base64.b64decode(encoded, validate=True).partition(b':')
    except (ValueError, binascii.Error):
        return False
    if username != USERNAME.encode() or not re.fullmatch(rb'[A-Za-z0-9_-]{43}', password):
        return False
    with events.store.connect() as db:
        stored = db.execute('SELECT value FROM metadata_settings WHERE key=?', (CREDENTIAL,)).fetchone()
    return bool(stored) and hmac.compare_digest(stored[0], credential_digest(gate, document, password))


# Создаёт или отзывает пароль CalDAV из штатного окна настроек.
# Любое новое значение немедленно заменяет старое и возвращается в браузер один раз.
def manage_credentials(handler, store, gate, document):
    if handler.headers.get_all('X-Manager-Settings', []) != ['1'] or handler.headers.get_content_type() != 'application/json':
        raise DavError(403)
    payload = json.loads(read_body(handler, limit=4096))
    if not isinstance(payload, dict) or payload.get('action') not in ('generate', 'revoke'):
        raise DavError(400)
    token = payload.get('csrf')
    if not isinstance(token, str) or not gate.valid(document, token, 'settings'):
        raise DavError(403)
    result = {'server': gate.public_host, 'path': ROOT, 'username': USERNAME}
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if payload['action'] == 'generate':
            password = secrets.token_urlsafe(32)
            check = credential_digest(gate, document, password.encode())
            db.execute('INSERT OR REPLACE INTO metadata_settings(key,value) VALUES (?,?)', (CREDENTIAL, check))
            result['password'] = password
        else:
            db.execute('DELETE FROM metadata_settings WHERE key=?', (CREDENTIAL,))
    return result


# Возвращает свободные события и их CalDAV-свойства из одного снимка SQLite.
# Неизвестные форматы не публикуются и остаются в рабочей базе.
def event_resources(events):
    with events.connect() as db:
        caldav_events.schema(db)
        db.execute('BEGIN')
        indexed = db.execute('SELECT * FROM calendar_dav_objects').fetchall()
        rows = db.execute('SELECT * FROM calendar_events WHERE deleted=0').fetchall()
    indexed = {item['event_id']: item for item in indexed}
    resources = {}
    for row in rows:
        try:
            events.validate(row)
            resource = caldav_events.event_resource(row, indexed.get(row['id']))
        except (ValueError, OverflowError):
            continue
        resources[resource.name] = resource
    return resources


# Преобразует путь в пару календарь и имя ресурса.
# Имя не используется как имя файла на диске.
def split_resource(path):
    collection, _, name = path.rpartition('/')
    collection += '/'
    if collection not in {EVENTS, ORDERS} or not NAME.fullmatch(name) or name.startswith('.'):
        raise DavError(404)
    return collection, name


# Строит XML-значение DAV-привилегии для конкретного ресурса.
# Календарь заказов никогда не получает прав создания и удаления.
def privileges(writable):
    names = [DAV + 'read', CAL + 'read-free-busy']
    if writable:
        names += [DAV + key for key in ('write', 'write-content', 'bind', 'unbind')]
    result = []
    for name in names:
        node = xml.Element(DAV + 'privilege')
        xml.SubElement(node, name)
        result.append(node)
    return result


# Собирает доступные свойства коллекции или отдельного VEVENT.
# ctag меняется при создании, переносе, правке или исчезновении любого ресурса.
def properties(path, item, resources, requested):
    if item:
        return {DAV + 'resourcetype': (), DAV + 'getcontenttype': 'text/calendar; charset=utf-8',
                DAV + 'getcontentlength': str(len(item.body)), DAV + 'getetag': item.etag,
                DAV + 'current-user-privilege-set': privileges(path.startswith(EVENTS)),
                CAL + 'calendar-data': item.body.decode() if CAL + 'calendar-data' in requested else ''}
    principal = xml.Element(DAV + 'href')
    principal.text = PRINCIPAL
    home = xml.Element(DAV + 'href')
    home.text = HOME
    address = xml.Element(DAV + 'href')
    address.text = 'urn:uuid:77ee236e-080c-45fe-8628-233a71940c43'
    types = [xml.Element(DAV + 'collection')]
    if path == PRINCIPAL:
        types.append(xml.Element(DAV + 'principal'))
    if path in {EVENTS, ORDERS}:
        types.append(xml.Element(CAL + 'calendar'))
    values = {DAV + 'resourcetype': types, DAV + 'displayname': LABELS[path],
              DAV + 'current-user-principal': [principal], DAV + 'principal-URL': [principal],
              DAV + 'owner': [principal], DAV + 'current-user-privilege-set': privileges(path == EVENTS),
              CAL + 'calendar-home-set': [home], CAL + 'calendar-user-address-set': [address],
              CAL + 'calendar-user-type': 'INDIVIDUAL'}
    if path in {EVENTS, ORDERS}:
        reports = []
        for name in ('calendar-query', 'calendar-multiget'):
            supported = xml.Element(DAV + 'supported-report')
            xml.SubElement(xml.SubElement(supported, DAV + 'report'), CAL + name)
            reports.append(supported)
        values.update({DAV + 'supported-report-set': reports,
                       CAL + 'supported-calendar-component-set': [xml.Element(CAL + 'comp', name='VEVENT')],
                       CAL + 'supported-calendar-data': [xml.Element(CAL + 'calendar-data', {'content-type': 'text/calendar', 'version': '2.0'})],
                       APPLE + 'calendar-color': '#208358FF' if path == EVENTS else '#5368A0FF',
                       CAL + 'calendar-description': LABELS[path]})
        if CS + 'getctag' in requested:
            values[CS + 'getctag'] = hashlib.sha256(
                '\n'.join(name + item.etag for name, item in sorted(resources.items())).encode()).hexdigest()
    return values


# Добавляет один ответ в DAV multistatus.
# Недоступные свойства имеют отдельный propstat со статусом 404.
def add_response(root, path, values, requested, *, propname=False):
    response = xml.SubElement(root, DAV + 'response')
    xml.SubElement(response, DAV + 'href').text = path
    if values is None:
        xml.SubElement(response, DAV + 'status').text = 'HTTP/1.1 404 Not Found'
        return
    accepted = values.keys() if requested is None else (key for key in requested if key in values)
    for status, keys in [('200 OK', list(accepted)), ('404 Not Found', [] if requested is None else [key for key in requested if key not in values])]:
        if not keys:
            continue
        propstat = xml.SubElement(response, DAV + 'propstat')
        prop = xml.SubElement(propstat, DAV + 'prop')
        for key in keys:
            element = xml.SubElement(prop, key)
            if propname or key not in values:
                continue
            value = values[key]
            if isinstance(value, str):
                element.text = value
            else:
                element.extend(value)
        xml.SubElement(propstat, DAV + 'status').text = 'HTTP/1.1 ' + status


# Сериализует результат PROPFIND или REPORT в протокольный XML.
# Экранирует имена, свойства и полное содержимое VEVENT стандартной библиотекой.
def multistatus(handler, root):
    handler.reply(207, xml.tostring(root, encoding='utf-8', xml_declaration=True), 'application/xml; charset=utf-8')


# Проверяет точный ETag операции записи.
# Для удаления и замены требуется совпадение версии, для создания допускается If-None-Match.
def precondition(handler, resource, *, deleting=False):
    match = handler.headers.get('If-Match')
    none = handler.headers.get('If-None-Match')
    if resource is None:
        if match or deleting:
            raise DavError(412 if match else 404)
        return
    if none == '*' or (match and resource.etag not in (tag.strip() for tag in match.split(','))):
        raise DavError(412)
    if not match:
        raise DavError(428)


# Создаёт или заменяет одно свободное событие со свойствами CalDAV.
# Имя, UID, ревизия и даты проверяются в транзакции рабочей базы.
def put(handler, events, name):
    if handler.headers.get_content_type() != 'text/calendar':
        raise DavError(415)
    body = read_body(handler)
    try:
        _, _, _, fields, uid, text, start, end = caldav_events.parse(body)
        day, period = caldav_events.placement(start, end)
        comment = caldav_events.unescape(fields['DESCRIPTION'][2]) if 'DESCRIPTION' in fields else ''
    except (ValueError, OverflowError) as exc:
        raise DavError(403, CAL + 'valid-calendar-object-resource') from exc
    with events.connect() as db:
        caldav_events.schema(db)
        db.execute('BEGIN IMMEDIATE')
        stored = db.execute('SELECT * FROM calendar_dav_objects WHERE name=?', (name,)).fetchone()
        stem = name[:-4]
        try:
            native_id = stem if str(uuid.UUID(stem)) == stem else None
        except ValueError:
            native_id = None
        identity = stored['event_id'] if stored else native_id
        row = db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone()
        if row and not stored and db.execute('SELECT 1 FROM calendar_dav_objects WHERE event_id=?', (identity,)).fetchone():
            raise DavError(409)
        if row and row['deleted']:
            raise DavError(412)
        before = caldav_events.event_resource(row, stored) if row else None
        precondition(handler, before)
        if row and uid != (stored['uid'] if stored else row['id']):
            raise DavError(403, CAL + 'no-uid-conflict')
        if not row and ((db.execute('SELECT 1 FROM calendar_dav_objects WHERE uid=?', (uid,)).fetchone()) or
                        db.execute('SELECT 1 FROM calendar_events WHERE id=?', (uid,)).fetchone()):
            raise DavError(403, CAL + 'no-uid-conflict')
        identity = identity or str(uuid.uuid4())
        events.save_in_transaction(db, {'id': identity, 'revision': row['revision'] if row else 0,
                                        'period': period, 'date': day, 'text': text, 'comment': comment}, reschedule=True)
        db.execute("""INSERT INTO calendar_dav_objects VALUES (?,?,?,?,?,?)
            ON CONFLICT(event_id) DO UPDATE SET original_date=excluded.original_date,
            original_period=excluded.original_period, icalendar=excluded.icalendar""",
                   (identity, name, uid, day, period, body.decode('utf-8-sig')))
    # The stored representation is normalized. The client fetches its new ETag.
    handler.reply(204 if before else 201)


# Удаляет одно свободное событие через прежнюю корзину и проверку версии.
# Чтение ETag и чтение revision берутся из одной записи.
def delete(handler, events, name):
    with events.connect() as db:
        caldav_events.schema(db)
        stored = db.execute('SELECT * FROM calendar_dav_objects WHERE name=?', (name,)).fetchone()
        identity = stored['event_id'] if stored else name[:-4]
        row = db.execute('SELECT * FROM calendar_events WHERE id=? AND deleted=0', (identity,)).fetchone()
        if row and not stored and db.execute('SELECT 1 FROM calendar_dav_objects WHERE event_id=?', (identity,)).fetchone():
            row = None
    precondition(handler, caldav_events.event_resource(row, stored) if row else None, deleting=True)
    events.set_deleted({'id': identity, 'revision': row['revision']}, True)
    handler.reply(204)


# Маршрутизирует свойства и отчёты для аутентифицированного аккаунта.
# Запрашивает SQLite только для нужного календаря и ограничивает запрос глубиной 0 или 1.
class CalendarDAV:
    # Передаёт рабочие события, источник заказов и защищённый внешний адрес.
    # Функция read_orders читает только зарегистрированные доступные заказы.
    def __init__(self, events, read_orders, public_host):
        self.events = events
        self.read_orders = read_orders
        self.public_host = public_host

    # Генерирует представления ресурсов одного календаря для текущего запроса.
    # Сопоставляет каждое имя с телом VEVENT и временем.
    def resources(self, collection):
        if collection == EVENTS:
            return event_resources(self.events)
        return {item.name: item for item in caldav_events.order_resources(self.read_orders(), self.public_host)}

    # Выдаёт свойства коллекций и их непосредственных членов.
    # При глубине 1 читает только ресурсы календаря или ctag запрошенных календарей.
    def propfind(self, handler, path):
        request = parse_xml(read_body(handler, optional=True))
        if request is not None and request.tag != DAV + 'propfind':
            raise DavError(400)
        prop = request.find(DAV + 'prop') if request is not None else None
        names = list(dict.fromkeys(child.tag for child in prop)) if prop is not None else None
        propname = request is not None and request.find(DAV + 'propname') is not None
        depth = handler.headers.get('Depth', '0')
        if depth not in ('0', '1'):
            raise DavError(403, DAV + 'propfind-finite-depth')
        result = xml.Element(DAV + 'multistatus')
        if path == '/':
            add_response(result, path, properties(ROOT, None, {}, names or ()), names, propname=propname)
            if depth == '1':
                add_response(result, ROOT, properties(ROOT, None, {}, names or ()), names, propname=propname)
            multistatus(handler, result)
            return
        if path not in COLLECTIONS:
            collection, name = split_resource(path)
            item = self.resources(collection).get(name)
            if item is None:
                raise DavError(404)
            add_response(result, path, properties(path, item, {}, names or ()), names, propname=propname)
        else:
            paths = [path, *COLLECTIONS[path]] if depth == '1' else [path]
            for child in paths:
                list_members = child == path and depth == '1' and child in {EVENTS, ORDERS}
                requested = names if names is not None else [CS + 'getctag']
                items = self.resources(child) if child in {EVENTS, ORDERS} and (list_members or CS + 'getctag' in requested) else {}
                add_response(result, child, properties(child, None, items, requested), names, propname=propname)
                if list_members:
                    for name, item in sorted(items.items()):
                        href = child + name
                        add_response(result, href, properties(href, item, {}, requested), names, propname=propname)
        multistatus(handler, result)

    # Обслуживает calendar-query и calendar-multiget для коллекции.
    # Применяет фильтр интервала VEVENT и возвращает 404 для исчезнувших ресурсов.
    def report(self, handler, path):
        if path not in {EVENTS, ORDERS}:
            raise DavError(403, DAV + 'supported-report')
        request = parse_xml(read_body(handler))
        if request is None or request.tag not in {CAL + 'calendar-query', CAL + 'calendar-multiget'}:
            raise DavError(403, DAV + 'supported-report')
        prop = request.find(DAV + 'prop')
        names = list(dict.fromkeys(child.tag for child in prop)) if prop is not None else [DAV + 'getetag', CAL + 'calendar-data']
        items = self.resources(path)
        result = xml.Element(DAV + 'multistatus')
        if request.tag == CAL + 'calendar-multiget':
            for element in request.findall(DAV + 'href'):
                href = route_for(element.text or '', 'REPORT')
                if not href or not href.startswith(path):
                    raise DavError(403)
                _, name = split_resource(href)
                if href != path + name:
                    raise DavError(403)
                item = items.get(name)
                add_response(result, href, properties(href, item, {}, names) if item else None, names)
        else:
            filters = request.findall('./' + CAL + 'filter/' + CAL + 'comp-filter')
            if len(filters) != 1 or filters[0].get('name') != 'VCALENDAR':
                raise DavError(403, CAL + 'supported-filter')
            event_filter = filters[0].find(CAL + 'comp-filter')
            if len(filters[0]) != (1 if event_filter is not None else 0):
                raise DavError(403, CAL + 'supported-filter')
            if event_filter is not None and (event_filter.get('name') != 'VEVENT' or
                                            any(child.tag != CAL + 'time-range' for child in event_filter)):
                raise DavError(403, CAL + 'supported-filter')
            interval = event_filter.find(CAL + 'time-range') if event_filter is not None else None
            lower = datetime.min.replace(tzinfo=timezone.utc)
            upper = datetime.max.replace(tzinfo=timezone.utc)
            if interval is not None:
                if interval.get('start'):
                    lower = datetime.strptime(interval.get('start'), caldav_events.UTC_FORMAT).replace(tzinfo=timezone.utc)
                if interval.get('end'):
                    upper = datetime.strptime(interval.get('end'), caldav_events.UTC_FORMAT).replace(tzinfo=timezone.utc)
                if lower >= upper:
                    raise DavError(400)
            for name, item in sorted(items.items()):
                if item.start < upper and max(item.end, item.start + timedelta(microseconds=1)) > lower:
                    href = path + name
                    add_response(result, href, properties(href, item, {}, names), names)
        multistatus(handler, result)

    # Обрабатывает разрешённые методы CalDAV и нормализует протокольные ошибки.
    # Записи блокируются при переключении рабочего сервера.
    def serve(self, handler, path, writes_allowed):
        try:
            method = handler.command
            if method == 'OPTIONS':
                handler.reply(200, headers=[('DAV', '1, calendar-access'), ('Allow', METHODS)])
            elif method == 'PROPFIND':
                self.propfind(handler, path)
            elif method == 'REPORT':
                self.report(handler, path)
            elif method in {'GET', 'HEAD'}:
                collection, name = split_resource(path)
                item = self.resources(collection).get(name)
                if not item:
                    raise DavError(404)
                if handler.headers.get('If-None-Match') == item.etag:
                    handler.reply(304, headers=[('ETag', item.etag)])
                else:
                    handler.reply(200, item.body, 'text/calendar; charset=utf-8', [('ETag', item.etag)])
            elif method in {'PUT', 'DELETE'}:
                collection, name = split_resource(path)
                if collection != EVENTS:
                    raise DavError(403)
                if not writes_allowed():
                    raise DavError(503)
                if method == 'PUT':
                    put(handler, self.events, name)
                else:
                    delete(handler, self.events, name)
            else:
                handler.reply(405, headers=[('Allow', METHODS)])
        except DavError as error:
            send_error(handler, error)
        except OrderConflict:
            handler.reply(412)
        except (ValueError, OverflowError, xml.ParseError):
            handler.reply(400)
        except (sqlite3.Error, TimeoutError):
            handler.reply(503)
        except (BrokenPipeError, ConnectionResetError):
            pass


# Передаёт ошибку CalDAV, включая именованное предусловие RFC.
# Тело лишено внутренних данных и содержит только безопасный XML.
def send_error(handler, error):
    if error.tag:
        root = xml.Element(DAV + 'error')
        xml.SubElement(root, error.tag)
        handler.reply(error.status, xml.tostring(root, encoding='utf-8', xml_declaration=True), 'application/xml; charset=utf-8')
    else:
        handler.reply(error.status)
