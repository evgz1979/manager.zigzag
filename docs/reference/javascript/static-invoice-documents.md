# static/invoice-documents.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/invoice-documents.js](../../../static/invoice-documents.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-attr"></a>

## attr

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
const attr = (record, action, document = '') =>
```

Экранирует текст перед вставкой в HTML-разметку или атрибут.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

<a id="symbol-button"></a>

## button

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
function button(record)
```

Строит кнопку действия компонента с текущим состоянием записи.

Использует `uploads.get`, `attr`, `Boolean`.

Непосредственные вызовы: `uploads.get`, `attr`, `Boolean`.

<a id="symbol-change"></a>

## change

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
async function change(record, documentId, deleted)
```

Сохраняет частичное изменение выбранного вложения счёта.

Использует `/api/invoice-document-remove`, `/api/invoice-document-restore`.

Непосредственные вызовы: `uiFor`, `repaint`, `request`, `hooks.accept`, `notify`, `hooks.refresh`.

Прямые присваивания полям/свойствам: `ui.busy`, `ui.revision`.

<a id="symbol-change.run"></a>

## change.run

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
run: () =>
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `change`.

Непосредственные вызовы: `change`.

<a id="symbol-encoded"></a>

## encoded

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
function encoded(file)
```

Кодирует байты выбранного документа для допустимого запроса загрузки.

Использует `Promise`.

Непосредственные вызовы: `Promise`.

<a id="symbol-focusKey"></a>

## focusKey

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
function focusKey()
```

Запоминает устойчивый ключ сфокусированного элемента вложений.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

Непосредственные вызовы: `document.activeElement?.closest`.

<a id="symbol-init"></a>

## init

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
function init(options)
```

Подключает обработчики и зависимости компонента.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `$('invoiceList').addEventListener`, `$`, `window.addEventListener`.

<a id="symbol-isBusy"></a>

## isBusy

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
isBusy: (id) =>
```

Проверяет наличие незавершённой операции редактора.

Использует `Boolean`, `uploads.get`.

Непосредственные вызовы: `Boolean`, `uploads.get`.

<a id="symbol-markup"></a>

## markup

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

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

<a id="symbol-queue"></a>

## queue

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
function queue(record, files)
```

Последовательно выполняет операции одного редактора документов.

Использует `uiFor`, `ui.files.push`, `freeCalendarIdentity`.

Непосредственные вызовы: `uiFor`, `ui.files.push`, `freeCalendarIdentity`, `document.activeElement?.matches`, `document.activeElement.blur`, `repaint`.

Прямые присваивания полям/свойствам: `ui.path`, `ui.revision`, `ui.conflict`, `ui.open`, `ui.message`, `ui.error`.

<a id="symbol-repaint"></a>

## repaint

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
const repaint = () =>
```

Обновляет существующий компонент после изменения его данных.

Использует `hooks.render`, `$`.

Непосредственные вызовы: `hooks.render`, `$`.

<a id="symbol-restoreFocus"></a>

## restoreFocus

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
function restoreFocus(key)
```

Возвращает фокус после обновления списка вложений.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$('invoiceList').querySelectorAll('[data-doc-action]')].find((element) => element.dataset.docAction === key.action && element.dataset.docInvoice === key.id && (element.dataset.docDocument || '') === key.document)?.focus`, `[...$('invoiceList').querySelectorAll('[data-doc-action]')].find`, `$('invoiceList').querySelectorAll`, `$`.

<a id="symbol-review"></a>

## review

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
async function review(record)
```

Показывает доступные действия проверки и изменения вложения.

Использует `/api/invoice`.

Непосредственные вызовы: `uiFor`, `request`, `apiUrl`, `Error`, `hooks.accept`, `saved.closing_documents.map((item) => item.name).join`, `saved.closing_documents.map`, `repaint`.

Прямые присваивания полям/свойствам: `ui.busy`, `ui.path`, `ui.revision`, `ui.conflict`, `ui.error`, `ui.message`.

<a id="symbol-row"></a>

## row

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
const row = (id) =>
```

Строит строку вложения счёта с состоянием публикации и удаления.

Использует `$`.

Непосредственные вызовы: `$('invoiceList').invoiceRecords?.find`, `$`.

<a id="symbol-size"></a>

## size

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
const size = (bytes) =>
```

Форматирует размер файла для интерфейса.

Использует `new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format`, `Intl.NumberFormat`.

Непосредственные вызовы: `new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format`, `Intl.NumberFormat`.

<a id="symbol-uiFor"></a>

## uiFor

[static/invoice-documents.js](../../../static/invoice-documents.js) · `ArrowFunctionExpression`.

```javascript
const uiFor = (record) =>
```

Получает локальное состояние редактора вложений выбранного счёта.

Использует `uploads.has`, `uploads.set`, `uploads.get`.

Непосредственные вызовы: `uploads.has`, `uploads.set`, `uploads.get`.

<a id="symbol-upload"></a>

## upload

[static/invoice-documents.js](../../../static/invoice-documents.js) · `FunctionDeclaration`.

```javascript
async function upload(record)
```

Передаёт выбранное вложение счёта в последовательную очередь сохранения.

Использует `/api/invoice-document-upload`.

Непосредственные вызовы: `uiFor`, `repaint`, `request`, `encoded`, `ui.files.shift`, `hooks.accept`, `notify`, `hooks.refresh`.

Прямые присваивания полям/свойствам: `ui.busy`, `ui.error`, `ui.message`, `ui.revision`, `ui.open`, `ui.conflict`.
