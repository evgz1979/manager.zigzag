import json
import unittest
import uuid

import test_server as fixtures


class CalendarStickerTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

    def post(self, **changes):
        return self.http('/api/calendar-sticker', 'POST', json.dumps({
            'id': self.identity, 'revision': 0, 'week': '2026-11-23',
            'x': 5000, 'y': 9000, 'text': '  Первая строка\nВторая <b> 🧵  ',
            'deleted': False, **changes}))

    def test_edit_move_delete_and_retry_keep_uuid_and_history(self):
        self.identity = str(uuid.uuid4())
        status, _, body = self.post()
        self.assertEqual(status, 200, body)
        original = json.loads(body)
        self.assertEqual(original['revision'], 1)
        self.assertEqual(json.loads(self.post()[2]), original)
        self.assertEqual(self.post(text='Другая запись')[0], 409)
        status, _, body = self.post(revision=1, week='2026-11-30', x=10000, y=0)
        self.assertEqual(status, 200, body)
        moved = json.loads(body)
        self.assertEqual(moved['text'], original['text'])
        self.assertEqual(moved['id'], original['id'])
        self.assertEqual(moved['revision'], 2)
        status, _, body = self.http('/api/orders')
        self.assertEqual(status, 200, body)
        overview = json.loads(body)
        self.assertEqual(overview['calendar_stickers'], [moved])
        self.assertEqual(overview['calendar_events'], [])
        self.assertEqual(self.post(revision=1, text='Устаревшая правка')[0], 409)
        status, _, body = self.post(revision=2, week=moved['week'], x=10000, y=0, deleted=True)
        self.assertEqual(status, 200, body)
        deleted = json.loads(body)
        self.assertEqual(deleted['deleted'], 1)
        self.assertEqual(json.loads(self.http('/api/calendar-sticker?id=' + self.identity)[2]), deleted)
        self.assertEqual(json.loads(self.http('/api/orders')[2])['calendar_stickers'], [])
        self.assertEqual(self.post(revision=3, text='Вернуть без разрешения')[0], 409)
        with fixtures.manager.order_store().connect() as db:
            history = [json.loads(row[0]) for row in db.execute(
                "SELECT data FROM metadata_history WHERE entity='calendar_stickers' AND identity=? ORDER BY seq", (self.identity,))]
        self.assertEqual(len(history), 2)
        for previous, saved in zip(history, [original, moved]):
            self.assertAlmostEqual(previous.pop('updated'), saved.pop('updated'), places=4)
            self.assertEqual(previous, saved)

    def test_invalid_positions_dont_create_a_sticker(self):
        self.identity = str(uuid.uuid4())
        for values in ({'x': True}, {'x': 10001}, {'y': -1}, {'y': 1.5}, {'week': '2026-11-24'},
                       {'week': '2026-11-31'}, {'text': 'a\x00b'}, {'text': 'x' * 2001}, {'deleted': 0}):
            with self.subTest(values=values):
                self.assertEqual(self.post(**values)[0], 400)
        self.assertIsNone(json.loads(self.http('/api/calendar-sticker?id=' + self.identity)[2]))
