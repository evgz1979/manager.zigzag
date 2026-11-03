# static/reconciliations.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/reconciliations.js:1](../../../static/reconciliations.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## money

[static/reconciliations.js:7](../../../static/reconciliations.js#L7) · `ArrowFunctionExpression`.

```javascript
const money = value =>
```

Форматирует денежное значение для соответствующего компонента.

Использует `Number.isSafeInteger`, `rubles`.

Непосредственные вызовы: `Number.isSafeInteger`, `rubles`.

## date

[static/reconciliations.js:10](../../../static/reconciliations.js#L10) · `ArrowFunctionExpression`.

```javascript
const date = value =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `/^\d{4}-\d{2}-\d{2}$/.test`, `value.split('-').reverse().join`, `value.split('-').reverse`.

Непосредственные вызовы: `/^\d{4}-\d{2}-\d{2}$/.test`, `value.split('-').reverse().join`, `value.split('-').reverse`, `value.split`.

## renderList

[static/reconciliations.js:14](../../../static/reconciliations.js#L14) · `FunctionDeclaration`.

```javascript
function renderList(folder, records)
```

Строит строки текущего списка компонента.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `Map`, `records.map`, `folder.directories.filter`, `rows.map(item => {
      const record = byPath.get(item.path.normalize('NFC'));
      return '<tr><td><a href="?path=' + encodeURIComponent(item.path) + '" data-reconciliation-path="' + escapeHtml(item.path) + '">' +
        escapeHtml(record?.title || item.name) + '</a></td><td>' + escapeHtml(record?.client || '—') +
        '</td><td><span class="reconciliation-list-note">' + escapeHtml(record?.note || '—') + '</span></td></tr>';
    }).join`, `rows.map`, `document.querySelector`, `$`, `[...$('reconciliationListRows').querySelectorAll('[data-reconciliation-path]')].find(el => el.dataset.reconciliationPath === focused)?.focus`, `[...$('reconciliationListRows').querySelectorAll('[data-reconciliation-path]')].find`, `$('reconciliationListRows').querySelectorAll`.

Прямые присваивания полям/свойствам: `$('reconciliationListRows').innerHTML`, `pane.scrollTop`, `$('reconciliationListCount').textContent`, `$('reconciliationListState').textContent`.

## button

[static/reconciliations.js:37](../../../static/reconciliations.js#L37) · `FunctionDeclaration`.

```javascript
function button(invoice)
```

Строит кнопку действия компонента с текущим состоянием записи.

Использует `links.set`, `links.get`, `escapeHtml`.

Непосредственные вызовы: `links.set`, `links.get`, `escapeHtml`.

## renderTable

[static/reconciliations.js:46](../../../static/reconciliations.js#L46) · `FunctionDeclaration`.

```javascript
function renderTable(record)
```

Показывает назначенные сверке счета с их состоянием и источником.

Использует `/api/invoice-pdf`.

Непосредственные вызовы: `$`, `rows.map(item => {
      const pdf = !item.trash && ['issued', 'external'].includes(item.state);
      const label = escapeHtml(item.label);
      const href = pdf ? apiUrl('/api/invoice-pdf', item.path, { id: item.id }) : '?path=' + encodeURIComponent(item.path);
      const stateLabel = item.trash ? 'В корзине' : { draft: 'Черновик', issued: 'Выпущен', external: 'Внешний' }[item.state] || item.state;
      return '<tr data-reconciliation-invoice="' + escapeHtml(item.id) + '"><td><a href="' + escapeHtml(href) + '"' + (pdf ? ' target="_blank" rel="noopener"' : ' data-reconciliation-order="' + escapeHtml(item.path) + '"') + '>' + label + '</a>' + (item.comment ? '<small title="' + escapeHtml(item.comment) + '">' + escapeHtml(item.comment) + '</small>' : '') + '</td><td>' + date(item.date) + '</td><td><a href="?path=' + encodeURIComponent(item.path) + '" data-reconciliation-order="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.path) + '">' + escapeHtml(item.order_title) + '</a></td><td class="reconciliation-amount">' + money(item.total) + '</td><td>' + escapeHtml(stateLabel) + '</td><td><button type="button" class="secondary-button" data-reconciliation-unlink="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml('Убрать из сверки · ' + item.label) + '">×</button></td></tr>';
    }).join`, `rows.map`, `document.querySelector`, `[...$('reconciliationInvoiceRows').querySelectorAll('[data-reconciliation-unlink]')].find(el => el.dataset.reconciliationUnlink === focused)?.focus`, `[...$('reconciliationInvoiceRows').querySelectorAll('[data-reconciliation-unlink]')].find`, `$('reconciliationInvoiceRows').querySelectorAll`.

Прямые присваивания полям/свойствам: `$('reconciliationInvoiceCount').textContent`, `$('reconciliationInvoiceRows').innerHTML`, `pane.scrollTop`, `$('reconciliationInvoiceState').textContent`, `$('reconciliationInvoiceRows').invoiceRecords`.

## refresh

[static/reconciliations.js:70](../../../static/reconciliations.js#L70) · `FunctionDeclaration`.

```javascript
async function refresh()
```

Перечитывает данные открытого компонента по установленным правилам в модуле самостоятельных сверок.

Использует `/api/reconciliations`, `/api/reconciliation`.

Непосредственные вызовы: `$`, `renderList`, `request`, `renderTable`, `apiUrl`, `document.activeElement?.closest`, `JSON.stringify`, `renderTodos`, `resizeOrderNote`, `renderOrderHeading`, `renderStatus`.

Прямые присваивания полям/свойствам: `$('reconciliationList').hidden`, `$('reconciliationInvoices').hidden`, `$('reconciliationListState').textContent`, `folder.reconciliation`, `folder.note`, `folder.todo_items`, `$('orderTitleInput').value`, `$('reconciliationClient').value`, `$('orderNote').value`, `$('reconciliationInvoiceState').textContent`.

## controls

[static/reconciliations.js:112](../../../static/reconciliations.js#L112) · `FunctionDeclaration`.

```javascript
function controls(busy)
```

Обновляет доступность действий открытого редактора в модуле самостоятельных сверок.

Использует `$`.

Непосредственные вызовы: `$`.

Прямые присваивания полям/свойствам: `$(id).disabled`.

## loadAssignment

[static/reconciliations.js:118](../../../static/reconciliations.js#L118) · `FunctionDeclaration`.

```javascript
async function loadAssignment(current, preserve = false)
```

Загружает допустимые сверки и текущее назначение счёта.

Использует `/api/reconciliations`, `/api/invoice`.

Непосредственные вызовы: `$`, `controls`, `Promise.all`, `request`, `apiUrl`, `links.get`, `catalog.items.map(item => '<option value="' + escapeHtml(item.id) + '">' + escapeHtml(item.title + (item.client ? ' · ' + item.client : '')) + '</option>').join`, `catalog.items.map`, `catalog.items.some`, `$('invoiceReconciliationSelect').insertAdjacentHTML`, `escapeHtml`.

Прямые присваивания полям/свойствам: `current.loading`, `current.invoice`, `current.items`, `current.link`, `$('invoiceReconciliationSelect').innerHTML`, `$('invoiceReconciliationSelect').value`, `current.ready`, `$('invoiceReconciliationState').textContent`, `$('saveInvoiceReconciliation').disabled`.

## open

[static/reconciliations.js:140](../../../static/reconciliations.js#L140) · `FunctionDeclaration`.

```javascript
async function open(invoice)
```

Открывает компонент и загружает его исходные данные в модуле самостоятельных сверок.

Использует `$`, `$('invoiceReconciliationDialog').showModal`, `loadAssignment`.

Непосредственные вызовы: `$`, `$('invoiceReconciliationDialog').showModal`, `loadAssignment`, `$('invoiceReconciliationSelect').focus`.

Прямые присваивания полям/свойствам: `$('invoiceReconciliationName').textContent`, `$('invoiceReconciliationState').textContent`.

## close

[static/reconciliations.js:151](../../../static/reconciliations.js#L151) · `FunctionDeclaration`.

```javascript
function close()
```

Закрывает компонент и освобождает его временное состояние в модуле самостоятельных сверок.

Использует `$('invoiceReconciliationDialog').close`, `$`.

Непосредственные вызовы: `$('invoiceReconciliationDialog').close`, `$`.
