# static/money-overview.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/money-overview.js:1](../../../static/money-overview.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## escape

[static/money-overview.js:9](../../../static/money-overview.js#L9) · `ArrowFunctionExpression`.

```javascript
const escape = (value) =>
```

Экранирует текст перед вставкой в HTML-разметку или атрибут.

Заменяет &, <, >, кавычки и апостроф на безопасные HTML-сущности.

Непосредственные вызовы: `String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll`, `String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll`, `String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll`, `String(value ?? "").replaceAll("&", "&amp;").replaceAll`, `String(value ?? "").replaceAll`, `String`.

## key

[static/money-overview.js:12](../../../static/money-overview.js#L12) · `ArrowFunctionExpression`.

```javascript
const key = (date) =>
```

Вычисляет строковый ключ месяца для группировки платежей.

Использует `date.toISOString().slice`, `date.toISOString`.

Непосредственные вызовы: `date.toISOString().slice`, `date.toISOString`.

## shift

[static/money-overview.js:15](../../../static/money-overview.js#L15) · `ArrowFunctionExpression`.

```javascript
const shift = (month, offset) =>
```

Сдвигает ключ месяца на заданное число месяцев.

Использует `Date`, `Date.UTC`, `Number`.

Непосредственные вызовы: `Date`, `Date.UTC`, `Number`, `month.slice`.

## currentMonth

[static/money-overview.js:18](../../../static/money-overview.js#L18) · `ArrowFunctionExpression`.

```javascript
const currentMonth = () =>
```

Вычисляет ключ текущего месяца по Москве.

Использует `Intl.DateTimeFormat`, `Date`.

Непосредственные вызовы: `new Intl.DateTimeFormat("sv-SE", { year: "numeric", month: "2-digit", timeZone: "Europe/Moscow" }).format`, `Intl.DateTimeFormat`, `Date`.

## months

[static/money-overview.js:23](../../../static/money-overview.js#L23) · `FunctionDeclaration`.

```javascript
function months(records, firstMonth)
```

Строит последовательность четырёх месяцев сводки.

Использует `Array.from`, `Map`, `result.map`.

Непосредственные вызовы: `Array.from`, `Map`, `result.map`, `["incoming", "outgoing"].includes`, `Number.isSafeInteger`, `byMonth.get`, `plan.date?.slice`, `month[plan.operation].push`, `month[direction].sort`.

Прямые присваивания полям/свойствам: `month[plan.operation === "incoming" ? "income" : "expense"]`.

## item

[static/money-overview.js:46](../../../static/money-overview.js#L46) · `FunctionDeclaration`.

```javascript
function item(plan)
```

Строит строку одного платежа помесячной сводки.

Использует `money.format`, `shortDate.format`, `Date`.

Непосредственные вызовы: `money.format`, `shortDate.format`, `Date`, `compactDate.format`, `[plan.client, plan.object, plan.text].filter(Boolean).join`, `[plan.client, plan.object, plan.text].filter`, `[period, plan.operation === "incoming" ? "Приход" : "Расход", amount + " ₽", caption, context, plan.invoice_label].filter(Boolean).join`, `[period, plan.operation === "incoming" ? "Приход" : "Расход", amount + " ₽", caption, context, plan.invoice_label].filter`, `escape`, `encodeURIComponent`.

## render

[static/money-overview.js:63](../../../static/money-overview.js#L63) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет DOM компонента из текущих данных в модуле помесячной сводки денег.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`, `months`, `key`, `shift`, `currentMonth`, `data.map((month) => {
      const difference = month.income - month.expense;
      return '<section class="money-month" aria-label="' + escape(monthName.format(shift(month.key, 0))) + '">' +
        '<h3>' + escape(monthName.format(shift(month.key, 0))) + '</h3><div class="money-month-columns">' +
        ["incoming", "outgoing"].map((direction) => '<div class="money-direction money-' + direction + '"><h4>' + (direction === "incoming" ? 'Приходы' : 'Расходы') + '</h4><ul>' +
          (month[direction].map(item).join("") || '<li class="money-empty">Нет планов</li>') + '</ul></div>').join("") + '</div>' +
        '<footer class="money-totals"><div class="money-total-columns">' +
        '<p class="money-total money-total-incoming"><span>Приходы</span><strong>' + money.format(month.income / 100) + '</strong></p>' +
        '<p class="money-total money-total-outgoing"><span>Расходы</span><strong>' + money.format(month.expense / 100) + '</strong></p></div>' +
        '<p class="money-difference">Разница <strong class="' + (difference < 0 ? 'negative' : difference > 0 ? 'positive' : '') + '">' +
        (difference > 0 ? '+' : difference < 0 ? '−' : '') + money.format(Math.abs(difference) / 100) + ' ₽</strong></p></footer></section>';
    }).join`, `data.map`, `document.activeElement?.closest`, `document.querySelector`, `[...container.querySelectorAll("[data-money-item]")].find((node) => node.dataset.moneyItem === focused)?.focus`, `[...container.querySelectorAll("[data-money-item]")].find`, `container.querySelectorAll`.

Прямые присваивания полям/свойствам: `container.innerHTML`, `viewport.scrollLeft`, `pane.scrollTop`.

## show

[static/money-overview.js:91](../../../static/money-overview.js#L91) · `FunctionDeclaration`.

```javascript
function show(records, visible, { loaded = false, error = "" } = {})
```

Показывает компонент по полученным данным и текущему состоянию в модуле помесячной сводки денег.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `document.getElementById`, `panel.setAttribute`, `String`, `document.getElementById(id).addEventListener`, `panel.addEventListener`, `render`.

Прямые присваивания полям/свойствам: `panel.hidden`, `document.getElementById("moneyNavigation").hidden`, `document.getElementById("moneyScroll").hidden`, `document.getElementById("moneyState").textContent`.
