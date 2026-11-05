# static/calendar-snapshot.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/calendar-snapshot.js](../../../static/calendar-snapshot.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-capture"></a>

## capture

[static/calendar-snapshot.js](../../../static/calendar-snapshot.js) · `FunctionDeclaration`.

```javascript
async function capture(now = new Date())
```

Создаёт общий PNG из отдельного DOM-снимка календаря.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `loadRenderer`, `HomeCalendar.createSnapshot`, `Math.max`, `Math.ceil`, `document.getElementById("homeCalendar").getBoundingClientRect`, `document.getElementById`, `document.body.append`, `element.querySelectorAll`, `parseFloat`, `getComputedStyle`, `week.querySelector`, `week.style.getPropertyValue`, `week.getBoundingClientRect`, `element.getBoundingClientRect`, `Math.min`, `Math.sqrt`, `Error`, `render`, `Promise`, `element.remove`.

Прямые присваивания полям/свойствам: `element.style.width`, `amount.style.fontSize`, `week.style.height`, `content.scrollTop`.

<a id="symbol-capture.ignoreElements"></a>

## capture.ignoreElements

[static/calendar-snapshot.js](../../../static/calendar-snapshot.js) · `ArrowFunctionExpression`.

```javascript
ignoreElements: (node) =>
```

Исключает управляющие элементы из изображения календаря.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-capture.onclone"></a>

## capture.onclone

[static/calendar-snapshot.js](../../../static/calendar-snapshot.js) · `ArrowFunctionExpression`.

```javascript
onclone: (_document, copy) =>
```

Применяет нужные размеры и оформление к копии DOM для снимка.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

Прямые присваивания полям/свойствам: `copy.style.position`, `copy.style.left`.

<a id="symbol-loadRenderer"></a>

## loadRenderer

[static/calendar-snapshot.js](../../../static/calendar-snapshot.js) · `FunctionDeclaration`.

```javascript
function loadRenderer()
```

Лениво загружает локальную библиотеку HTML-снимка.

Использует `Promise.resolve`, `Promise`.

Непосредственные вызовы: `Promise.resolve`, `Promise`.
