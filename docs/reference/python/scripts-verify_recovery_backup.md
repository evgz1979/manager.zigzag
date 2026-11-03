# scripts/verify_recovery_backup.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/verify_recovery_backup.py:1](../../../scripts/verify_recovery_backup.py#L1).

Standalone verification of an extracted recovery bundle, without the application.

Импорты Python, включая локальные: `argparse`, `contextlib`, `hashlib`, `json`, `pathlib`, `sqlite3`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## verify

[scripts/verify_recovery_backup.py:13](../../../scripts/verify_recovery_backup.py#L13) · `function`.

```python
def verify(directory):
```

Проверяет состав, хеши и SQLite-снимок выбранной резервной копии.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `Path(directory).resolve`, `Path`, `json.loads`, `(directory / 'manifest.json').read_text`, `manifest.get`, `ValueError`, `files.items`, `relative.is_absolute`, `relative.as_posix`, `any`, `(directory / Path(*relative.parts[:i])).is_symlink`, `range`, `len`, `hashlib.sha256`, `path.open`, `iter`, `checksum.update`, `path.stat`, `checksum.hexdigest`, `database.with_name(database.name + suffix).exists`, `database.with_name`, `closing`, `sqlite3.connect`, `database.as_uri`, `db.execute('PRAGMA integrity_check').fetchall`, `db.execute`, `db.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone`, `name.replace`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
manifest
```
