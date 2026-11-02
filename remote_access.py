"""Password gate on a separate loopback listener; the LAN handler is unchanged."""
import configparser
import hashlib
import hmac
import html
import json
import math
import os
import re
import secrets
import stat
import threading
import time
import urllib.parse
from collections import deque
from http.server import ThreadingHTTPServer
from pathlib import Path

REMOTE_ACCESS_VERSION = 1
ITERATIONS = 600_000
SESSION_SECONDS = 30 * 86400
LOGIN_SECONDS = 600
SESSION_COOKIE = '__Host-zigzag-session'
LOGIN_COOKIE = '__Host-zigzag-login'
LOGIN_PATH = '/_auth/login'
DEFAULT_CREDENTIALS = Path.home() / '.local/share/manager-remote-access/password.json'


def password_document(password):
    if not isinstance(password, str) or not 12 <= len(password) <= 1024 or '\x00' in password:
        raise ValueError('Используй пароль от 12 до 1024 символов')
    salt = secrets.token_bytes(32)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return {'version': 1, 'algorithm': 'pbkdf2-sha256', 'iterations': ITERATIONS,
            'salt': salt.hex(), 'digest': digest.hex(), 'signing_key': secrets.token_hex(32)}


def save_password(path, password):
    """Initial creation only. Never replace an existing/unknown credential file."""
    document = password_document(password)
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or path.parent.stat().st_mode & 0o077:
        raise ValueError('Каталог пароля должен быть закрыт для других пользователей')
    body = (json.dumps(document) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def settings(config_file):
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file, encoding='utf-8')
    if not config.getboolean('remote_access', 'enabled', fallback=False):
        return None
    host = config.get('remote_access', 'public_host', fallback='').strip().lower()
    if not re.fullmatch(r'[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?', host) or '.' not in host:
        raise ValueError('Укажи имя внешнего сайта без протокола и порта')
    port = config.getint('remote_access', 'port', fallback=18767)
    if not 1 <= port <= 65535 or port == config.getint('server', 'port', fallback=8765):
        raise ValueError('Для внешнего входа нужен отдельный порт')
    credentials = Path(config.get('remote_access', 'credentials_file', fallback=str(DEFAULT_CREDENTIALS))).expanduser()
    if not credentials.is_absolute():
        raise ValueError('Для пароля нужен абсолютный путь вне документов')
    return {'public_host': host, 'port': port, 'credentials_file': credentials}


class PasswordGate:
    def __init__(self, path, public_host, clock=time.time):
        self.path = Path(path)
        self.public_host = public_host
        self.clock = clock
        self.lock = threading.Lock()
        self.attempts = deque()
        self.verifying = threading.BoundedSemaphore(1)

    def document(self):
        # Open without following links and check the opened inode, not a prior stat.
        fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 4096:
                raise ValueError('Недоступные настройки внешнего входа')
            value = json.loads(stream.read(4097))
        if (not isinstance(value, dict) or set(value) != {'version', 'algorithm', 'iterations', 'salt', 'digest', 'signing_key'}
                or type(value['version']) is not int or value['version'] != 1
                or value['algorithm'] != 'pbkdf2-sha256' or type(value['iterations']) is not int or value['iterations'] != ITERATIONS
                or any(not isinstance(value[name], str) or not re.fullmatch('[0-9a-f]{64}', value[name])
                       for name in ('salt', 'digest', 'signing_key'))):
            raise ValueError('Неизвестные настройки внешнего входа')
        return value

    def key(self, document):
        # Changing either the password or signing key invalidates every session.
        return hmac.digest(bytes.fromhex(document['signing_key']), bytes.fromhex(document['digest']), 'sha256')

    def token(self, document, kind, lifetime):
        now = int(self.clock())
        value = f'1.{kind}.{now}.{now + lifetime}.{secrets.token_hex(16)}'
        return value + '.' + hmac.new(self.key(document), value.encode(), hashlib.sha256).hexdigest()

    def valid(self, document, token, kind):
        if not isinstance(token, str) or len(token) > 220:
            return False
        match = re.fullmatch(r'1\.(session|login)\.([0-9]{1,12})\.([0-9]{1,12})\.[0-9a-f]{32}\.[0-9a-f]{64}', token)
        if not match or match[1] != kind:
            return False
        issued, expires, now = int(match[2]), int(match[3]), self.clock()
        limit = SESSION_SECONDS if kind == 'session' else LOGIN_SECONDS
        if issued > now + 60 or not issued < expires or expires <= now or expires - issued > limit:
            return False
        value, signature = token.rsplit('.', 1)
        expected = hmac.new(self.key(document), value.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def retry_after(self):
        # Global, bounded limiter: proxy/client IP headers cannot bypass it.
        with self.lock:
            now = self.clock()
            while self.attempts and self.attempts[0] <= now - 60:
                self.attempts.popleft()
            if len(self.attempts) >= 10:
                return max(1, math.ceil(60 - (now - self.attempts[0])))
            self.attempts.append(now)
        return 0


def cookie(handler, name):
    matches = []
    for header in handler.headers.get_all('Cookie', []):
        for part in header.split(';'):
            key, separator, value = part.strip().partition('=')
            if separator and key == name:
                matches.append(value)
    return matches[0] if len(matches) == 1 else ''


def safe_next(value):
    if (not isinstance(value, str) or len(value) > 3072 or not value.startswith('/') or value.startswith('//')
            or '\\' in value or any(ord(char) < 32 or ord(char) == 127 for char in value)
            or urllib.parse.urlsplit(value).path.startswith('/_auth/')):
        return '/'
    return urllib.parse.quote(value, safe='/%?&#=:+,;@!$()*-._~')


def cookie_header(name, value, lifetime=None):
    result = f'{name}={value}; Path=/; Secure; HttpOnly; SameSite=Lax'
    return result if lifetime is None else result + f'; Max-Age={lifetime}'


class RemoteHTTPServer(ThreadingHTTPServer):
    """Bound concurrent requests so anonymous clients cannot create unlimited threads."""
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(64)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


def handler_class(base_handler):
    class RemoteHandler(base_handler):
        # This class is used only by the separate 127.0.0.1 listener. Never infer
        # local trust from Host, X-Forwarded-For, CF-Connecting-IP or client IP.
        def setup(self):
            super().setup()
            self.connection.settimeout(20)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('CDN-Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Strict-Transport-Security', 'max-age=31536000')
            super().end_headers()

        def reply(self, status, body=b'', content_type='text/html; charset=utf-8', headers=()):
            self.close_connection = True
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            for name, value in headers:
                self.send_header(name, value)
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def context(self):
            gate = self.server.password_gate
            hosts = self.headers.get_all('Host', [])
            if len(hosts) != 1 or hosts[0].lower() not in {gate.public_host, gate.public_host + ':443'}:
                self.reply(421, 'Неверный адрес сайта'.encode())
                return None
            try:
                document = gate.document()
            except (OSError, ValueError, UnicodeError):
                self.reply(503, 'Внешний вход ещё не настроен'.encode())
                return None
            return gate, document

        def same_origin(self):
            origins = self.headers.get_all('Origin', [])
            host = self.server.password_gate.public_host
            return len(origins) == 1 and origins[0] in {'https://' + host, 'https://' + host + ':443'}

        def authenticated(self, gate, document):
            return gate.valid(document, cookie(self, SESSION_COOKIE), 'session')

        def denied(self):
            if urllib.parse.urlsplit(self.path).path.startswith('/api/') or self.path.startswith('/_auth/session') or self.command == 'POST':
                self.reply(401, json.dumps({'error': 'Нужен вход в менеджер', 'login_required': True}).encode(),
                           'application/json; charset=utf-8', [('X-Manager-Login', 'required')])
            else:
                self.reply(303, headers=[('Location', LOGIN_PATH + '?' + urllib.parse.urlencode({'next': safe_next(self.path)}))])

        def login_page(self, gate, document, error='', status=200, retry=0):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            destination = safe_next(query.get('next', ['/'])[0])
            csrf = gate.token(document, 'login', LOGIN_SECONDS)
            nonce = secrets.token_urlsafe(24)
            body = f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход · Зигзаг</title>
<style nonce="{nonce}">*{{box-sizing:border-box}}body{{margin:0;min-height:100dvh;display:grid;place-items:center;padding:24px;background:#f7f9f8;color:#263738;font:15px -apple-system,BlinkMacSystemFont,sans-serif}}main{{width:100%;max-width:360px;background:white;border:1px solid #e0e7e4;border-radius:16px;padding:28px}}h1{{font-size:24px;margin:0 0 24px}}label{{display:block}}input[type=password]{{width:100%;font:16px -apple-system,BlinkMacSystemFont,sans-serif;padding:12px;border:1px solid #bdccc6;border-radius:8px;margin:8px 0 16px}}button{{width:100%;border:0;border-radius:8px;background:#167a65;color:white;padding:13px;font:16px -apple-system,BlinkMacSystemFont,sans-serif;margin-top:22px;cursor:pointer}}.remember{{font-size:13px;color:#667570;display:flex;gap:8px;align-items:center}}.error{{color:#b13535;font-size:13px}}input:focus-visible,button:focus-visible{{outline:3px solid #76bcaa;outline-offset:2px}}</style>
<main><h1>Зигзаг · Вход</h1><form method="post" action="https://{gate.public_host}{LOGIN_PATH}"><input type="hidden" name="username" autocomplete="username" value="manager"><input type="hidden" name="csrf" value="{csrf}"><input type="hidden" name="next" value="{html.escape(destination, quote=True)}"><label for="password">Пароль<input id="password" name="password" type="password" autocomplete="current-password" required maxlength="1024" autofocus></label><label class="remember"><input type="checkbox" name="remember" value="1" checked>Запомнить на этом устройстве</label><p class="error" role="alert">{html.escape(error)}</p><button type="submit">Войти</button></form></main>
<script nonce="{nonce}">document.querySelector('form').addEventListener('submit',()=>{{let n=document.querySelector('[name=next]');if(location.hash&&!n.value.includes('#'))n.value+=location.hash}});</script></html>'''.encode()
            headers = [('Set-Cookie', cookie_header(LOGIN_COOKIE, csrf, LOGIN_SECONDS)),
                       ('Content-Security-Policy', f"default-src 'none'; style-src 'nonce-{nonce}'; script-src 'nonce-{nonce}'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")]
            if retry:
                headers.append(('Retry-After', str(retry)))
            self.reply(status, body, headers=headers)

        def get_remote(self):
            context = self.context()
            if not context:
                return
            gate, document = context
            route = urllib.parse.urlsplit(self.path).path
            logged_in = self.authenticated(gate, document)
            if route == LOGIN_PATH:
                if logged_in:
                    self.reply(303, headers=[('Location', '/')])
                else:
                    self.login_page(gate, document)
            elif not logged_in:
                self.denied()
            elif route == '/_auth/session':
                token = cookie(self, SESSION_COOKIE)
                csrf = hmac.new(gate.key(document), ('logout:' + token).encode(), hashlib.sha256).hexdigest()
                self.reply(200, json.dumps({'csrf': csrf}).encode(), 'application/json; charset=utf-8')
            elif route.startswith('/_auth/'):
                self.reply(404)
            else:
                super().handle_get(head=self.command == 'HEAD')

        def do_GET(self):
            self.get_remote()

        def do_HEAD(self):
            self.get_remote()

        def send_file(self, target, head=False, download=False, allow_range=False, private=False):
            if not private and not download and not allow_range and target.suffix == '.html' and target.is_file():
                body = target.read_bytes().replace(b'</head>', b'<script src="/remote-access.js"></script></head>', 1)
                self.reply(200, body)
            else:
                super().send_file(target, head=head, download=download, allow_range=allow_range, private=private)

        def do_POST(self):
            context = self.context()
            if not context:
                return
            gate, document = context
            route = urllib.parse.urlsplit(self.path).path
            if route != LOGIN_PATH and not self.authenticated(gate, document):
                self.denied()
                return
            if not self.same_origin():
                self.reply(403, 'Открой форму на странице менеджера'.encode())
                return
            if route in {LOGIN_PATH, '/_auth/logout'}:
                try:
                    lengths = self.headers.get_all('Content-Length', [])
                    if (len(lengths) != 1 or not re.fullmatch('[0-9]+', lengths[0]) or int(lengths[0]) > 32768
                            or self.headers.get('Transfer-Encoding') or self.headers.get_content_type() != 'application/x-www-form-urlencoded'):
                        raise ValueError()
                    body = self.rfile.read(int(lengths[0])).decode('utf-8')
                    fields = urllib.parse.parse_qs(body, keep_blank_values=True, max_num_fields=8, errors='strict')
                    if any(len(values) != 1 for values in fields.values()):
                        raise ValueError()
                    csrf = fields.get('csrf', [''])[0]
                except (ValueError, UnicodeError):
                    self.reply(400, 'Некорректная форма'.encode())
                    return
                if route == '/_auth/logout':
                    expected = hmac.new(gate.key(document), ('logout:' + cookie(self, SESSION_COOKIE)).encode(), hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(expected.encode(), csrf.encode()):
                        self.reply(403)
                        return
                    self.reply(200, b'{}', 'application/json', [('Set-Cookie', cookie_header(SESSION_COOKIE, '', 0))])
                    return
                if not gate.valid(document, csrf, 'login') or not hmac.compare_digest(csrf.encode(), cookie(self, LOGIN_COOKIE).encode()):
                    self.login_page(gate, document, 'Обнови страницу входа и попробуй снова', 403)
                    return
                retry = gate.retry_after()
                if retry or not gate.verifying.acquire(blocking=False):
                    self.login_page(gate, document, 'Слишком много попыток. Попробуй через минуту', 429, retry or 1)
                    return
                try:
                    password = fields.get('password', [''])[0]
                    valid = 1 <= len(password) <= 1024 and '\x00' not in password
                    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(document['salt']), ITERATIONS) if valid else b''
                    valid = hmac.compare_digest(digest.hex(), document['digest'])
                finally:
                    gate.verifying.release()
                if not valid:
                    self.login_page(gate, document, 'Пароль не подошёл', 401)
                    return
                remember = fields.get('remember') == ['1']
                lifetime = SESSION_SECONDS if remember else 12 * 3600
                session = gate.token(document, 'session', lifetime)
                self.reply(303, headers=[('Location', safe_next(fields.get('next', ['/'])[0])),
                           ('Set-Cookie', cookie_header(SESSION_COOKIE, session, lifetime if remember else None)),
                           ('Set-Cookie', cookie_header(LOGIN_COOKIE, '', 0))])
            elif route.startswith('/_auth/'):
                self.reply(404)
            else:
                super().do_POST()

    return RemoteHandler


def start(base_handler, config_file):
    value = settings(config_file)
    if value is None:
        return None
    server = RemoteHTTPServer(('127.0.0.1', value['port']), handler_class(base_handler))
    server.password_gate = PasswordGate(value['credentials_file'], value['public_host'])
    thread = threading.Thread(target=server.serve_forever, daemon=True, name='remote-password-gate')
    thread.start()
    return server
