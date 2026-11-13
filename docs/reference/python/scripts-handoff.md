# scripts/handoff.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/handoff.py](../../../scripts/handoff.py).

Полный перенос рабочей установки на MacBook и обратно.

Импорты Python, включая локальные: `argparse`, `configparser`, `deploy_remote`, `fcntl`, `handoff_host`, `json`, `os`, `pathlib`, `plistlib`, `shlex`, `shutil`, `socket`, `sqlite3`, `subprocess`, `sys`, `tempfile`, `uuid`, `zipfile`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-back"></a>

## back

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def back(local, settings, state_file, state):
```

Передаёт свежий снимок с MacBook на остановленный M4.

После сбоя повторяет прежнюю передачу и сохраняет записи уже запущенного M4.

Непосредственные вызовы: `remote`, `print`, `RuntimeError`, `confirm`, `uuid.uuid4`, `deployment.write_json`, `local.freeze(state['return_id'], state['trip']).open`, `local.freeze`.

Явные исключения: `RuntimeError`.

<a id="symbol-confirm"></a>

## confirm

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def confirm(target):
```

Уточняет готовность общей папки перед остановкой источника.

При повторе уже начатой передачи используется сохранённый номер и прежнее подтверждение.

Непосредственные вызовы: `input`, `answer.strip`, `RuntimeError`.

Явные исключения: `RuntimeError`.

<a id="symbol-deploy_connector"></a>

## deploy_connector

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def deploy_connector(local, stage):
```

Устанавливает проверенный бинарник и помощник в пути действующего коннектора.

Оставляет уже имеющийся одноимённый файл, если его содержимое совпадает.

Непосредственные вызовы: `destination.parent.mkdir`, `destination.is_symlink`, `destination.exists`, `destination.read_bytes`, `source.read_bytes`, `RuntimeError`, `str`, `destination.open`, `source.open`, `shutil.copyfileobj`, `destination.chmod`, `subprocess.run`.

Явные исключения: `RuntimeError`.

<a id="symbol-leave"></a>

## leave

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def leave(local, settings, state_file, state):
```

Переносит базу на MacBook с продолжением по тому же номеру после обрыва.

Каждый номер принимается ровно один раз, включая повтор после запуска.

Непосредственные вызовы: `remote`, `prepare`, `confirm`, `uuid.uuid4`, `deployment.write_json`, `local.check_active`, `subprocess.run`, `print`, `RuntimeError`, `local.history`, `history.mkdir`, `(history / 'installed.json').exists`, `tempfile.TemporaryFile`, `package.seek`, `local.activate`.

Явные исключения: `RuntimeError`.

<a id="symbol-main"></a>

## main

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def main():
```

Выбирает действие и защищает весь цикл переключения от запуска второй команды.

Состояние хранится на внутреннем диске MacBook вне проекта и iCloud.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `configparser.ConfigParser`, `config.read`, `dict`, `Installation`, `state_file.exists`, `json.loads`, `state_file.read_text`, `remote`, `print`, `json.dumps`, `local.status`, `os.umask`, `local.root.mkdir`, `(local.root / '.handoff-command.lock').open`, `fcntl.flock`, `RuntimeError`, `prepare`, `leave`, `back`.

Явные исключения: `RuntimeError`.

<a id="symbol-prepare"></a>

## prepare

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def prepare(local, settings, home_state):
```

Готовит MacBook с точной версией M4, штатным запуском и нативными помощниками.

Рабочая база и закрытые настройки не нужны для этой стадии.

Непосредственные вызовы: `RuntimeError`, `str`, `local.documents.is_dir`, `any`, `item.is_dir`, `item.name.startswith`, `local.documents.iterdir`, `RELEASE.fullmatch`, `socket.create_connection`, `local.lock`, `local.status`, `local.data.mkdir`, `local.stopped`, `local.stop_job`, `deployment.write_json`, `deployment.atomic_write`, `config.encode`, `(local.current / 'scripts/handoff_host.py').is_file`, `tempfile.TemporaryDirectory`, `Path`, `tempfile.TemporaryFile`, `remote`, `package.seek`, `zipfile.ZipFile`, `Bundle.read`, `json.loads`, `(app / '.manifest.json').read_text`, `(app / '.release-id').read_text().strip`, `(app / '.release-id').read_text`, `set`, `manifest['files'].items`, `(app / 'data').symlink_to`, `(app / 'manager.ini').symlink_to`, `target.parent.mkdir`, `target.exists`, `target.with_name`, `uuid.uuid4`, `app.rename`, `deploy_connector`, `temporary_link.unlink`, `temporary_link.symlink_to`, `target.relative_to`, `temporary_link.replace`, `deployment.prepare_renderers`, `local.current.resolve`, `deployment.prepare_launcher`, `write_agents`, `print`.

Явные исключения: `RuntimeError`.

<a id="symbol-remote"></a>

## remote

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def remote(settings, action, *arguments, source=None, target=None):
```

Выполняет одну команду штатного помощника на M4 с проверкой ключа SSH.

Пакет с закрытыми файлами передаётся напрямую по потокам файлов.

Непосредственные вызовы: `str`, `Path`, `shlex.join`, `json.dumps`, `subprocess.run`, `json.loads`.

Выражения возврата (ветки читаются в исходнике):

```python
json.loads(result.stdout) if target is None else None
```

<a id="symbol-write_agents"></a>

## write_agents

[scripts/handoff.py](../../../scripts/handoff.py) · `function`.

```python
def write_agents(local, launcher):
```

Сохраняет штатные пользовательские задания MacBook без их запуска.

Оба задания устанавливаются только на подготовленной выключенной машине.

Непосредственные вызовы: `local.agents.mkdir`, `logs.mkdir`, `str`, `deployment.atomic_write`, `plistlib.dumps`.
