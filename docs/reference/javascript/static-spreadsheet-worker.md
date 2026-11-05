# static/spreadsheet-worker.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/spreadsheet-worker.js](../../../static/spreadsheet-worker.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-page"></a>

## page

[static/spreadsheet-worker.js](../../../static/spreadsheet-worker.js) · `FunctionDeclaration`.

```javascript
function page(sheetIndex, offset)
```

Формирует ограниченную порцию строк таблицы для браузерного окна.

Использует `Error`, `XLSX.utils.decode_range`, `Math.min`.

Непосредственные вызовы: `Error`, `XLSX.utils.decode_range`, `Math.min`, `Math.floor`, `Math.max`, `line.push`, `value`, `cells.push`, `heights.push`, `widths.push`, `merges.push`.

<a id="symbol-page.value"></a>

## page.value

[static/spreadsheet-worker.js](../../../static/spreadsheet-worker.js) · `FunctionDeclaration`.

```javascript
function value(row, column)
```

Извлекает форматированное значение ячейки или части даты.

Использует `XLSX.utils.encode_cell`, `XLSX.SSF.is_date`, `XLSX.SSF.format`.

Непосредственные вызовы: `XLSX.utils.encode_cell`, `XLSX.SSF.is_date`, `XLSX.SSF.format`, `cell.z.replace`, `Boolean`, `String`.
