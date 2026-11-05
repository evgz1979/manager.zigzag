# work_order_list.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [work_order_list.py](../../../work_order_list.py).

Production order tables in #work and individual supplier sections.

Импорты Python, включая локальные: `event_folder_undo`, `folder_structure`, `json`, `object_orders`, `pathlib`, `work_orders`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-WorkOrderList"></a>

## WorkOrderList

[work_order_list.py](../../../work_order_list.py) · `class`.

```python
class WorkOrderList(ObjectOrders):
```

Объединяет операции модуля: sqlite-каталог производственных заказов и поставщиков.

Основные операции: path, sections, allowed_paths, refresh, read.

<a id="symbol-WorkOrderList.allowed_paths"></a>

## WorkOrderList.allowed_paths

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def allowed_paths(self, relative, inactive=(), show_inactive=False):
```

Вычисляет допустимые пути текущего списка из сохранённого каталога.

Возвращает `lambda path: canonical(Path(path).parent.as_posix()) == relative and (not Path(path).name.startswith(('.', '#')))`; либо `allowed`.

Непосредственные вызовы: `supplier_scope`, `self.sections`.

Выражения возврата (ветки читаются в исходнике):

```python
lambda path: canonical(Path(path).parent.as_posix()) == relative and (not Path(path).name.startswith(('.', '#')))
allowed
```

<a id="symbol-WorkOrderList.allowed_paths.allowed"></a>

## WorkOrderList.allowed_paths.allowed

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def allowed(path):
```

Проверяет допустимость одной папки в текущем каталоге.

Возвращает `False`; либо `len(parts) == 2 and dated(parts[1]) or (len(parts) == 3 and Path(path).parent.as_posix() in sections)`.

Непосредственные вызовы: `canonical`, `Path`, `parts[-1].startswith`, `len`, `dated`, `Path(path).parent.as_posix`.

Выражения возврата (ветки читаются в исходнике):

```python
False
len(parts) == 2 and dated(parts[1]) or (len(parts) == 3 and Path(path).parent.as_posix() in sections)
```

<a id="symbol-WorkOrderList.path"></a>

## WorkOrderList.path

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def path(self, relative):
```

Проверяет относительный путь внутри допустимой области.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `canonical`, `self.store.path`, `len`, `Path`, `is_work_root`, `supplier_scope`, `ValueError`, `guard_database`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
relative
```

<a id="symbol-WorkOrderList.read"></a>

## WorkOrderList.read

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def read(self, relative, **kwargs):
```

Собирает список производства, группы и статусы из SQLite.

Работает с таблицами metadata_history.

Непосредственные вызовы: `super().read`, `super`, `self.store.connect`, `Path(row['path']).name.lstrip('#').strip`, `Path(row['path']).name.lstrip`, `Path`, `work_orders.supplier_color`, `self.sections`, `work_orders.folder_date`, `work_orders.supplier_name`, `colors.get`, `canonical`, `Path(order['path']).parent.as_posix`, `work_orders.status_order`, `work_orders.read_status`, `work_orders.archived`, `work_orders.archive_time`, `db.execute`, `json.loads`, `sorted`, `result['orders'].sort`, `supplier_scope`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-WorkOrderList.refresh"></a>

## WorkOrderList.refresh

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def refresh(self, relative):
```

Обновляет разрешённый каталог непосредственных производственных заказов.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.store.path`, `self.path`, `self.store.target`, `self.allowed_paths`, `set`, `self.sections`, `list`, `target.iterdir`, `len`, `ValueError`, `child.name.startswith`, `child.is_symlink`, `child.is_dir`, `child.relative_to(self.store.root).as_posix`, `child.relative_to`, `allowed`, `found.add`, `canonical`, `child.iterdir`, `order.relative_to(self.store.root).as_posix`, `order.relative_to`, `order.is_symlink`, `order.is_dir`, `errors.append`, `str`, `self.save_catalog`.

Явные исключения: `ValueError`.

<a id="symbol-WorkOrderList.sections"></a>

## WorkOrderList.sections

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def sections(self, relative):
```

Читает сохранённые разделы производственного каталога.

Возвращает `[{'path': relative}]`.

Непосредственные вызовы: `supplier_scope`, `work_orders.read_supplier_favorites`, `sorted`, `records.values`, `is_print_section`.

Выражения возврата (ветки читаются в исходнике):

```python
[{'path': relative}]
sorted((row for row in records.values() if row['is_favorite'] is True and (not is_print_section(row['path']))), key=lambda row: (work_orders.is_etc_section(row['path']), row['position'], row['path']))
```

<a id="symbol-supplier_scope"></a>

## supplier_scope

[work_order_list.py](../../../work_order_list.py) · `function`.

```python
def supplier_scope(relative):
```

Определяет область текущего списка поставщика.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `is_print_section`, `in_freza`, `len`, `is_supplier_root`, `is_work_root`, `dated`, `parts[1].startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
not is_print_section(relative) and (not in_freza(relative)) and (len(parts) == 1 and is_supplier_root(parts[0]) or (len(parts) == 2 and is_work_root(parts[0]) and (not dated(parts[1])) and (not parts[1].startswith('.'))))
```
