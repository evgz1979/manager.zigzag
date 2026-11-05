# telegram_calendar.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [telegram_calendar.py](../../../telegram_calendar.py).

Calendar delivery through a dedicated Telegram bot; never return or log tokens.

Импорты Python, включая локальные: `calendar_todos`, `configparser`, `datetime`, `http.client`, `json`, `os`, `pathlib`, `re`, `struct`, `tempfile`, `threading`, `time`, `urllib.error`, `urllib.request`, `uuid`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-TelegramError"></a>

## TelegramError

[telegram_calendar.py](../../../telegram_calendar.py) · `class`.

```python
class TelegramError(RuntimeError):
```

Обозначает ошибку выполнения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-api_request"></a>

## api_request

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def api_request(request, timeout=15):
```

Выполняет ограниченный запрос Bot API и проверяет ответ.

При недопустимом состоянии возбуждает TelegramError.

Непосредственные вызовы: `urllib.request.urlopen`, `json.loads`, `response.read`, `isinstance`, `result.get`, `TelegramError`, `{400: 'Telegram не принял запрос. Проверь чат и токен нового бота', 401: 'Telegram не принял токен. Скопируй токен нового бота из BotFather', 403: 'Бот не может писать в этот чат. Открой нового бота в Telegram и нажми «Старт»', 409: 'Этот бот уже подключён к другому сервису. Используй отдельного бота менеджера', 429: 'Telegram просит подождать. Повтори чуть позже'}.get`.

Явные исключения: `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
result['result']
```

<a id="symbol-bot_api"></a>

## bot_api

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def bot_api(token, method, payload=None):
```

Создаёт запрос к нужному методу Bot API без раскрытия токена в ошибках.

Возвращает `api_request(request)`.

Непосредственные вызовы: `urllib.request.Request`, `json.dumps(payload or {}).encode`, `json.dumps`, `api_request`.

Выражения возврата (ветки читаются в исходнике):

```python
api_request(request)
```

<a id="symbol-bot_info"></a>

## bot_info

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def bot_info(token, data_dir):
```

Проверяет подключённого бота методом getMe.

При недопустимом состоянии возбуждает TelegramError.

Непосредственные вызовы: `validate_token`, `bot_api`, `isinstance`, `bot.get`, `str`, `token.split`, `re.fullmatch`, `TelegramError`.

Явные исключения: `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
bot
```

<a id="symbol-chats"></a>

## chats

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def chats(token, data_dir):
```

Получает допустимые личные чаты для явной настройки отправки.

При недопустимом состоянии возбуждает TelegramError.

Непосредственные вызовы: `bot_info`, `bot_api`, `isinstance`, `TelegramError`, `update.get`, `message.get`, `chat.get`, `type`, `str`, `' '.join((str(chat.get(field) or '') for field in ('first_name', 'last_name'))).strip`, `' '.join`, `list`, `found.values`.

Явные исключения: `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'bot_username': bot['username'], 'chats': list(found.values())}
```

<a id="symbol-configure"></a>

## configure

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def configure(payload, data_dir):
```

Проверяет и сохраняет настройки функции с учётом режима хранения.

При недопустимом состоянии возбуждает ValueError, TelegramError.

Непосредственные вызовы: `payload.get`, `isinstance`, `ValueError`, `token.strip`, `chats`, `re.fullmatch`, `chat.strip`, `bot_info`, `bot_api`, `recipient.get`, `str`, `settings_path`, `path.is_symlink`, `path.exists`, `read_ini`, `existing.get`, `path.parent.mkdir`, `tempfile.NamedTemporaryFile`, `Path`, `os.fchmod`, `stream.fileno`, `stream.write`, `stream.flush`, `os.fsync`, `os.replace`, `TelegramError`, `temporary.unlink`.

Явные исключения: `ValueError`, `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
chats(token, data_dir)
{'configured': True, 'chat_id': chat, 'bot_username': bot['username']}
```

<a id="symbol-current_week"></a>

## current_week

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def current_week(now=None):
```

Определяет понедельник текущей недели по Москве.

Возвращает `today - timedelta(days=today.weekday())`.

Непосредственные вызовы: `(now or datetime.now(ZoneInfo('Europe/Moscow'))).astimezone(ZoneInfo('Europe/Moscow')).date`, `(now or datetime.now(ZoneInfo('Europe/Moscow'))).astimezone`, `datetime.now`, `ZoneInfo`, `timedelta`, `today.weekday`.

Выражения возврата (ветки читаются в исходнике):

```python
today - timedelta(days=today.weekday())
```

<a id="symbol-read_ini"></a>

## read_ini

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def read_ini(path):
```

Читает конфигурацию Telegram без вывода секретов.

Возвращает `config`.

Непосредственные вызовы: `configparser.ConfigParser`, `path.open`, `config.read_file`.

Выражения возврата (ветки читаются в исходнике):

```python
config
```

<a id="symbol-send"></a>

## send

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def send(image, start, data_dir, *, now=None, todo_text='', through=None):
```

Отправляет общий PNG и последующие тексты с последовательными подтверждениями.

При недопустимом состоянии возбуждает ValueError, TelegramError.

Непосредственные вызовы: `validate_image`, `current_week`, `timedelta`, `week.isoformat`, `end.isoformat`, `(week - timedelta(days=7)).isoformat`, `ValueError`, `settings`, `datetime.fromisoformat(start).date`, `datetime.fromisoformat`, `uuid4`, `chunks.append`, `f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode`, `chunks.extend`, `f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode`, `f'\r\n--{boundary}--\r\n'.encode`, `urllib.request.Request`, `b''.join`, `api_request`, `isinstance`, `type`, `result.get`, `TelegramError`, `through.isoformat`, `message_parts`, `time.sleep`, `bot_api`, `message.get`.

Явные исключения: `ValueError`, `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
response
```

<a id="symbol-settings"></a>

## settings

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def settings(data_dir):
```

Читает и проверяет настройки функции без раскрытия секретов вызывающему коду.

При недопустимом состоянии возбуждает ValueError, TelegramError.

Непосредственные вызовы: `read_ini`, `settings_path`, `config.get`, `ValueError`, `config.get('telegram', 'bot_token', fallback='').strip`, `config.get('telegram', 'chat_id', fallback='').strip`, `validate_token`, `re.fullmatch`, `TelegramError`.

Явные исключения: `ValueError`, `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
(token, chat)
```

<a id="symbol-settings_path"></a>

## settings_path

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def settings_path(data_dir):
```

Вычисляет закрытый локальный путь настроек Telegram.

Возвращает `Path(os.environ.get('MANAGER_TELEGRAM_SETTINGS') or Path(data_dir) / 'telegram.ini')`.

Непосредственные вызовы: `Path`, `os.environ.get`.

Выражения возврата (ветки читаются в исходнике):

```python
Path(os.environ.get('MANAGER_TELEGRAM_SETTINGS') or Path(data_dir) / 'telegram.ini')
```

<a id="symbol-status"></a>

## status

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def status(data_dir):
```

Возвращает состояние обработки и сохранённые ошибки.

Возвращает `{'configured': True, 'chat_id': chat, 'bot_username': config.get('telegram', 'bot_username', fallback='')}`; либо `{'configured': False}`.

Непосредственные вызовы: `settings`, `read_ini`, `settings_path`, `config.get`.

Выражения возврата (ветки читаются в исходнике):

```python
{'configured': True, 'chat_id': chat, 'bot_username': config.get('telegram', 'bot_username', fallback='')}
{'configured': False}
```

<a id="symbol-validate_image"></a>

## validate_image

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def validate_image(image):
```

Проверяет байты PNG и допустимые ограничения общего снимка.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `len`, `ValueError`, `struct.unpack`.

Явные исключения: `ValueError`.

<a id="symbol-validate_token"></a>

## validate_token

[telegram_calendar.py](../../../telegram_calendar.py) · `function`.

```python
def validate_token(token, data_dir):
```

Проверяет допустимую форму токена Telegram перед использованием.

При недопустимом состоянии возбуждает ValueError, TelegramError.

Непосредственные вызовы: `isinstance`, `re.fullmatch`, `ValueError`, `Path`, `settings_path`, `read_ini`, `config.get`, `config.get('telegram', 'bot_token', fallback='').strip`, `old_token.split`, `token.split`, `TelegramError`.

Явные исключения: `ValueError`, `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
token
```
