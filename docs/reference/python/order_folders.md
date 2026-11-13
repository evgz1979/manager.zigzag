# order_folders.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_folders.py](../../../order_folders.py).

Создание папки заказа в объекте с журналом и самостоятельным откатом.

Импорты Python, включая локальные: `datetime`, `folder_layout`, `folder_structure`, `order_creation`, `os`, `pathlib`, `re`, `threading`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-OrderFolderConflict"></a>

## OrderFolderConflict

[order_folders.py](../../../order_folders.py) · `class`.

```python
class OrderFolderConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-create"></a>

## create

[order_folders.py](../../../order_folders.py) · `function`.

```python
def create(root, relative, order_date, title, *, store=None):
```

Создаёт папку заказа или сверки и при наличии базы регистрирует карточку.

Для сверки и записи зарплаты планирует только основную папку; при конфликте останавливает создание.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `store.root.resolve`, `ValueError`, `isinstance`, `any`, `part.startswith`, `is_print_section`, `layout.safe_path`, `layout_scope`, `parent.is_dir`, `FileNotFoundError`, `folder_role`, `year_container`, `re.fullmatch`, `date.fromisoformat`, `YEAR.fullmatch`, `ord`, `unicodedata.normalize`, `title.strip`, `len`, `os.fsencode`, `year_groups`, `layout.exists`, `parent.is_symlink`, `parent.relative_to(root).as_posix`, `parent.relative_to`, `OrderFolderConflict`, `destination.relative_to(root).as_posix`, `destination.relative_to`, `layout.Plan`, `str`, `store.database.resolve`, `parent.exists`, `plan.mkdir`, `in_freza`, `in_payroll`, `(Path(path) / service).as_posix`, `layout.identity`, `(root / relative).iterdir`, `plan.create_session`, `order_creation.prepare`, `layout.apply`, `order_creation.register`, `layout.save_json`, `order_creation.failed`, `session.relative_to(root).as_posix`, `session.relative_to`, `bool`.

Явные исключения: `ValueError`, `FileNotFoundError`, `OrderFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path, 'name': name, 'journal': session.relative_to(root).as_posix(), 'registered': bool(store)}
```

<a id="symbol-create_object"></a>

## create_object

[order_folders.py](../../../order_folders.py) · `function`.

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

<a id="symbol-year_container"></a>

## year_container

[order_folders.py](../../../order_folders.py) · `function`.

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
