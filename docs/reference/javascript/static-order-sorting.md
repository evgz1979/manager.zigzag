# static/order-sorting.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/order-sorting.js:1](../../../static/order-sorting.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## compareOrderText

[static/order-sorting.js:5](../../../static/order-sorting.js#L5) · `FunctionDeclaration`.

```javascript
function compareOrderText(first, second)
```

Сравнивает значения заказов по выбранному порядку сортировки.

Использует `String(first ?? "").normalize`, `String`, `String(second ?? "").normalize`.

Непосредственные вызовы: `String(first ?? "").normalize`, `String`, `String(second ?? "").normalize`, `first.localeCompare`.

## compareOrders

[static/order-sorting.js:13](../../../static/order-sorting.js#L13) · `FunctionDeclaration`.

```javascript
function compareOrders(a, b, key = "title", direction = 1, labelSets = {})
```

Сравнивает значения заказов по выбранному порядку сортировки.

Использует `compareOrderText`, `Boolean`, `Number`.

Непосредственные вызовы: `compareOrderText`, `Boolean`, `Number`.
