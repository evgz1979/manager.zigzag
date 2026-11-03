# static/home-calendar.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/home-calendar.js:1](../../../static/home-calendar.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## showTripMark

[static/home-calendar.js:14](../../../static/home-calendar.js#L14) · `FunctionDeclaration`.

```javascript
function showTripMark(element, marked)
```

Добавляет или снимает значок выезда у события календаря.

Использует `element.classList.toggle`, `element.insertAdjacentHTML`.

Непосредственные вызовы: `element.classList.toggle`, `element.insertAdjacentHTML`.

## showTodoMark

[static/home-calendar.js:20](../../../static/home-calendar.js#L20) · `FunctionDeclaration`.

```javascript
function showTodoMark(element, marked, path)
```

Добавляет или снимает значок просмотра задач у события заказа.

Использует `element.classList.toggle`, `element.setAttribute`, `element.insertAdjacentHTML`.

Непосредственные вызовы: `element.classList.toggle`, `element.setAttribute`, `element.insertAdjacentHTML`, `element.removeAttribute`.

Прямые присваивания полям/свойствам: `element.dataset.calendarTodos`.

## dateKey

[static/home-calendar.js:33](../../../static/home-calendar.js#L33) · `ArrowFunctionExpression`.

```javascript
const dateKey = (date) =>
```

Формирует ключ гражданской даты YYYY-MM-DD.

Использует `date.toISOString().slice`, `date.toISOString`.

Непосредственные вызовы: `date.toISOString().slice`, `date.toISOString`.

## shiftDays

[static/home-calendar.js:36](../../../static/home-calendar.js#L36) · `ArrowFunctionExpression`.

```javascript
const shiftDays = (date, days) =>
```

Сдвигает гражданскую UTC-дату на заданное число суток.

Использует `Date`, `date.getTime`.

Непосредственные вызовы: `Date`, `date.getTime`.

## monday

[static/home-calendar.js:39](../../../static/home-calendar.js#L39) · `ArrowFunctionExpression`.

```javascript
const monday = (date) =>
```

Возвращает понедельник недели переданной гражданской даты.

Использует `shiftDays`, `date.getUTCDay`.

Непосредственные вызовы: `shiftDays`, `date.getUTCDay`.

## weekNumber

[static/home-calendar.js:42](../../../static/home-calendar.js#L42) · `ArrowFunctionExpression`.

```javascript
const weekNumber = (date) =>
```

Вычисляет ISO-номер недели через её четверг.

Использует `shiftDays`, `monday`, `Math.ceil`.

Непосредственные вызовы: `shiftDays`, `monday`, `Math.ceil`, `Date`, `Date.UTC`, `thursday.getUTCFullYear`.

## moscowDate

[static/home-calendar.js:48](../../../static/home-calendar.js#L48) · `ArrowFunctionExpression`.

```javascript
const moscowDate = (now) =>
```

Преобразует текущее время в гражданскую дату Москвы.

Использует `Intl.DateTimeFormat`, `Date`.

Непосредственные вызовы: `new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts`, `Intl.DateTimeFormat`, `Date`, `Date.UTC`, `value`.

## value

[static/home-calendar.js:52](../../../static/home-calendar.js#L52) · `ArrowFunctionExpression`.

```javascript
const value = (name) =>
```

Извлекает форматированное значение ячейки или части даты.

Использует `Number`, `parts.find`.

Непосредственные вызовы: `Number`, `parts.find`.

## activeOrderDays

[static/home-calendar.js:57](../../../static/home-calendar.js#L57) · `ArrowFunctionExpression`.

```javascript
const activeOrderDays = (order) =>
```

Отбирает дни событий без выполнения и неактуальности.

Использует `Object.keys(order.calendar_events || {}).filter`, `Object.keys`.

Непосредственные вызовы: `Object.keys(order.calendar_events || {}).filter`, `Object.keys`.

## visibleOrderWeeks

[static/home-calendar.js:61](../../../static/home-calendar.js#L61) · `FunctionDeclaration`.

```javascript
function visibleOrderWeeks(order, today)
```

Вычисляет недели видимых строк заказа по срокам и состоянию событий.

Использует `activeOrderDays(order).map`, `activeOrderDays`, `Set`.

Непосредственные вызовы: `activeOrderDays(order).map`, `activeOrderDays`, `Set`, `dateKey`, `monday`, `weeks.filter`.

## calendarRange

[static/home-calendar.js:80](../../../static/home-calendar.js#L80) · `FunctionDeclaration`.

```javascript
function calendarRange(now = new Date(), calendarOrders = [], freeEvents = [], plans = [])
```

Расширяет диапазон календаря по сохранённым срокам и видимым событиям.

Использует `moscowDate`, `monday`, `shiftDays`.

Непосредственные вызовы: `moscowDate`, `monday`, `shiftDays`, `include`, `activeOrderDays`, `["day", "week"].includes`.

## include

[static/home-calendar.js:85](../../../static/home-calendar.js#L85) · `ArrowFunctionExpression`.

```javascript
const include = (key, period = "day") =>
```

Добавляет корректную дату или неделю в вычисляемый диапазон.

Использует `/^\d{4}-\d{2}-\d{2}$/.test`, `Date`, `Number.isFinite`.

Непосредственные вызовы: `/^\d{4}-\d{2}-\d{2}$/.test`, `Date`, `Number.isFinite`, `date.getTime`, `dateKey`, `date.getUTCDay`, `monday`, `shiftDays`.

## get

[static/home-calendar.js:109](../../../static/home-calendar.js#L109) · `ArrowFunctionExpression`.

```javascript
const get = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

## maxScroll

[static/home-calendar.js:114](../../../static/home-calendar.js#L114) · `ArrowFunctionExpression`.

```javascript
const maxScroll = () =>
```

Вычисляет максимальную прокрутку календарного контейнера.

Использует `Math.max`, `Math.min`, `get`.

Непосредственные вызовы: `Math.max`, `Math.min`, `get`.

## measureWeeks

[static/home-calendar.js:119](../../../static/home-calendar.js#L119) · `FunctionDeclaration`.

```javascript
function measureWeeks()
```

Измеряет текущие высоты недель и их положения.

Использует `[...get("calendarWeeks").children].map`, `get`, `weekHeights.map`.

Непосредственные вызовы: `[...get("calendarWeeks").children].map`, `get`, `weekHeights.map`.

## weekIndex

[static/home-calendar.js:127](../../../static/home-calendar.js#L127) · `FunctionDeclaration`.

```javascript
function weekIndex(top)
```

Находит неделю, соответствующую текущей позиции прокрутки.

Использует `Math.min`, `Math.max`.

Непосредственные вызовы: `Math.min`, `Math.max`.

## fitViewport

[static/home-calendar.js:135](../../../static/home-calendar.js#L135) · `FunctionDeclaration`.

```javascript
function fitViewport(index)
```

Подгоняет высоту окна календаря под две полные недели.

Использует `weekHeights.slice(index, index + VISIBLE_WEEKS).reduce`, `weekHeights.slice`, `get`.

Непосредственные вызовы: `weekHeights.slice(index, index + VISIBLE_WEEKS).reduce`, `weekHeights.slice`, `get`, `weekHeights.slice(-VISIBLE_WEEKS).reduce`, `Math.max`, `Math.round`.

Прямые присваивания полям/свойствам: `weeks.style.paddingBottom`, `viewport.style.height`.

## scrollToIndex

[static/home-calendar.js:149](../../../static/home-calendar.js#L149) · `FunctionDeclaration`.

```javascript
function scrollToIndex(index)
```

Прокручивает календарь к началу выбранной недели.

Использует `Math.max`, `Math.min`, `fitViewport`.

Непосредственные вызовы: `Math.max`, `Math.min`, `fitViewport`, `get("calendarViewport").scrollTo`, `get`, `maxScroll`, `updateHeading`.

## updateHeading

[static/home-calendar.js:158](../../../static/home-calendar.js#L158) · `FunctionDeclaration`.

```javascript
function updateHeading()
```

Обновляет заголовок и доступность навигации календаря.

Использует `get`, `[...get("calendarWeeks").children].some`, `maxScroll`.

Непосредственные вызовы: `get`, `[...get("calendarWeeks").children].some`, `maxScroll`, `weekIndex`, `fitViewport`, `shiftDays`, `viewport.setAttribute`, `fullDate.format`, `first.getUTCMonth`, `last.getUTCMonth`, `first.getUTCFullYear`, `last.getUTCFullYear`, `monthName.format`.

Прямые присваивания полям/свойствам: `viewport.scrollTop`, `get("calendarTitle").textContent`, `get("calendarEarlier").disabled`, `get("calendarLater").disabled`.

## scrollToWeek

[static/home-calendar.js:180](../../../static/home-calendar.js#L180) · `FunctionDeclaration`.

```javascript
function scrollToWeek(date)
```

Находит неделю по ключу и показывает её в окне календаря.

Использует `scrollToIndex`, `Math.round`, `monday`.

Непосредственные вызовы: `scrollToIndex`, `Math.round`, `monday`.

## renderWeekOrders

[static/home-calendar.js:186](../../../static/home-calendar.js#L186) · `FunctionDeclaration`.

```javascript
function renderWeekOrders()
```

Строит обычные строки заказов и их события выбранной недели.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `Map`, `visibleOrderWeeks`, `byWeek.has`, `byWeek.set`, `byWeek.get(week).push`, `byWeek.get`, `get`, `row.querySelector`, `eligible.filter`, `renderCompactOrders`, `JSON.stringify`, `weekly.map`, `list.contains`, `[...list.children].map`, `Set`, `Boolean`, `existing.get`, `document.createElement`, `markers.setAttribute`, `orderMarkers.map((marker) => '<span class="calendar-order-marker calendar-order-' + marker.name + '">' + marker.content + '</span>').join`, `orderMarkers.map`, `link.append`, `item.append`, `item.classList.toggle`, `item.style.setProperty`, `String`, `item.style.removeProperty`, `orderMarkers.filter`, `orderMarkers.forEach`, `encodeURIComponent`, `link.setAttribute`, `[...(supplier ? [order.work_supplier, title] : [title, order.client]), order.object, ...activeMarkers.map((marker) => marker.label)].filter(Boolean).join`, `[...(supplier ? [order.work_supplier, title] : [title, order.client]), order.object, ...activeMarkers.map((marker) => marker.label)].filter`, `activeMarkers.map`, `link.querySelector`, `Date`, `shiftDays`, `dateKey`, `slot.classList.toggle`, `showTripMark`, `order.calendar_trip?.[isWeek ? "week" : "day"]?.includes`, `showTodoMark`, `order.calendar_watch_todos?.[isWeek ? "week" : "day"]?.includes`, `order.calendar_inactive?.[isWeek ? "week" : "day"]?.includes`, `order.calendar_completed?.[isWeek ? "week" : "day"]?.includes`, `Array.isArray`, `order.deadline_weeks.includes`, `slot.setAttribute`, `slot.removeAttribute`, `weekNumber`, `fullDate.format`, `slot.classList.contains`, `list.insertBefore`, `retained.add`, `retained.has`, `item.remove`, `list.append`, `(focused.isConnected ? focused : list.querySelector("a") || get("calendarViewport")).focus`, `list.querySelector`.

Прямые присваивания полям/свойствам: `list.dataset.signature`, `item.dataset.orderKey`, `item.className`, `link.className`, `markers.className`, `markers.innerHTML`, `title.className`, `client.className`, `slot.type`, `slot.className`, `markers.hidden`, `link.href`, `link.dataset.calendarOrder`, `link.querySelector(".calendar-order-title").textContent`, `client.textContent`, `client.hidden`, `slot.dataset.calendarEvent`, `slot.dataset.calendarDate`, `slot.dataset.calendarPeriod`, `slot.dataset.calendarColor`, `slot.textContent`, `slot.disabled`, `empty.className`, `empty.textContent`, `list.parentElement.scrollTop`.

## renderCompactOrders

[static/home-calendar.js:293](../../../static/home-calendar.js#L293) · `FunctionDeclaration`.

```javascript
function renderCompactOrders(container, compact)
```

Строит синие ссылки мелких заказов в первой колонке недели.

Использует `Map`, `[...container.children].map`, `Set`.

Непосредственные вызовы: `Map`, `[...container.children].map`, `Set`, `existing.get`, `document.createElement`, `encodeURIComponent`, `link.setAttribute`, `container.insertBefore`, `retained.add`, `container.contains`, `retained.has`, `link.remove`, `get("calendarViewport").focus`, `get`.

Прямые присваивания полям/свойствам: `link.className`, `link.href`, `link.dataset.calendarOrder`, `link.textContent`.

## renderFreeEvents

[static/home-calendar.js:316](../../../static/home-calendar.js#L316) · `FunctionDeclaration`.

```javascript
function renderFreeEvents()
```

Строит свободные дневные и недельные события.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `get`, `row.querySelector`, `Date`, `events.filter`, `JSON.stringify`, `area.contains`, `Map`, `[...area.querySelectorAll(".has-event")].map`, `area.querySelectorAll`, `Set`, `shiftDays`, `dateKey`, `weekNumber`, `fullDate.format`, `add.setAttribute`, `weekly.filter`, `existing.get`, `document.createElement`, `button.setAttribute`, `showTripMark`, `button.classList.toggle`, `[0, 1].includes`, `["gray", "red", "orange", "yellow", "green", "blue", "purple"].includes`, `button.classList.contains`, `column.insertBefore`, `retained.add`, `existing.values`, `retained.has`, `button.remove`, `(focused.isConnected ? focused : area.querySelector(".calendar-free-add:not(:disabled)") || get("calendarViewport")).focus`, `area.querySelector`.

Прямые присваивания полям/свойствам: `area.dataset.signature`, `add.dataset.calendarDate`, `add.dataset.calendarPeriod`, `add.disabled`, `button.type`, `button.className`, `button.dataset.calendarEvent`, `button.dataset.calendarFree`, `button.textContent`, `button.dataset.calendarColor`, `button.dataset.calendarDate`, `button.dataset.calendarPeriod`, `button.disabled`, `area.parentElement.scrollTop`.

## renderInvoicePlans

[static/home-calendar.js:369](../../../static/home-calendar.js#L369) · `FunctionDeclaration`.

```javascript
function renderInvoicePlans()
```

Строит приходы и расходы календаря с сохранёнными отметками.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `Map`, `['incoming', 'outgoing'].includes`, `dateKey`, `monday`, `Date`, `byDate.has`, `byDate.set`, `byDate.get(key).push`, `byDate.get`, `get("calendarWeeks").querySelectorAll`, `get`, `JSON.stringify`, `area.contains`, `[...area.querySelectorAll('.calendar-invoice-plan')].map`, `area.querySelectorAll`, `area.querySelector`, `Object.values(targets).map`, `Object.values`, `Set`, `existing.get`, `document.createElement`, `new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format`, `Intl.NumberFormat`, `link.classList.toggle`, `link.setAttribute`, `link.replaceChildren`, `showTripMark`, `showTodoMark`, `Boolean`, `encodeURIComponent`, `fullDate.format`, `shiftDays`, `[plan.is_carryover === true ? 'Перенос слева' : '', plan.is_watch_todos === true ? 'Смотри ту-ду' : '', plan.is_completed === true ? 'Выполнено' : '', plan.is_trip === true ? 'Выезд' : '', plan.is_inactive === true ? 'Неактуально' : '', label, signedAmount ? signedAmount + ' ₽' : '', plan.text, plan.invoice_label, plan.title, plan.client, plan.object, periodLabel].filter(Boolean).join`, `[plan.is_carryover === true ? 'Перенос слева' : '', plan.is_watch_todos === true ? 'Смотри ту-ду' : '', plan.is_completed === true ? 'Выполнено' : '', plan.is_trip === true ? 'Выезд' : '', plan.is_inactive === true ? 'Неактуально' : '', label, signedAmount ? signedAmount + ' ₽' : '', plan.text, plan.invoice_label, plan.title, plan.client, plan.object, periodLabel].filter`, `before.get`, `target.insertBefore`, `before.set`, `retained.add`, `existing.values`, `retained.has`, `link.remove`, `(focused.isConnected ? focused : get('calendarViewport')).focus`, `sizeInvoicePlanHeaders`.

Прямые присваивания полям/свойствам: `area.dataset.signature`, `link.className`, `link.type`, `link.dataset.invoicePlan`, `link.dataset.operation`, `link.dataset.calendarDate`, `link.dataset.calendarPeriod`, `value.className`, `value.textContent`, `caption.className`, `caption.textContent`, `link.href`, `link.dataset.calendarOrder`, `link.dataset.calendarPlanEdit`, `link.title`.

## sizeInvoicePlanHeaders

[static/home-calendar.js:432](../../../static/home-calendar.js#L432) · `FunctionDeclaration`.

```javascript
function sizeInvoicePlanHeaders()
```

Выравнивает высоту шапки оплат по наполнению недель.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `get`, `[...get('calendarWeeks').children].some`, `weekIndex`, `get('calendarWeeks').querySelectorAll`, `parseFloat`, `getComputedStyle`, `Math.max`, `[...row.querySelectorAll('.calendar-invoice-plans')].map`, `row.querySelectorAll`, `row.style.getPropertyValue`, `row.querySelector`, `row.style.setProperty`, `measureWeeks`, `weekHeights.some`, `fitViewport`, `Math.min`, `maxScroll`, `updateHeading`.

Прямые присваивания полям/свойствам: `amount.style.fontSize`, `content.scrollTop`, `viewport.scrollTop`.

## planHeader

[static/home-calendar.js:466](../../../static/home-calendar.js#L466) · `FunctionDeclaration`.

```javascript
function planHeader(date, label, period = 'day')
```

Строит область планов или ручных переносов платежей.

Использует `document.createElement`, `fullDate.format`, `shiftDays`.

Непосредственные вызовы: `document.createElement`, `fullDate.format`, `shiftDays`, `dateKey`, `button.setAttribute`, `controls.append`, `payments.append`, `rail.append`, `plans.append`.

Прямые присваивания полям/свойствам: `controls.className`, `button.type`, `button.textContent`, `button.dataset.calendarPaymentAdd`, `button.dataset.calendarDate`, `button.dataset.calendarPeriod`, `button.disabled`, `plans.className`, `plans.dataset.date`, `plans.dataset.period`, `payments.className`, `column.className`, `column.dataset.planColumn`, `rail.className`.

## carryoverHeader

[static/home-calendar.js:495](../../../static/home-calendar.js#L495) · `FunctionDeclaration`.

```javascript
function carryoverHeader(week)
```

Строит область планов или ручных переносов платежей.

Использует `document.createElement`, `dateKey`, `area.setAttribute`.

Непосредственные вызовы: `document.createElement`, `dateKey`, `area.setAttribute`, `fullDate.format`, `payments.append`, `area.append`.

Прямые присваивания полям/свойствам: `area.className`, `area.dataset.period`, `area.dataset.date`, `payments.className`, `column.className`, `column.dataset.planColumn`.

## show

[static/home-calendar.js:511](../../../static/home-calendar.js#L511) · `FunctionDeclaration`.

```javascript
function show(nextOrders, nextEvents, nextInvoicePlans, now = new Date())
```

Показывает компонент по полученным данным и текущему состоянию в модуле календарной сетки.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `Array.isArray`, `calendarRange`, `dateKey`, `get`, `weekIndex`, `shiftDays`, `Map`, `[...weeks.children].map`, `weeks.contains`, `row.remove`, `existing.get`, `document.createElement`, `orderCell.append`, `carryoverHeader`, `list.setAttribute`, `fullDate.format`, `spacer.setAttribute`, `free.append`, `cell.append`, `content.append`, `row.append`, `weekNumber`, `weekLabel.setAttribute`, `weekCell.append`, `planHeader`, `label.setAttribute`, `String`, `date.getUTCDate`, `row.querySelectorAll`, `label.classList.toggle`, `label.removeAttribute`, `weeks.insertBefore`, `viewport.focus`, `measureWeeks`, `scrollToWeek`, `Math.max`, `Math.min`, `maxScroll`, `updateHeading`, `renderWeekOrders`, `renderFreeEvents`, `renderInvoicePlans`, `get("calendarToday").addEventListener`, `get("calendarEarlier").addEventListener`, `get("calendarLater").addEventListener`, `viewport.addEventListener`, `ResizeObserver`, `observer.observe`.

Прямые присваивания полям/свойствам: `row.className`, `row.dataset.week`, `orderCell.className`, `orderCell.style.gridArea`, `content.className`, `list.className`, `free.className`, `spacer.className`, `cell.className`, `add.type`, `add.className`, `add.dataset.calendarEvent`, `add.dataset.calendarFree`, `add.textContent`, `weekCell.className`, `weekCell.style.gridArea`, `weekLabel.className`, `weekLabel.textContent`, `cell.style.gridArea`, `label.dateTime`, `label.textContent`, `viewport.scrollTop`.

## snapshotRange

[static/home-calendar.js:614](../../../static/home-calendar.js#L614) · `FunctionDeclaration`.

```javascript
function snapshotRange(now = new Date(), calendarOrders = orders, freeEvents = events, plans = invoicePlans)
```

Выбирает две или три недели общего снимка по видимому наполнению.

Использует `moscowDate`, `monday`, `dateKey`.

Непосредственные вызовы: `moscowDate`, `monday`, `dateKey`, `shiftDays`, `calendarOrders.some`, `[...freeEvents, ...plans].some`.

## createSnapshot

[static/home-calendar.js:623](../../../static/home-calendar.js#L623) · `FunctionDeclaration`.

```javascript
function createSnapshot(now = new Date())
```

Создаёт отдельный DOM календаря для рендера общего PNG.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `snapshotRange`, `document.createElement`, `snapshot.setAttribute`, `fullDate.format`, `snapshot.append`, `get("homeCalendar").querySelector(".calendar-weekdays").cloneNode`, `get("homeCalendar").querySelector`, `get`, `dateKey`, `shiftDays`, `[...get("calendarWeeks").children].find`, `Error`, `row.cloneNode`, `snapshot.querySelectorAll`, `element.removeAttribute`.

Прямые присваивания полям/свойствам: `snapshot.className`, `snapshot.inert`, `title.textContent`.
