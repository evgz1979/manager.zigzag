# static/spreadsheet-worker.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/spreadsheet-worker.js:1](../../../static/spreadsheet-worker.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## page

[static/spreadsheet-worker.js:9](../../../static/spreadsheet-worker.js#L9) · `FunctionDeclaration`.

```javascript
function page(sheetIndex, offset)
```

Формирует ограниченную порцию строк таблицы для браузерного окна.

Использует `Error`, `XLSX.utils.decode_range`, `Math.min`.

Непосредственные вызовы: `Error`, `XLSX.utils.decode_range`, `Math.min`, `Math.floor`, `Math.max`, `line.push`, `value`, `cells.push`, `heights.push`, `widths.push`, `merges.push`.

## value

[static/spreadsheet-worker.js:25](../../../static/spreadsheet-worker.js#L25) · `FunctionDeclaration`.

```javascript
function value(row, column)
```

Извлекает форматированное значение ячейки или части даты.

Использует `XLSX.utils.encode_cell`, `XLSX.SSF.is_date`, `XLSX.SSF.format`.

Непосредственные вызовы: `XLSX.utils.encode_cell`, `XLSX.SSF.is_date`, `XLSX.SSF.format`, `cell.z.replace`, `Boolean`, `String`.
