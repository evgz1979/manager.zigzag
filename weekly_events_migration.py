"""Consolidate legacy week comments into order calendar events, with a snapshot."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

import local_metadata
import order_calendar
from event_folder_undo import assert_unlocked

MARKER = 'weekly_events_unified'


def changes(db):
    """Validate the whole plan before changing any row."""
    result = []
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table, column in [('orders', 'extra_blocks'), ('folder_notes', 'document')]:
        if table not in tables:
            continue
        for row in db.execute('SELECT * FROM '+table):
            before = row[column]
            value = json.loads(before)
            blocks = value if table == 'orders' else value.get('extra_blocks', {})
            try:
                unified = order_calendar.unify_weekly_blocks(blocks)
            except ValueError as error:
                raise ValueError(row['path']+': '+str(error)) from None
            if table == 'orders':
                after = json.dumps(unified, ensure_ascii=False) if unified != blocks else before
            else:
                body = dict(value)
                if unified != blocks:
                    body['extra_blocks'] = unified
                body.pop('deadline_comments', None)  # Old computed snapshot, not a source.
                after = json.dumps(body, ensure_ascii=False) if body != value else before
            if after != before:
                assert_unlocked(db, row['path'])
                result.append({'table': table, 'column': column, 'id': row['id'], 'path': row['path'],
                               'revision': row['revision'], 'before': before, 'after': after})
    return result


def table_counts(db):
    names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    return {name: db.execute('SELECT count(*) FROM "'+name.replace('"', '""')+'"').fetchone()[0] for name in names}


RESTORE = '''#!/usr/bin/env python3
"""Restore only untouched migrated fields; never replace the working database."""
from contextlib import closing
import hashlib,json,sqlite3
from pathlib import Path
HERE=Path(__file__).resolve().parent
raw=(HERE/'plan.json').read_bytes()
if hashlib.sha256(raw).hexdigest()!=PLAN_SHA256:
    raise SystemExit('План изменён. Восстановление остановлено')
plan=json.loads(raw)
with closing(sqlite3.connect(plan['database'],timeout=30)) as db:
    db.row_factory=sqlite3.Row
    with db:
        db.execute('BEGIN IMMEDIATE')
        for item in plan['changes']:
            table,column=item['table'],item['column']
            if (table,column) not in [('orders','extra_blocks'),('folder_notes','document')]:
                raise ValueError('Неизвестная таблица плана')
            row=db.execute('SELECT * FROM '+table+' WHERE id=?',(item['id'],)).fetchone()
            if row is None or row['path']!=item['path'] or row['revision']!=item['revision']+1 or row[column]!=item['after']:
                raise ValueError('Есть более поздние изменения: '+item['path']+'. Ничего не заменено')
        for item in plan['changes']:
            db.execute('UPDATE '+item['table']+' SET '+item['column']+'=?,revision=revision+1 WHERE id=?',
                       (item['before'],item['id']))
print('Исходные поля восстановлены, версии и история сохранены. Код и остальные данные не заменены.')
'''


def migrate(database, output):
    database = Path(database).resolve()
    with closing(sqlite3.connect(database.as_uri()+'?mode=rw', uri=True, timeout=30)) as db:
        db.row_factory = sqlite3.Row
        local_metadata.schema(db)
        for table in ('orders', 'folder_notes'):
            local_metadata.audit(db, table)
        db.commit()
        # The lock prevents writes between planning, snapshot and the transaction.
        db.execute('BEGIN IMMEDIATE')
        journal = None
        committed = False
        try:
            planned = changes(db)
            current = db.execute('SELECT value FROM metadata_settings WHERE key=?', (MARKER,)).fetchone()
            if not planned and current and current[0] == '1':
                db.rollback()
                return {'status': 'already-migrated', 'orders': 0, 'folder_notes': 0}
            journal = Path(output)/('weekly-events-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
            journal.mkdir(parents=True, exist_ok=False)
            backup = journal/'before.sqlite3'
            counts = table_counts(db)
            # A separate reader sees the same committed state while BEGIN IMMEDIATE
            # holds the writer slot; backing up this writer would wait on itself.
            with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as source:
                with closing(sqlite3.connect(backup)) as target:
                    source.backup(target)
            with closing(sqlite3.connect(backup)) as saved:
                saved.execute('PRAGMA journal_mode=DELETE')
                if saved.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or table_counts(saved) != counts:
                    raise ValueError('Проверка снимка базы не пройдена; перенос не выполнен')
            plan = {'version': 1, 'database': str(database), 'backup': str(backup), 'counts': counts,
                    'backup_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'changes': planned}
            raw = (json.dumps(plan, ensure_ascii=False, indent=2)+'\n').encode()
            with (journal/'plan.json').open('xb') as file:
                file.write(raw); file.flush(); os.fsync(file.fileno())
            helper = 'PLAN_SHA256 = '+repr(hashlib.sha256(raw).hexdigest())+'\n'+RESTORE
            (journal/'.restore.py').write_text(helper)
            for item in planned:
                db.execute('UPDATE '+item['table']+' SET '+item['column']+'=?,revision=revision+1 WHERE id=?',
                           (item['after'], item['id']))
            db.execute('INSERT INTO metadata_settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (MARKER, '1'))
            db.commit()
            committed = True
            result = {'status': 'ok', 'orders': sum(item['table']=='orders' for item in planned),
                      'folder_notes': sum(item['table']=='folder_notes' for item in planned),
                      'journal': str(journal), 'backup_sha256': plan['backup_sha256']}
            (journal/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
            return result
        except Exception as error:
            db.rollback()
            if journal is not None:
                (journal/'result.json').write_text(json.dumps({'status': 'applied-report-error' if committed else 'failed', 'error': str(error)}, ensure_ascii=False)+'\n')
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.apply:
        result = migrate(args.database, args.output or args.database.parent/'backups')
    else:
        with closing(sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            plan = changes(db)
            result = {'status': 'plan', 'orders': sum(row['table']=='orders' for row in plan),
                      'folder_notes': sum(row['table']=='folder_notes' for row in plan)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
