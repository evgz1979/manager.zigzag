# static/work-orders.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/work-orders.js](../../../static/work-orders.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-refresh"></a>

## refresh

[static/work-orders.js](../../../static/work-orders.js) · `FunctionDeclaration`.

```javascript
async function refresh(force = false)
```

Перечитывает данные открытого компонента по установленным правилам в модуле подборки заказов поставщиков.

Использует `/api/work-order-links`.

Непосредственные вызовы: `$`, `visible`, `render`, `request`, `apiUrl`.

Прямые присваивания полям/свойствам: `$("workLinksSection").hidden`, `$("workLinksState").textContent`.

<a id="symbol-render"></a>

## render

[static/work-orders.js](../../../static/work-orders.js) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет DOM компонента из текущих данных в модуле подборки заказов поставщиков.

Использует `$`, `items.map`.

Непосредственные вызовы: `$`, `items.map((item) => '<div class="work-link-row"><div>' + (item.path
      ? '<button type="button" class="order-row-link" data-work-order-path="' + escapeHtml(item.path) + '">' + escapeHtml(item.title) + '</button>'
      : '<span>' + escapeHtml(item.title) + '</span>') + '<small>' + escapeHtml(item.supplier || "") + (item.registered ? "" : " · Убран из списка") + '</small>' +
      (item.path ? '<small>' + escapeHtml(item.path) + '</small>' : '') + '</div>' + (Object.hasOwn(item, "supplier_status")
        ? '<span class="status-badge" data-status="supplier-' + escapeHtml(item.supplier_status || "unknown") + '">' + escapeHtml(supplierStatusLabels[item.supplier_status] || "Неизвестный статус") + '</span>'
        : item.status ? '<span class="status-badge" data-status="' + escapeHtml(item.status) + '">' + escapeHtml(statusLabels[item.status] || item.status) + '</span>' : '') + '</div>').join`, `items.map`.

Прямые присваивания полям/свойствам: `$("workLinksCount").textContent`, `$("editWorkLinks").disabled`, `$("editWorkLinks").textContent`, `$("workLinksList").innerHTML`, `$("workLinksState").textContent`.

<a id="symbol-renderOptions"></a>

## renderOptions

[static/work-orders.js](../../../static/work-orders.js) · `FunctionDeclaration`.

```javascript
function renderOptions()
```

Строит варианты заказов поставщиков для связанной подборки.

Использует `model.items.filter`, `normalize`, `$("workLinksSearch").value.trim`.

Непосредственные вызовы: `model.items.filter`, `normalize`, `$("workLinksSearch").value.trim`, `$`, `options.filter`, `matches.map((item) => '<label class="work-link-option"><input type="checkbox" data-work-order-id="' + escapeHtml(item.id) + '"' + (selection.has(item.id) ? ' checked' : '') + '><span><strong>' + escapeHtml(item.title) + '</strong><small>' + escapeHtml(item.supplier || "") + (item.registered ? "" : " · Убран из списка") + '</small><small>' + escapeHtml(item.path || "Запись недоступна") + '</small></span></label>').join`, `matches.map`.

Прямые присваивания полям/свойствам: `$("workLinksOptions").innerHTML`.

<a id="symbol-visible"></a>

## visible

[static/work-orders.js](../../../static/work-orders.js) · `ArrowFunctionExpression`.

```javascript
const visible = (folder) =>
```

Проверяет, относится ли открытая папка к области текущего компонента.

Использует `folder.path.split`, `/^#\s*work$/i.test`.

Непосредственные вызовы: `folder.path.split`, `/^#\s*work$/i.test`.
