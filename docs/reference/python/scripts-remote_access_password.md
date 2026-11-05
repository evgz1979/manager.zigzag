# scripts/remote_access_password.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/remote_access_password.py](../../../scripts/remote_access_password.py).

Initial password setup on loopback, or interactively in a private terminal.

Импорты Python, включая локальные: `argparse`, `getpass`, `hmac`, `html`, `http.server`, `pathlib`, `remote_access`, `secrets`, `sys`, `threading`, `time`, `urllib.parse`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-main"></a>

## main

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def main():
```

Разбирает параметры запуска и выполняет основной сценарий программы.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `setup_server`, `print`, `time.monotonic`, `server.setup_done.is_set`, `server.handle_request`, `server.server_close`, `getpass.getpass`, `hmac.compare_digest`, `password.encode`, `getpass.getpass('Повтори пароль: ').encode`, `ValueError`, `remote_access.save_password`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
0 if server.setup_done.is_set() else 1
0
```

<a id="symbol-setup_server"></a>

## setup_server

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def setup_server(path, port=18766):
```

Создаёт настройки рабочей установки из проверенных параметров развёртывания.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path(path).expanduser`, `Path`, `path.exists`, `path.is_symlink`, `ValueError`, `secrets.token_urlsafe`, `threading.Event`, `threading.Lock`, `remote_access.RemoteHTTPServer`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
server
```

<a id="symbol-setup_server.Handler"></a>

## setup_server.Handler

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `class`.

```python
class Handler(BaseHTTPRequestHandler):
```

Объединяет операции модуля: временная loopback-форма первоначального задания пароля владельцем.

Основные операции: setup, log_message, reply, allowed, page; остальные описаны у методов.

<a id="symbol-setup_server.Handler.allowed"></a>

## setup_server.Handler.allowed

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def allowed(self):
```

Проверяет допустимость одной папки в текущем каталоге.

Возвращает `self.headers.get_all('Host', []) == ['127.0.0.1:' + str(self.server.server_port)]`.

Непосредственные вызовы: `self.headers.get_all`, `str`.

Выражения возврата (ветки читаются в исходнике):

```python
self.headers.get_all('Host', []) == ['127.0.0.1:' + str(self.server.server_port)]
```

<a id="symbol-setup_server.Handler.do_GET"></a>

## setup_server.Handler.do_GET

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def do_GET(self):
```

Обслуживает GET через проверки и маршрутизацию текущего обработчика.

Передаёт работу `self.allowed`, `self.reply`, `done.is_set`.

Непосредственные вызовы: `self.allowed`, `self.reply`, `done.is_set`, `self.page`.

<a id="symbol-setup_server.Handler.do_POST"></a>

## setup_server.Handler.do_POST

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def do_POST(self):
```

Проверяет и маршрутизирует запрос изменения данных текущего обработчика.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `str`, `self.allowed`, `self.headers.get_all`, `self.reply`, `len`, `lengths[0].isdigit`, `int`, `self.headers.get`, `self.headers.get_content_type`, `ValueError`, `urllib.parse.parse_qs`, `self.rfile.read(int(lengths[0])).decode`, `self.rfile.read`, `any`, `fields.values`, `hmac.compare_digest`, `fields.get('csrf', [''])[0].encode`, `fields.get`, `csrf.encode`, `password.encode`, `fields.get('confirmation', [''])[0].encode`, `remote_access.save_password`, `self.page`, `done.set`.

Явные исключения: `ValueError`.

<a id="symbol-setup_server.Handler.log_message"></a>

## setup_server.Handler.log_message

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def log_message(self, *_):
```

Записывает предусмотренное диагностическое сообщение обработчика.

Выполняет локальные проверки или меняет только переданные структуры данных.

<a id="symbol-setup_server.Handler.page"></a>

## setup_server.Handler.page

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def page(self, error=''):
```

Формирует страницу временного локального ввода пароля.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `html.escape`.

Выражения возврата (ветки читаются в исходнике):

```python
f'<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Пароль для внешнего входа · Зигзаг</title>\n<style>body{{font:15px -apple-system,sans-serif;color:#263738;background:#f7f9f8;margin:0;padding:24px}}main{{box-sizing:border-box;max-width:400px;margin:8vh auto;background:white;border:1px solid #dce5e0;border-radius:14px;padding:26px}}h1{{font-size:23px}}label{{display:block;margin:18px 0}}input{{box-sizing:border-box;width:100%;padding:12px;margin-top:7px;border:1px solid #bbcfc5;border-radius:8px;font:16px -apple-s...
```

<a id="symbol-setup_server.Handler.reply"></a>

## setup_server.Handler.reply

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def reply(self, status, body):
```

Отправляет локальный ответ защищённого обработчика с нужным статусом.

Передаёт работу `body.encode`, `self.send_response`, `self.send_header`.

Непосредственные вызовы: `body.encode`, `self.send_response`, `self.send_header`, `str`, `len`, `self.end_headers`, `self.wfile.write`.

<a id="symbol-setup_server.Handler.setup"></a>

## setup_server.Handler.setup

[scripts/remote_access_password.py](../../../scripts/remote_access_password.py) · `function`.

```python
def setup(self):
```

Настраивает ограничения соединения перед обработкой защищённого запроса.

Передаёт работу `super().setup`, `super`, `self.connection.settimeout`.

Непосредственные вызовы: `super().setup`, `super`, `self.connection.settimeout`.
