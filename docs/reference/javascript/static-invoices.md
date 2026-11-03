# static/invoices.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/invoices.js:1](../../../static/invoices.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## invoiceLabel

[static/invoices.js:11](../../../static/invoices.js#L11) · `ArrowFunctionExpression`.

```javascript
const invoiceLabel = (record) =>
```

Формирует отображаемое название счёта или плана.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## displayDate

[static/invoices.js:14](../../../static/invoices.js#L14) · `ArrowFunctionExpression`.

```javascript
const displayDate = (value) =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `value.split('-').reverse().join`, `value.split('-').reverse`, `value.split`.

Непосредственные вызовы: `value.split('-').reverse().join`, `value.split('-').reverse`, `value.split`.

## displayPlanDate

[static/invoices.js:17](../../../static/invoices.js#L17) · `ArrowFunctionExpression`.

```javascript
const displayPlanDate = (record) =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `Date`, `Number.isNaN`, `end.getTime`.

Непосредственные вызовы: `Date`, `Number.isNaN`, `end.getTime`, `displayDate`, `end.setUTCDate`, `end.getUTCDate`, `end.toISOString().slice`, `end.toISOString`.

## planAmount

[static/invoices.js:25](../../../static/invoices.js#L25) · `ArrowFunctionExpression`.

```javascript
const planAmount = (record) =>
```

Выбирает сохранённую сумму плана для формы и списка.

Использует `['incoming', 'outgoing'].includes`, `Number.isSafeInteger`, `cash`.

Непосредственные вызовы: `['incoming', 'outgoing'].includes`, `Number.isSafeInteger`, `cash`.

## cash

[static/invoices.js:33](../../../static/invoices.js#L33) · `ArrowFunctionExpression`.

```javascript
const cash = (cents) =>
```

Форматирует денежное значение для соответствующего компонента.

Использует `Intl.NumberFormat`.

Непосредственные вызовы: `new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB" }).format`, `Intl.NumberFormat`.

## pdfUrl

[static/invoices.js:36](../../../static/invoices.js#L36) · `ArrowFunctionExpression`.

```javascript
const pdfUrl = (record, preview = false) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `/api/invoice-preview`, `/api/invoice-pdf`.

Непосредственные вызовы: `apiUrl`.

## message

[static/invoices.js:39](../../../static/invoices.js#L39) · `ArrowFunctionExpression`.

```javascript
const message = (text, error = false) =>
```

Показывает сообщение пользователю и предусмотренное действие отмены.

Использует `$`, `$("invoiceEditorState").classList.toggle`.

Непосредственные вызовы: `$`, `$("invoiceEditorState").classList.toggle`.

Прямые присваивания полям/свойствам: `$("invoiceEditorState").textContent`.

## renderInvoiceList

[static/invoices.js:46](../../../static/invoices.js#L46) · `FunctionDeclaration`.

```javascript
function renderInvoiceList(records)
```

Показывает счета, планы и состояние документов текущего заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `picker?.matches`, `InvoiceDocuments.focusKey`, `document.activeElement?.closest`, `Map`, `records.filter((record) => ['issued', 'external'].includes(record.state)).map`, `records.filter`, `$`, `rows.map((record) => {
      const external = record.state === "external";
      const label = invoiceLabel(record);
      const date = record.state === 'planned' ? displayPlanDate(record) : displayDate(record.data.date);
      if (record.state === 'planned') {
        const completed = record.data._calendar_completed === true;
        const details = [date, planAmount(record), record.data.invoice_label, record.data.text].filter(Boolean).join(' · ');
        const planLabelClass = completed ? ' invoice-completed-plan-label' : (record.data.operation || 'invoice') === 'invoice' ? ' invoice-issuance-plan-label' : '';
        const planLabel = (completed ? '✓ Выполнено · ' : '') + label;
        return '<div class="invoice-row"><button type="button" class="invoice-row-name' + (completed ? ' invoice-plan-completed' : '') + '" data-invoice-plan="' + record.id + '" title="' + escapeHtml(planLabel + ' · ' + details) + '"' + (record.plan_editable ? '' : ' disabled') + '><span class="invoice-row-label' + planLabelClass + '">' + escapeHtml(planLabel) + '</span><small class="invoice-row-meta" title="' + escapeHtml(details) + '">' + escapeHtml(details) + (record.plan_editable ? '' : ' · Неизвестный формат плана') + '</small></button><div class="invoice-row-actions"><button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + record.id + '" aria-label="В корзину · ' + escapeHtml(planLabel + ' · ' + date) + '">×</button></div></div>';
      }
      const details = (external ? 'Внешний · ' : '') + date;
      const comment = external ? record.data.comment?.trim() : '';
      const heading = comment || label;
      const secondary = (comment ? label + ' · ' : '') + details;
      const sync = record.state === "draft" ? "Черновик" : record.sync_error ? "PDF в базе · " + record.sync_error + " · автоповтор" : record.sync_pending ? "PDF в базе · копия в # bills ожидает выгрузки" : "PDF в # bills";
      const busy = statusSaving.has(record.id) || InvoiceDocuments.isBusy(record.id);
      const status = record.list_status === undefined ? 'none' : record.list_status;
      const buttons = '<div class="invoice-list-status" role="group" aria-label="Отметка счёта · ' + escapeHtml(label) + '" aria-busy="' + busy + '">' +
        Object.entries(listStatusLabels).map(([value, name]) => '<button type="button" class="secondary-button" data-invoice-status="' + record.id + '" data-value="' + value + '" aria-pressed="' + (status === value) + '" title="' + (status === null ? 'Неизвестная отметка сохранена без замены' : status === value ? 'Снять отметку «' + name + '»' : name) + '"' + (busy || status === null ? ' disabled' : '') + '>' + name + '</button>').join('') + '</div>';
      const schedule = record.state === 'draft' ? '' : '<button class="secondary-button" type="button" data-invoice-schedule="' + record.id + '" aria-label="Запланировать оплату · ' + escapeHtml(label) + '">Запланировать</button>';
      const plans = (linkedPlans.get(record.id) || []).map((plan) => {
        const inactive = record.list_status === 'inactive' || plan.data._calendar_inactive === true;
        const completed = plan.data._calendar_completed === true;
        const status = [completed ? '✓ Выполнено' : '', inactive ? 'Неактуально' : ''].filter(Boolean).join(' · ') || 'Запланировано';
        const summary = [status + ': ' + planAmount(plan), displayPlanDate(plan), plan.data.text].filter(Boolean).join(' · ');
        const description = [completed ? 'Выполнено' : '', inactive ? 'Неактуально' : '', invoiceLabel(plan), label, displayPlanDate(plan), planAmount(plan), plan.data.text].filter(Boolean).join(' · ');
        return '<div class="invoice-linked-entry"><button type="button" class="invoice-linked-plan' + (inactive ? ' invoice-linked-inactive' : '') + (completed ? ' invoice-plan-completed' : '') + '" data-invoice-plan="' + plan.id + '" data-operation="' + escapeHtml(plan.data.operation || 'invoice') + '" aria-label="' + escapeHtml(description) + '" title="' + escapeHtml(description) + '"' + (plan.plan_editable ? '' : ' disabled') + '>' + escapeHtml(summary) + (plan.plan_editable ? '' : ' · Неизвестный формат плана') + '</button><button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + plan.id + '" aria-label="' + escapeHtml('В корзину · ' + description) + '">×</button></div>';
      }).join('');
      return '<div class="invoice-row" data-invoice-row="' + record.id + '"><div class="invoice-row-content"><button type="button" class="invoice-row-name" data-invoice-' + (external ? 'view' : 'edit') + '="' + record.id + '"><span class="invoice-row-label' + (comment ? ' invoice-row-comment' : '') + '" title="' + escapeHtml(heading) + '">' + escapeHtml(heading) + '</span><small class="invoice-row-meta" title="' + escapeHtml(secondary + ' · ' + sync) + '">' + escapeHtml(secondary) + '<span class="invoice-row-state' + (record.sync_error ? ' error' : '') + '"> · ' + escapeHtml(sync) + '</span></small></button>' + (plans ? '<div class="invoice-linked-plans">' + plans + '</div>' : '') + InvoiceDocuments.markup(record) + '</div><div class="invoice-row-actions">' + (external ? '' : '<strong>' + cash(record.data.total) + '</strong>') + buttons + schedule + InvoiceDocuments.button(record) +
        (typeof ReconciliationUI === 'undefined' ? '' : ReconciliationUI.button(record)) + (external ? '<button class="secondary-button" type="button" data-invoice-view="' + record.id + '">PDF</button>' : record.state !== "draft" ? '<a class="secondary-button" href="' + escapeHtml(pdfUrl(record)) + '" target="_blank" rel="noopener">PDF ↗</a>' : '') + (external ? '' : '<button class="secondary-button" type="button" data-invoice-copy="' + record.id + '">На основе</button>') + '<button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + record.id + '" title="В корзину" aria-label="' + escapeHtml('В корзину · ' + label) + '">×</button></div></div>';
    }).join`, `rows.map`, `focusStatusButton`, `[...$("invoiceList").querySelectorAll('[data-invoice-plan]')].find((button) => button.dataset.invoicePlan === focusedPlan)?.focus`, `[...$("invoiceList").querySelectorAll('[data-invoice-plan]')].find`, `$("invoiceList").querySelectorAll`, `[...$("invoiceList").querySelectorAll('[data-invoice-schedule]')].find((button) => button.dataset.invoiceSchedule === focusedSchedule)?.focus`, `[...$("invoiceList").querySelectorAll('[data-invoice-schedule]')].find`, `[...$("invoiceList").querySelectorAll('[data-invoice-reconciliation]')].find(button => button.dataset.invoiceReconciliation === focusedReconciliation)?.focus`, `[...$("invoiceList").querySelectorAll('[data-invoice-reconciliation]')].find`, `InvoiceDocuments.restoreFocus`.

Прямые присваивания полям/свойствам: `$("invoiceCount").textContent`, `$("invoiceList").innerHTML`, `$("invoiceList").invoiceRecords`.

## focusStatusButton

[static/invoices.js:113](../../../static/invoices.js#L113) · `FunctionDeclaration`.

```javascript
function focusStatusButton(key)
```

Возвращает фокус на статус выбранной строки счёта.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$("invoiceList").querySelectorAll('[data-invoice-status]')].find((button) =>
      button.dataset.invoiceStatus === key.id && button.dataset.value === key.value)?.focus`, `[...$("invoiceList").querySelectorAll('[data-invoice-status]')].find`, `$("invoiceList").querySelectorAll`, `$`.

## toggleListStatus

[static/invoices.js:120](../../../static/invoices.js#L120) · `FunctionDeclaration`.

```javascript
async function toggleListStatus(record, value)
```

Сохраняет изменение статуса строки счёта.

Использует `/api/invoice-list-status`.

Непосредственные вызовы: `statusSaving.has`, `statusSaving.add`, `renderInvoiceList`, `$`, `request`, `($("invoiceList").invoiceRecords || []).map`, `refreshList`, `statusSaving.delete`, `focusStatusButton`.

## refreshList

[static/invoices.js:146](../../../static/invoices.js#L146) · `FunctionDeclaration`.

```javascript
async function refreshList(force = false)
```

Перечитывает счета из SQLite с учётом открытых редакторов.

Использует `/api/invoices`.

Непосредственные вызовы: `Boolean`, `isWorkOrderPath`, `$`, `$("invoiceList").replaceChildren`, `renderCandidates`, `checkInvoiceFolder`, `request`, `apiUrl`, `renderInvoiceList`, `Set`, `[...result.items, ...trashed].flatMap((record) => [record.filename,
        ...(record.closing_documents || []).map((item) => item.filename), ...(record.closing_documents_trash || []).map((item) => item.filename)])
        .filter(Boolean).map`, `[...result.items, ...trashed].flatMap((record) => [record.filename,
        ...(record.closing_documents || []).map((item) => item.filename), ...(record.closing_documents_trash || []).map((item) => item.filename)])
        .filter`, `[...result.items, ...trashed].flatMap`, `folderCandidates.filter`, `trashed.map((record) => {
        const label = invoiceLabel(record), marker = record.trash;
        const sync = marker.error ? marker.error + ' · автоповтор' : marker.state === 'pending' ? 'Перенос PDF в .trash…' : record.filename ? 'В корзине · # bills/.trash' : record.state === 'planned' ? 'План в корзине · ' + displayPlanDate(record) + ' ' + planAmount(record) : 'Черновик в корзине';
        const comment = record.state === 'external' && record.data.comment ? record.data.comment + ' · ' : '';
        return '<div class="invoice-row"><div class="invoice-row-name"><span class="invoice-row-label" title="' + escapeHtml(label) + '">' + escapeHtml(label) + '</span><small class="invoice-row-meta' + (marker.error ? ' error' : '') + '" title="' + escapeHtml(comment + sync) + '">' + escapeHtml(comment + sync) + '</small></div><button class="secondary-button" type="button" data-invoice-restore="' + record.id + '">Восстановить</button></div>';
      }).join`, `trashed.map`.

Прямые присваивания полям/свойствам: `$("invoiceSection").hidden`, `$("invoiceCount").textContent`, `$("invoiceTrash").hidden`, `$("invoiceTrash").open`, `$("invoiceListState").textContent`, `$("invoiceTrashCount").textContent`, `$("invoiceTrashList").innerHTML`, `$("invoiceTrashList").invoiceRecords`.

## renderCandidates

[static/invoices.js:191](../../../static/invoices.js#L191) · `FunctionDeclaration`.

```javascript
function renderCandidates()
```

Показывает найденные ещё не прикреплённые PDF из # bills.

Использует `/api/file`.

Непосредственные вызовы: `$`, `folderCandidates.map((item) => '<div class="invoice-row invoice-candidate"><div class="invoice-row-content"><a class="invoice-row-name" href="' +
      escapeHtml(apiUrl('/api/file', candidatePath + '/# bills/' + item.name)) + '" target="_blank" rel="noopener"><span class="invoice-row-label">' + escapeHtml(item.name) +
      '</span></a><small class="invoice-row-meta">В папке найден новый счёт · ' + escapeHtml(formatSize(item.size)) + '</small></div><button type="button" class="secondary-button" data-invoice-candidate="' +
      escapeHtml(item.name) + '" aria-label="Прикрепить найденный счёт · ' + escapeHtml(item.name) + '">Прикрепить?</button></div>').join`, `folderCandidates.map`, `[...list.querySelectorAll('[data-invoice-candidate]')]
      .find((button) => button.dataset.invoiceCandidate === focused)?.focus`, `[...list.querySelectorAll('[data-invoice-candidate]')]
      .find`, `list.querySelectorAll`.

Прямые присваивания полям/свойствам: `list.innerHTML`.

## checkInvoiceFolder

[static/invoices.js:205](../../../static/invoices.js#L205) · `FunctionDeclaration`.

```javascript
async function checkInvoiceFolder()
```

Явно запрашивает проверку непосредственных файлов # bills.

Использует `/api/invoice-folder-candidates`.

Непосредственные вызовы: `isWorkOrderPath`, `$`, `status.classList.remove`, `request`, `apiUrl`, `renderCandidates`, `[result.items.length ? 'Найдено новых PDF: ' + result.items.length : 'Новых PDF нет', result.warning].filter(Boolean).join`, `[result.items.length ? 'Найдено новых PDF: ' + result.items.length : 'Новых PDF нет', result.warning].filter`, `status.classList.add`.

Прямые присваивания полям/свойствам: `$("checkInvoiceFolder").disabled`, `status.textContent`.

## newIdentity

[static/invoices.js:225](../../../static/invoices.js#L225) · `FunctionDeclaration`.

```javascript
function newIdentity()
```

Создаёт новый UUID клиентского намерения для защиты от повтора.

Использует `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((b) => b.toString(16).padStart(2, "0")).join`.

Непосредственные вызовы: `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((b) => b.toString(16).padStart(2, "0")).join`, `[...bytes].map`, `hex.slice`.

Прямые присваивания полям/свойствам: `bytes[6]`, `bytes[8]`.

## showPlan

[static/invoices.js:234](../../../static/invoices.js#L234) · `FunctionDeclaration`.

```javascript
function showPlan(record = null, options = {})
```

Открывает редактор самостоятельного или связанного плана платежа.

Использует `Intl.DateTimeFormat`, `Date`.

Непосредственные вызовы: `new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Moscow', year: 'numeric', month: '2-digit', day: '2-digit' }).format`, `Intl.DateTimeFormat`, `Date`, `newIdentity`, `Boolean`, `$`, `state.orders.find`, `invoiceLabel`, `normalizePlanDate`, `(amount / 100).toFixed(2).replace`, `(amount / 100).toFixed`, `updatePlanFields`, `JSON.stringify`, `planValues`, `$("planInvoiceState").classList.remove`, `$("planInvoiceDialog").showModal`, `$("planInvoiceDate").focus`, `readPlanSource`.

Прямые присваивания полям/свойствам: `$(id).disabled`, `$("planInvoiceOrder").textContent`, `$("planInvoiceSource").hidden`, `$("planInvoiceSource").textContent`, `$("planInvoiceDate").value`, `$("planInvoicePeriod").value`, `$("planInvoiceOperation").value`, `$("planInvoiceAmount").value`, `$("planInvoiceText").value`, `$("deleteInvoicePlan").hidden`, `planning.savedForm`, `$("planInvoiceState").textContent`, `$("refreshInvoicePlan").hidden`, `$("saveInvoicePlan").disabled`, `$("saveInvoicePlan").textContent`.

## closePlan

[static/invoices.js:265](../../../static/invoices.js#L265) · `FunctionDeclaration`.

```javascript
function closePlan()
```

Закрывает форму плана и очищает её локальное состояние.

Использует `$("planInvoiceDialog").close`, `$`.

Непосредственные вызовы: `$("planInvoiceDialog").close`, `$`.

## planValues

[static/invoices.js:272](../../../static/invoices.js#L272) · `FunctionDeclaration`.

```javascript
function planValues()
```

Собирает текущие значения формы плана платежа.

Использует `$`.

Непосредственные вызовы: `$`.

## normalizePlanDate

[static/invoices.js:279](../../../static/invoices.js#L279) · `FunctionDeclaration`.

```javascript
function normalizePlanDate()
```

Нормализует дату плана относительно дневного или недельного периода.

Использует `$`, `Date`, `Number.isNaN`.

Непосредственные вызовы: `$`, `Date`, `Number.isNaN`, `date.getTime`, `date.setUTCDate`, `date.getUTCDate`, `date.getUTCDay`, `date.toISOString().slice`, `date.toISOString`, `displayPlanDate`.

Прямые присваивания полям/свойствам: `$("planInvoiceDateCaption").textContent`, `$("planInvoiceWeekHint").hidden`, `$("planInvoiceWeekHint").textContent`, `$("planInvoiceDate").value`.

## updatePlanFields

[static/invoices.js:293](../../../static/invoices.js#L293) · `FunctionDeclaration`.

```javascript
function updatePlanFields()
```

Обновляет доступность и подписи зависимых полей плана.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `$("planInvoiceOperation").querySelector`, `Boolean`.

Прямые присваивания полям/свойствам: `$("planInvoiceAmountLabel").hidden`, `$("planInvoiceAmount").required`, `$("planInvoiceTextLabel").hidden`, `invoiceOption.hidden`, `invoiceOption.disabled`.

## readPlanSource

[static/invoices.js:304](../../../static/invoices.js#L304) · `FunctionDeclaration`.

```javascript
async function readPlanSource(current, preserveInput = false)
```

Читает выбранный источник плана из текущей формы.

Использует `/api/invoice-plan-source`.

Непосредственные вызовы: `$`, `request`, `apiUrl`, `Number.isSafeInteger`, `(source.total / 100).toFixed(2).replace`, `(source.total / 100).toFixed`, `cash`, `$("planInvoiceState").classList.remove`, `$("planInvoiceState").classList.add`.

Прямые присваивания полям/свойствам: `current.sourceLoading`, `$("saveInvoicePlan").disabled`, `$("refreshInvoicePlan").disabled`, `$("planInvoiceState").textContent`, `current.source`, `$("planInvoiceAmount").value`, `$("planInvoiceSource").textContent`, `current.conflict`, `$("refreshInvoicePlan").hidden`, `$("deleteInvoicePlan").disabled`.

## savePlan

[static/invoices.js:336](../../../static/invoices.js#L336) · `FunctionDeclaration`.

```javascript
async function savePlan()
```

Сохраняет план платежа с UUID и ожидаемой версией.

Использует `/api/invoice-plan`.

Непосредственные вызовы: `normalizePlanDate`, `$`, `status.classList.remove`, `request`, `planValues`, `closePlan`, `refreshList`, `notify`, `invoiceLabel`, `displayPlanDate`, `loadOrders`, `status.classList.add`.

Прямые присваивания полям/свойствам: `current.busy`, `$(id).disabled`, `status.textContent`, `current.conflict`, `$("refreshInvoicePlan").hidden`, `$("saveInvoicePlan").disabled`, `$("deleteInvoicePlan").disabled`.

## deletePlan

[static/invoices.js:367](../../../static/invoices.js#L367) · `FunctionDeclaration`.

```javascript
async function deletePlan()
```

Помещает выбранный план платежа в корзину.

Использует `$`, `removeCalendarRecord`, `closePlan`.

Непосредственные вызовы: `$`, `removeCalendarRecord`, `closePlan`, `$("planInvoiceState").classList.add`.

Прямые присваивания полям/свойствам: `current.busy`, `$(id).disabled`, `$("planInvoiceState").textContent`, `current.conflict`, `$("refreshInvoicePlan").hidden`, `$("deleteInvoicePlan").disabled`, `$("saveInvoicePlan").disabled`.

## checkPlan

[static/invoices.js:393](../../../static/invoices.js#L393) · `FunctionDeclaration`.

```javascript
async function checkPlan()
```

Перечитывает источник плана после конфликта без автоматического повтора.

Использует `/api/invoice`.

Непосредственные вызовы: `readPlanSource`, `$`, `request`, `apiUrl`, `Error`, `invoiceLabel`, `displayPlanDate`, `planAmount`, `$("planInvoiceState").classList.remove`.

Прямые присваивания полям/свойствам: `button.disabled`, `current.record`, `current.conflict`, `$("planInvoiceState").textContent`, `button.hidden`, `$("saveInvoicePlan").disabled`, `$("deleteInvoicePlan").disabled`.

## showExternal

[static/invoices.js:413](../../../static/invoices.js#L413) · `FunctionDeclaration`.

```javascript
function showExternal(record = null, candidate = null)
```

Открывает форму прикрепления внешнего PDF к заказу.

Использует `newIdentity`, `$`, `$("externalInvoiceDialog").classList.remove`.

Непосредственные вызовы: `newIdentity`, `$`, `$("externalInvoiceDialog").classList.remove`, `Boolean`, `$("externalInvoiceState").classList.remove`, `$("externalInvoiceDialog").showModal`, `(record || candidate ? $("externalInvoiceComment") : $("externalInvoiceFile")).focus`.

Прямые присваивания полям/свойствам: `$("externalInvoiceTitle").textContent`, `$("externalInvoicePath").textContent`, `$("externalInvoiceFile").value`, `$("externalInvoiceFileHint").textContent`, `$("externalInvoiceFileLabel").hidden`, `$("externalInvoiceName").hidden`, `$("externalInvoiceName").textContent`, `$("externalInvoiceComment").value`, `$("externalInvoiceState").textContent`, `$("externalInvoicePdf").hidden`, `$("saveExternalInvoice").textContent`.

## closeExternal

[static/invoices.js:436](../../../static/invoices.js#L436) · `FunctionDeclaration`.

```javascript
function closeExternal()
```

Закрывает форму внешнего PDF и освобождает выбранный файл.

Использует `$("externalInvoiceDialog").close`, `$`.

Непосредственные вызовы: `$("externalInvoiceDialog").close`, `$`.

## selectExternalFile

[static/invoices.js:444](../../../static/invoices.js#L444) · `FunctionDeclaration`.

```javascript
function selectExternalFile(file)
```

Проверяет выбранный файл внешнего PDF в браузере.

Использует `$`, `/\.pdf$/i.test`, `status.classList.add`.

Непосредственные вызовы: `$`, `/\.pdf$/i.test`, `status.classList.add`, `newIdentity`, `formatSize`, `status.classList.remove`.

Прямые присваивания полям/свойствам: `status.textContent`, `attachment.file`, `attachment.id`, `$("externalInvoiceFileHint").textContent`.

## saveExternal

[static/invoices.js:458](../../../static/invoices.js#L458) · `FunctionDeclaration`.

```javascript
async function saveExternal()
```

Передаёт проверенный внешний PDF и комментарий серверу.

Использует `/api/invoice-folder-attach`, `/api/invoice-upload`, `/api/invoice-comment`.

Непосредственные вызовы: `$`, `/\.pdf$/i.test`, `status.classList.add`, `status.classList.remove`, `request`, `Promise`, `folderCandidates.filter`, `renderCandidates`, `closeExternal`, `refreshList`.

Прямые присваивания полям/свойствам: `status.textContent`, `current.busy`, `$(id).disabled`, `current.record`, `current.saved`, `$("invoiceFolderState").textContent`.

## itemMarkup

[static/invoices.js:500](../../../static/invoices.js#L500) · `FunctionDeclaration`.

```javascript
function itemMarkup(item)
```

Строит строку позиции редактируемого счёта.

Экранирует значения полей и задаёт допустимую длину ввода каждой позиции.

Непосредственные вызовы: `[["name", "Наименование", 500], ["quantity", "Количество", 30], ["unit", "Единица", 16], ["price", "Цена", 30]].map(([key, label, limit]) =>
      '<td><input data-field="' + key + '" aria-label="' + label + '" maxlength="' + limit + '" value="' + escapeHtml(item[key]) + '"' + (["quantity", "price"].includes(key) ? ' inputmode="decimal"' : '') + '></td>').join`, `[["name", "Наименование", 500], ["quantity", "Количество", 30], ["unit", "Единица", 16], ["price", "Цена", 30]].map`.

## collect

[static/invoices.js:507](../../../static/invoices.js#L507) · `FunctionDeclaration`.

```javascript
function collect()
```

Собирает значения полей редактора счёта для сохранения.

Использует `Object.fromEntries`, `Object.entries(fields).map`, `Object.entries`.

Непосредственные вызовы: `Object.fromEntries`, `Object.entries(fields).map`, `Object.entries`, `Object.keys(sellerFields).map`, `Object.keys`, `[...$("invoiceItems").rows].map`, `$`.

Прямые присваивания полям/свойствам: `data.seller`, `data.items`.

## totals

[static/invoices.js:516](../../../static/invoices.js#L516) · `FunctionDeclaration`.

```javascript
function totals()
```

Вычисляет отображаемые итоги позиций счёта.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `scaled`, `row.querySelector`, `cash`, `Number`.

Прямые присваивания полям/свойствам: `row.querySelector(".invoice-item-total").textContent`, `$("invoiceTotal").textContent`, `$("invoiceContract").hidden`, `$("invoiceTitle").textContent`.

## scaled

[static/invoices.js:520](../../../static/invoices.js#L520) · `ArrowFunctionExpression`.

```javascript
const scaled = (value, places) =>
```

Преобразует десятичное значение в масштабированное целое для расчёта.

Использует `value.replace(/[\s\u00a0]/g, "").replace`, `value.replace`, `new RegExp("^\\d+(?:\\.\\d{0," + places + "})?$").test`.

Непосредственные вызовы: `value.replace(/[\s\u00a0]/g, "").replace`, `value.replace`, `new RegExp("^\\d+(?:\\.\\d{0," + places + "})?$").test`, `RegExp`, `Error`, `value.split`, `BigInt`, `fraction.padEnd`.

## controls

[static/invoices.js:541](../../../static/invoices.js#L541) · `FunctionDeclaration`.

```javascript
function controls()
```

Обновляет доступность действий открытого редактора в модуле счетов и планов платежей.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$("invoiceForm").querySelectorAll`, `$`, `Boolean`.

Прямые присваивания полям/свойствам: `input.disabled`, `$(id).disabled`, `$("saveInvoice").hidden`, `$("issueInvoice").hidden`, `$("addInvoiceItem").hidden`, `$("previewInvoice").textContent`, `$("invoiceDraftHint").textContent`.

## show

[static/invoices.js:555](../../../static/invoices.js#L555) · `FunctionDeclaration`.

```javascript
function show(record)
```

Показывает компонент по полученным данным и текущему состоянию в модуле счетов и планов платежей.

Использует `$`, `Object.entries`.

Непосредственные вызовы: `$`, `Object.entries`, `Object.entries(sellerFields).map(([key, label]) => '<label>' + label + '<input id="invoiceSeller-' + key + '" maxlength="' + (key === "address" ? 500 : 300) + '" value="' + escapeHtml(record.data.seller[key] || "") + '"></label>').join`, `Object.entries(sellerFields).map`, `record.data.items.map(itemMarkup).join`, `record.data.items.map`, `JSON.stringify`, `collect`, `message`, `controls`, `totals`, `$("invoiceDialog").showModal`, `$("invoiceBuyer").focus`.

Прямые присваивания полям/свойствам: `$("invoiceTitle").textContent`, `$("invoiceOrderPath").textContent`, `$(id).value`, `$("invoiceSellerFields").innerHTML`, `$("invoiceItems").innerHTML`, `$("invoiceRememberSeller").checked`, `editor.saved`.

## save

[static/invoices.js:572](../../../static/invoices.js#L572) · `FunctionDeclaration`.

```javascript
async function save()
```

Сохраняет данные открытой формы с ожидаемой версией.

Использует `/api/invoice-save`.

Непосредственные вызовы: `clearTimeout`, `save`, `collect`, `JSON.stringify`, `$`, `message`, `request`, `controls`, `refreshList`.

Прямые присваивания полям/свойствам: `current.saving`, `current.record`, `current.saved`, `current.dirty`.

## close

[static/invoices.js:597](../../../static/invoices.js#L597) · `FunctionDeclaration`.

```javascript
async function close()
```

Закрывает компонент и освобождает его временное состояние в модуле счетов и планов платежей.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `save`, `clearTimeout`, `$("invoiceDialog").close`, `$`, `refreshList`.

## create

[static/invoices.js:606](../../../static/invoices.js#L606) · `FunctionDeclaration`.

```javascript
async function create(source)
```

Создаёт новый черновик счёта по выбранному действию.

Использует `/api/invoice-create`.

Непосредственные вызовы: `newIdentity`, `$`, `request`, `show`, `refreshList`.

Прямые присваивания полям/свойствам: `$("newInvoice").disabled`.

## action

[static/invoices.js:623](../../../static/invoices.js#L623) · `FunctionDeclaration`.

```javascript
function action(work)
```

Маршрутизирует выбранное действие пользователя внутри компонента.

Использует `Promise.resolve().then(work).catch`, `Promise.resolve().then`, `Promise.resolve`.

Непосредственные вызовы: `Promise.resolve().then(work).catch`, `Promise.resolve().then`, `Promise.resolve`.

## changed

[static/invoices.js:631](../../../static/invoices.js#L631) · `FunctionDeclaration`.

```javascript
function changed()
```

Помечает редактор изменённым и обновляет зависимые поля.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `JSON.stringify`, `collect`, `$`, `totals`, `clearTimeout`, `message`, `setTimeout`.

Прямые присваивания полям/свойствам: `editor.dirty`, `editor.timer`.

## refresh

[static/invoices.js:639](../../../static/invoices.js#L639) · `ArrowFunctionExpression`.

```javascript
refresh: () =>
```

Перечитывает данные открытого компонента по установленным правилам в модуле счетов и планов платежей.

Использует `refreshList`.

Непосредственные вызовы: `refreshList`.

## accept

[static/invoices.js:640](../../../static/invoices.js#L640) · `ArrowFunctionExpression`.

```javascript
accept: (saved) =>
```

Принимает подтверждённые данные счёта в локальный редактор.

Использует `renderInvoiceList`, `($("invoiceList").invoiceRecords || []).map`, `$`.

Непосредственные вызовы: `renderInvoiceList`, `($("invoiceList").invoiceRecords || []).map`, `$`.
