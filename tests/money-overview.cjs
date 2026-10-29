const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const months = vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../static/money-overview.js'), 'utf8') + '\nMoneyOverview.months');
const plain = (value) => JSON.parse(JSON.stringify(value));
const plan = (id, changes = {}) => ({ id, date: '2026-10-28', operation: 'incoming', amount: 10001, ...changes });

// Empty months are present across the year boundary; nothing is fabricated.
assert.deepEqual(plain(months([], '2026-11')).map((month) => [month.key, month.income, month.expense]), [
  ['2026-11', 0, 0], ['2026-12', 0, 0], ['2027-01', 0, 0], ['2027-02', 0, 0],
]);

// Separate equal-valued plans remain distinct, with exact kopecks and date order.
const records = Object.freeze([
  Object.freeze(plan('later', { date: '2026-10-30' })),
  Object.freeze(plan('earlier')),
  Object.freeze(plan('expense', { operation: 'outgoing', amount: 20002 })),
  Object.freeze(plan('free', { path: '', amount: 99 })),
]);
let result = plain(months(records, '2026-10'));
assert.equal(result[0].income, 20101);
assert.equal(result[0].expense, 20002);
assert.equal(result[0].income - result[0].expense, 99);
assert.deepEqual(result[0].incoming.map((item) => item.id), ['earlier', 'free', 'later']);
assert.equal(records[0].id, 'later');

// Only future cash flow is counted, never invoice issuance or unknown flags.
result = plain(months([
  plan('valid'), plan('inactive', { is_inactive: true }), plan('done', { is_completed: true }),
  plan('unknown-inactive', { is_inactive: null }), plan('unknown-completion', { is_completed: 1 }),
  plan('invoice', { operation: 'invoice' }), plan('zero', { amount: 0 }), plan('negative', { amount: -1 }),
  plan('string', { amount: '100' }), plan('fraction', { amount: 12.34 }), plan('other-month', { date: '2026-09-30' }),
  plan('beyond-range', { date: '2027-02-01' }),
], '2026-10'));
assert.deepEqual(result[0].incoming.map((item) => item.id), ['valid']);
assert.equal(result[0].income, 10001);

// A weekly payment crossing a month is counted once in its Monday's month.
result = plain(months([
  plan('weekly', { date: '2026-08-31', period: 'week', amount: 70000 }),
  plan('daily', { date: '2026-09-01', amount: 12345 }),
], '2026-08'));
assert.equal(result[0].income, 70000);
assert.equal(result[1].income, 12345);
assert.equal(result.reduce((sum, month) => sum + month.income, 0), 82345);
console.log('Money overview: month boundaries, exact sums, filters, weekly plans and unchanged source verified.');
