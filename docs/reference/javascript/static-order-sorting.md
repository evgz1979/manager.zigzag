# static/order-sorting.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/order-sorting.js](../../../static/order-sorting.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-compareOrderText"></a>

## compareOrderText

[static/order-sorting.js](../../../static/order-sorting.js) · `FunctionDeclaration`.

```javascript
function compareOrderText(first, second)
```

Сравнивает значения заказов по выбранному порядку сортировки.

Использует `String(first ?? "").normalize`, `String`, `String(second ?? "").normalize`.

Непосредственные вызовы: `String(first ?? "").normalize`, `String`, `String(second ?? "").normalize`, `first.localeCompare`.

<a id="symbol-compareOrders"></a>

## compareOrders

[static/order-sorting.js](../../../static/order-sorting.js) · `FunctionDeclaration`.

```javascript
function compareOrders(a, b, key = "title", direction = 1, labelSets = {})
```

Сравнивает значения заказов по выбранному порядку сортировки.

Использует `compareOrderText`, `Boolean`, `Number`.

Непосредственные вызовы: `compareOrderText`, `Boolean`, `Number`.
