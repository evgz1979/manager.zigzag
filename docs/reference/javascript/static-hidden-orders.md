# static/hidden-orders.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/hidden-orders.js](../../../static/hidden-orders.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-%24"></a>

## $

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const $ = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

<a id="symbol-escape"></a>

## escape

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const escape = (value) =>
```

Экранирует текст перед вставкой в HTML-разметку или атрибут.

Заменяет &, <, >, кавычки и апостроф на безопасные HTML-сущности.

Непосредственные вызовы: `String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll`, `String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll`, `String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll`, `String(value ?? "").replaceAll("&", "&amp;").replaceAll`, `String(value ?? "").replaceAll`, `String`.

<a id="symbol-groupKey"></a>

## groupKey

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const groupKey = (kind, path) =>
```

Строит ключ группировки скрытых заказов по местоположению.

Использует `JSON.stringify`.

Непосредственные вызовы: `JSON.stringify`.

<a id="symbol-groupOrders"></a>

## groupOrders

[static/hidden-orders.js](../../../static/hidden-orders.js) · `FunctionDeclaration`.

```javascript
function groupOrders(rows)
```

Группирует известные скрытые заказы по клиентам и объектам.

Использует `Map`, `clients.has`, `clients.set`.

Непосредственные вызовы: `Map`, `clients.has`, `clients.set`, `clients.get`, `client.objects.has`, `client.objects.set`, `client.objects.get(objectPath).orders.push`, `client.objects.get`, `[...clients.values()].sort`, `clients.values`.

Прямые присваивания полям/свойствам: `client.count`.

<a id="symbol-href"></a>

## href

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const href = (path) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `encodeURIComponent`.

Непосредственные вызовы: `encodeURIComponent`.

<a id="symbol-link"></a>

## link

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const link = (path, label, className = "") =>
```

Строит ссылку открытия папки с безопасным отображением имени.

Использует `escape`, `href`.

Непосредственные вызовы: `escape`, `href`.

<a id="symbol-load"></a>

## load

[static/hidden-orders.js](../../../static/hidden-orders.js) · `FunctionDeclaration`.

```javascript
async function load()
```

Загружает сохранённые данные компонента с сервера в модуле списка скрытых заказов.

Использует `/api/hidden-orders`.

Непосредственные вызовы: `$("hiddenOrdersRefresh").setAttribute`, `$`, `$("hiddenOrdersGroups").setAttribute`, `fetch`, `response.json`, `Error`, `data.warnings.slice(0, 3).join`, `data.warnings.slice`, `render`.

Прямые присваивания полям/свойствам: `$("hiddenOrdersState").textContent`, `$("hiddenOrdersCount").textContent`.

<a id="symbol-normalize"></a>

## normalize

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const normalize = (value) =>
```

Нормализует строку для поиска и сравнения без учёта регистра.

Использует `String(value ?? "").normalize("NFC").toLocaleLowerCase`, `String(value ?? "").normalize`, `String`.

Непосредственные вызовы: `String(value ?? "").normalize("NFC").toLocaleLowerCase`, `String(value ?? "").normalize`, `String`.

<a id="symbol-remember"></a>

## remember

[static/hidden-orders.js](../../../static/hidden-orders.js) · `ArrowFunctionExpression`.

```javascript
const remember = () =>
```

Сохраняет полученные скрытые заказы для фильтрации интерфейса.

Сохраняет локальную настройку интерфейса через localStorage.

Непосредственные вызовы: `localStorage.setItem`, `JSON.stringify`.

<a id="symbol-render"></a>

## render

[static/hidden-orders.js](../../../static/hidden-orders.js) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет DOM компонента из текущих данных в модуле списка скрытых заказов.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `normalize`, `$("hiddenOrdersSearch").value.trim`, `$`, `Object.hasOwn`, `orders.filter`, `Object.entries(labels).map(([key, label]) => '<option value="' + escape(key) + '">' + escape(label) + ' · ' + matching.filter((order) => order.reasons.includes(key)).length + '</option>').join`, `Object.entries(labels).map`, `Object.entries`, `matching.filter`, `groupOrders`, `clients.map((client) => {
      const key = groupKey("client", client.path || client.name);
      return '<details class="hidden-orders-client" data-group="' + escape(key) + '"' + (collapsed.has(key) ? '' : ' open') + '><summary data-focus-key="' + escape(key) + '"><strong>' + escape(client.name) + '</strong><span class="count-badge">' + client.count + '</span><span class="hidden-orders-group-path">' + escape(client.path) + '</span></summary><div class="hidden-orders-objects">' +
        [...client.objects.values()].sort((a, b) => !a.path - !b.path || compare(a.name, b.name) || compare(a.path, b.path)).map((object) => {
          const objectKey = groupKey("object", [client.path || client.name, object.path]);
          const sorted = object.orders.slice().sort((a, b) => (b.updated || 0) - (a.updated || 0) || compare(a.title, b.title) || compare(a.path, b.path));
          return '<details class="hidden-orders-object" data-group="' + escape(objectKey) + '"' + (collapsed.has(objectKey) ? '' : ' open') + '><summary data-focus-key="' + escape(objectKey) + '"><span>' + escape(object.name) + '</span><span class="count-badge">' + sorted.length + '</span></summary>' +
            (object.path ? '<p class="hidden-orders-location">' + link(object.path, "Открыть объект ↗") + '</p>' : '') + '<ul class="hidden-orders-list">' + sorted.map((order) => '<li class="hidden-orders-row"><div class="hidden-orders-order">' +
              '<a class="hidden-orders-title" data-focus-key="' + escape(groupKey("order", order.path)) + '" href="' + escape(href(order.path)) + '">' + escape(order.title) + '</a><span class="hidden-orders-order-path" title="' + escape(order.path) + '">' + escape(order.path) + '</span>' +
              (order.note ? '<span class="hidden-orders-note" title="' + escape(order.note) + '">' + escape(order.note) + '</span>' : '') + '</div><span class="status-badge">' + escape(order.status_label) + '</span><div class="hidden-orders-reasons">' + order.reasons.map((key) => '<span>' + escape(labels[key] || key) + '</span>').join("") + '</div></li>').join("") + '</ul></details>';
        }).join("") + '</div></details>';
    }).join`, `clients.map`, `[...$("hiddenOrdersGroups").querySelectorAll("[data-focus-key]")].find((element) => element.dataset.focusKey === focusKey)?.focus`, `[...$("hiddenOrdersGroups").querySelectorAll("[data-focus-key]")].find`, `$("hiddenOrdersGroups").querySelectorAll`, `Boolean`.

Прямые присваивания полям/свойствам: `$("hiddenOrdersReason").innerHTML`, `$("hiddenOrdersReason").value`, `$("hiddenOrdersGroups").innerHTML`, `document.scrollingElement.scrollTop`, `$("hiddenOrdersCount").textContent`, `$("hiddenOrdersEmpty").hidden`.
