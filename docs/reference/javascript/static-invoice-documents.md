# static/invoice-documents.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/invoice-documents.js:1](../../../static/invoice-documents.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## size

[static/invoice-documents.js:7](../../../static/invoice-documents.js#L7) · `ArrowFunctionExpression`.

```javascript
const size = (bytes) =>
```

Форматирует размер файла для интерфейса.

Использует `new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format`, `Intl.NumberFormat`.

Непосредственные вызовы: `new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format`, `Intl.NumberFormat`.

## row

[static/invoice-documents.js:10](../../../static/invoice-documents.js#L10) · `ArrowFunctionExpression`.

```javascript
const row = (id) =>
```

Строит строку вложения счёта с состоянием публикации и удаления.

Использует `$`.

Непосредственные вызовы: `$('invoiceList').invoiceRecords?.find`, `$`.

## attr

[static/invoice-documents.js:13](../../../static/invoice-documents.js#L13) · `ArrowFunctionExpression`.

```javascript
const attr = (record, action, document = '') =>
```

Экранирует текст перед вставкой в HTML-разметку или атрибут.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## uiFor

[static/invoice-documents.js:16](../../../static/invoice-documents.js#L16) · `ArrowFunctionExpression`.

```javascript
const uiFor = (record) =>
```

Получает локальное состояние редактора вложений выбранного счёта.

Использует `uploads.has`, `uploads.set`, `uploads.get`.

Непосредственные вызовы: `uploads.has`, `uploads.set`, `uploads.get`.

## repaint

[static/invoice-documents.js:22](../../../static/invoice-documents.js#L22) · `ArrowFunctionExpression`.

```javascript
const repaint = () =>
```

Обновляет существующий компонент после изменения его данных.

Использует `hooks.render`, `$`.

Непосредственные вызовы: `hooks.render`, `$`.

## button

[static/invoice-documents.js:26](../../../static/invoice-documents.js#L26) · `FunctionDeclaration`.

```javascript
function button(record)
```

Строит кнопку действия компонента с текущим состоянием записи.

Использует `uploads.get`, `attr`, `Boolean`.

Непосредственные вызовы: `uploads.get`, `attr`, `Boolean`.

## markup

[static/invoice-documents.js:33](../../../static/invoice-documents.js#L33) · `FunctionDeclaration`.

```javascript
function markup(record)
```

Формирует HTML текущего компонента из переданных данных.

Использует `/api/invoice-document`.

Непосредственные вызовы: `uploads.get`, `items.map((document) => {
      const url = apiUrl('/api/invoice-document', record.path, { id: record.id, document_id: document.id });
      const copy = document.sync_error ? 'Копия в # bills: ' + document.sync_error + ' · автоповтор' : document.exported ? 'Копия в # bills' : 'Копия в # bills ожидает сохранения';
      return '<div class="invoice-closing-file"><div class="invoice-closing-name"><a href="' + escapeHtml(url) + '" target="_blank" rel="noopener">' + escapeHtml(document.name) + '</a><small class="invoice-closing-copy' + (document.sync_error ? ' error' : '') + '">' + escapeHtml(copy) + '</small></div><small>' + size(document.size) + '</small><button type="button" class="secondary-button invoice-remove"' + attr(record, 'remove', document.id) + ' aria-label="Убрать закрывающий документ · ' + escapeHtml(document.name) + '"' + (ui?.busy ? ' disabled' : '') + '>×</button></div>';
    }).join`, `items.map`, `trash.map((document) => '<div class="invoice-closing-file"><span>' + escapeHtml(document.name) + '</span><button class="secondary-button" type="button"' + attr(record, 'restore', document.id) + (ui?.busy ? ' disabled' : '') + '>Восстановить</button></div>').join`, `trash.map`, `attr`, `ui.files.map((pending) => '<div class="invoice-closing-file"><span>' + escapeHtml(pending.file.name) + '</span><small>' + size(pending.file.size) + '</small><button class="secondary-button invoice-remove" type="button"' + attr(record, 'unselect', pending.id) + ' aria-label="Убрать из выбранных · ' + escapeHtml(pending.file.name) + '"' + disabled + '>×</button></div>').join`, `ui.files.map`, `escapeHtml`.

## queue

[static/invoice-documents.js:56](../../../static/invoice-documents.js#L56) · `FunctionDeclaration`.

```javascript
function queue(record, files)
```

Последовательно выполняет операции одного редактора документов.

Использует `uiFor`, `ui.files.push`, `freeCalendarIdentity`.

Непосредственные вызовы: `uiFor`, `ui.files.push`, `freeCalendarIdentity`, `document.activeElement?.matches`, `document.activeElement.blur`, `repaint`.

Прямые присваивания полям/свойствам: `ui.path`, `ui.revision`, `ui.conflict`, `ui.open`, `ui.message`, `ui.error`.

## encoded

[static/invoice-documents.js:71](../../../static/invoice-documents.js#L71) · `FunctionDeclaration`.

```javascript
function encoded(file)
```

Кодирует байты выбранного документа для допустимого запроса загрузки.

Использует `Promise`.

Непосредственные вызовы: `Promise`.

## upload

[static/invoice-documents.js:82](../../../static/invoice-documents.js#L82) · `FunctionDeclaration`.

```javascript
async function upload(record)
```

Передаёт выбранное вложение счёта в последовательную очередь сохранения.

Использует `/api/invoice-document-upload`.

Непосредственные вызовы: `uiFor`, `repaint`, `request`, `encoded`, `ui.files.shift`, `hooks.accept`, `notify`, `hooks.refresh`.

Прямые присваивания полям/свойствам: `ui.busy`, `ui.error`, `ui.message`, `ui.revision`, `ui.open`, `ui.conflict`.

## review

[static/invoice-documents.js:108](../../../static/invoice-documents.js#L108) · `FunctionDeclaration`.

```javascript
async function review(record)
```

Показывает доступные действия проверки и изменения вложения.

Использует `/api/invoice`.

Непосредственные вызовы: `uiFor`, `request`, `apiUrl`, `Error`, `hooks.accept`, `saved.closing_documents.map((item) => item.name).join`, `saved.closing_documents.map`, `repaint`.

Прямые присваивания полям/свойствам: `ui.busy`, `ui.path`, `ui.revision`, `ui.conflict`, `ui.error`, `ui.message`.

## change

[static/invoice-documents.js:123](../../../static/invoice-documents.js#L123) · `FunctionDeclaration`.

```javascript
async function change(record, documentId, deleted)
```

Сохраняет частичное изменение выбранного вложения счёта.

Использует `/api/invoice-document-remove`, `/api/invoice-document-restore`.

Непосредственные вызовы: `uiFor`, `repaint`, `request`, `hooks.accept`, `notify`, `hooks.refresh`.

Прямые присваивания полям/свойствам: `ui.busy`, `ui.revision`.

## run

[static/invoice-documents.js:133](../../../static/invoice-documents.js#L133) · `ArrowFunctionExpression`.

```javascript
run: () =>
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `change`.

Непосредственные вызовы: `change`.

## init

[static/invoice-documents.js:141](../../../static/invoice-documents.js#L141) · `FunctionDeclaration`.

```javascript
function init(options)
```

Подключает обработчики и зависимости компонента.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `$('invoiceList').addEventListener`, `$`, `window.addEventListener`.

## focusKey

[static/invoice-documents.js:189](../../../static/invoice-documents.js#L189) · `FunctionDeclaration`.

```javascript
function focusKey()
```

Запоминает устойчивый ключ сфокусированного элемента вложений.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

Непосредственные вызовы: `document.activeElement?.closest`.

## restoreFocus

[static/invoice-documents.js:196](../../../static/invoice-documents.js#L196) · `FunctionDeclaration`.

```javascript
function restoreFocus(key)
```

Возвращает фокус после обновления списка вложений.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$('invoiceList').querySelectorAll('[data-doc-action]')].find((element) => element.dataset.docAction === key.action && element.dataset.docInvoice === key.id && (element.dataset.docDocument || '') === key.document)?.focus`, `[...$('invoiceList').querySelectorAll('[data-doc-action]')].find`, `$('invoiceList').querySelectorAll`, `$`.

## isBusy

[static/invoice-documents.js:202](../../../static/invoice-documents.js#L202) · `ArrowFunctionExpression`.

```javascript
isBusy: (id) =>
```

Проверяет наличие незавершённой операции редактора.

Использует `Boolean`, `uploads.get`.

Непосредственные вызовы: `Boolean`, `uploads.get`.
