# static/inbox.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/inbox.js](../../../static/inbox.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-complete"></a>

## complete

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
async function complete(id, completed)
```

Сохраняет выполнение выбранной задачи Inbox с ожидаемой версией.

Использует `entries.find`, `update`, `focusRemaining`.

Непосредственные вызовы: `entries.find`, `update`, `focusRemaining`, `focusTask`.

<a id="symbol-copy"></a>

## copy

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
async function copy(id)
```

Копирует точный текст задачи и сообщает результат пользователю.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `entries.find`, `navigator.clipboard.writeText`, `window.getSelection`, `Array.from`, `document.createElement`, `document.body.append`, `document.addEventListener`, `field.focus`, `field.select`, `field.setSelectionRange`, `document.execCommand`, `Error`, `document.removeEventListener`, `field.remove`, `focused.focus`, `selection.removeAllRanges`, `ranges.forEach`, `notify`.

Прямые присваивания полям/свойствам: `field.value`, `field.readOnly`, `field.style.cssText`.

<a id="symbol-copy.onCopy"></a>

## copy.onCopy

[static/inbox.js](../../../static/inbox.js) · `ArrowFunctionExpression`.

```javascript
const onCopy = event =>
```

Копирует точный текст задачи и сообщает результат пользователю.

Использует `event.clipboardData.setData`, `event.preventDefault`.

Непосредственные вызовы: `event.clipboardData.setData`, `event.preventDefault`.

<a id="symbol-focusRemaining"></a>

## focusRemaining

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
function focusRemaining()
```

Переводит фокус на доступную задачу после удаления строки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `($("inboxList").querySelector("input") || (!$("inboxCompleted").hidden && $("inboxCompletedSummary")) || $("inboxTitle")).focus`, `$("inboxList").querySelector`, `$`.

<a id="symbol-focusTask"></a>

## focusTask

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
function focusTask(id)
```

Возвращает фокус на действие конкретной задачи Inbox.

Использует `rows.get`.

Непосредственные вызовы: `rows.get(id)?.querySelector("input").focus`, `rows.get(id)?.querySelector`, `rows.get`.

<a id="symbol-load"></a>

## load

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
async function load()
```

Загружает сохранённые данные компонента с сервера в модуле Telegram Inbox.

Использует `/api/inbox`.

Непосредственные вызовы: `request`, `render`, `$`, `$("inboxState").classList.toggle`, `Boolean`, `$("inboxState").classList.add`.

Прямые присваивания полям/свойствам: `$("inboxState").textContent`.

<a id="symbol-loadAll"></a>

## loadAll

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
function loadAll()
```

Загружает задачи Telegram и файловый счётчик Inbox.

Использует `Promise.all`, `load`, `loadFolder`.

Непосредственные вызовы: `Promise.all`, `load`, `loadFolder`.

<a id="symbol-loadFolder"></a>

## loadFolder

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
async function loadFolder()
```

Перечитывает узкий файловый счётчик папки Inbox.

Использует `/api/inbox-folder`.

Непосредственные вызовы: `request`, `renderFolder`.

<a id="symbol-remove"></a>

## remove

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
async function remove(id)
```

Удаляет выбранную задачу или документ через API компонента.

Использует `entries.find`, `update`, `focusRemaining`.

Непосредственные вызовы: `entries.find`, `update`, `focusRemaining`, `notify`.

<a id="symbol-remove.run"></a>

## remove.run

[static/inbox.js](../../../static/inbox.js) · `ArrowFunctionExpression`.

```javascript
run: async () =>
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `update`, `$`, `focusTask`.

Непосредственные вызовы: `update`, `$`, `focusTask`, `notify`.

Прямые присваивания полям/свойствам: `$("inboxCompleted").open`.

<a id="symbol-render"></a>

## render

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет DOM компонента из текущих данных в модуле Telegram Inbox.

Использует `entries.filter`, `renderList`, `$`.

Непосредственные вызовы: `entries.filter`, `renderList`, `$`, `Boolean`.

Прямые присваивания полям/свойствам: `$("inboxCount").textContent`, `$("inboxEmpty").hidden`, `$("inboxCompleted").hidden`, `$("inboxCompletedSummary").textContent`.

<a id="symbol-renderFolder"></a>

## renderFolder

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
function renderFolder()
```

Показывает доступность и количество файлов папки Inbox.

Использует `$`, `Boolean`, `button.setAttribute`.

Непосредственные вызовы: `$`, `Boolean`, `button.setAttribute`.

Прямые присваивания полям/свойствам: `$("inboxFolderCount").textContent`, `button.disabled`, `button.title`.

<a id="symbol-renderList"></a>

## renderList

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
function renderList(container, items)
```

Строит строки текущего списка компонента.

Использует `Set`, `items.map`, `ids.has`.

Непосредственные вызовы: `Set`, `items.map`, `ids.has`, `row.remove`, `items.forEach`.

<a id="symbol-update"></a>

## update

[static/inbox.js](../../../static/inbox.js) · `FunctionDeclaration`.

```javascript
async function update(item, action, fields = {})
```

Применяет подтверждённое частичное изменение к компоненту в модуле Telegram Inbox.

Использует `/api/inbox-`.

Непосредственные вызовы: `Error`, `$("inboxPanel").querySelectorAll("input, .inbox-remove").forEach`, `$("inboxPanel").querySelectorAll`, `$`, `fetch`, `JSON.stringify`, `response.json`, `entries.filter`, `entries.push`, `entries.sort`, `render`, `focused.focus`, `load`.
