/* Regression: ordinary HTTP has getRandomValues, but no crypto.randomUUID. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { randomFillSync } = require('node:crypto');

async function check() {
  const elements = new Map(), writes = [], confirmations = [];
  let confirmDelete = false;
  const document = { activeElement: null, getElementById: id => element(id) };
  function element(id) {
    if (!elements.has(id)) {
      const node = { id, value: '', options: [], handlers: {}, open: false, isConnected: true,
        addEventListener(name, callback) { this.handlers[name] = callback; },
        querySelectorAll() { return []; }, querySelector() { return null; },
        focus() { document.activeElement = this; },
        showModal() { this.open = true; },
        close() { this.open = false; this.handlers.close?.(); },
        set innerHTML(value) {
          this.markup = value;
          if (['invoiceProductGroup', 'invoiceProductParent'].includes(id)) {
            this.options = [...value.matchAll(/<option value="([^"]*)"/g)].map(match => ({ value: match[1] }));
            this.value = this.options[0]?.value || '';
          }
        },
      };
      elements.set(id, node);
    }
    return elements.get(id);
  }
  let catalog = { version: 1, revision: 0, groups: [], products: [] };
  const context = vm.createContext({ document, isSecureContext: false,
    crypto: { getRandomValues: array => randomFillSync(array) },
    window: { confirm: message => { confirmations.push(message); return confirmDelete; } },
    fetch: async (url, options = {}) => {
      assert.equal(url, '/api/invoice-products');
      if (options.method === 'POST') {
        const payload = JSON.parse(options.body);
        assert.match(payload.id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
        assert.equal(payload.revision, catalog.revision);
        writes.push(payload);
        const items = payload.kind === 'group' ? catalog.groups : catalog.products;
        const index = items.findIndex(item => item.id === payload.id);
        if (payload.action === 'delete') {
          assert.equal(payload.confirmed, true); assert(index >= 0); items.splice(index, 1);
        } else {
          const node = { id: payload.id, name: payload.name };
          if (payload.kind === 'product') Object.assign(node, { group_id: payload.group_id, unit: payload.unit, price: payload.price });
          if (index < 0) items.push(node); else items[index] = node;
        }
        catalog.revision++;
      }
      return { ok: true, json: async () => JSON.parse(JSON.stringify(catalog)) };
    },
  });
  const invoices = fs.readFileSync(path.join(__dirname, '../static/invoices.js'), 'utf8');
  const identity = invoices.match(/function newIdentity\(\) \{[\s\S]*?\n  \}/);
  assert(identity, 'Use the actual invoice UUID generator');
  const generator = vm.runInContext('(' + identity[0] + ')', context);
  const products = vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/invoice-products.js'), 'utf8') + '\nInvoiceProducts', context);
  assert.equal(vm.runInContext('typeof crypto.randomUUID', context), 'undefined');
  products.init(() => {}, generator);
  await products.load();

  element('newInvoiceProductGroup').handlers.click();
  assert.equal(element('invoiceProductDialog').open, true, '+ Group opens on HTTP');
  assert.equal(writes.length, 0, 'Opening a form must not save');
  element('invoiceProductName').value = 'Вывески';
  await element('invoiceProductForm').handlers.submit({ preventDefault() {} });
  assert.equal(writes[0].kind, 'group');
  assert.equal(catalog.groups[0].name, 'Вывески');

  element('newInvoiceProduct').handlers.click();
  assert.equal(element('invoiceProductDialog').open, true, '+ Product opens on HTTP');
  assert.equal(element('deleteInvoiceProduct').hidden, true);
  element('invoiceProductName').value = 'Буквы';
  element('invoiceProductUnit').value = 'шт';
  element('invoiceProductPrice').value = '4200';
  await element('invoiceProductForm').handlers.submit({ preventDefault() {} });
  assert.equal(writes[1].kind, 'product');
  assert.notEqual(writes[0].id, writes[1].id);
  assert.equal(catalog.products[0].price, '4200');

  const id = catalog.products[0].id;
  products.open('product', catalog.products[0]);
  element('invoiceProductPrice').value = '4300';
  await element('invoiceProductForm').handlers.submit({ preventDefault() {} });
  assert.equal(writes[2].id, id, 'Editing preserves the UUID');
  assert.equal(catalog.products[0].price, '4300');
  assert.equal(element('invoiceProductDialog').open, false);

  const source = JSON.parse(JSON.stringify(catalog.products[0]));
  products.open('product', catalog.products[0], true);
  assert.equal(element('deleteInvoiceProduct').hidden, true, 'New copy cannot be deleted before saving');
  assert.equal(element('invoiceProductTitle').textContent, 'Новый товар на основе');
  assert.equal(element('invoiceProductName').value, source.name);
  assert.equal(element('invoiceProductParent').value, source.group_id);
  assert.equal(element('invoiceProductUnit').value, source.unit);
  assert.equal(element('invoiceProductPrice').value, source.price);
  assert.equal(writes.length, 3, 'Opening a copy does not create it');
  element('invoiceProductName').value = 'Буквы, 100 см';
  element('invoiceProductPrice').value = '5900';
  await element('invoiceProductForm').handlers.submit({ preventDefault() {} });
  assert.equal(catalog.products.length, 2);
  assert.notEqual(writes[3].id, source.id, 'Copy receives a new UUID');
  assert.equal(writes[3].group_id, source.group_id);
  assert.deepEqual(catalog.products[0], source, 'Copying leaves the source unchanged');
  assert.equal(catalog.products[1].name, 'Буквы, 100 см');
  assert.equal(catalog.products[1].price, '5900');
  products.open('product', source, true);
  element('cancelInvoiceProduct').handlers.click();
  assert.equal(writes.length, 4, 'Cancelling a copy does not write');
  products.open('product', catalog.products[0]);
  assert.equal(element('deleteInvoiceProduct').hidden, false);
  await element('deleteInvoiceProduct').handlers.click();
  assert.equal(writes.length, 4, 'Cancelling the deletion confirmation does not write');
  confirmDelete = true;
  await element('deleteInvoiceProduct').handlers.click();
  assert.equal(writes[4].action, 'delete');
  assert.equal(writes[4].id, source.id);
  assert.equal(catalog.products.length, 1);
  assert.equal(catalog.products[0].id, writes[3].id, 'Deleting the source preserves its independent copy');
  assert.equal(element('invoiceProductDialog').open, false);
  assert(confirmations[0].includes(source.name));

  const names = ['Я 2', 'А 10', 'а 2', 'А 2'];
  catalog.products = names.map((name, index) => ({ id: generator(), group_id: source.group_id, name, unit: 'шт', price: String(100 - index) }));
  const originalOrder = catalog.products.map(item => item.id);
  await products.load();
  const displayed = [...element('invoiceProductsList').markup.matchAll(/data-product-add="([^"]*)"/g)].map(match => match[1]);
  assert.deepEqual(displayed, [originalOrder[2], originalOrder[3], originalOrder[1], originalOrder[0]], 'Russian natural name order with stable equal names');
  assert.deepEqual(catalog.products.map(item => item.id), originalOrder, 'Sorting never rewrites storage order');
  assert.equal(writes.length, 5, 'Sorting is read-only');
  console.log('Invoice products: HTTP create/edit/copy, confirmed deletion and stable Russian name sorting passed.');
}
check().catch(error => { console.error(error); process.exitCode = 1; });
