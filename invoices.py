"""Invoice drafts, immutable issued PDFs and a durable folder-copy outbox."""
from contextlib import contextmanager
import base64
import binascii
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time
import uuid
import unicodedata
from zoneinfo import ZoneInfo

from event_folder_undo import assert_unlocked
from folder_layout import rename_exclusive
import native_renderers
import orders
import file_comments
import file_trash
import local_metadata

BUILD_LOCK = threading.Lock()
SYNC_LOCK = threading.Lock()
MAX_EXTERNAL_BYTES = 20 * 1024 * 1024
INVOICE_TRASH_VERSION = 1
INVOICE_PLAN_VERSION = 1
INVOICE_PAYMENT_SOURCE_VERSION = 1
INVOICE_WEEK_PLAN_VERSION = 1
LIST_STATUSES = {"none": "Без отметки", "active": "Актуально", "inactive": "Неактуально", "later": "Позже", "sent": "Отправлен"}
EXTERNAL_REQUEST_LIMIT = ((MAX_EXTERNAL_BYTES + 2) // 3) * 4 + 64 * 1024
DEFAULT_SELLER = {
    "name": "ИП ЗАЙЦЕВ ЕВГЕНИЙ КОНСТАНТИНОВИЧ", "inn": "280404583555", "kpp": "",
    "address": "141703, Россия, Московская обл., г. Долгопрудный, ул. Набережная, д. 29, корп. 1, кв. 181",
    "bank": "АО «ТБанк»", "bik": "044525974", "account": "40802810900001017661",
    "correspondent": "30101810145250000974", "signer": "Зайцев Е.К.",
}
DEFAULT_TERMS = (
    "Исполнитель обязуется выполнить работы (поставить товары), указанные в таблице, "
    "а Заказчик - принять результат и оплатить указанную стоимость. "
    "Оплата производится до указанной в счёте даты. Оплата счёта в этот срок означает принятие условий договора.\n"
    "Результат передаётся по акту или накладной. Изменения объёма, стоимости и сроков стороны согласуют письменно. "
    "В остальном стороны руководствуются законодательством РФ."
)
FIELDS = {"kind": 20, "number": 40, "date": 10, "due_date": 10, "buyer_name": 300,
          "buyer_inn": 12, "buyer_kpp": 9, "buyer_address": 500, "note": 1000,
          "work_start": 10, "work_end": 10, "terms": 2500}


class InvoiceConflict(ValueError):
    pass


def external_comment(value):
    if not isinstance(value, str) or len(value) > 5000 or any(ord(c) < 32 and c not in '\n\r\t' for c in value):
        raise ValueError("Комментарий к счёту: до 5000 символов")
    return value


def today():
    return datetime.now(ZoneInfo("Europe/Moscow")).date()


def plan_date(value):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except ValueError:
        raise ValueError('Выбери день выписки счёта') from None
    return value


def plan_period(value, scheduled):
    if value not in ('day', 'week'):
        raise ValueError('Выбери день или неделю планирования')
    if value == 'week' and date.fromisoformat(scheduled).weekday() != 0:
        raise ValueError('Для недельного плана укажи дату понедельника')
    return value


def known_plan(data):
    if type(data.get('version')) is not int or data['version'] != 1 or data.get('kind') != 'planned':
        return False
    try:
        scheduled = plan_date(data.get('date'))
        plan_period(data.get('period', 'day'), scheduled)
        if data.get('scope', 'order') not in ('order', 'calendar') or not isinstance(data.get('text', ''), str):
            return False
        operation = data.get('operation', 'invoice')
        return isinstance(operation, str) and (operation == 'invoice' or (operation in {'incoming', 'outgoing'} and
            type(data.get('amount')) is int and 0 < data['amount'] <= 99999999999))
    except ValueError:
        return False


def total_from_text(text):
    """Only accept an unambiguous labelled total, never an arbitrary PDF number."""
    text = text.replace('\u00a0', ' ').replace('\u202f', ' ')
    money = r'(?<![\d.,])((?:\d{1,3}(?:[ .]\d{3})+|\d+)[,.]\d{2})(?!\d)'
    labels = [r'(?:итого|всего|сумма)\s+к\s+оплате', r'всего\s+(?:на\s+сумму|с\s+ндс)', r'итого', r'всего']
    for label in labels:
        candidates = set()
        for match in re.finditer(r'(?im)^\s*' + label + r'\s*[:=]?\s*', text):
            tail = text[match.end():].split('\n', 1)[0]
            if not tail.strip():
                tail = text[match.end():].lstrip('\n').split('\n', 1)[0]
            values = list(re.finditer(money, tail))
            if len(values) != 1 or re.search(r'[$€]|\b(?:USD|EUR|CNY)\b', tail, re.I):
                continue
            if tail[:values[0].start()].rstrip().endswith(('-', '−')):
                continue
            value = values[0].group(1).replace(' ', '')
            if ',' in value:
                value = value.replace('.', '').replace(',', '.')
            try:
                cents = int(Decimal(value) * 100)
                if 0 < cents <= 99999999999:
                    candidates.add(cents)
            except InvalidOperation:
                pass
        if candidates:
            return candidates.pop() if len(candidates) == 1 else None
    return None


def pdf_total(body, app_dir, data_dir):
    cache = Path(data_dir) / 'invoice-amounts'
    cache.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(body).hexdigest()
    cached = cache / (digest + '.txt')
    if cached.is_file():
        return total_from_text(cached.read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='.amount-', dir=cache) as work:
        source = Path(work) / 'invoice.pdf'
        source.write_bytes(body)
        binary = native_renderers.build(Path(app_dir) / 'pdf_preview.swift', data_dir, 'pdf-renderer', 90)
        result = subprocess.run([str(binary), str(source), 'invoice-text'], capture_output=True, check=True, timeout=30)
        text = result.stdout[:2000000].decode('utf-8', errors='replace')
        temporary = Path(work) / 'text.txt'
        temporary.write_text(text, encoding='utf-8')
        temporary.replace(cached)
        return total_from_text(text)


def decimal(value, label, places, maximum):
    if not isinstance(value, str) or len(value) > 30:
        raise ValueError("Проверь поле «" + label + "»")
    try:
        number = Decimal(value.replace(" ", "").replace("\u00a0", "").replace(",", "."))
        if not number.is_finite() or number < 0 or number > maximum or number != number.quantize(Decimal(1).scaleb(-places)):
            raise ValueError()
        return number
    except (InvalidOperation, ValueError):
        raise ValueError("Проверь поле «" + label + "»: допустимо до " + str(places) + " знаков после запятой") from None


def validate(value, *, issuing=False):
    if not isinstance(value, dict):
        raise ValueError("Некорректные данные счёта")
    result = {}
    for field, limit in FIELDS.items():
        text = value.get(field, "")
        if not isinstance(text, str) or len(text) > limit or any(ord(c) < 32 and c not in "\n\t" for c in text):
            raise ValueError("Слишком длинное или некорректное поле: " + field)
        if field not in {"terms", "note"} and ("\n" in text or "\t" in text):
            raise ValueError("Поле должно быть в одну строку: " + field)
        result[field] = text.strip()
    if result["kind"] not in {"invoice", "contract"}:
        raise ValueError("Выбери счёт или счёт-договор")
    if not re.fullmatch(r"[0-9А-Яа-яЁёA-Za-z._/-]{1,40}", result["number"]):
        raise ValueError("Номер: до 40 букв, цифр, точек, /, - и _")
    for field in ("date", "due_date", "work_start", "work_end"):
        if result[field]:
            try:
                if date.fromisoformat(result[field]).isoformat() != result[field]:
                    raise ValueError()
            except ValueError:
                raise ValueError("Проверь дату: " + field) from None
    if not result["date"]:
        raise ValueError("Укажи дату счёта")
    if result["due_date"] and result["due_date"] < result["date"]:
        raise ValueError("Срок оплаты раньше даты счёта")
    seller = value.get("seller")
    if not isinstance(seller, dict):
        raise ValueError("Укажи реквизиты исполнителя")
    result["seller"] = {}
    for field in DEFAULT_SELLER:
        text = seller.get(field, "")
        if not isinstance(text, str) or len(text) > (500 if field == "address" else 300) or any(ord(c) < 32 for c in text):
            raise ValueError("Проверь реквизиты исполнителя: " + field)
        result["seller"][field] = text.strip()
    for obj, field, lengths in ((result, "buyer_inn", (10, 12)), (result, "buyer_kpp", (9,)),
                                (result["seller"], "inn", (10, 12)), (result["seller"], "kpp", (9,)),
                                (result["seller"], "bik", (9,)), (result["seller"], "account", (20,)),
                                (result["seller"], "correspondent", (20,))):
        text = obj[field]
        if text and (not text.isascii() or not text.isdigit() or len(text) not in lengths):
            raise ValueError("Проверь реквизит: " + field)
    items = value.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 40:
        raise ValueError("В счёте должно быть от 1 до 40 позиций")
    result["items"], total = [], 0
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Некорректная позиция счёта")
        name, unit = item.get("name"), item.get("unit")
        if not isinstance(name, str) or len(name) > 500 or any(ord(c) < 32 for c in name):
            raise ValueError("Наименование позиции: одна строка до 500 символов")
        if not isinstance(unit, str) or len(unit) > 16 or any(ord(c) < 32 for c in unit):
            raise ValueError("Единица измерения: до 16 символов")
        qty = decimal(item.get("quantity"), "Количество", 3, Decimal("1000000"))
        price = decimal(item.get("price"), "Цена", 2, Decimal("999999999.99"))
        if issuing and (not name.strip() or qty <= 0):
            raise ValueError("Заполни наименования и положительное количество всех позиций")
        amount = int((qty * price * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        total += amount
        result["items"].append({"name": name.strip(), "unit": unit.strip(), "quantity": str(qty),
                                "price": str(price), "amount": amount})
    if total > 99999999999:
        raise ValueError("Сумма счёта превышает 999 999 999,99 ₽")
    result["total"] = total
    if issuing:
        if not result["buyer_name"] or not result["seller"]["name"] or not total:
            raise ValueError("Укажи покупателя, исполнителя и ненулевую сумму")
        if any(not result["seller"][key] for key in ("inn", "bank", "bik", "account", "correspondent", "signer")):
            raise ValueError("Заполни ИНН, банковские реквизиты и подписанта исполнителя")
        if result["kind"] == "contract":
            if not all(result[key] for key in ("due_date", "work_start", "work_end", "terms")):
                raise ValueError("Для счёта-договора укажи срок оплаты, начало и окончание работ и условия")
            if result["work_end"] < result["work_start"] or result["work_start"] < result["date"]:
                raise ValueError("Проверь начало и окончание работ")
    return result


def renderer(app_dir, data_dir):
    with BUILD_LOCK:
        return native_renderers.build(Path(app_dir) / "invoice_pdf.swift", data_dir, "invoice-pdf", 90)


def render(data, app_dir, data_dir):
    cache = Path(data_dir) / "invoices"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".invoice-", dir=cache) as work:
        source, output = Path(work) / "input.json", Path(work) / "invoice.pdf"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        try:
            subprocess.run([str(renderer(app_dir, data_dir)), str(source), str(output)], check=True,
                           capture_output=True, timeout=30)
        except subprocess.CalledProcessError as error:
            raise ValueError(error.stderr.decode("utf-8", errors="replace").strip() or "Не удалось создать PDF") from error
        except subprocess.TimeoutExpired as error:
            raise ValueError("Формирование PDF заняло слишком много времени. Черновик сохранён") from error
        body = output.read_bytes()
        if not body.startswith(b"%PDF-") or len(body) > 10 * 1024 * 1024:
            raise ValueError("Не удалось проверить PDF")
        return body


class InvoiceStore:
    def __init__(self, store, app_dir):
        self.store, self.app_dir = store, Path(app_dir)

    @contextmanager
    def connect(self):
        with self.store.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY, path TEXT NOT NULL, year INTEGER NOT NULL, number TEXT NOT NULL,
                revision INTEGER NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, pdf BLOB,
                filename TEXT NOT NULL DEFAULT '', exported INTEGER NOT NULL DEFAULT 0,
                sync_error TEXT NOT NULL DEFAULT '', created REAL NOT NULL, updated REAL NOT NULL,
                UNIQUE(year,number))""")
            db.execute("CREATE TABLE IF NOT EXISTS invoice_sequences (year INTEGER PRIMARY KEY, value INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS invoice_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS invoice_history (id TEXT, revision INTEGER, data TEXT NOT NULL, saved REAL NOT NULL, PRIMARY KEY(id,revision))")
            yield db

    def owner(self, db, path, *, active=False):
        path = self.store.path(path)
        assert_unlocked(db, path)
        row = db.execute("SELECT * FROM orders WHERE path=?", (path,)).fetchone()
        if not row or (active and not row["registered"]):
            raise ValueError("Сначала добавь заказ в список заказов")
        return row

    @staticmethod
    def record(row):
        result = {key: row[key] for key in row.keys() if key != "pdf"}
        result["data"] = json.loads(result["data"])
        result['trash'] = result['data'].get('_trash')
        value = result['data'].get('_list_status', 'none')
        result['list_status'] = value if isinstance(value, str) and value in LIST_STATUSES else None
        result['plan_editable'] = result['state'] == 'planned' and known_plan(result['data'])
        result["sync_pending"] = not result['trash'] and result["state"] in {"issued", "external"} and not result["exported"]
        result["pdf_path"] = str(Path(result["path"]) / "# bills" / result["filename"]) if result["filename"] else None
        return result

    def current(self, db, path, identity, *, trashed=False):
        path = '' if path == '' else self.store.path(path)
        if path:
            assert_unlocked(db, path)
        if not isinstance(identity, str):
            raise ValueError("Не указан идентификатор счёта")
        row = db.execute("SELECT * FROM invoices WHERE id=? AND path=?", (identity, path)).fetchone()
        if not row:
            raise InvoiceConflict("Счёт не найден по этому пути. Открой заказ заново")
        if path:
            self.owner(db, path)
        elif row['state'] != 'planned' or json.loads(row['data']).get('scope') != 'calendar':
            raise InvoiceConflict('План не найден в календаре')
        if not trashed and json.loads(row['data']).get('_trash'):
            raise InvoiceConflict('Счёт в корзине. Обнови список или восстанови его')
        return row

    def list(self, path, *, trashed=False):
        with self.connect() as db:
            self.owner(db, path)
            # Do not load PDF blobs when listing invoices.
            condition = 'IS NOT NULL' if trashed else 'IS NULL'
            rows = db.execute("SELECT id,path,year,number,revision,state,data,filename,exported,sync_error,created,updated FROM invoices WHERE path=? AND json_extract(data,'$._trash') " + condition + ' ORDER BY created DESC,id', (path,))
            return [self.record(row) for row in rows]

    def get(self, path, identity):
        with self.connect() as db:
            return self.record(self.current(db, path, identity))

    @staticmethod
    def source_label(row):
        data = json.loads(row['data'])
        return data.get('original_name', 'Внешний счёт') if row['state'] == 'external' else ('Счёт-договор' if data.get('kind') == 'contract' else 'Счёт') + ' № ' + row['number']

    def plan_source(self, path, identity):
        with self.connect() as db:
            row = self.current(db, path, identity)
            self.owner(db, path, active=True)
            if row['state'] not in {'issued', 'external'}:
                raise ValueError('Запланировать оплату можно по готовому счёту')
            data = json.loads(row['data'])
            total = data.get('total') if row['state'] == 'issued' else None
            result = {'id': row['id'], 'revision': row['revision'], 'label': self.source_label(row), 'total': total, 'hint': ''}
            body = row['pdf']
        if row['state'] == 'external':
            try:
                result['total'] = pdf_total(body, self.app_dir, self.store.database.parent)
            except (OSError, ValueError, subprocess.SubprocessError):
                result['total'] = None
            if result['total'] is None:
                result['hint'] = 'Не удалось однозначно прочитать итог PDF. Укажи сумму вручную.'
        return result

    def calendar_plans(self, visible_orders):
        owners = {order['path']: order for order in visible_orders if order.get('registered') is not False}
        with self.connect() as db:
            rows = db.execute("SELECT id,path,data,revision FROM invoices WHERE state='planned' AND json_extract(data,'$._trash') IS NULL ORDER BY created,id")
            result = []
            for row in rows:
                owner, data = owners.get(row['path']), json.loads(row['data'])
                free = row['path'] == '' and data.get('scope') == 'calendar'
                if (owner is not None or free) and known_plan(data):
                    result.append({'id': row['id'], 'path': row['path'], 'date': data['date'], 'period': data.get('period', 'day'),
                                   'revision': row['revision'], 'is_inactive': data.get('_calendar_inactive', False),
                                   'operation': data.get('operation', 'invoice'), 'amount': data.get('amount'),
                                   'text': data.get('text', ''), 'invoice_label': data.get('invoice_label', ''),
                                   'title': owner['title'] if owner else 'Без заказа', 'client': owner['client'] if owner else '', 'object': owner['object'] if owner else ''})
            return result

    def save_plan_calendar_inactive(self, payload):
        import order_calendar
        inactive = payload.get('is_inactive')
        if type(inactive) is not bool:
            raise ValueError('Укажи состояние актуальности события')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self.current(db, payload.get('path'), payload.get('id'))
            if row['path']:
                self.owner(db, row['path'], active=True)
            if row['state'] != 'planned' or type(payload.get('revision')) is not int or row['revision'] != payload['revision']:
                raise InvoiceConflict('План изменился в другом окне. Обнови календарь и повтори отметку')
            data = json.loads(row['data'])
            if not known_plan(data) or type(data.get('_calendar_inactive', False)) is not bool:
                raise ValueError('Неизвестный формат актуальности плана сохранён без изменений')
            db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (row['id'], row['revision'], row['data'], time.time()))
            data['_calendar_inactive'] = inactive
            db.execute('UPDATE invoices SET data=?,revision=revision+1,updated=? WHERE id=?',
                       (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
            order_calendar.mark_relevance_contract(db)
            return self.record(self.current(db, row['path'], row['id']))

    def plan(self, payload):
        path, identity = ('' if payload.get('path') == '' else self.store.path(payload.get('path'))), payload.get('id')
        scheduled = plan_date(payload.get('date'))
        period = plan_period(payload.get('period', 'day'), scheduled)
        operation = payload.get('operation', 'invoice')
        if not isinstance(operation, str) or operation not in {'invoice', 'incoming', 'outgoing'}:
            raise ValueError('Выбери выписку счёта, получение оплаты или платёж')
        if not path and operation == 'invoice':
            raise ValueError('Для выписки счёта выбери заказ')
        text = payload.get('text', '')
        if not isinstance(text, str) or len(text) > 500 or any(ord(c) < 32 for c in text):
            raise ValueError('Комментарий плана: одна строка до 500 символов')
        amount = None
        if operation != 'invoice':
            amount = int(decimal(payload.get('amount'), 'Сумма', 2, Decimal('999999999.99')) * 100)
            if amount <= 0:
                raise ValueError('Сумма запланированной оплаты должна быть больше нуля')
        try:
            if str(uuid.UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Не указан идентификатор плана выписки счёта') from None
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if path:
                self.owner(db, path, active=True)
            row = db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone()
            if row:
                data = json.loads(row['data'])
                if row['path'] != path or row['state'] != 'planned' or data.get('_trash') or (not path and data.get('scope') != 'calendar'):
                    raise InvoiceConflict('План больше недоступен по этому пути. Обнови список счетов')
                if not known_plan(data):
                    raise InvoiceConflict('Неизвестный формат плана сохранён без изменений')
                if 'text' not in payload:
                    text = data.get('text', '')
                if 'revision' not in payload:
                    # Lost create responses never overwrite a later date edit.
                    return self.record(row)
                if type(payload['revision']) is not int or row['revision'] != payload['revision']:
                    raise InvoiceConflict('План изменился в другом окне. Проверь изменения перед повтором')
                if 'period' not in payload:
                    period = plan_period(data.get('period', 'day'), scheduled)
                if data.get('invoice_id') and operation == 'invoice':
                    raise ValueError('Для готового счёта выбери получение оплаты или платёж')
                if data['date'] == scheduled and data.get('period', 'day') == period and data.get('operation', 'invoice') == operation and data.get('amount') == amount and data.get('text', '') == text:
                    return self.record(row)
                db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (identity, row['revision'], row['data'], time.time()))
                data['date'] = scheduled
                data['period'] = period
                data['operation'] = operation
                data['text'] = text
                if amount is None:
                    data.pop('amount', None)
                else:
                    data['amount'] = amount
                db.execute('UPDATE invoices SET data=?,revision=revision+1,updated=? WHERE id=?',
                           (json.dumps(data, ensure_ascii=False), time.time(), identity))
            else:
                if 'revision' in payload:
                    raise InvoiceConflict('План не найден. Обнови список счетов')
                data = {'version': 1, 'kind': 'planned', 'date': scheduled, 'period': period, 'operation': operation}
                if not path:
                    data['scope'] = 'calendar'
                if text:
                    data['text'] = text
                if payload.get('source_invoice'):
                    source = self.current(db, path, payload['source_invoice'])
                    if source['state'] not in {'issued', 'external'} or operation == 'invoice':
                        raise ValueError('Для готового счёта выбери получение оплаты или платёж')
                    if type(payload.get('source_revision')) is not int or source['revision'] != payload['source_revision']:
                        raise InvoiceConflict('Счёт изменился. Проверь его перед планированием')
                    data.update(invoice_id=source['id'], invoice_label=self.source_label(source))
                if amount is not None:
                    data['amount'] = amount
                stamp = time.time()
                # Plans reserve no annual number and never enter the PDF outbox.
                db.execute("INSERT INTO invoices(id,path,year,number,revision,state,data,created,updated) VALUES (?,?,0,?,1,'planned',?,?,?)",
                           (identity, path, identity, json.dumps(data, ensure_ascii=False), stamp, stamp))
                if not path or data.get('invoice_id'):
                    local_metadata.schema(db)
                    db.execute("INSERT OR REPLACE INTO metadata_settings VALUES ('invoice_payment_sources','1')")
            return self.record(self.current(db, path, identity))

    def upload(self, payload):
        path, identity, name = self.store.path(payload.get('path')), payload.get('id'), payload.get('name')
        try:
            if str(uuid.UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Не указан идентификатор внешнего счёта") from None
        if not isinstance(name, str) or not name or name.startswith('.') or any(c in '/\\:' or ord(c) < 32 or ord(c) == 127 for c in name):
            raise ValueError("Недопустимое имя PDF")
        name = unicodedata.normalize('NFC', name)
        if len(os.fsencode(name)) > 255 or Path(name).suffix.casefold() != '.pdf':
            raise ValueError("Выбери PDF-файл с именем до 255 байт")
        comment = external_comment(payload.get('comment', ''))
        encoded = payload.get('pdf')
        if not isinstance(encoded, str) or len(encoded) > ((MAX_EXTERNAL_BYTES + 2) // 3) * 4:
            raise ValueError("PDF может занимать до 20 МБ")
        try:
            pdf = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("Не удалось прочитать переданный PDF. Повтори загрузку") from None
        if len(pdf) > MAX_EXTERNAL_BYTES:
            raise ValueError("PDF может занимать до 20 МБ")
        if not pdf.startswith(b'%PDF-') or b'%%EOF' not in pdf[-2048:]:
            raise ValueError("Файл не похож на завершённый PDF. Выбери исходный PDF ещё раз")
        stem = Path(name).stem
        suffix = ' - ' + identity[:8] + '.pdf'
        while len(os.fsencode(stem + suffix)) > 255:
            stem = stem[:-1]
        filename = stem + suffix
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self.owner(db, path, active=True)
            existing = db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone()
            if existing:
                if json.loads(existing['data']).get('_trash'):
                    raise InvoiceConflict('Этот счёт уже в корзине. Восстанови его вместо повторной загрузки')
                if existing['path'] != path or existing['state'] != 'external' or json.loads(existing['data'])['original_name'] != name or existing['pdf'] != pdf:
                    raise InvoiceConflict("Этот идентификатор уже относится к другому счёту")
                return self.record(existing)  # Retry never resets a later comment edit.
            data = {'kind': 'external', 'original_name': name, 'comment': comment, 'date': today().isoformat()}
            stamp = time.time()
            # External invoices do not consume or reserve annual invoice numbers.
            db.execute("""INSERT INTO invoices(id,path,year,number,revision,state,data,pdf,filename,created,updated)
                VALUES (?,?,0,?,1,'external',?,?,?,?,?)""",
                (identity, path, identity, json.dumps(data, ensure_ascii=False), pdf, filename, stamp, stamp))
            return self.record(self.current(db, path, identity))

    def save_comment(self, payload):
        comment = external_comment(payload.get('comment'))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self.current(db, payload.get('path'), payload.get('id'))
            self.owner(db, row['path'], active=True)
            if row['state'] != 'external' or type(payload.get('revision')) is not int or row['revision'] != payload['revision']:
                raise InvoiceConflict("Счёт уже изменён. Твой комментарий остался в форме; открой актуальную версию отдельно")
            data = json.loads(row['data'])
            if data.get('comment', '') == comment:
                return self.record(row)
            db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (row['id'], row['revision'], row['data'], time.time()))
            data['comment'] = comment
            db.execute('UPDATE invoices SET data=?,revision=revision+1,updated=? WHERE id=?',
                       (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
            return self.record(self.current(db, row['path'], row['id']))

    def save_list_status(self, payload):
        value = payload.get('value')
        if not isinstance(value, str) or value not in LIST_STATUSES:
            raise ValueError('Выбери отметку счёта: Актуально, Неактуально, Позже или Отправлен')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self.current(db, payload.get('path'), payload.get('id'))
            self.owner(db, row['path'], active=True)
            if type(payload.get('revision')) is not int or row['revision'] != payload['revision']:
                raise InvoiceConflict('Счёт изменился в другом окне. Обнови список и повтори выбор отметки')
            data = json.loads(row['data'])
            current = self.record(row)['list_status']
            if current is None:
                raise ValueError('У счёта неизвестная отметка. Она сохранена без замены')
            if current == value:
                return self.record(row)
            db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (row['id'], row['revision'], row['data'], time.time()))
            data['_list_status'] = value
            db.execute('UPDATE invoices SET data=?,revision=revision+1,updated=? WHERE id=?',
                       (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
            return self.record(self.current(db, row['path'], row['id']))

    @staticmethod
    def require_calendar_payment(row):
        data = json.loads(row['data'])
        if row['path'] or row['state'] != 'planned' or data.get('scope') != 'calendar' or not known_plan(data) or data.get('operation') not in ('incoming', 'outgoing'):
            raise ValueError('В календаре можно удалять только поступления и затраты без заказа')

    def remove(self, payload, *, calendar_only=False):
        if payload.get('confirmed') is not True:
            raise ValueError('Подтверди перенос выбранного счёта в корзину')
        with orders.SYNC_LOCK, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self.current(db, payload.get('path'), payload.get('id'), trashed=True)
            if calendar_only:
                self.require_calendar_payment(row)
            if row['path']:
                self.owner(db, row['path'], active=True)
            data = json.loads(row['data'])
            if data.get('_trash'):
                return self.record(row)
            if type(payload.get('revision')) is not int or row['revision'] != payload['revision']:
                raise InvoiceConflict('Счёт изменился. Обнови список перед удалением')
            local_metadata.schema(db)
            data['_trash'] = {'token': uuid.uuid4().hex, 'state': 'pending' if row['filename'] else 'complete', 'error': ''}
            db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (row['id'], row['revision'], row['data'], time.time()))
            db.execute('UPDATE invoices SET data=?,revision=revision+1,updated=? WHERE id=?', (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
            return self.record(self.current(db, row['path'], row['id'], trashed=True))

    def restore(self, payload, *, calendar_only=False):
        with orders.SYNC_LOCK, file_comments.LOCK:
            with self.connect() as db:
                row = self.current(db, payload.get('path'), payload.get('id'), trashed=True)
                if calendar_only:
                    self.require_calendar_payment(row)
                if row['path']:
                    self.owner(db, row['path'], active=True)
                marker = json.loads(row['data']).get('_trash')
                if not marker:
                    return self.record(row)
                if type(payload.get('revision')) is not int or row['revision'] != payload['revision']:
                    raise InvoiceConflict('Корзина счёта изменилась. Обнови список')
            session = file_trash.session_path(self.store.root, marker['token'])
            if (session / '.plan.json').exists():
                result = file_trash.restore(self.store.root, marker['token'])
                if result['error']:
                    raise InvoiceConflict(result['error'])
            else:
                with self.connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row = self.current(db, payload.get('path'), payload.get('id'), trashed=True)
                    data = json.loads(row['data'])
                    data.pop('_trash')
                    db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (row['id'], row['revision'], row['data'], time.time()))
                    db.execute('UPDATE invoices SET data=?,revision=revision+1,exported=0,updated=? WHERE id=?',
                               (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
            return self.get(payload['path'], payload['id'])

    def publish_copy(self, row):
        folder = self.store.target(row["path"]) / "# bills"
        if folder.is_symlink():
            raise ValueError("# bills является ссылкой; PDF остался в базе")
        if not folder.exists():
            # Reuse the project's journal and standalone mkdir undo.
            from folder_layout import Plan
            from order_folders import layout_scope
            plan = Plan(self.store.root, [Path(row["path"]).parts[0]], **layout_scope(row["path"]))
            plan.mkdir(folder.relative_to(self.store.root).as_posix())
            session = plan.create_session(["Создание # bills для выпущенных счетов; PDF сохранён в SQLite."], {"order": row["path"], "invoice": row["id"]})
            from folder_layout import apply
            apply(session)
        target = folder / row["filename"]
        if os.path.lexists(target):
            if target.is_symlink() or not target.is_file() or hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(row["pdf"]).digest():
                raise ValueError("Копия PDF изменена или имя занято. Файл не перезаписан; оригинал доступен из базы")
        else:
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(prefix=".invoice-", dir=folder, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(row["pdf"])
                    stream.flush()
                    os.fsync(stream.fileno())
                rename_exclusive(temporary, target)
            finally:
                if temporary:
                    temporary.unlink(missing_ok=True)
        return target

    def sync_trash(self):
        with self.connect() as db:
            identities = [row[0] for row in db.execute("SELECT id FROM invoices WHERE json_extract(data,'$._trash.state')='pending'")]
        for identity in identities:
            with orders.SYNC_LOCK, file_comments.LOCK:
                with self.connect() as db:
                    row = db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone()
                    if any(part.startswith('.') for part in Path(row['path']).parts):
                        continue
                    marker = json.loads(row['data']).get('_trash')
                    if not marker or marker['state'] != 'pending':
                        continue
                try:
                    with self.connect() as db:
                        assert_unlocked(db, row['path'])
                    session = file_trash.session_path(self.store.root, marker['token'])
                    if (session / '.plan.json').exists():
                        result = file_trash.resume(self.store.root, marker['token'])
                    else:
                        relative = (Path(row['path']) / '# bills' / row['filename']).as_posix()
                        target = file_trash.checked(self.store.root, relative)
                        folder = str(Path(relative).parent)
                        files = file_trash.preview(self.store.root, folder, [relative])['files'] if os.path.lexists(target) else None
                        self.publish_copy(row)
                        files = files or file_trash.preview(self.store.root, folder, [relative])['files']
                        result = file_trash.remove(self.store.root, folder, files, True, self.store.database,
                                                  token=marker['token'], invoice_id=identity)
                    error = result['error']
                except (OSError, ValueError, RuntimeError) as problem:
                    error = str(problem)
                with self.connect() as db:
                    db.execute("UPDATE invoices SET data=json_set(data,'$._trash.error',?,'$._trash.state',?) WHERE id=? AND json_extract(data,'$._trash.token')=?",
                               (error, 'pending' if error else 'complete', identity, marker['token']))

    def create(self, payload):
        path, identity = payload.get("path"), payload.get("id")
        try:
            if str(uuid.UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Не указан идентификатор нового счёта") from None
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            owner = self.owner(db, path, active=True)
            existing = db.execute("SELECT * FROM invoices WHERE id=?", (identity,)).fetchone()
            if existing:
                if existing["path"] != path:
                    raise InvoiceConflict("Этот идентификатор относится к другому заказу")
                if existing['state'] == 'planned':
                    raise InvoiceConflict('Этот идентификатор относится к плану выписки счёта')
                if json.loads(existing['data']).get('_trash'):
                    raise InvoiceConflict('Этот счёт уже в корзине. Восстанови его из списка удалённых')
                return self.record(existing)
            year = today().year
            row = db.execute("SELECT value FROM invoice_sequences WHERE year=?", (year,)).fetchone()
            sequence = row[0] if row else 0
            while True:
                sequence += 1
                number = str(sequence)
                if not db.execute("SELECT 1 FROM invoices WHERE year=? AND number=?", (year, number)).fetchone():
                    break
            db.execute("INSERT INTO invoice_sequences VALUES (?,?) ON CONFLICT(year) DO UPDATE SET value=excluded.value", (year, sequence))
            settings = db.execute("SELECT value FROM invoice_settings WHERE key='seller'").fetchone()
            data = {key: "" for key in FIELDS}
            data.update(kind="invoice", number=number, date=today().isoformat(), due_date=(today() + timedelta(days=7)).isoformat(),
                        buyer_name=orders.client_name(path), seller=json.loads(settings[0]) if settings else dict(DEFAULT_SELLER),
                        terms=DEFAULT_TERMS, items=[{"name": owner["title"], "unit": "шт", "quantity": "1", "price": "0"}])
            if payload.get("source"):
                source = self.current(db, path, payload["source"])
                if source['state'] not in {'draft', 'issued'}:
                    raise ValueError("Этот документ нельзя использовать как черновик редактора")
                data.update(json.loads(source["data"]))
                data.update(number=number, date=today().isoformat(), due_date=(today() + timedelta(days=7)).isoformat(), work_start="", work_end="")
            data = validate(data)
            stamp = time.time()
            db.execute("INSERT INTO invoices(id,path,year,number,revision,state,data,created,updated) VALUES (?,?,?,?,1,'draft',?,?,?)",
                       (identity, path, year, number, json.dumps(data, ensure_ascii=False), stamp, stamp))
            return self.record(self.current(db, path, identity))

    def save(self, payload):
        data = validate(payload.get("data"))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.current(db, payload.get("path"), payload.get("id"))
            self.owner(db, row["path"], active=True)
            if row["state"] != "draft" or type(payload.get("revision")) is not int or row["revision"] != payload["revision"]:
                raise InvoiceConflict("Счёт уже изменён или выпущен. Твой ввод сохранён в форме; открой актуальную версию отдельно")
            previous = json.loads(row['data'])
            if '_list_status' in previous:
                data['_list_status'] = previous['_list_status']
            year = int(data["date"][:4])
            if db.execute("SELECT 1 FROM invoices WHERE year=? AND number=? AND id<>?", (year, data["number"], row["id"])).fetchone():
                raise InvoiceConflict("Такой номер уже занят в этом году. Укажи другой номер")
            db.execute("INSERT INTO invoice_history VALUES (?,?,?,?)", (row["id"], row["revision"], row["data"], time.time()))
            db.execute("UPDATE invoices SET year=?,number=?,data=?,revision=revision+1,updated=? WHERE id=?",
                       (year, data["number"], json.dumps(data, ensure_ascii=False), time.time(), row["id"]))
            if payload.get("remember_seller") is True:
                db.execute("INSERT INTO invoice_settings VALUES ('seller',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                           (json.dumps(data["seller"], ensure_ascii=False),))
            return self.record(self.current(db, row["path"], row["id"]))

    def issue(self, payload):
        with self.connect() as db:
            row = self.current(db, payload.get("path"), payload.get("id"))
            if row["state"] == "issued":
                return self.record(row)  # A retry after a lost HTTP response is safe.
            if row['state'] != 'draft':
                raise ValueError("Внешний PDF уже прикреплён; выпуск в редакторе ему не нужен")
            if type(payload.get("revision")) is not int or payload["revision"] != row["revision"]:
                raise InvoiceConflict("Черновик изменился. Обнови его перед выпуском")
            data = validate(json.loads(row["data"]), issuing=True)
            revision, path, identity = row["revision"], row["path"], row["id"]
        # PDF generation uses only local data; it holds no SQLite writer lock.
        pdf = render(data, self.app_dir, self.store.database.parent)
        label = "Счёт-договор" if data["kind"] == "contract" else "Счёт"
        number = re.sub(r"[^0-9А-Яа-яЁёA-Za-z._-]", "-", data["number"])
        filename = f"{label} № {number} от {data['date']} - {identity[:8]}.pdf"
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self.owner(db, path, active=True)
            row = self.current(db, path, identity)
            if row["state"] == "issued":
                return self.record(row)
            if row["revision"] != revision:
                raise InvoiceConflict("Черновик изменился во время подготовки PDF. Выпуск отменён")
            db.execute("UPDATE invoices SET pdf=?,state='issued',filename=?,revision=revision+1,updated=?,sync_error='' WHERE id=?",
                       (pdf, filename, time.time(), identity))
            return self.record(self.current(db, path, identity))

    def pdf(self, path, identity):
        with self.connect() as db:
            row = self.current(db, path, identity)
            if row["state"] not in {"issued", "external"}:
                raise ValueError("Сначала выпусти PDF")
            return row["pdf"], row["filename"]

    def preview(self, path, identity):
        record = self.get(path, identity)
        if record['state'] == 'planned':
            raise ValueError('Запланирована только выписка счёта; PDF ещё нет')
        if record['state'] == 'external':
            return self.pdf(path, identity)[0]
        data = validate(record["data"], issuing=True)
        return render({**data, "preview": True}, self.app_dir, self.store.database.parent)

    def sync(self):
        if not SYNC_LOCK.acquire(blocking=False):
            return
        try:
            self.sync_trash()
            with self.connect() as db:
                pending = [row[0] for row in db.execute("SELECT id FROM invoices WHERE state IN ('issued','external') AND exported=0 AND json_extract(data,'$._trash') IS NULL")]
            for identity in pending:
                # Coordinate path changes with the existing folder rename protocol.
                with orders.SYNC_LOCK:
                    try:
                        with self.connect() as db:
                            row = db.execute("SELECT * FROM invoices WHERE id=?", (identity,)).fetchone()
                            if any(part.startswith('.') for part in Path(row['path']).parts):
                                continue
                            if json.loads(row['data']).get('_trash'):
                                continue
                            assert_unlocked(db, row["path"])
                        self.publish_copy(row)
                        error = ""
                    except (OSError, ValueError, RuntimeError) as problem:
                        error = str(problem)
                    with self.connect() as db:
                        db.execute("UPDATE invoices SET exported=?,sync_error=? WHERE id=?", (int(not error), error, identity))
        finally:
            SYNC_LOCK.release()
