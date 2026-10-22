/* Run with Node: node tests/spreadsheet-preview.cjs. No npm installation needed. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const XLSX = require('../static/vendor/sheetjs/xlsx.full.min.js');

async function run() {
  let response;
  const self = { postMessage(data) { response = data; } };
  const book = XLSX.utils.book_new();
  const first = XLSX.utils.aoa_to_sheet([
    ['Кириллица', '<img src=x onerror=alert(1)>', 1234.5],
    ['Дата', 45000], ['Формула', { t: 'n', v: 3, f: '1+2' }]
  ]);
  first.C1.z = '#,##0.00';
  first.B2.z = 'dd.mm.yyyy';
  const second = XLSX.utils.aoa_to_sheet(Array.from({ length: 450 }, (_, i) => ['Строка ' + (i + 1), i]));
  second['!merges'] = [{ s: { r: 198, c: 0 }, e: { r: 202, c: 0 } }];
  XLSX.utils.book_append_sheet(book, first, 'Данные');
  XLSX.utils.book_append_sheet(book, second, 'Длинный лист');
  const raw = XLSX.write(book, { type: 'buffer', bookType: 'xlsx' });
  const context = vm.createContext({ self, XLSX, importScripts() {}, AbortSignal,
    fetch: async () => ({ ok: true, arrayBuffer: async () => raw }) });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/spreadsheet-worker.js'), 'utf8'), context);
  await self.onmessage({ data: { type: 'load', url: '/api/spreadsheet', id: 1 } });
  assert.equal(response.error, undefined);
  assert.equal(response.cells[0][0].text, 'Кириллица');
  assert.equal(response.cells[0][1].text, '<img src=x onerror=alert(1)>');
  assert.equal(response.cells[0][2].text, '1,234.50');
  assert.equal(response.cells[1][1].text, '15.03.2023');
  assert.equal(response.cells[2][1].text, '3');
  assert.equal(response.sheets.length, 2);
  await self.onmessage({ data: { type: 'page', sheetIndex: 1, offset: 0, id: 2 } });
  assert.equal(response.cells.length, 200);
  assert.equal(response.merges[0].rows, 2);
  await self.onmessage({ data: { type: 'page', sheetIndex: 1, offset: 200, id: 3 } });
  assert.equal(response.start, 200);
  assert.equal(response.end, 399);
  assert.equal(response.merges[0].text, 'Строка 199');
  assert.equal(response.merges[0].rows, 3);
  await self.onmessage({ data: { type: 'page', sheetIndex: 1, offset: 400, id: 4 } });
  assert.equal(response.cells.length, 50);
  await self.onmessage({ data: { type: 'page', sheetIndex: 99, offset: 0, id: 5 } });
  assert.equal(response.error, 'Лист не найден');
  console.log('Spreadsheet worker: Cyrillic, escaping, numbers, dates, cached formulas, sheets and merged pagination OK');
}
run().catch((error) => { console.error(error); process.exitCode = 1; });
