# image_reports.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [image_reports.py](../../../image_reports.py).

Image/comment PDFs generated with macOS, published without overwriting files.

Импорты Python, включая локальные: `datetime`, `folder_layout`, `json`, `native_renderers`, `os`, `pathlib`, `shutil`, `subprocess`, `tempfile`, `threading`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-create"></a>

## create

[image_reports.py](../../../image_reports.py) · `function`.

```python
def create(folder, items, app_dir, data_dir):
```

Создаёт PDF-отчёт выбранных изображений и сохранённых комментариев.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `Path`, `cache.mkdir`, `tempfile.TemporaryDirectory`, `manifest.write_text`, `json.dumps`, `subprocess.run`, `str`, `renderer`, `json.loads`, `output.open`, `stream.read`, `isinstance`, `len`, `ValueError`, `error.stderr.decode('utf-8', errors='replace').strip`, `error.stderr.decode`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `datetime.now`, `ZoneInfo`, `tempfile.NamedTemporaryFile`, `shutil.copyfileobj`, `stream.flush`, `os.fsync`, `stream.fileno`, `rename_exclusive`, `temporary.unlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(target, pages)
```

<a id="symbol-renderer"></a>

## renderer

[image_reports.py](../../../image_reports.py) · `function`.

```python
def renderer(app_dir, data_dir):
```

Получает собранный Swift-помощник для текущего исходника.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `native_renderers.build`, `Path`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
native_renderers.build(Path(app_dir) / 'image_report.swift', data_dir, 'image-report', 90)
```
