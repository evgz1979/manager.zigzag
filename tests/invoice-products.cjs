/* Regression: ordinary HTTP has getRandomValues, but no crypto.randomUUID. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { randomFillSync } = require('node:crypto');

async function check() {
  const elements = new Map(), writes = [];
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
    fetch: async (url, options = {}) => {
      assert.equal(url, '/api/invoice-products');
      if (options.method === 'POST') {
        const payload = JSON.parse(options.body);
        assert.match(payload.id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
        assert.equal(payload.revision, catalog.revision);
        writes.push(payload);
        const items = payload.kind === 'group' ? catalog.groups : catalog.products;
        const node = { id: payload.id, name: payload.name };
        if (payload.kind === 'product') Object.assign(node, { group_id: payload.group_id, unit: payload.unit, price: payload.price });
        const index = items.findIndex(item => item.id === node.id);
        if (index < 0) items.push(node); else items[index] = node;
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
  console.log('Invoice products: create group/product and edit with randomUUID unavailable passed.');
}
check().catch(error => { console.error(error); process.exitCode = 1; });
