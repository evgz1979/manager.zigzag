# static/inbox.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/inbox.js:1](../../../static/inbox.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## renderFolder

[static/inbox.js:9](../../../static/inbox.js#L9) · `FunctionDeclaration`.

```javascript
function renderFolder()
```

Показывает доступность и количество файлов папки Inbox.

Использует `$`, `Boolean`, `button.setAttribute`.

Непосредственные вызовы: `$`, `Boolean`, `button.setAttribute`.

Прямые присваивания полям/свойствам: `$("inboxFolderCount").textContent`, `button.disabled`, `button.title`.

## loadFolder

[static/inbox.js:19](../../../static/inbox.js#L19) · `FunctionDeclaration`.

```javascript
async function loadFolder()
```

Перечитывает узкий файловый счётчик папки Inbox.

Использует `/api/inbox-folder`.

Непосредственные вызовы: `request`, `renderFolder`.

## renderList

[static/inbox.js:42](../../../static/inbox.js#L42) · `FunctionDeclaration`.

```javascript
function renderList(container, items)
```

Строит строки текущего списка компонента.

Использует `Set`, `items.map`, `ids.has`.

Непосредственные вызовы: `Set`, `items.map`, `ids.has`, `row.remove`, `items.forEach`.

## render

[static/inbox.js:90](../../../static/inbox.js#L90) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет DOM компонента из текущих данных в модуле Telegram Inbox.

Использует `entries.filter`, `renderList`, `$`.

Непосредственные вызовы: `entries.filter`, `renderList`, `$`, `Boolean`.

Прямые присваивания полям/свойствам: `$("inboxCount").textContent`, `$("inboxEmpty").hidden`, `$("inboxCompleted").hidden`, `$("inboxCompletedSummary").textContent`.

## load

[static/inbox.js:102](../../../static/inbox.js#L102) · `FunctionDeclaration`.

```javascript
async function load()
```

Загружает сохранённые данные компонента с сервера в модуле Telegram Inbox.

Использует `/api/inbox`.

Непосредственные вызовы: `request`, `render`, `$`, `$("inboxState").classList.toggle`, `Boolean`, `$("inboxState").classList.add`.

Прямые присваивания полям/свойствам: `$("inboxState").textContent`.

## focusTask

[static/inbox.js:123](../../../static/inbox.js#L123) · `FunctionDeclaration`.

```javascript
function focusTask(id)
```

Возвращает фокус на действие конкретной задачи Inbox.

Использует `rows.get`.

Непосредственные вызовы: `rows.get(id)?.querySelector("input").focus`, `rows.get(id)?.querySelector`, `rows.get`.

## focusRemaining

[static/inbox.js:129](../../../static/inbox.js#L129) · `FunctionDeclaration`.

```javascript
function focusRemaining()
```

Переводит фокус на доступную задачу после удаления строки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `($("inboxList").querySelector("input") || (!$("inboxCompleted").hidden && $("inboxCompletedSummary")) || $("inboxTitle")).focus`, `$("inboxList").querySelector`, `$`.

## update

[static/inbox.js:135](../../../static/inbox.js#L135) · `FunctionDeclaration`.

```javascript
async function update(item, action, fields = {})
```

Применяет подтверждённое частичное изменение к компоненту в модуле Telegram Inbox.

Использует `/api/inbox-`.

Непосредственные вызовы: `Error`, `$("inboxPanel").querySelectorAll("input, .inbox-remove").forEach`, `$("inboxPanel").querySelectorAll`, `$`, `fetch`, `JSON.stringify`, `response.json`, `entries.filter`, `entries.push`, `entries.sort`, `render`, `focused.focus`, `load`.

## complete

[static/inbox.js:165](../../../static/inbox.js#L165) · `FunctionDeclaration`.

```javascript
async function complete(id, completed)
```

Сохраняет выполнение выбранной задачи Inbox с ожидаемой версией.

Использует `entries.find`, `update`, `focusRemaining`.

Непосредственные вызовы: `entries.find`, `update`, `focusRemaining`, `focusTask`.

## remove

[static/inbox.js:175](../../../static/inbox.js#L175) · `FunctionDeclaration`.

```javascript
async function remove(id)
```

Удаляет выбранную задачу или документ через API компонента.

Использует `entries.find`, `update`, `focusRemaining`.

Непосредственные вызовы: `entries.find`, `update`, `focusRemaining`, `notify`.

## run

[static/inbox.js:181](../../../static/inbox.js#L181) · `ArrowFunctionExpression`.

```javascript
run: async () =>
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `update`, `$`, `focusTask`.

Непосредственные вызовы: `update`, `$`, `focusTask`, `notify`.

Прямые присваивания полям/свойствам: `$("inboxCompleted").open`.

## copy

[static/inbox.js:191](../../../static/inbox.js#L191) · `FunctionDeclaration`.

```javascript
async function copy(id)
```

Копирует точный текст задачи и сообщает результат пользователю.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `entries.find`, `navigator.clipboard.writeText`, `window.getSelection`, `Array.from`, `document.createElement`, `document.body.append`, `document.addEventListener`, `field.focus`, `field.select`, `field.setSelectionRange`, `document.execCommand`, `Error`, `document.removeEventListener`, `field.remove`, `focused.focus`, `selection.removeAllRanges`, `ranges.forEach`, `notify`.

Прямые присваивания полям/свойствам: `field.value`, `field.readOnly`, `field.style.cssText`.

## onCopy

[static/inbox.js:208](../../../static/inbox.js#L208) · `ArrowFunctionExpression`.

```javascript
const onCopy = event =>
```

Копирует точный текст задачи и сообщает результат пользователю.

Использует `event.clipboardData.setData`, `event.preventDefault`.

Непосредственные вызовы: `event.clipboardData.setData`, `event.preventDefault`.

## loadAll

[static/inbox.js:233](../../../static/inbox.js#L233) · `FunctionDeclaration`.

```javascript
function loadAll()
```

Загружает задачи Telegram и файловый счётчик Inbox.

Использует `Promise.all`, `load`, `loadFolder`.

Непосредственные вызовы: `Promise.all`, `load`, `loadFolder`.
