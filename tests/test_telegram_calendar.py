import base64
import configparser
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

import telegram_calendar as telegram
import test_server as fixtures

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4x8AAAAASUVORK5CYII=')
TOKEN = '123456:' + 'a' * 32
NOW = datetime(2026, 10, 25, 21, 1, tzinfo=timezone.utc)  # Monday in Moscow.


class TelegramCalendarTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.data = Path(self.temporary.name)
        (self.data / 'telegram.ini').write_text(f'[telegram]\npurpose = manager-calendar\nbot_token = {TOKEN}\nchat_id = -123456\n')
        self.env = patch.dict('os.environ', {'MANAGER_TELEGRAM_SETTINGS': ''})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()

    def test_moscow_week_png_original_caption_and_destination(self):
        with patch.object(telegram.urllib.request, 'urlopen') as post:
            post.return_value.__enter__.return_value.read.return_value = b'{"ok":true,"result":{"message_id":42}}'
            result = telegram.send(PNG, '2026-10-26', self.data, now=NOW)
        self.assertEqual(result, {'ok': True, 'start': '2026-10-26', 'through': '2026-11-08'})
        request = post.call_args.args[0]
        self.assertEqual(request.full_url, f'https://api.telegram.org/bot{TOKEN}/sendDocument')
        self.assertIn(PNG, request.data)
        self.assertIn(b'name="chat_id"\r\n\r\n-123456', request.data)
        self.assertIn(b'zigzag-calendar-2026-10-26.png', request.data)
        self.assertIn('26.10.2026 — 08.11.2026'.encode(), request.data)
        self.assertNotIn(TOKEN, json.dumps(result))
        self.assertEqual(post.call_args.kwargs['timeout'], 40)

    def test_unknown_settings_wrong_week_and_invalid_image_do_not_send(self):
        with patch.object(telegram.urllib.request, 'urlopen') as post:
            for image, start in ((b'bad', '2026-10-26'), (PNG, '2026-10-19')):
                with self.assertRaises(ValueError):
                    telegram.send(image, start, self.data, now=NOW)
            (self.data / 'telegram.ini').write_text('[telegram]\nbot_token = invalid\nchat_id = 1\n')
            with self.assertRaises(telegram.TelegramError):
                telegram.send(PNG, '2026-10-26', self.data, now=NOW)
            post.assert_not_called()

    def test_errors_never_leak_token_or_retry_ambiguous_send(self):
        for error in (urllib.error.URLError(f'https://api.telegram.org/bot{TOKEN}'),
                      urllib.error.HTTPError(f'https://api.telegram.org/bot{TOKEN}', 403, TOKEN, {}, io.BytesIO())):
            with self.subTest(error=type(error)), patch.object(telegram.urllib.request, 'urlopen', side_effect=error) as post:
                with self.assertRaises(telegram.TelegramError) as caught:
                    telegram.send(PNG, '2026-10-26', self.data, now=NOW)
                self.assertNotIn(TOKEN, str(caught.exception))
                post.assert_called_once()
        for response in (b'{"ok":false}', b'{"ok":true,"result":null}', b'not json'):
            with patch.object(telegram.urllib.request, 'urlopen') as post:
                post.return_value.__enter__.return_value.read.return_value = response
                with self.assertRaises(telegram.TelegramError):
                    telegram.send(PNG, '2026-10-26', self.data, now=NOW)
                post.assert_called_once()

    def test_actu_settings_and_rotated_actu_token_are_never_used(self):
        old = f'[telegram]\nbot_token = {TOKEN}\nchat_id = 42\n'
        (self.data / 'telegram.ini').write_text(old)
        with patch.object(telegram.urllib.request, 'urlopen') as post:
            self.assertEqual(telegram.status(self.data), {'configured': False})
            with self.assertRaises(telegram.TelegramError):
                telegram.send(PNG, '2026-10-26', self.data, now=NOW)
            (self.data / 'telegram.ini').rename(self.data / 'telegram-actu-disabled.ini')
            with self.assertRaises(telegram.TelegramError):
                telegram.configure({'action':'chats','bot_token':'123456:' + 'b'*32}, self.data)
            post.assert_not_called()
        self.assertFalse((self.data / 'telegram.ini').exists())

    def test_discovery_does_not_consume_messages_and_only_returns_private_chat_labels(self):
        with patch.object(telegram, 'bot_api') as api:
            api.side_effect = [
                {'id':123456,'is_bot':True,'username':'zigzag_calendar_bot'},
                [{'message':{'chat':{'id':42,'type':'private','first_name':'Евгений'},'text':'НЕ ВОЗВРАЩАТЬ'}},
                 {'message':{'chat':{'id':-20,'type':'group','title':'Группа'}}}],
            ]
            result = telegram.configure({'action':'chats','bot_token':TOKEN}, self.data)
        self.assertEqual(result, {'bot_username':'zigzag_calendar_bot','chats':[{'id':'42','label':'Евгений'}]})
        self.assertEqual(api.call_args_list[1].args[2], {'timeout':0,'limit':100})
        self.assertNotIn(TOKEN, json.dumps(result))
        self.assertNotIn('НЕ ВОЗВРАЩАТЬ', json.dumps(result))

    def test_setup_checks_bot_and_private_recipient_before_atomic_secret_save(self):
        with patch.object(telegram, 'bot_api') as api:
            api.side_effect = [{'id':123456,'is_bot':True,'username':'zigzag_calendar_bot'}, {'id':42,'type':'private'}]
            result = telegram.configure({'action':'save','bot_token':TOKEN,'chat_id':'42'}, self.data)
        self.assertEqual(result, {'configured':True,'chat_id':'42','bot_username':'zigzag_calendar_bot'})
        self.assertEqual(telegram.status(self.data), result)
        self.assertEqual(telegram.settings(self.data), (TOKEN,'42'))
        self.assertEqual((self.data / 'telegram.ini').stat().st_mode & 0o777, 0o600)
        self.assertNotIn(TOKEN, json.dumps(result))
        before = (self.data / 'telegram.ini').read_bytes()
        with patch.object(telegram, 'bot_api') as api:
            api.side_effect = [{'id':123456,'is_bot':True,'username':'zigzag_calendar_bot'}, {'id':99,'type':'group'}]
            with self.assertRaises(ValueError):
                telegram.configure({'action':'save','bot_token':TOKEN,'chat_id':'99'}, self.data)
        self.assertEqual((self.data / 'telegram.ini').read_bytes(), before)

    def test_failed_setup_preserves_saved_settings_and_does_not_return_secret(self):
        before = (self.data / 'telegram.ini').read_bytes()
        with patch.object(telegram, 'bot_api', side_effect=telegram.TelegramError('Нет связи')):
            with self.assertRaises(telegram.TelegramError):
                telegram.configure({'action':'save','bot_token':TOKEN,'chat_id':'42'}, self.data)
        self.assertEqual((self.data / 'telegram.ini').read_bytes(), before)


class TelegramCalendarHTTPTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

    def test_settings_api_does_not_expose_token_and_rejects_foreign_posts(self):
        headers = {'Content-Type':'application/json','X-Manager-Calendar':'1'}
        route = '/api/calendar-telegram-settings'
        with patch.object(fixtures.manager.telegram_calendar, 'configure', return_value={'configured':True}) as configure:
            self.assertEqual(self.http(route,'POST',json.dumps({'bot_token':TOKEN}),{})[0],403)
            self.assertEqual(self.http(route,'POST',json.dumps({'bot_token':TOKEN}),{**headers,'Origin':'https://foreign.example'})[0],403)
            configure.assert_not_called()
            self.assertEqual(json.loads(self.http(route)[2]), {'configured':False})
            self.assertEqual(self.http(route,'POST',json.dumps({'action':'save','bot_token':TOKEN,'chat_id':'42'}),headers)[0],200)
            configure.assert_called_once()
        self.assertFalse(fixtures.manager.DATA_DIR.exists())
        with telegram.SEND_LOCK:
            self.assertEqual(self.http(route,'POST','{}',headers)[0],409)
        with patch.object(fixtures.manager.telegram_calendar,'configure', side_effect=configparser.Error(TOKEN)):
            status, _, body = self.http(route,'POST','{}',headers)
            self.assertEqual(status,400)
            self.assertNotIn(TOKEN,body.decode())

    def test_binary_route_only_same_origin_and_limited_image_with_no_database_changes(self):
        headers = {'Content-Type': 'image/png', 'X-Manager-Calendar': '1'}
        route = '/api/calendar-telegram?start=2026-10-26'
        with patch.object(fixtures.manager.telegram_calendar, 'send', return_value={'ok': True}) as send:
            for invalid in ({}, {**headers, 'Origin': 'https://foreign.example'}):
                self.assertEqual(self.http(route, 'POST', PNG, invalid)[0], 403)
            self.assertEqual(self.http(route, 'POST', PNG, {**headers, 'Content-Length': str(telegram.MAX_IMAGE_BYTES + 1)})[0], 413)
            self.assertEqual(self.http('/api/calendar-telegram', 'POST', PNG, headers)[0], 400)
            send.assert_not_called()
            status, _, body = self.http(route, 'POST', PNG, headers)
            self.assertEqual((status, json.loads(body)), (200, {'ok': True}))
            send.assert_called_once_with(PNG, '2026-10-26', fixtures.manager.DATA_DIR)
        self.assertFalse(fixtures.manager.DATA_DIR.exists())
        with telegram.SEND_LOCK:
            self.assertEqual(self.http(route, 'POST', PNG, headers)[0], 429)
        with patch.object(fixtures.manager.telegram_calendar, 'send', side_effect=telegram.TelegramError('Нет подтверждения')):
            self.assertEqual(self.http(route, 'POST', PNG, headers)[0], 502)
        self.assertFalse(telegram.SEND_LOCK.locked())
