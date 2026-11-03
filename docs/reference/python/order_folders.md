# order_folders.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [order_folders.py:1](../../../order_folders.py#L1).

Создание папки заказа в объекте с журналом и самостоятельным откатом.

Импорты Python, включая локальные: `datetime`, `folder_layout`, `folder_structure`, `order_creation`, `os`, `pathlib`, `re`, `threading`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## OrderFolderConflict

[order_folders.py:17](../../../order_folders.py#L17) · `class`.

```python
class OrderFolderConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## layout_scope

[order_folders.py:23](../../../order_folders.py#L23) · `function`.

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

## year_container

[order_folders.py:30](../../../order_folders.py#L30) · `function`.

```python
def year_container(root, relative):
```

Распознаёт контейнер года внутри объекта клиента.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `bool`, `YEAR.fullmatch`, `folder_role`, `Path(relative).parent.as_posix`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(parts and YEAR.fullmatch(parts[-1]) and (folder_role(root, relative)['folderKind'] == 'year') and (folder_role(root, Path(relative).parent.as_posix())['folderKind'] == 'object'))
```

## year_groups

[order_folders.py:38](../../../order_folders.py#L38) · `function`.

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

## create_object

[order_folders.py:47](../../../order_folders.py#L47) · `function`.

```python
def create_object(root, relative, title):
```

Создаёт объект клиента после проверки имени и отсутствия назначения.

При недопустимом состоянии возбуждает ValueError, OrderFolderConflict.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `isinstance`, `any`, `p.startswith`, `ValueError`, `ord`, `unicodedata.normalize`, `title.strip`, `name.startswith`, `len`, `os.fsencode`, `YEAR.fullmatch`, `DATE.match`, `DATE_LIKE.match`, `NUMBER.match`, `layout.safe_path`, `parent.is_dir`, `folder_role`, `(Path(relative) / name).as_posix`, `layout.exists`, `OrderFolderConflict`, `layout.Plan`, `plan.mkdir`, `plan.create_session`, `layout.identity`, `layout.apply`, `layout.save_json`, `session.relative_to(root).as_posix`, `session.relative_to`.

Явные исключения: `ValueError`, `OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path, 'name': name, 'journal': session.relative_to(root).as_posix()}
```

## create

[order_folders.py:76](../../../order_folders.py#L76) · `function`.

```python
def create(root, relative, order_date, title, *, store=None):
```

Создаёт новый объект после проверки области и входных данных.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError, OrderFolderConflict.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `store.root.resolve`, `ValueError`, `isinstance`, `any`, `part.startswith`, `is_print_section`, `layout.safe_path`, `layout_scope`, `parent.is_dir`, `FileNotFoundError`, `folder_role`, `year_container`, `re.fullmatch`, `date.fromisoformat`, `YEAR.fullmatch`, `ord`, `unicodedata.normalize`, `title.strip`, `len`, `os.fsencode`, `year_groups`, `layout.exists`, `parent.is_symlink`, `parent.relative_to(root).as_posix`, `parent.relative_to`, `OrderFolderConflict`, `destination.relative_to(root).as_posix`, `destination.relative_to`, `layout.Plan`, `str`, `store.database.resolve`, `in_reconciliations`, `parent.exists`, `plan.mkdir`, `in_freza`, `(Path(path) / service).as_posix`, `layout.identity`, `(root / relative).iterdir`, `plan.create_session`, `order_creation.prepare`, `layout.apply`, `order_creation.register`, `layout.save_json`, `order_creation.failed`, `session.relative_to(root).as_posix`, `session.relative_to`, `bool`.

Явные исключения: `ValueError`, `FileNotFoundError`, `OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path, 'name': name, 'journal': session.relative_to(root).as_posix(), 'registered': bool(store)}
```
