# thumbnail_cache.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [thumbnail_cache.py](../../../thumbnail_cache.py).

Rebuildable local thumbnail database. HTTP reads never open source files.

Импорты Python, включая локальные: `argparse`, `contextlib`, `fcntl`, `hashlib`, `json`, `native_renderers`, `os`, `pathlib`, `signal`, `sketches`, `sqlite3`, `stat`, `subprocess`, `sys`, `tempfile`, `threading`, `time`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-ThumbnailCache"></a>

## ThumbnailCache

[thumbnail_cache.py](../../../thumbnail_cache.py) · `class`.

```python
class ThumbnailCache:
```

Объединяет операции модуля: отдельная sqlite превью и контролируемый фоновый процесс генерации.

Основные операции: __init__, connect, observe, items, image; остальные описаны у методов.

<a id="symbol-ThumbnailCache.__init__"></a>

## ThumbnailCache.__init__

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def __init__(self, root, data_dir):
```

Сохраняет зависимости и начальные параметры экземпляра.

Работает с таблицами thumbnails, worker_status.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `Path(data_dir).resolve`, `ValueError`, `hashlib.sha256(str(self.root).encode()).hexdigest`, `hashlib.sha256`, `str(self.root).encode`, `str`, `self.data_dir.mkdir`, `self.connect`, `db.execute`, `db.executescript`.

Явные исключения: `ValueError`.

Прямые присваивания полям/свойствам: `self.root`, `self.data_dir`, `self.database`.

<a id="symbol-ThumbnailCache.connect"></a>

## ThumbnailCache.connect

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.

Непосредственные вызовы: `sqlite3.connect`, `db.close`.

<a id="symbol-ThumbnailCache.cover"></a>

## ThumbnailCache.cover

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def cover(self, folder):
```

Выбирает подходящую готовую обложку из сохранённого каталога превью.

Работает с таблицами thumbnails.

Непосредственные вызовы: `relative`, `self.connect`, `db.execute`, `Path(row['path']).suffix.lower`, `Path`, `dict`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(row)
{'path': '', 'signature': '', 'state': 'pending'}
```

<a id="symbol-ThumbnailCache.finish"></a>

## ThumbnailCache.finish

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def finish(self, item, image=None, mime='image/jpeg', error=''):
```

Фиксирует результат обработки задания миниатюры.

Работает с таблицами thumbnails.

Непосредственные вызовы: `time.time`, `self.connect`, `db.execute`, `min`.

<a id="symbol-ThumbnailCache.image"></a>

## ThumbnailCache.image

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def image(self, path, key=''):
```

Читает готовую миниатюру для точной версии исходного файла.

Работает с таблицами thumbnails.

Непосредственные вызовы: `self.connect`, `db.execute('SELECT signature,state,image,mime FROM thumbnails WHERE path=?', (relative(path),)).fetchone`, `db.execute`, `relative`, `bytes`.

Выражения возврата (ветки читаются в исходнике):

```python
(bytes(row['image']), row['mime'], row['signature'])
None
```

<a id="symbol-ThumbnailCache.items"></a>

## ThumbnailCache.items

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def items(self, paths):
```

Читает сохранённые элементы очереди или каталога модуля.

Работает с таблицами thumbnails.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `relative`, `self.connect`, `db.execute('SELECT path,signature,state,error FROM thumbnails WHERE path IN (' + ','.join(('?' for _ in paths)) + ')', paths).fetchall`, `db.execute`, `','.join`, `dict`, `found.get`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
[found.get(path, {'path': path, 'state': 'pending', 'signature': ''}) for path in paths]
```

<a id="symbol-ThumbnailCache.next_item"></a>

## ThumbnailCache.next_item

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def next_item(self):
```

Выбирает следующее задание фоновой генерации миниатюр.

Работает с таблицами thumbnails.

Непосредственные вызовы: `self.connect`, `db.execute("SELECT path,signature,attempts FROM thumbnails\n                WHERE state IN ('pending','error') AND retry_at<=?\n                ORDER BY priority DESC, attempts ASC, modified DESC LIMIT 1", (time.time(),)).fetchone`, `db.execute`, `time.time`, `dict`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(row) if row else None
```

<a id="symbol-ThumbnailCache.observe"></a>

## ThumbnailCache.observe

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def observe(self, entries, *, requested=False):
```

Регистрирует наблюдённые версии файлов в локальной очереди миниатюр.

Работает с таблицами thumbnails.

Непосредственные вызовы: `time.time`, `self.connect`, `relative`, `supported`, `signature`, `db.execute`.

<a id="symbol-ThumbnailCache.scan"></a>

## ThumbnailCache.scan

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def scan(self, stop):
```

Обходит разрешённые имена/метаданные для обновления фонового индекса.

Работает с таблицами thumbnails.

Непосредственные вызовы: `time.time`, `self.status`, `os.walk`, `stop.is_set`, `Path`, `name.startswith`, `(folder / name).is_symlink`, `supported`, `(folder / name).relative_to(self.root).as_posix`, `(folder / name).relative_to`, `source`, `entries.append`, `failed`, `self.observe`, `self.connect`, `db.execute`, `'; '.join`.

<a id="symbol-ThumbnailCache.scan.failed"></a>

## ThumbnailCache.scan.failed

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def failed(error):
```

Сохраняет диагностический результат неудачного фонового обхода.

Передаёт работу `errors.append`.

Непосредственные вызовы: `len`, `errors.append`, `str`.

<a id="symbol-ThumbnailCache.status"></a>

## ThumbnailCache.status

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def status(self, **values):
```

Возвращает состояние обработки и сохранённые ошибки.

Работает с таблицами worker_status, thumbnails.

Непосредственные вызовы: `self.connect`, `values.items`, `db.execute`, `json.dumps`, `json.loads`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-generate"></a>

## generate

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def generate(cache, item, binary, stop):
```

Генерирует превью поддерживаемого файла и сохраняет результат обработки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `source`, `signature`, `cache.observe`, `tempfile.TemporaryDirectory`, `Path`, `target.suffix.lower`, `run_renderer`, `str`, `sketches.embedded_preview`, `embedded.write_bytes`, `output.read_bytes`, `raw.startswith`, `len`, `ValueError`, `cache.finish`.

Явные исключения: `ValueError`.

<a id="symbol-relative"></a>

## relative

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def relative(value):
```

Преобразует путь в относительный ключ корня документов.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path`, `path.is_absolute`, `any`, `part.startswith`, `unicodedata.normalize`, `path.as_posix`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', path.as_posix())
```

<a id="symbol-renderer"></a>

## renderer

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def renderer(data_dir):
```

Получает собранный Swift-помощник для текущего исходника.

Возвращает `native_renderers.build(Path(__file__).with_name('thumbnail_preview.swift'), data_dir, 'thumbnail-renderer', 90)`.

Непосредственные вызовы: `native_renderers.build`, `Path(__file__).with_name`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
native_renderers.build(Path(__file__).with_name('thumbnail_preview.swift'), data_dir, 'thumbnail-renderer', 90)
```

<a id="symbol-run_renderer"></a>

## run_renderer

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def run_renderer(command, stop):
```

Вызывает ограниченный процесс генерации одной миниатюры.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `tempfile.TemporaryFile`, `subprocess.Popen`, `time.monotonic`, `process.poll`, `stop.wait`, `ValueError`, `errors.seek`, `errors.read(8000).decode`, `errors.read`, `next`, `line.partition`, `message.splitlines`, `line.startswith`, `process.kill`, `process.wait`.

Явные исключения: `ValueError`.

<a id="symbol-signature"></a>

## signature

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def signature(info):
```

Вычисляет отпечаток метаданных объекта для проверки свежести.

Возвращает `hashlib.sha256(value.encode()).hexdigest()`.

Непосредственные вызовы: `hashlib.sha256(value.encode()).hexdigest`, `hashlib.sha256`, `value.encode`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(value.encode()).hexdigest()
```

<a id="symbol-source"></a>

## source

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def source(root, path):
```

Проверяет исходный объект перед чтением или переносом.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `relative`, `target.is_symlink`, `ValueError`, `target.lstat`, `stat.S_ISREG`, `supported`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(target, info)
```

<a id="symbol-supervise"></a>

## supervise

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def supervise(root, data_dir, stop):
```

Поддерживает один отдельный процесс миниатюр в течение жизни сервера.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `stop.is_set`, `subprocess.Popen`, `str`, `Path(__file__).resolve`, `Path`, `os.getpid`, `process.poll`, `stop.wait`, `print`, `process.terminate`, `process.wait`, `process.kill`.

<a id="symbol-supported"></a>

## supported

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def supported(path):
```

Проверяет, поддерживается ли формат файла генератором превью.

Возвращает `path.suffix.lower() in EXTENSIONS and (path.suffix.lower() != '.cdr' or sketches.sketch_name(path.name))`.

Непосредственные вызовы: `Path`, `path.suffix.lower`, `sketches.sketch_name`.

Выражения возврата (ветки читаются в исходнике):

```python
path.suffix.lower() in EXTENSIONS and (path.suffix.lower() != '.cdr' or sketches.sketch_name(path.name))
```

<a id="symbol-worker"></a>

## worker

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def worker(cache, parent):
```

Выполняет фоновый цикл обработки с контролем остановки или паузами.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `cache.database.with_suffix('.lock').open`, `cache.database.with_suffix`, `fcntl.flock`, `threading.Event`, `signal.signal`, `threading.Thread(target=watch_parent, daemon=True).start`, `threading.Thread`, `renderer`, `threading.Thread(target=scan_loop, daemon=True).start`, `cache.status`, `os.getpid`, `stop.is_set`, `time.time`, `cache.next_item`, `stop.wait`, `generate`, `cache.finish`, `str`.

<a id="symbol-worker.scan_loop"></a>

## worker.scan_loop

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def scan_loop():
```

Периодически обновляет наблюдаемый каталог в фоновом процессе.

Передаёт работу `stop.is_set`, `cache.scan`, `cache.status().get`.

Непосредственные вызовы: `stop.is_set`, `cache.scan`, `cache.status().get`, `cache.status`, `str`, `stop.wait`.

<a id="symbol-worker.watch_parent"></a>

## worker.watch_parent

[thumbnail_cache.py](../../../thumbnail_cache.py) · `function`.

```python
def watch_parent():
```

Завершает дочерний процесс после исчезновения родительского сервера.

Передаёт работу `stop.wait`, `os.getppid`, `stop.set`.

Непосредственные вызовы: `stop.wait`, `os.getppid`, `stop.set`.
