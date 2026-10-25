"""Rebuildable local thumbnail database. HTTP reads never open source files."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

import native_renderers
import sketches

FORMAT = 1
SCAN_INTERVAL = 300
RENDER_TIMEOUT = 35
EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.gif', '.heic', '.heif', '.webp', '.avif', '.tif', '.tiff', '.bmp', '.svg',
    '.mov', '.mp4', '.m4v', '.webm', '.avi', '.pdf', '.cdr', '.ai', '.eps', '.psd', '.dxf',
    '.doc', '.docx', '.rtf', '.xls', '.xlsx', '.xlsm', '.xlsb', '.ppt', '.pptx', '.txt', '.md', '.csv',
})


def relative(value):
    if not isinstance(value, str) or not value or '\x00' in value:
        raise ValueError('Укажи путь файла')
    path = Path(value)
    if path.is_absolute() or any(part in {'.', '..'} or part.startswith('.') for part in path.parts):
        raise ValueError('Скрытые файлы и пути вне документов недоступны')
    return unicodedata.normalize('NFC', path.as_posix())


def supported(path):
    path = Path(path)
    return path.suffix.lower() in EXTENSIONS and (path.suffix.lower() != '.cdr' or sketches.sketch_name(path.name))


def signature(info):
    value = f'{FORMAT}:{info.st_dev}:{info.st_ino}:{info.st_size}:{info.st_mtime_ns}'
    return hashlib.sha256(value.encode()).hexdigest()


def source(root, path):
    """Check every path component without following links, including inside root."""
    target = Path(root)
    for part in Path(relative(path)).parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('Символические ссылки не сканируются')
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or not supported(target):
        raise ValueError('Миниатюра для этого файла недоступна')
    return target, info


class ThumbnailCache:
    def __init__(self, root, data_dir):
        self.root = Path(root).resolve()
        self.data_dir = Path(data_dir).resolve()
        if self.data_dir == self.root or self.root in self.data_dir.parents:
            raise ValueError('База превью должна храниться вне каталога документов')
        digest = hashlib.sha256(str(self.root).encode()).hexdigest()[:16]
        self.database = self.data_dir / f'thumbnails-{digest}.sqlite3'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS thumbnails (
                    path TEXT PRIMARY KEY, signature TEXT NOT NULL, modified REAL NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending', image BLOB, mime TEXT,
                    priority REAL NOT NULL DEFAULT 0, seen REAL NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0, retry_at REAL NOT NULL DEFAULT 0,
                    error TEXT NOT NULL DEFAULT '', updated REAL NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS thumbnail_queue ON thumbnails(state, retry_at, priority, modified);
                CREATE TABLE IF NOT EXISTS worker_status (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def observe(self, entries, *, requested=False):
        now = time.time()
        with self.connect() as db:
            for path, info in entries:
                path = relative(path)
                if not supported(path):
                    continue
                key = signature(info)
                db.execute('''INSERT INTO thumbnails(path,signature,modified,seen,priority) VALUES (?,?,?,?,?)
                    ON CONFLICT(path) DO UPDATE SET
                        state=CASE WHEN signature!=excluded.signature OR state='missing' THEN 'pending' ELSE state END,
                        image=CASE WHEN signature!=excluded.signature THEN NULL ELSE image END,
                        attempts=CASE WHEN signature!=excluded.signature THEN 0 ELSE attempts END,
                        retry_at=CASE WHEN signature!=excluded.signature THEN 0 ELSE retry_at END,
                        error=CASE WHEN signature!=excluded.signature THEN '' ELSE error END,
                        signature=excluded.signature, modified=excluded.modified, seen=excluded.seen,
                        priority=MAX(priority, excluded.priority)''',
                           (path, key, info.st_mtime, now, now if requested else 0))

    def items(self, paths):
        if not isinstance(paths, list) or len(paths) > 120:
            raise ValueError('Запроси не больше 120 превью')
        paths = [relative(path) for path in paths]
        if not paths:
            return []
        with self.connect() as db:
            rows = db.execute('SELECT path,signature,state,error FROM thumbnails WHERE path IN (' +
                              ','.join('?' for _ in paths) + ')', paths).fetchall()
            # Polling must not reset backoff or move a failed file ahead of all other work.
        found = {row['path']: dict(row) for row in rows}
        return [found.get(path, {'path': path, 'state': 'pending', 'signature': ''}) for path in paths]

    def image(self, path, key=''):
        with self.connect() as db:
            row = db.execute("SELECT signature,state,image,mime FROM thumbnails WHERE path=?", (relative(path),)).fetchone()
        if row and row['state'] == 'ready' and row['image'] and (not key or row['signature'] == key):
            return bytes(row['image']), row['mime'], row['signature']
        return None

    def cover(self, folder):
        prefix = relative(folder) + '/'
        with self.connect() as db:
            rows = db.execute("""SELECT path,signature,state FROM thumbnails WHERE path>=? AND path<?
                              AND state!='missing' ORDER BY (state='ready') DESC, modified DESC""",
                              (prefix, prefix + '\U0010ffff'))
            for row in rows:
                if Path(row['path']).suffix.lower() in {'.png', '.jpg', '.jpeg', '.heic', '.heif', '.tif', '.tiff', '.bmp', '.webp', '.cdr'}:
                    return dict(row)
        return {'path': '', 'signature': '', 'state': 'pending'}

    def next_item(self):
        with self.connect() as db:
            row = db.execute("""SELECT path,signature,attempts FROM thumbnails
                WHERE state IN ('pending','error') AND retry_at<=?
                ORDER BY priority DESC, attempts ASC, modified DESC LIMIT 1""", (time.time(),)).fetchone()
        return dict(row) if row else None

    def finish(self, item, image=None, mime='image/jpeg', error=''):
        now = time.time()
        with self.connect() as db:
            db.execute('''UPDATE thumbnails SET state=?,image=?,mime=?,error=?,attempts=attempts+1,
                       retry_at=?,updated=? WHERE path=? AND signature=?''',
                       ('error' if error else 'ready', image, mime, error[:1000],
                        now + min(3600, 60 * 2 ** min(item['attempts'], 6)) if error else 0,
                        now, item['path'], item['signature']))

    def status(self, **values):
        with self.connect() as db:
            for key, value in values.items():
                db.execute('INSERT OR REPLACE INTO worker_status VALUES (?,?)', (key, json.dumps(value)))
            result = {row['key']: json.loads(row['value']) for row in db.execute('SELECT * FROM worker_status')}
            result['counts'] = {row['state']: row['count'] for row in db.execute(
                'SELECT state,COUNT(*) AS count FROM thumbnails GROUP BY state')}
        return result

    def scan(self, stop):
        started = time.time()
        errors = []
        self.status(scan_started=started, scan_error='')

        def failed(error):
            if len(errors) < 10:
                errors.append(str(error))

        for current, dirs, names in os.walk(self.root, followlinks=False, onerror=failed):
            if stop.is_set():
                return
            folder = Path(current)
            dirs[:] = [name for name in dirs if not name.startswith('.') and not (folder / name).is_symlink()]
            entries = []
            for name in names:
                if stop.is_set():
                    return
                if name.startswith(('.', '~')) or name in {'!.txt', '!order.txt', '!status.txt'} or not supported(name):
                    continue
                path = (folder / name).relative_to(self.root).as_posix()
                try:
                    _, info = source(self.root, path)
                    entries.append((path, info))
                except ValueError:
                    continue
                except OSError as error:
                    failed(error)
            self.observe(entries)
        # An unavailable directory must never make its previous thumbnails disappear.
        if not errors:
            with self.connect() as db:
                db.execute("UPDATE thumbnails SET state='missing',image=NULL WHERE seen<? AND state!='missing'", (started,))
        self.status(last_scan=time.time(), scan_error='; '.join(errors))


def renderer(data_dir):
    return native_renderers.build(Path(__file__).with_name('thumbnail_preview.swift'), data_dir, 'thumbnail-renderer', 90)


def run_renderer(command, stop):
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=errors)
        deadline = time.monotonic() + RENDER_TIMEOUT
        try:
            while process.poll() is None:
                if stop.wait(0.2) or time.monotonic() >= deadline:
                    raise ValueError('iCloud или просмотр файла пока недоступен; повторим автоматически')
            if process.returncode:
                errors.seek(0)
                message = errors.read(8000).decode('utf-8', errors='replace')
                clean = next((line.partition('ZIGZAG_THUMBNAIL_ERROR: ')[2] for line in message.splitlines()
                              if line.startswith('ZIGZAG_THUMBNAIL_ERROR: ')), '')
                raise ValueError(clean or 'Не удалось создать превью; повторим автоматически')
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()


def generate(cache, item, binary, stop):
    target, info = source(cache.root, item['path'])
    if signature(info) != item['signature']:
        cache.observe([(item['path'], info)])
        return
    with tempfile.TemporaryDirectory(prefix='.thumbnail-', dir=cache.data_dir) as staging:
        staging = Path(staging)
        output = staging / 'preview.jpg'
        if target.suffix.lower() == '.cdr':
            copied = staging / 'source.cdr'
            run_renderer([str(binary), str(target), str(copied), str(staging), 'copy'], stop)
            raw = sketches.embedded_preview(copied, allow_bmp=True)
            embedded = staging / ('embedded.bmp' if raw[:2] == b'BM' else 'embedded.png')
            embedded.write_bytes(raw)
            run_renderer([str(binary), str(embedded), str(output), str(staging)], stop)
        else:
            run_renderer([str(binary), str(target), str(output), str(staging)], stop)
        raw = output.read_bytes()
        if not raw.startswith(b'\xff\xd8\xff') or not 100 < len(raw) <= 2 * 1024 * 1024:
            raise ValueError('Некорректная миниатюра')
        _, after = source(cache.root, item['path'])
        if signature(after) != item['signature']:
            cache.observe([(item['path'], after)])
            return
        cache.finish(item, raw)


def worker(cache, parent):
    # A lock spans the worker lifetime, including overlapping service restarts.
    with cache.database.with_suffix('.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        stop = threading.Event()
        for number in (signal.SIGTERM, signal.SIGINT):
            signal.signal(number, lambda *_: stop.set())

        def watch_parent():
            while not stop.wait(1):
                if os.getppid() != parent:
                    stop.set()

        def scan_loop():
            while not stop.is_set():
                try:
                    cache.scan(stop)
                    delay = 60 if cache.status().get('scan_error') else SCAN_INTERVAL
                except Exception as error:
                    cache.status(scan_error=str(error))
                    delay = 60
                stop.wait(delay)

        threading.Thread(target=watch_parent, daemon=True).start()
        binary = renderer(cache.data_dir)
        threading.Thread(target=scan_loop, daemon=True).start()
        cache.status(pid=os.getpid(), running=True)
        try:
            while not stop.is_set():
                cache.status(heartbeat=time.time())
                item = cache.next_item()
                if not item:
                    stop.wait(1)
                    continue
                try:
                    generate(cache, item, binary, stop)
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    cache.finish(item, error=str(error))
                stop.wait(0.1)
        finally:
            cache.status(running=False, heartbeat=time.time())


def supervise(root, data_dir, stop):
    """Keep one separate low-priority process alive for this server lifetime."""
    while not stop.is_set():
        process = None
        try:
            process = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()),
                                        '--root', str(root), '--data-dir', str(data_dir), '--parent', str(os.getpid())])
            while process.poll() is None and not stop.wait(1):
                pass
        except OSError as error:
            print(f'Не удалось запустить кеш превью: {error}', file=sys.stderr, flush=True)
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        stop.wait(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--parent', required=True, type=int)
    arguments = parser.parse_args()
    os.nice(10)
    worker(ThumbnailCache(arguments.root, arguments.data_dir), arguments.parent)
