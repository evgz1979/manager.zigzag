# static/calendar-snapshot.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/calendar-snapshot.js:1](../../../static/calendar-snapshot.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## loadRenderer

[static/calendar-snapshot.js:6](../../../static/calendar-snapshot.js#L6) · `FunctionDeclaration`.

```javascript
function loadRenderer()
```

Лениво загружает локальную библиотеку HTML-снимка.

Использует `Promise.resolve`, `Promise`.

Непосредственные вызовы: `Promise.resolve`, `Promise`.

## capture

[static/calendar-snapshot.js:20](../../../static/calendar-snapshot.js#L20) · `FunctionDeclaration`.

```javascript
async function capture(now = new Date())
```

Создаёт общий PNG из отдельного DOM-снимка календаря.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `loadRenderer`, `HomeCalendar.createSnapshot`, `Math.max`, `Math.ceil`, `document.getElementById("homeCalendar").getBoundingClientRect`, `document.getElementById`, `document.body.append`, `element.querySelectorAll`, `parseFloat`, `getComputedStyle`, `week.querySelector`, `week.style.getPropertyValue`, `week.getBoundingClientRect`, `element.getBoundingClientRect`, `Math.min`, `Math.sqrt`, `Error`, `render`, `Promise`, `element.remove`.

Прямые присваивания полям/свойствам: `element.style.width`, `amount.style.fontSize`, `week.style.height`, `content.scrollTop`.

## ignoreElements

[static/calendar-snapshot.js:47](../../../static/calendar-snapshot.js#L47) · `ArrowFunctionExpression`.

```javascript
ignoreElements: (node) =>
```

Исключает управляющие элементы из изображения календаря.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## onclone

[static/calendar-snapshot.js:50](../../../static/calendar-snapshot.js#L50) · `ArrowFunctionExpression`.

```javascript
onclone: (_document, copy) =>
```

Применяет нужные размеры и оформление к копии DOM для снимка.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

Прямые присваивания полям/свойствам: `copy.style.position`, `copy.style.left`.
