import base64
import json
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as xml

import caldav
import caldav_events
from calendar_events import CalendarEvents
import test_remote_access as remote


class CalendarDAVTests(unittest.TestCase):
    def setUp(self):
        remote.RemoteAccessTests.setUp(self)
        self.addCleanup(remote.RemoteAccessTests.tearDown, self)
        self.data = self.path / 'local'
        self.data.mkdir()
        data_patch = patch.object(remote.manager, 'DATA_DIR', self.data)
        data_patch.start()
        self.addCleanup(data_patch.stop)
        self.events = CalendarEvents(remote.manager.order_store())
        self.orders = [{'id': '5773a4d8-ef23-8683-8bae-e782569197cd', 'title': 'Витрина',
                        'client': 'Клиент', 'path': 'Клиент/Объект/Витрина', 'updated': self.now,
                        'deadline_weeks': ['2026-11-16'], 'calendar_events': {},
                        'calendar_week_events': {'2026-11-16': 'Монтаж'}}]
        self.remote.caldav = caldav.CalendarDAV(self.events, lambda: self.orders, remote.HOST)
        self.session_cookie = self.session()
        self.settings_headers = {'Cookie': self.session_cookie, 'Origin': 'https://' + remote.HOST,
                                 'Content-Type': 'application/json', 'X-Manager-Settings': '1'}
        self.dav_headers = self.issue_password()

    http = remote.RemoteAccessTests.http
    serve = remote.RemoteAccessTests.serve
    session = remote.RemoteAccessTests.session
    login = remote.RemoteAccessTests.login
    form = remote.RemoteAccessTests.form

    def issue_password(self):
        status, _, body = self.http(remote.auth.SETTINGS_PATH, headers=self.settings_headers)
        self.assertEqual(status, 200, body)
        self.form_token = json.loads(body)['csrf']
        payload = json.dumps({'csrf': self.form_token, 'action': 'generate'})
        status, _, body = self.http(caldav.SETTINGS, 'POST', payload, self.settings_headers)
        self.assertEqual(status, 200, body)
        password = json.loads(body)['password']
        secret = (caldav.USERNAME + ':' + password).encode()
        return {'Authorization': 'Basic ' + base64.b64encode(secret).decode()}

    def request(self, route, method='GET', body=None, **headers):
        return self.http(route, method, body, {**self.dav_headers, **headers})

    def card(self, uid='Apple-event_777', title='Замер', notes='За́метка 🧵', start='20261119T090000Z',
             end='20261119T100000Z'):
        return caldav_events.encode_lines([
            'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Apple//Calendar//EN', 'BEGIN:VEVENT',
            'UID:' + uid, 'DTSTAMP:20261114T070000Z', 'DTSTART:' + start, 'DTEND:' + end,
            'SUMMARY:' + caldav_events.escape(title), 'DESCRIPTION:' + caldav_events.escape(notes),
            'LOCATION:Офис', 'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:Напоминание',
            'TRIGGER:-PT15M', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR',
        ])

    def test_discovery_and_isolation(self):
        status, headers, _ = self.http(caldav.WELL_KNOWN, 'PROPFIND')
        self.assertEqual(status, 301)
        self.assertIn(('Location', caldav.ROOT), headers)
        self.assertEqual(self.http(caldav.ROOT, 'PROPFIND')[0], 401)
        self.assertEqual(self.http(caldav.ROOT, 'PROPFIND', headers={'Cookie': self.session_cookie})[0], 401)
        self.assertEqual(self.request('/api/orders')[0], 401)
        self.assertEqual(self.request(caldav.ROOT, 'OPTIONS', Host='localhost')[0], 421)
        self.assertEqual(self.http(caldav.ROOT, 'PROPFIND', headers=self.dav_headers, server=self.local)[0], 501)
        self.assertEqual(self.http(caldav.SETTINGS, 'POST', json.dumps({'csrf': self.form_token, 'action': 'revoke'}),
                                  {**self.settings_headers, 'Origin': 'https://other.example'})[0], 403)
        status, _, body = self.request(caldav.ROOT, 'PROPFIND',
                                       '<propfind xmlns="DAV:"><prop><current-user-principal/></prop></propfind>')
        self.assertEqual(status, 207, body)
        self.assertEqual(xml.fromstring(body).find('.//' + caldav.DAV + 'current-user-principal/' + caldav.DAV + 'href').text,
                         caldav.PRINCIPAL)
        status, _, body = self.request(caldav.HOME, 'PROPFIND', Depth='1')
        self.assertEqual(status, 207, body)
        self.assertIn(caldav.EVENTS.encode(), body)
        self.assertIn(caldav.ORDERS.encode(), body)
        self.assertIn('Зигзаг · События', body.decode())
        old_key = self.dav_headers
        self.dav_headers = self.issue_password()
        self.assertEqual(self.http(caldav.ROOT, 'PROPFIND', headers=old_key)[0], 401)
        self.assertEqual(self.request(caldav.ROOT, 'PROPFIND')[0], 207)
        self.assertEqual(self.http(caldav.SETTINGS, 'POST', json.dumps({'csrf': self.form_token, 'action': 'revoke'}),
                                  self.settings_headers)[0], 200)
        self.assertEqual(self.request(caldav.ROOT, 'PROPFIND')[0], 401)

    def test_changes_from_both_calendars_and_stale_versions(self):
        path = caldav.EVENTS + 'apple-event.ics'
        options = {'Content-Type': 'text/calendar; charset=utf-8'}
        title = 'Большой замер ' + '🧵 Кириллица ' * 12
        self.assertEqual(self.request(path, 'PUT', self.card(title=title), Origin='https://' + remote.HOST, **options)[0], 403)
        self.assertEqual(self.request(path, 'PUT', self.card(title=title), **options, **{'If-None-Match': '*'})[0], 201)
        first, = self.events.list()
        self.assertEqual((first['date'], first['text'], first['revision']), ('2026-11-19', title, 1))
        status, headers, body = self.request(path)
        self.assertEqual(status, 200)
        self.assertTrue(all(len(line) <= 75 for line in body.split(b'\r\n')))
        _, _, _, _, uid, summary, _, _ = caldav_events.parse(body)
        self.assertEqual((uid, summary), ('Apple-event_777', title))
        tag = dict(headers)['ETag']
        self.assertEqual(self.request(path, 'HEAD')[2], b'')
        self.assertEqual(self.request(path, 'GET', **{'If-None-Match': tag})[0], 304)
        self.assertEqual(self.request(path, 'PUT', self.card(title='Без версии'), **options)[0], 428)

        self.events.set_trip(first | {'is_trip': True})
        self.assertEqual(self.request(path, 'PUT', self.card(title='Устарело'), **options, **{'If-Match': tag})[0], 412)
        self.assertEqual(self.request(path, 'DELETE', **{'If-Match': tag})[0], 412)
        tag = dict(self.request(path)[1])['ETag']
        changed = self.card(title='Другой день', start='20261120T223000Z', end='20261120T233000Z')
        self.assertEqual(self.request(path, 'PUT', changed, **options, **{'If-Match': tag})[0], 204)
        second, = self.events.list()
        self.assertEqual((second['id'], second['date'], second['text'], second['is_trip'], second['revision']),
                         (first['id'], '2026-11-21', 'Другой день', 1, 3))
        self.events.move(second | {'days': 3})
        self.events.save(self.events.get(first['id']) | {'text': 'Из браузера'})
        status, headers, body = self.request(path)
        self.assertEqual(status, 200)
        self.assertIn(b'DTSTART:20261123T223000Z', body)
        self.assertIn('Из браузера', body.decode())
        self.assertIn('LOCATION:Офис', body.decode())
        self.assertIn(b'BEGIN:VALARM', body)
        tag = dict(headers)['ETag']
        with patch.object(remote.manager, 'HANDOFF_STOP') as stop:
            stop.is_set.return_value = True
            self.assertEqual(self.request(path, 'DELETE', **{'If-Match': tag})[0], 503)
        self.assertEqual(self.request(path, 'DELETE', **{'If-Match': tag})[0], 204)
        self.assertEqual(self.events.list(), [])
        self.assertEqual(self.request(path, 'PUT', changed, **options)[0], 412)
        self.assertEqual(self.request(caldav.EVENTS + 'duplicate.ics', 'PUT', changed, **options)[0], 403)
        removed = self.events.get(first['id'])
        self.events.set_deleted(removed, False)
        self.assertEqual(self.request(path)[0], 200)
        with self.events.connect() as db:
            history = db.execute("SELECT COUNT(*) FROM metadata_history WHERE entity='calendar_events' AND identity=?",
                                 (first['id'],)).fetchone()[0]
            self.assertGreaterEqual(history, 6)

    def test_query_multiget_and_order_access(self):
        order, = caldav_events.order_resources(self.orders, remote.HOST)
        href = caldav.ORDERS + order.name
        self.assertEqual(self.request(href, 'DELETE', **{'If-Match': order.etag})[0], 403)
        self.assertEqual(self.request(href, 'PUT', self.card(), **{'Content-Type': 'text/calendar'})[0], 403)
        status, _, body = self.request(href)
        self.assertEqual(status, 200)
        self.assertIn(b'DTSTART;VALUE=DATE:20261116', body)
        self.assertIn(b'DTEND;VALUE=DATE:20261123', body)
        self.assertIn('https://' + remote.HOST + '/?path=', body.decode())
        query = '<C:calendar-query xmlns:C="urn:ietf:params:xml:ns:caldav" xmlns:D="DAV:"><D:prop><D:getetag/><C:calendar-data/></D:prop><C:filter><C:comp-filter name="VCALENDAR"><C:comp-filter name="VEVENT"><C:time-range start="{}" end="{}"/></C:comp-filter></C:comp-filter></C:filter></C:calendar-query>'
        status, _, body = self.request(caldav.ORDERS, 'REPORT', query.format('20261121T000000Z', '20261122T000000Z'))
        self.assertEqual(status, 207)
        self.assertEqual(xml.fromstring(body).find('.//' + caldav.DAV + 'href').text, href)
        status, _, body = self.request(caldav.ORDERS, 'REPORT', query.format('20261125T000000Z', '20261126T000000Z'))
        self.assertEqual(status, 207)
        self.assertEqual(len(xml.fromstring(body)), 0)
        multiget = '<C:calendar-multiget xmlns:C="urn:ietf:params:xml:ns:caldav" xmlns:D="DAV:"><D:prop><D:getetag/><C:calendar-data/></D:prop><D:href>{}</D:href><D:href>{}missing.ics</D:href></C:calendar-multiget>'
        status, _, body = self.request(caldav.ORDERS, 'REPORT', multiget.format(href, caldav.ORDERS))
        self.assertEqual(status, 207)
        root = xml.fromstring(body)
        self.assertEqual(len(root), 2)
        self.assertIn(order.etag, body.decode())
        self.assertIn(b'404 Not Found', body)

    def test_weekly_roundtrip_and_recurring_rejected(self):
        import uuid
        uid = str(uuid.uuid4())
        initial = self.events.save({'id': uid, 'revision': 0, 'period': 'week', 'date': '2026-11-16', 'text': 'На неделю'})
        path = caldav.EVENTS + uid + '.ics'
        status, headers, body = self.request(path)
        self.assertEqual(status, 200)
        tag = dict(headers)['ETag']
        self.assertIn(b'DTEND;VALUE=DATE:20261123', body)
        recurring = body.replace(b'END:VEVENT', b'RRULE:FREQ=WEEKLY\r\nEND:VEVENT')
        self.assertEqual(self.request(path, 'PUT', recurring, **{'Content-Type': 'text/calendar', 'If-Match': tag})[0], 403)
        self.assertEqual(self.events.get(uid), initial)
        moved = body.replace(b'20261116', b'20261123').replace(b'20261123\r\nEND:VEVENT', b'20261130\r\nEND:VEVENT')
        self.assertEqual(self.request(path, 'PUT', moved, **{'Content-Type': 'text/calendar', 'If-Match': tag})[0], 204)
        self.assertEqual((self.events.get(uid)['date'], self.events.get(uid)['period']), ('2026-11-23', 'week'))
