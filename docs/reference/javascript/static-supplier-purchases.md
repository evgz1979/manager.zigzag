# static/supplier-purchases.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/supplier-purchases.js](../../../static/supplier-purchases.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-checkText"></a>

## checkText

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
async function checkText()
```

Перечитывает источник закупки при конфликте, сохраняя введённый черновик.

Использует `/api/supplier-purchases`.

Непосредственные вызовы: `editorControls`, `Error`, `request`, `apiUrl`, `current.orders.find`, `order?.items.find`, `render`, `$`, `item.suppliers.join`, `$("supplierPurchaseText").focus`.

Прямые присваивания полям/свойствам: `edit.busy`, `$("supplierPurchaseCurrent").textContent`, `$("supplierPurchaseCurrent").hidden`, `edit.order`, `edit.item`, `edit.conflict`, `$("supplierPurchaseEditState").textContent`.

<a id="symbol-editorControls"></a>

## editorControls

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
function editorControls()
```

Обновляет доступность сохранения редактора закупки.

Использует `Boolean`, `$`.

Непосредственные вызовы: `Boolean`, `$`.

Прямые присваивания полям/свойствам: `$("supplierPurchaseText").readOnly`, `$("saveSupplierPurchase").disabled`, `$("cancelSupplierPurchase").disabled`, `$("checkSupplierPurchase").disabled`, `$("checkSupplierPurchase").hidden`.

<a id="symbol-focusEdit"></a>

## focusEdit

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
function focusEdit(key)
```

Возвращает фокус на кнопку правки исходной закупки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `([...list.querySelectorAll("[data-supplier-purchase-edit]")].find(el => el.dataset.supplierPurchaseEdit === key) || $(panel.hidden ? "openFolderButton" : "supplierPurchasesShowDone")).focus`, `[...list.querySelectorAll("[data-supplier-purchase-edit]")].find`, `list.querySelectorAll`, `$`.

<a id="symbol-itemKey"></a>

## itemKey

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `ArrowFunctionExpression`.

```javascript
const itemKey = (order, item) =>
```

Вычисляет устойчивый ключ строки исходной закупки.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-openEditor"></a>

## openEditor

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
function openEditor(button)
```

Открывает правку точной исходной строки закупки у поставщика.

Использует `model.orders.find`, `itemKey`, `$`.

Непосредственные вызовы: `model.orders.find`, `order?.items.find`, `itemKey`, `$`, `[order.client, order.object, order.title].filter(Boolean).join`, `[order.client, order.object, order.title].filter`, `editorControls`, `dialog.showModal`, `$("supplierPurchaseText").focus`.

Прямые присваивания полям/свойствам: `$("supplierPurchaseSource").textContent`, `$("supplierPurchaseText").value`, `$("supplierPurchaseEditState").textContent`, `$("supplierPurchaseCurrent").hidden`.

<a id="symbol-refresh"></a>

## refresh

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
async function refresh()
```

Перечитывает данные открытого компонента по установленным правилам в модуле закупок у поставщика.

Использует `/api/supplier-purchases`.

Непосредственные вызовы: `visible`, `$("orderOverview").classList.remove`, `$`, `render`, `request`, `apiUrl`.

Прямые присваивания полям/свойствам: `panel.hidden`, `$("supplierPurchasesShowDone").checked`, `list.innerHTML`.

<a id="symbol-render"></a>

## render

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет DOM компонента из текущих данных в модуле закупок у поставщика.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `visible`, `$("orderOverview").classList.toggle`, `$`, `document.querySelector`, `groups.flatMap`, `all.filter`, `groups.map(order => {
      const items = order.items.filter(item => showDone || !item.done || itemKey(order, item) === pendingKey);
      if (!items.length) return "";
      const name = [order.client, order.object, order.title].filter(Boolean).join(" · ");
      return '<section class="supplier-purchase-group" data-supplier-purchase-order="' + escapeHtml(order.id) + '">' +
        items.map(item => '<div class="supplier-purchase-row' + (item.done ? ' done' : '') + '"><label class="supplier-purchase-task"><input type="checkbox" class="todo-check" data-supplier-purchase-done="' + escapeHtml(itemKey(order, item)) +
          '" data-purchase-index="' + item.index + '" aria-label="Закупка выполнена: ' + escapeHtml(item.text + ' · ' + name) + '"' + (item.done ? ' checked' : '') + (saving ? ' disabled' : '') +
          '><span title="' + escapeHtml(item.text) + '">' + escapeHtml(item.text) + '</span></label>' +
          '<a class="order-row-link supplier-purchase-source" data-supplier-purchase-path="' + escapeHtml(order.path) + '" data-supplier-purchase-source="' + escapeHtml(itemKey(order, item)) +
          '" href="?path=' + encodeURIComponent(order.path) + '" title="' + escapeHtml(name + ' · ' + order.path) + '" aria-label="' + escapeHtml('Открыть заказ · ' + name + ' · ' + order.path) + '">' + escapeHtml(name) + '</a>' +
          '<button class="supplier-purchase-edit" type="button" data-supplier-purchase-edit="' + escapeHtml(itemKey(order, item)) + '" data-purchase-index="' + item.index + '" title="Изменить закупку" aria-label="' + escapeHtml('Изменить закупку: ' + item.text + ' · ' + name) + '"' + (saving ? ' disabled' : '') + '>' + icon("edit") + '</button></div>').join("") + '</section>';
    }).join`, `groups.map`, `([...list.querySelectorAll("[data-supplier-purchase-done]")].find(el => el.dataset.supplierPurchaseDone === focused) || $("supplierPurchasesShowDone")).focus`, `[...list.querySelectorAll("[data-supplier-purchase-done]")].find`, `list.querySelectorAll`, `([...list.querySelectorAll("[data-supplier-purchase-source]")].find(el => el.dataset.supplierPurchaseSource === focusedSource) || $("supplierPurchasesShowDone")).focus`, `[...list.querySelectorAll("[data-supplier-purchase-source]")].find`, `focusEdit`.

Прямые присваивания полям/свойствам: `panel.hidden`, `$("supplierPurchasesCount").textContent`, `$("refreshSupplierPurchases").disabled`, `list.innerHTML`, `$("supplierPurchasesState").textContent`, `pane.scrollTop`.

<a id="symbol-saveText"></a>

## saveText

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `FunctionDeclaration`.

```javascript
async function saveText()
```

Сохраняет текст исходной закупки с её версией и проверочной строкой.

Использует `/api/supplier-purchase-text`.

Непосредственные вызовы: `$`, `$("supplierPurchaseText").value.trim`, `dialog.close`, `editorControls`, `render`, `request`, `applyOrderRecord`, `notify`, `refresh`, `$("supplierPurchaseText").focus`.

Прямые присваивания полям/свойствам: `$("supplierPurchaseEditState").textContent`, `edit.busy`, `edit.conflict`.

<a id="symbol-visible"></a>

## visible

[static/supplier-purchases.js](../../../static/supplier-purchases.js) · `ArrowFunctionExpression`.

```javascript
const visible = () =>
```

Проверяет, относится ли открытая папка к области текущего компонента.

Использует `Boolean`.

Непосредственные вызовы: `Boolean`.
