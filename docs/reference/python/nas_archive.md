# nas_archive.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [nas_archive.py](../../../nas_archive.py).

Archive folders on the server's mounted SMB share.

Импорты Python, включая локальные: `contextlib`, `errno`, `hashlib`, `json`, `local_metadata`, `order_folders`, `os`, `pathlib`, `re`, `subprocess`, `threading`, `unicodedata`, `urllib.parse`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-archive"></a>

## archive

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def archive(store, relative, payload=None, *, open_finder=False):
```

Читает, открывает или меняет # nas по проверенному пути заказа.

Привязка хранит исходный относительный путь, перемещения заказа обновляют её ключ в SQLite.

Непосредственные вызовы: `nullcontext`, `unicodedata.normalize`, `store.path`, `store.target`, `order_folders.can_manage_service_folders`, `store.require_order_folder`, `ValueError`, `order_folders.service_parent_key`, `target.stat`, `settings`, `MetadataStore`, `metadata.get`, `binding.get`, `Path`, `type`, `payload.get`, `metadata.connect`, `db.execute("SELECT 1 FROM metadata_records WHERE kind=? AND path<>? AND json_extract(data,'$.archive')=?", (BINDING, relative, archive_path)).fetchone`, `db.execute`, `order_folders.OrderFolderConflict`, `mounted_root`, `archive_state`, `hashlib.sha256(json.dumps([*revision_input, key]).encode()).hexdigest`, `hashlib.sha256`, `json.dumps([*revision_input, key]).encode`, `json.dumps`, `store.target(relative).stat`, `audit`, `metadata.put`, `descend`, `os.mkdir`, `os.rmdir`, `quote`, `'/'.join`, `str`, `mounted_path.joinpath`, `subprocess.run`, `isinstance`.

Явные исключения: `ValueError`, `order_folders.OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{**state, 'reason': reason}
{'enabled': enabled, 'revision': revision, 'reason': reason, 'url': url, 'finder_path': finder_path}
```

<a id="symbol-archive_state"></a>

## archive_state

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def archive_state(directory, parts):
```

Читает наличие и пустоту конечной папки архива без обхода файлов.

Любая непосредственная запись, в том числе скрытая, блокирует выключение.

Непосредственные вызовы: `descend`, `os.fstat`, `os.scandir`, `next`, `order_folders.service_parent_key`.

Выражения возврата (ветки читаются в исходнике):

```python
(True, f'{order_folders.service_parent_key(info)}:{info.st_ctime_ns}', reason)
(False, '', '')
(False, '', 'На пути к архиву есть файл или ссылка')
```

<a id="symbol-descend"></a>

## descend

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def descend(directory, parts, *, create=False):
```

Открывает компоненты пути по дескриптору того же сетевого тома.

Ссылки и переход на другое устройство запрещены, создание разрешено только по явному запросу.

Непосредственные вызовы: `os.dup`, `os.fstat`, `os.open`, `os.mkdir`, `os.close`, `OSError`.

Явные исключения: `OSError`.

<a id="symbol-mounted_root"></a>

## mounted_root

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def mounted_root(path):
```

Открывает настроенный архивный корень по настоящему SMB-монтированию.

Передаёт дескриптор, устройство, путь Finder и SMB-адрес существующего корня.

Непосредственные вызовы: `Path`, `mounted_volume`, `os.open`, `os.fstat`, `OSError`, `descend`, `volume.joinpath`, `quote`, `'/'.join`, `os.close`.

Явные исключения: `OSError`.

<a id="symbol-mounted_volume"></a>

## mounted_volume

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def mounted_volume(name):
```

Находит конкретный SMB-том в таблице монтирования macOS.

Возвращает путь, устройство и адрес SMB без имени пользователя и пароля.

Непосредственные вызовы: `subprocess.run`, `listing.stdout.splitlines`, `line.rpartition`, `source.startswith`, `source[2:].partition`, `host.rsplit`, `re.sub`, `re.fullmatch`, `target.stat`, `VOLUMES.stat`, `quote`, `unquote`, `FileNotFoundError`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
(target, device, f'smb://{host}/' + quote(unquote(share), safe='/'))
```

<a id="symbol-root_path"></a>

## root_path

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def root_path(value):
```

Нормализует адрес архивного корня в формате /Том/Папка.

Принимает только компоненты сетевого тома без переходов и управляющих символов.

Непосредственные вызовы: `isinstance`, `ValueError`, `unicodedata.normalize`, `value.strip().rstrip`, `value.strip`, `value[1:].split`, `value.startswith`, `len`, `any`, `os.fsencode`, `ord`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-settings"></a>

## settings

[nas_archive.py](../../../nas_archive.py) · `function`.

```python
def settings(store, payload=None):
```

Читает или сохраняет общий адрес SMB-архива в SQLite.

Проверяет ожидаемую версию и пишет историю, сохранение адреса само папок не создаёт.

Непосредственные вызовы: `MetadataStore`, `nullcontext`, `metadata.get`, `type`, `record.get`, `ValueError`, `root_path`, `payload.get`, `metadata.connect`, `audit`, `metadata.put`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'root': root_path(record.get('root')) if record else DEFAULT_ROOT, 'revision': record['revision'] if record else 'missing'}
```
