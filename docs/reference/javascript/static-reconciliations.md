# static/reconciliations.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/reconciliations.js](../../../static/reconciliations.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-button"></a>

## button

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
function button(invoice)
```

Строит кнопку действия компонента с текущим состоянием записи.

Использует `links.set`, `links.get`, `escapeHtml`.

Непосредственные вызовы: `links.set`, `links.get`, `escapeHtml`.

<a id="symbol-close"></a>

## close

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
function close()
```

Закрывает компонент и освобождает его временное состояние в модуле самостоятельных сверок.

Использует `$('invoiceReconciliationDialog').close`, `$`.

Непосредственные вызовы: `$('invoiceReconciliationDialog').close`, `$`.

<a id="symbol-controls"></a>

## controls

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
function controls(busy)
```

Обновляет доступность действий открытого редактора в модуле самостоятельных сверок.

Использует `$`.

Непосредственные вызовы: `$`.

Прямые присваивания полям/свойствам: `$(id).disabled`.

<a id="symbol-date"></a>

## date

[static/reconciliations.js](../../../static/reconciliations.js) · `ArrowFunctionExpression`.

```javascript
const date = value =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `/^\d{4}-\d{2}-\d{2}$/.test`, `value.split('-').reverse().join`, `value.split('-').reverse`.

Непосредственные вызовы: `/^\d{4}-\d{2}-\d{2}$/.test`, `value.split('-').reverse().join`, `value.split('-').reverse`, `value.split`.

<a id="symbol-loadAssignment"></a>

## loadAssignment

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
async function loadAssignment(current, preserve = false)
```

Загружает допустимые сверки и текущее назначение счёта.

Использует `/api/reconciliations`, `/api/invoice`.

Непосредственные вызовы: `$`, `controls`, `Promise.all`, `request`, `apiUrl`, `links.get`, `catalog.items.map(item => '<option value="' + escapeHtml(item.id) + '">' + escapeHtml(item.title + (item.client ? ' · ' + item.client : '')) + '</option>').join`, `catalog.items.map`, `catalog.items.some`, `$('invoiceReconciliationSelect').insertAdjacentHTML`, `escapeHtml`.

Прямые присваивания полям/свойствам: `current.loading`, `current.invoice`, `current.items`, `current.link`, `$('invoiceReconciliationSelect').innerHTML`, `$('invoiceReconciliationSelect').value`, `current.ready`, `$('invoiceReconciliationState').textContent`, `$('saveInvoiceReconciliation').disabled`.

<a id="symbol-money"></a>

## money

[static/reconciliations.js](../../../static/reconciliations.js) · `ArrowFunctionExpression`.

```javascript
const money = value =>
```

Форматирует денежное значение для соответствующего компонента.

Использует `Number.isSafeInteger`, `rubles`.

Непосредственные вызовы: `Number.isSafeInteger`, `rubles`.

<a id="symbol-open"></a>

## open

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
async function open(invoice)
```

Открывает компонент и загружает его исходные данные в модуле самостоятельных сверок.

Использует `$`, `$('invoiceReconciliationDialog').showModal`, `loadAssignment`.

Непосредственные вызовы: `$`, `$('invoiceReconciliationDialog').showModal`, `loadAssignment`, `$('invoiceReconciliationSelect').focus`.

Прямые присваивания полям/свойствам: `$('invoiceReconciliationName').textContent`, `$('invoiceReconciliationState').textContent`.

<a id="symbol-refresh"></a>

## refresh

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
async function refresh()
```

Перечитывает данные открытого компонента по установленным правилам в модуле самостоятельных сверок.

Использует `/api/reconciliations`, `/api/reconciliation`.

Непосредственные вызовы: `$`, `renderList`, `request`, `renderTable`, `apiUrl`, `document.activeElement?.closest`, `JSON.stringify`, `renderTodos`, `resizeOrderNote`, `renderOrderHeading`, `renderStatus`.

Прямые присваивания полям/свойствам: `$('reconciliationList').hidden`, `$('reconciliationInvoices').hidden`, `$('reconciliationListState').textContent`, `folder.reconciliation`, `folder.note`, `folder.todo_items`, `$('orderTitleInput').value`, `$('reconciliationClient').value`, `$('orderNote').value`, `$('reconciliationInvoiceState').textContent`.

<a id="symbol-renderList"></a>

## renderList

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

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

<a id="symbol-renderTable"></a>

## renderTable

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

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
