# native_renderers.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [native_renderers.py](../../../native_renderers.py).

Сборка Swift-помощников с постоянным путём кеша между релизами.

Импорты Python, включая локальные: `hashlib`, `pathlib`, `subprocess`, `tempfile`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-build"></a>

## build

[native_renderers.py](../../../native_renderers.py) · `function`.

```python
def build(source, data_dir, name, timeout):
```

Собирает Swift-исходник по хешу и атомарно публикует готовый бинарный файл.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `Path(source).resolve`, `Path`, `Path(data_dir).resolve`, `hashlib.sha256(source.read_bytes()).hexdigest`, `hashlib.sha256`, `source.read_bytes`, `binary.is_file`, `binary.parent.mkdir`, `tempfile.TemporaryDirectory`, `subprocess.run`, `str`, `output.replace`.

Выражения возврата (ветки читаются в исходнике):

```python
binary
```
