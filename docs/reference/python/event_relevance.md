# event_relevance.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [event_relevance.py](../../../event_relevance.py).

Актуальность события — независимый читаемый блок карточки папки.

Импорты Python, включая локальные: `folder_structure`, `pathlib`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-info"></a>

## info

[event_relevance.py](../../../event_relevance.py) · `function`.

```python
def info(record, error=''):
```

Формирует представление состояния и ошибок для интерфейса.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `read`.

Выражения возврата (ветки читаются в исходнике):

```python
{'value': value, 'revision': record['revision'] if record else None, 'sync_pending': record['sync_pending'] if record else False, 'sync_error': record['sync_error'] if record else '', 'error': error or (f'Проверьте раздел [{BLOCK}] в !.txt события' if record and value is None else '')}
```

<a id="symbol-is_event"></a>

## is_event

[event_relevance.py](../../../event_relevance.py) · `function`.

```python
def is_event(path, owner):
```

Проверяет, является ли папка непосредственным событием заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path(path).parent.as_posix`, `Path`, `is_service_folder`, `any`, `part.startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
Path(path).parent.as_posix() == owner and (not is_service_folder(path)) and (not any((part.startswith('.') for part in Path(path).parts)))
```

<a id="symbol-read"></a>

## read

[event_relevance.py](../../../event_relevance.py) · `function`.

```python
def read(blocks):
```

Сопоставляет текст блока актуальности с известным состоянием события.

Возвращает `'none' if body is None else next((key for (key, label) in LABELS.items() if body.strip() == label), None)`.

Непосредственные вызовы: `blocks.get`, `next`, `LABELS.items`, `body.strip`.

Выражения возврата (ветки читаются в исходнике):

```python
'none' if body is None else next((key for (key, label) in LABELS.items() if body.strip() == label), None)
```

<a id="symbol-write"></a>

## write

[event_relevance.py](../../../event_relevance.py) · `function`.

```python
def write(blocks, value):
```

Меняет только известный блок актуальности папки события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `', '.join`, `LABELS.values`, `read`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, BLOCK: LABELS[value]}
```
