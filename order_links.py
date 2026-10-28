"""Symmetric client-order links, stored by UUID in existing order extra blocks."""
import json
import uuid
from pathlib import Path

from event_folder_undo import assert_unlocked
from folder_structure import order_location

BLOCK = "Связанные клиентские заказы"
PRIMARY_BLOCK = "Главные связи клиентского заказа"
ORDER_LINKS_VERSION = 1
ORDER_LINK_ROLES_VERSION = 1
ORDER_LINK_STATUS_VERSION = 1
ORDER_LINK_STAR_VERSION = 1
MAX_LINKS = 200


def mark_status_contract(db):
    db.execute("INSERT INTO metadata_settings VALUES ('client_order_link_status','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")


def checked_ids(value):
    if not isinstance(value, list) or len(value) > MAX_LINKS:
        raise ValueError(f"Выбери не больше {MAX_LINKS} разных заказов")
    if any(not isinstance(item, str) for item in value):
        raise ValueError("Некорректный идентификатор связанного заказа")
    if len(set(value)) != len(value):
        raise ValueError("Связанный заказ не должен повторяться")
    for identity in value:
        try:
            if str(uuid.UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError("Некорректный идентификатор связанного заказа") from None
    return value


def read(blocks, block=BLOCK):
    if block not in blocks:
        return []
    try:
        body = json.loads(blocks[block])
        if not isinstance(body, dict) or set(body) != {"version", "order_ids"} or type(body["version"]) is not int or body["version"] != 1:
            return None
        return checked_ids(body["order_ids"])
    except (TypeError, ValueError):
        return None


def read_primary(blocks):
    identities, primary = read(blocks), read(blocks, PRIMARY_BLOCK)
    return primary if identities is not None and primary is not None and set(primary) <= set(identities) else None


def write(blocks, identities, primary=None):
    if read(blocks) is None or read_primary(blocks) is None:
        raise ValueError("Неизвестный формат связанных заказов сохранён без изменений")
    identities = checked_ids(identities)
    primary_ids = read_primary(blocks) if primary is None else checked_ids(primary)
    if not set(primary_ids) <= set(identities):
        raise ValueError("Главные связи должны входить в список связанных заказов")
    result = {**blocks, BLOCK: json.dumps({"version": 1, "order_ids": sorted(identities)}, ensure_ascii=False)}
    if primary is not None:
        result[PRIMARY_BLOCK] = json.dumps({"version": 1, "order_ids": sorted(primary_ids)}, ensure_ascii=False)
    return result


def scope(path):
    if any(part.startswith(("#", ".")) for part in Path(path).parts):
        return None
    location = order_location(path)
    if not location["client_path"] or not location["object_path"]:
        return None
    return location["client_path"], location["object_path"]


def primary_items(db, path, identities):
    if identities is None:
        return None
    if not identities:
        return []
    rows = {row["id"]: row for row in db.execute("SELECT id,path,title,registered FROM orders WHERE id IN (" + ','.join('?' for _ in identities) + ")", identities)}
    result = []
    for identity in identities:
        row = rows.get(identity)
        result.append({"id": identity, "path": row["path"] if row else None, "title": row["title"] if row else "Заказ недоступен",
                       "available": bool(row and row["registered"] and scope(row["path"]) == scope(path))})
    return sorted(result, key=lambda item: (item["title"].casefold(), item["id"]))


def states(rows):
    result = {}
    for identity, row in rows.items():
        blocks = json.loads(row["extra_blocks"])
        links, primary = read(blocks), read_primary(blocks)
        if links is not None and primary is not None:
            result[identity] = (set(links), set(primary))
    return result


def group_main(rows, identity):
    """Return one main and whether an old, undirected star needs initialization."""
    known = states(rows)
    if identity not in known:
        raise ValueError("Неизвестный формат связанных заказов сохранён без изменений")
    links, primary = known[identity]
    incoming = [key for key, (_, own) in known.items() if identity in own]
    if primary:
        main = identity
        if incoming or primary != links:
            raise ValueError("В прежних связях несколько главных; данные сохранены без изменений")
    elif incoming:
        if len(incoming) != 1 or links != {incoming[0]}:
            raise ValueError("У подчинённого должен быть один главный заказ")
        main = incoming[0]
    elif not links:
        return identity, False
    else:
        # A legacy star can be initialized once, as a whole group. With two
        # undirected orders, the explicitly opened order will become the main.
        main = identity
        if len(links) == 1:
            neighbor = next(iter(links))
            if neighbor in known and len(known[neighbor][0]) > 1:
                main = neighbor
        if main not in known:
            raise ValueError("Главный заказ недоступен")
    children, own = known[main]
    legacy = bool(children) and not own
    if own and own != children:
        raise ValueError("У группы должен быть один главный заказ")
    for child in children:
        if child not in rows:
            continue
        if child not in known or known[child] != ({main}, set()):
            raise ValueError("Подчинённый заказ не может иметь других связей или быть главным")
    if any(main in own_ids for _, own_ids in known.values()):
        raise ValueError("Главный заказ не может быть подчинённым")
    return main, legacy


def child_ids(rows):
    children = set()
    for identity, (_, primary) in states(rows).items():
        if not primary:
            continue
        try:
            main, legacy = group_main(rows, identity)
        except ValueError:
            continue
        if main == identity and not legacy:
            children.update(child for child in primary if child in rows and scope(rows[child]["path"]) == scope(rows[main]["path"]))
    return children


def mark_group_contract(db):
    for key in ('client_order_links', 'client_order_link_roles', 'client_order_link_star'):
        db.execute("INSERT INTO metadata_settings VALUES (?, '1') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key,))
    mark_status_contract(db)


class OrderLinks:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _rows(db):
        return {row["id"]: dict(row) for row in db.execute("SELECT * FROM orders")}

    def _read(self, db, source):
        rows = self._rows(db)
        claimed = {child for _, own in states(rows).values() for child in own}
        problem, legacy = '', False
        try:
            main, legacy = group_main(rows, source['id'])
            source = rows[main]
        except ValueError as error:
            problem = str(error)
        source_scope = scope(source['path'])
        if not source_scope:
            raise ValueError("Связывать можно только заказы объекта клиента")
        identities = read(json.loads(source['extra_blocks']))
        items, candidates = [], []
        for row in rows.values():
            if row['id'] == source['id']:
                continue
            blocks = json.loads(row['extra_blocks'])
            links, primary = read(blocks), read_primary(blocks)
            available = bool(row['registered']) and scope(row['path']) == source_scope
            summary = {key: row[key] for key in ('id', 'path', 'title', 'revision')}
            summary.update(available=available, registered=bool(row['registered']), editable=links is not None and primary is not None)
            if identities is not None and row['id'] in identities:
                items.append(summary)
            elif source['registered'] and available and links == [] and primary == [] and row['id'] not in claimed:
                # Orders in any other group are never candidates.
                candidates.append(summary)
        for identity in identities or []:
            if identity not in rows:
                items.append({'id': identity, 'path': None, 'title': 'Заказ недоступен', 'revision': None, 'available': False, 'registered': False, 'editable': True})
        key = lambda item: (item['title'].casefold(), item['path'] or '', item['id'])
        versions = {identity: rows[identity]['revision'] for identity in [source['id'], *(identities or [])] if identity in rows}
        return {'order': self.store.record(source, db), 'linked_ids': identities, 'items': sorted(items, key=key),
                'candidates': sorted(candidates, key=key), 'needs_primary': legacy, 'group_error': problem, 'versions': versions}

    def read(self, relative):
        relative = self.store.path(relative)
        with self.store.connect() as db:
            assert_unlocked(db, relative)
            source = db.execute('SELECT * FROM orders WHERE path=?', (relative,)).fetchone()
            if source is None:
                raise FileNotFoundError('Заказ не найден')
            return self._read(db, source)

    def migrate_statuses(self):
        if not self.store.database_only:
            return 0
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM metadata_settings WHERE key='client_order_link_status_migrated' AND value='1'").fetchone():
                return 0
            rows = self._rows(db)
            updates = []
            for identity in child_ids(rows):
                row = rows[identity]
                if row['status'] != 'related':
                    assert_unlocked(db, row['path'])
                    updates.append((identity,))
            db.executemany("UPDATE orders SET status='related',revision=revision+1 WHERE id=?", updates)
            db.execute("INSERT INTO metadata_settings VALUES ('client_order_link_status_migrated','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
            if updates:
                mark_group_contract(db)
            return len(updates)

    def save(self, payload):
        from orders import OrderConflict
        relative = self.store.path(payload.get('path'))
        identity, revision = payload.get('id'), payload.get('revision')
        checked_ids([identity])
        if type(revision) is not int:
            raise ValueError('Не указана версия заказа')
        initialize = payload.get('initialize', False)
        if type(initialize) is not bool:
            raise ValueError('Некорректное действие со связями')
        if payload.get('make_primary', False) is not False:
            raise ValueError('Главный в группе один. Смена ролей отдельной связи недоступна')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = self._rows(db)
            requested = rows.get(identity)
            if requested is None or requested['path'] != relative or requested['revision'] != revision:
                raise OrderConflict('Заказ изменён. Обнови список связей перед повтором')
            assert_unlocked(db, relative)
            main, legacy = group_main(rows, identity)
            source = rows[main]
            if not scope(source['path']):
                raise ValueError('Связывать можно только заказы объекта клиента')
            source_ids = read(json.loads(source['extra_blocks']))
            if initialize:
                if not legacy or identity != main:
                    raise ValueError('Главный заказ этой группы уже определён')
                expected = {key: rows[key]['revision'] for key in [main, *source_ids] if key in rows}
                versions = payload.get('versions')
                if not isinstance(versions, dict) or any(type(value) is not int for value in versions.values()) or versions != expected:
                    raise OrderConflict('Группа изменилась. Обнови список связей перед повтором')
                if not source['registered']:
                    raise ValueError('Сначала верни главный заказ в список')
                updates = []
                for key in [main, *source_ids]:
                    if key not in rows:
                        continue
                    row = rows[key]
                    assert_unlocked(db, row['path'])
                    if scope(row['path']) != scope(source['path']):
                        raise ValueError('Все подчинённые должны находиться в том же объекте и клиенте')
                    blocks = json.loads(row['extra_blocks'])
                    ids = read(blocks)
                    primary = source_ids if key == main else []
                    blocks = json.dumps(write(blocks, ids, primary), ensure_ascii=False)
                    status = row['status'] if key == main else 'related'
                    if blocks != row['extra_blocks'] or status != row['status']:
                        updates.append((blocks, status, key))
            else:
                target_id, target_revision, linked = payload.get('target_id'), payload.get('target_revision'), payload.get('linked')
                checked_ids([identity, target_id])
                if type(linked) is not bool or (target_revision is not None and type(target_revision) is not int):
                    raise ValueError('Нужны версии заказов и логическое состояние связи')
                target = rows.get(target_id)
                if (target['revision'] if target else None) != target_revision:
                    raise OrderConflict('Связанный заказ изменён. Обнови список связей перед повтором')
                if main != identity:
                    if linked or target_id != main:
                        raise ValueError('Подчинённый может быть связан только со своим главным заказом')
                    # Removing from the child's side still updates the same group.
                    target_id, target = identity, requested
                elif legacy:
                    raise ValueError('Сначала выбери главный заказ для прежней группы связей')
                if linked and (not source['registered'] or target is None or not target['registered'] or scope(source['path']) != scope(target['path'])):
                    raise ValueError('Выбери зарегистрированный заказ этого же объекта и клиента')
                if target:
                    assert_unlocked(db, target['path'])
                    target_blocks = json.loads(target['extra_blocks'])
                    target_links, target_primary = read(target_blocks), read_primary(target_blocks)
                    if target_links is None or target_primary is None:
                        raise ValueError('Неизвестный формат связанных заказов сохранён без изменений')
                    claimed = any(target_id in own for _, own in states(rows).values())
                    if linked and target_id not in source_ids and (target_links or target_primary or claimed):
                        raise ValueError('Заказ уже входит в другую группу. Сначала сними прежнюю связь')
                if not linked and target_id not in source_ids:
                    return {**self._read(db, source), 'records': []}
                new_ids = set(source_ids)
                new_ids.add(target_id) if linked else new_ids.discard(target_id)
                source_blocks = json.loads(source['extra_blocks'])
                source_blocks = json.dumps(write(source_blocks, list(new_ids), list(new_ids)), ensure_ascii=False)
                updates = []
                if source_blocks != source['extra_blocks']:
                    updates.append((source_blocks, source['status'], main))
                if target:
                    child_links = [main] if linked else []
                    target_blocks = json.dumps(write(target_blocks, child_links, []), ensure_ascii=False)
                    status = 'related' if linked else 'new'
                    if target_blocks != target['extra_blocks'] or status != target['status']:
                        updates.append((target_blocks, status, target_id))
            # Check the main too when a request originates from its child.
            assert_unlocked(db, source['path'])
            db.executemany('UPDATE orders SET extra_blocks=?,status=?,revision=revision+1 WHERE id=?', updates)
            if updates and self.store.database_only:
                mark_group_contract(db)
            source = db.execute('SELECT * FROM orders WHERE id=?', (main,)).fetchone()
            result = self._read(db, source)
            result['records'] = [self.store.record(db.execute('SELECT * FROM orders WHERE id=?', (key,)).fetchone(), db) for _, _, key in updates]
            return result
