# inbox_folder.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [inbox_folder.py](../../../inbox_folder.py).

Count direct Inbox files without opening documents or walking subfolders.

Импорты Python, включая локальные: `os`, `pathlib`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-snapshot"></a>

## snapshot

[inbox_folder.py](../../../inbox_folder.py) · `function`.

```python
def snapshot(root):
```

Считает только непосредственные видимые обычные файлы единственной папки Inbox.

Возвращает `{'path': '', 'count': 0, 'error': ''}`; либо `{'path': '', 'count': None, 'error': 'Найдено несколько папок #inbox'}`.

Непосредственные вызовы: `Path`, `os.scandir`, `entry.name.startswith`, `unicodedata.normalize('NFC', entry.name[1:]).casefold().strip`, `unicodedata.normalize('NFC', entry.name[1:]).casefold`, `unicodedata.normalize`, `entry.is_dir`, `len`, `sum`, `entry.is_file`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': '', 'count': 0, 'error': ''}
{'path': '', 'count': None, 'error': 'Найдено несколько папок #inbox'}
{'path': name, 'count': count, 'error': ''}
{'path': '', 'count': None, 'error': 'Не удалось проверить папку #inbox. Повторим автоматически'}
```
