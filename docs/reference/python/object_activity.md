# object_activity.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [object_activity.py:1](../../../object_activity.py#L1).

Object visibility using the shared SQLite activity index and legacy marker compatibility.

Импорты Python, включая локальные: `client_activity`, `folder_structure`, `os`, `pathlib`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## ObjectActivity

[object_activity.py:13](../../../object_activity.py#L13) · `class`.

```python
class ObjectActivity(ClientActivity):
```

Объединяет операции модуля: индекс неактивности объектов на основе механизма активности клиента.

Основные операции: matches, refresh.

## ObjectActivity.matches

[object_activity.py:20](../../../object_activity.py#L20) · `function`.

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

## ObjectActivity.refresh

[object_activity.py:25](../../../object_activity.py#L25) · `function`.

```python
def refresh(self):
```

Обновляет индекс из разрешённого источника данных.

Передаёт работу `os.walk`, `Path`, `name.startswith`.

Непосредственные вызовы: `os.walk`, `Path`, `name.startswith`, `folder.is_symlink`, `folder.relative_to(self.root).as_posix`, `folder.relative_to`, `folder_role`, `allowed.append`, `self.read`, `self.error`.

## ObjectActivity.refresh.on_error

[object_activity.py:29](../../../object_activity.py#L29) · `function`.

```python
def on_error(error):
```

Сохраняет ошибку обхода, не выдавая неполный результат за полный.

Передаёт работу `print`.

Непосредственные вызовы: `print`.
