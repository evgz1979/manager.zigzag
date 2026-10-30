"""Calendar delivery through a dedicated Telegram bot; never return or log tokens."""
import configparser
import http.client
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import threading
import time
import urllib.error
import urllib.request
from uuid import uuid4
from zoneinfo import ZoneInfo

MAX_IMAGE_BYTES = 10 * 1024 * 1024
SEND_LOCK = threading.Lock()
PURPOSE = "manager-calendar"


class TelegramError(RuntimeError):
    """A safe error that can be shown in the browser."""


def settings_path(data_dir):
    return Path(os.environ.get("MANAGER_TELEGRAM_SETTINGS") or Path(data_dir) / "telegram.ini")


def read_ini(path):
    config = configparser.ConfigParser(interpolation=None)
    with path.open(encoding="utf-8") as source:
        config.read_file(source)
    return config


def validate_token(token, data_dir):
    if not isinstance(token, str) or not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,}", token):
        raise ValueError("Проверь токен нового бота из BotFather")
    # The old manager-local actu copy is retained only to reject accidental reuse.
    for path in {Path(data_dir) / "telegram-actu-disabled.ini", settings_path(data_dir)}:
        try:
            config = read_ini(path)
            if config.get("telegram", "purpose", fallback="") == PURPOSE:
                continue
            old_token = config.get("telegram", "bot_token", fallback="").strip()
            if old_token and old_token.split(":", 1)[0] == token.split(":", 1)[0]:
                raise TelegramError("Это бот actu. Создай отдельного бота через BotFather")
        except (OSError, configparser.Error):
            continue
    return token


def settings(data_dir):
    # An old actu INI without purpose must never be used as a fallback.
    try:
        config = read_ini(settings_path(data_dir))
        if config.get("telegram", "purpose", fallback="") != PURPOSE:
            raise ValueError()
        token = config.get("telegram", "bot_token", fallback="").strip()
        chat = config.get("telegram", "chat_id", fallback="").strip()
        validate_token(token, data_dir)
        if not re.fullmatch(r"-?[1-9]\d*", chat):
            raise ValueError()
        return token, chat
    except (OSError, ValueError, configparser.Error):
        raise TelegramError("Подключи отдельного бота в настройке Telegram менеджера") from None


def status(data_dir):
    try:
        _, chat = settings(data_dir)
        config = read_ini(settings_path(data_dir))
        return {"configured": True, "chat_id": chat, "bot_username": config.get("telegram", "bot_username", fallback="")}
    except (TelegramError, OSError, configparser.Error):
        return {"configured": False}


def api_request(request, timeout=15):
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read(1024 * 1024))
        if not isinstance(result, dict) or result.get("ok") is not True or "result" not in result:
            raise TelegramError("Telegram не подтвердил запрос. Проверь подключение и повтори")
        return result["result"]
    except urllib.error.HTTPError as error:
        message = {
            400: "Telegram не принял запрос. Проверь чат и токен нового бота",
            401: "Telegram не принял токен. Скопируй токен нового бота из BotFather",
            403: "Бот не может писать в этот чат. Открой нового бота в Telegram и нажми «Старт»",
            409: "Этот бот уже подключён к другому сервису. Используй отдельного бота менеджера",
            429: "Telegram просит подождать. Повтори чуть позже",
        }.get(error.code, "Telegram не подтвердил запрос. Проверь чат перед повтором отправки")
        raise TelegramError(message) from None
    except (OSError, ValueError, TypeError, AttributeError, http.client.HTTPException):
        raise TelegramError("Нет подтверждения от Telegram. Проверь чат перед повтором отправки") from None


def bot_api(token, method, payload=None):
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload or {}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return api_request(request)


def bot_info(token, data_dir):
    validate_token(token, data_dir)
    bot = bot_api(token, "getMe")
    if (not isinstance(bot, dict) or bot.get("is_bot") is not True or str(bot.get("id")) != token.split(":", 1)[0]
            or not isinstance(bot.get("username"), str) or not re.fullmatch(r"[A-Za-z0-9_]{5,32}", bot["username"])):
        raise TelegramError("Telegram не подтвердил нового бота")
    return bot


def chats(token, data_dir):
    bot = bot_info(token, data_dir)
    updates = bot_api(token, "getUpdates", {"timeout": 0, "limit": 100})
    if not isinstance(updates, list):
        raise TelegramError("Telegram не вернул список чатов")
    found = {}
    for update in updates:
        if not isinstance(update, dict):
            continue
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat", {}) if isinstance(message, dict) else {}
        if isinstance(chat, dict) and chat.get("type") == "private" and type(chat.get("id")) is int and chat["id"] > 0:
            key = str(chat["id"])
            label = " ".join(str(chat.get(field) or "") for field in ("first_name", "last_name")).strip()
            found[key] = {"id": key, "label": label or chat.get("username") or key}
    # No offset or allowed_updates: do not consume updates or change webhook settings.
    return {"bot_username": bot["username"], "chats": list(found.values())}


def configure(payload, data_dir):
    token = payload.get("bot_token", "")
    if not isinstance(token, str):
        raise ValueError("Введи токен нового бота")
    token = token.strip()
    if payload.get("action") == "chats":
        return chats(token, data_dir)
    if payload.get("action") != "save":
        raise ValueError("Неизвестная настройка Telegram")
    chat = payload.get("chat_id", "")
    if not isinstance(chat, str) or not re.fullmatch(r"[1-9]\d*", chat.strip()):
        raise ValueError("Выбери свой личный чат с новым ботом")
    chat = chat.strip()
    bot = bot_info(token, data_dir)
    recipient = bot_api(token, "getChat", {"chat_id": chat})
    if not isinstance(recipient, dict) or recipient.get("type") != "private" or str(recipient.get("id")) != chat:
        raise ValueError("Выбери свой личный чат с новым ботом")
    path = settings_path(data_dir)
    if path.is_symlink():
        raise ValueError("Настройки Telegram не сохраняются через символическую ссылку")
    if path.exists():
        existing = read_ini(path)
        if existing.get("telegram", "purpose", fallback="") != PURPOSE:
            raise ValueError("Прежние настройки actu нужно отключить перед подключением нового бота")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".telegram-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(f"[telegram]\npurpose = {PURPOSE}\nbot_token = {token}\nchat_id = {chat}\nbot_username = {bot['username']}\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError:
        raise TelegramError("Не удалось сохранить настройки Telegram на M4. Введённые данные остались в форме") from None
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return {"configured": True, "chat_id": chat, "bot_username": bot["username"]}


def validate_image(image):
    if not 33 <= len(image) <= MAX_IMAGE_BYTES or image[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("Передай снимок календаря в формате PNG, до 10 МБ")
    width, height = struct.unpack(">II", image[16:24])
    if not (1 <= width <= 8192 and 1 <= height <= 16384 and width * height <= 32000000):
        raise ValueError("Слишком большой снимок календаря")


def current_week(now=None):
    today = (now or datetime.now(ZoneInfo("Europe/Moscow"))).astimezone(ZoneInfo("Europe/Moscow")).date()
    return today - timedelta(days=today.weekday())


def send(image, start, data_dir, *, now=None, todo_text=''):
    validate_image(image)
    week = current_week(now)
    if start != week.isoformat():
        raise ValueError("Текущая неделя изменилась. Обнови календарь и повтори отправку")
    token, chat = settings(data_dir)
    through = week + timedelta(days=13)
    caption = f"Календарь Зигзаг · {week:%d.%m.%Y} — {through:%d.%m.%Y}"
    boundary = "manager-" + uuid4().hex
    chunks = []
    for name, value in (("chat_id", chat), ("caption", caption)):
        chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode())
    filename = f"zigzag-calendar-{week.isoformat()}.png"
    chunks.extend([
        (f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n').encode(),
        image, f"\r\n--{boundary}--\r\n".encode(),
    ])
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendDocument", data=b"".join(chunks),
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    # Never retry an ambiguous result automatically: Telegram may already have sent it.
    result = api_request(request, timeout=40)
    if not isinstance(result, dict) or type(result.get("message_id")) is not int:
        raise TelegramError("Telegram не подтвердил отправку. Проверь чат перед повтором")
    response = {"ok": True, "start": week.isoformat(), "through": through.isoformat()}
    if todo_text:
        from calendar_todos import message_parts
        sent = 0
        try:
            for text in message_parts(todo_text):
                time.sleep(1.05)
                message = bot_api(token, 'sendMessage', {'chat_id': chat, 'text': text, 'link_preview_options': {'is_disabled': True}})
                if not isinstance(message, dict) or type(message.get('message_id')) is not int:
                    raise TelegramError('Telegram не подтвердил сообщение')
                sent += 1
        except TelegramError:
            raise TelegramError(f'PNG отправлен. Подтверждено сообщений To-do: {sent}; дальнейшая отправка остановлена. Проверь Telegram перед повтором') from None
        response['todo_messages'] = sent
    return response
