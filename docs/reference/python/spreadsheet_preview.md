# spreadsheet_preview.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [spreadsheet_preview.py:1](../../../spreadsheet_preview.py#L1).

Чтение оригиналов Excel для браузерного просмотра без внешних программ.

Импорты Python, включая локальные: `icloud_access`, `pathlib`, `subprocess`, `sys`, `threading`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## read_bytes

[spreadsheet_preview.py:16](../../../spreadsheet_preview.py#L16) · `function`.

```python
def read_bytes(target):
```

Возвращает ограниченное содержимое файла после необходимых проверок.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `Path`, `target.suffix.lower`, `ValueError`, `target.is_symlink`, `target.is_file`, `target.stat`, `READ_SLOTS.acquire`, `subprocess.run`, `str`, `icloud_access.renderer`, `target.open`, `stream.read`, `len`, `READ_SLOTS.release`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
raw
```
