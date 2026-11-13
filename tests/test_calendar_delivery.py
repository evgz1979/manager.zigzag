from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import calendar_delivery as delivery
import calendar_todos
from local_metadata import MetadataStore
from orders import OrderStore
import telegram_calendar as telegram
import telegram_calendar_commands as commands
import telegram_inbox as inbox
from test_telegram_calendar import PNG, NOW
from test_telegram_inbox import message

APP = Path(__file__).resolve().parents[1]


class CalendarDeliveryTests(unittest.TestCase):
    def snapshot(self, **changes):
        return {'orders': [], 'calendar_supplier_orders': [], 'calendar_events': [], 'calendar_invoice_plans': [], **changes}

    def order(self, **changes):
        return {'path': 'client/order', 'title': 'Окна', 'deadline_weeks': ['2026-10-19'],
                'calendar_events': {}, 'calendar_week_events': {}, 'calendar_completed': {'day': [], 'week': []},
                'calendar_inactive': {'day': [], 'week': []}, **changes}

    @unittest.skipUnless(shutil.which('node'), 'Node.js is required')
    def test_browser_and_server_choose_same_optional_previous_week(self):
        empty = self.order()
        pending = self.order(calendar_week_events={'2026-10-19': 'Осталось'})
        closed = {**pending, 'calendar_inactive': {'week': ['2026-10-19'], 'day': []}}
        cases = [self.snapshot(), self.snapshot(orders=[empty]), self.snapshot(orders=[pending]),
                 self.snapshot(calendar_supplier_orders=[{**pending, 'work_supplier': 'glass'}]),
                 self.snapshot(orders=[closed]), self.snapshot(orders=[{**empty, 'calendar_compact': True}]),
                 self.snapshot(calendar_events=[{'date': '2026-10-20', 'period': 'day'}]),
                 self.snapshot(calendar_invoice_plans=[{'date': '2026-10-19', 'period': 'week', 'is_carryover': True}]),
                 self.snapshot(orders=[self.order(deadline_weeks=['2026-10-12'], calendar_week_events={'2026-10-12':'Older'})]),
                 self.snapshot(orders=[{**empty, 'calendar_events': None}])]
        expected = [('2026-10-19' if index in {2,6,7,9} else '2026-10-26', '2026-11-08') for index in range(len(cases))]
        for group in ['calendar_events', 'calendar_invoice_plans']:
            for period in ['day', 'week']:
                for flags, retained in [({'is_completed': 1}, False), ({'is_inactive': 1}, False),
                                        ({'is_completed': True}, False), ({'is_inactive': True}, False),
                                        ({'is_completed': False, 'is_inactive': 0}, True),
                                        ({'is_completed': None, 'is_inactive': 'unknown'}, True),
                                        ({'deleted': 1}, False)]:
                    cases.append(self.snapshot(**{group: [{'date': '2026-10-19', 'period': period, **flags}]}))
                    expected.append(('2026-10-19' if retained else '2026-10-26', '2026-11-08'))
        before = json.dumps(cases, sort_keys=True)
        self.assertEqual([delivery.period(case, NOW) for case in cases], expected)
        raw = subprocess.run(['node', str(Path(__file__).with_name('calendar-delivery.cjs'))],
                             input=json.dumps([{'snapshot': case, 'now': NOW.isoformat()} for case in cases]), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(raw.stdout), [list(value) for value in expected])
        self.assertEqual(json.dumps(cases, sort_keys=True), before)

    def test_previous_digest_includes_only_visible_marked_rows_and_keeps_next_week(self):
        order = self.order(calendar_week_events={'2026-10-19': 'Прошлая', '2026-11-02': 'Следующая'},
                           deadline_weeks=['2026-10-19', '2026-11-02'],
                           calendar_watch_todos={'week': ['2026-10-19','2026-11-02'], 'day': []},
                           todo_groups=[{'label':'Заказ', 'items':[{'text':'Позвонить', 'done':False}]}])
        with patch('calendar_delivery.current_week', return_value=datetime(2026,10,26).date()):
            text = calendar_todos.digest(self.snapshot(orders=[order]), '2026-10-19', '2026-11-08')
            self.assertIn('Прошлая', text)
            self.assertIn('Следующая', text)
            order['calendar_inactive']['week'] = ['2026-10-19']
            text = calendar_todos.digest(self.snapshot(orders=[order]), '2026-10-19', '2026-11-08')
            self.assertNotIn('Прошлая', text)
            self.assertIn('Следующая', text)

    def test_supplier_todo_digest_survives_move_out_of_png(self):
        supplier = self.order(work_supplier='glass', deadline_weeks=[], calendar_compact=True,
                              calendar_week_events={'2026-10-26': 'В пределах периода', '2026-10-19': 'До периода'},
                              calendar_watch_todos={'week': ['2026-10-19', '2026-10-26']})
        snapshot = self.snapshot(calendar_supplier_orders=[supplier])
        start, through = delivery.period(snapshot, NOW)
        self.assertEqual((start, through), ('2026-10-26', '2026-11-08'))
        text = calendar_todos.digest(snapshot, start, through)
        self.assertIn('В пределах периода', text)
        self.assertNotIn('До периода', text)

    def test_png_extended_caption_and_bounds(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(telegram, 'settings', return_value=('123:test', '42')), patch.object(telegram, 'api_request', return_value={'message_id':1}) as send:
            result = telegram.send(PNG, '2026-10-19', Path(temp), now=NOW, through='2026-11-08')
            self.assertEqual(result['start'], '2026-10-19')
            self.assertIn('19.10.2026 — 08.11.2026'.encode(), send.call_args.args[0].data)
            for start,end in [('2026-10-12','2026-11-08'), ('2026-10-19','2026-11-01'), ('2026-10-19',None)]:
                with self.assertRaises(ValueError):
                    telegram.send(PNG,start,Path(temp),now=NOW,through=end)
            send.assert_called_once()

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS WebKit renderer')
    def test_native_renderer_uses_three_weeks_and_escaped_data_without_http(self):
        now = datetime.now(timezone.utc)
        current = telegram.current_week(now)
        from datetime import timedelta
        previous = (current-timedelta(days=7)).isoformat()
        order = self.order(deadline_weeks=[previous], calendar_week_events={previous:'Проверить <детали> 😀'},
                           title='</script><script>throw 1</script>')
        snapshot = self.snapshot(orders=[order])
        with tempfile.TemporaryDirectory() as temp:
            image = delivery.render(snapshot, APP, Path(temp), now)
        width,height = struct.unpack('>II',image[16:24])
        self.assertEqual(width,2880)
        self.assertGreater(height,1300)


class CalendarCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.store = OrderStore(self.base/'documents', self.base/'data', {})
        self.settings = patch.object(telegram,'settings',return_value=('123456:test','42'))
        self.settings.start()

    def tearDown(self):
        self.settings.stop()
        self.temp.cleanup()

    def records(self):
        with MetadataStore(self.store).connect() as db:
            return [commands.decode(row) for row in db.execute('SELECT * FROM metadata_records WHERE kind=?',(commands.KIND,))]

    def test_command_is_committed_with_offset_not_an_inbox_todo_and_replay_never_resends(self):
        command = message(text='/calendar')
        self.assertEqual(inbox.ingest(self.store,'123456','42',[command]),0)
        self.assertEqual(inbox.items(self.store),[])
        with patch.object(self.store,'target',side_effect=AssertionError('No cloud')), patch('telegram_calendar_commands.telegram.bot_api') as reply:
            sender = unittest.mock.Mock(return_value={'ok':True})
            commands.process(self.store,self.base,sender)
            inbox.ingest(self.store,'123456','42',[command,message(11,text='/calendar')])
            commands.process(self.store,self.base,sender)
            sender.assert_called_once()
            reply.assert_not_called()
        self.assertEqual(self.records()[0]['state'],'complete')
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(inbox.cursor(db,'123456'),12)
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='telegram_calendar_commands'").fetchone()[0],'1')
            self.assertGreater(db.execute('SELECT count(*) FROM metadata_history').fetchone()[0],0)

    def test_only_exact_original_private_human_command_and_plain_tasks_continue(self):
        foreign = message(11,text='/calendar',chat=99)
        bot = message(12,text='/calendar',**{'from':{'id':42,'is_bot':True}})
        group = message(13,text='/calendar'); group['message']['chat']['type']='group'
        edited = {'update_id':14,'edited_message':message(text='/calendar')['message']}
        inbox.ingest(self.store,'123456','42',[foreign,bot,group,edited,message(15,text='/calendar extra'),message(16,text='/start'),message(17,text='Обычная задача')])
        self.assertEqual(self.records(),[])
        self.assertEqual([item['text'] for item in inbox.items(self.store)],['Обычная задача'])

    def test_lock_busy_waits_pending_and_failed_or_interrupted_send_never_retries(self):
        inbox.ingest(self.store,'123456','42',[message(text='/calendar')])
        sender=unittest.mock.Mock(side_effect=telegram.TelegramError('PNG отправлен. Подтверждено сообщений To-do: 1'))
        with telegram.SEND_LOCK:
            commands.process(self.store,self.base,sender)
        sender.assert_not_called()
        self.assertEqual(self.records()[0]['state'],'pending')
        with patch.object(telegram,'bot_api',return_value={'message_id':2}) as reply:
            commands.process(self.store,self.base,sender)
            commands.process(self.store,self.base,sender)
        sender.assert_called_once()
        reply.assert_called_once()
        self.assertEqual(self.records()[0]['state'],'failed')
        inbox.ingest(self.store,'123456','42',[message(12,text='/calendar',message_id=8)])
        with MetadataStore(self.store).connect() as db:
            db.execute("UPDATE metadata_records SET data=json_set(data,'$.state','sending') WHERE kind=?",(commands.KIND,))
        commands.process(self.store,self.base,sender)
        sender.assert_called_once()

    def test_changed_destination_and_unknown_format_are_not_overwritten(self):
        inbox.ingest(self.store,'123456','42',[message(text='/calendar')])
        sender=unittest.mock.Mock()
        with patch.object(telegram,'settings',return_value=('654321:test','42')):
            commands.process(self.store,self.base,sender)
        sender.assert_not_called()
        self.assertEqual(self.records()[0]['state'],'failed')
        with MetadataStore(self.store).connect() as db:
            db.execute('UPDATE metadata_records SET data=? WHERE kind=?',('{"version":99}',commands.KIND))
        with self.assertRaises(ValueError):
            inbox.ingest(self.store,'123456','42',[message(12,text='/calendar')])
        with MetadataStore(self.store).connect() as db:
            self.assertEqual(inbox.cursor(db,'123456'),11)
            self.assertEqual(db.execute('SELECT data FROM metadata_records WHERE kind=?',(commands.KIND,)).fetchone()[0],'{"version":99}')
