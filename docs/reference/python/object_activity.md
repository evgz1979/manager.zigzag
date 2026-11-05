# object_activity.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [object_activity.py](../../../object_activity.py).

Object visibility using the shared SQLite activity index and legacy marker compatibility.

Импорты Python, включая локальные: `client_activity`, `folder_structure`, `os`, `pathlib`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-ObjectActivity"></a>

## ObjectActivity

[object_activity.py](../../../object_activity.py) · `class`.

```python
class ObjectActivity(ClientActivity):
```

Объединяет операции модуля: индекс неактивности объектов на основе механизма активности клиента.

Основные операции: matches, refresh.

<a id="symbol-ObjectActivity.matches"></a>

## ObjectActivity.matches

[object_activity.py](../../../object_activity.py) · `function`.

```python
def matches(self, path):
```

Проверяет соответствие папки роли индексируемой сущности.

Возвращает `folder_role(self.root, path)['folderKind'] == 'object'`.

Непосредственные вызовы: `folder_role`.

Выражения возврата (ветки читаются в исходнике):

```python
folder_role(self.root, path)['folderKind'] == 'object'
```

<a id="symbol-ObjectActivity.refresh"></a>

## ObjectActivity.refresh

[object_activity.py](../../../object_activity.py) · `function`.

```python
def refresh(self):
```

Обновляет индекс из разрешённого источника данных.

Передаёт работу `os.walk`, `Path`, `name.startswith`.

Непосредственные вызовы: `os.walk`, `Path`, `name.startswith`, `folder.is_symlink`, `folder.relative_to(self.root).as_posix`, `folder.relative_to`, `folder_role`, `allowed.append`, `self.read`, `self.error`.

<a id="symbol-ObjectActivity.refresh.on_error"></a>

## ObjectActivity.refresh.on_error

[object_activity.py](../../../object_activity.py) · `function`.

```python
def on_error(error):
```

Сохраняет ошибку обхода, не выдавая неполный результат за полный.

Передаёт работу `print`.

Непосредственные вызовы: `print`.
