# thumbnail_cache.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [thumbnail_cache.py:1](../../../thumbnail_cache.py#L1).

Rebuildable local thumbnail database. HTTP reads never open source files.

Импорты Python, включая локальные: `argparse`, `contextlib`, `fcntl`, `hashlib`, `json`, `native_renderers`, `os`, `pathlib`, `signal`, `sketches`, `sqlite3`, `stat`, `subprocess`, `sys`, `tempfile`, `threading`, `time`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## relative

[thumbnail_cache.py:34](../../../thumbnail_cache.py#L34) · `function`.

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

## supported

[thumbnail_cache.py:45](../../../thumbnail_cache.py#L45) · `function`.

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

## signature

[thumbnail_cache.py:52](../../../thumbnail_cache.py#L52) · `function`.

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

## source

[thumbnail_cache.py:59](../../../thumbnail_cache.py#L59) · `function`.

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

## ThumbnailCache

[thumbnail_cache.py:74](../../../thumbnail_cache.py#L74) · `class`.

```python
class ThumbnailCache:
```

Объединяет операции модуля: отдельная sqlite превью и контролируемый фоновый процесс генерации.

Основные операции: __init__, connect, observe, items, image; остальные описаны у методов.

## ThumbnailCache.__init__

[thumbnail_cache.py:77](../../../thumbnail_cache.py#L77) · `function`.

```python
def __init__(self, root, data_dir):
```

Сохраняет зависимости и начальные параметры экземпляра.

Работает с таблицами thumbnails, worker_status.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `Path(data_dir).resolve`, `ValueError`, `hashlib.sha256(str(self.root).encode()).hexdigest`, `hashlib.sha256`, `str(self.root).encode`, `str`, `self.data_dir.mkdir`, `self.connect`, `db.execute`, `db.executescript`.

Явные исключения: `ValueError`.

Прямые присваивания полям/свойствам: `self.root`, `self.data_dir`, `self.database`.

## ThumbnailCache.connect

[thumbnail_cache.py:102](../../../thumbnail_cache.py#L102) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.

Непосредственные вызовы: `sqlite3.connect`, `db.close`.

## ThumbnailCache.observe

[thumbnail_cache.py:113](../../../thumbnail_cache.py#L113) · `function`.

```python
def observe(self, entries, *, requested=False):
```

Регистрирует наблюдённые версии файлов в локальной очереди миниатюр.

Работает с таблицами thumbnails.

Непосредственные вызовы: `time.time`, `self.connect`, `relative`, `supported`, `signature`, `db.execute`.

## ThumbnailCache.items

[thumbnail_cache.py:134](../../../thumbnail_cache.py#L134) · `function`.

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

## ThumbnailCache.image

[thumbnail_cache.py:149](../../../thumbnail_cache.py#L149) · `function`.

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

## ThumbnailCache.cover

[thumbnail_cache.py:158](../../../thumbnail_cache.py#L158) · `function`.

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

## ThumbnailCache.next_item

[thumbnail_cache.py:171](../../../thumbnail_cache.py#L171) · `function`.

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

## ThumbnailCache.finish

[thumbnail_cache.py:180](../../../thumbnail_cache.py#L180) · `function`.

```python
def finish(self, item, image=None, mime='image/jpeg', error=''):
```

Фиксирует результат обработки задания миниатюры.

Работает с таблицами thumbnails.

Непосредственные вызовы: `time.time`, `self.connect`, `db.execute`, `min`.

## ThumbnailCache.status

[thumbnail_cache.py:191](../../../thumbnail_cache.py#L191) · `function`.

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

## ThumbnailCache.scan

[thumbnail_cache.py:202](../../../thumbnail_cache.py#L202) · `function`.

```python
def scan(self, stop):
```

Обходит разрешённые имена/метаданные для обновления фонового индекса.

Работает с таблицами thumbnails.

Непосредственные вызовы: `time.time`, `self.status`, `os.walk`, `stop.is_set`, `Path`, `name.startswith`, `(folder / name).is_symlink`, `supported`, `(folder / name).relative_to(self.root).as_posix`, `(folder / name).relative_to`, `source`, `entries.append`, `failed`, `self.observe`, `self.connect`, `db.execute`, `'; '.join`.

## ThumbnailCache.scan.failed

[thumbnail_cache.py:209](../../../thumbnail_cache.py#L209) · `function`.

```python
def failed(error):
```

Сохраняет диагностический результат неудачного фонового обхода.

Передаёт работу `errors.append`.

Непосредственные вызовы: `len`, `errors.append`, `str`.

## renderer

[thumbnail_cache.py:242](../../../thumbnail_cache.py#L242) · `function`.

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

## run_renderer

[thumbnail_cache.py:248](../../../thumbnail_cache.py#L248) · `function`.

```python
def run_renderer(command, stop):
```

Вызывает ограниченный процесс генерации одной миниатюры.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `tempfile.TemporaryFile`, `subprocess.Popen`, `time.monotonic`, `process.poll`, `stop.wait`, `ValueError`, `errors.seek`, `errors.read(8000).decode`, `errors.read`, `next`, `line.partition`, `message.splitlines`, `line.startswith`, `process.kill`, `process.wait`.

Явные исключения: `ValueError`.

## generate

[thumbnail_cache.py:270](../../../thumbnail_cache.py#L270) · `function`.

```python
def generate(cache, item, binary, stop):
```

Генерирует превью поддерживаемого файла и сохраняет результат обработки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `source`, `signature`, `cache.observe`, `tempfile.TemporaryDirectory`, `Path`, `target.suffix.lower`, `run_renderer`, `str`, `sketches.embedded_preview`, `embedded.write_bytes`, `output.read_bytes`, `raw.startswith`, `len`, `ValueError`, `cache.finish`.

Явные исключения: `ValueError`.

## worker

[thumbnail_cache.py:299](../../../thumbnail_cache.py#L299) · `function`.

```python
def worker(cache, parent):
```

Выполняет фоновый цикл обработки с контролем остановки или паузами.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `cache.database.with_suffix('.lock').open`, `cache.database.with_suffix`, `fcntl.flock`, `threading.Event`, `signal.signal`, `threading.Thread(target=watch_parent, daemon=True).start`, `threading.Thread`, `renderer`, `threading.Thread(target=scan_loop, daemon=True).start`, `cache.status`, `os.getpid`, `stop.is_set`, `time.time`, `cache.next_item`, `stop.wait`, `generate`, `cache.finish`, `str`.

## worker.watch_parent

[thumbnail_cache.py:312](../../../thumbnail_cache.py#L312) · `function`.

```python
def watch_parent():
```

Завершает дочерний процесс после исчезновения родительского сервера.

Передаёт работу `stop.wait`, `os.getppid`, `stop.set`.

Непосредственные вызовы: `stop.wait`, `os.getppid`, `stop.set`.

## worker.scan_loop

[thumbnail_cache.py:319](../../../thumbnail_cache.py#L319) · `function`.

```python
def scan_loop():
```

Периодически обновляет наблюдаемый каталог в фоновом процессе.

Передаёт работу `stop.is_set`, `cache.scan`, `cache.status().get`.

Непосредственные вызовы: `stop.is_set`, `cache.scan`, `cache.status().get`, `cache.status`, `str`, `stop.wait`.

## supervise

[thumbnail_cache.py:351](../../../thumbnail_cache.py#L351) · `function`.

```python
def supervise(root, data_dir, stop):
```

Поддерживает один отдельный процесс миниатюр в течение жизни сервера.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `stop.is_set`, `subprocess.Popen`, `str`, `Path(__file__).resolve`, `Path`, `os.getpid`, `process.poll`, `stop.wait`, `print`, `process.terminate`, `process.wait`, `process.kill`.
