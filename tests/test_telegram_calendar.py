import base64
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
        (self.data / 'telegram.ini').write_text(f'[telegram]\nbot_token = {TOKEN}\nchat_id = -123456\n')
        self.env = patch.dict('os.environ', {'MANAGER_TELEGRAM_SETTINGS': ''})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()

    def test_moscow_week_png_original_caption_and_destination(self):
        with patch.object(telegram.urllib.request, 'urlopen') as post:
            post.return_value.__enter__.return_value.read.return_value = b'{"ok":true,"result":{"message_id":42}}'
            result = telegram.send(PNG, '2026-10-26', self.data, now=NOW)
        self.assertEqual(result, {'ok': True, 'start': '2026-10-26', 'through': '2026-11-15'})
        request = post.call_args.args[0]
        self.assertEqual(request.full_url, f'https://api.telegram.org/bot{TOKEN}/sendDocument')
        self.assertIn(PNG, request.data)
        self.assertIn(b'name="chat_id"\r\n\r\n-123456', request.data)
        self.assertIn(b'zigzag-calendar-2026-10-26.png', request.data)
        self.assertIn('26.10.2026 — 15.11.2026'.encode(), request.data)
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


class TelegramCalendarHTTPTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

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
