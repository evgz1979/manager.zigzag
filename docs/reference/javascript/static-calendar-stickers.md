# static/calendar-stickers.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/calendar-stickers.js](../../../static/calendar-stickers.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-accept"></a>

## accept

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function accept(entry, record, replaceDraft)
```

Принимает серверную запись как сохранённую или как текущий редакторский черновик.

Переводит SQLite 0/1 в boolean для следующих запросов и сравнений.

Непосредственные вызовы: `Boolean`.

Прямые присваивания полям/свойствам: `entry.saved`, `entry.draft`.

<a id="symbol-controls"></a>

## controls

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function controls(entry)
```

Обновляет кнопки листка с учётом сохранения, удаления и ошибки.

Ошибка доступна через подсказку кнопки, повторное действие запускает редактор.

Непосредственные вызовы: `element.classList.toggle`, `Boolean`, `element.setAttribute`, `String`.

Прямые присваивания полям/свойствам: `editor.readOnly`, `grip.disabled`, `dismiss.disabled`, `retry.hidden`, `retry.disabled`, `retry.textContent`, `retry.title`.

<a id="symbol-create"></a>

## create

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function create(entry)
```

Создаёт редактор листка и подключает ввод, ручку и удаление.

Элемент сохраняет идентичность при опросе и при переносе в другую неделю.

Непосредственные вызовы: `document.createElement`, `element.setAttribute`, `element.querySelectorAll`, `element.querySelector`, `Object.assign`, `grip.addEventListener`, `editor.addEventListener`, `retry.addEventListener`, `dismiss.addEventListener`.

Прямые присваивания полям/свойствам: `element.className`, `element.dataset.stickerId`, `element.innerHTML`.

<a id="symbol-dirty"></a>

## dirty

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function dirty(entry)
```

Проверяет, есть ли у листка ещё не сохранённые изменения.

Нулевая ревизия обозначает новый листок, даже если текст пока пуст.

Непосредственные вызовы: `fields.some`.

<a id="symbol-dragPointer"></a>

## dragPointer

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function dragPointer(event)
```

Превращает движение захваченного указателя в перетаскивание после небольшого порога.

Поддерживает мышь, палец и перо через Pointer Events.

Непосредственные вызовы: `Math.hypot`, `viewport.classList.add`, `drag.entry.element.classList.add`, `followPointer`.

Прямые присваивания полям/свойствам: `drag.x`, `drag.y`.

<a id="symbol-endDrag"></a>

## endDrag

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function endDrag(commit)
```

Завершает перетаскивание и записывает новую позицию только при отпускании указателя.

Отменённый захват или Escape возвращает листок в исходную точку.

Непосредственные вызовы: `cancelAnimationFrame`, `entry.grip.hasPointerCapture`, `entry.grip.releasePointerCapture`, `entry.element.classList.remove`, `entry.element.style.removeProperty`, `move`, `viewport.classList.remove`.

<a id="symbol-followPointer"></a>

## followPointer

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function followPointer()
```

Перемещает сам листок вслед за указателем и прокручивает сетку у краёв.

Предпросмотр не меняет сохранённое положение до завершения жеста.

Непосредственные вызовы: `viewport.getBoundingClientRect`, `speed`, `viewport.scrollBy`, `entry.element.parentElement.getBoundingClientRect`, `requestAnimationFrame`.

Прямые присваивания полям/свойствам: `entry.element.style.left`, `entry.element.style.top`, `drag.frame`.

<a id="symbol-followPointer.speed"></a>

## followPointer.speed

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `ArrowFunctionExpression`.

```javascript
const speed = (point, start, end) =>
```

Выбирает направление автопрокрутки у границы видимой области.

Средняя часть viewport даёт нулевой сдвиг.

<a id="symbol-move"></a>

## move

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function move(entry, x, y)
```

Сохраняет новое положение после перетаскивания или нажатия стрелки.

Доли вычисляются относительно соответствующей недели и сохраняются вместе с текстом.

Непосредственные вызовы: `position`, `Object.assign`, `HomeCalendar.show`, `save`.

<a id="symbol-position"></a>

## position

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function position(x, y)
```

Выбирает неделю по вертикальной координате центра листка.

За пределами сетки ближайшая крайняя неделя получает координату 0 или 10000.

Непосредственные вызовы: `rows.find`, `rows.at`, `row.getBoundingClientRect`, `ratio`.

<a id="symbol-position.ratio"></a>

## position.ratio

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `ArrowFunctionExpression`.

```javascript
const ratio = (value, size) =>
```

Преобразует координату в целую долю для хранения в SQLite.

Ограничивает результат границами выбранной недели.

Непосредственные вызовы: `Math.round`, `Math.min`, `Math.max`.

<a id="symbol-queueSave"></a>

## queueSave

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function queueSave(entry)
```

Планирует автосохранение после короткой паузы ввода.

При уходе из поля или перемещении листка сохранение вызывается сразу.

Непосредственные вызовы: `clearTimeout`, `setTimeout`.

Прямые присваивания полям/свойствам: `entry.timer`.

<a id="symbol-recover"></a>

## recover

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
async function recover(entry)
```

Повторяет временно неудачную запись или открывает актуальную версию после конфликта.

Замена конфликтующего черновика требует отдельного явного действия.

Непосредственные вызовы: `save`, `window.confirm`, `controls`, `request`, `encodeURIComponent`, `accept`, `remove`, `HomeCalendar.show`, `notify`, `entries.has`.

Прямые присваивания полям/свойствам: `entry.failure`, `entry.pending`.

<a id="symbol-remove"></a>

## remove

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function remove(entry)
```

Убирает листок из редактора и возвращает фокус кнопке добавления при необходимости.

Все отложенные сохранения этого листка отменяются.

Непосредственные вызовы: `clearTimeout`, `entries.delete`, `entry.element?.contains`, `addButton.focus`, `entry.element?.remove`.

<a id="symbol-render"></a>

## render

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function render()
```

Раскладывает листки поверх нужных недель и оставляет фокус при переносе.

Доли задают центр листка; соседние недели могут лежать под одним листком.

Непосредственные вызовы: `Map`, `[...calendar.children].map`, `entries.values`, `rows.get`, `create`, `element.style.setProperty`, `controls`, `element.contains`, `row.append`, `focus?.focus`.

Прямые присваивания полям/свойствам: `editor.value`.

<a id="symbol-save"></a>

## save

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
async function save(entry)
```

Сохраняет очередной снимок черновика одного листка.

Пока идёт запрос, следующий ввод остаётся в черновике и записывается после ответа.

Непосредственные вызовы: `clearTimeout`, `dirty`, `controls`, `request`, `accept`, `remove`, `HomeCalendar.show`, `notify`, `entries.has`, `queueSave`.

Прямые присваивания полям/свойствам: `entry.pending`, `entry.failure`.

<a id="symbol-startDrag"></a>

## startDrag

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function startDrag(entry, event)
```

Начинает жест только с ручки листка и захватывает один указатель.

Текст по-прежнему выделяется и редактируется в отдельном поле.

Непосредственные вызовы: `event.preventDefault`, `entry.grip.focus`, `entry.element.getBoundingClientRect`, `entry.grip.setPointerCapture`.

<a id="symbol-update"></a>

## update

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function update(records, generation)
```

Переносит свежие изменения из общей сводки в редактор.

Черновики и листок под указателем остаются локальными до окончания операции.

Непосредственные вызовы: `Array.isArray`, `Set`, `incoming.add`, `entries.has`, `entries.set`, `entries.get`, `dirty`, `accept`, `incoming.has`, `remove`.

Прямые присваивания полям/свойствам: `addButton.disabled`.

<a id="symbol-weeks"></a>

## weeks

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function weeks()
```

Возвращает даты недель, которые нужны для показа всех открытых стикеров.

Черновик передаёт новое положение сразу после отпускания указателя.

Непосредственные вызовы: `Set`, `[...entries.values()].map`, `entries.values`.

<a id="symbol-writeVersion"></a>

## writeVersion

[static/calendar-stickers.js](../../../static/calendar-stickers.js) · `FunctionDeclaration`.

```javascript
function writeVersion()
```

Возвращает поколение записей перед запросом очередной сводки.

Начало и завершение записи меняют поколение, поэтому старый список пропускается.
