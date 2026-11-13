# static/app.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/app.js](../../../static/app.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-%24"></a>

## $

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const $ = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

<a id="symbol-activityRoute"></a>

## activityRoute

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function activityRoute(folder)
```

Выбирает API активности клиента или объекта.

Использует `/api/object-activity`, `/api/client-activity`.

<a id="symbol-apiUrl"></a>

## apiUrl

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const apiUrl = (route, path = "", extra = {}) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `URLSearchParams`.

Непосредственные вызовы: `URLSearchParams`.

<a id="symbol-applyCalendarDeletion"></a>

## applyCalendarDeletion

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applyCalendarDeletion(entry, saved, deleted)
```

Применяет подтверждённое удаление к локальному состоянию календаря.

Использует `state.calendarInvoicePlans.filter`, `state.calendarInvoicePlans.push`, `applyFreeCalendarEvent`.

Непосредственные вызовы: `state.calendarInvoicePlans.filter`, `state.calendarInvoicePlans.push`, `applyFreeCalendarEvent`, `applyOrderRecord`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.calendarInvoicePlans`.

<a id="symbol-applyCalendarInvoicePlan"></a>

## applyCalendarInvoicePlan

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applyCalendarInvoicePlan(saved)
```

Применяет подтверждённый план платежа к локальной сводке.

Использует `state.calendarInvoicePlans.find`, `Object.assign`.

Непосредственные вызовы: `state.calendarInvoicePlans.find`, `Object.assign`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-applyFreeCalendarEvent"></a>

## applyFreeCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applyFreeCalendarEvent(saved)
```

Применяет подтверждённое свободное событие к локальной сводке.

Использует `state.calendarEvents.find`, `state.calendarEvents.filter`, `state.calendarEvents.push`.

Непосредственные вызовы: `state.calendarEvents.find`, `state.calendarEvents.filter`, `state.calendarEvents.push`, `state.calendarEvents.sort`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.calendarEvents`.

<a id="symbol-applyOrderGroupVisibility"></a>

## applyOrderGroupVisibility

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applyOrderGroupVisibility(button)
```

Применяет сворачивание к строкам уже построенной группы.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `orderGroupCollapsed`, `button.setAttribute`, `String`, `$("ordersTableBody").querySelectorAll("[data-order-group-row]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`.

<a id="symbol-applyOrderRecord"></a>

## applyOrderRecord

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applyOrderRecord(folder, saved)
```

Применяет подтверждённую запись заказа к локальным представлениям.

Использует `orders.find`, `Object.assign`.

Непосредственные вызовы: `orders.find`, `Object.assign`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `folder.order`.

<a id="symbol-applyRemotePurchaseUpdate"></a>

## applyRemotePurchaseUpdate

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applyRemotePurchaseUpdate(folder, order)
```

Применяет фоновое изменение закупок с проверкой локального черновика.

Использует `$`, `unchanged`, `JSON.stringify`.

Непосредственные вызовы: `document.activeElement?.closest`, `$`, `unchanged`, `JSON.stringify`, `Array.isArray`, `order.purchase_items.map`, `renderPurchases`, `renderExportState`.

Прямые присваивания полям/свойствам: `folder.order`, `folder.purchase_items`.

<a id="symbol-applyRemotePurchaseUpdate.unchanged"></a>

## applyRemotePurchaseUpdate.unchanged

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const unchanged = record =>
```

Сравнивает данные редактора с сохранённым исходным состоянием.

Использует `JSON.stringify`.

Непосредственные вызовы: `JSON.stringify`, `["path", "id", "title", "status", "financial_status", "note", "amount", "costs", "paid", "updated"].map`.

<a id="symbol-applySketchGroup"></a>

## applySketchGroup

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function applySketchGroup(folder, path, record)
```

Применяет полученную группу актуальности эскизов к локальному состоянию.

Использует `item.name.normalize`, `JSON.stringify`.

Непосредственные вызовы: `item.name.normalize`, `JSON.stringify`.

Прямые присваивания полям/свойствам: `item.relevance`.

<a id="symbol-askRemoveOrder"></a>

## askRemoveOrder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function askRemoveOrder(path)
```

Открывает предусмотренное подтверждение снятия регистрации заказа.

Использует `state.orders.find`, `notify`, `$`.

Непосредственные вызовы: `state.orders.find`, `notify`, `$`, `isWorkOrderPath`, `$("removeOrderDialog").showModal`, `$("cancelRemoveOrder").focus`.

Прямые присваивания полям/свойствам: `state.removeOrder`, `$("removeOrderName").textContent`, `$("removeOrderPath").textContent`, `$("removeOrderTitle").textContent`, `$("confirmRemoveOrder").textContent`, `$("removeOrderDescription").textContent`.

<a id="symbol-calendarEventEntries"></a>

## calendarEventEntries

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function calendarEventEntries(order, period)
```

Выбирает дневные или недельные записи текущего заказа.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-cancelCalendarTodoPreviewSwitch"></a>

## cancelCalendarTodoPreviewSwitch

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function cancelCalendarTodoPreviewSwitch()
```

Отменяет ожидающее переключение окна задач на соседнее событие.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.switchTimer`, `calendarTodoPreview.pendingAnchor`.

<a id="symbol-changeOrderDeadline"></a>

## changeOrderDeadline

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function changeOrderDeadline({ path, id, revision, week, selected }, button)
```

Сохраняет изменение одной недели срока заказа.

Использует `/api/order-deadline-week`.

Непосредственные вызовы: `orderRowSaving`, `findListOrder`, `state.deadlineSaving.add`, `renderOrderHeading`, `renderCardDeadlines`, `$("ordersTableBody").querySelectorAll("[data-order-deadline], [data-order-status], [data-order-favorite], [data-order-flag], [data-order-blue-plus], [data-order-dollar]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`, `request("/api/order-deadline-week", { path, id, revision, week, selected }).then`, `request`, `notify`, `loadOrders`, `state.deadlineSaving.delete`, `renderStatus`, `[...$("orderCardDeadlineList").querySelectorAll("[data-deadline-week]")].find`, `$("orderCardDeadlineList").querySelectorAll`, `(focus || $("orderCardDeadlineEarlier")).focus`, `hasOrderList`, `renderOrders`, `focusOrderDeadline`, `$("orderSearch").focus`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `folder.deadlineError`, `state.saving`, `folder.deadlineConflict`.

<a id="symbol-changeOrderProductionStatus"></a>

## changeOrderProductionStatus

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function changeOrderProductionStatus(select)
```

Сохраняет изменение производственного статуса одной строки.

Использует `/api/order-supplier-status`, `/api/order-status`.

Непосредственные вызовы: `Number`, `orderRowSaving`, `findListOrder`, `state.orderStatusSaving.add`, `select.setAttribute`, `$("ordersTableBody").querySelectorAll("[data-order-favorite], [data-order-deadline], [data-order-flag], [data-order-blue-plus], [data-order-dollar]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`, `request`, `orders.find`, `Object.assign`, `isWorkOrderList`, `state.objectOrders.find`, `state.workArchivedOrders.filter`, `state.workArchivedPaths.push`, `saved.path.normalize`, `renderFavoriteOrders`, `notify`, `loadOrders`, `state.orderStatusSaving.delete`, `hasOrderList`, `renderOrders`, `[...$("ordersTableBody").querySelectorAll("[data-order-status]")].find`, `(next || $("orderSearch")).focus`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `select.disabled`, `state.workArchivedOrders`.

<a id="symbol-closeCalendarEvent"></a>

## closeCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function closeCalendarEvent()
```

Закрывает редактор календаря и очищает связанное состояние.

Использует `$("calendarEventDialog").close`, `$`.

Непосредственные вызовы: `$("calendarEventDialog").close`, `$`.

Прямые присваивания полям/свойствам: `state.calendarEvent`.

<a id="symbol-closeCalendarEventMenu"></a>

## closeCalendarEventMenu

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function closeCalendarEventMenu(restoreFocus = true)
```

Закрывает контекстное меню события и очищает его состояние.

Использует `$`, `(menu.slot.isConnected ? menu.slot : $("calendarViewport")).focus`.

Непосредственные вызовы: `$`, `(menu.slot.isConnected ? menu.slot : $("calendarViewport")).focus`.

Прямые присваивания полям/свойствам: `state.calendarMenu`, `$("calendarEventMenu").hidden`.

<a id="symbol-closeCalendarTodoPreview"></a>

## closeCalendarTodoPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function closeCalendarTodoPreview(restoreFocus = false)
```

Закрывает общее окно задач или комментария и отменяет отложенные действия.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `cancelCalendarTodoPreviewSwitch`, `$`, `anchor.removeAttribute`, `anchor.focus`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.anchor`, `calendarTodoPreview.pinned`, `$("calendarTodoPreview").hidden`, `calendarTodoPreview.suppressed`.

<a id="symbol-closeOrderLinks"></a>

## closeOrderLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function closeOrderLinks()
```

Закрывает окно связей и возвращает фокус инициатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$("orderLinksDialog").close`, `$`, `[...$("ordersTableBody").querySelectorAll('[data-order-related]')].find(button => button.dataset.orderRelated === edit.path)?.focus`, `[...$("ordersTableBody").querySelectorAll('[data-order-related]')].find`, `$("ordersTableBody").querySelectorAll`.

Прямые присваивания полям/свойствам: `state.orderLinks`.

<a id="symbol-closePreview"></a>

## closePreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function closePreview()
```

Закрывает просмотрщик и освобождает его локальные ресурсы.

Использует `saveFileComment`, `$("previewDialog").close`, `$`.

Непосредственные вызовы: `saveFileComment`, `$("previewDialog").close`, `$`.

<a id="symbol-colorCalendarEvent"></a>

## colorCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function colorCalendarEvent(color)
```

Сохраняет индивидуальный цвет выбранного события.

Использует `/api/calendar-color`, `/api/order-calendar-color`.

Непосредственные вызовы: `state.calendarMoving.has`, `orderRowSaving`, `closeCalendarEventMenu`, `state.calendarMoving.add`, `request`, `applyFreeCalendarEvent`, `applyOrderRecord`, `notify`, `loadOrders`, `state.calendarMoving.delete`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-compareOrders"></a>

## compareOrders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function compareOrders(a, b, key = state.orderSort, direction = state.orderDirection)
```

Сравнивает значения заказов по выбранному порядку сортировки.

Использует `OrderSorting.compare`.

Непосредственные вызовы: `OrderSorting.compare`.

<a id="symbol-confirmEventRemoval"></a>

## confirmEventRemoval

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function confirmEventRemoval()
```

Запрашивает предусмотренное подтверждение удаления выбранной цели.

Использует `/api/event-trash-preview`.

Непосредственные вызовы: `saveCurrentStatus`, `request`, `$`, `$("deleteEventDialog").showModal`, `$("cancelDeleteEvent").focus`.

Прямые присваивания полям/свойствам: `state.eventRemoval`, `$("deleteEventPath").textContent`, `$("deleteEventCount").textContent`, `$("deleteEventError").hidden`.

<a id="symbol-confirmFileRemoval"></a>

## confirmFileRemoval

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function confirmFileRemoval()
```

Запрашивает предусмотренное подтверждение удаления выбранной цели.

Использует `/api/files-trash-preview`.

Непосредственные вызовы: `folder.files.filter((file) => state.selectedFiles.has(file.path)).map`, `folder.files.filter`, `request`, `$`, `preview.files.map((file) => '<li>' + escapeHtml(file.path) + '</li>').join`, `preview.files.map`, `$("deleteFilesDialog").showModal`.

Прямые присваивания полям/свойствам: `state.fileRemoval`, `$("deleteFilesCount").textContent`, `$("deleteFilesList").innerHTML`, `$("confirmDeleteFiles").disabled`, `$("cancelDeleteFiles").disabled`.

<a id="symbol-copyText"></a>

## copyText

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function copyText(text)
```

Копирует полный исходный текст в буфер браузера.

В обычном HTTP использует событие copy, восстанавливает фокус и выделение.

Непосредственные вызовы: `navigator.clipboard.writeText`, `window.getSelection`, `Array.from`, `document.createElement`, `document.body.append`, `document.addEventListener`, `field.focus`, `field.select`, `field.setSelectionRange`, `document.execCommand`, `Error`, `document.removeEventListener`, `field.remove`, `focused.focus`, `selection.removeAllRanges`, `ranges.forEach`.

Прямые присваивания полям/свойствам: `field.value`, `field.readOnly`, `field.style.cssText`.

<a id="symbol-copyText.onCopy"></a>

## copyText.onCopy

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const onCopy = event =>
```

Подставляет исходный текст в буфер по событию копирования.

Сохраняет точное значение, включая пробелы и переводы строк.

Непосредственные вызовы: `event.clipboardData.setData`, `event.preventDefault`.

<a id="symbol-createImageReport"></a>

## createImageReport

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function createImageReport()
```

Запрашивает PDF-отчёт по выбранным изображениям и комментариям.

Использует `/api/image-report`.

Непосредственные вызовы: `filteredFiles`, `[...files, ...folder.files.filter((file) => !files.includes(file))].filter((file) => state.selectedFiles.has(file.path)).map`, `[...files, ...folder.files.filter((file) => !files.includes(file))].filter`, `folder.files.filter`, `renderFileActions`, `request`, `loadOrderFiles`, `notify`.

Прямые присваивания полям/свойствам: `state.imageReport`, `report.result`, `report.error`, `report.busy`.

<a id="symbol-createObject"></a>

## createObject

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function createObject()
```

Создаёт объект по подтверждённым полям формы.

Использует `/api/object-folder-create`.

Непосредственные вызовы: `$("createObjectFolderForm").reportValidity`, `$`, `controls.forEach`, `saveCurrentStatus`, `request`, `$("createObjectFolderDialog").close`, `reloadClientTrees`, `navigate`, `notify`.

Прямые присваивания полям/свойствам: `state.creatingObject`, `$("newObjectError").hidden`, `$("newObjectError").textContent`.

<a id="symbol-createOrderFolder"></a>

## createOrderFolder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function createOrderFolder()
```

Создаёт папку заказа и применяет ответ устойчивой операции.

Использует `/api/order-folder-create`.

Непосредственные вызовы: `$("createOrderFolderForm").reportValidity`, `$`, `Boolean`, `controls.forEach`, `saveCurrentStatus`, `request`, `$("createOrderFolderDialog").close`, `loadTree`, `navigate`, `loadOrders`, `notify`, `isWorkOrderPath`.

Прямые присваивания полям/свойствам: `state.creatingOrderFolder`, `$("submitCreateOrderFolder").textContent`, `$("newOrderError").hidden`, `$("newOrderError").textContent`.

<a id="symbol-currentOrderValues"></a>

## currentOrderValues

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function currentOrderValues()
```

Собирает значения текущего редактора заказа для сравнения или сохранения.

Использует `$`, `state.folder.todo_items.map`, `Array.isArray`.

Непосредственные вызовы: `$`, `state.folder.todo_items.map`, `Array.isArray`, `Object.hasOwn`, `isWorkOrderPath`, `hasDescendantTodos`, `state.folder.purchase_items.map`.

<a id="symbol-deadlineCommentInput"></a>

## deadlineCommentInput

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function deadlineCommentInput(event)
```

Принимает ввод недельного события в локальный черновик.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `event.target.closest`, `folder?.deadlineCommentDrafts?.get`, `clearTimeout`, `renderDeadlineComments`, `setTimeout`.

Прямые присваивания полям/свойствам: `draft.value`, `draft.dirty`, `draft.error`, `folder.deadlineCommentTimer`.

<a id="symbol-deadlineWeekDates"></a>

## deadlineWeekDates

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function deadlineWeekDates(week)
```

Вычисляет даты начала и конца недели по её ключу.

Использует `Date`, `end.setUTCDate`, `end.getUTCDate`.

Непосредственные вызовы: `Date`, `end.setUTCDate`, `end.getUTCDate`, `dateLabel`, `end.toISOString().slice`, `end.toISOString`.

<a id="symbol-deadlineWeekDates.dateLabel"></a>

## deadlineWeekDates.dateLabel

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const dateLabel = (value) =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `value.slice`.

Непосредственные вызовы: `value.slice`.

<a id="symbol-deadlineWeekInfo"></a>

## deadlineWeekInfo

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function deadlineWeekInfo(start)
```

Готовит номер, даты и месяц выбранной недели срока.

Использует `Date`, `thursday.setUTCDate`, `thursday.getUTCDate`.

Непосредственные вызовы: `Date`, `thursday.setUTCDate`, `thursday.getUTCDate`, `thursday.getUTCFullYear`, `first.setUTCMonth`, `thursday.getUTCMonth`, `Math.ceil`, `deadlineWeekDates`.

<a id="symbol-deleteCalendarEventFromDialog"></a>

## deleteCalendarEventFromDialog

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function deleteCalendarEventFromDialog()
```

Удаляет сохранённое свободное событие любого периода либо дневное событие заказа из формы.

При конфликте или ошибке оставляет ввод; после успеха закрывает форму и сохраняет действие отмены.

Непосредственные вызовы: `renderCalendarEventControls`, `removeCalendarRecord`, `closeCalendarEvent`, `$`.

Прямые присваивания полям/свойствам: `edit.saving`, `edit.conflict`, `$("calendarEventState").textContent`.

<a id="symbol-deleteCalendarEventFromMenu"></a>

## deleteCalendarEventFromMenu

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function deleteCalendarEventFromMenu()
```

Удаляет точное событие из открытого меню или редактора.

Использует `findListOrder`, `state.calendarEvents.find`, `calendarEventEntries`.

Непосредственные вызовы: `findListOrder`, `state.calendarEvents.find`, `calendarEventEntries`, `closeCalendarEventMenu`, `removeCalendarRecord`, `notify`, `loadOrders`.

<a id="symbol-escapeHtml"></a>

## escapeHtml

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const escapeHtml = (value) =>
```

Экранирует текст перед вставкой в HTML-разметку или атрибут.

Заменяет &, <, >, кавычки и апостроф на безопасные HTML-сущности.

Непосредственные вызовы: `String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll`, `String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll`, `String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll`, `String(value).replaceAll("&", "&amp;").replaceAll`, `String(value).replaceAll`, `String`.

<a id="symbol-eventAction"></a>

## eventAction

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function eventAction(action)
```

Выполняет выбранную операцию формы события по текущей версии.

Использует `/api/event-folder-create`, `/api/event-folders-rename`, `/api/event-folders`.

Непосредственные вызовы: `$`, `form.reportValidity`, `$("createEventFolderDialog").querySelectorAll`, `controls.forEach`, `saveCurrentStatus`, `request`, `[...$("eventRenameList").querySelectorAll("input")].map`, `$("eventRenameList").querySelectorAll`, `apiUrl`, `renderEventProposal`, `loadTree`, `navigate`, `notify`, `$("createEventFolderDialog").close`.

Прямые присваивания полям/свойствам: `state.eventBusy`, `$("eventFolderError").hidden`, `state.eventPlan`, `$("eventFolderError").textContent`.

<a id="symbol-expandCardDeadlineWeeks"></a>

## expandCardDeadlineWeeks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function expandCardDeadlineWeeks(direction)
```

Раскрывает дополнительные недели срока в карточке.

Использует `[...folder.deadlineVisibleWeeks].sort`, `weeks.at`, `shiftDeadlineWeek`.

Непосредственные вызовы: `[...folder.deadlineVisibleWeeks].sort`, `weeks.at`, `shiftDeadlineWeek`, `folder.deadlineVisibleWeeks.add`, `renderCardDeadlines`.

<a id="symbol-fileCard"></a>

## fileCard

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function fileCard(file, selectable = true)
```

Строит карточку файла с превью, комментарием и прямым скачиванием CDR.

При selectable=false скрывает выбор; скачивание передаёт оригинал через `/api/file`.

Непосредственные вызовы: `apiUrl`, `["image", "cdr"].includes`, `escapeHtml`, `icon`, `state.selectedFiles.has`, `file.comment?.trim`, `fileDownloadButton`.

<a id="symbol-fileDownloadButton"></a>

## fileDownloadButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function fileDownloadButton(file)
```

Строит ссылку скачивания оригинала на устройство текущего браузера.

Использует прежний `/api/file?download=1`, не запуская приложение на сервере.

Непосредственные вызовы: `escapeHtml`, `apiUrl`.

<a id="symbol-filteredFiles"></a>

## filteredFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function filteredFiles()
```

Отбирает файлы по текущей группе и строке поиска.

Использует `normalize`, `state.fileQuery.trim`, `state.folder.files.filter`.

Непосредственные вызовы: `normalize`, `state.fileQuery.trim`, `state.folder.files.filter`, `files.sort`.

<a id="symbol-findListOrder"></a>

## findListOrder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function findListOrder(path)
```

Находит текущую строку заказа по устойчивой идентичности.

Использует `orderListRows().find`, `orderListRows`, `state.orders.find`.

Непосредственные вызовы: `orderListRows().find`, `orderListRows`, `state.orders.find`, `state.calendarSupplierOrders.find`.

<a id="symbol-flushDeadlineComments"></a>

## flushDeadlineComments

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function flushDeadlineComments(folder = state.folder)
```

Последовательно сохраняет ожидающие недельные тексты по версиям.

Использует `/api/order-deadline-comment`.

Непосредственные вызовы: `Promise.resolve`, `clearTimeout`, `[...(folder.deadlineCommentDrafts?.values() || [])].some`, `folder.deadlineCommentDrafts?.values`, `async () => {
    while (true) {
      while (state.saving) await state.saving;
      if (state.folder !== folder) throw new Error("Событие осталось в открытой карточке. Вернись к ней для сохранения.");
      const entry = [...folder.deadlineCommentDrafts].find(([, draft]) => draft.dirty);
      if (!entry) return;
      const [week, draft] = entry, value = draft.value, order = folder.order;
      if (folder.deadlineConflict) throw new Error(folder.deadlineError || "Обнови карточку перед сохранением события. Ввод остался в поле.");
      draft.saving = true;
      draft.error = "";
      state.deadlineSaving.add(order.path);
      ++state.ordersRequest;
      const saving = request("/api/order-deadline-comment", { path: order.path, id: order.id, revision: order.revision, week, comment: value }).then((saved) => {
        applyOrderRecord(folder, saved);
        draft.saved = saved.calendar_week_events?.[week] || "";
        if (draft.value === value) draft.value = draft.saved;
        draft.dirty = draft.value !== draft.saved;
      });
      state.saving = saving;
      renderOrderHeading();
      renderCardDeadlines();
      try {
        await saving;
      } catch (error) {
        folder.deadlineConflict = error.status === 409;
        draft.error = error.message + " Текст остался в поле." + (folder.deadlineConflict ? " Обнови карточку перед повтором." : "");
        if (folder.deadlineConflict) folder.deadlineError = draft.error;
        throw error;
      } finally {
        if (state.saving === saving) state.saving = null;
        state.deadlineSaving.delete(order.path);
        draft.saving = false;
        if (state.folder === folder) { renderOrderHeading(); renderStatus(); }
      }
    }
  }`, `pending.finally`.

Прямые присваивания полям/свойствам: `folder.deadlineCommentFlush`.

<a id="symbol-focusOrderDeadline"></a>

## focusOrderDeadline

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function focusOrderDeadline(path, week)
```

Возвращает фокус на кнопку недели выбранного заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `[...$("ordersTableBody").querySelectorAll("[data-order-deadline]")].find`, `$("ordersTableBody").querySelectorAll`, `$`, `button?.focus`, `Boolean`.

<a id="symbol-focusOrderFavorite"></a>

## focusOrderFavorite

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function focusOrderFavorite(path)
```

Возвращает фокус на звезду избранного заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `$("ordersTableBody").querySelectorAll("[data-order-favorite]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`.

<a id="symbol-focusOrderGroup"></a>

## focusOrderGroup

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function focusOrderGroup(group)
```

Возвращает фокус на заголовок выбранной группы списка.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `[...$("ordersTableBody").querySelectorAll("[data-order-group-toggle]")].find((button) => button.dataset.orderGroupToggle === group)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-group-toggle]")].find`, `$("ordersTableBody").querySelectorAll`, `$`.

<a id="symbol-focusOrderMarker"></a>

## focusOrderMarker

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function focusOrderMarker(path, kind)
```

Возвращает фокус на выбранную отметку после обновления строки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `[...$("ordersTableBody").querySelectorAll("[data-order-" + marker.suffix + "]")].find((button) => button.dataset[marker.data] === path)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-" + marker.suffix + "]")].find`, `$("ordersTableBody").querySelectorAll`, `$`.

<a id="symbol-focusSupplierStar"></a>

## focusSupplierStar

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function focusSupplierStar(path)
```

Возвращает фокус на звезду выбранного раздела поставщика.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$("subfolders").querySelectorAll("[data-supplier-favorite]")].find((button) => button.dataset.supplierFavorite === path)?.focus`, `[...$("subfolders").querySelectorAll("[data-supplier-favorite]")].find`, `$("subfolders").querySelectorAll`, `$`.

<a id="symbol-focusTree"></a>

## focusTree

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function focusTree(path)
```

Возвращает клавиатурный фокус в нужный узел дерева.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$("folderTree").querySelectorAll(".tree-row")].find`, `$("folderTree").querySelectorAll`, `$`, `row.closest('[role="tree"]').querySelectorAll(".tree-row").forEach`, `row.closest('[role="tree"]').querySelectorAll`, `row.closest`, `row.focus`.

Прямые присваивания полям/свойствам: `row.tabIndex`.

<a id="symbol-folderActivity"></a>

## folderActivity

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function folderActivity(folder)
```

Выбирает состояние активности папки текущей роли.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-folderParent"></a>

## folderParent

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const folderParent = (path) =>
```

Вычисляет относительный путь родительской папки.

Использует `path.split("/").slice(0, -1).join`, `path.split("/").slice`, `path.split`.

Непосредственные вызовы: `path.split("/").slice(0, -1).join`, `path.split("/").slice`, `path.split`.

<a id="symbol-folderUrl"></a>

## folderUrl

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const folderUrl = (path) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `/api/folder`.

Непосредственные вызовы: `apiUrl`.

<a id="symbol-formatDate"></a>

## formatDate

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const formatDate = (seconds) =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `new Date(seconds * 1000).toLocaleDateString`, `Date`.

Непосредственные вызовы: `new Date(seconds * 1000).toLocaleDateString`, `Date`.

<a id="symbol-formatSize"></a>

## formatSize

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const formatSize = (bytes) =>
```

Форматирует размер файла для интерфейса.

Использует `Math.round`, `(bytes / 1024 ** 2).toFixed`, `(bytes / 1024 ** 3).toFixed`.

Непосредственные вызовы: `Math.round`, `(bytes / 1024 ** 2).toFixed`, `(bytes / 1024 ** 3).toFixed`.

<a id="symbol-freeCalendarIdentity"></a>

## freeCalendarIdentity

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function freeCalendarIdentity()
```

Собирает UUID и версию свободного события для частичного запроса.

Использует `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join`.

Непосредственные вызовы: `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join`, `[...bytes].map`, `[hex.slice(0,8), hex.slice(8,12), hex.slice(12,16), hex.slice(16,20), hex.slice(20)].join`, `hex.slice`.

Прямые присваивания полям/свойствам: `bytes[6]`, `bytes[8]`.

<a id="symbol-groupObjectYears"></a>

## groupObjectYears

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function groupObjectYears()
```

Выполняет подтверждённую группировку заказов по годам.

Использует `/api/object-years`.

Непосредственные вызовы: `$`, `request`, `$("objectYearsDialog").close`, `Set`, `[...state.expanded].map`, `reloadClientTrees`, `navigate`, `loadOrders`, `notify`.

Прямые присваивания полям/свойствам: `state.groupingYears`, `$("submitObjectYears").disabled`, `$("cancelObjectYears").disabled`, `$("objectYearsError").hidden`, `$("objectYearsError").textContent`, `state.expanded`.

<a id="symbol-groupObjectYears.moved"></a>

## groupObjectYears.moved

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const moved=path=>
```

Обновляет путь элемента интерфейса после подтверждённого переноса папок.

Использует `state.objectYears.mappings.find`, `path.slice`.

Непосредственные вызовы: `state.objectYears.mappings.find`, `path.slice`.

<a id="symbol-hasDescendantTodos"></a>

## hasDescendantTodos

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function hasDescendantTodos(folder)
```

Проверяет наличие вложенных задач для показа сводки.

Использует `Boolean`.

Непосредственные вызовы: `Boolean`.

<a id="symbol-hasOrderList"></a>

## hasOrderList

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function hasOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Использует `isFolderOrderList`.

Непосредственные вызовы: `isFolderOrderList`.

<a id="symbol-hasPendingDeadlineComments"></a>

## hasPendingDeadlineComments

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function hasPendingDeadlineComments(folder = state.folder)
```

Проверяет наличие несохранённых недельных текстов карточки.

Использует `Boolean`, `[...(folder?.deadlineCommentDrafts?.values() || [])].some`.

Непосредственные вызовы: `Boolean`, `[...(folder?.deadlineCommentDrafts?.values() || [])].some`, `folder?.deadlineCommentDrafts?.values`.

<a id="symbol-hoverCalendarTodoPreview"></a>

## hoverCalendarTodoPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function hoverCalendarTodoPreview(anchor)
```

Планирует открытие или смену окна после устойчивого наведения.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `$("calendarTodoPreview").contains`, `$`, `clearTimeout`, `openCalendarTodoPreview`, `cancelCalendarTodoPreviewSwitch`, `setTimeout`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.pendingAnchor`, `calendarTodoPreview.switchTimer`.

<a id="symbol-icon"></a>

## icon

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const icon = (name) =>
```

Строит SVG-значок из локального набора символов.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-initializeOrderLinks"></a>

## initializeOrderLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function initializeOrderLinks()
```

Выбирает главного для прежней ненаправленной группы.

Использует `saveOrderLinksChange`.

Непосредственные вызовы: `saveOrderLinksChange`.

<a id="symbol-isFolderOrderList"></a>

## isFolderOrderList

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function isFolderOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Использует `isObjectOrderList`, `isWorkOrderList`.

Непосредственные вызовы: `isObjectOrderList`, `isWorkOrderList`.

<a id="symbol-isObjectOrderList"></a>

## isObjectOrderList

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function isObjectOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-isWorkOrderList"></a>

## isWorkOrderList

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function isWorkOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-isWorkOrderPath"></a>

## isWorkOrderPath

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const isWorkOrderPath = (path) =>
```

Определяет производственную область по относительному пути заказа.

Использует `/^#\s*work$/i.test`, `String(path || "").split`, `String`.

Непосредственные вызовы: `/^#\s*work$/i.test`, `String(path || "").split`, `String`.

<a id="symbol-loadChildren"></a>

## loadChildren

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadChildren(path)
```

Загружает непосредственных потомков раскрываемого узла.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `state.children.has`, `request`, `treeUrl`, `registerNodes`, `state.children.set`, `state.children.get`.

<a id="symbol-loadDescendantTodos"></a>

## loadDescendantTodos

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadDescendantTodos(folder)
```

Перечитывает SQLite-сводку вложенных задач текущего заказа.

Использует `/api/order-todos`.

Непосредственные вызовы: `hasDescendantTodos`, `request`, `apiUrl`, `renderDescendantTodos`.

Прямые присваивания полям/свойствам: `folder.descendantTodoLoading`, `folder.descendantTodos`, `folder.descendantTodoError`.

<a id="symbol-loadFileComment"></a>

## loadFileComment

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadFileComment(path, version)
```

Читает комментарий файла и сохраняет его проверочную версию.

Использует `/api/invoice`, `/api/file-comment`.

Непосредственные вызовы: `state.folder?.files.find`, `$`, `renderFileComment`, `request`, `apiUrl`, `Error`, `Object.assign`, `updateFileCommentCaption`.

Прямые присваивания полям/свойствам: `state.fileComment`, `$("fileCommentText").value`, `comment.loading`, `comment.error`.

<a id="symbol-loadFileTrash"></a>

## loadFileTrash

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadFileTrash()
```

Загружает сеансы корзины файлов и событий.

Использует `/api/event-trash-list`, `/api/files-trash-list`.

Непосредственные вызовы: `request`, `(data.events || []).map((session) => '<section class="file-trash-session"><strong>Событие · ' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + '</strong><p>' + escapeHtml(session.path) +
    '</p>' + (session.pending ? '<p>Операция прервана. Доступно восстановление.</p>' : '') + '<button class="secondary-button" data-restore-event="' + escapeHtml(session.session) + '">Восстановить событие</button></section>').join`, `(data.events || []).map`, `$`, `data.sessions.map((session) => '<section class="file-trash-session"><strong>' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + ' · файлов: ' + session.count + '</strong><p>' + escapeHtml(session.folder) +
    '</p><ul class="file-operation-list">' + session.files.map((path) => '<li>' + escapeHtml(path) + '</li>').join("") + '</ul><button class="secondary-button" data-restore-session="' + session.session + '">Восстановить</button></section>').join`, `data.sessions.map`.

Прямые присваивания полям/свойствам: `$("fileTrashList").innerHTML`, `$("fileTrashWarning").hidden`, `$("fileTrashWarning").textContent`.

<a id="symbol-loadOrderFiles"></a>

## loadOrderFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadOrderFiles(path, navigation)
```

Запрашивает доступный перечень вложений выбранного заказа.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `$`, `fetch`, `folderUrl`, `response.json`, `Error`, `Object.assign`, `renderFolder`.

Прямые присваивания полям/свойствам: `$("loadOrderFilesButton").hidden`, `$("scanState").textContent`, `state.folder.filesLoading`, `state.folder.filesUnavailable`, `state.folder.warnings`.

<a id="symbol-loadOrders"></a>

## loadOrders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadOrders()
```

Перечитывает серверную сводку и обновляет текущие представления заказов.

Использует `/api/orders`, `/api/work-orders`, `/api/object-orders`.

Непосредственные вызовы: `isFolderOrderList`, `isWorkOrderList`, `request`, `renderMoneyOverview`, `apiUrl`, `(object.archived_paths || []).map`, `result.orders.filter`, `renderFavoriteOrders`, `hasOrderList`, `renderOrders`, `renderCardDeadlines`, `[...(result.orders || []), ...(result.favorites || [])].find`, `renderOrderCardLinks`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.calendarPlansError`, `state.objectOrders`, `state.objectOrdersError`, `state.workOrderGroups`, `state.workArchivedOrders`, `state.workArchivedPaths`, `state.orders`, `state.calendarSupplierOrders`, `state.calendarEvents`, `state.calendarInvoicePlans`, `state.calendarPlansLoaded`, `state.deadlineWeekOptions`, `state.favoriteOrders`, `state.unregistrations`, `state.scan`, `state.storage`.

<a id="symbol-loadTree"></a>

## loadTree

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function loadTree()
```

Загружает дерево текущего корня с учётом поиска и области.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `request`, `treeUrl`, `state.nodes.clear`, `state.children.clear`, `registerNodes`, `state.children.set`, `$`, `[...state.expanded].sort`, `loadChildren`, `state.expanded.delete`, `renderTree`.

Прямые присваивания полям/свойствам: `state.tree`, `state.groups`, `state.auxiliary`, `$("rootLabel").textContent`, `$("rootLabel").title`.

<a id="symbol-mountOrderList"></a>

## mountOrderList

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function mountOrderList()
```

Перемещает общий DOM списка в место текущего представления.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `isObjectOrderList`, `$`, `isWorkOrderList`, `["title", "folder_date"].includes`, `workspace.classList.toggle`, `workspace.querySelector`, `workspace.querySelector('[data-sort="status"]').closest`, `deadlineHeader.after`, `workspace.querySelectorAll("thead th").forEach`, `workspace.querySelectorAll`, `deadlineHeader.before`, `document.querySelector`, `pane.classList.toggle`, `pane.querySelector`, `heading.append`, `heading.firstElementChild.append`, `toolbarSlot.append`, `syncSlot.append`, `window.ManagerInbox?.load`, `$("objectOrdersSlot").append`, `$("workOrdersSlot").append`, `$("folderView").before`, `hasOrderList`, `renderWorkArchive`, `renderHomeCalendar`, `workspace.setAttribute`.

Прямые присваивания полям/свойствам: `state.orderSort`, `state.orderDirection`, `$("orderDateSort").dataset.sort`, `$("orderDateSort").textContent`, `$("orderRelatedHeading").hidden`, `$("supplierStatusHeading").hidden`, `workspace.querySelector('[data-sort="status"]').hidden`, `workspace.querySelector("caption").textContent`, `$("orderSearch").placeholder`, `$("homeToolbarSlot").hidden`, `$("homeSyncSlot").hidden`, `$("homeCalendar").hidden`, `$("inboxPanel").hidden`, `$("objectOrdersSection").hidden`, `workspace.hidden`, `$("syncOrdersButton").hidden`, `state.orderListScope`, `state.orderQuery`, `$("orderSearch").value`.

<a id="symbol-moveCalendarEvent"></a>

## moveCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function moveCalendarEvent(days, targetPeriod = null)
```

Сохраняет перенос события, включая смену привязки свободного события день/неделя.

targetPeriod передаёт только свободной записи; остальные виды используют прежние сдвиги.

Непосредственные вызовы: `state.calendarMoving.has`, `orderRowSaving`, `closeCalendarEventMenu`, `state.calendarMoving.add`, `request`, `applyCalendarInvoicePlan`, `applyFreeCalendarEvent`, `applyOrderRecord`, `Date`, `target.setUTCDate`, `target.getUTCDate`, `notify`, `target.toLocaleDateString`, `loadOrders`, `state.calendarMoving.delete`, `renderOrders`, `($("calendarWeeks").querySelector('[' + (menu.free ? 'data-calendar-free' : 'data-invoice-plan') + '="' + menu.id + '"]') || $("calendarViewport")).focus`, `$("calendarWeeks").querySelector`, `$`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-navigate"></a>

## navigate

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function navigate(path, { history = true } = {})
```

Загружает выбранную папку и применяет соответствующий интерфейс.

Использует `/api/order`, `/api/todos-refresh`.

Непосредственные вызовы: `closeCalendarTodoPreview`, `$`, `$("orderTodoDialog").close`, `closePreview`, `saveCurrentPrintTask`, `saveCurrentStatus`, `state.folderRequest?.abort`, `AbortController`, `document.querySelector(".content-pane").setAttribute`, `document.querySelector`, `request`, `apiUrl`, `path.split`, `parts.at`, `parts.map`, `fetch`, `folderUrl`, `response.json`, `Error`, `Boolean`, `$("homeButton").removeAttribute`, `(data.objectOrders?.archived_paths || []).map`, `state.selectedFiles.clear`, `window.history.pushState`, `encodeURIComponent`, `renderTree`, `renderFolder`, `document.dispatchEvent`, `Event`, `run`, `revealPath(data.path, navigation).catch`, `revealPath`, `notify`.

Прямые присваивания полям/свойствам: `state.navigation`, `state.folderRequest`, `$("scanState").textContent`, `data.service`, `state.view`, `$("folderView").hidden`, `$("ordersWorkspace").hidden`, `$("openFolderButton").hidden`, `state.folder`, `state.objectOrders`, `state.objectOrdersError`, `state.workOrderGroups`, `state.workArchivedOrders`, `state.workArchivedPaths`, `state.deadlineWeekOptions`, `$("fileTrashState").textContent`, `state.imageReport`, `state.printTask`, `$("frezaTaskSearch").value`, `$("frezaLegacyFolders").open`, `state.selected`, `state.fileType`, `state.fileQuery`, `state.limit`, `state.dirty`, `document.querySelector(".content-pane").scrollTop`, `$("notice").textContent`, `$("notice").hidden`.

<a id="symbol-newPrintTask"></a>

## newPrintTask

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function newPrintTask()
```

Создаёт новый черновик задания печати выбранного типа.

Использует `saveCurrentPrintTask`, `showPrintTask`, `URL`.

Непосредственные вызовы: `saveCurrentPrintTask`, `showPrintTask`, `URL`, `url.searchParams.delete`, `window.history.replaceState`, `$("printTitle").focus`, `$`.

<a id="symbol-normalize"></a>

## normalize

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const normalize = (value) =>
```

Нормализует строку для поиска и сравнения без учёта регистра.

Использует `String(value).normalize("NFC").toLocaleLowerCase`, `String(value).normalize`, `String`.

Непосредственные вызовы: `String(value).normalize("NFC").toLocaleLowerCase`, `String(value).normalize`, `String`.

<a id="symbol-notify"></a>

## notify

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function notify(message, error = false, action = null)
```

Показывает сообщение пользователю и предусмотренное действие отмены.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `clearTimeout`, `$`, `document.createElement`, `button.addEventListener`, `$("toast").append`, `$("toast").classList.toggle`, `setTimeout`.

Прямые присваивания полям/свойствам: `$("toast").textContent`, `button.type`, `button.textContent`, `$("toast").hidden`.

<a id="symbol-openCalendarEvent"></a>

## openCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openCalendarEvent(slot)
```

Открывает редактор названия события и необязательного комментария без заказа.

Запоминает оба исходных поля для защиты черновика; комментарий заказа не редактирует.

Непосредственные вызовы: `closeCalendarEventMenu`, `state.calendarEvents.find`, `findListOrder`, `state.calendarMoving.has`, `orderRowSaving`, `calendarEventEntries`, `notify`, `Boolean`, `order.calendar_inactive?.[period]?.includes`, `order.calendar_completed?.[period]?.includes`, `order.calendar_trip?.[period]?.includes`, `order.calendar_watch_todos?.[period]?.includes`, `freeCalendarIdentity`, `$`, `(order.work_supplier ? [order.title, order.work_supplier] : [order.title, order.client, order.object]).filter(Boolean).join`, `(order.work_supplier ? [order.title, order.work_supplier] : [order.title, order.client, order.object]).filter`, `Date`, `Intl.DateTimeFormat`, `end.setUTCDate`, `end.getUTCDate`, `format.format`, `renderCalendarEventControls`, `$("calendarEventDialog").showModal`, `$("calendarEventText").focus`.

Прямые присваивания полям/свойствам: `state.calendarEvent`, `$("calendarEventTitle").textContent`, `$("calendarEventOrder").textContent`, `$("calendarEventDate").textContent`, `$("calendarEventText").value`, `$("calendarEventComment").value`, `$("calendarEventState").textContent`.

<a id="symbol-openCalendarEventMenu"></a>

## openCalendarEventMenu

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openCalendarEventMenu(slot, x, y)
```

Открывает контекстное меню с действиями для точного вида события.

Дневным показывает следующие семь дат; свободной недельной — пн–вс своей недели с переносом в день.

Непосредственные вызовы: `closeCalendarTodoPreview`, `state.calendarInvoicePlans.find`, `state.calendarEvents.find`, `findListOrder`, `slot.getAttribute`, `calendarEventEntries`, `state.calendarMoving.has`, `orderRowSaving`, `[0, 1].includes`, `notify`, `closeCalendarEventMenu`, `Boolean`, `order.calendar_inactive?.[period]?.includes`, `order.calendar_completed?.[period]?.includes`, `order.calendar_trip?.[period]?.includes`, `order.calendar_watch_todos?.[period]?.includes`, `$`, `Date`, `start.setUTCDate`, `start.getUTCDate`, `start.getUTCDay`, `end.setUTCDate`, `end.getUTCDate`, `start.toLocaleDateString`, `end.toLocaleDateString`, `$("calendarEventToWeek").setAttribute`, `$("calendarEventNextDays").setAttribute`, `$("calendarEventNextDays").querySelectorAll("[data-calendar-move]").forEach`, `$("calendarEventNextDays").querySelectorAll`, `$("calendarEventInactive").setAttribute`, `String`, `$("calendarEventCompleted").setAttribute`, `$("calendarEventTrip").setAttribute`, `$("calendarEventWatchTodos").setAttribute`, `["incoming", "outgoing"].includes`, `$("calendarEventCarryover").setAttribute`, `$("calendarEventNotified").setAttribute`, `menu.querySelectorAll("[data-calendar-color]").forEach`, `menu.querySelectorAll`, `menu.getBoundingClientRect`, `Math.max`, `Math.min`, `[...menu.querySelectorAll("button")].find((button) => button.getClientRects().length).focus`, `[...menu.querySelectorAll("button")].find`.

Прямые присваивания полям/свойствам: `state.calendarMenu`, `$("calendarEventMenuName").textContent`, `$("calendarEventDayMoves").hidden`, `$("calendarEventToWeek").hidden`, `$("calendarEventToWeek").title`, `$("calendarEventNextDays").hidden`, `$("calendarEventMoveDivider").hidden`, `$("calendarEventWatchTodos").hidden`, `$("calendarEventWatchTodos").disabled`, `$("calendarEventCarryover").hidden`, `$("calendarEventCarryover").disabled`, `$("calendarEventNotified").hidden`, `$("calendarEventNotified").disabled`, `$("calendarEventDelete").hidden`, `$("calendarEventColors").hidden`, `menu.hidden`, `menu.style.left`, `menu.style.top`.

<a id="symbol-openCalendarTodoPreview"></a>

## openCalendarTodoPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openCalendarTodoPreview(anchor, pinned = false)
```

Открывает или закрепляет общее окно задач либо комментария события.

Значок и Alt+↓ закрепляют окно; наведение сохраняет прежние задержки и подавление после Escape.

Непосредственные вызовы: `cancelCalendarTodoPreviewSwitch`, `clearTimeout`, `closeCalendarTodoPreview`, `$`, `anchor.setAttribute`, `renderCalendarTodoPreview`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.anchor`, `calendarTodoPreview.markup`, `$("calendarTodoPreviewBody").scrollTop`, `calendarTodoPreview.pinned`, `$("calendarTodoPreview").hidden`.

<a id="symbol-openCreateEventFolder"></a>

## openCreateEventFolder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openCreateEventFolder()
```

Открывает форму создания или переименования события.

Использует `/api/event-folders`.

Непосредственные вызовы: `request`, `apiUrl`, `$`, `renderEventProposal`, `$("createEventFolderDialog").showModal`, `$("newEventTitle").focus`.

Прямые присваивания полям/свойствам: `state.eventPlan`, `$("newEventParent").textContent`, `$("newEventTitle").value`, `$("eventFolderError").hidden`.

<a id="symbol-openCreateObject"></a>

## openCreateObject

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openCreateObject()
```

Открывает форму создания объекта в выбранном клиенте.

Использует `$`, `$("createObjectFolderDialog").showModal`, `$("newObjectTitle").focus`.

Непосредственные вызовы: `$`, `$("createObjectFolderDialog").showModal`, `$("newObjectTitle").focus`.

Прямые присваивания полям/свойствам: `state.newObjectParent`, `$("newObjectParent").textContent`, `$("newObjectTitle").value`, `$("newObjectError").hidden`.

<a id="symbol-openCreateOrderFolder"></a>

## openCreateOrderFolder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openCreateOrderFolder()
```

Открывает форму создания нового заказа в объекте.

Использует `["supplier_root", "work_section"].includes`, `$`, `Object.fromEntries`.

Непосредственные вызовы: `["supplier_root", "work_section"].includes`, `$`, `Object.fromEntries`, `new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date()).map`, `new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts`, `Intl.DateTimeFormat`, `Date`, `renderNewOrderName`, `$("createOrderFolderDialog").showModal`, `$("newOrderTitle").focus`.

Прямые присваивания полям/свойствам: `state.newOrderParent`, `$("newOrderDateLabel").textContent`, `$("newOrderTitleLabel").textContent`, `$("createOrderFolderTitle").textContent`, `$("submitCreateOrderFolder").textContent`, `$("newOrderParentLabel").textContent`, `$("newOrderTitle").placeholder`, `$("newOrderDate").value`, `$("newOrderTitle").value`, `$("newOrderParent").textContent`, `$("newOrderError").hidden`.

<a id="symbol-openFileTrash"></a>

## openFileTrash

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openFileTrash(eventsOnly = false)
```

Открывает окно корзины и загружает доступное восстановление.

Использует `$`, `loadFileTrash`, `$("fileTrashDialog").showModal`.

Непосредственные вызовы: `$`, `loadFileTrash`, `$("fileTrashDialog").showModal`.

Прямые присваивания полям/свойствам: `state.trashEventsOnly`, `$("fileTrashTitle").textContent`, `$("fileTrashDialogState").textContent`.

<a id="symbol-openFolderRename"></a>

## openFolderRename

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openFolderRename()
```

Открывает форму переименования выбранной папки.

Использует `/api/folder-rename`.

Непосредственные вызовы: `saveCurrentPrintTask`, `saveCurrentStatus`, `request`, `apiUrl`, `$`, `renderFolderRename`, `$("renameFolderDialog").showModal`, `$("renameFolderName").focus`, `$("renameFolderName").select`.

Прямые присваивания полям/свойствам: `state.folderRename`, `$("renameFolderSource").textContent`, `$("renameFolderName").value`, `$("renameFolderError").hidden`.

<a id="symbol-openLocation"></a>

## openLocation

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openLocation()
```

Открывает сохранённое местоположение заказа в дереве.

Использует `URLSearchParams`, `params.has`, `navigate`.

Непосредственные вызовы: `URLSearchParams`, `params.has`, `navigate`, `params.get`, `showOrders`.

<a id="symbol-openNative"></a>

## openNative

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openNative(path, reveal = false)
```

Просит сервер открыть проверенную папку или документ на Mac.

Использует `/api/open`.

Непосредственные вызовы: `request`.

<a id="symbol-openObjectYears"></a>

## openObjectYears

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openObjectYears()
```

Открывает предварительный план группировки заказов объекта по годам.

Использует `/api/object-years`.

Непосредственные вызовы: `saveCurrentStatus`, `request`, `apiUrl`, `$`, `plan.mappings.map(pair=>'<div class="year-group-item"><strong>'+escapeHtml(pair.source.split('/').pop())+'</strong><span>→ '+escapeHtml(pair.year)+'/</span></div>').join`, `plan.mappings.map`, `plan.created_years.map(path=>'<p>Создать папку '+escapeHtml(path.split('/').pop())+'</p>').join`, `plan.created_years.map`, `plan.skipped.join`, `plan.conflicts.join`, `Boolean`, `$("objectYearsDialog").showModal`.

Прямые присваивания полям/свойствам: `state.objectYears`, `$("objectYearsParent").textContent`, `$("objectYearsPlan").innerHTML`, `$("objectYearsSkipped").hidden`, `$("objectYearsSkipped").textContent`, `$("objectYearsError").hidden`, `$("objectYearsError").textContent`, `$("submitObjectYears").disabled`, `$("submitObjectYears").textContent`.

<a id="symbol-openOrderLinks"></a>

## openOrderLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openOrderLinks(path)
```

Открывает окно связей выбранного заказа объекта.

Использует `isObjectOrderList`, `findListOrder`, `orderRowSaving`.

Непосредственные вызовы: `isObjectOrderList`, `findListOrder`, `orderRowSaving`, `$`, `$("orderLinksDialog").showModal`, `$("orderLinksSearch").focus`, `refreshOrderLinks`.

Прямые присваивания полям/свойствам: `state.orderLinks`, `$("orderLinksSearch").value`, `$("orderLinksOptions").scrollTop`.

<a id="symbol-openOrderTodos"></a>

## openOrderTodos

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function openOrderTodos(path, kind = "todos")
```

Открывает сводку задач или закупок выбранной строки.

Использует `findListOrder`, `$("orderTodoBody").replaceChildren`, `$`.

Непосредственные вызовы: `findListOrder`, `$("orderTodoBody").replaceChildren`, `$`, `$("orderTodoDialog").showModal`, `renderOrderTodoDialog`.

Прямые присваивания полям/свойствам: `state.orderTodoPath`, `state.orderTodoKind`, `state.orderTodoMarkup`, `$("orderTodoBody").scrollTop`.

<a id="symbol-openPrintTask"></a>

## openPrintTask

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openPrintTask(path)
```

Открывает выбранное задание печати в общем редакторе.

Использует `/api/print-task`.

Непосредственные вызовы: `saveCurrentPrintTask`, `$`, `request`, `apiUrl`, `showPrintTask`, `URL`, `url.searchParams.set`, `window.history.replaceState`.

Прямые присваивания полям/свойствам: `$("printEditorForm").hidden`, `$("printEditorEmpty").hidden`, `$("printEditorEmpty").textContent`.

<a id="symbol-openRelocatedFolder"></a>

## openRelocatedFolder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openRelocatedFolder(result)
```

Обновляет дерево, адрес страницы и общую сводку после перемещения папки.

Сохраняет раскрытые ветки и открывает результат по новому пути.

Непосредственные вызовы: `Set`, `[...state.expanded].map`, `navigate`, `Error`, `window.history.replaceState`, `encodeURIComponent`, `reloadClientTrees`, `loadOrders`.

Прямые присваивания полям/свойствам: `state.expanded`.

<a id="symbol-openRelocatedFolder.moved"></a>

## openRelocatedFolder.moved

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const moved = (path) =>
```

Обновляет путь элемента интерфейса после подтверждённого переноса папок.

Использует `path.startsWith`, `path.slice`.

Непосредственные вызовы: `path.startsWith`, `path.slice`.

<a id="symbol-openSketch"></a>

## openSketch

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function openSketch(path, key)
```

Запрашивает открытие исходного CDR на серверном Mac.

Использует `/api/sketch-open`.

Непосредственные вызовы: `folder?.sketches?.find`, `renderSketches`, `request`, `notify`.

Прямые присваивания полям/свойствам: `item.opening`.

<a id="symbol-orderDeadlineRange"></a>

## orderDeadlineRange

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderDeadlineRange(weeks)
```

Вычисляет отображаемый диапазон выбранных недель заказа.

Использует `[...weeks].sort`, `Date`, `sorted.at`.

Непосредственные вызовы: `[...weeks].sort`, `Date`, `sorted.at`, `end.setUTCDate`, `end.getUTCDate`, `sorted[0].slice`, `String(end.getUTCDate()).padStart`, `String`, `String(end.getUTCMonth() + 1).padStart`, `end.getUTCMonth`.

<a id="symbol-orderGroupCollapsed"></a>

## orderGroupCollapsed

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderGroupCollapsed(scope, group)
```

Читает сохранённое состояние сворачивания группы.

Использует `JSON.stringify`, `state.collapsedOrderGroups.has`, `localStorage.getItem`.

Непосредственные вызовы: `JSON.stringify`, `state.collapsedOrderGroups.has`, `localStorage.getItem`, `state.collapsedOrderGroups.set`, `state.collapsedOrderGroups.get`.

<a id="symbol-orderGroupScope"></a>

## orderGroupScope

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderGroupScope()
```

Вычисляет ключ сохранённого сворачивания групп текущего списка.

Использует `isFolderOrderList`, `isWorkOrderList`, `state.folder.path.normalize`.

Непосредственные вызовы: `isFolderOrderList`, `isWorkOrderList`, `state.folder.path.normalize`.

<a id="symbol-orderListDeadlineOptions"></a>

## orderListDeadlineOptions

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderListDeadlineOptions(orders)
```

Выбирает ограниченный набор недель для строки списка.

Использует `Set`, `state.deadlineWeekOptions.map`, `starts.add`.

Непосредственные вызовы: `Set`, `state.deadlineWeekOptions.map`, `starts.add`, `[...starts].sort().map`, `[...starts].sort`.

<a id="symbol-orderListGroups"></a>

## orderListGroups

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderListGroups()
```

Распределяет строки текущего списка по группам статусов.

Использует `isObjectOrderList`, `productionStatusGroups().map`, `productionStatusGroups`.

Непосредственные вызовы: `isObjectOrderList`, `productionStatusGroups().map`, `productionStatusGroups`, `Object.keys(statusLabels).filter`, `Object.keys`, `groups.push`, `[...statuses.map((status) => statusLabels[status]), "Не добавлены"].join`, `statuses.map`.

<a id="symbol-orderListRows"></a>

## orderListRows

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderListRows()
```

Возвращает строки текущего общего, объектного или производственного списка.

Использует `(isFolderOrderList() ? state.objectOrders : state.orders).filter`, `isFolderOrderList`.

Непосредственные вызовы: `(isFolderOrderList() ? state.objectOrders : state.orders).filter`, `isFolderOrderList`.

<a id="symbol-orderPurchaseSummary"></a>

## orderPurchaseSummary

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderPurchaseSummary(order)
```

Собирает сводку или текст закупок строки заказа.

Использует `(order.purchase_items || []).filter`.

Непосредственные вызовы: `(order.purchase_items || []).filter`.

<a id="symbol-orderPurchaseText"></a>

## orderPurchaseText

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderPurchaseText(order)
```

Собирает сводку или текст закупок строки заказа.

Использует `(orderPurchaseSummary(order).items || []).map`, `orderPurchaseSummary`.

Непосредственные вызовы: `(orderPurchaseSummary(order).items || []).map((item) => [item.text, ...(item.suppliers || [])].join(" ")).join`, `(orderPurchaseSummary(order).items || []).map`, `orderPurchaseSummary`.

<a id="symbol-orderRowSaving"></a>

## orderRowSaving

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderRowSaving(path)
```

Проверяет наличие незавершённой записи для строки заказа.

Использует `state.markerSaving.has`, `state.favoriteSaving.has`, `state.orderStatusSaving.has`.

Непосредственные вызовы: `state.markerSaving.has`, `state.favoriteSaving.has`, `state.orderStatusSaving.has`, `state.deadlineSaving.has`, `state.calendarMoving.has`.

<a id="symbol-orderShownOnMain"></a>

## orderShownOnMain

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderShownOnMain(order)
```

Проверяет включение заказа в текущую главную таблицу.

Использует `["cancelled", "done"].includes`.

Непосредственные вызовы: `["cancelled", "done"].includes`.

<a id="symbol-orderTodoSummary"></a>

## orderTodoSummary

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderTodoSummary(order)
```

Собирает текст или сводные данные задач строки заказа.

Использует `groups.reduce`.

Непосредственные вызовы: `groups.reduce`.

<a id="symbol-orderTodoText"></a>

## orderTodoText

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function orderTodoText(order)
```

Собирает текст или сводные данные задач строки заказа.

Использует `(order.todo_groups || []).map`.

Непосредственные вызовы: `(order.todo_groups || []).map((group) => [group.label, ...(group.items || []).map((item) => item.text)].join(" ")).join`, `(order.todo_groups || []).map`.

<a id="symbol-positionCalendarTodoPreview"></a>

## positionCalendarTodoPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function positionCalendarTodoPreview()
```

Размещает окно задач или комментария вплотную к границе события.

Использует `$`, `anchor.getBoundingClientRect`, `preview.getBoundingClientRect`.

Непосредственные вызовы: `$`, `anchor.getBoundingClientRect`, `preview.getBoundingClientRect`, `Math.max`, `Math.min`.

Прямые присваивания полям/свойствам: `preview.style.left`, `preview.style.top`.

<a id="symbol-previewUnavailable"></a>

## previewUnavailable

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function previewUnavailable(message)
```

Показывает ошибку или недоступность превью без замены исходника.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `document.createElement`, `$`, `button.addEventListener`, `wrapper.append`, `$("previewBody").replaceChildren`.

Прямые присваивания полям/свойствам: `wrapper.className`, `label.textContent`, `text.textContent`, `button.className`, `button.textContent`, `button.href`.

<a id="symbol-printCountLabel"></a>

## printCountLabel

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const printCountLabel = (count) =>
```

Выбирает русскую подпись количества заданий печати.

Использует `new Intl.PluralRules("ru").select`, `Intl.PluralRules`.

Непосредственные вызовы: `new Intl.PluralRules("ru").select`, `Intl.PluralRules`.

<a id="symbol-printFiles"></a>

## printFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function printFiles()
```

Выбирает поддерживаемые задания печати из открытой папки.

Использует `normalize`, `state.printQuery.trim`.

Непосредственные вызовы: `normalize`, `state.printQuery.trim`, `state.folder.files.filter((file) => !needle || normalize(file.name + " " + (file.title || "") + " " + (file.description || "") + " " + file.folder).includes(needle))
    .sort`, `state.folder.files.filter`.

<a id="symbol-productionStatusGroups"></a>

## productionStatusGroups

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function productionStatusGroups()
```

Возвращает согласованные группы производственных статусов.

Использует `orderStatusGroups.map`.

Непосредственные вызовы: `orderStatusGroups.map`.

<a id="symbol-purchaseSupplierButtons"></a>

## purchaseSupplierButtons

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function purchaseSupplierButtons(item)
```

Строит переключатели назначений поставщиков одной закупки.

Использует `(state.purchaseSuppliers || []).map`, `(item.suppliers || []).filter`.

Непосредственные вызовы: `(state.purchaseSuppliers || []).map`, `(item.suppliers || []).filter`, `names.map(name => {
    const selected = (item.suppliers || []).includes(name), inactive = !available.includes(name);
    const label = inactive ? "Снять назначение " + name + " · поставщик без звезды или недоступен" : "Отметить поставщика " + name;
    return '<button type="button" data-purchase-supplier="' + escapeHtml(name) + '" aria-pressed="' + selected + '" title="' + escapeHtml(label) + '"' +
      (inactive ? ' class="purchase-supplier-retained"' : '') + '>' + escapeHtml(name) + (inactive ? ' ×' : '') + '</button>';
  }).join`, `names.map`.

<a id="symbol-refreshCalendarEvent"></a>

## refreshCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshCalendarEvent()
```

Перечитывает источник события при конфликте, сохраняя черновик формы.

Использует `/api/calendar-event`, `/api/order`.

Непосредственные вызовы: `renderCalendarEventControls`, `request`, `encodeURIComponent`, `Error`, `Boolean`, `applyFreeCalendarEvent`, `apiUrl`, `calendarEventEntries`, `order.calendar_inactive?.[edit.period]?.includes`, `order.calendar_completed?.[edit.period]?.includes`, `order.calendar_trip?.[edit.period]?.includes`, `order.calendar_watch_todos?.[edit.period]?.includes`, `applyOrderRecord`, `$`, `renderOrders`.

Прямые присваивания полям/свойствам: `edit.saving`, `edit.revision`, `edit.previous`, `edit.previousComment`, `edit.inactive`, `edit.completed`, `edit.trip`, `edit.color`, `edit.conflict`, `edit.watch_todos`, `$("calendarEventState").textContent`.

<a id="symbol-refreshEventProposal"></a>

## refreshEventProposal

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshEventProposal()
```

Перепроверяет предложение события без замены пользовательского ввода.

Использует `/api/event-folders`.

Непосредственные вызовы: `Map`, `[...$("eventRenameList").querySelectorAll("input")].map`, `$("eventRenameList").querySelectorAll`, `$`, `request`, `apiUrl`, `renderEventProposal`.

Прямые присваивания полям/свойствам: `state.eventPlan`, `$("eventFolderError").hidden`.

<a id="symbol-refreshEventRelevance"></a>

## refreshEventRelevance

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshEventRelevance(folder)
```

Перечитывает актуальность событий из SQLite без повторного чтения файлов.

Использует `/api/event-relevance`.

Непосредственные вызовы: `request`, `apiUrl`, `JSON.stringify`, `renderSubfolders`.

Прямые присваивания полям/свойствам: `item.eventRelevance`.

<a id="symbol-refreshOrderLinks"></a>

## refreshOrderLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshOrderLinks()
```

Перечитывает подтверждённую группу связей из базы.

Использует `/api/order-links`.

Непосредственные вызовы: `renderOrderLinks`, `request`, `apiUrl`, `applyOrderRecord`, `hasOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `edit.loading`, `edit.error`, `edit.data`, `edit.conflict`.

<a id="symbol-refreshPurchaseSuppliers"></a>

## refreshPurchaseSuppliers

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshPurchaseSuppliers()
```

Загружает доступные избранные разделы поставщиков.

Использует `/api/purchase-suppliers`.

Непосредственные вызовы: `isWorkOrderPath`, `request`, `updatePurchaseSupplierButtons`, `Number.isSafeInteger`, `[...$("subfolders").querySelectorAll("[data-path]")].find`, `$("subfolders").querySelectorAll`, `$`, `button?.querySelector`, `button.setAttribute`.

Прямые присваивания полям/свойствам: `state.purchaseSupplierRequest`, `state.purchaseSuppliers`, `item.supplierPurchaseCount`, `badge.textContent`, `button.title`.

<a id="symbol-refreshSketchRelevance"></a>

## refreshSketchRelevance

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshSketchRelevance(folder)
```

Перечитывает сохранённую актуальность эскизов из базы.

Использует `/api/sketch-relevance`.

Непосредственные вызовы: `request`, `apiUrl`, `Object.entries`, `folder.sketchSavingFolders?.has`, `applySketchGroup`, `renderSketches`.

<a id="symbol-refreshSupplierFavorites"></a>

## refreshSupplierFavorites

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshSupplierFavorites(folder)
```

Перечитывает сохранённые звёзды и порядок разделов производства.

Использует `/api/work-supplier-favorites`.

Непосредственные вызовы: `request`, `apiUrl`, `String(item.path).normalize`, `String`, `String(item.supplierFavorite?.revision || "").split`, `String(saved?.revision || "").split`, `Number`, `state.supplierFavoriteSaving.has`, `JSON.stringify`, `renderSubfolders`.

Прямые присваивания полям/свойствам: `item.supplierFavorite`.

<a id="symbol-refreshThumbnails"></a>

## refreshThumbnails

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshThumbnails()
```

Обновляет доступность миниатюр для уже показанных файлов.

Использует `/api/thumbnails`, `/api/thumbnail`.

Непосредственные вызовы: `document.querySelectorAll`, `images.slice`, `request`, `batch.map((image) => image.dataset.thumbnailPath).filter`, `batch.map`, `batch.map((image) => image.dataset.thumbnailFolder).filter`, `Map`, `result.items.map`, `items.get`, `image.closest`, `apiUrl`, `container?.classList.add`.

Прямые присваивания полям/свойствам: `image.dataset.thumbnailKey`, `image.loading`, `image.hidden`, `image.onload`, `image.onerror`, `image.src`.

<a id="symbol-refreshUploadedFiles"></a>

## refreshUploadedFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function refreshUploadedFiles(job)
```

Перечитывает содержимое папки после успешных загрузок.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `request`, `folderUrl`, `Math.max`, `job.results.filter`, `renderFiles`, `$`, `formatSize`.

Прямые присваивания полям/свойствам: `folder[key]`, `state.limit`, `$("folderSummary").textContent`.

<a id="symbol-registerNodes"></a>

## registerNodes

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function registerNodes(nodes)
```

Запоминает узлы дерева для последующих раскрытий и навигации.

Использует `state.nodes.set`, `registerNodes`.

Непосредственные вызовы: `state.nodes.set`, `registerNodes`.

<a id="symbol-reloadClientTrees"></a>

## reloadClientTrees

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function reloadClientTrees()
```

Перечитывает деревья клиентов после изменения индекса активности.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `clearTimeout`, `loadTree`, `state.treeQuery.trim`, `request`, `treeUrl`, `registerNodes`, `renderTree`.

Прямые присваивания полям/свойствам: `state.searchTree`.

<a id="symbol-removeCalendarRecord"></a>

## removeCalendarRecord

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function removeCalendarRecord(entry)
```

Удаляет выбранную запись через API её конкретного вида.

Свободные события удаляет на день/неделю, события заказа только на день; предлагает прежнюю отмену.

Непосредственные вызовы: `state.calendarInvoicePlans.find`, `['incoming', 'outgoing'].includes`, `Error`, `state.calendarMoving.has`, `state.calendarMoving.add`, `request`, `applyCalendarDeletion`, `notify`, `state.calendarMoving.delete`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-removeCalendarRecord.run"></a>

## removeCalendarRecord.run

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
run: () =>
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `restoreCalendarDeletion`.

Непосредственные вызовы: `restoreCalendarDeletion`.

<a id="symbol-removeEvent"></a>

## removeEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function removeEvent()
```

Перемещает подтверждённую папку события в корзину.

Использует `/api/event-trash`.

Непосредственные вызовы: `["confirmDeleteEvent", "cancelDeleteEvent"].forEach`, `$`, `request`, `$("deleteEventDialog").close`, `Set`, `[...state.expanded].filter`, `reloadClientTrees`, `navigate`, `loadOrders`, `notify`.

Прямые присваивания полям/свойствам: `state.eventRemoving`, `$("deleteEventError").hidden`, `$("deleteEventError").textContent`, `state.expanded`, `state.dirty`.

<a id="symbol-removeSelectedFiles"></a>

## removeSelectedFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function removeSelectedFiles()
```

Перемещает подтверждённые файлы в корзину менеджера.

Использует `/api/files-trash`.

Непосредственные вызовы: `$`, `request`, `$("deleteFilesDialog").close`, `state.selectedFiles.delete`, `loadOrderFiles`, `$("fileTrashState").classList.toggle`, `Boolean`, `notify`, `renderFileActions`.

Прямые присваивания полям/свойствам: `state.fileRemoving`, `$("confirmDeleteFiles").disabled`, `$("cancelDeleteFiles").disabled`, `$("confirmDeleteFiles").textContent`, `$("fileTrashState").textContent`.

<a id="symbol-renderBrandCalendar"></a>

## renderBrandCalendar

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderBrandCalendar(now = new Date())
```

Показывает текущую московскую ISO-неделю в шапке меню.

Использует прежний расчёт/цвет недели заказа; меняет только свои узлы при смене даты, без запросов.

Непосредственные вызовы: `Object.fromEntries`, `new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now).map`, `new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts`, `Intl.DateTimeFormat`, `$`, `Date`, `start.setUTCDate`, `start.getUTCDate`, `start.getUTCDay`, `deadlineWeekInfo`, `start.toISOString().slice`, `start.toISOString`, `badge.style.setProperty`, `badge.setAttribute`.

Прямые присваивания полям/свойствам: `calendar.dataset.date`, `badge.textContent`, `badge.title`.

<a id="symbol-renderCalendarEventControls"></a>

## renderCalendarEventControls

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderCalendarEventControls()
```

Обновляет доступные действия редактора и поле комментария свободного события.

Блокирует ввод при сохранении; удаление доступно свободным обоих периодов и дневным событиям заказа.

Непосредственные вызовы: `$`, `Boolean`.

Прямые присваивания полям/свойствам: `$("calendarEventText").disabled`, `$("calendarEventCommentField").hidden`, `$("calendarEventComment").disabled`, `$("saveCalendarEvent").disabled`, `$("cancelCalendarEvent").disabled`, `$("refreshCalendarEvent").hidden`, `$("refreshCalendarEvent").disabled`, `$("deleteCalendarEvent").hidden`, `$("deleteCalendarEvent").disabled`.

<a id="symbol-renderCalendarTodoPreview"></a>

## renderCalendarTodoPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderCalendarTodoPreview()
```

Показывает актуальные задачи заказа либо комментарий свободного события.

Комментарий выводит через textContent с переносами строк; опрос сохраняет прокрутку и фокус.

Непосредственные вызовы: `state.calendarEvents.find`, `findListOrder`, `record.comment.trim`, `closeCalendarTodoPreview`, `anchor.getBoundingClientRect`, `$("calendarViewport").getBoundingClientRect`, `$`, `Boolean`, `orderTodoSummary`, `$("closeCalendarTodoPreview").setAttribute`, `renderOrderTodos`, `body.classList.toggle`, `body.setAttribute`, `body.contains`, `([...body.querySelectorAll('[data-order]')].find((link) => link.dataset.order === path) || body).focus`, `[...body.querySelectorAll('[data-order]')].find`, `body.querySelectorAll`, `positionCalendarTodoPreview`.

Прямые присваивания полям/свойствам: `$("calendarTodoPreviewHeading").textContent`, `$("calendarTodoPreviewTitle").textContent`, `$("calendarTodoPreviewCount").hidden`, `$("calendarTodoPreviewCount").textContent`, `$("calendarTodoPreviewFooter").hidden`, `body.textContent`, `body.innerHTML`, `calendarTodoPreview.markup`, `body.scrollTop`.

<a id="symbol-renderCardDeadlines"></a>

## renderCardDeadlines

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderCardDeadlines()
```

Показывает недели срока в карточке с раскрытием прошлых периодов.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `isWorkOrderPath`, `Boolean`, `orderRowSaving`, `Set`, `visible.add`, `Object.keys`, `shiftDeadlineWeek`, `[...visible].sort().map`, `[...visible].sort`, `renderDeadlineMonthLegend`, `renderOrderDeadlines`, `document.activeElement?.hasAttribute`, `$("orderCardDeadlineList").querySelector("[data-order-calendar-compact]")?.focus`, `$("orderCardDeadlineList").querySelector`, `options.at`, `state.deadlineSaving.has`, `renderDeadlineComments`.

Прямые присваивания полям/свойствам: `panel.hidden`, `folder.deadlineVisibleWeeks`, `$("orderCardDeadlineList").innerHTML`, `$("orderCardDeadlineEarlier").disabled`, `$("orderCardDeadlineLater").disabled`, `$("orderCardDeadlineState").textContent`.

<a id="symbol-renderClientActivity"></a>

## renderClientActivity

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderClientActivity()
```

Показывает состояние активности клиента или объекта и действия пользователя.

Использует `folderActivity`, `$`, `Boolean`.

Непосредственные вызовы: `folderActivity`, `$`, `Boolean`, `$("clientActivityCard").setAttribute`, `$("clientActivityState").classList.toggle`.

Прямые присваивания полям/свойствам: `$("folderFooter").hidden`, `$("clientActivityCard").hidden`, `$("activityLabel").textContent`, `$("activityHint").textContent`, `$("clientInactive").checked`, `$("clientInactive").disabled`, `$("clientActivityState").textContent`, `$("clientActivityAcceptFile").hidden`, `$("clientActivityAcceptFile").disabled`.

<a id="symbol-renderCompactOrderLinks"></a>

## renderCompactOrderLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderCompactOrderLinks(order)
```

Показывает компактные ссылки главного на его подчинённые заказы.

Использует `items.map`.

Непосредственные вызовы: `items.map(item => '<li>' + icon('link') +
    (item.available ? '<a href="?path=' + encodeURIComponent(item.path) + '" data-related-card-open="' + escapeHtml(item.path) + '" data-related-card-id="' + escapeHtml(item.id) + '">' + escapeHtml(item.title) + '</a>' :
      '<span class="unavailable">' + escapeHtml(item.title) + '</span>') + '</li>').join`, `items.map`.

<a id="symbol-renderDeadlineComments"></a>

## renderDeadlineComments

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderDeadlineComments(folder)
```

Показывает редакторы общих недельных событий заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `Map`, `$`, `container.replaceChildren`, `Set`, `selected.has`, `drafts.delete`, `Object.keys`, `drafts.keys`, `[...container.children].map`, `weeks.has`, `row.remove`, `[...weeks].sort`, `drafts.get`, `drafts.set`, `deadlineWeekInfo`, `rows.get`, `document.createElement`, `Array.isArray`, `row.classList.toggle`, `row.querySelector`, `input.setAttribute`, `Boolean`, `container.insertBefore`, `drafts.values`, `values.find`, `values.some`.

Прямые присваивания полям/свойствам: `folder.deadlineCommentDrafts`, `container.dataset.scope`, `draft.value`, `draft.saved`, `row.className`, `row.dataset.weekCommentRow`, `row.innerHTML`, `row.title`, `input.value`, `input.title`, `input.disabled`, `input.readOnly`, `$("orderDeadlineCommentsState").textContent`, `$("retryDeadlineComments").hidden`, `$("retryDeadlineComments").disabled`.

<a id="symbol-renderDeadlineMonthLegend"></a>

## renderDeadlineMonthLegend

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderDeadlineMonthLegend(options)
```

Строит легенду месяцев для цветов недель срока.

Использует `Map`, `options.map`.

Непосредственные вызовы: `new Map(options.map((week) => { const info = deadlineWeekInfo(week.start); return [info.monthYear, info]; })).values`, `Map`, `options.map`, `Set`, `months.map`, `months.map((month) =>
    '<span style="--deadline-month-hue:' + month.hue + '" title="' + deadlineMonthNames[month.month] + ' ' + month.year + '">' +
    deadlineMonthNames[month.month] + (years.size > 1 ? ' ' + month.year : '') + '</span>').join`.

<a id="symbol-renderDescendantTodos"></a>

## renderDescendantTodos

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderDescendantTodos()
```

Показывает задачи вложенных папок с переходом к исходному месту.

Использует `$`, `hasDescendantTodos`, `groups.some`.

Непосредственные вызовы: `$`, `hasDescendantTodos`, `groups.some`, `Boolean`, `groups.map((group) => ({ ...group, items: group.items?.filter((item) => folder.showCompletedTodos || !item.done) ?? null }))
    .filter`, `groups.map`, `groups.reduce`, `visible.map(renderOrderTodoGroup).join`, `visible.map`, `orderTodoSummary`.

Прямые присваивания полям/свойствам: `$("descendantTodos").hidden`, `$("descendantCompletedLabel").hidden`, `$("descendantCompleted").checked`, `$("descendantTodoCount").textContent`, `$("descendantTodoList").innerHTML`, `$("descendantTodoList").scrollTop`, `folder.descendantTodoMarkup`, `$("descendantTodoState").textContent`.

<a id="symbol-renderEventProposal"></a>

## renderEventProposal

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderEventProposal(previous = new Map())
```

Показывает проверенное предложение имени и пути события.

Использует `$`, `suggestions.map`.

Непосредственные вызовы: `$`, `suggestions.map((item) => {
    const title = previous.get(item.source) ?? item.title;
    return '<div class="event-rename-row" data-number="' + item.number + '"><p class="event-old-name">' + escapeHtml(item.source) + '</p>' +
      '<label>Название события<input data-event-source="' + escapeHtml(item.source) + '" aria-label="Название для ' + escapeHtml(item.source) + '" type="text" maxlength="240" required value="' + escapeHtml(title) + '" placeholder="Укажите название"></label>' +
      '<p class="new-order-preview">→ <strong>' + escapeHtml(item.number + ' - ' + (title || 'Название события')) + '</strong></p></div>';
  }).join`, `suggestions.map`, `renderNewEventName`.

Прямые присваивания полям/свойствам: `$("eventRenameSection").hidden`, `$("confirmEventRenames").checked`, `$("eventRenameList").innerHTML`.

<a id="symbol-renderExportState"></a>

## renderExportState

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderExportState()
```

Показывает состояние импорта и очереди выпущенных документов.

Использует `$`, `renderPurchaseSaveState`.

Непосредственные вызовы: `$`, `renderPurchaseSaveState`.

Прямые присваивания полям/свойствам: `$("orderExportState").textContent`.

<a id="symbol-renderFavoriteOrders"></a>

## renderFavoriteOrders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderFavoriteOrders()
```

Показывает избранные заказы в панели навигации.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `state.favoriteOrders.filter((order) => order.is_favorite === true && order.supplier_status !== "archived").sort`, `state.favoriteOrders.filter`, `favorites.map((order) => {
    const active = state.view !== "orders" && (state.selected === order.path || state.selected.startsWith(order.path + "/"));
    return '<button type="button" class="favorite-order-button' + (active ? ' active' : '') + '" data-path="' + escapeHtml(order.path) + '" title="' + escapeHtml(order.title + " · " + (order.client || "") + "\n" + order.path) + '"' + (active ? ' aria-current="page"' : '') + '><span class="favorite-order-star" aria-hidden="true">★</span><span class="favorite-order-text"><span class="favorite-order-title">' + escapeHtml(order.title) + '</span>' + (order.client ? '<span class="favorite-order-client">' + escapeHtml(order.client) + '</span>' : '') + '</span></button>';
  }).join`, `favorites.map`, `container.contains`, `[...container.querySelectorAll("[data-path]")].find((button) => button.dataset.path === focusedPath)?.focus`, `[...container.querySelectorAll("[data-path]")].find`, `container.querySelectorAll`.

Прямые присваивания полям/свойствам: `container.innerHTML`, `container.scrollTop`, `container.hidden`.

<a id="symbol-renderFileActions"></a>

## renderFileActions

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderFileActions()
```

Обновляет действия над выбранным набором файлов.

Использует `state.folder.files.filter`, `selected.filter`, `filteredFiles`.

Непосредственные вызовы: `state.folder.files.filter`, `selected.filter`, `filteredFiles`, `visible.filter`, `$`, `Boolean`, `$("fileReportState").classList.toggle`, `state.folder.files.some`.

Прямые присваивания полям/свойствам: `$("selectAllFiles").checked`, `$("selectAllFiles").indeterminate`, `$("selectAllFiles").disabled`, `$("fileSelectionCount").textContent`, `$("clearFileSelection").hidden`, `$("createImageReport").disabled`, `$("deleteSelectedFiles").disabled`, `$("createImageReport").textContent`, `$("fileReportState").textContent`, `$("openImageReport").hidden`.

<a id="symbol-renderFileComment"></a>

## renderFileComment

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderFileComment()
```

Заполняет редактор комментария точного файла.

Использует `Boolean`, `$`, `$("fileCommentState").classList.toggle`.

Непосредственные вызовы: `Boolean`, `$`, `$("fileCommentState").classList.toggle`.

Прямые присваивания полям/свойствам: `$("fileCommentText").disabled`, `$("saveFileComment").disabled`, `$("saveFileComment").textContent`, `$("cancelFileComment").hidden`, `$("cancelFileComment").disabled`, `$("reloadFileComment").hidden`, `$("fileCommentState").textContent`.

<a id="symbol-renderFiles"></a>

## renderFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderFiles()
```

Показывает отфильтрованные файлы и состояние их загрузки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `filteredFiles`, `Set`, `state.folder.files.map`, `available.has`, `state.selectedFiles.delete`, `renderFileActions`, `$`, `Object.entries(typeLabels)
    .filter(([type]) => type === "all" || state.folder.counts[type] > 0)
    .map(([type, label]) => '<button class="file-filter' + (state.fileType === type ? " active" : "") +
      '" data-type="' + type + '" aria-pressed="' + (state.fileType === type) + '">' + label + '<span>' +
      (type === "all" ? state.folder.fileCount : state.folder.counts[type]) + "</span></button>").join`, `Object.entries(typeLabels)
    .filter(([type]) => type === "all" || state.folder.counts[type] > 0)
    .map`, `Object.entries(typeLabels)
    .filter`, `Object.entries`, `icon`, `Map`, `files.slice`, `groups.has`, `groups.set`, `groups.get(key).push`, `groups.get`, `[...groups.entries()].map(([folder, group]) => {
    const path = [state.folder.path, folder].filter(Boolean).join("/");
    return '<section class="file-group">' +
      (state.fileSort === "folders" ? '<button class="file-group-heading" data-path="' + escapeHtml(path) + '">' +
        icon("folder") + "<span>" + escapeHtml(folder || "В выбранной папке") + '</span><small>' + group.length + "</small></button>" : "") +
      '<div class="file-grid">' + group.map((file) => fileCard(file)).join("") + "</div></section>";
  }).join`, `[...groups.entries()].map`, `groups.entries`, `$("files").querySelectorAll("img").forEach`, `$("files").querySelectorAll`, `refreshThumbnails().catch`, `refreshThumbnails`.

Прямые присваивания полям/свойствам: `$("fileCount").textContent`, `$("fileFilters").innerHTML`, `$("files").innerHTML`.

<a id="symbol-renderFolder"></a>

## renderFolder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderFolder(preserveForm = false)
```

Собирает представление открытой папки и доступные её роли блоки интерфейса.

Использует `renderMoneyOverview`, `document.dispatchEvent`, `CustomEvent`.

Непосредственные вызовы: `renderMoneyOverview`, `document.dispatchEvent`, `CustomEvent`, `renderClientActivity`, `Boolean`, `Object.hasOwn`, `isWorkOrderPath`, `hasDescendantTodos`, `$`, `$("orderOverview").classList.toggle`, `folder.breadcrumbs.map((part, index) =>
    (index ? '<span class="breadcrumb-divider">/</span>' : "") +
    '<button data-path="' + escapeHtml(part.path) + '"' + (index === folder.breadcrumbs.length - 1 ? ' aria-current="page"' : "") + ">" +
    escapeHtml(part.name) + "</button>").join`, `folder.breadcrumbs.map`, `renderOrderHeading`, `renderOrderCardLinks`, `printCountLabel`, `folder.directories.filter`, `formatSize`, `foldersAnchor.before`, `renderSubfolders`, `renderSketches`, `renderOrderFileFolders`, `renderDescendantTodos`, `$("statusForm").classList.toggle`, `["supplier_root", "work_section"].includes`, `renderTodos`, `renderPurchases`, `(card[key] / 100).toFixed`, `renderOrderCalculated`, `renderExportState`, `Object.entries(supplierStatusLabels).map(([key, label]) => '<option value="' + key + '">' + label + '</option>').join`, `Object.entries(supplierStatusLabels).map`, `Object.entries`, `resizeOrderNote`, `renderStatus`, `warnings.push`, `warnings.join`, `["events", "subfolders"].includes`, `renderUpload`, `renderPrintList`, `new URLSearchParams(location.search).get`, `URLSearchParams`, `printFiles().find`, `printFiles`, `run`, `renderFiles`, `$("files").replaceChildren`, `renderCardDeadlines`, `mountOrderList`, `isFolderOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `$("orderFinanceOverview").hidden`, `$("purchasePanel").hidden`, `$("orderOverview").hidden`, `$("todoPanel").hidden`, `$("orderTasksColumn").hidden`, `$("breadcrumbs").innerHTML`, `$("clientLabel").textContent`, `$("folderSummary").textContent`, `$("orderDetails").hidden`, `$("folderDetailsTitle").textContent`, `$("statusLabel").hidden`, `$("orderStatusFields").hidden`, `$("supplierStatusLabel").hidden`, `$("supplierStatusLabel").firstChild.textContent`, `$("orderTitleLabel").hidden`, `$("orderTitleLabel").firstChild.textContent`, `$("reconciliationClientLabel").hidden`, `$("financialFields").hidden`, `$("orderNote").placeholder`, `$("removeOrderButton").hidden`, `$("addOrderButton").textContent`, `$("removeOrderButton").textContent`, `$("createObjectFolderButton").hidden`, `$("groupObjectYearsButton").hidden`, `$("createOrderFolderButton").hidden`, `$("createOrderFolderButton").textContent`, `$("createEventFolderButton").hidden`, `$("renameFolderButton").hidden`, `$("moveObjectButton").hidden`, `$("deleteEventButton").hidden`, `$("openEventTrash").hidden`, `folder.todo_items`, `folder.purchase_items`, `$("todoNewText").value`, `$("purchaseNewText").value`, `$("orderDetails").open`, `$("orderTitleInput").value`, `$("reconciliationClient").value`, `$(field).value`, `$("addOrderButton").hidden`, `$("statusSelect").value`, `$("supplierStatusSelect").innerHTML`, `$("supplierStatusSelect").value`, `$("supplierStatusSelect").disabled`, `$("supplierStatusSelect").title`, `$("financialStatusSelect").value`, `$("orderNote").value`, `$("loadOrderFilesButton").hidden`, `$("notice").hidden`, `$("notice").textContent`, `$("fileSearch").value`, `$("filesSection").hidden`, `$("uploadDropZone").hidden`, `$("printWorkspace").hidden`, `state.printQuery`, `$("printTaskSearch").value`, `$("printEditorForm").hidden`, `$("printEditorEmpty").hidden`, `$("printEditorEmpty").textContent`.

<a id="symbol-renderFolderRename"></a>

## renderFolderRename

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderFolderRename()
```

Показывает предварительный результат формы переименования.

Использует `folderParent`, `$`, `$("renameFolderName").value.trim().normalize`.

Непосредственные вызовы: `folderParent`, `$`, `$("renameFolderName").value.trim().normalize`, `$("renameFolderName").value.trim`.

Прямые присваивания полям/свойствам: `$("renameFolderDestination").textContent`.

<a id="symbol-renderHomeCalendar"></a>

## renderHomeCalendar

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderHomeCalendar()
```

Обновляет календарь из текущей SQLite-сводки главной.

Использует `[...state.orders, ...state.calendarSupplierOrders].map`, `HomeCalendar.show`, `orders.sort`.

Непосредственные вызовы: `[...state.orders, ...state.calendarSupplierOrders].map`, `HomeCalendar.show`, `orders.sort`, `renderCalendarTodoPreview`.

<a id="symbol-renderMoneyOverview"></a>

## renderMoneyOverview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderMoneyOverview()
```

Обновляет помесячную сводку из текущих планов платежей.

Использует `MoneyOverview.show`.

Непосредственные вызовы: `MoneyOverview.show`.

<a id="symbol-renderNewEventName"></a>

## renderNewEventName

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderNewEventName()
```

Обновляет предлагаемое имя создаваемой папки по полям формы.

Использует `$`, `$("newEventTitle").value.trim`.

Непосредственные вызовы: `$`, `$("newEventTitle").value.trim`.

Прямые присваивания полям/свойствам: `$("newEventFolderName").textContent`.

<a id="symbol-renderNewOrderName"></a>

## renderNewOrderName

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderNewOrderName()
```

Обновляет предлагаемое имя создаваемой папки по полям формы.

Использует `$`, `$("newOrderTitle").value.trim`.

Непосредственные вызовы: `$`, `$("newOrderTitle").value.trim`.

Прямые присваивания полям/свойствам: `$("newOrderFolderName").textContent`.

<a id="symbol-renderOrderCalculated"></a>

## renderOrderCalculated

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderCalculated()
```

Пересчитывает отображаемые прибыль и остаток из полей редактора.

Использует `read`, `$`, `rubles`.

Непосредственные вызовы: `read`, `$`, `rubles`.

Прямые присваивания полям/свойствам: `$("orderProfit").textContent`, `$("orderDebt").textContent`.

<a id="symbol-renderOrderCalculated.read"></a>

## renderOrderCalculated.read

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const read = (id) =>
```

Читает текущее значение поля локального редактора.

Использует `$(id).value.replace(/[\s\u00a0]/g, "").replace`, `$(id).value.replace`, `$`.

Непосредственные вызовы: `$(id).value.replace(/[\s\u00a0]/g, "").replace`, `$(id).value.replace`, `$`, `/^\d+(\.\d{1,2})?$/.test`, `Math.round`, `Number`.

<a id="symbol-renderOrderCardLinks"></a>

## renderOrderCardLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderCardLinks(order = state.folder?.order)
```

Показывает компактные ссылки главного на его подчинённые заказы.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `renderCompactOrderLinks`, `container.contains`, `[...container.querySelectorAll('[data-related-card-id]')].find(link => link.dataset.relatedCardId === active)?.focus`, `[...container.querySelectorAll('[data-related-card-id]')].find`, `container.querySelectorAll`.

Прямые присваивания полям/свойствам: `state.folder.cardLinksRevision`, `container.hidden`, `container.innerHTML`, `state.cardLinksMarkup`.

<a id="symbol-renderOrderComment"></a>

## renderOrderComment

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderComment(order)
```

Показывает первую строку комментария заказа в таблице.

Использует `String(order.note || "").split(/\r\n?|\n/, 1)[0].trim`, `String(order.note || "").split`, `String`.

Непосредственные вызовы: `String(order.note || "").split(/\r\n?|\n/, 1)[0].trim`, `String(order.note || "").split`, `String`, `escapeHtml`.

<a id="symbol-renderOrderDeadlines"></a>

## renderOrderDeadlines

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderDeadlines(order, { options = state.deadlineWeekOptions, card = false, disabled = false } = {})
```

Строит кнопки недель и диапазон срока в строке заказа.

Использует `Set`, `[...selected].filter`.

Непосредственные вызовы: `Set`, `[...selected].filter`, `Object.entries(order.calendar_week_events || {}).filter(([, comment]) => comment.trim()).sort`, `Object.entries(order.calendar_week_events || {}).filter`, `Object.entries`, `comments.map(([start, comment]) => deadlineWeekInfo(start).number + '-' + comment.trim()).join`, `comments.map`, `[outsideText, preview].filter(Boolean).join`, `[outsideText, preview].filter`, `[unknown ? outsideText : outside.length ? 'Начало выбранных недель: ' + outside.join(', ') : '',
    ...comments.map(([start, comment]) => 'Неделя ' + deadlineWeekInfo(start).number + ' · ' + deadlineWeekDates(start) + ': ' + comment)].filter(Boolean).join`, `[unknown ? outsideText : outside.length ? 'Начало выбранных недель: ' + outside.join(', ') : '',
    ...comments.map(([start, comment]) => 'Неделя ' + deadlineWeekInfo(start).number + ' · ' + deadlineWeekDates(start) + ': ' + comment)].filter`, `outside.join`, `orderDeadlineRange`, `escapeHtml`, `orderRowSaving`, `options.map((option, index) => {
      const week = deadlineWeekInfo(option.start);
      const past = currentWeek && week.start < currentWeek;
      const overdue = selected.has(week.start) && past;
      const travel = week.start >= deadlineTravelPeriod.start && week.start <= deadlineTravelPeriod.end;
      const travelContinues = travel && options[index + 1]?.start === shiftDeadlineWeek(week.start, 1) && options[index + 1].start <= deadlineTravelPeriod.end;
      const comment = order.calendar_week_events?.[week.start] || "";
      const help = (overdue ? "Просрочено · " : "") + week.label + (travel ? "\n" + deadlineTravelPeriod.label : "") + (comment ? "\n" + comment : "");
      const gap = card && previous && shiftDeadlineWeek(previous, 1) !== week.start ? '<span class="deadline-week-gap" title="Между этими неделями есть пропуск">…</span>' : '';
      previous = week.start;
      return gap + '<button type="button" class="deadline-week' + (week.current ? ' current' : '') + (past ? ' past' : '') + (overdue ? ' overdue' : '') + (travel ? ' travel' : '') + (travelContinues ? ' travel-continues' : '') +
      '" style="--deadline-month-hue:' + week.hue +
      '" data-order-deadline="' + escapeHtml(order.path) + '" data-deadline-week="' + week.start +
      '" data-order-id="' + escapeHtml(order.id) + '" data-revision="' + order.revision + '" aria-pressed="' + selected.has(week.start) +
      '" aria-label="' + escapeHtml("Неделя " + week.number + " · " + help) + '" title="' + escapeHtml(help) +
      '"' + (disabled || unknown || order.registered === false || orderRowSaving(order.path) ? ' disabled' : '') + '>' + week.number + '</button>';
    }).join`, `options.map`.

<a id="symbol-renderOrderFavoriteButton"></a>

## renderOrderFavoriteButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderFavoriteButton(order)
```

Строит кнопку избранного текущего заказа.

Использует `escapeHtml`, `Boolean`, `orderRowSaving`.

Непосредственные вызовы: `escapeHtml`, `Boolean`, `orderRowSaving`.

<a id="symbol-renderOrderFileFolders"></a>

## renderOrderFileFolders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderFileFolders()
```

Показывает существующие # cutter, # freza и # docs под эскизами в порядке ответа сервера.

Использует общий просмотрщик и группирует вложенные файлы по относительной папке.

Непосредственные вызовы: `$`, `folders.map((item) => {
    const files = folder.files.filter((file) => file.path.startsWith(item.path + "/"));
    const groups = new Map();
    for (const file of files) {
      if (!groups.has(file.folder)) groups.set(file.folder, []);
      groups.get(file.folder).push(file);
    }
    return '<section class="folder-section" aria-label="' + escapeHtml(item.name) + '">' +
      '<div class="section-heading"><h2>' + escapeHtml(item.name) + '</h2><span>' + files.length + '</span>' +
      '<button type="button" class="secondary-button" data-path="' + escapeHtml(item.path) + '">Открыть папку</button></div>' +
      [...groups.entries()].map(([path, group]) => '<section class="file-group">' +
        (path !== item.path.slice(folder.path.length + 1) ? '<button type="button" class="file-group-heading" data-path="' +
          escapeHtml(folder.path + "/" + path) + '">' + icon("folder") + '<span>' + escapeHtml(path) + '</span></button>' : '') +
        '<div class="file-grid">' + group.map((file) => fileCard(file, false)).join("") + '</div></section>').join("") +
      (!files.length ? '<p class="todo-empty">В этой папке пока нет файлов</p>' : '') + '</section>';
  }).join`, `folders.map`.

Прямые присваивания полям/свойствам: `container.hidden`, `container.innerHTML`.

<a id="symbol-renderOrderHeading"></a>

## renderOrderHeading

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderHeading()
```

Показывает заголовок карточки заказа и его независимые отметки.

Использует `$`, `supplierLabel.setAttribute`, `supplierLabel.style.setProperty`.

Непосредственные вызовы: `$`, `supplierLabel.setAttribute`, `supplierLabel.style.setProperty`, `String`, `supplierLabel.classList.toggle`, `Boolean`, `createEvent.before`, `metaParent.append`, `headingMeta.classList.toggle`, `$("orderHeadingTitle").parentElement.classList.toggle`, `button.setAttribute`, `orderRowSaving`.

Прямые присваивания полям/свойствам: `supplierLabel.hidden`, `supplierLabel.textContent`, `$("folderTitleText").textContent`, `$("orderFolderName").hidden`, `$("orderFolderName").textContent`, `button.hidden`, `button.title`, `button.disabled`, `button.firstElementChild.textContent`.

<a id="symbol-renderOrderLinks"></a>

## renderOrderLinks

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderLinks()
```

Показывает состав и доступные действия группы связанных заказов.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `Boolean`, `normalize`, `$("orderLinksSearch").value.trim`, `[document.body, $("orderLinksDialog")].includes`, `section`, `[...$("orderLinksOptions").querySelectorAll('[data-related-target]')].find(button => button.dataset.relatedTarget === active)?.focus`, `[...$("orderLinksOptions").querySelectorAll('[data-related-target]')].find`, `$("orderLinksOptions").querySelectorAll`.

Прямые присваивания полям/свойствам: `$("closeOrderLinks").disabled`, `$("refreshOrderLinks").disabled`, `$("initializeOrderLinks").hidden`, `$("initializeOrderLinks").disabled`, `$("orderLinksOrder").textContent`, `$("orderLinksState").textContent`, `$("orderLinksOptions").innerHTML`, `$("orderLinksOptions").scrollTop`.

<a id="symbol-renderOrderLinks.section"></a>

## renderOrderLinks.section

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const section = (items, linked) =>
```

Строит отображаемую секцию доступных связанных заказов.

Использует `(items || []).filter`, `visible.map`.

Непосредственные вызовы: `(items || []).filter`, `visible.map(item =>
      '<div class="order-link-option"><div>' + (item.available ? '<a href="?path=' + encodeURIComponent(item.path) + '" data-related-open="' + escapeHtml(item.path) + '">' + escapeHtml(item.title) + '</a>' : '<span>' + escapeHtml(item.title) + '</span>') +
      '<small>' + escapeHtml(item.available ? item.path : item.registered ? 'Заказ больше не находится в этом объекте' : 'Заказ недоступен или убран из списка') +
      '</small></div><div class="order-link-actions">' +
      '<button type="button" class="secondary-button" data-related-target="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml((linked ? 'Убрать связь: ' : 'Связать: ') + item.title) + '"' +
      (edit.saving || edit.loading || edit.conflict || unknown || edit.data?.group_error || edit.data?.needs_primary || !item.editable ? ' disabled' : '') + '>' + (linked ? 'Убрать связь' : 'Связать') + '</button></div></div>').join`, `visible.map`.

<a id="symbol-renderOrderLocationLink"></a>

## renderOrderLocationLink

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderLocationLink(label, path)
```

Строит переход к клиенту или объекту заказа.

Использует `escapeHtml`, `encodeURIComponent`.

Непосредственные вызовы: `escapeHtml`, `encodeURIComponent`.

<a id="symbol-renderOrderMarkerButton"></a>

## renderOrderMarkerButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderMarkerButton(order, kind)
```

Строит кнопку независимой отметки заказа.

Использует `escapeHtml`, `Boolean`, `orderRowSaving`.

Непосредственные вызовы: `escapeHtml`, `Boolean`, `orderRowSaving`, `icon`.

<a id="symbol-renderOrderProductionStatus"></a>

## renderOrderProductionStatus

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderProductionStatus(order)
```

Строит переключатель производственного статуса строки.

Использует `escapeHtml`, `Object.hasOwn`, `orderRowSaving`.

Непосредственные вызовы: `escapeHtml`, `Object.hasOwn`, `orderRowSaving`, `renderProductionStatusOptions`.

<a id="symbol-renderOrderPurchaseButton"></a>

## renderOrderPurchaseButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderPurchaseButton(order)
```

Строит кнопку закупок текущего заказа в списке.

Использует `orderPurchaseSummary`, `escapeHtml`, `icon`.

Непосредственные вызовы: `orderPurchaseSummary`, `escapeHtml`, `icon`.

<a id="symbol-renderOrderPurchases"></a>

## renderOrderPurchases

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderPurchases(order)
```

Показывает сводку закупок в открытом окне заказа.

Использует `orderPurchaseSummary`, `items.map`.

Непосредственные вызовы: `orderPurchaseSummary`, `items.map((item) => '<li><div class="order-purchase-text"><span aria-hidden="true">○</span><span class="visually-hidden">Нужно закупить: </span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></div>' +
      '<div class="order-purchase-suppliers" aria-label="Выбранные поставщики">' + ((item.suppliers || []).length ? item.suppliers.map((name) => '<span>' + escapeHtml(name) + '</span>').join("") : '<span class="no-supplier">Поставщик не выбран</span>') + '</div></li>').join`, `items.map`, `escapeHtml`.

<a id="symbol-renderOrderRelatedButton"></a>

## renderOrderRelatedButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderRelatedButton(order)
```

Строит цепочку связанных заказов выбранного объекта.

Использует `Boolean`, `escapeHtml`, `orderRowSaving`.

Непосредственные вызовы: `Boolean`, `escapeHtml`, `orderRowSaving`, `icon`.

<a id="symbol-renderOrderTodoButton"></a>

## renderOrderTodoButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderTodoButton(order)
```

Строит кнопку количества актуальных задач заказа.

Использует `orderTodoSummary`, `escapeHtml`, `icon`.

Непосредственные вызовы: `orderTodoSummary`, `escapeHtml`, `icon`.

<a id="symbol-renderOrderTodoDialog"></a>

## renderOrderTodoDialog

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderTodoDialog()
```

Обновляет открытое окно задач с текущим состоянием заказа.

Использует `$`, `findListOrder`, `$("orderTodoDialog").close`.

Непосредственные вызовы: `$`, `findListOrder`, `$("orderTodoDialog").close`, `$("closeOrderTodos").setAttribute`, `$("orderTodoBody").setAttribute`, `orderPurchaseSummary`, `orderTodoSummary`, `renderOrderPurchases`, `renderOrderTodos`.

Прямые присваивания полям/свойствам: `$("orderTodoKindTitle").textContent`, `$("orderTodoHint").textContent`, `$("orderTodoDialogCount").textContent`, `$("orderTodoOrder").textContent`, `$("orderTodoOrder").title`, `$("orderTodoPath").textContent`, `$("orderTodoPath").title`, `$("orderTodoBody").innerHTML`, `state.orderTodoMarkup`, `$("orderTodoBody").scrollTop`.

<a id="symbol-renderOrderTodoGroup"></a>

## renderOrderTodoGroup

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderTodoGroup(group)
```

Строит группу задач с переходом к исходной папке.

Использует `escapeHtml`, `group.items.map`.

Непосредственные вызовы: `escapeHtml`, `group.items.map((item) => '<li' + (item.done ? ' class="done"' : '') + '><span aria-hidden="true">' + (item.done ? '✓' : '○') + '</span><span class="visually-hidden">' + (item.done ? 'Выполнено: ' : 'Нужно сделать: ') + '</span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></li>').join`, `group.items.map`.

<a id="symbol-renderOrderTodos"></a>

## renderOrderTodos

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrderTodos(order)
```

Показывает собственные и вложенные задачи выбранного заказа.

Использует `orderTodoSummary`, `groups.map(renderOrderTodoGroup).join`, `groups.map`.

Непосредственные вызовы: `orderTodoSummary`, `groups.map(renderOrderTodoGroup).join`, `groups.map`, `escapeHtml`.

<a id="symbol-renderOrders"></a>

## renderOrders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderOrders({ force = false } = {})
```

Перестраивает строки текущего списка из локальных данных.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.activeElement?.closest`, `relatedLink.closest('tr').querySelector`, `relatedLink.closest`, `$("ordersWorkspace").querySelector`, `$`, `document.querySelector`, `orderListRows().filter`, `orderListRows`, `isObjectOrderList`, `isWorkOrderList`, `orderListDeadlineOptions`, `renderWorkArchive`, `renderHomeCalendar`, `normalize`, `state.orderQuery.trim`, `orders.filter`, `filtered.sort`, `orderGroupScope`, `orderListGroups().map`, `orderListGroups`, `filtered.forEach`, `renderWorkOrders`, `groups.filter((group) => group.orders.length).map((group) =>
    '<tr class="order-group-divider"><th colspan="' + (object ? 11 : 10) + '"><button type="button" class="order-group-toggle" data-order-group-toggle="' + group.key +
    '" data-order-group-scope="' + escapeHtml(groupScope) + '" aria-expanded="' + !group.collapsed +
    '"><span class="order-group-chevron" aria-hidden="true">▸</span><span>' + escapeHtml(group.label) +
    '</span><span class="count-badge">' + group.orders.length + '</span></button></th><td class="order-deadline-column">' + renderDeadlineMonthLegend(deadlineOptions) + '</td><td colspan="2"></td></tr>' +
    group.orders.map((order) => '<tr data-order-group-row="' + group.key + '"' + (group.collapsed ? ' hidden' : '') + '><td class="order-blue-plus-column">' + renderOrderMarkerButton(order, "bluePlus") + '</td><td class="order-dollar-column">' + renderOrderMarkerButton(order, "dollar") + '</td><td class="order-flag-column">' + renderOrderMarkerButton(order, "flag") + '</td><td class="order-favorite-column">' + renderOrderFavoriteButton(order) + '</td>' + (object ? '<td class="order-related-column">' + renderOrderRelatedButton(order) + '</td>' : '') + '<td class="order-todo-column">' + renderOrderTodoButton(order) + '</td><td class="order-todo-column">' + renderOrderPurchaseButton(order) + '</td><td class="order-client-column">' + renderOrderLocationLink(order.client, order.client_path) + '</td><td class="order-object-column">' + renderOrderLocationLink(order.object, order.object_path) + '</td><td><button class="order-row-link" data-order="' + escapeHtml(order.path) + '">' + escapeHtml(order.title) + '</button>' + (order.registered === false ? '<span class="order-unregistered-label">Не добавлен</span>' : '') + '<span class="order-row-path">' + escapeHtml(order.path) + '</span>' + (object ? renderCompactOrderLinks(order) : '') + '</td><td class="order-comment-column">' + renderOrderComment(order) + '</td><td class="order-deadline-column">' + renderOrderDeadlines(order, { options: deadlineOptions }) + '</td><td>' + renderOrderProductionStatus(order) + '</td>' +
    '<td class="order-updated">' + (order.updated ? formatDate(order.updated) : '—') + (order.sync_pending ? '<span class="sync-pending" title="' + escapeHtml(order.sync_error || "Ожидает выгрузки в папку") + '">' + (order.sync_error ? "В очереди · автоповтор" : "Ожидает выгрузки") + '</span>' : '<span class="sync-complete">' + (order.storage === 'database' ? 'В базе' : 'Выгружено') + '</span>') + '</td></tr>').join("")).join`, `groups.filter((group) => group.orders.length).map`, `groups.filter`, `Boolean`, `pending.filter`, `[scan?.folders ? "Поиск завершён: добавлено " + scan.added + (scan.errors.length ? ", ошибок: " + scan.errors.length : "") : "", errors.length ? "Сохранено в базе · в очереди выгрузки: " + pending.length + " · ошибок: " + errors.length + " · повторим автоматически" : pending.length ? "Ожидает выгрузки: " + pending.length : "Изменения выгружены в папки"].filter(Boolean).join`, `[scan?.folders ? "Поиск завершён: добавлено " + scan.added + (scan.errors.length ? ", ошибок: " + scan.errors.length : "") : "", errors.length ? "Сохранено в базе · в очереди выгрузки: " + pending.length + " · ошибок: " + errors.length + " · повторим автоматически" : pending.length ? "Ожидает выгрузки: " + pending.length : "Изменения выгружены в папки"].filter`, `storage.errors.slice(0, 2).map(item => item.path + ": " + item.error).join`, `storage.errors.slice(0, 2).map`, `storage.errors.slice`, `formatDate`, `Date.parse`, `scan.errors.slice(0, 3).join`, `scan.errors.slice`, `state.unregistrations.some`, `$("ordersWorkspace").querySelectorAll("th").forEach`, `$("ordersWorkspace").querySelectorAll`, `renderOrderTodoDialog`, `focusOrderMarker`, `focusOrderFavorite`, `[...$("ordersTableBody").querySelectorAll("[data-order-related]")].find(button => button.dataset.orderRelated === focusedRelated)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-related]")].find`, `$("ordersTableBody").querySelectorAll`, `[...$("ordersTableBody").querySelectorAll('[data-order]')].find(button => button.dataset.order === focusedRelatedLink.path)?.closest`, `[...$("ordersTableBody").querySelectorAll('[data-order]')].find`, `[...(row?.querySelectorAll('[data-related-card-id]') || [])].find(link => link.dataset.relatedCardId === focusedRelatedLink.id)?.focus`, `[...(row?.querySelectorAll('[data-related-card-id]') || [])].find`, `row?.querySelectorAll`, `focusOrderDeadline`, `[...$("ordersTableBody").querySelectorAll("[data-order-calendar-compact]")].find(el => el.dataset.orderCalendarCompact === focusedCompact)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-calendar-compact]")].find`, `focusOrderGroup`, `[...$("ordersTableBody").querySelectorAll("[data-order], [data-order-todos]")].find((button) => focusedOrder ? button.dataset.order === focusedOrder : button.dataset.orderTodos === focusedTodos)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order], [data-order-todos]")].find`.

Прямые присваивания полям/свойствам: `$(work ? "workOrderDirectoryCount" : object ? "objectOrdersSummary" : "folderSummary").textContent`, `$("ordersTableBody").innerHTML`, `$("ordersEmpty").hidden`, `$("ordersEmptyTitle").textContent`, `$("ordersEmptyHint").textContent`, `$("ordersSyncState").textContent`, `listScroll.scrollLeft`, `pane.scrollTop`.

<a id="symbol-renderPrintList"></a>

## renderPrintList

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderPrintList()
```

Показывает список черновиков и выпущенных заданий печати.

Использует `$`, `printFiles`.

Непосредственные вызовы: `$`, `printFiles`, `files.map((file) => '<button class="print-task-button' +
    (state.printTask?.path === file.path ? " active" : "") + '" data-task="' + escapeHtml(file.path) +
    '" title="' + escapeHtml(file.name) + '"><span>' + icon("file") + '<strong>' +
    escapeHtml(file.title || file.name.replace(/\.(textClipping|txt|text|md|rtf)$/i, "")) + '</strong></span><small>' +
    formatDate(file.modified) + (file.folder ? " · " + escapeHtml(file.folder) : "") + '</small></button>').join`, `files.map`.

Прямые присваивания полям/свойствам: `$("printTaskCount").textContent`, `$("printTaskList").innerHTML`.

<a id="symbol-renderPrintSaveState"></a>

## renderPrintSaveState

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderPrintSaveState()
```

Обновляет состояние сохранения открытого задания печати.

Использует `$`, `$("printSaveState").classList.toggle`, `Boolean`.

Непосредственные вызовы: `$`, `$("printSaveState").classList.toggle`, `Boolean`, `$("printLink").value.trim`, `URL`, `["http:", "https:"].includes`.

Прямые присваивания полям/свойствам: `$("printTaskName").textContent`, `$("printSaveState").textContent`, `$("savePrintTask").textContent`, `$("savePrintTask").disabled`, `$("publishPrintTask").hidden`, `$("publishPrintTask").disabled`, `$("openPrintLink").hidden`, `$("openPrintLink").href`.

<a id="symbol-renderProductionStatusOptions"></a>

## renderProductionStatusOptions

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderProductionStatusOptions(selected)
```

Строит варианты производственного статуса для редактора.

Использует `productionStatusGroups().map`, `productionStatusGroups`.

Непосредственные вызовы: `productionStatusGroups().map((group, index) => {
    return '<optgroup label="— ' + (index + 1) + '-я группа —">' + group.statuses.map((status) =>
      '<option value="' + status + '"' + (selected === status ? ' selected' : '') + '>' +
      statusLabels[status] + '</option>').join("") + '</optgroup>';
  }).join`, `productionStatusGroups().map`, `productionStatusGroups`.

<a id="symbol-renderPurchaseSaveState"></a>

## renderPurchaseSaveState

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderPurchaseSaveState()
```

Показывает состояние сохранения закупок и доступность повторной проверки.

Использует `$`.

Непосредственные вызовы: `$`.

Прямые присваивания полям/свойствам: `$("purchaseSaveState").textContent`.

<a id="symbol-renderPurchases"></a>

## renderPurchases

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderPurchases()
```

Показывает редактор исходных закупок текущего заказа.

Использует `Array.isArray`, `$`, `Boolean`.

Непосредственные вызовы: `Array.isArray`, `$`, `Boolean`, `items.filter`, `items.map((item, index) => '<div class="todo-row' + (item.done ? ' done' : '') + '" data-purchase-index="' + index + '">' +
    '<input class="todo-check" type="checkbox" aria-label="Закупка выполнена: ' + escapeHtml(item.text) + '"' + (item.done ? ' checked' : '') + '>' +
    '<input class="todo-text" type="text" maxlength="1000" size="' + Math.max(4, Array.from(item.text).length + 1) + '" aria-label="Текст закупки или затраты" value="' + escapeHtml(item.text) + '">' +
    '<div class="purchase-suppliers" role="group" aria-label="Поставщики для закупки: ' + escapeHtml(item.text) + '">' + purchaseSupplierButtons(item) + '</div>' +
    '<button class="todo-delete" type="button" aria-label="Удалить закупку: ' + escapeHtml(item.text) + '">×</button></div>').join`, `items.map`, `renderPurchaseSaveState`.

Прямые присваивания полям/свойствам: `$("purchaseLegacy").hidden`, `$("purchaseLegacyText").textContent`, `$("purchaseAddForm").hidden`, `$("purchaseEmpty").hidden`, `$("purchaseCount").textContent`, `$("purchaseList").innerHTML`.

<a id="symbol-renderSketches"></a>

## renderSketches

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderSketches()
```

Показывает непосредственные CDR, скачивание и актуальность в карточке заказа.

Использует `/api/thumbnail` и `/api/file`; сохраняет фокус статуса или скачивания.

Непосредственные вызовы: `document.activeElement?.closest`, `$`, `files.map((item) => {
    const relevance = item.relevance, saving = folder.sketchSavingFolders?.has(item.folder);
    const message = saving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder sketch-tile" data-relevance-state="' + escapeHtml(relevance.value || "none") + '">' +
      '<button class="subfolder sketch-open" data-sketch-open="' + escapeHtml(item.path) + '" data-sketch-key="' + escapeHtml(item.key) + '" title="' + escapeHtml(item.name + " · Открыть в CorelDRAW на Mac с менеджером") + '" aria-label="' + escapeHtml("Открыть в CorelDRAW на Mac с менеджером: " + item.name) + '"' + (item.opening ? ' disabled' : '') + '>' +
      '<span class="sketch-picture"><img data-thumbnail-path="' + escapeHtml(item.path) + '" data-thumbnail-key="' + escapeHtml(item.thumbnail_key) + '" src="' + escapeHtml(apiUrl("/api/thumbnail", item.path, { v: item.thumbnail_key })) + '" alt="" loading="lazy" decoding="async"><span class="sketch-fallback">CDR</span></span><span class="sketch-name">' + escapeHtml(item.name) + '</span></button>' +
      fileDownloadButton(item) +
      '<div class="event-relevance" role="group" aria-label="' + escapeHtml("Актуальность эскиза " + item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-sketch-file="' + escapeHtml(item.path) + '" data-sketch-status="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (saving || relevance.error || !relevance.revision ? ' disabled' : '') + '>' + label + '</button>').join("") + '</div>' +
      (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? ' error' : '') + '" role="status">' + escapeHtml(message) + '</p>' : '') + '</div>';
  }).join`, `files.map`, `[...$("sketchTiles").querySelectorAll(focusSelector)].find((button) => (button.dataset.sketchFile || button.dataset.downloadFile) === focusPath && button.dataset.sketchStatus === focusValue)?.focus`, `[...$("sketchTiles").querySelectorAll(focusSelector)].find`, `$("sketchTiles").querySelectorAll`.

Прямые присваивания полям/свойствам: `$("sketchSection").hidden`, `$("sketchCount").textContent`, `$("sketchTiles").innerHTML`.

<a id="symbol-renderStatus"></a>

## renderStatus

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderStatus()
```

Заполняет редактор сохранённого состояния текущей карточки.

Использует `Boolean`, `Object.hasOwn`, `isWorkOrderPath`.

Непосредственные вызовы: `Boolean`, `Object.hasOwn`, `isWorkOrderPath`, `$`, `renderPurchaseSaveState`, `renderCardDeadlines`.

Прямые присваивания полям/свойствам: `$("statusBadge").hidden`, `$("statusBadge").textContent`, `$("statusBadge").dataset.status`, `$("statusSelect").dataset.status`, `$("financialStatusSelect").dataset.financialStatus`, `$("saveStatusButton").textContent`, `$("todoSaveState").textContent`.

<a id="symbol-renderSubfolders"></a>

## renderSubfolders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderSubfolders()
```

Показывает подпапки текущей папки согласно их ролям.

Использует `/api/thumbnail-cover`.

Непосредственные вызовы: `$("subfolders").classList.toggle`, `$`, `document.activeElement?.closest`, `document.querySelector`, `folder.directories.filter`, `Boolean`, `folder.directories.map(subfolderButton).join`, `folder.directories.map`, `normalize`, `$("frezaTaskSearch").value.trim`, `visibleDirectories.filter((item) => !query || normalize(item.name).includes(query)).sort`, `visibleDirectories.filter`, `$("subfolders").classList.remove`, `tasks.map((item) => '<button type="button" class="subfolder freza-task" data-path="' + escapeHtml(item.path) + '"><span class="freza-task-picture"><img data-thumbnail-folder="' + escapeHtml(item.path) + '" src="' + escapeHtml(apiUrl("/api/thumbnail-cover", item.path)) + '" alt="" loading="lazy" decoding="async"><span class="thumbnail-fallback">' + icon("file") + '</span></span><span>' + escapeHtml(item.name) + '</span>' + icon("chevron") + '</button>').join`, `tasks.map`, `directories.filter((item) => item.supplierFavorite?.is_favorite === true).sort`, `directories.filter`, `isWorkOrderList`, `$("workOrdersSection").setAttribute`, `$("workOrdersSection").classList.toggle`, `workOrders.map(subfolderButton).join`, `workOrders.map`, `folder.directories.map((item) => '<button type="button" class="subfolder" data-path="' + escapeHtml(item.path) + '">' + icon("folder") + '<span>' + escapeHtml(item.name) + '</span>' + icon("chevron") + '</button>').join`, `directories.some`, `["supplier_root", "work_section"].includes`, `directories.map((item, index) => {
    const open = subfolderButton(item);
    const relevance = item.eventRelevance;
    if (!relevance) return (supplierDividerAfter && index === supplierDividerAfter ? '<hr class="work-supplier-divider">' : "") + open;
    const message = item.relevanceSaving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder" data-relevance-state="' + escapeHtml(relevance.value || "none") + '" aria-busy="' + Boolean(item.relevanceSaving) + '">' + open +
      '<div class="event-relevance" role="group" aria-label="Актуальность события ' + escapeHtml(item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-event-path="' + escapeHtml(item.path) + '" data-relevance="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (item.relevanceSaving || relevance.error || !relevance.revision ? " disabled" : "") + '>' + label + '</button>').join("") +
      '</div>' + (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? " error" : "") + '" role="status">' + escapeHtml(message) + '</p>' : "") + '</div>';
  }).join`, `directories.map`, `[...$("subfolders").querySelectorAll("[data-relevance]")].find((button) => button.dataset.eventPath === focusPath && button.dataset.relevance === focusValue)?.focus`, `[...$("subfolders").querySelectorAll("[data-relevance]")].find`, `$("subfolders").querySelectorAll`, `focusSupplierStar`, `[...$("subfolders").querySelectorAll("[data-path]")].find(button => button.dataset.path === focusedFolder)?.focus`, `[...$("subfolders").querySelectorAll("[data-path]")].find`.

Прямые присваивания полям/свойствам: `$("frezaTaskSearchLabel").hidden`, `$("frezaLegacyFolders").hidden`, `$("folderSection").hidden`, `$("workOrdersSection").hidden`, `$("printLegacyFolders").hidden`, `$("frezaLegacyCount").textContent`, `$("frezaLegacyList").innerHTML`, `$("foldersTitle").textContent`, `$("directoryCount").textContent`, `$("subfolders").innerHTML`, `$("workOrdersTitle").textContent`, `$("workOrderFolders").innerHTML`, `$("printLegacyFolderCount").textContent`, `$("printLegacyFolderList").innerHTML`, `document.querySelector(".content-pane").scrollTop`.

<a id="symbol-renderSupplierOrderStatus"></a>

## renderSupplierOrderStatus

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderSupplierOrderStatus(order)
```

Строит самостоятельный статус заказа поставщика.

Использует `Object.hasOwn`, `escapeHtml`, `orderRowSaving`.

Непосредственные вызовы: `Object.hasOwn`, `escapeHtml`, `orderRowSaving`, `Object.entries(supplierStatusLabels).map(([key, label]) =>
      '<option value="' + key + '"' + (status === key ? ' selected' : '') + '>' + label + '</option>').join`, `Object.entries(supplierStatusLabels).map`, `Object.entries`.

<a id="symbol-renderTodos"></a>

## renderTodos

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderTodos()
```

Показывает собственные задачи текущей карточки.

Использует `Array.isArray`, `$`, `Boolean`.

Непосредственные вызовы: `Array.isArray`, `$`, `Boolean`, `items.filter`, `items.map((item, index) => '<div class="todo-row' + (item.done ? ' done' : '') + '" data-todo-index="' + index + '">' +
    '<input class="todo-check" type="checkbox" aria-label="Выполнено: ' + escapeHtml(item.text) + '"' + (item.done ? ' checked' : '') + '>' +
    '<input class="todo-text" type="text" maxlength="1000" aria-label="Текст задачи" value="' + escapeHtml(item.text) + '">' +
    '<button class="todo-delete" type="button" aria-label="Удалить задачу: ' + escapeHtml(item.text) + '">×</button></div>').join`, `items.map`.

Прямые присваивания полям/свойствам: `$("todoLegacy").hidden`, `$("todoLegacyText").textContent`, `$("todoAddForm").hidden`, `$("todoEmpty").hidden`, `$("todoEmpty").textContent`, `$("todoCount").textContent`, `$("todoList").innerHTML`.

<a id="symbol-renderTree"></a>

## renderTree

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderTree()
```

Обновляет DOM дерева для текущего состояния навигации.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.activeElement?.closest`, `Boolean`, `$`, `markup`, `data.groups.map((group) => '<section class="catalog-tree-section"><div class="tree-heading catalog-tree-heading"><button type="button" data-catalog-group="' + escapeHtml(group.path) + '" title="Открыть группу ' + escapeHtml(group.name) + '"' + (state.selected === group.path ? ' aria-current="page"' : '') + '>' + escapeHtml(group.name) + '</button><span>' + (group.error ? "—" : group.children.length) + '</span></div><div role="tree" aria-label="Группа ' + escapeHtml(group.name) + '">' + (group.error ? '<p class="tree-empty" role="status">' + escapeHtml(group.error) + '</p>' : markup(group.children)) + '</div></section>').join`, `data.groups.map`, `$("folderTree").querySelectorAll`, `tree.querySelectorAll`, `rows.find`, `rows.forEach`, `focusTree`, `[...$("folderTree").querySelectorAll("[data-catalog-group]")].find((button) => button.dataset.catalogGroup === focusedGroup)?.focus`, `[...$("folderTree").querySelectorAll("[data-catalog-group]")].find`, `state.auxiliary.map((node) =>
    '<button class="auxiliary-button' + (state.selected === node.path || state.selected.startsWith(node.path + "/") ? " active" : "") +
    '" data-path="' + escapeHtml(node.path) + '" title="' + escapeHtml(node.name) + '">' + icon("folder") +
    '<span>' + escapeHtml(node.name) + "</span></button>").join`, `state.auxiliary.map`, `renderFavoriteOrders`.

Прямые присваивания полям/свойствам: `$("folderTree").innerHTML`, `$("auxiliaryButtons").innerHTML`, `$("auxiliaryButtons").hidden`.

<a id="symbol-renderTree.markup"></a>

## renderTree.markup

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const markup = (nodes) =>
```

Формирует HTML текущего компонента из переданных данных.

Использует `treeMarkup`.

Непосредственные вызовы: `treeMarkup`.

<a id="symbol-renderUpload"></a>

## renderUpload

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderUpload()
```

Обновляет прогресс и результаты текущей последовательной загрузки файлов.

Использует `$`, `Boolean`, `formatSize`.

Непосредственные вызовы: `$`, `Boolean`, `formatSize`, `$("uploadDestination").setAttribute`, `Math.round`, `job.results.filter`, `$("uploadSummary").classList.toggle`, `job.results.map((item) => '<li' + (item.error ? ' class="error"' : '') + '>' + escapeHtml(item.error ? item.original + " — " + item.error : item.name + " · сохранён") + '</li>').join`, `job.results.map`.

Прямые присваивания полям/свойствам: `$("uploadPanel").hidden`, `$("chooseUploadFiles").disabled`, `$("uploadDropHint").textContent`, `$("uploadTitle").textContent`, `$("uploadDestination").textContent`, `$("uploadDestination").title`, `$("uploadCurrent").textContent`, `$("uploadProgress").hidden`, `$("uploadProgress").value`, `$("closeUploadPanel").hidden`, `$("uploadSummary").textContent`, `$("uploadResults").innerHTML`.

<a id="symbol-renderWorkArchive"></a>

## renderWorkArchive

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderWorkArchive()
```

Показывает архивные заказы поставщиков с возможностью возврата.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `isWorkOrderList`, `state.workArchivedOrders.filter(order => order.supplier_status === "archived")
    .sort((a, b) => (b.archived_at || 0) - (a.archived_at || 0) || (b.archive_sequence || 0) - (a.archive_sequence || 0) || compareOrderText(a.path, b.path)).slice`, `state.workArchivedOrders.filter(order => order.supplier_status === "archived")
    .sort`, `state.workArchivedOrders.filter`, `rows.map(order => '<div class="work-archive-row"><div><a class="order-row-link" data-work-archive-order="' + escapeHtml(order.path) +
    '" href="?path=' + encodeURIComponent(order.path) + '">' + escapeHtml(order.title) + '</a><small>' + escapeHtml([order.work_supplier, order.path].filter(Boolean).join(" · ")) +
    '</small></div><span class="work-archive-date">' + (order.archived_at ? escapeHtml(formatDate(order.archived_at)) : '') + '</span><button type="button" class="secondary-button" data-work-archive-restore="' + escapeHtml(order.path) +
    '"' + (orderRowSaving(order.path) || order.registered === false || order.supplier_status === null ? ' disabled' : '') + '>Вернуть в работу</button></div>').join`, `rows.map`, `([...section.querySelectorAll("[data-work-archive-restore]")].find(button => button.dataset.workArchiveRestore === focused) || $("workArchiveHeading")).focus`, `[...section.querySelectorAll("[data-work-archive-restore]")].find`, `section.querySelectorAll`.

Прямые присваивания полям/свойствам: `section.hidden`, `$("workArchiveCount").textContent`, `$("workArchiveList").innerHTML`.

<a id="symbol-renderWorkOrders"></a>

## renderWorkOrders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function renderWorkOrders(orders, options)
```

Обновляет сводку производственных заказов текущего раздела.

Использует `orderGroupScope`, `state.workOrderGroups.map`.

Непосредственные вызовы: `orderGroupScope`, `state.workOrderGroups.map((group) => {
    const rows = orders.filter((order) => order.path.normalize("NFC").split("/").slice(0, -1).join("/") === group.key);
    if (!rows.length) return "";
    const collapsed = orderGroupCollapsed(scope, group.key);
    const style = group.color ? ' style="--supplier-hue:' + Number(group.color.hue) + '"' : '';
    return '<tr class="order-group-divider"' + style + '><th colspan="7"><button type="button" class="order-group-toggle" data-order-group-toggle="' + escapeHtml(group.key) +
      '" data-order-group-scope="' + escapeHtml(scope) + '" aria-expanded="' + !collapsed + '"><span class="order-group-chevron" aria-hidden="true">▸</span><span>' + escapeHtml(group.label) +
      '</span><span class="count-badge">' + rows.length + '</span></button></th><td></td><td class="order-deadline-column">' + renderDeadlineMonthLegend(options) + '</td><td></td></tr>' +
      rows.map((order) => '<tr data-order-group-row="' + escapeHtml(group.key) + '"' + style + (group.color?.neutral ? ' class="supplier-neutral"' : '') + (collapsed ? ' hidden' : '') + '>' +
        '<td class="order-blue-plus-column">' + renderOrderMarkerButton(order, "bluePlus") + '</td><td class="order-dollar-column">' + renderOrderMarkerButton(order, "dollar") + '</td><td class="order-flag-column">' + renderOrderMarkerButton(order, "flag") + '</td>' +
        '<td class="order-favorite-column">' + renderOrderFavoriteButton(order) + '</td><td class="order-todo-column">' + renderOrderTodoButton(order) + '</td>' +
        '<td><button class="order-row-link" data-order="' + escapeHtml(order.path) + '">' + escapeHtml(order.title) + '</button>' + (order.registered === false ? '<span class="order-unregistered-label">Не добавлен в производство</span>' : '') +
        '<span class="order-row-path">' + escapeHtml(order.path) + '</span></td><td class="order-comment-column">' + renderOrderComment(order) + '</td><td>' + renderSupplierOrderStatus(order) + '</td>' +
        '<td class="order-deadline-column">' + renderOrderDeadlines(order, { options }) + '</td><td class="order-updated">' + (order.folder_date ? escapeHtml(order.folder_date.split("-").reverse().join(".")) : '—') + '</td></tr>').join("");
  }).join`, `state.workOrderGroups.map`.

<a id="symbol-request"></a>

## request

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function request(url, payload, options = {})
```

Отправляет запрос серверу и преобразует HTTP-ошибку в исключение интерфейса.

Использует `/api/reconciliation-save`, `/api/invoice-reconciliation`.

Непосредственные вызовы: `fetch`, `['/api/reconciliation-save', '/api/invoice-reconciliation'].includes`, `JSON.stringify`, `response.json`, `Error`.

Прямые присваивания полям/свойствам: `error.status`.

<a id="symbol-resizeOrderNote"></a>

## resizeOrderNote

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function resizeOrderNote()
```

Подгоняет высоту поля заметки под его текущее содержимое.

Использует `$`, `Math.min`, `Math.max`.

Непосредственные вызовы: `$`, `Math.min`, `Math.max`, `note.value.trim`.

Прямые присваивания полям/свойствам: `note.style.height`.

<a id="symbol-restoreCalendarDeletion"></a>

## restoreCalendarDeletion

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function restoreCalendarDeletion(entry, revision)
```

Запрашивает восстановление удалённой записи со всеми отметками.

Использует `/api/calendar-payment-restore`, `/api/calendar-event-restore`, `/api/order-calendar-event-restore`.

Непосредственные вызовы: `state.calendarMoving.has`, `Error`, `state.calendarMoving.add`, `request`, `applyCalendarDeletion`, `notify`, `state.calendarMoving.delete`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-restoreEventSession"></a>

## restoreEventSession

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function restoreEventSession(session)
```

Запускает восстановление выбранного сеанса корзины.

Использует `/api/event-trash-restore`.

Непосредственные вызовы: `$("fileTrashList").querySelectorAll("button").forEach`, `$("fileTrashList").querySelectorAll`, `$`, `request`, `loadFileTrash`, `reloadClientTrees`, `loadOrderFiles`, `loadDescendantTodos`, `loadOrders`, `$("fileTrashDialogState").classList.remove`, `$("fileTrashDialogState").classList.add`.

Прямые присваивания полям/свойствам: `state.trashRestoring`, `$("fileTrashDialogState").textContent`.

<a id="symbol-restoreFileSession"></a>

## restoreFileSession

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function restoreFileSession(session)
```

Запускает восстановление выбранного сеанса корзины.

Использует `/api/files-trash-restore`.

Непосредственные вызовы: `$("fileTrashList").querySelectorAll("button").forEach`, `$("fileTrashList").querySelectorAll`, `$`, `request`, `loadFileTrash`, `loadOrderFiles`, `$("fileTrashDialogState").classList.toggle`, `Boolean`, `$("fileTrashState").classList.toggle`.

Прямые присваивания полям/свойствам: `state.trashRestoring`, `$("fileTrashDialogState").textContent`, `$("fileTrashState").textContent`.

<a id="symbol-restoreWorkArchive"></a>

## restoreWorkArchive

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function restoreWorkArchive(button)
```

Снимает архивирование выбранного заказа поставщика.

Использует `/api/order-supplier-status`.

Непосредственные вызовы: `state.workArchivedOrders.find`, `orderRowSaving`, `state.orderStatusSaving.add`, `renderWorkArchive`, `request`, `isWorkOrderList`, `state.workArchivedOrders.filter`, `state.workArchivedPaths.filter`, `state.objectOrders.some`, `state.objectOrders.push`, `applyOrderRecord`, `notify`, `loadOrders`, `state.orderStatusSaving.delete`, `hasOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.workArchivedOrders`, `state.workArchivedPaths`.

<a id="symbol-revealPath"></a>

## revealPath

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function revealPath(path, navigation)
```

Последовательно раскрывает дерево до выбранной папки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `state.auxiliary.some`, `path.split`, `parts.slice(0, index).join`, `parts.slice`, `loadChildren`, `state.expanded.add`, `renderTree`, `$("folderTree").querySelector`, `$`, `selected?.scrollIntoView`.

<a id="symbol-rubles"></a>

## rubles

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const rubles = (value) =>
```

Форматирует денежное значение для соответствующего компонента.

Использует `Intl.NumberFormat`.

Непосредственные вызовы: `new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 2 }).format`, `Intl.NumberFormat`.

<a id="symbol-run"></a>

## run

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function run(action)
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `Promise.resolve().then(action).catch`, `Promise.resolve().then`, `Promise.resolve`.

Непосредственные вызовы: `Promise.resolve().then(action).catch`, `Promise.resolve().then`, `Promise.resolve`.

<a id="symbol-saveCalendarEvent"></a>

## saveCalendarEvent

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveCalendarEvent()
```

Сохраняет название и необязательный комментарий свободного события с UUID/revision.

Комментарий отправляет только свободному событию; оба поля сохраняет при ошибке.

Непосредственные вызовы: `$`, `text.trim`, `renderCalendarEventControls`, `request`, `applyFreeCalendarEvent`, `applyOrderRecord`, `closeCalendarEvent`, `renderOrders`, `notify`.

Прямые присваивания полям/свойствам: `$("calendarEventState").textContent`, `edit.saving`, `state.ordersRequest`, `edit.conflict`.

<a id="symbol-saveClientActivity"></a>

## saveClientActivity

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveClientActivity(inactive, acceptFile = false)
```

Сохраняет выбранную активность с версией текущей записи.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `folderActivity`, `renderClientActivity`, `saveCurrentStatus`, `updateFolderActivity`, `request`, `activityRoute`, `reloadClientTrees`, `loadOrders`, `apiUrl`.

Прямые присваивания полям/свойствам: `state.clientActivitySaving`.

<a id="symbol-saveCurrentPrintTask"></a>

## saveCurrentPrintTask

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveCurrentPrintTask(force = false)
```

Сохраняет или выпускает открытое задание печати.

Использует `/api/print-create`, `/api/print-save`.

Непосредственные вызовы: `saveCurrentPrintTask`, `$("printLink").checkValidity`, `$`, `$("printLink").reportValidity`, `Error`, `$("printTitle").value.trim`, `$("printLink").value.trim`, `async () => {
    const saved = await request(task.isNew ? "/api/print-create" : "/api/print-save", {
      path: task.isNew ? folder : task.path, revision: task.revision, title, link, description,
    });
    if (state.printTask === task) {
      Object.assign(task, saved, { isNew: false });
      task.dirty = $("printTitle").value.trim() !== saved.title || $("printLink").value.trim() !== saved.link || $("printDescription").value !== saved.description;
      const url = new URL(location.href);
      url.searchParams.set("task", saved.path);
      window.history.replaceState(null, "", url.pathname + url.search);
    }
    const refreshed = await request(folderUrl(folder));
    Object.assign(state.folder, refreshed, { note: state.folder.note });
    $("folderSummary").textContent = printCountLabel(state.folder.fileCount) + " · название, ссылка и описание";
    renderPrintList();
  }`, `renderPrintSaveState`.

Прямые присваивания полям/свойствам: `state.printSaving`.

<a id="symbol-saveCurrentStatus"></a>

## saveCurrentStatus

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveCurrentStatus()
```

Сохраняет открытый редактор карточки с проверкой версии.

Использует `/api/reconciliation-save`, `/api/folder-note-save`, `/api/note`.

Непосредственные вызовы: `flushDeadlineComments`, `saveCurrentStatus`, `currentOrderValues`, `$`, `request`, `renderStatus`, `JSON.stringify`, `renderExportState`, `renderOrderHeading`.

Прямые присваивания полям/свойствам: `$("saveStatusButton").disabled`, `$("saveStatusButton").textContent`, `state.saving`, `folder.status`, `folder.financial_status`, `folder.note`, `folder.statusSource`, `folder.order`, `folder.reconciliation`, `folder.folderNote`, `folder.draftCard`, `state.dirty`.

<a id="symbol-saveEventRelevance"></a>

## saveEventRelevance

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveEventRelevance(path, value)
```

Сохраняет актуальность выбранной папки события.

Использует `/api/event-relevance`.

Непосредственные вызовы: `folder?.directories.find`, `renderSubfolders`, `request`, `apiUrl`.

Прямые присваивания полям/свойствам: `item.relevanceSaving`, `item.eventRelevance`.

<a id="symbol-saveFileComment"></a>

## saveFileComment

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveFileComment()
```

Сохраняет текст комментария по привязке файла и версии.

Использует `/api/invoice-comment`, `/api/file-comment`.

Непосредственные вызовы: `saveFileComment`, `Error`, `request`, `renderFileComment`, `Object.assign`, `document.dispatchEvent`, `Event`, `updateFileCommentCaption`.

Прямые присваивания полям/свойствам: `state.fileCommentSaving`, `comment.error`.

<a id="symbol-saveOrderLinksChange"></a>

## saveOrderLinksChange

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveOrderLinksChange(payload)
```

Сохраняет изменение группы связей с проверкой UUID и версии.

Использует `/api/order-links`.

Непосредственные вызовы: `renderOrderLinks`, `request`, `applyOrderRecord`, `hasOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `edit.saving`, `edit.error`, `edit.data`, `edit.conflict`.

<a id="symbol-saveSketchRelevance"></a>

## saveSketchRelevance

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function saveSketchRelevance(path, value)
```

Сохраняет актуальность конкретного эскиза с проверочной привязкой.

Использует `/api/sketch-relevance`.

Непосредственные вызовы: `folder?.sketches?.find`, `folder.sketchSavingFolders?.has`, `Set`, `folder.sketchSavingFolders.add`, `renderSketches`, `request`, `Error`, `applySketchGroup`, `apiUrl`, `folder.sketchSavingFolders.delete`.

Прямые присваивания полям/свойствам: `folder.sketchSavingFolders`.

<a id="symbol-saveTodosSoon"></a>

## saveTodosSoon

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function saveTodosSoon(delay = 0)
```

Планирует отложенное сохранение изменённых задач.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `renderStatus`, `setTimeout`.

Прямые присваивания полям/свойствам: `state.dirty`.

<a id="symbol-scheduleCalendarTodoPreviewClose"></a>

## scheduleCalendarTodoPreviewClose

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function scheduleCalendarTodoPreviewClose()
```

Планирует закрытие общего окна задач или комментария после ухода мыши.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `setTimeout`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.timer`.

<a id="symbol-sendUpload"></a>

## sendUpload

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function sendUpload(file, job)
```

Передаёт один файл с привязкой к открытой папке и обновлением прогресса.

Использует `/api/file-upload`.

Непосредственные вызовы: `Promise`.

<a id="symbol-setPreviewExpanded"></a>

## setPreviewExpanded

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function setPreviewExpanded(expanded)
```

Переключает полнооконный просмотр с сохранением редактора комментария.

Использует `$("previewDialog").classList.toggle`, `$`, `$("previewExpand").setAttribute`.

Непосредственные вызовы: `$("previewDialog").classList.toggle`, `$`, `$("previewExpand").setAttribute`, `String`.

Прямые присваивания полям/свойствам: `$("previewExpand").textContent`, `$("previewExpand").title`.

<a id="symbol-shiftDeadlineWeek"></a>

## shiftDeadlineWeek

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function shiftDeadlineWeek(start, offset)
```

Сдвигает ключ понедельника на заданное число недель.

Использует `Date`, `date.setUTCDate`, `date.getUTCDate`.

Непосредственные вызовы: `Date`, `date.setUTCDate`, `date.getUTCDate`, `date.toISOString().slice`, `date.toISOString`, `end.setUTCDate`, `end.getUTCDate`, `/^\d{4}-\d{2}-\d{2}$/.test`, `end.getUTCFullYear`.

<a id="symbol-showInvoicePreview"></a>

## showInvoicePreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function showInvoicePreview(record)
```

Открывает общий PDF-просмотр для сохранённого счёта или вложения.

Использует `/api/invoice-pdf`, `/api/invoice-pdf-info`.

Непосредственные вызовы: `saveFileComment`, `SpreadsheetPreview.close`, `$`, `record.data.date.split("-").reverse().join`, `record.data.date.split("-").reverse`, `record.data.date.split`, `apiUrl`, `$("previewDialog").showModal`, `run`, `request`, `Error`, `showPdfPages`, `previewUnavailable`.

Прямые присваивания полям/свойствам: `state.preview`, `$("previewTitle").textContent`, `$("previewPath").textContent`, `$("previewMeta").textContent`, `$("previewDownload").href`, `$("previewFolderNotePath").textContent`, `$("previewFolderNote").value`, `$("previewPrevious").disabled`, `$("previewNext").disabled`, `$("previewNative").hidden`, `$("fileCommentLabel").textContent`, `$("fileCommentText").maxLength`, `$("previewBody").textContent`.

<a id="symbol-showOrders"></a>

## showOrders

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function showOrders({ history = true } = {})
```

Открывает главную страницу и загружает её сводку.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `closeCalendarTodoPreview`, `$`, `$("orderTodoDialog").close`, `closePreview`, `saveCurrentPrintTask`, `saveCurrentStatus`, `state.folderRequest?.abort`, `mountOrderList`, `state.selectedFiles.clear`, `$("homeButton").setAttribute`, `document.querySelector(".content-pane").setAttribute`, `document.querySelector`, `window.history.pushState`, `renderTree`, `renderOrders`, `document.dispatchEvent`, `Event`, `loadOrders`.

Прямые присваивания полям/свойствам: `state.navigation`, `state.view`, `state.folder`, `state.imageReport`, `state.printTask`, `state.selected`, `$("folderView").hidden`, `$("ordersWorkspace").hidden`, `$("openFolderButton").hidden`, `$("addOrderButton").hidden`, `$("removeOrderButton").hidden`, `$("createObjectFolderButton").hidden`, `$("groupObjectYearsButton").hidden`, `$("createOrderFolderButton").hidden`, `$("createEventFolderButton").hidden`, `$("renameFolderButton").hidden`, `$("moveObjectButton").hidden`, `$("deleteEventButton").hidden`, `$("openEventTrash").hidden`, `$("notice").hidden`, `$("loadOrderFilesButton").hidden`, `$("breadcrumbs").innerHTML`, `$("workSupplierName").hidden`, `$("folderTitleText").textContent`, `$("orderFolderName").hidden`, `$("orderPageFavorite").hidden`, `$("clientLabel").textContent`, `$("scanState").textContent`.

<a id="symbol-showPdfPages"></a>

## showPdfPages

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function showPdfPages(file, pages, version)
```

Загружает сведения о PDF и показывает выбранные страницы.

Использует `/api/invoice-pdf-page`, `/api/pdf-page`.

Непосредственные вызовы: `document.createElement`, `previous.setAttribute`, `next.setAttribute`, `String`, `input.setAttribute`, `label.append`, `document.createTextNode`, `toolbar.append`, `canvas.append`, `viewer.append`, `image.addEventListener`, `previous.addEventListener`, `next.addEventListener`, `input.addEventListener`, `$("previewBody").replaceChildren`, `$`, `changePage`.

Прямые присваивания полям/свойствам: `viewer.className`, `toolbar.className`, `previous.textContent`, `next.textContent`, `label.textContent`, `input.type`, `input.min`, `input.max`, `canvas.className`.

<a id="symbol-showPdfPages.changePage"></a>

## showPdfPages.changePage

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function changePage(page)
```

Переключает отображаемую страницу текущего документа.

Использует `/api/invoice-pdf-page`, `/api/pdf-page`.

Непосредственные вызовы: `Math.min`, `Math.max`, `String`, `apiUrl`.

Прямые присваивания полям/свойствам: `input.value`, `previous.disabled`, `next.disabled`, `image.alt`, `image.src`, `canvas.scrollTop`.

<a id="symbol-showPreview"></a>

## showPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function showPreview(path)
```

Открывает подходящий просмотрщик выбранного файла.

Использует `/api/file`, `/api/freza-preview`, `/api/preview`.

Непосредственные вызовы: `saveFileComment`, `state.folder.files.find`, `SpreadsheetPreview.close`, `$`, `formatSize`, `formatDate`, `apiUrl`, `filteredFiles`, `files.findIndex`, `$("previewBody").replaceChildren`, `$("previewDialog").showModal`, `run`, `["image", "cdr"].includes`, `document.createElement`, `media.addEventListener`, `SpreadsheetPreview.open`, `request`, `Error`, `showPdfPages`, `previewUnavailable`, `$("previewBody").appendChild`.

Прямые присваивания полям/свойствам: `state.preview`, `$("previewNative").hidden`, `$("fileCommentLabel").textContent`, `$("fileCommentText").maxLength`, `$("previewTitle").textContent`, `$("previewPath").textContent`, `$("previewMeta").textContent`, `$("previewDownload").href`, `$("previewFolderNotePath").textContent`, `$("previewFolderNote").value`, `$("previewPrevious").disabled`, `$("previewNext").disabled`, `media.src`, `media.alt`, `$("previewBody").textContent`, `media.controls`, `media.preload`, `media.textContent`.

<a id="symbol-showPrintTask"></a>

## showPrintTask

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function showPrintTask(task)
```

Заполняет редактор выбранного задания печати.

Использует `$`, `renderPrintList`, `renderPrintSaveState`.

Непосредственные вызовы: `$`, `renderPrintList`, `renderPrintSaveState`.

Прямые присваивания полям/свойствам: `state.printTask`, `$("printTitle").value`, `$("printLink").value`, `$("printDescription").value`, `$("printEditorForm").hidden`, `$("printEditorEmpty").hidden`.

<a id="symbol-stepPreview"></a>

## stepPreview

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function stepPreview(direction)
```

Переходит к предыдущему или следующему файлу текущего набора.

Использует `filteredFiles`, `files.findIndex`, `run`.

Непосредственные вызовы: `filteredFiles`, `files.findIndex`, `run`.

<a id="symbol-subfolderButton"></a>

## subfolderButton

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function subfolderButton(item)
```

Строит кнопку подпапки с ролью и доступными действиями.

Использует `Number.isSafeInteger`, `Number`, `escapeHtml`.

Непосредственные вызовы: `Number.isSafeInteger`, `Number`, `escapeHtml`, `icon`, `Boolean`, `state.supplierFavoriteSaving.has`.

<a id="symbol-submitFolderRename"></a>

## submitFolderRename

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function submitFolderRename()
```

Выполняет подтверждённое переименование и применяет новые пути.

Использует `/api/folder-rename`.

Непосредственные вызовы: `controls.forEach`, `$`, `saveCurrentStatus`, `request`, `$("renameFolderDialog").close`, `openRelocatedFolder`, `notify`.

Прямые присваивания полям/свойствам: `state.folderRenaming`, `$("renameFolderError").hidden`, `$("renameFolderError").textContent`.

<a id="symbol-toggleCalendarCompact"></a>

## toggleCalendarCompact

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleCalendarCompact(button)
```

Сохраняет включение или выключение мелкого заказа календаря.

Использует `/api/order-calendar-compact`.

Непосредственные вызовы: `orderRowSaving`, `flushDeadlineComments`, `findListOrder`, `button.getAttribute`, `state.deadlineSaving.add`, `request("/api/order-calendar-compact", { path, id: order.id, revision: folder?.order?.revision ?? Number(button.dataset.revision), calendar_compact: enabled })
      .then`, `request`, `Number`, `notify`, `loadOrders`, `state.deadlineSaving.delete`, `renderStatus`, `renderCardDeadlines`, `hasOrderList`, `renderOrders`, `$`, `[...root.querySelectorAll("[data-order-calendar-compact]")].find(el => el.dataset.orderCalendarCompact === path)?.focus`, `[...root.querySelectorAll("[data-order-calendar-compact]")].find`, `root.querySelectorAll`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.saving`, `button.disabled`, `folder.deadlineConflict`, `folder.deadlineError`.

<a id="symbol-toggleCalendarEventFlag"></a>

## toggleCalendarEventFlag

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleCalendarEventFlag(flag)
```

Сохраняет одну независимую отметку выбранного события.

Использует `/api/invoice-plan-calendar-`, `/api/calendar-`, `/api/order-calendar-`.

Непосредственные вызовы: `state.calendarMoving.has`, `orderRowSaving`, `closeCalendarEventMenu`, `state.calendarMoving.add`, `flag.replaceAll`, `request`, `applyCalendarInvoicePlan`, `applyFreeCalendarEvent`, `applyOrderRecord`, `notify`, `loadOrders`, `state.calendarMoving.delete`, `renderOrders`, `$("calendarViewport").focus`, `$`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-toggleFolder"></a>

## toggleFolder

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleFolder(path, forceOpen = false)
```

Раскрывает или сворачивает ветвь дерева папок.

Использует `state.expanded.has`, `state.expanded.delete`, `loadChildren`.

Непосредственные вызовы: `state.expanded.has`, `state.expanded.delete`, `loadChildren`, `state.expanded.add`, `renderTree`.

<a id="symbol-toggleOrderDeadline"></a>

## toggleOrderDeadline

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleOrderDeadline(button)
```

Сохраняет изменение одной недели срока заказа.

Использует `button.getAttribute`, `flushDeadlineComments`, `changeOrderDeadline`.

Непосредственные вызовы: `button.getAttribute`, `flushDeadlineComments`, `changeOrderDeadline`, `Number`.

<a id="symbol-toggleOrderFavorite"></a>

## toggleOrderFavorite

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleOrderFavorite(path)
```

Сохраняет изменение избранного заказа по текущей версии.

Использует `/api/order-favorite`.

Непосредственные вызовы: `flushDeadlineComments`, `findListOrder`, `orderRowSaving`, `state.favoriteSaving.add`, `hasOrderList`, `renderOrders`, `renderOrderHeading`, `renderCardDeadlines`, `request("/api/order-favorite", { path, revision: order.revision, is_favorite: !order.is_favorite }).then`, `request`, `loadOrders`, `state.favoriteSaving.delete`, `renderFavoriteOrders`, `renderExportState`, `renderStatus`, `focusOrderFavorite`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.saving`.

<a id="symbol-toggleOrderGroup"></a>

## toggleOrderGroup

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function toggleOrderGroup(button)
```

Меняет сворачивание группы и сохраняет выбор интерфейса.

Сохраняет локальную настройку интерфейса через localStorage.

Непосредственные вызовы: `JSON.stringify`, `orderGroupCollapsed`, `state.collapsedOrderGroups.set`, `localStorage.setItem`, `notify`, `applyOrderGroupVisibility`.

<a id="symbol-toggleOrderLink"></a>

## toggleOrderLink

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleOrderLink(identity)
```

Добавляет или снимает выбранную связь в общей группе.

Использует `[...edit.data.items, ...edit.data.candidates].find`, `saveOrderLinksChange`, `edit.data.linked_ids.includes`.

Непосредственные вызовы: `[...edit.data.items, ...edit.data.candidates].find`, `saveOrderLinksChange`, `edit.data.linked_ids.includes`.

Прямые присваивания полям/свойствам: `edit.focusTarget`.

<a id="symbol-toggleOrderMarker"></a>

## toggleOrderMarker

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleOrderMarker(button, kind)
```

Сохраняет изменение одной независимой отметки заказа.

Использует `/api/order-`.

Непосредственные вызовы: `findListOrder`, `orderRowSaving`, `Number`, `button.getAttribute`, `state.markerSaving.add`, `button.setAttribute`, `$("ordersTableBody").querySelectorAll("[data-order-flag], [data-order-favorite], [data-order-status], [data-order-deadline], [data-order-blue-plus], [data-order-dollar]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`, `applyOrderRecord`, `request`, `loadOrders`, `state.markerSaving.delete`, `hasOrderList`, `renderOrders`, `focusOrderMarker`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

<a id="symbol-toggleSupplierFavorite"></a>

## toggleSupplierFavorite

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function toggleSupplierFavorite(path)
```

Сохраняет изменение избранного раздела поставщика.

Использует `/api/work-supplier-favorite`.

Непосредственные вызовы: `folder?.directories.find`, `state.supplierFavoriteSaving.has`, `state.supplierFavoriteSaving.add`, `renderSubfolders`, `request`, `state.supplierFavoriteSaving.delete`, `refreshSupplierFavorites`, `loadOrders`, `focusSupplierStar`.

Прямые присваивания полям/свойствам: `state.supplierFavoriteFocus`, `item.supplierFavorite`.

<a id="symbol-treeMarkup"></a>

## treeMarkup

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function treeMarkup(nodes, depth = 0, searching = false)
```

Строит разметку ветвей дерева из полученных узлов.

Использует `nodes.map`.

Непосредственные вызовы: `nodes.map((node, index) => {
    const open = searching ? Boolean(node.children?.length) : state.expanded.has(node.path);
    const children = searching ? node.children || [] : state.children.get(node.path) || [];
    const selected = node.path === state.selected;
    const tabIndex = selected || (!state.selected && depth === 0 && index === 0) ? 0 : -1;
    return '<div class="tree-branch" role="none"><div class="tree-row' + (selected ? " selected" : "") + (node.inactive ? " inactive" : "") +
      '" role="treeitem" tabindex="' + tabIndex + '" aria-selected="' + selected + '"' +
      (node.hasChildren ? ' aria-expanded="' + open + '"' : "") + ' aria-level="' + (depth + 1) +
      '" data-path="' + escapeHtml(node.path) + '" style="--depth:' + depth + '" title="' + escapeHtml(node.name + (node.inactive ? " · Неактивная папка" : "")) + '">' +
      '<button class="tree-toggle' + (open ? " expanded" : "") + '" tabindex="-1" aria-label="' +
      (open ? "Свернуть " : "Раскрыть ") + escapeHtml(node.name) + '"' + (!node.hasChildren ? ' disabled aria-hidden="true"' : "") + ">" +
      icon("chevron") + "</button>" + icon("folder") + '<span class="tree-name">' + escapeHtml(node.name) +
      '</span></div>' + (open && children.length ? '<div role="group">' + treeMarkup(children, depth + 1, searching) + "</div>" : "") + "</div>";
  }).join`, `nodes.map`.

<a id="symbol-treeUrl"></a>

## treeUrl

[static/app.js](../../../static/app.js) · `ArrowFunctionExpression`.

```javascript
const treeUrl = (path = "", extra = {}) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `/api/tree`.

Непосредственные вызовы: `apiUrl`.

<a id="symbol-updateFileCommentCaption"></a>

## updateFileCommentCaption

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function updateFileCommentCaption(path, text, key)
```

Обновляет подпись комментария у соответствующей карточки файла.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `state.folder?.files.find`, `[...document.querySelectorAll("#files [data-file], #orderFileFolders [data-file]")].find`, `document.querySelectorAll`, `button.querySelector`, `text.trim`, `caption?.remove`, `document.createElement`, `button.appendChild`.

Прямые присваивания полям/свойствам: `file.comment`, `caption.className`, `caption.textContent`.

<a id="symbol-updateFolderActivity"></a>

## updateFolderActivity

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function updateFolderActivity(folder, activity)
```

Применяет подтверждённую активность к локальному состоянию интерфейса.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

Прямые присваивания полям/свойствам: `folder[folder.objectActivity ? "objectActivity" : "clientActivity"]`.

<a id="symbol-updatePurchaseSupplierButtons"></a>

## updatePurchaseSupplierButtons

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
function updatePurchaseSupplierButtons()
```

Обновляет назначения строки закупки в существующем редакторе.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `focused?.closest`, `document.querySelector`, `$("purchaseList").querySelectorAll`, `$`, `Number`, `row.querySelector`, `purchaseSupplierButtons`, `$("purchaseList").querySelector`, `([...(row?.querySelectorAll("[data-purchase-supplier]") || [])].find(button => button.dataset.purchaseSupplier === name) || row?.querySelector(".todo-text"))?.focus`, `[...(row?.querySelectorAll("[data-purchase-supplier]") || [])].find`, `row?.querySelectorAll`, `row?.querySelector`.

Прямые присваивания полям/свойствам: `group.innerHTML`, `document.querySelector(".content-pane").scrollTop`.

<a id="symbol-uploadFiles"></a>

## uploadFiles

[static/app.js](../../../static/app.js) · `FunctionDeclaration`.

```javascript
async function uploadFiles(files)
```

Последовательно загружает выбранные файлы с сохранением отдельных результатов.

Использует `notify`, `$`, `renderUpload`.

Непосредственные вызовы: `notify`, `$`, `renderUpload`, `Error`, `formatSize`, `job.results.push`, `sendUpload`, `files.slice`, `job.results.some`, `refreshUploadedFiles(job).catch`, `refreshUploadedFiles`.

Прямые присваивания полям/свойствам: `state.upload`, `$("uploadDetails").open`, `job.index`, `job.filename`, `job.size`, `job.sent`, `job.busy`.
