# static/spreadsheet-preview.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/spreadsheet-preview.js:1](../../../static/spreadsheet-preview.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## close

[static/spreadsheet-preview.js:6](../../../static/spreadsheet-preview.js#L6) · `FunctionDeclaration`.

```javascript
function close()
```

Закрывает компонент и освобождает его временное состояние в модуле браузерного просмотра таблиц.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `active.worker.terminate`, `clearTimeout`.

## open

[static/spreadsheet-preview.js:14](../../../static/spreadsheet-preview.js#L14) · `FunctionDeclaration`.

```javascript
function open(container, url, onError)
```

Открывает компонент и загружает его исходные данные в модуле браузерного просмотра таблиц.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `close`, `Worker`, `document.createElement`, `sheets.setAttribute`, `label.append`, `zoom.setAttribute`, `zoom.add`, `Option`, `zoomLabel.append`, `toolbar.append`, `scroll.setAttribute`, `previous.setAttribute`, `next.setAttribute`, `footer.append`, `viewer.append`, `container.replaceChildren`, `sheets.addEventListener`, `previous.addEventListener`, `next.addEventListener`, `zoom.addEventListener`, `send`.

Прямые присваивания полям/свойствам: `viewer.className`, `toolbar.className`, `label.textContent`, `sheets.disabled`, `zoomLabel.textContent`, `zoom.value`, `readonly.textContent`, `scroll.className`, `scroll.tabIndex`, `scroll.textContent`, `footer.className`, `previous.textContent`, `next.textContent`, `notice.className`, `footer.hidden`, `worker.onerror`, `worker.onmessage`.

## fail

[static/spreadsheet-preview.js:59](../../../static/spreadsheet-preview.js#L59) · `FunctionDeclaration`.

```javascript
function fail(message)
```

Показывает ошибку открытия таблицы и освобождает временные ресурсы.

Использует `close`, `onError`.

Непосредственные вызовы: `close`, `onError`.

## send

[static/spreadsheet-preview.js:66](../../../static/spreadsheet-preview.js#L66) · `FunctionDeclaration`.

```javascript
function send(message)
```

Передаёт команду отдельному Worker просмотра таблиц.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `setTimeout`, `worker.postMessage`.

Прямые присваивания полям/свойствам: `current.timeout`, `current.id`.

## changePage

[static/spreadsheet-preview.js:73](../../../static/spreadsheet-preview.js#L73) · `FunctionDeclaration`.

```javascript
function changePage(sheetIndex, offset)
```

Переключает отображаемую страницу текущего документа.

Использует `send`.

Непосредственные вызовы: `send`.

Прямые присваивания полям/свойствам: `previous.disabled`, `next.disabled`.

## resize

[static/spreadsheet-preview.js:82](../../../static/spreadsheet-preview.js#L82) · `FunctionDeclaration`.

```javascript
function resize()
```

Пересчитывает размеры видимой области просмотрщика таблицы.

Использует `Number`.

Непосредственные вызовы: `Number`.

Прямые присваивания полям/свойствам: `table.style.zoom`.

## columnName

[static/spreadsheet-preview.js:112](../../../static/spreadsheet-preview.js#L112) · `FunctionDeclaration`.

```javascript
function columnName(index)
```

Преобразует номер колонки в буквенное обозначение Excel.

Использует `Math.floor`, `String.fromCharCode`.

Непосредственные вызовы: `Math.floor`, `String.fromCharCode`.
