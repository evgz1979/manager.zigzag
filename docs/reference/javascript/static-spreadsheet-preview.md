# static/spreadsheet-preview.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-close"></a>

## close

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function close()
```

Закрывает компонент и освобождает его временное состояние в модуле браузерного просмотра таблиц.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `active.worker.terminate`, `clearTimeout`.

<a id="symbol-open"></a>

## open

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function open(container, url, onError)
```

Открывает компонент и загружает его исходные данные в модуле браузерного просмотра таблиц.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `close`, `Worker`, `document.createElement`, `sheets.setAttribute`, `label.append`, `zoom.setAttribute`, `zoom.add`, `Option`, `zoomLabel.append`, `toolbar.append`, `scroll.setAttribute`, `previous.setAttribute`, `next.setAttribute`, `footer.append`, `viewer.append`, `container.replaceChildren`, `sheets.addEventListener`, `previous.addEventListener`, `next.addEventListener`, `zoom.addEventListener`, `send`.

Прямые присваивания полям/свойствам: `viewer.className`, `toolbar.className`, `label.textContent`, `sheets.disabled`, `zoomLabel.textContent`, `zoom.value`, `readonly.textContent`, `scroll.className`, `scroll.tabIndex`, `scroll.textContent`, `footer.className`, `previous.textContent`, `next.textContent`, `notice.className`, `footer.hidden`, `worker.onerror`, `worker.onmessage`.

<a id="symbol-open.changePage"></a>

## open.changePage

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function changePage(sheetIndex, offset)
```

Переключает отображаемую страницу текущего документа.

Использует `send`.

Непосредственные вызовы: `send`.

Прямые присваивания полям/свойствам: `previous.disabled`, `next.disabled`.

<a id="symbol-open.columnName"></a>

## open.columnName

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function columnName(index)
```

Преобразует номер колонки в буквенное обозначение Excel.

Использует `Math.floor`, `String.fromCharCode`.

Непосредственные вызовы: `Math.floor`, `String.fromCharCode`.

<a id="symbol-open.fail"></a>

## open.fail

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function fail(message)
```

Показывает ошибку открытия таблицы и освобождает временные ресурсы.

Использует `close`, `onError`.

Непосредственные вызовы: `close`, `onError`.

<a id="symbol-open.resize"></a>

## open.resize

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function resize()
```

Пересчитывает размеры видимой области просмотрщика таблицы.

Использует `Number`.

Непосредственные вызовы: `Number`.

Прямые присваивания полям/свойствам: `table.style.zoom`.

<a id="symbol-open.send"></a>

## open.send

[static/spreadsheet-preview.js](../../../static/spreadsheet-preview.js) · `FunctionDeclaration`.

```javascript
function send(message)
```

Передаёт команду отдельному Worker просмотра таблиц.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `setTimeout`, `worker.postMessage`.

Прямые присваивания полям/свойствам: `current.timeout`, `current.id`.
