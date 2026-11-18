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

Строит кнопку сверки в строке счёта.

Подсвечивает привязанный счёт и передаёт название сверки в подсказку и доступное имя.

Непосредственные вызовы: `links.set`, `links.get`, `escapeHtml`, `Boolean`, `icon`.

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

<a id="symbol-listStatusEditing"></a>

## listStatusEditing

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
function listStatusEditing()
```

Проверяет, можно ли заменить DOM списка при фоновом обновлении.

Сохраняет открытый выбор статуса и ожидает завершения записи.

Непосредственные вызовы: `Boolean`, `document.activeElement?.matches`.

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
async function refresh(forceList = false)
```

Перечитывает данные открытого компонента по установленным правилам в модуле самостоятельных сверок.

Принудительно перечитывает список после ошибки записи статуса через `/api/reconciliations`.

Непосредственные вызовы: `$`, `renderList`, `listStatusEditing`, `request`, `renderTable`, `apiUrl`, `document.activeElement?.closest`, `JSON.stringify`, `renderTodos`, `resizeOrderNote`, `renderOrderHeading`, `renderStatus`.

Прямые присваивания полям/свойствам: `$('reconciliationList').hidden`, `$('reconciliationInvoices').hidden`, `$('reconciliationListState').textContent`, `folder.reconciliation`, `folder.note`, `folder.todo_items`, `$('orderTitleInput').value`, `$('reconciliationClient').value`, `$('orderNote').value`, `$('reconciliationInvoiceState').textContent`.

<a id="symbol-renderList"></a>

## renderList

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
function renderList(folder, records)
```

Строит список сверок с активными строками перед оплаченными.

Сохраняет фокус и прокрутку; связывает цвет клиента только при однозначном совпадении.

Непосредственные вызовы: `Map`, `records.map`, `[...state.tree, ...state.groups.flatMap(group => group.children)].filter`, `state.groups.flatMap`, `folder.directories.filter(item => !item.name.startsWith('#'))
      .map(item => ({ item, record: byPath.get(item.path.normalize('NFC')) }))
      .sort`, `folder.directories.filter(item => !item.name.startsWith('#'))
      .map`, `folder.directories.filter`, `rows.map(({ item, record }) => {
      const title = record?.title || item.name;
      const client = (record?.client || '').normalize('NFC');
      const matches = clients.filter(node => node.name.normalize('NFC') === client || node.path.normalize('NFC') === client);
      const options = Object.entries(listStatuses).map(([value, label]) => '<option value="' + value + '"' +
        (value === record?.status ? ' selected' : '') + '>' + label + '</option>').join('');
      const status = record ? '<select class="status-badge order-status-select reconciliation-status-select" data-status="' + escapeHtml(record.status) +
        '" data-reconciliation-status="' + escapeHtml(record.id) + '" aria-label="' + escapeHtml('Статус сверки «' + title + '»') +
        '"' + (statusSaves.has(record.id) ? ' disabled' : '') + '>' + options + '</select>' : '—';
      return '<tr role="row"><td role="cell" class="reconciliation-list-title"><a href="?path=' + encodeURIComponent(item.path) +
        '" data-reconciliation-path="' + escapeHtml(item.path) + '">' + escapeHtml(title) + '</a></td>' +
        '<td role="cell" class="reconciliation-list-client" data-empty="' + !client + '">' + ClientBadge.markup(record?.client || '—', matches.length === 1 ? matches[0].path : '') + '</td>' +
        '<td role="cell" class="reconciliation-list-note-cell" data-empty="' + !record?.note + '"><span class="reconciliation-list-note">' + escapeHtml(record?.note || '—') + '</span></td>' +
        '<td role="cell" class="reconciliation-list-status">' + status + '</td></tr>';
    }).join`, `rows.map`, `document.querySelector`, `$`, `[...body.querySelectorAll('[data-reconciliation-path], [data-reconciliation-status]')]
          .find(el => el.dataset[focusKey] === focused[focusKey])?.focus`, `[...body.querySelectorAll('[data-reconciliation-path], [data-reconciliation-status]')]
          .find`, `body.querySelectorAll`.

Прямые присваивания полям/свойствам: `body.innerHTML`, `pane.scrollTop`, `$('reconciliationListTable').hidden`, `$('reconciliationListCount').textContent`, `$('reconciliationListState').textContent`.

<a id="symbol-renderTable"></a>

## renderTable

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
function renderTable(record)
```

Показывает назначенные счета, комментарии, состояние и исходные заказы.

Сохраняет переносы строк в комментариях; готовые счета открывает через `/api/invoice-pdf`.

Непосредственные вызовы: `$`, `rows.map(item => {
      const pdf = !item.trash && ['issued', 'external'].includes(item.state);
      const label = escapeHtml(item.label);
      const href = pdf ? apiUrl('/api/invoice-pdf', item.path, { id: item.id }) : '?path=' + encodeURIComponent(item.path);
      const stateLabel = item.trash ? 'В корзине' : { draft: 'Черновик', issued: 'Выпущен', external: 'Внешний' }[item.state] || item.state;
      return '<tr data-reconciliation-invoice="' + escapeHtml(item.id) + '">' +
        '<td><a href="' + escapeHtml(href) + '"' + (pdf ? ' target="_blank" rel="noopener"' : ' data-reconciliation-order="' + escapeHtml(item.path) + '"') + '>' + label + '</a></td>' +
        '<td class="reconciliation-invoice-comment">' + escapeHtml(item.comment || '—') + '</td>' +
        '<td>' + date(item.date) + '</td>' +
        '<td><a href="?path=' + encodeURIComponent(item.path) + '" data-reconciliation-order="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.path) + '">' + escapeHtml(item.order_title) + '</a></td>' +
        '<td class="reconciliation-amount">' + money(item.total) + '</td><td>' + escapeHtml(stateLabel) + '</td>' +
        '<td><button type="button" class="secondary-button" data-reconciliation-unlink="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml('Убрать из сверки · ' + item.label) + '">×</button></td></tr>';
    }).join`, `rows.map`, `document.querySelector`, `[...$('reconciliationInvoiceRows').querySelectorAll('[data-reconciliation-unlink]')].find(el => el.dataset.reconciliationUnlink === focused)?.focus`, `[...$('reconciliationInvoiceRows').querySelectorAll('[data-reconciliation-unlink]')].find`, `$('reconciliationInvoiceRows').querySelectorAll`.

Прямые присваивания полям/свойствам: `$('reconciliationInvoiceCount').textContent`, `$('reconciliationInvoiceRows').innerHTML`, `pane.scrollTop`, `$('reconciliationInvoiceState').textContent`, `$('reconciliationInvoiceRows').invoiceRecords`.

<a id="symbol-saveListStatus"></a>

## saveListStatus

[static/reconciliations.js](../../../static/reconciliations.js) · `FunctionDeclaration`.

```javascript
async function saveListStatus(control)
```

Сохраняет выбранный статус по версии строки и переставляет её после ответа.

При ошибке возвращает сохранённое значение и перечитывает список без повтора записи.

Непосредственные вызовы: `listRecords.find`, `statusSaves.has`, `Object.hasOwn`, `statusSaves.add`, `request`, `notify`, `statusSaves.delete`, `renderList`, `listRecords.map`, `refresh`, `[...$('reconciliationListRows').querySelectorAll('[data-reconciliation-status]')]
        .find(el => el.dataset.reconciliationStatus === current.id)?.focus`, `[...$('reconciliationListRows').querySelectorAll('[data-reconciliation-status]')]
        .find`, `$('reconciliationListRows').querySelectorAll`, `$`.

Прямые присваивания полям/свойствам: `control.value`, `control.disabled`.
