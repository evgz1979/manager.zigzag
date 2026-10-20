"""Group an object's dated orders by year, with coordinated SQLite paths and undo."""
from contextlib import closing
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from zoneinfo import ZoneInfo

import folder_layout as layout
import folder_notes
import folder_rename_undo as restore
from event_folder_undo import assert_unlocked
from folder_structure import folder_role, dated, DATE, YEAR
from order_folders import LOCK, year_groups
from order_todos import REFRESH_LOCK
import orders


class YearGroupConflict(ValueError):
    pass


def _preview(store, relative, db):
    if not isinstance(relative,str) or not Path(relative).parts or any(p.startswith('.') for p in Path(relative).parts):
        raise ValueError("Выбери объект клиента")
    root = store.root.resolve()
    parent = layout.safe_path(root,relative,[Path(relative).parts[0]])
    if not parent.is_dir() or folder_role(root,relative)["folderKind"]!="object":
        raise ValueError("Группировка по годам доступна в объекте клиента")
    assert_unlocked(db,relative,include_children=True)
    inventory=[]; mappings=[]; skipped=[]; conflicts=[]
    existing = sorted(year_groups(root,relative))
    for child in sorted(parent.iterdir(),key=lambda p:p.name):
        if child.name.startswith('.'):
            continue
        inventory.append({"name":child.name,"identity":layout.identity(child)})
        if child.name in existing:
            inventory[-1]['children']=[{"name":p.name,"identity":layout.identity(p)} for p in sorted(child.iterdir(),key=lambda p:p.name) if not p.name.startswith('.')]
        if child.is_symlink() or not child.is_dir() or child.name.startswith('#') or child.name in existing:
            continue
        source = child.relative_to(root).as_posix()
        if not dated(child.name):
            if folder_role(root,source)["folderKind"] in {'order','invalid'}:
                skipped.append(child.name)
            continue
        year = DATE.match(child.name)[1]
        year = '20'+year if len(year)==2 else year
        if not YEAR.fullmatch(year):
            skipped.append(child.name)
            continue
        container = parent/year
        destination = (container/child.name).relative_to(root).as_posix()
        if layout.exists(container) and year not in existing:
            conflicts.append("Путь года занят отдельной работой, файлом или ссылкой: "+year)
        if layout.exists(root/destination):
            conflicts.append("Путь уже занят: "+destination)
        try:
            restore.check(db,source,destination)
        except ValueError as error:
            conflicts.append(str(error))
        mappings.append({"source":source,"destination":destination,"year":year})
    years = sorted({pair['year'] for pair in mappings})
    if not years and not existing:
        years = [datetime.now(ZoneInfo('Europe/Moscow')).strftime('%Y')]
    for year in years:
        if layout.exists(parent/year) and year not in existing:
            conflicts.append("Путь года занят отдельной работой, файлом или ссылкой: "+year)
    created = [str(Path(relative)/year) for year in years if not layout.exists(parent/year)]
    for path in created:
        try:
            restore.check(db,str(Path(relative)/'.new-year'),path)
        except ValueError as error:
            conflicts.append(str(error))
    token = {"path":relative,"identity":layout.identity(parent),"children":inventory}
    return {"path":relative,"revision":hashlib.sha256(json.dumps(token,sort_keys=True).encode()).hexdigest(),
            "mappings":mappings,"created_years":created,"existing_years":existing,
            "skipped":skipped,"conflicts":list(dict.fromkeys(conflicts)),"before":token}


def preview(store,relative):
    with LOCK, store.connect() as db:
        return _preview(store,relative,db)


def group(store,payload):
    if payload.get('confirmed') is not True:
        raise ValueError("Подтверди показанный список переносов")
    root = store.root.resolve()
    with LOCK, REFRESH_LOCK, orders.SYNC_LOCK, folder_notes.SYNC_LOCK, store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        view = _preview(store,payload.get('path'),db)
        if view['revision']!=payload.get('revision'):
            raise YearGroupConflict("Состав папок изменился. Обнови список перед группировкой")
        if view['conflicts']:
            raise YearGroupConflict('; '.join(view['conflicts']))
        if not view['mappings'] and not view['created_years']:
            raise YearGroupConflict("Заказы уже распределены по годам")
        plan = layout.Plan(root,[Path(view['path']).parts[0]])
        plan.database_paths = True
        for path in view['created_years']:
            plan.mkdir(path)
        for pair in view['mappings']:
            plan.move(pair['source'],pair['destination'],"Сгруппировать заказ по году его даты")
        session = plan.create_session(["Группировка заказов объекта по годам.","Откат через .restore.py с сохранением путей SQLite."],view['before'])
        layout.save_json(session/'.folder-paths.json',{"database":str(store.database.resolve()),"mappings":view['mappings'],"created_years":view['created_years']})
        shutil.copyfile(restore.__file__,session/'.restore.py')
        with closing(sqlite3.connect(store.database.resolve().as_uri()+'?mode=ro',uri=True)) as source:
            with closing(sqlite3.connect(session/'.before.sqlite3')) as backup:
                source.backup(backup)
        db.execute("CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)")
        guards = [*view['mappings'],{"source":view['path'],"destination":view['path']}]
        db.execute("INSERT INTO folder_renames VALUES (?,'pending',?,0)",(str(session),json.dumps(guards,ensure_ascii=False)))
        db.commit()
        try:
            db.execute('BEGIN IMMEDIATE')
            layout.apply(session)
            for pair in view['mappings']:
                if folder_role(root,pair['destination'])["folderKind"]!='order':
                    raise ValueError("Папка после переноса перестала распознаваться как заказ")
                restore.rewrite(db,pair['source'],pair['destination'])
            db.execute("UPDATE folder_renames SET state='complete',paths_applied=1 WHERE session=?",(str(session),))
            db.commit()
        except Exception as error:
            db.rollback()
            try:
                restore.undo(session,True)
            except (OSError,ValueError,sqlite3.Error) as problem:
                layout.append(session,{"phase":"rollback_failed","error":str(problem)})
                raise YearGroupConflict("Группировка остановлена; данные сохранены. Нужен откат из журнала: "+str(session)) from error
            raise YearGroupConflict("Группировка отменена, прежние пути восстановлены: "+str(error)) from error
        layout.save_json(session/'.result.json',{"status":"grouped","mappings":view['mappings']})
        return {"path":view['path'],"moved":len(view['mappings']),"journal":session.relative_to(root).as_posix()}
