# scripts/deploy.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/deploy.py:1](../../../scripts/deploy.py#L1).

Проверка и доставка кода на M4; рабочие данные не входят в обычный деплой.

Импорты Python, включая локальные: `argparse`, `configparser`, `contextlib`, `datetime`, `hashlib`, `io`, `json`, `pathlib`, `shlex`, `sqlite3`, `subprocess`, `sys`, `tarfile`, `tempfile`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## source_files

[scripts/deploy.py:24](../../../scripts/deploy.py#L24) · `function`.

```python
def source_files():
```

Собирает только исходники приложения без обхода рабочих документов и data.

Возвращает `{p.relative_to(APP).as_posix(): p.read_bytes() for p in sorted(files)}`.

Непосредственные вызовы: `APP.iterdir`, `(APP / directory).rglob`, `path.relative_to`, `path.is_file`, `path.is_symlink`, `any`, `part.startswith`, `files.append`, `p.relative_to(APP).as_posix`, `p.relative_to`, `p.read_bytes`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
{p.relative_to(APP).as_posix(): p.read_bytes() for p in sorted(files)}
```

## snapshot_bytes

[scripts/deploy.py:38](../../../scripts/deploy.py#L38) · `function`.

```python
def snapshot_bytes(path):
```

Получает согласованный SQLite-снимок без зависимости от WAL/SHM.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `tempfile.TemporaryDirectory`, `Path`, `closing`, `sqlite3.connect`, `path.resolve().as_uri`, `path.resolve`, `source.backup`, `snapshot.execute`, `snapshot.execute('PRAGMA quick_check').fetchone`, `RuntimeError`, `target.read_bytes`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
target.read_bytes()
```

## main

[scripts/deploy.py:54](../../../scripts/deploy.py#L54) · `function`.

```python
def main():
```

Разбирает параметры запуска и выполняет основной сценарий программы.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `sum`, `bool`, `parser.error`, `configparser.ConfigParser`, `config.read`, `dict`, `int`, `source_files`, `subprocess.run`, `RuntimeError`, `datetime.now(timezone.utc).strftime`, `datetime.now`, `uuid4`, `hashlib.sha256(body).hexdigest`, `hashlib.sha256`, `files.items`, `(release + '\n').encode`, `snapshot_bytes`, `hashlib.sha256(files['.initial.sqlite3']).hexdigest`, `(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode`, `json.dumps`, `io.BytesIO`, `tarfile.open`, `tarfile.TarInfo`, `len`, `archive.addfile`, `buffer.getvalue`, `(APP / 'scripts/deploy_remote.py').read_text`, `shlex.join`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
result.returncode
```
