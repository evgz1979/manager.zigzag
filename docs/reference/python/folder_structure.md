# folder_structure.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [folder_structure.py:1](../../../folder_structure.py#L1).

Recognize folder roles from names and immediate children, without reading cards.

Импорты Python, включая локальные: `datetime`, `os`, `pathlib`, `re`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## is_supplier_root

[folder_structure.py:26](../../../folder_structure.py#L26) · `function`.

```python
def is_supplier_root(name):
```

Распознаёт прежний корневой раздел поставщика по имени.

Возвращает `name.startswith('#') and name[1:].strip().casefold() == 'glass'`.

Непосредственные вызовы: `name.startswith`, `name[1:].strip().casefold`, `name[1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
name.startswith('#') and name[1:].strip().casefold() == 'glass'
```

## is_work_root

[folder_structure.py:32](../../../folder_structure.py#L32) · `function`.

```python
def is_work_root(name):
```

Распознаёт корень производства # work по имени папки.

Возвращает `name.startswith('#') and name[1:].strip().casefold() == 'work'`.

Непосредственные вызовы: `name.startswith`, `name[1:].strip().casefold`, `name[1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
name.startswith('#') and name[1:].strip().casefold() == 'work'
```

## is_moneys_root

[folder_structure.py:38](../../../folder_structure.py#L38) · `function`.

```python
def is_moneys_root(name):
```

Распознаёт финансовый корень # moneys по имени папки.

Возвращает `name.startswith('#') and name[1:].strip().casefold() == 'moneys'`.

Непосредственные вызовы: `name.startswith`, `name[1:].strip().casefold`, `name[1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
name.startswith('#') and name[1:].strip().casefold() == 'moneys'
```

## in_reconciliations

[folder_structure.py:44](../../../folder_structure.py#L44) · `function`.

```python
def in_reconciliations(relative, *, legacy=False):
```

Проверяет принадлежность пути разделу самостоятельных сверок.

Возвращает `False`; либо `len(parts) >= 2 and is_moneys_root(parts[0]) and (unicodedata.normalize('NFC', parts[1]).lstrip('#').strip().casefold() in names)`.

Непосредственные вызовы: `isinstance`, `Path`, `len`, `is_moneys_root`, `unicodedata.normalize('NFC', parts[1]).lstrip('#').strip().casefold`, `unicodedata.normalize('NFC', parts[1]).lstrip('#').strip`, `unicodedata.normalize('NFC', parts[1]).lstrip`, `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
False
len(parts) >= 2 and is_moneys_root(parts[0]) and (unicodedata.normalize('NFC', parts[1]).lstrip('#').strip().casefold() in names)
```

## is_print_section

[folder_structure.py:54](../../../folder_structure.py#L54) · `function`.

```python
def is_print_section(relative):
```

Распознаёт раздел заданий печати внутри производства.

Возвращает `len(parts) == 2 and is_work_root(parts[0]) and parts[1].startswith('#') and (parts[1][1:].strip().casefold() == 'print')`.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `parts[1].startswith`, `parts[1][1:].strip().casefold`, `parts[1][1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
len(parts) == 2 and is_work_root(parts[0]) and parts[1].startswith('#') and (parts[1][1:].strip().casefold() == 'print')
```

## in_freza

[folder_structure.py:61](../../../folder_structure.py#L61) · `function`.

```python
def in_freza(relative):
```

Распознаёт путь раздела фрезеровки или его задания.

Возвращает `len(parts) >= 2 and is_work_root(parts[0]) and parts[1].startswith('#') and (parts[1][1:].strip().casefold() == 'freza')`.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `parts[1].startswith`, `parts[1][1:].strip().casefold`, `parts[1][1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
len(parts) >= 2 and is_work_root(parts[0]) and parts[1].startswith('#') and (parts[1][1:].strip().casefold() == 'freza')
```

## is_freza_task

[folder_structure.py:68](../../../folder_structure.py#L68) · `function`.

```python
def is_freza_task(relative):
```

Распознаёт путь раздела фрезеровки или его задания.

Возвращает `in_freza(relative) and len(parts) == 3 and (not parts[2].startswith(('.', '#')))`.

Непосредственные вызовы: `Path`, `in_freza`, `len`, `parts[2].startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
in_freza(relative) and len(parts) == 3 and (not parts[2].startswith(('.', '#')))
```

## supplier_prefix

[folder_structure.py:75](../../../folder_structure.py#L75) · `function`.

```python
def supplier_prefix(relative):
```

Определяет префикс раздела поставщика в относительном пути.

Возвращает `parts[:1]`; либо `parts[:2]`.

Непосредственные вызовы: `Path`, `is_supplier_root`, `len`, `is_work_root`.

Выражения возврата (ветки читаются в исходнике):

```python
parts[:1]
parts[:2]
()
```

## section_prefix

[folder_structure.py:86](../../../folder_structure.py#L86) · `function`.

```python
def section_prefix(relative):
```

Определяет префикс выбранного служебного раздела пути.

Возвращает `parts[:1]`; либо `parts[:2]`.

Непосредственные вызовы: `Path`, `is_work_root`, `len`, `dated`, `is_moneys_root`, `supplier_prefix`.

Выражения возврата (ветки читаются в исходнике):

```python
parts[:1]
parts[:2]
supplier_prefix(relative)
```

## is_service_folder

[folder_structure.py:97](../../../folder_structure.py#L97) · `function`.

```python
def is_service_folder(relative):
```

Распознаёт служебную папку, которая не регистрируется заказом.

Возвращает `False`; либо `any((part.startswith('#') for part in parts[len(section_prefix(relative)):]))`.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `is_moneys_root`, `any`, `part.startswith`, `section_prefix`.

Выражения возврата (ветки читаются в исходнике):

```python
False
any((part.startswith('#') for part in parts[len(section_prefix(relative)):]))
```

## dated

[folder_structure.py:106](../../../folder_structure.py#L106) · `function`.

```python
def dated(name):
```

Проверяет принятую форму даты в названии папки.

Возвращает `False`; либо `day == 0`.

Непосредственные вызовы: `DATE.match`, `map`, `match.groups`, `len`, `date`.

Выражения возврата (ветки читаются в исходнике):

```python
False
day == 0
True
```

## is_catalog_group

[folder_structure.py:124](../../../folder_structure.py#L124) · `function`.

```python
def is_catalog_group(name):
```

Распознаёт числовую группу клиентов в корне документов.

Возвращает `bool(numbered and (not (dated(name) or DATE.match(name) or DATE_LIKE.match(name) or YEAR.fullmatch(name))))`.

Непосредственные вызовы: `NUMBER.match`, `re.match`, `bool`, `dated`, `DATE.match`, `DATE_LIKE.match`, `YEAR.fullmatch`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(numbered and (not (dated(name) or DATE.match(name) or DATE_LIKE.match(name) or YEAR.fullmatch(name))))
```

## grouped_client

[folder_structure.py:131](../../../folder_structure.py#L131) · `function`.

```python
def grouped_client(parts):
```

Определяет клиента с учётом корневой числовой группы.

Возвращает `False`; либо `not (dated(name) or DATE.match(name) or DATE_LIKE.match(name) or YEAR.fullmatch(name) or NUMBER.match(name))`.

Непосредственные вызовы: `len`, `is_catalog_group`, `dated`, `DATE.match`, `DATE_LIKE.match`, `YEAR.fullmatch`, `NUMBER.match`.

Выражения возврата (ветки читаются в исходнике):

```python
False
not (dated(name) or DATE.match(name) or DATE_LIKE.match(name) or YEAR.fullmatch(name) or NUMBER.match(name))
```

## client_name

[folder_structure.py:140](../../../folder_structure.py#L140) · `function`.

```python
def client_name(relative):
```

Извлекает отображаемое имя клиента из сохранённого пути.

Возвращает `parts[1] if grouped_client(parts) else parts[0] if parts else ''`.

Непосредственные вызовы: `Path`, `grouped_client`.

Выражения возврата (ветки читаются в исходнике):

```python
parts[1] if grouped_client(parts) else parts[0] if parts else ''
```

## client_path

[folder_structure.py:147](../../../folder_structure.py#L147) · `function`.

```python
def client_path(relative):
```

Определяет полный путь клиента без обращения к файловой системе.

Возвращает `''`; либо `Path(*parts[:2]).as_posix() if grouped_client(parts) and (not parts[1].startswith(('.', '#'))) else ''`.

Непосредственные вызовы: `Path`, `parts[0].startswith`, `is_catalog_group`, `grouped_client`, `parts[1].startswith`, `Path(*parts[:2]).as_posix`.

Выражения возврата (ветки читаются в исходнике):

```python
''
Path(*parts[:2]).as_posix() if grouped_client(parts) and (not parts[1].startswith(('.', '#'))) else ''
parts[0]
```

## order_location

[folder_structure.py:159](../../../folder_structure.py#L159) · `function`.

```python
def order_location(relative):
```

Вычисляет клиента и объект заказа только по сохранённому пути.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `client_path`, `len`, `parts[0].startswith`, `enumerate`, `dated`, `DATE.match`, `DATE_LIKE.match`, `name.startswith`, `YEAR.fullmatch`, `NUMBER.match`, `names.append`, `Path(*parts[:index + 1]).as_posix`, `unicodedata.normalize`, `' / '.join`.

Выражения возврата (ветки читаются в исходнике):

```python
{'client_path': unicodedata.normalize('NFC', client), 'object': unicodedata.normalize('NFC', ' / '.join(names)), 'object_path': unicodedata.normalize('NFC', object_path)}
```

## folder_role

[folder_structure.py:180](../../../folder_structure.py#L180) · `function`.

```python
def folder_role(root, relative):
```

Классифицирует роль папки для выбора доступного интерфейса и операций.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `is_moneys_root`, `in_reconciliations`, `parts[2].startswith`, `is_service_folder`, `is_catalog_group`, `dated`, `is_supplier_root`, `supplier_prefix`, `grouped_client`, `enumerate`, `DATE.match`, `DATE_LIKE.match`, `YEAR.fullmatch`, `NUMBER.match`, `Path(root).joinpath`, `os.scandir`, `entry.is_dir`, `entry.name.startswith`, `entry.is_symlink`, `any`, `child.startswith`, `re.match`, `is_print_section`, `Path(*parts[:2]).as_posix`.

Выражения возврата (ветки читаются в исходнике):

```python
{'folderKind': kind, 'folderKindLabel': LABELS[kind], 'canRegisterOrder': allowed, 'registrationHint': 'Задания печати создаются в отдельном редакторе # print. Прежняя папка сохранена для доступа к данным.' if print_archive else '' if allowed else LABELS[kind] + ' — не заказ. Выберите папку конкретного заказа по дате или номеру.'}
```
