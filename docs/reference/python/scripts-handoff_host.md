# scripts/handoff_host.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/handoff_host.py](../../../scripts/handoff_host.py).

Принимает и передаёт рабочую установку менеджера между двумя Mac.

Импорты Python, включая локальные: `configparser`, `contextlib`, `deploy_remote`, `fcntl`, `hashlib`, `http.client`, `json`, `os`, `pathlib`, `plistlib`, `re`, `remote_access`, `shutil`, `socket`, `sqlite3`, `subprocess`, `sys`, `tempfile`, `time`, `urllib.request`, `zipfile`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Bundle"></a>

## Bundle

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `class`.

```python
class Bundle:
```

Считывает и записывает ZIP одного направления без распаковки произвольных путей.

Получатель проверяет SHA-256 всех файлов и допускает только ожидаемый состав.

<a id="symbol-Bundle.digest"></a>

## Bundle.digest

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def digest(stream):
```

Вычисляет SHA-256 содержимого небольшого файла или открытого потока.

Читает блоками по одному мегабайту до конца потока.

Непосредственные вызовы: `hashlib.sha256`, `iter`, `value.update`, `value.hexdigest`.

Выражения возврата (ветки читаются в исходнике):

```python
value.hexdigest()
```

<a id="symbol-Bundle.read"></a>

## Bundle.read

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def read(cls, archive, directory, allowed):
```

Извлекает только разрешённые обычные файлы в отдельную закрытую папку.

Проверяет состав, пути, типы, размер и хеш каждого распакованного файла.

Непосредственные вызовы: `json.loads`, `archive.read`, `set`, `archive.namelist`, `len`, `archive.infolist`, `RuntimeError`, `any`, `allowed`, `sum`, `shutil.disk_usage`, `files.items`, `name.split`, `target.parent.mkdir`, `archive.open`, `target.open`, `shutil.copyfileobj`, `stream.flush`, `os.fsync`, `stream.fileno`, `cls.digest`, `os.chmod`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
metadata
```

<a id="symbol-Bundle.write"></a>

## Bundle.write

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def write(cls, path, metadata, files):
```

Записывает закрытый ZIP с SHA-256 и публикует его атомарно.

Незавершённый временный файл можно заменить при повторе операции.

Непосредственные вызовы: `path.with_suffix`, `zipfile.ZipFile`, `files.items`, `source.open`, `cls.digest`, `archive.write`, `archive.writestr`, `json.dumps`, `os.chmod`, `temporary.open`, `os.fsync`, `stream.fileno`, `temporary.replace`.

<a id="symbol-Installation"></a>

## Installation

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `class`.

```python
class Installation:
```

Управляет одной рабочей установкой и её сохранёнными этапами передачи.

Использует существующие launchd, SQLite-снимки, настройки и релизы.

<a id="symbol-Installation.__init__"></a>

## Installation.__init__

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def __init__(self, settings, documents, role):
```

Определяет локальные пути, порты, роль машины и имя SQLite.

MacBook и M4 должны использовать одинаковый абсолютный путь iCloud.

Непосредственные вызовы: `Path(settings['directory']).expanduser().resolve`, `Path(settings['directory']).expanduser`, `Path`, `Path(documents).expanduser().resolve`, `Path(documents).expanduser`, `int`, `deployment.database_name`, `Path.home`, `str`, `os.getuid`.

Прямые присваивания полям/свойствам: `self.root`, `self.documents`, `self.python`, `self.port`, `self.host`, `self.role`, `self.data`, `self.database`, `self.parked`, `self.current`, `self.home`, `self.support`, `self.domain`, `self.agents`.

<a id="symbol-Installation.activate"></a>

## Installation.activate

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def activate(self, identity, trip, archive):
```

Устанавливает полученную базу ровно один раз и подтверждает оба входа.

При повторе после запуска сохраняет изменения, сделанные на новой машине.

Непосредственные вызовы: `self.lock`, `self.history`, `history.mkdir`, `self.status`, `receipt.exists`, `json.loads`, `receipt.read_text`, `RuntimeError`, `tempfile.TemporaryDirectory`, `Path`, `zipfile.ZipFile`, `Bundle.read`, `set`, `received['files'].keys`, `str`, `self.check_database`, `self.stopped`, `self.install_files`, `deployment.write_json`, `self.parked.exists`, `self.parked.read_text`, `self.parked.unlink`, `self.start_job`, `self.check_service`, `self.check_public`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.status()
```

<a id="symbol-Installation.bootstrap"></a>

## Installation.bootstrap

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def bootstrap(self, output):
```

Проверяет рабочий корень и исходные файлы активного релиза перед переездом.

Отправляет только файлы, перечисленные в проверенном манифесте деплоя.

Непосредственные вызовы: `self.status`, `RELEASE.fullmatch`, `RuntimeError`, `str`, `self.documents.is_dir`, `json.loads`, `manifest_path.read_text`, `(self.current / 'scripts/handoff_host.py').is_file`, `sources.update`, `Bundle.write`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.check_active"></a>

## Installation.check_active

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def check_active(self):
```

Печатает состояние сетевых входов для проверки перед передачей.

Требует подтверждения точного релиза и обоих защищённых маршрутов.

Непосредственные вызовы: `self.status`, `RuntimeError`, `self.check_service`, `self.check_public`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
state
```

<a id="symbol-Installation.check_database"></a>

## Installation.check_database

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def check_database(database):
```

Проверяет незавершённые файловые намерения и целостность SQLite-снимка.

Очереди публикации и прочие сохранённые данные переносятся в исходном виде.

Непосредственные вызовы: `closing`, `sqlite3.connect`, `database.as_uri`, `db.execute('PRAGMA integrity_check').fetchall`, `db.execute`, `RuntimeError`, `db.execute(f'SELECT 1 FROM {table} WHERE {condition} LIMIT 1').fetchone`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.check_public"></a>

## Installation.check_public

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def check_public(self, state):
```

Проверяет, что прежний HTTPS-адрес отвечает с принимающей машины.

Использует короткую штатную сессию в памяти, без вывода или записи подписи.

Непосредственные вызовы: `sys.path.insert`, `str`, `self.current.resolve`, `settings`, `PasswordGate`, `gate.token`, `gate.document`, `time.monotonic`, `urllib.request.urlopen`, `response.geturl`, `RuntimeError`, `http.client.HTTPSConnection`, `connection.request`, `connection.getresponse`, `json.load`, `value.get`, `socket.gethostname`, `connection.close`, `time.sleep`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.check_service"></a>

## Installation.check_service

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def check_service(self, state):
```

Проверяет номер релиза, корень документов и защищённый локальный слушатель.

Открывает дерево самим сервером и проверяет, что внешний API требует входа.

Непосредственные вызовы: `time.monotonic`, `deployment.health`, `str`, `RuntimeError`, `urllib.request.urlopen`, `json.load`, `http.client.HTTPConnection`, `connection.request`, `connection.getresponse`, `connection.close`, `time.sleep`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.check_source"></a>

## Installation.check_source

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def check_source(self, state):
```

Проверяет, что активная база соответствует пути в конфигурации приложения.

Обнаруживает отсутствующую базу до остановки рабочего сервера.

Непосредственные вызовы: `RELEASE.fullmatch`, `str`, `RuntimeError`, `self.database.is_file`, `self.database.is_symlink`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.freeze"></a>

## Installation.freeze

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def freeze(self, identity, trip):
```

Останавливает источник и публикует неизменяемый снимок указанной передачи.

После публикации источник остаётся выключенным до получения обратной передачи.

Непосредственные вызовы: `self.lock`, `self.history`, `history.mkdir`, `self.status`, `RuntimeError`, `archive.exists`, `self.check_source`, `deployment.write_json`, `self.stop_job`, `self.stopped`, `snapshot.unlink`, `deployment.backup_database`, `self.check_database`, `configparser.ConfigParser`, `config.read`, `Path(config.get('remote_access', 'credentials_file', fallback=str(self.support / PROFILE))).expanduser`, `Path`, `config.get`, `str`, `profile.resolve`, `(self.data / name).is_file`, `any`, `path.is_symlink`, `path.is_file`, `files.values`, `Bundle.write`, `self.loaded`, `self.parked.unlink`, `self.start_job`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
archive
```

<a id="symbol-Installation.history"></a>

## Installation.history

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def history(self, identity):
```

Возвращает папку передачи по проверенному идентификатору.

Вызывать после блокировки установки при записи.

Непосредственные вызовы: `TRANSFER.fullmatch`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.root / '.handoffs' / identity
```

<a id="symbol-Installation.install_files"></a>

## Installation.install_files

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def install_files(self, history, stage):
```

Сохраняет прежнюю SQLite с её журналами, затем атомарно ставит проверенные файлы.

Копия прежней базы создаётся один раз и остаётся доступной после прерывания.

Непосредственные вызовы: `(saved / 'ready').exists`, `saved.mkdir`, `self.database.with_name`, `path.exists`, `path.open`, `temporary.open`, `shutil.copyfileobj`, `target.flush`, `os.fsync`, `target.fileno`, `temporary.replace`, `deployment.atomic_write`, `self.database.with_name(self.database.name + suffix).unlink`, `self.support.mkdir`, `destination.parent.mkdir`, `destination.is_symlink`, `RuntimeError`, `path.read_bytes`, `destination.unlink`, `(stage / 'snapshot.sqlite3').replace`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.loaded"></a>

## Installation.loaded

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def loaded(self, label):
```

Проверяет регистрацию заданного задания launchd текущего пользователя.

Использует только метки менеджера и его туннеля.

Непосредственные вызовы: `deployment.launchctl`.

Выражения возврата (ветки читаются в исходнике):

```python
deployment.launchctl('print', self.domain + '/' + label, check=False).returncode == 0
```

<a id="symbol-Installation.lock"></a>

## Installation.lock

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def lock(self):
```

Защищает операции с установкой от параллельного деплоя и другой передачи.

Запись выполняется под закрытой маской файлов и общей блокировкой.

Непосредственные вызовы: `os.umask`, `self.root.mkdir`, `(self.root / '.deploy.lock').open`, `fcntl.flock`.

<a id="symbol-Installation.start_job"></a>

## Installation.start_job

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def start_job(self, label):
```

Запускает существующее задание launchd, если оно ещё не загружено.

Состояние enable сохраняется для входа в сеанс macOS.

Непосредственные вызовы: `self.loaded`, `deployment.launchctl`, `str`.

<a id="symbol-Installation.status"></a>

## Installation.status

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def status(self):
```

Читает текущее состояние установки и параметры защищённого слушателя.

Удалённый ответ содержит только проверенные эксплуатационные поля.

Непосредственные вызовы: `configparser.ConfigParser`, `config.read`, `str`, `release_file.is_file`, `release_file.read_text().strip`, `release_file.read_text`, `self.parked.exists`, `json.loads`, `self.parked.read_text`, `self.loaded`, `config.get`, `config.getint`, `config.getboolean`, `Path(config.get('storage', 'root', fallback='/')).expanduser().resolve`, `Path(config.get('storage', 'root', fallback='/')).expanduser`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
{'documents': str(self.documents), 'directory': str(self.root), 'release': release_file.read_text().strip() if release_file.is_file() else '', 'parked': json.loads(self.parked.read_text()) if self.parked.exists() else None, 'manager': self.loaded(deployment.LABEL), 'tunnel': self.loaded(TUNNEL), 'public_host': config.get('remote_access', 'public_host', fallback=''), 'remote_port': config.getint('remote_access', 'port', fallback=0), 'configured_remote': config.getboolean('remote_access', 'enabled', fallback=False), 'config_root': str(Path(config.get('storage', 'root', fallback='/')).expandus...
```

<a id="symbol-Installation.stop_job"></a>

## Installation.stop_job

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def stop_job(self, label):
```

Отключает автоматический запуск, выгружает задание и ждёт его остановки.

Сохраняет plist для следующего переключения.

Непосредственные вызовы: `deployment.launchctl`, `self.loaded`, `range`, `time.sleep`, `RuntimeError`.

Явные исключения: `RuntimeError`.

<a id="symbol-Installation.stopped"></a>

## Installation.stopped

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def stopped(self, remote_port, *, drain=False):
```

Проверяет, что ни один прежний сервер не удерживает SQLite или сетевой порт.

Блокировка остаётся у вызывающего кода на весь период остановки или установки базы.

Непосредственные вызовы: `(self.data / '.handoff-run.lock').open`, `self.loaded`, `deployment.launchctl`, `time.monotonic`, `fcntl.flock`, `RuntimeError`, `time.sleep`, `self.stop_job`, `socket.socket`, `probe.connect_ex`.

Явные исключения: `RuntimeError`.

<a id="symbol-main"></a>

## main

[scripts/handoff_host.py](../../../scripts/handoff_host.py) · `function`.

```python
def main():
```

Выполняет одну строго заданную операцию на M4 через SSH.

Бинарные пакеты передаёт по stdin/stdout без вывода файлов настроек в журнал.

Непосредственные вызовы: `json.loads`, `Installation`, `print`, `json.dumps`, `installation.status`, `installation.check_active`, `installation.lock`, `tempfile.TemporaryDirectory`, `Path`, `installation.bootstrap`, `path.open`, `shutil.copyfileobj`, `installation.freeze`, `os.umask`, `tempfile.TemporaryFile`, `stream.seek`, `installation.activate`, `ValueError`.

Явные исключения: `ValueError`.
