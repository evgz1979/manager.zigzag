"""Send a calendar PNG using the existing actu Telegram bot, without logging secrets."""
import configparser
import http.client
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import struct
import threading
import urllib.error
import urllib.request
from uuid import uuid4
from zoneinfo import ZoneInfo

MAX_IMAGE_BYTES = 10 * 1024 * 1024
SEND_LOCK = threading.Lock()


class TelegramError(RuntimeError):
    """A safe error that can be shown in the browser."""


def settings(data_dir):
    # Shared data/ survives code deploys and is excluded from source/recovery ZIPs.
    path = Path(os.environ.get("MANAGER_TELEGRAM_SETTINGS") or Path(data_dir) / "telegram.ini")
    config = configparser.ConfigParser(interpolation=None)
    try:
        with path.open(encoding="utf-8") as source:
            config.read_file(source)
        token = config.get("telegram", "bot_token", fallback="").strip()
        chat = config.get("telegram", "chat_id", fallback="").strip()
        if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,}", token) or not re.fullmatch(r"-?[1-9]\d*", chat):
            raise ValueError()
        return token, chat
    except (OSError, ValueError, configparser.Error):
        raise TelegramError("Не настроена отправка в Telegram на M4: проверь data/telegram.ini") from None


def validate_image(image):
    if not 33 <= len(image) <= MAX_IMAGE_BYTES or image[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("Передай снимок календаря в формате PNG, до 10 МБ")
    width, height = struct.unpack(">II", image[16:24])
    if not (1 <= width <= 8192 and 1 <= height <= 16384 and width * height <= 32000000):
        raise ValueError("Слишком большой снимок календаря")


def current_week(now=None):
    today = (now or datetime.now(ZoneInfo("Europe/Moscow"))).astimezone(ZoneInfo("Europe/Moscow")).date()
    return today - timedelta(days=today.weekday())


def send(image, start, data_dir, *, now=None):
    validate_image(image)
    week = current_week(now)
    if start != week.isoformat():
        raise ValueError("Текущая неделя изменилась. Обнови календарь и повтори отправку")
    token, chat = settings(data_dir)
    through = week + timedelta(days=20)
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
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.loads(response.read(1024 * 1024))
        if not isinstance(result, dict) or result.get("ok") is not True or type(result.get("result", {}).get("message_id")) is not int:
            raise TelegramError("Telegram не подтвердил отправку. Проверь чат перед повтором")
    except urllib.error.HTTPError as error:
        message = {
            400: "Telegram отклонил снимок или чат. Проверь получателя в data/telegram.ini",
            401: "Telegram не принял токен бота. Проверь data/telegram.ini",
            403: "Бот не может писать в этот чат. Открой бот actu и разреши сообщения",
            429: "Telegram просит подождать. Повтори отправку чуть позже",
        }.get(error.code, "Telegram не подтвердил отправку. Проверь чат перед повтором")
        raise TelegramError(message) from None
    except (OSError, ValueError, TypeError, AttributeError, http.client.HTTPException):
        raise TelegramError("Нет подтверждения от Telegram. Проверь чат перед повтором") from None
    return {"ok": True, "start": week.isoformat(), "through": through.isoformat()}
