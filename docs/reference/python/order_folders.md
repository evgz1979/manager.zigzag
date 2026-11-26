# order_folders.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_folders.py](../../../order_folders.py).

Создание заказа и управление его непосредственными служебными папками.

Импорты Python, включая локальные: `datetime`, `errno`, `event_folder_undo`, `folder_layout`, `folder_structure`, `order_creation`, `os`, `pathlib`, `re`, `stat`, `threading`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-OrderFolderConflict"></a>

## OrderFolderConflict

[order_folders.py](../../../order_folders.py) · `class`.

```python
class OrderFolderConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-can_manage_service_folders"></a>

## can_manage_service_folders

[order_folders.py](../../../order_folders.py) · `function`.

```python
def can_manage_service_folders(relative, role):
```

Проверяет доступность переключателей для непосредственного заказа клиента.

Учитывает клиентов в числовых группах и готовую роль папки.

Непосредственные вызовы: `bool`, `client_path`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(client_path(relative)) and role['canRegisterOrder']
```

<a id="symbol-create"></a>

## create

[order_folders.py](../../../order_folders.py) · `function`.

```python
def create(root, relative, order_date, title, *, store=None):
```

Создаёт папку заказа или сверки и при наличии базы регистрирует карточку.

В группе годов имя равно названию; для сверки и зарплаты планирует только основную папку.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `store.root.resolve`, `ValueError`, `isinstance`, `any`, `part.startswith`, `is_print_section`, `layout.safe_path`, `layout_scope`, `parent.is_dir`, `FileNotFoundError`, `folder_role`, `year_container`, `is_catalog_year`, `re.fullmatch`, `date.fromisoformat`, `YEAR.fullmatch`, `ord`, `unicodedata.normalize`, `title.strip`, `title.startswith`, `len`, `os.fsencode`, `year_groups`, `layout.exists`, `parent.is_symlink`, `parent.relative_to(root).as_posix`, `parent.relative_to`, `OrderFolderConflict`, `destination.relative_to(root).as_posix`, `destination.relative_to`, `layout.Plan`, `str`, `store.database.resolve`, `parent.exists`, `plan.mkdir`, `in_freza`, `in_payroll`, `(Path(path) / service).as_posix`, `layout.identity`, `(root / relative).iterdir`, `summary.insert`, `plan.create_session`, `order_creation.prepare`, `layout.apply`, `order_creation.register`, `layout.save_json`, `order_creation.failed`, `session.relative_to(root).as_posix`, `session.relative_to`, `bool`.

Явные исключения: `ValueError`, `FileNotFoundError`, `OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path, 'name': name, 'journal': session.relative_to(root).as_posix(), 'registered': bool(store)}
```

<a id="symbol-create_client"></a>

## create_client

[order_folders.py](../../../order_folders.py) · `function`.

```python
def create_client(store, relative, title):
```

Создаёт пустую папку клиента в корне документов или выбранной группе клиентов.

Использует общий план создания контейнера с журналом и откатом.

Непосредственные вызовы: `create_client_container`.

Выражения возврата (ветки читаются в исходнике):

```python
create_client_container(store.root, relative, title, 'client', database=store.database)
```

<a id="symbol-create_client_container"></a>

## create_client_container

[order_folders.py](../../../order_folders.py) · `function`.

```python
def create_client_container(root, relative, title, kind, *, database=None):
```

Создаёт клиентский контейнер по роли родителя и безопасному имени.

План работает без перезаписи, регистрации заказа и создания служебных папок.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `isinstance`, `any`, `p.startswith`, `ValueError`, `ord`, `unicodedata.normalize`, `title.strip`, `name.startswith`, `len`, `os.fsencode`, `YEAR.fullmatch`, `DATE.match`, `DATE_LIKE.match`, `NUMBER.match`, `is_catalog_group`, `(Path(relative) / name).as_posix`, `guard_database`, `layout.safe_path`, `parent.is_dir`, `folder_role`, `(role['catalogGroup'] or {}).get`, `layout.exists`, `OrderFolderConflict`, `layout.Plan`, `plan.mkdir`, `plan.create_session`, `layout.identity`, `layout.apply`, `layout.save_json`, `session.relative_to(root).as_posix`, `session.relative_to`.

Явные исключения: `ValueError`, `OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path, 'name': name, 'journal': session.relative_to(root).as_posix()}
```

<a id="symbol-create_object"></a>

## create_object

[order_folders.py](../../../order_folders.py) · `function`.

```python
def create_object(root, relative, title):
```

Создаёт объект клиента после проверки имени и отсутствия назначения.

При недопустимом состоянии возбуждает ValueError, OrderFolderConflict.

Непосредственные вызовы: `create_client_container`.

Выражения возврата (ветки читаются в исходнике):

```python
create_client_container(root, relative, title, 'object')
```

<a id="symbol-layout_scope"></a>

## layout_scope

[order_folders.py](../../../order_folders.py) · `function`.

```python
def layout_scope(relative):
```

Проверяет допустимую клиентскую область для создания папок.

Возвращает `{'service_roots': [Path(*prefix).as_posix()]} if prefix else {}`.

Непосредственные вызовы: `section_prefix`, `Path(*prefix).as_posix`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
{'service_roots': [Path(*prefix).as_posix()]} if prefix else {}
```

<a id="symbol-service_folder_state"></a>

## service_folder_state

[order_folders.py](../../../order_folders.py) · `function`.

```python
def service_folder_state(directory):
```

Читает семь переключателей из непосредственных записей открытой папки заказа.

Проверяет пустоту по первой записи, включая скрытые файлы, ссылки и подпапки.

Непосредственные вызовы: `os.scandir`, `entry.name.startswith`, `entry.name[1:].strip().casefold`, `entry.name[1:].strip`, `matches[kind].append`, `entry.stat`, `matches.items`, `any`, `stat.S_ISDIR`, `len`, `service_parent_key`, `os.open`, `next`, `os.close`, `folders.append`, `os.fstat`.

Выражения возврата (ветки читаются в исходнике):

```python
{'parent': service_parent_key(os.fstat(directory)), 'folders': folders}
```

<a id="symbol-service_folders"></a>

## service_folders

[order_folders.py](../../../order_folders.py) · `function`.

```python
def service_folders(store, relative, change=None, *, role=None):
```

Читает или меняет одну служебную папку клиентского заказа.

Сверяет снимок и использует mkdir/rmdir относительно открытой папки без рекурсивного удаления.

Непосредственные вызовы: `store.path`, `store.target`, `can_manage_service_folders`, `folder_role`, `ValueError`, `guard_database`, `change.get`, `type`, `os.open`, `service_folder_state`, `next`, `OrderFolderConflict`, `os.mkdir`, `os.rmdir`, `os.close`.

Явные исключения: `ValueError`, `OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
snapshot
service_folder_state(directory)
```

<a id="symbol-service_parent_key"></a>

## service_parent_key

[order_folders.py](../../../order_folders.py) · `function`.

```python
def service_parent_key(info):
```

Формирует идентификатор открытого заказа для проверки перед записью.

Изменение содержимого папки сохраняет идентификатор, замена папки меняет его.

Непосредственные вызовы: `getattr`.

Выражения возврата (ветки читаются в исходнике):

```python
f"{info.st_dev}:{info.st_ino}:{getattr(info, 'st_birthtime', '')}"
```

<a id="symbol-year_container"></a>

## year_container

[order_folders.py](../../../order_folders.py) · `function`.

```python
def year_container(root, relative):
```

Распознаёт контейнер года, в котором можно создать заказ.

В группе годов проверяет явный тип; в объекте проверяет роли года и его родителя.

Непосредственные вызовы: `is_catalog_year`, `Path`, `bool`, `YEAR.fullmatch`, `folder_role`, `Path(relative).parent.as_posix`.

Выражения возврата (ветки читаются в исходнике):

```python
True
bool(parts and YEAR.fullmatch(parts[-1]) and (folder_role(root, relative)['folderKind'] == 'year') and (folder_role(root, Path(relative).parent.as_posix())['folderKind'] == 'object'))
```

<a id="symbol-year_groups"></a>

## year_groups

[order_folders.py](../../../order_folders.py) · `function`.

```python
def year_groups(root, relative):
```

Читает допустимые группы годов выбранного объекта.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `parent.iterdir`, `YEAR.fullmatch`, `item.is_symlink`, `item.is_dir`, `folder_role`, `item.relative_to(root).as_posix`, `item.relative_to`.

Выражения возврата (ветки читаются в исходнике):

```python
[item.name for item in parent.iterdir() if YEAR.fullmatch(item.name) and (not item.is_symlink()) and item.is_dir() and (folder_role(root, item.relative_to(root).as_posix())['folderKind'] == 'year')]
```
