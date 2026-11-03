#!/usr/bin/env python3
"""Initial password setup on loopback, or interactively in a private terminal."""
import argparse
import getpass
import html
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import sys
import threading
import time
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import remote_access


# Создаёт настройки рабочей установки из проверенных параметров развёртывания.
# При недопустимом состоянии возбуждает ValueError.
def setup_server(path, port=18766):
    path = Path(path).expanduser()
    if path.exists() or path.is_symlink():
        raise ValueError('Пароль уже настроен. Существующий файл не заменён')
    csrf = secrets.token_urlsafe(32)
    done = threading.Event()
    write_lock = threading.Lock()

    # Объединяет операции модуля: временная loopback-форма первоначального задания пароля владельцем.
    # Основные операции: setup, log_message, reply, allowed, page; остальные описаны у методов.
    class Handler(BaseHTTPRequestHandler):
        # Настраивает ограничения соединения перед обработкой защищённого запроса.
        # Передаёт работу `super().setup`, `super`, `self.connection.settimeout`.
        def setup(self):
            super().setup()
            self.connection.settimeout(20)

        # Записывает предусмотренное диагностическое сообщение обработчика.
        # Выполняет локальные проверки или меняет только переданные структуры данных.
        def log_message(self, *_):
            pass

        # Отправляет локальный ответ защищённого обработчика с нужным статусом.
        # Передаёт работу `body.encode`, `self.send_response`, `self.send_header`.
        def reply(self, status, body):
            body = body.encode()
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        # Проверяет допустимость одной папки в текущем каталоге.
        # Возвращает `self.headers.get_all('Host', []) == ['127.0.0.1:' + str(self.server.server_port)]`.
        def allowed(self):
            return self.headers.get_all('Host', []) == ['127.0.0.1:' + str(self.server.server_port)]

        # Формирует страницу временного локального ввода пароля.
        # Формирует возвращаемое значение из проверенного локального состояния.
        def page(self, error=''):
            return f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Пароль для внешнего входа · Зигзаг</title>
<style>body{{font:15px -apple-system,sans-serif;color:#263738;background:#f7f9f8;margin:0;padding:24px}}main{{box-sizing:border-box;max-width:400px;margin:8vh auto;background:white;border:1px solid #dce5e0;border-radius:14px;padding:26px}}h1{{font-size:23px}}label{{display:block;margin:18px 0}}input{{box-sizing:border-box;width:100%;padding:12px;margin-top:7px;border:1px solid #bbcfc5;border-radius:8px;font:16px -apple-system,sans-serif}}button{{width:100%;padding:13px;border:0;background:#167a65;color:white;border-radius:8px;font:16px -apple-system,sans-serif}}p{{line-height:1.5}}.error{{color:#b13535}}</style>
<main><h1>Пароль для внешнего входа</h1><p>Дома менеджер открывается как прежде. Этот пароль понадобится для входа через интернет.</p><form method="post" action="/"><input type="hidden" name="csrf" value="{csrf}"><label>Новый пароль<input name="password" type="password" minlength="12" maxlength="1024" autocomplete="new-password" required autofocus></label><label>Повтори пароль<input name="confirmation" type="password" minlength="12" maxlength="1024" autocomplete="new-password" required></label><p class="error" role="alert">{html.escape(error)}</p><button>Сохранить пароль</button></form></main></html>'''

        # Обслуживает GET через проверки и маршрутизацию текущего обработчика.
        # Передаёт работу `self.allowed`, `self.reply`, `done.is_set`.
        def do_GET(self):
            if not self.allowed() or self.path != '/':
                self.reply(403, 'Недоступно')
            elif done.is_set():
                self.reply(200, 'Пароль сохранён. Эту вкладку можно закрыть.')
            else:
                self.reply(200, self.page())

        # Проверяет и маршрутизирует запрос изменения данных текущего обработчика.
        # При недопустимом состоянии возбуждает ValueError.
        def do_POST(self):
            origin = 'http://127.0.0.1:' + str(self.server.server_port)
            if not self.allowed() or self.path != '/' or self.headers.get_all('Origin', []) != [origin]:
                self.reply(403, 'Открой форму по локальному адресу')
                return
            try:
                lengths = self.headers.get_all('Content-Length', [])
                if (len(lengths) != 1 or not lengths[0].isdigit() or int(lengths[0]) > 32768
                        or self.headers.get('Transfer-Encoding') or self.headers.get_content_type() != 'application/x-www-form-urlencoded'):
                    raise ValueError('Некорректная форма')
                fields = urllib.parse.parse_qs(self.rfile.read(int(lengths[0])).decode(), keep_blank_values=True, max_num_fields=4, errors='strict')
                if any(len(value) != 1 for value in fields.values()) or not hmac.compare_digest(fields.get('csrf', [''])[0].encode(), csrf.encode()):
                    raise ValueError('Обнови страницу и попробуй снова')
                password = fields.get('password', [''])[0]
                if not hmac.compare_digest(password.encode(), fields.get('confirmation', [''])[0].encode()):
                    raise ValueError('Пароли не совпадают')
                with write_lock:
                    remote_access.save_password(path, password)
            except (OSError, ValueError, UnicodeError):
                self.reply(400, self.page('Не удалось сохранить. Пароли должны совпадать и содержать не меньше 12 символов. Существующий пароль не заменяется.'))
                return
            self.reply(200, '<!doctype html><meta charset="utf-8"><title>Пароль сохранён</title><p>Пароль сохранён. Эту вкладку можно закрыть.</p>')
            done.set()

    server = remote_access.RemoteHTTPServer(('127.0.0.1', port), Handler)
    server.timeout = 1
    server.setup_done = done
    return server


# Разбирает параметры запуска и выполняет основной сценарий программы.
# При недопустимом состоянии возбуждает ValueError.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials-file', type=Path, default=remote_access.DEFAULT_CREDENTIALS)
    parser.add_argument('--web', action='store_true', help='Временная форма только на 127.0.0.1')
    parser.add_argument('--port', type=int, default=18766)
    args = parser.parse_args()
    if args.web:
        server = setup_server(args.credentials_file, args.port)
        print(f'http://127.0.0.1:{server.server_port}', flush=True)
        deadline = time.monotonic() + 900
        try:
            while not server.setup_done.is_set() and time.monotonic() < deadline:
                server.handle_request()
        finally:
            server.server_close()
        return 0 if server.setup_done.is_set() else 1
    password = getpass.getpass('Пароль для внешнего входа (от 12 символов): ')
    if not hmac.compare_digest(password.encode(), getpass.getpass('Повтори пароль: ').encode()):
        raise ValueError('Пароли не совпадают')
    remote_access.save_password(args.credentials_file, password)
    print('Пароль сохранён. Локальный вход остался прежним.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
