# remote_access.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [remote_access.py:1](../../../remote_access.py#L1).

Password gate on a separate loopback listener; the LAN handler is unchanged.

Импорты Python, включая локальные: `collections`, `configparser`, `hashlib`, `hmac`, `html`, `http.server`, `json`, `math`, `os`, `pathlib`, `re`, `secrets`, `stat`, `threading`, `time`, `urllib.parse`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## password_document

[remote_access.py:31](../../../remote_access.py#L31) · `function`.

```python
def password_document(password):
```

Создаёт документ хеша пароля с солью и случайным ключом подписи.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `secrets.token_bytes`, `hashlib.pbkdf2_hmac`, `password.encode`, `salt.hex`, `digest.hex`, `secrets.token_hex`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'version': 1, 'algorithm': 'pbkdf2-sha256', 'iterations': ITERATIONS, 'salt': salt.hex(), 'digest': digest.hex(), 'signing_key': secrets.token_hex(32)}
```

## save_password

[remote_access.py:42](../../../remote_access.py#L42) · `function`.

```python
def save_password(path, password):
```

Первоначально сохраняет закрытый профиль пароля без замены существующего.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `password_document`, `Path(path).expanduser`, `Path`, `path.parent.mkdir`, `path.parent.is_symlink`, `path.parent.stat`, `ValueError`, `(json.dumps(document) + '\n').encode`, `json.dumps`, `os.open`, `os.fdopen`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`.

Явные исключения: `ValueError`.

## settings

[remote_access.py:59](../../../remote_access.py#L59) · `function`.

```python
def settings(config_file):
```

Читает и проверяет настройки функции без раскрытия секретов вызывающему коду.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `configparser.ConfigParser`, `config.read`, `config.getboolean`, `config.get('remote_access', 'public_host', fallback='').strip().lower`, `config.get('remote_access', 'public_host', fallback='').strip`, `config.get`, `re.fullmatch`, `ValueError`, `config.getint`, `Path(config.get('remote_access', 'credentials_file', fallback=str(DEFAULT_CREDENTIALS))).expanduser`, `Path`, `str`, `credentials.is_absolute`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
None
{'public_host': host, 'port': port, 'credentials_file': credentials}
```

## PasswordGate

[remote_access.py:78](../../../remote_access.py#L78) · `class`.

```python
class PasswordGate:
```

Проверяет профиль пароля, подписывает сессии и ограничивает попытки.

Основные операции: __init__, document, key, token, valid; остальные описаны у методов.

## PasswordGate.__init__

[remote_access.py:81](../../../remote_access.py#L81) · `function`.

```python
def __init__(self, path, public_host, clock=time.time):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `Path`, `threading.Lock`, `deque`, `threading.BoundedSemaphore`.

Прямые присваивания полям/свойствам: `self.path`, `self.public_host`, `self.clock`, `self.lock`, `self.attempts`, `self.verifying`.

## PasswordGate.document

[remote_access.py:91](../../../remote_access.py#L91) · `function`.

```python
def document(self):
```

Читает и проверяет закрытый документ пароля и подписи сессий.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `os.open`, `os.fdopen`, `os.fstat`, `stream.fileno`, `stat.S_ISREG`, `os.getuid`, `ValueError`, `json.loads`, `stream.read`, `isinstance`, `set`, `type`, `any`, `re.fullmatch`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

## PasswordGate.key

[remote_access.py:109](../../../remote_access.py#L109) · `function`.

```python
def key(self, document):
```

Вычисляет нормализованный ключ для обращения к данным.

Возвращает `hmac.digest(bytes.fromhex(document['signing_key']), bytes.fromhex(document['digest']), 'sha256')`.

Непосредственные вызовы: `hmac.digest`, `bytes.fromhex`.

Выражения возврата (ветки читаются в исходнике):

```python
hmac.digest(bytes.fromhex(document['signing_key']), bytes.fromhex(document['digest']), 'sha256')
```

## PasswordGate.token

[remote_access.py:115](../../../remote_access.py#L115) · `function`.

```python
def token(self, document, kind, lifetime):
```

Создаёт подписанный либо вычисляемый проверочный токен текущего контекста.

Возвращает `value + '.' + hmac.new(self.key(document), value.encode(), hashlib.sha256).hexdigest()`.

Непосредственные вызовы: `int`, `self.clock`, `secrets.token_hex`, `hmac.new(self.key(document), value.encode(), hashlib.sha256).hexdigest`, `hmac.new`, `self.key`, `value.encode`.

Выражения возврата (ветки читаются в исходнике):

```python
value + '.' + hmac.new(self.key(document), value.encode(), hashlib.sha256).hexdigest()
```

## PasswordGate.valid

[remote_access.py:122](../../../remote_access.py#L122) · `function`.

```python
def valid(self, document, token, kind):
```

Проверяет срок и подпись переданного проверочного значения.

Возвращает `False`; либо `hmac.compare_digest(expected, signature)`.

Непосредственные вызовы: `isinstance`, `len`, `re.fullmatch`, `int`, `self.clock`, `token.rsplit`, `hmac.new(self.key(document), value.encode(), hashlib.sha256).hexdigest`, `hmac.new`, `self.key`, `value.encode`, `hmac.compare_digest`.

Выражения возврата (ветки читаются в исходнике):

```python
False
hmac.compare_digest(expected, signature)
```

## PasswordGate.retry_after

[remote_access.py:138](../../../remote_access.py#L138) · `function`.

```python
def retry_after(self):
```

Возвращает задержку глобального ограничения попыток входа.

Возвращает `max(1, math.ceil(60 - (now - self.attempts[0])))`; либо `0`.

Непосредственные вызовы: `self.clock`, `self.attempts.popleft`, `len`, `max`, `math.ceil`, `self.attempts.append`.

Выражения возврата (ветки читаются в исходнике):

```python
max(1, math.ceil(60 - (now - self.attempts[0])))
0
```

## cookie

[remote_access.py:152](../../../remote_access.py#L152) · `function`.

```python
def cookie(handler, name):
```

Извлекает ожидаемую cookie из HTTP-заголовка запроса.

Возвращает `matches[0] if len(matches) == 1 else ''`.

Непосредственные вызовы: `handler.headers.get_all`, `header.split`, `part.strip().partition`, `part.strip`, `matches.append`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
matches[0] if len(matches) == 1 else ''
```

## safe_next

[remote_access.py:164](../../../remote_access.py#L164) · `function`.

```python
def safe_next(value):
```

Ограничивает адрес возврата после входа локальным путём приложения.

Возвращает `'/'`; либо `urllib.parse.quote(value, safe='/%?&#=:+,;@!$()*-._~')`.

Непосредственные вызовы: `isinstance`, `len`, `value.startswith`, `any`, `ord`, `urllib.parse.urlsplit(value).path.startswith`, `urllib.parse.urlsplit`, `urllib.parse.quote`.

Выражения возврата (ветки читаются в исходнике):

```python
'/'
urllib.parse.quote(value, safe='/%?&#=:+,;@!$()*-._~')
```

## cookie_header

[remote_access.py:174](../../../remote_access.py#L174) · `function`.

```python
def cookie_header(name, value, lifetime=None):
```

Формирует cookie с обязательными атрибутами защищённого входа.

Возвращает `result if lifetime is None else result + f'; Max-Age={lifetime}'`.

Выражения возврата (ветки читаются в исходнике):

```python
result if lifetime is None else result + f'; Max-Age={lifetime}'
```

## RemoteHTTPServer

[remote_access.py:181](../../../remote_access.py#L181) · `class`.

```python
class RemoteHTTPServer(ThreadingHTTPServer):
```

Ограничивает параллельные соединения отдельного защищённого слушателя.

Основные операции: __init__, process_request, process_request_thread.

## RemoteHTTPServer.__init__

[remote_access.py:187](../../../remote_access.py#L187) · `function`.

```python
def __init__(self, *args, **kwargs):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `threading.BoundedSemaphore`, `super().__init__`, `super`.

Прямые присваивания полям/свойствам: `self.slots`.

## RemoteHTTPServer.process_request

[remote_access.py:193](../../../remote_access.py#L193) · `function`.

```python
def process_request(self, request, client_address):
```

Ограничивает количество одновременно обслуживаемых HTTP-запросов.

Передаёт работу `self.slots.acquire`, `self.shutdown_request`, `super().process_request`.

Непосредственные вызовы: `self.slots.acquire`, `self.shutdown_request`, `super().process_request`, `super`, `self.slots.release`.

## RemoteHTTPServer.process_request_thread

[remote_access.py:205](../../../remote_access.py#L205) · `function`.

```python
def process_request_thread(self, request, client_address):
```

Освобождает занятый слот после завершения обработки запроса.

Передаёт работу `super().process_request_thread`, `super`, `self.slots.release`.

Непосредственные вызовы: `super().process_request_thread`, `super`, `self.slots.release`.

## handler_class

[remote_access.py:214](../../../remote_access.py#L214) · `function`.

```python
def handler_class(base_handler):
```

Создаёт отдельный класс обработчика защищённого слушателя.

Возвращает `RemoteHandler`.

Выражения возврата (ветки читаются в исходнике):

```python
RemoteHandler
```

## handler_class.RemoteHandler

[remote_access.py:217](../../../remote_access.py#L217) · `class`.

```python
class RemoteHandler(base_handler):
```

Закрывает все унаследованные маршруты проверками отдельного внешнего входа.

Основные операции: setup, end_headers, reply, context, same_origin; остальные описаны у методов.

## handler_class.RemoteHandler.setup

[remote_access.py:222](../../../remote_access.py#L222) · `function`.

```python
def setup(self):
```

Настраивает ограничения соединения перед обработкой защищённого запроса.

Передаёт работу `super().setup`, `super`, `self.connection.settimeout`.

Непосредственные вызовы: `super().setup`, `super`, `self.connection.settimeout`.

## handler_class.RemoteHandler.end_headers

[remote_access.py:228](../../../remote_access.py#L228) · `function`.

```python
def end_headers(self):
```

Добавляет обязательные заголовки перед завершением HTTP-ответа.

Передаёт работу `self.send_header`, `super().end_headers`, `super`.

Непосредственные вызовы: `self.send_header`, `super().end_headers`, `super`.

## handler_class.RemoteHandler.reply

[remote_access.py:239](../../../remote_access.py#L239) · `function`.

```python
def reply(self, status, body=b'', content_type='text/html; charset=utf-8', headers=()):
```

Отправляет локальный ответ защищённого обработчика с нужным статусом.

Передаёт работу `self.send_response`, `self.send_header`, `self.end_headers`.

Непосредственные вызовы: `self.send_response`, `self.send_header`, `str`, `len`, `self.end_headers`, `self.wfile.write`.

Прямые присваивания полям/свойствам: `self.close_connection`.

## handler_class.RemoteHandler.context

[remote_access.py:252](../../../remote_access.py#L252) · `function`.

```python
def context(self):
```

Проверяет Host и состояние профиля для текущего запроса.

Возвращает `None`; либо `(gate, document)`.

Непосредственные вызовы: `self.headers.get_all`, `len`, `hosts[0].lower`, `self.reply`, `'Неверный адрес сайта'.encode`, `gate.document`, `'Внешний вход ещё не настроен'.encode`.

Выражения возврата (ветки читаются в исходнике):

```python
None
(gate, document)
```

## handler_class.RemoteHandler.same_origin

[remote_access.py:267](../../../remote_access.py#L267) · `function`.

```python
def same_origin(self):
```

Проверяет строгий HTTPS Origin внешней записи.

Возвращает `len(origins) == 1 and origins[0] in {'https://' + host, 'https://' + host + ':443'}`.

Непосредственные вызовы: `self.headers.get_all`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
len(origins) == 1 and origins[0] in {'https://' + host, 'https://' + host + ':443'}
```

## handler_class.RemoteHandler.authenticated

[remote_access.py:274](../../../remote_access.py#L274) · `function`.

```python
def authenticated(self, gate, document):
```

Проверяет подписанную cookie сессии и её срок действия.

Возвращает `gate.valid(document, cookie(self, SESSION_COOKIE), 'session')`.

Непосредственные вызовы: `gate.valid`, `cookie`.

Выражения возврата (ветки читаются в исходнике):

```python
gate.valid(document, cookie(self, SESSION_COOKIE), 'session')
```

## handler_class.RemoteHandler.denied

[remote_access.py:279](../../../remote_access.py#L279) · `function`.

```python
def denied(self):
```

Отправляет отказ или предложение входа без выдачи закрытых данных.

Передаёт работу `urllib.parse.urlsplit(self.path).path.startswith`, `urllib.parse.urlsplit`, `self.path.startswith`.

Непосредственные вызовы: `urllib.parse.urlsplit(self.path).path.startswith`, `urllib.parse.urlsplit`, `self.path.startswith`, `self.reply`, `json.dumps({'error': 'Нужен вход в менеджер', 'login_required': True}).encode`, `json.dumps`, `urllib.parse.urlencode`, `safe_next`.

## handler_class.RemoteHandler.login_page

[remote_access.py:288](../../../remote_access.py#L288) · `function`.

```python
def login_page(self, gate, document, error='', status=200, retry=0):
```

Формирует страницу входа и короткую привязку CSRF.

Передаёт работу `urllib.parse.parse_qs`, `urllib.parse.urlsplit`, `safe_next`.

Непосредственные вызовы: `urllib.parse.parse_qs`, `urllib.parse.urlsplit`, `safe_next`, `query.get`, `gate.token`, `secrets.token_urlsafe`, `f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход · Зигзаг</title>\n<style nonce="{nonce}">*{{box-sizing:border-box}}body{{margin:0;min-height:100dvh;display:grid;place-items:center;padding:24px;background:#f7f9f8;color:#263738;font:15px -apple-system,BlinkMacSystemFont,sans-serif}}main{{width:100%;max-width:360px;background:white;border:1px solid #e0e7e4;border-radius:16px;padding:28px}}h1{{font-size:24px;margin:0 0 24px}}label{{display:block}}input[type=password]{{width:100%;font:16px -apple-system,BlinkMacSystemFont,sans-serif;padding:12px;border:1px solid #bdccc6;border-radius:8px;margin:8px 0 16px}}button{{width:100%;border:0;border-radius:8px;background:#167a65;color:white;padding:13px;font:16px -apple-system,BlinkMacSystemFont,sans-serif;margin-top:22px;cursor:pointer}}.remember{{font-size:13px;color:#667570;display:flex;gap:8px;align-items:center}}.error{{color:#b13535;font-size:13px}}input:focus-visible,button:focus-visible{{outline:3px solid #76bcaa;outline-offset:2px}}</style>\n<main><h1>Зигзаг · Вход</h1><form method="post" action="https://{gate.public_host}{LOGIN_PATH}"><input type="hidden" name="username" autocomplete="username" value="manager"><input type="hidden" name="csrf" value="{csrf}"><input type="hidden" name="next" value="{html.escape(destination, quote=True)}"><label for="password">Пароль<input id="password" name="password" type="password" autocomplete="current-password" required maxlength="1024" autofocus></label><label class="remember"><input type="checkbox" name="remember" value="1" checked>Запомнить на этом устройстве</label><p class="error" role="alert">{html.escape(error)}</p><button type="submit">Войти</button></form></main>\n<script nonce="{nonce}">document.querySelector('form').addEventListener('submit',()=>{{let n=document.querySelector('[name=next]');if(location.hash&&!n.value.includes('#'))n.value+=location.hash}});</script></html>'''.encode`, `html.escape`, `cookie_header`, `headers.append`, `str`, `self.reply`.

## handler_class.RemoteHandler.get_remote

[remote_access.py:305](../../../remote_access.py#L305) · `function`.

```python
def get_remote(self):
```

Проверяет вход перед выдачей страницы, API или файла.

Передаёт работу `self.context`, `urllib.parse.urlsplit`, `self.authenticated`.

Непосредственные вызовы: `self.context`, `urllib.parse.urlsplit`, `self.authenticated`, `self.reply`, `self.login_page`, `self.denied`, `cookie`, `hmac.new(gate.key(document), ('logout:' + token).encode(), hashlib.sha256).hexdigest`, `hmac.new`, `gate.key`, `('logout:' + token).encode`, `json.dumps({'csrf': csrf}).encode`, `json.dumps`, `route.startswith`, `super().handle_get`, `super`.

## handler_class.RemoteHandler.do_GET

[remote_access.py:330](../../../remote_access.py#L330) · `function`.

```python
def do_GET(self):
```

Обслуживает GET через проверки и маршрутизацию текущего обработчика.

Передаёт работу `self.get_remote`.

Непосредственные вызовы: `self.get_remote`.

## handler_class.RemoteHandler.do_HEAD

[remote_access.py:335](../../../remote_access.py#L335) · `function`.

```python
def do_HEAD(self):
```

Обслуживает HEAD с теми же ограничениями доступа, что GET.

Передаёт работу `self.get_remote`.

Непосредственные вызовы: `self.get_remote`.

## handler_class.RemoteHandler.send_file

[remote_access.py:340](../../../remote_access.py#L340) · `function`.

```python
def send_file(self, target, head=False, download=False, allow_range=False, private=False):
```

Передаёт проверенный файл или статический ресурс в HTTP-ответе.

Передаёт работу `target.is_file`, `target.read_bytes().replace`, `target.read_bytes`.

Непосредственные вызовы: `target.is_file`, `target.read_bytes().replace`, `target.read_bytes`, `self.reply`, `super().send_file`, `super`.

## handler_class.RemoteHandler.do_POST

[remote_access.py:349](../../../remote_access.py#L349) · `function`.

```python
def do_POST(self):
```

Проверяет и маршрутизирует запрос изменения данных текущего обработчика.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.context`, `urllib.parse.urlsplit`, `self.authenticated`, `self.denied`, `self.same_origin`, `self.reply`, `'Открой форму на странице менеджера'.encode`, `self.headers.get_all`, `len`, `re.fullmatch`, `int`, `self.headers.get`, `self.headers.get_content_type`, `ValueError`, `self.rfile.read(int(lengths[0])).decode`, `self.rfile.read`, `urllib.parse.parse_qs`, `any`, `fields.values`, `fields.get`, `'Некорректная форма'.encode`, `hmac.new(gate.key(document), ('logout:' + cookie(self, SESSION_COOKIE)).encode(), hashlib.sha256).hexdigest`, `hmac.new`, `gate.key`, `('logout:' + cookie(self, SESSION_COOKIE)).encode`, `cookie`, `hmac.compare_digest`, `expected.encode`, `csrf.encode`, `cookie_header`, `gate.valid`, `cookie(self, LOGIN_COOKIE).encode`, `self.login_page`, `gate.retry_after`, `gate.verifying.acquire`, `hashlib.pbkdf2_hmac`, `password.encode`, `bytes.fromhex`, `digest.hex`, `gate.verifying.release`, `gate.token`, `safe_next`, `route.startswith`, `super().do_POST`, `super`.

Явные исключения: `ValueError`.

## start

[remote_access.py:415](../../../remote_access.py#L415) · `function`.

```python
def start(base_handler, config_file):
```

Проверяет профиль и запускает отдельный loopback-слушатель внешнего входа.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `settings`, `RemoteHTTPServer`, `handler_class`, `PasswordGate`, `threading.Thread`, `thread.start`.

Выражения возврата (ветки читаются в исходнике):

```python
None
server
```
