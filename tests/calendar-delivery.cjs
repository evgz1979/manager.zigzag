const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = vm.createContext({ Intl, Date });
vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/home-calendar.js'), 'utf8') + '\nthis.calendar = HomeCalendar;', context);
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(cases.map(({snapshot, now}) => {
  const result = context.calendar.snapshotRange(new Date(now), [...snapshot.orders, ...snapshot.calendar_supplier_orders], snapshot.calendar_events, snapshot.calendar_invoice_plans);
  return [result.start.toISOString().slice(0,10), result.end.toISOString().slice(0,10)];
})));
