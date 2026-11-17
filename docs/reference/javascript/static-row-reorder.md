# static/row-reorder.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/row-reorder.js](../../../static/row-reorder.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-bindRowReorder"></a>

## bindRowReorder

[static/row-reorder.js](../../../static/row-reorder.js) · `FunctionDeclaration`.

```javascript
function bindRowReorder(list, rowSelector, transferType, changed)
```

Подключает ручки перемещения строк мышью и клавиатурой.

Меняет DOM только при вставке, возвращает фокус ручке и вызывает changed после перестановки.

Непосредственные вызовы: `list.addEventListener`.

<a id="symbol-bindRowReorder.clearDrag"></a>

## bindRowReorder.clearDrag

[static/row-reorder.js](../../../static/row-reorder.js) · `FunctionDeclaration`.

```javascript
function clearDrag()
```

Очищает подсветку при вставке, отмене и замене списка.

Можно вызывать без активного перетаскивания.

Непосредственные вызовы: `markDrop`, `drag.row.classList.remove`.

<a id="symbol-bindRowReorder.dropPosition"></a>

## bindRowReorder.dropPosition

[static/row-reorder.js](../../../static/row-reorder.js) · `FunctionDeclaration`.

```javascript
function dropPosition(event)
```

Находит точку вставки по верхней или нижней половине строки.

Возвращает null вне списка и при сохранении текущего порядка.

Непосредственные вызовы: `event.target.closest`, `target.getBoundingClientRect`.

<a id="symbol-bindRowReorder.markDrop"></a>

## bindRowReorder.markDrop

[static/row-reorder.js](../../../static/row-reorder.js) · `FunctionDeclaration`.

```javascript
function markDrop(position)
```

Показывает линию вставки у подходящего края строки.

Положение линии не меняет порядок до завершения перетаскивания.

Непосредственные вызовы: `marker?.target.removeAttribute`.

Прямые присваивания полям/свойствам: `position.target.dataset.rowDrop`, `drag.marker`.

<a id="symbol-bindRowReorder.moveRow"></a>

## bindRowReorder.moveRow

[static/row-reorder.js](../../../static/row-reorder.js) · `FunctionDeclaration`.

```javascript
function moveRow(row, before)
```

Вставляет существующий узел перед соседней строкой или в конец.

Сохраняет поля узла и передаёт новый порядок владельцу списка.

Непосредственные вызовы: `list.insertBefore`, `row.querySelector(".row-drag-handle").focus`, `row.querySelector`, `changed`.
