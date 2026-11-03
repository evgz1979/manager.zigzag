# static/work-orders.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/work-orders.js:1](../../../static/work-orders.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## visible

[static/work-orders.js:6](../../../static/work-orders.js#L6) · `ArrowFunctionExpression`.

```javascript
const visible = (folder) =>
```

Проверяет, относится ли открытая папка к области текущего компонента.

Использует `folder.path.split`, `/^#\s*work$/i.test`.

Непосредственные вызовы: `folder.path.split`, `/^#\s*work$/i.test`.

## render

[static/work-orders.js:10](../../../static/work-orders.js#L10) · `FunctionDeclaration`.

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

## refresh

[static/work-orders.js:27](../../../static/work-orders.js#L27) · `FunctionDeclaration`.

```javascript
async function refresh(force = false)
```

Перечитывает данные открытого компонента по установленным правилам в модуле подборки заказов поставщиков.

Использует `/api/work-order-links`.

Непосредственные вызовы: `$`, `visible`, `render`, `request`, `apiUrl`.

Прямые присваивания полям/свойствам: `$("workLinksSection").hidden`, `$("workLinksState").textContent`.

## renderOptions

[static/work-orders.js:52](../../../static/work-orders.js#L52) · `FunctionDeclaration`.

```javascript
function renderOptions()
```

Строит варианты заказов поставщиков для связанной подборки.

Использует `model.items.filter`, `normalize`, `$("workLinksSearch").value.trim`.

Непосредственные вызовы: `model.items.filter`, `normalize`, `$("workLinksSearch").value.trim`, `$`, `options.filter`, `matches.map((item) => '<label class="work-link-option"><input type="checkbox" data-work-order-id="' + escapeHtml(item.id) + '"' + (selection.has(item.id) ? ' checked' : '') + '><span><strong>' + escapeHtml(item.title) + '</strong><small>' + escapeHtml(item.supplier || "") + (item.registered ? "" : " · Убран из списка") + '</small><small>' + escapeHtml(item.path || "Запись недоступна") + '</small></span></label>').join`, `matches.map`.

Прямые присваивания полям/свойствам: `$("workLinksOptions").innerHTML`.
