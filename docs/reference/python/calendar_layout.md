# calendar_layout.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_layout.py](../../../calendar_layout.py).

Manual calendar placement, independent of dates, deadlines and finances.

Импорты Python, включая локальные: `json`, `local_metadata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-mark_contract"></a>

## mark_contract

[calendar_layout.py](../../../calendar_layout.py) · `function`.

```python
def mark_contract(db):
```

Фиксирует в настройках базы использование несовместимого со старым кодом формата.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `schema`, `db.execute`.

<a id="symbol-read_compact"></a>

## read_compact

[calendar_layout.py](../../../calendar_layout.py) · `function`.

```python
def read_compact(blocks):
```

Читает строгую отметку мелкого заказа из дополнительных блоков.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`.

Выражения возврата (ветки читаются в исходнике):

```python
False
None
value['enabled']
```

<a id="symbol-write_compact"></a>

## write_compact

[calendar_layout.py](../../../calendar_layout.py) · `function`.

```python
def write_compact(blocks, enabled):
```

Сериализует известную отметку мелкого заказа без замены неизвестного формата.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `type`, `ValueError`, `read_compact`, `json.dumps`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, COMPACT_BLOCK: json.dumps({'version': 1, 'enabled': enabled}, ensure_ascii=False)}
```
