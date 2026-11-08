# static/home-calendar.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/home-calendar.js](../../../static/home-calendar.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-activeOrderDays"></a>

## activeOrderDays

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const activeOrderDays = (order) =>
```

Отбирает дни событий без выполнения и неактуальности.

Использует `Object.keys(order.calendar_events || {}).filter`, `Object.keys`.

Непосредственные вызовы: `Object.keys(order.calendar_events || {}).filter`, `Object.keys`.

<a id="symbol-calendarRange"></a>

## calendarRange

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function calendarRange(now = new Date(), calendarOrders = [], freeEvents = [], plans = [], history = false)
```

Выбирает недели календаря; прошлые без открытых событий доступны только в истории.

Текущая и будущие недели непрерывны; пустые промежутки прошлого пропускаются.

Непосредственные вызовы: `moscowDate`, `monday`, `dateKey`, `Set`, `shiftDays`, `visibleOrderWeeks`, `include`, `["day", "week"].includes`, `pendingRecord`, `[...past].sort`, `weeks.push`.

<a id="symbol-calendarRange.include"></a>

## calendarRange.include

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const include = (key, period = "day") =>
```

Добавляет корректную дату или неделю в вычисляемый диапазон.

Использует `/^\d{4}-\d{2}-\d{2}$/.test`, `Date`, `Number.isFinite`.

Непосредственные вызовы: `/^\d{4}-\d{2}-\d{2}$/.test`, `Date`, `Number.isFinite`, `date.getTime`, `dateKey`, `date.getUTCDay`, `monday`, `shiftDays`, `past.add`.

<a id="symbol-carryoverHeader"></a>

## carryoverHeader

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function carryoverHeader(week)
```

Строит область планов или ручных переносов платежей.

Использует `document.createElement`, `dateKey`, `area.setAttribute`.

Непосредственные вызовы: `document.createElement`, `dateKey`, `area.setAttribute`, `fullDate.format`, `payments.append`, `area.append`.

Прямые присваивания полям/свойствам: `area.className`, `area.dataset.period`, `area.dataset.date`, `payments.className`, `column.className`, `column.dataset.planColumn`.

<a id="symbol-createSnapshot"></a>

## createSnapshot

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function createSnapshot(now = new Date())
```

Создаёт отдельный DOM календаря для рендера общего PNG.

Исключает строки прошлой истории и их пустые заголовки, сохраняя группировку и подписи.

Непосредственные вызовы: `snapshotRange`, `document.createElement`, `snapshot.setAttribute`, `fullDate.format`, `snapshot.append`, `get("homeCalendar").querySelector(".calendar-weekdays").cloneNode`, `get("homeCalendar").querySelector`, `get`, `dateKey`, `shiftDays`, `[...get("calendarWeeks").children].find`, `Error`, `row.cloneNode`, `Set`, `orders.filter(order => visibleOrderWeeks(order, moscowDate(now)).includes(key)).map`, `orders.filter`, `clone.querySelectorAll`, `visible.has`, `item.remove`, `heading.remove`, `snapshot.querySelectorAll`, `element.removeAttribute`.

Прямые присваивания полям/свойствам: `snapshot.className`, `snapshot.inert`, `title.textContent`.

<a id="symbol-dateKey"></a>

## dateKey

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const dateKey = (date) =>
```

Формирует ключ гражданской даты YYYY-MM-DD.

Использует `date.toISOString().slice`, `date.toISOString`.

Непосредственные вызовы: `date.toISOString().slice`, `date.toISOString`.

<a id="symbol-fitViewport"></a>

## fitViewport

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function fitViewport(index)
```

Подгоняет высоту окна календаря под две полные недели.

Использует `weekHeights.slice(index, index + VISIBLE_WEEKS).reduce`, `weekHeights.slice`, `get`.

Непосредственные вызовы: `weekHeights.slice(index, index + VISIBLE_WEEKS).reduce`, `weekHeights.slice`, `get`, `weekHeights.slice(-VISIBLE_WEEKS).reduce`, `Math.max`, `Math.round`.

Прямые присваивания полям/свойствам: `weeks.style.paddingBottom`, `viewport.style.height`.

<a id="symbol-get"></a>

## get

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const get = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

<a id="symbol-maxScroll"></a>

## maxScroll

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const maxScroll = () =>
```

Вычисляет максимальную прокрутку календарного контейнера.

Использует `Math.max`, `Math.min`, `get`.

Непосредственные вызовы: `Math.max`, `Math.min`, `get`.

<a id="symbol-measureWeeks"></a>

## measureWeeks

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function measureWeeks()
```

Измеряет текущие высоты недель и их положения.

Использует `[...get("calendarWeeks").children].map`, `get`, `weekHeights.map`.

Непосредственные вызовы: `[...get("calendarWeeks").children].map`, `get`, `weekHeights.map`.

<a id="symbol-monday"></a>

## monday

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const monday = (date) =>
```

Возвращает понедельник недели переданной гражданской даты.

Использует `shiftDays`, `date.getUTCDay`.

Непосредственные вызовы: `shiftDays`, `date.getUTCDay`.

<a id="symbol-moscowDate"></a>

## moscowDate

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const moscowDate = (now) =>
```

Преобразует текущее время в гражданскую дату Москвы.

Использует `Intl.DateTimeFormat`, `Date`.

Непосредственные вызовы: `new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts`, `Intl.DateTimeFormat`, `Date`, `Date.UTC`, `value`.

<a id="symbol-moscowDate.value"></a>

## moscowDate.value

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const value = (name) =>
```

Извлекает форматированное значение ячейки или части даты.

Использует `Number`, `parts.find`.

Непосредственные вызовы: `Number`, `parts.find`.

<a id="symbol-orderGroups"></a>

## orderGroups

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function orderGroups(source)
```

Собирает обычные заказы под заголовками клиентов, поставщиков оставляет отдельными строками.

Сначала возвращает поставщиков; сохраняет порядок внутри частей и точные пути клиентов.

Непосредственные вызовы: `Map`, `Boolean`, `JSON.stringify`, `identity.normalize`, `groups.has`, `groups.set`, `groups.get(key).orders.push`, `groups.get`, `groups.values`, `ordered.filter`.

<a id="symbol-pendingRecord"></a>

## pendingRecord

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const pendingRecord = (event) =>
```

Проверяет отсутствие явных отметок выполнения и неактуальности свободной записи/плана.

Поддерживает SQLite 0/1 и JSON boolean; неизвестные значения не скрывают запись.

Непосредственные вызовы: `[true, 1].includes`.

<a id="symbol-planHeader"></a>

## planHeader

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function planHeader(date, label, period = 'day')
```

Строит область планов или ручных переносов платежей.

Использует `document.createElement`, `fullDate.format`, `shiftDays`.

Непосредственные вызовы: `document.createElement`, `fullDate.format`, `shiftDays`, `dateKey`, `button.setAttribute`, `controls.append`, `payments.append`, `rail.append`, `plans.append`.

Прямые присваивания полям/свойствам: `controls.className`, `button.type`, `button.textContent`, `button.dataset.calendarPaymentAdd`, `button.dataset.calendarDate`, `button.dataset.calendarPeriod`, `button.disabled`, `plans.className`, `plans.dataset.date`, `plans.dataset.period`, `payments.className`, `column.className`, `column.dataset.planColumn`, `rail.className`.

<a id="symbol-renderCompactOrders"></a>

## renderCompactOrders

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function renderCompactOrders(container, compact)
```

Строит прежний плоский список синих ссылок мелких заказов без заголовков клиентов.

Сохраняет подписи, нижнюю левую область, узлы ссылок и фокус без показа скрытых событий.

Непосредственные вызовы: `container.contains`, `Map`, `[...container.children].map`, `Set`, `existing.get`, `document.createElement`, `encodeURIComponent`, `link.setAttribute`, `container.insertBefore`, `retained.add`, `retained.has`, `link.remove`, `(focused.isConnected ? focused : get("calendarViewport")).focus`, `get`.

Прямые присваивания полям/свойствам: `link.className`, `link.href`, `link.dataset.calendarOrder`, `link.textContent`.

<a id="symbol-renderFreeEvents"></a>

## renderFreeEvents

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function renderFreeEvents()
```

Строит свободные события с отдельным значком непустого комментария.

Значок и UUID открывают общее окно просмотра; название, узлы и фокус сохраняются.

Непосредственные вызовы: `get`, `row.querySelector`, `Date`, `events.filter`, `JSON.stringify`, `area.contains`, `Map`, `[...area.querySelectorAll(".has-event")].map`, `area.querySelectorAll`, `Set`, `shiftDays`, `dateKey`, `weekNumber`, `fullDate.format`, `add.setAttribute`, `weekly.filter`, `existing.get`, `document.createElement`, `button.setAttribute`, `showTripMark`, `button.removeAttribute`, `Boolean`, `event.comment.trim`, `button.classList.toggle`, `button.insertAdjacentHTML`, `[0, 1].includes`, `["gray", "red", "orange", "yellow", "green", "blue", "purple"].includes`, `button.classList.contains`, `column.insertBefore`, `retained.add`, `existing.values`, `retained.has`, `button.remove`, `(focused.isConnected ? focused : area.querySelector(".calendar-free-add:not(:disabled)") || get("calendarViewport")).focus`, `area.querySelector`.

Прямые присваивания полям/свойствам: `area.dataset.signature`, `add.dataset.calendarDate`, `add.dataset.calendarPeriod`, `add.disabled`, `button.type`, `button.className`, `button.dataset.calendarEvent`, `button.dataset.calendarFree`, `button.textContent`, `button.dataset.calendarComment`, `button.dataset.calendarColor`, `button.dataset.calendarDate`, `button.dataset.calendarPeriod`, `button.disabled`, `area.parentElement.scrollTop`.

<a id="symbol-renderInvoicePlans"></a>

## renderInvoicePlans

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function renderInvoicePlans()
```

Строит приходы и расходы календаря с сохранёнными отметками.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `Map`, `['incoming', 'outgoing'].includes`, `dateKey`, `monday`, `Date`, `byDate.has`, `byDate.set`, `byDate.get(key).push`, `byDate.get`, `get("calendarWeeks").querySelectorAll`, `get`, `JSON.stringify`, `area.contains`, `[...area.querySelectorAll('.calendar-invoice-plan')].map`, `area.querySelectorAll`, `area.querySelector`, `Object.values(targets).map`, `Object.values`, `Set`, `existing.get`, `document.createElement`, `new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format`, `Intl.NumberFormat`, `link.classList.toggle`, `link.setAttribute`, `link.replaceChildren`, `showTripMark`, `showTodoMark`, `Boolean`, `encodeURIComponent`, `fullDate.format`, `shiftDays`, `[payment && plan.is_notified === true ? 'Сообщил' : '', plan.is_carryover === true ? 'Перенос слева' : '', plan.is_watch_todos === true ? 'Смотри ту-ду' : '', plan.is_completed === true ? 'Выполнено' : '', plan.is_trip === true ? 'Выезд' : '', plan.is_inactive === true ? 'Неактуально' : '', label, signedAmount ? signedAmount + ' ₽' : '', plan.text, plan.invoice_label, plan.title, plan.client, plan.object, periodLabel].filter(Boolean).join`, `[payment && plan.is_notified === true ? 'Сообщил' : '', plan.is_carryover === true ? 'Перенос слева' : '', plan.is_watch_todos === true ? 'Смотри ту-ду' : '', plan.is_completed === true ? 'Выполнено' : '', plan.is_trip === true ? 'Выезд' : '', plan.is_inactive === true ? 'Неактуально' : '', label, signedAmount ? signedAmount + ' ₽' : '', plan.text, plan.invoice_label, plan.title, plan.client, plan.object, periodLabel].filter`, `before.get`, `target.insertBefore`, `before.set`, `retained.add`, `existing.values`, `retained.has`, `link.remove`, `(focused.isConnected ? focused : get('calendarViewport')).focus`, `sizeInvoicePlanHeaders`.

Прямые присваивания полям/свойствам: `area.dataset.signature`, `link.className`, `link.type`, `link.dataset.invoicePlan`, `link.dataset.operation`, `link.dataset.calendarDate`, `link.dataset.calendarPeriod`, `value.className`, `value.textContent`, `caption.className`, `caption.textContent`, `link.href`, `link.dataset.calendarOrder`, `link.dataset.calendarPlanEdit`, `link.title`.

<a id="symbol-renderWeekOrders"></a>

## renderWeekOrders

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function renderWeekOrders()
```

Строит заголовки клиентов обычных заказов и отдельные строки поставщиков.

Переиспользует узлы строк и групп, сохраняя фокус, прокрутку и привязку событий.

Непосредственные вызовы: `Map`, `visibleOrderWeeks`, `byWeek.has`, `byWeek.set`, `byWeek.get(week).push`, `byWeek.get`, `get`, `row.querySelector`, `eligible.filter`, `renderCompactOrders`, `JSON.stringify`, `weekly.map`, `list.contains`, `[...list.children].map`, `[...list.querySelectorAll(".calendar-order-group")].map`, `list.querySelectorAll`, `Set`, `orderGroups`, `headings.get`, `document.createElement`, `updateGroupHeading`, `list.insertBefore`, `retained.add`, `Boolean`, `existing.get`, `markers.setAttribute`, `orderMarkers.map((marker) => '<span class="calendar-order-marker calendar-order-' + marker.name + '">' + marker.content + '</span>').join`, `orderMarkers.map`, `link.append`, `item.append`, `item.classList.toggle`, `item.style.setProperty`, `String`, `item.style.removeProperty`, `orderMarkers.filter`, `orderMarkers.forEach`, `encodeURIComponent`, `link.setAttribute`, `[group.label, title, order.object, ...activeMarkers.map((marker) => marker.label)].filter(Boolean).join`, `[group.label, title, order.object, ...activeMarkers.map((marker) => marker.label)].filter`, `activeMarkers.map`, `link.querySelector`, `Date`, `shiftDays`, `dateKey`, `slot.classList.toggle`, `showTripMark`, `order.calendar_trip?.[isWeek ? "week" : "day"]?.includes`, `showTodoMark`, `order.calendar_watch_todos?.[isWeek ? "week" : "day"]?.includes`, `order.calendar_inactive?.[isWeek ? "week" : "day"]?.includes`, `order.calendar_completed?.[isWeek ? "week" : "day"]?.includes`, `Array.isArray`, `order.deadline_weeks.includes`, `slot.setAttribute`, `slot.removeAttribute`, `weekNumber`, `fullDate.format`, `slot.classList.contains`, `retained.has`, `item.remove`, `list.append`, `(focused.isConnected ? focused : list.querySelector("a") || get("calendarViewport")).focus`, `list.querySelector`.

Прямые присваивания полям/свойствам: `list.dataset.signature`, `item.dataset.orderKey`, `item.className`, `link.className`, `markers.className`, `markers.innerHTML`, `title.className`, `client.className`, `object.className`, `slot.type`, `slot.className`, `item.dataset.groupKey`, `markers.hidden`, `link.href`, `link.dataset.calendarOrder`, `link.querySelector(".calendar-order-title").textContent`, `client.textContent`, `client.hidden`, `object.textContent`, `object.hidden`, `slot.dataset.calendarEvent`, `slot.dataset.calendarDate`, `slot.dataset.calendarPeriod`, `slot.dataset.calendarColor`, `slot.textContent`, `slot.disabled`, `empty.className`, `empty.textContent`, `list.parentElement.scrollTop`.

<a id="symbol-scrollToIndex"></a>

## scrollToIndex

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function scrollToIndex(index)
```

Прокручивает календарь к началу выбранной недели.

Использует `Math.max`, `Math.min`, `fitViewport`.

Непосредственные вызовы: `Math.max`, `Math.min`, `fitViewport`, `get("calendarViewport").scrollTo`, `get`, `maxScroll`, `updateHeading`.

<a id="symbol-scrollToWeek"></a>

## scrollToWeek

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function scrollToWeek(date)
```

Показывает заданную неделю или ближайшую следующую сохранившуюся неделю.

Поиск по ключам поддерживает пропущенные закрытые недели прошлого.

Непосредственные вызовы: `dateKey`, `monday`, `range.weeks.findIndex`, `scrollToIndex`.

<a id="symbol-shiftDays"></a>

## shiftDays

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const shiftDays = (date, days) =>
```

Сдвигает гражданскую UTC-дату на заданное число суток.

Использует `Date`, `date.getTime`.

Непосредственные вызовы: `Date`, `date.getTime`.

<a id="symbol-show"></a>

## show

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function show(nextOrders, nextEvents, nextInvoicePlans, now = new Date())
```

Показывает компонент по полученным данным и текущему состоянию в модуле календарной сетки.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `Array.isArray`, `calendarRange`, `dateKey`, `range.weeks.join`, `nextRange.weeks.join`, `get`, `weekIndex`, `Date`, `Map`, `[...weeks.children].map`, `weeks.contains`, `Set`, `retained.has`, `row.remove`, `existing.get`, `document.createElement`, `orderCell.append`, `carryoverHeader`, `list.setAttribute`, `fullDate.format`, `shiftDays`, `spacer.setAttribute`, `free.append`, `cell.append`, `content.append`, `row.append`, `weekNumber`, `weekLabel.setAttribute`, `weekCell.append`, `planHeader`, `label.setAttribute`, `String`, `date.getUTCDate`, `row.querySelectorAll`, `label.classList.toggle`, `label.removeAttribute`, `weeks.insertBefore`, `viewport.focus`, `measureWeeks`, `scrollToWeek`, `Math.max`, `Math.min`, `maxScroll`, `updateHeading`, `renderWeekOrders`, `renderFreeEvents`, `renderInvoicePlans`, `get("calendarToday").addEventListener`, `get("calendarEarlier").addEventListener`, `get("calendarLater").addEventListener`, `history.addEventListener`, `viewport.addEventListener`, `ResizeObserver`, `observer.observe`.

Прямые присваивания полям/свойствам: `row.className`, `row.dataset.week`, `orderCell.className`, `orderCell.style.gridArea`, `content.className`, `list.className`, `free.className`, `spacer.className`, `cell.className`, `add.type`, `add.className`, `add.dataset.calendarEvent`, `add.dataset.calendarFree`, `add.textContent`, `weekCell.className`, `weekCell.style.gridArea`, `weekLabel.className`, `weekLabel.textContent`, `cell.style.gridArea`, `label.dateTime`, `label.textContent`, `viewport.scrollTop`.

<a id="symbol-showTodoMark"></a>

## showTodoMark

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function showTodoMark(element, marked, path)
```

Добавляет или снимает значок просмотра задач у события заказа.

Использует `element.classList.toggle`, `element.setAttribute`, `element.insertAdjacentHTML`.

Непосредственные вызовы: `element.classList.toggle`, `element.setAttribute`, `element.insertAdjacentHTML`, `element.removeAttribute`.

Прямые присваивания полям/свойствам: `element.dataset.calendarTodos`.

<a id="symbol-showTripMark"></a>

## showTripMark

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function showTripMark(element, marked)
```

Добавляет или снимает значок выезда у события календаря.

Использует `element.classList.toggle`, `element.insertAdjacentHTML`.

Непосредственные вызовы: `element.classList.toggle`, `element.insertAdjacentHTML`.

<a id="symbol-sizeInvoicePlanHeaders"></a>

## sizeInvoicePlanHeaders

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function sizeInvoicePlanHeaders()
```

Выравнивает высоту шапки оплат по наполнению недель.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `get`, `[...get('calendarWeeks').children].some`, `weekIndex`, `get('calendarWeeks').querySelectorAll`, `parseFloat`, `getComputedStyle`, `Math.max`, `[...row.querySelectorAll('.calendar-invoice-plans')].map`, `row.querySelectorAll`, `row.style.getPropertyValue`, `row.querySelector`, `row.style.setProperty`, `measureWeeks`, `weekHeights.some`, `fitViewport`, `Math.min`, `maxScroll`, `updateHeading`.

Прямые присваивания полям/свойствам: `amount.style.fontSize`, `content.scrollTop`, `viewport.scrollTop`.

<a id="symbol-snapshotRange"></a>

## snapshotRange

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function snapshotRange(now = new Date(), calendarOrders = orders, freeEvents = events, plans = invoicePlans)
```

Выбирает две или три недели снимка независимо от просмотра истории.

Предыдущую неделю удерживает только видимое актуальное невыполненное событие.

Непосредственные вызовы: `moscowDate`, `monday`, `dateKey`, `shiftDays`, `calendarOrders.some`, `[...freeEvents, ...plans].some`.

<a id="symbol-updateGroupHeading"></a>

## updateGroupHeading

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function updateGroupHeading(heading, group)
```

Обновляет отдельную строку заголовка клиентской группы календаря.

Название выводится безопасным текстом; поставщикам заголовки не создаются.

Непосредственные вызовы: `document.createElement`, `label.setAttribute`, `heading.append`.

Прямые присваивания полям/свойствам: `heading.className`, `heading.dataset.groupKey`, `heading.firstElementChild.textContent`, `heading.firstElementChild.title`.

<a id="symbol-updateHeading"></a>

## updateHeading

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function updateHeading()
```

Обновляет заголовок и доступность навигации календаря.

Использует `get`, `[...get("calendarWeeks").children].some`, `maxScroll`.

Непосредственные вызовы: `get`, `[...get("calendarWeeks").children].some`, `maxScroll`, `weekIndex`, `fitViewport`, `Date`, `shiftDays`, `Math.min`, `viewport.setAttribute`, `fullDate.format`, `first.getUTCMonth`, `last.getUTCMonth`, `first.getUTCFullYear`, `last.getUTCFullYear`, `monthName.format`.

Прямые присваивания полям/свойствам: `viewport.scrollTop`, `get("calendarTitle").textContent`, `get("calendarEarlier").disabled`, `get("calendarLater").disabled`.

<a id="symbol-visibleOrderWeeks"></a>

## visibleOrderWeeks

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function visibleOrderWeeks(order, today, history = false)
```

Вычисляет недели строк заказа; просмотр истории возвращает закрытые прошлые записи.

Не меняет сроки и отметки; снятые недельные тексты доступны только в прошлой истории.

Непосредственные вызовы: `dateKey`, `monday`, `Set`, `activeOrderDays`, `Object.keys(order.calendar_events || {}).filter`, `Object.keys`, `eventDays.map`, `Object.keys(order.calendar_week_events || {}).filter`, `weeks.filter`.

<a id="symbol-weekIndex"></a>

## weekIndex

[static/home-calendar.js](../../../static/home-calendar.js) · `FunctionDeclaration`.

```javascript
function weekIndex(top)
```

Находит неделю, соответствующую текущей позиции прокрутки.

Использует `Math.min`, `Math.max`.

Непосредственные вызовы: `Math.min`, `Math.max`.

<a id="symbol-weekNumber"></a>

## weekNumber

[static/home-calendar.js](../../../static/home-calendar.js) · `ArrowFunctionExpression`.

```javascript
const weekNumber = (date) =>
```

Вычисляет ISO-номер недели через её четверг.

Использует `shiftDays`, `monday`, `Math.ceil`.

Непосредственные вызовы: `shiftDays`, `monday`, `Math.ceil`, `Date`, `Date.UTC`, `thursday.getUTCFullYear`.
