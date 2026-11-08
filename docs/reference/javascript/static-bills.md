# static/bills.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/bills.js](../../../static/bills.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-clientKey"></a>

## clientKey

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function clientKey(item)
```

Возвращает точный ключ клиента для фильтра общего списка.

Путь различает одноимённые папки, JSON отделяет отсутствие клиента от режима «Все клиенты».

Непосредственные вызовы: `JSON.stringify`.

<a id="symbol-compareRecords"></a>

## compareRecords

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function compareRecords(first, second)
```

Сравнивает счета по текущей колонке и направлению без изменения исходного массива.

Пустые значения всегда в конце, равные сохраняют устойчивый порядок ответа сервера.

Непосредственные вызовы: `sortValue`, `OrderSorting.text`.

<a id="symbol-date"></a>

## date

[static/bills.js](../../../static/bills.js) · `ArrowFunctionExpression`.

```javascript
const date = value =>
```

Форматирует дату счёта без преобразования часового пояса.

Нераспознанная или отсутствующая дата показана прочерком.

Непосредственные вызовы: `/^\d{4}-\d{2}-\d{2}$/.test`, `value.split('-').reverse().join`, `value.split('-').reverse`, `value.split`.

<a id="symbol-refresh"></a>

## refresh

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
async function refresh()
```

Обновляет общий список только при открытом финансовом разделе счетов.

Опрос читает SQLite; устаревший ответ после навигации не применяется.

Непосредственные вызовы: `$`, `renderInbox`, `renderCatalog`, `request`.

Прямые присваивания полям/свойствам: `$('billsCatalog').hidden`, `$('billsInbox').hidden`, `$('billsCatalogSearch').value`, `$('billsCatalogState').textContent`.

<a id="symbol-renderCatalog"></a>

## renderCatalog

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function renderCatalog()
```

Показывает счета с фильтром одного клиента, поиском, сортировкой и действиями правки.

Клиент выбирается по точному пути; обновление сохраняет фильтр, ссылки и доступные действия.

Непосредственные вызовы: `renderClientFilter`, `normalize`, `$('billsCatalogSearch').value.trim`, `$`, `records.filter(item => (!clientFilter || clientKey(item) === clientFilter) && (!query || normalize([item.label, item.client, item.order_title, item.path, item.comment, item.date, statuses[item.list_status]].join(' ')).includes(query))).sort`, `records.filter`, `renderSorting`, `visible.map(item => {
      const pdf = ['issued', 'external'].includes(item.state);
      const href = pdf ? apiUrl('/api/invoice-pdf', item.path, { id: item.id }) : '?path=' + encodeURIComponent(item.path);
      const type = { draft: 'Черновик', issued: 'Выпущен', external: 'Прикреплён' }[item.state];
      const editable = item.edit_action === 'edit' && item.state === 'draft' || item.edit_action === 'copy' && item.state === 'issued';
      const action = item.edit_action === 'edit' ? 'Редактировать' : 'Новая правка';
      const name = editable ? '<button type="button" class="bills-edit" data-bills-key="' + escapeHtml(item.id) + '" data-bills-edit="' + escapeHtml(item.id) + '" title="' + escapeHtml(item.edit_action === 'edit' ? 'Редактировать черновик · ' + item.label : 'Создать отдельный черновик на основе · ' + item.label) + '"' + (opening ? ' disabled' : '') + '><span>' + escapeHtml(item.label) + '</span><span class="bills-edit-badge">' + action + '</span></button>' : '<a data-bills-key="' + escapeHtml(item.id) + '" href="' + escapeHtml(href) + '"' + (pdf ? ' target="_blank" rel="noopener"' : ' data-bills-order="' + escapeHtml(item.path) + '"') + '>' + escapeHtml(item.label) + '</a>';
      return '<tr' + (editable ? ' class="bills-editable"' : '') + '><td class="bills-date">' + date(item.date) + '</td><td>' + name + '<small>' + escapeHtml(type) + (editable && pdf ? ' · <a data-bills-key="' + escapeHtml(item.id + ':pdf') + '" href="' + escapeHtml(href) + '" target="_blank" rel="noopener">PDF</a>' : '') + '</small>' + (item.comment ? '<small class="bills-comment" title="' + escapeHtml(item.comment) + '">' + escapeHtml(item.comment) + '</small>' : '') + '</td><td><button type="button" class="bills-client" data-bills-key="' + escapeHtml(item.id + ':client') + '" data-bills-client="' + escapeHtml(clientKey(item)) + '" title="' + escapeHtml('Показать только счета клиента · ' + (item.client || 'Без клиента')) + '">' + escapeHtml(item.client || '—') + '</button></td><td><a data-bills-key="' + escapeHtml(item.id + ':order') + '" data-bills-order="' + escapeHtml(item.path) + '" href="?path=' + encodeURIComponent(item.path) + '" title="' + escapeHtml(item.path) + '">' + escapeHtml(item.order_title) + '</a></td><td class="reconciliation-amount">' + (Number.isSafeInteger(item.total) ? rubles(item.total) : '—') + '</td><td>' + escapeHtml(item.list_status === null ? 'Неизвестная отметка' : statuses[item.list_status] || '—') + '</td></tr>';
    }).join`, `visible.map`, `replaceRows`.

Прямые присваивания полям/свойствам: `$('billsCatalogCount').textContent`, `$('billsCatalogState').textContent`.

<a id="symbol-renderClientFilter"></a>

## renderClientFilter

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function renderClientFilter()
```

Обновляет полный список клиентов независимо от поиска и выбранного фильтра.

Не меняет открытый select; исчезнувший выбранный клиент остаётся выбранным с пустым результатом.

Непосредственные вызовы: `Map`, `records.map`, `clients.values`, `names.set`, `normalize`, `names.get`, `[...clients.entries()].sort`, `clients.entries`, `entries.map(([key, item]) => {
      const label = names.get(normalize(item.name)) > 1 && item.path ? item.name + ' · ' + item.path : item.name;
      if (key === clientFilter) clientFilterLabel = label;
      return '<option value="' + escapeHtml(key) + '" data-client-label="' + escapeHtml(label) + '">' + escapeHtml(label) + '</option>';
    }).join`, `entries.map`, `clients.has`, `escapeHtml`, `$`.

Прямые присваивания полям/свойствам: `select.innerHTML`, `select.value`.

<a id="symbol-renderInbox"></a>

## renderInbox

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function renderInbox(folder)
```

Показывает непосредственные входящие файлы без прикрепления их к заказам.

Использует проверенный список открытой папки и прежний просмотрщик файлов.

Непосредственные вызовы: `replaceRows`, `files.map(file => '<tr><td><button type="button" class="bills-file" data-bills-key="' + escapeHtml(file.path) + '" data-bills-file="' + escapeHtml(file.path) + '">' + escapeHtml(file.name) + '</button></td><td class="bills-date">' + formatSize(file.size) + '</td><td class="bills-date">' + new Date(file.modified * 1000).toLocaleDateString('ru-RU') + '</td></tr>').join`, `files.map`, `$`.

Прямые присваивания полям/свойствам: `$('billsInboxCount').textContent`, `$('billsInboxState').textContent`.

<a id="symbol-renderSorting"></a>

## renderSorting

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function renderSorting()
```

Обновляет направление сортировки в заголовках для мыши и клавиатуры.

aria-sort отражает текущую колонку, подсказка описывает следующее переключение.

Непосредственные вызовы: `$('billsCatalog').querySelectorAll('[data-bills-sort]').forEach`, `$('billsCatalog').querySelectorAll`, `$`.

<a id="symbol-replaceRows"></a>

## replaceRows

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function replaceRows(id, html)
```

Заменяет строки списка, сохраняя фокус ссылки и положение прокрутки.

Неизменившаяся разметка не пересоздаётся; ключи ссылок устойчивы к опросу.

Непосредственные вызовы: `$`, `document.activeElement?.closest`, `document.querySelector`, `$(id).closest`, `[...$(id).querySelectorAll('[data-bills-key]')].find(item => item.dataset.billsKey === focused)?.focus`, `[...$(id).querySelectorAll('[data-bills-key]')].find`, `$(id).querySelectorAll`.

Прямые присваивания полям/свойствам: `$(id).innerHTML`, `pane.scrollTop`, `table.scrollLeft`.

<a id="symbol-selectClient"></a>

## selectClient

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function selectClient(key)
```

Применяет выбор клиента из списка или по имени в колонке.

Поиск и сортировка сохраняются; фильтрация не отправляет запросы записи.

Непосредственные вызовы: `[...$('billsClientFilter').options].find`, `$`, `renderCatalog`.

<a id="symbol-sortValue"></a>

## sortValue

[static/bills.js](../../../static/bills.js) · `FunctionDeclaration`.

```javascript
function sortValue(item)
```

Выбирает значение выбранной колонки для сортировки счетов.

Даты сравниваются в ISO, суммы — в копейках; отсутствующие значения возвращают null.

Непосредственные вызовы: `Number.isSafeInteger`, `/^\d{4}-\d{2}-\d{2}$/.test`, `item[sortKey]?.trim`.
