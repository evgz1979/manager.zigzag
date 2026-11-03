# static/app.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/app.js:1](../../../static/app.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## $

[static/app.js:3](../../../static/app.js#L3) · `ArrowFunctionExpression`.

```javascript
const $ = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

## icon

[static/app.js:53](../../../static/app.js#L53) · `ArrowFunctionExpression`.

```javascript
const icon = (name) =>
```

Строит SVG-значок из локального набора символов.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## escapeHtml

[static/app.js:56](../../../static/app.js#L56) · `ArrowFunctionExpression`.

```javascript
const escapeHtml = (value) =>
```

Экранирует текст перед вставкой в HTML-разметку или атрибут.

Заменяет &, <, >, кавычки и апостроф на безопасные HTML-сущности.

Непосредственные вызовы: `String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll`, `String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll`, `String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll`, `String(value).replaceAll("&", "&amp;").replaceAll`, `String(value).replaceAll`, `String`.

## normalize

[static/app.js:59](../../../static/app.js#L59) · `ArrowFunctionExpression`.

```javascript
const normalize = (value) =>
```

Нормализует строку для поиска и сравнения без учёта регистра.

Использует `String(value).normalize("NFC").toLocaleLowerCase`, `String(value).normalize`, `String`.

Непосредственные вызовы: `String(value).normalize("NFC").toLocaleLowerCase`, `String(value).normalize`, `String`.

## isWorkOrderPath

[static/app.js:62](../../../static/app.js#L62) · `ArrowFunctionExpression`.

```javascript
const isWorkOrderPath = (path) =>
```

Определяет производственную область по относительному пути заказа.

Использует `/^#\s*work$/i.test`, `String(path || "").split`, `String`.

Непосредственные вызовы: `/^#\s*work$/i.test`, `String(path || "").split`, `String`.

## apiUrl

[static/app.js:65](../../../static/app.js#L65) · `ArrowFunctionExpression`.

```javascript
const apiUrl = (route, path = "", extra = {}) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `URLSearchParams`.

Непосредственные вызовы: `URLSearchParams`.

## treeUrl

[static/app.js:68](../../../static/app.js#L68) · `ArrowFunctionExpression`.

```javascript
const treeUrl = (path = "", extra = {}) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `/api/tree`.

Непосредственные вызовы: `apiUrl`.

## folderUrl

[static/app.js:71](../../../static/app.js#L71) · `ArrowFunctionExpression`.

```javascript
const folderUrl = (path) =>
```

Собирает URL запроса с безопасным кодированием параметров.

Использует `/api/folder`.

Непосредственные вызовы: `apiUrl`.

## formatSize

[static/app.js:74](../../../static/app.js#L74) · `ArrowFunctionExpression`.

```javascript
const formatSize = (bytes) =>
```

Форматирует размер файла для интерфейса.

Использует `Math.round`, `(bytes / 1024 ** 2).toFixed`, `(bytes / 1024 ** 3).toFixed`.

Непосредственные вызовы: `Math.round`, `(bytes / 1024 ** 2).toFixed`, `(bytes / 1024 ** 3).toFixed`.

## formatDate

[static/app.js:82](../../../static/app.js#L82) · `ArrowFunctionExpression`.

```javascript
const formatDate = (seconds) =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `new Date(seconds * 1000).toLocaleDateString`, `Date`.

Непосредственные вызовы: `new Date(seconds * 1000).toLocaleDateString`, `Date`.

## printCountLabel

[static/app.js:85](../../../static/app.js#L85) · `ArrowFunctionExpression`.

```javascript
const printCountLabel = (count) =>
```

Выбирает русскую подпись количества заданий печати.

Использует `new Intl.PluralRules("ru").select`, `Intl.PluralRules`.

Непосредственные вызовы: `new Intl.PluralRules("ru").select`, `Intl.PluralRules`.

## folderParent

[static/app.js:88](../../../static/app.js#L88) · `ArrowFunctionExpression`.

```javascript
const folderParent = (path) =>
```

Вычисляет относительный путь родительской папки.

Использует `path.split("/").slice(0, -1).join`, `path.split("/").slice`, `path.split`.

Непосредственные вызовы: `path.split("/").slice(0, -1).join`, `path.split("/").slice`, `path.split`.

## renderUpload

[static/app.js:92](../../../static/app.js#L92) · `FunctionDeclaration`.

```javascript
function renderUpload()
```

Обновляет прогресс и результаты текущей последовательной загрузки файлов.

Использует `$`, `Boolean`, `formatSize`.

Непосредственные вызовы: `$`, `Boolean`, `formatSize`, `$("uploadDestination").setAttribute`, `Math.round`, `job.results.filter`, `$("uploadSummary").classList.toggle`, `job.results.map((item) => '<li' + (item.error ? ' class="error"' : '') + '>' + escapeHtml(item.error ? item.original + " — " + item.error : item.name + " · сохранён") + '</li>').join`, `job.results.map`.

Прямые присваивания полям/свойствам: `$("uploadPanel").hidden`, `$("chooseUploadFiles").disabled`, `$("uploadDropHint").textContent`, `$("uploadTitle").textContent`, `$("uploadDestination").textContent`, `$("uploadDestination").title`, `$("uploadCurrent").textContent`, `$("uploadProgress").hidden`, `$("uploadProgress").value`, `$("closeUploadPanel").hidden`, `$("uploadSummary").textContent`, `$("uploadResults").innerHTML`.

## sendUpload

[static/app.js:115](../../../static/app.js#L115) · `FunctionDeclaration`.

```javascript
function sendUpload(file, job)
```

Передаёт один файл с привязкой к открытой папке и обновлением прогресса.

Использует `/api/file-upload`.

Непосредственные вызовы: `Promise`.

## refreshUploadedFiles

[static/app.js:139](../../../static/app.js#L139) · `FunctionDeclaration`.

```javascript
async function refreshUploadedFiles(job)
```

Перечитывает содержимое папки после успешных загрузок.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `request`, `folderUrl`, `Math.max`, `job.results.filter`, `renderFiles`, `$`, `formatSize`.

Прямые присваивания полям/свойствам: `folder[key]`, `state.limit`, `$("folderSummary").textContent`.

## uploadFiles

[static/app.js:152](../../../static/app.js#L152) · `FunctionDeclaration`.

```javascript
async function uploadFiles(files)
```

Последовательно загружает выбранные файлы с сохранением отдельных результатов.

Использует `notify`, `$`, `renderUpload`.

Непосредственные вызовы: `notify`, `$`, `renderUpload`, `Error`, `formatSize`, `job.results.push`, `sendUpload`, `files.slice`, `job.results.some`, `refreshUploadedFiles(job).catch`, `refreshUploadedFiles`.

Прямые присваивания полям/свойствам: `state.upload`, `$("uploadDetails").open`, `job.index`, `job.filename`, `job.size`, `job.sent`, `job.busy`.

## request

[static/app.js:183](../../../static/app.js#L183) · `FunctionDeclaration`.

```javascript
async function request(url, payload)
```

Отправляет запрос серверу и преобразует HTTP-ошибку в исключение интерфейса.

Использует `/api/reconciliation-save`, `/api/invoice-reconciliation`.

Непосредственные вызовы: `fetch`, `['/api/reconciliation-save', '/api/invoice-reconciliation'].includes`, `JSON.stringify`, `response.json`, `Error`.

Прямые присваивания полям/свойствам: `error.status`.

## notify

[static/app.js:198](../../../static/app.js#L198) · `FunctionDeclaration`.

```javascript
function notify(message, error = false, action = null)
```

Показывает сообщение пользователю и предусмотренное действие отмены.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `clearTimeout`, `$`, `document.createElement`, `button.addEventListener`, `$("toast").append`, `$("toast").classList.toggle`, `setTimeout`.

Прямые присваивания полям/свойствам: `$("toast").textContent`, `button.type`, `button.textContent`, `$("toast").hidden`.

## registerNodes

[static/app.js:218](../../../static/app.js#L218) · `FunctionDeclaration`.

```javascript
function registerNodes(nodes)
```

Запоминает узлы дерева для последующих раскрытий и навигации.

Использует `state.nodes.set`, `registerNodes`.

Непосредственные вызовы: `state.nodes.set`, `registerNodes`.

## treeMarkup

[static/app.js:227](../../../static/app.js#L227) · `FunctionDeclaration`.

```javascript
function treeMarkup(nodes, depth = 0, searching = false)
```

Строит разметку ветвей дерева из полученных узлов.

Использует `nodes.map`.

Непосредственные вызовы: `nodes.map((node, index) => {
    const open = searching ? Boolean(node.children?.length) : state.expanded.has(node.path);
    const children = searching ? node.children || [] : state.children.get(node.path) || [];
    const selected = node.path === state.selected;
    const tabIndex = selected || (!state.selected && depth === 0 && index === 0) ? 0 : -1;
    return '<div class="tree-branch" role="none"><div class="tree-row' + (selected ? " selected" : "") + (node.inactive ? " inactive" : "") +
      '" role="treeitem" tabindex="' + tabIndex + '" aria-selected="' + selected + '"' +
      (node.hasChildren ? ' aria-expanded="' + open + '"' : "") + ' aria-level="' + (depth + 1) +
      '" data-path="' + escapeHtml(node.path) + '" style="--depth:' + depth + '" title="' + escapeHtml(node.name + (node.inactive ? " · Неактивная папка" : "")) + '">' +
      '<button class="tree-toggle' + (open ? " expanded" : "") + '" tabindex="-1" aria-label="' +
      (open ? "Свернуть " : "Раскрыть ") + escapeHtml(node.name) + '"' + (!node.hasChildren ? ' disabled aria-hidden="true"' : "") + ">" +
      icon("chevron") + "</button>" + icon("folder") + '<span class="tree-name">' + escapeHtml(node.name) +
      '</span></div>' + (open && children.length ? '<div role="group">' + treeMarkup(children, depth + 1, searching) + "</div>" : "") + "</div>";
  }).join`, `nodes.map`.

## renderFavoriteOrders

[static/app.js:246](../../../static/app.js#L246) · `FunctionDeclaration`.

```javascript
function renderFavoriteOrders()
```

Показывает избранные заказы в панели навигации.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `state.favoriteOrders.filter((order) => order.is_favorite === true && order.supplier_status !== "archived").sort`, `state.favoriteOrders.filter`, `favorites.map((order) => {
    const active = state.view !== "orders" && (state.selected === order.path || state.selected.startsWith(order.path + "/"));
    return '<button type="button" class="favorite-order-button' + (active ? ' active' : '') + '" data-path="' + escapeHtml(order.path) + '" title="' + escapeHtml(order.title + " · " + (order.client || "") + "\n" + order.path) + '"' + (active ? ' aria-current="page"' : '') + '><span class="favorite-order-star" aria-hidden="true">★</span><span class="favorite-order-text"><span class="favorite-order-title">' + escapeHtml(order.title) + '</span>' + (order.client ? '<span class="favorite-order-client">' + escapeHtml(order.client) + '</span>' : '') + '</span></button>';
  }).join`, `favorites.map`, `container.contains`, `[...container.querySelectorAll("[data-path]")].find((button) => button.dataset.path === focusedPath)?.focus`, `[...container.querySelectorAll("[data-path]")].find`, `container.querySelectorAll`.

Прямые присваивания полям/свойствам: `container.innerHTML`, `container.scrollTop`, `container.hidden`.

## renderTree

[static/app.js:266](../../../static/app.js#L266) · `FunctionDeclaration`.

```javascript
function renderTree()
```

Обновляет DOM дерева для текущего состояния навигации.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.activeElement?.closest`, `Boolean`, `$`, `markup`, `data.groups.map((group) => '<section class="catalog-tree-section"><div class="tree-heading catalog-tree-heading"><button type="button" data-catalog-group="' + escapeHtml(group.path) + '" title="Открыть группу ' + escapeHtml(group.name) + '"' + (state.selected === group.path ? ' aria-current="page"' : '') + '>' + escapeHtml(group.name) + '</button><span>' + (group.error ? "—" : group.children.length) + '</span></div><div role="tree" aria-label="Группа ' + escapeHtml(group.name) + '">' + (group.error ? '<p class="tree-empty" role="status">' + escapeHtml(group.error) + '</p>' : markup(group.children)) + '</div></section>').join`, `data.groups.map`, `$("folderTree").querySelectorAll`, `tree.querySelectorAll`, `rows.find`, `rows.forEach`, `focusTree`, `[...$("folderTree").querySelectorAll("[data-catalog-group]")].find((button) => button.dataset.catalogGroup === focusedGroup)?.focus`, `[...$("folderTree").querySelectorAll("[data-catalog-group]")].find`, `state.auxiliary.map((node) =>
    '<button class="auxiliary-button' + (state.selected === node.path || state.selected.startsWith(node.path + "/") ? " active" : "") +
    '" data-path="' + escapeHtml(node.path) + '" title="' + escapeHtml(node.name) + '">' + icon("folder") +
    '<span>' + escapeHtml(node.name) + "</span></button>").join`, `state.auxiliary.map`, `renderFavoriteOrders`.

Прямые присваивания полям/свойствам: `$("folderTree").innerHTML`, `$("auxiliaryButtons").innerHTML`, `$("auxiliaryButtons").hidden`.

## markup

[static/app.js:273](../../../static/app.js#L273) · `ArrowFunctionExpression`.

```javascript
const markup = (nodes) =>
```

Формирует HTML текущего компонента из переданных данных.

Использует `treeMarkup`.

Непосредственные вызовы: `treeMarkup`.

## focusTree

[static/app.js:293](../../../static/app.js#L293) · `FunctionDeclaration`.

```javascript
function focusTree(path)
```

Возвращает клавиатурный фокус в нужный узел дерева.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$("folderTree").querySelectorAll(".tree-row")].find`, `$("folderTree").querySelectorAll`, `$`, `row.closest('[role="tree"]').querySelectorAll(".tree-row").forEach`, `row.closest('[role="tree"]').querySelectorAll`, `row.closest`, `row.focus`.

Прямые присваивания полям/свойствам: `row.tabIndex`.

## loadChildren

[static/app.js:304](../../../static/app.js#L304) · `FunctionDeclaration`.

```javascript
async function loadChildren(path)
```

Загружает непосредственных потомков раскрываемого узла.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `state.children.has`, `request`, `treeUrl`, `registerNodes`, `state.children.set`, `state.children.get`.

## toggleFolder

[static/app.js:315](../../../static/app.js#L315) · `FunctionDeclaration`.

```javascript
async function toggleFolder(path, forceOpen = false)
```

Раскрывает или сворачивает ветвь дерева папок.

Использует `state.expanded.has`, `state.expanded.delete`, `loadChildren`.

Непосредственные вызовы: `state.expanded.has`, `state.expanded.delete`, `loadChildren`, `state.expanded.add`, `renderTree`.

## revealPath

[static/app.js:328](../../../static/app.js#L328) · `FunctionDeclaration`.

```javascript
async function revealPath(path, navigation)
```

Последовательно раскрывает дерево до выбранной папки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `state.auxiliary.some`, `path.split`, `parts.slice(0, index).join`, `parts.slice`, `loadChildren`, `state.expanded.add`, `renderTree`, `$("folderTree").querySelector`, `$`, `selected?.scrollIntoView`.

## loadTree

[static/app.js:346](../../../static/app.js#L346) · `FunctionDeclaration`.

```javascript
async function loadTree()
```

Загружает дерево текущего корня с учётом поиска и области.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `request`, `treeUrl`, `state.nodes.clear`, `state.children.clear`, `registerNodes`, `state.children.set`, `$`, `[...state.expanded].sort`, `loadChildren`, `state.expanded.delete`, `renderTree`.

Прямые присваивания полям/свойствам: `state.tree`, `state.groups`, `state.auxiliary`, `$("rootLabel").textContent`, `$("rootLabel").title`.

## reloadClientTrees

[static/app.js:365](../../../static/app.js#L365) · `FunctionDeclaration`.

```javascript
async function reloadClientTrees()
```

Перечитывает деревья клиентов после изменения индекса активности.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `clearTimeout`, `loadTree`, `state.treeQuery.trim`, `request`, `treeUrl`, `registerNodes`, `renderTree`.

Прямые присваивания полям/свойствам: `state.searchTree`.

## folderActivity

[static/app.js:382](../../../static/app.js#L382) · `FunctionDeclaration`.

```javascript
function folderActivity(folder)
```

Выбирает состояние активности папки текущей роли.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## activityRoute

[static/app.js:388](../../../static/app.js#L388) · `FunctionDeclaration`.

```javascript
function activityRoute(folder)
```

Выбирает API активности клиента или объекта.

Использует `/api/object-activity`, `/api/client-activity`.

## updateFolderActivity

[static/app.js:394](../../../static/app.js#L394) · `FunctionDeclaration`.

```javascript
function updateFolderActivity(folder, activity)
```

Применяет подтверждённую активность к локальному состоянию интерфейса.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

Прямые присваивания полям/свойствам: `folder[folder.objectActivity ? "objectActivity" : "clientActivity"]`.

## renderClientActivity

[static/app.js:400](../../../static/app.js#L400) · `FunctionDeclaration`.

```javascript
function renderClientActivity()
```

Показывает состояние активности клиента или объекта и действия пользователя.

Использует `folderActivity`, `$`, `Boolean`.

Непосредственные вызовы: `folderActivity`, `$`, `Boolean`, `$("clientActivityCard").setAttribute`, `$("clientActivityState").classList.toggle`.

Прямые присваивания полям/свойствам: `$("folderFooter").hidden`, `$("clientActivityCard").hidden`, `$("activityLabel").textContent`, `$("activityHint").textContent`, `$("clientInactive").checked`, `$("clientInactive").disabled`, `$("clientActivityState").textContent`, `$("clientActivityAcceptFile").hidden`, `$("clientActivityAcceptFile").disabled`.

## saveClientActivity

[static/app.js:419](../../../static/app.js#L419) · `FunctionDeclaration`.

```javascript
async function saveClientActivity(inactive, acceptFile = false)
```

Сохраняет выбранную активность с версией текущей записи.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `folderActivity`, `renderClientActivity`, `saveCurrentStatus`, `updateFolderActivity`, `request`, `activityRoute`, `reloadClientTrees`, `loadOrders`, `apiUrl`.

Прямые присваивания полям/свойствам: `state.clientActivitySaving`.

## renderSketches

[static/app.js:444](../../../static/app.js#L444) · `FunctionDeclaration`.

```javascript
function renderSketches()
```

Показывает непосредственные CDR и их актуальность в карточке заказа.

Использует `/api/thumbnail`.

Непосредственные вызовы: `document.activeElement?.closest`, `$`, `files.map((item) => {
    const relevance = item.relevance, saving = folder.sketchSavingFolders?.has(item.folder);
    const message = saving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder sketch-tile" data-relevance-state="' + escapeHtml(relevance.value || "none") + '">' +
      '<button class="subfolder sketch-open" data-sketch-open="' + escapeHtml(item.path) + '" data-sketch-key="' + escapeHtml(item.key) + '" title="' + escapeHtml(item.name + " · Открыть в CorelDRAW на M4") + '" aria-label="' + escapeHtml("Открыть в CorelDRAW: " + item.name) + '"' + (item.opening ? ' disabled' : '') + '>' +
      '<span class="sketch-picture"><img data-thumbnail-path="' + escapeHtml(item.path) + '" data-thumbnail-key="' + escapeHtml(item.thumbnail_key) + '" src="' + escapeHtml(apiUrl("/api/thumbnail", item.path, { v: item.thumbnail_key })) + '" alt="" loading="lazy" decoding="async"><span class="sketch-fallback">CDR</span></span><span class="sketch-name">' + escapeHtml(item.name) + '</span></button>' +
      '<div class="event-relevance" role="group" aria-label="' + escapeHtml("Актуальность эскиза " + item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-sketch-file="' + escapeHtml(item.path) + '" data-sketch-status="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (saving || relevance.error || !relevance.revision ? ' disabled' : '') + '>' + label + '</button>').join("") + '</div>' +
      (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? ' error' : '') + '" role="status">' + escapeHtml(message) + '</p>' : '') + '</div>';
  }).join`, `files.map`, `[...$("sketchTiles").querySelectorAll("[data-sketch-status]")].find((button) => button.dataset.sketchFile === focusPath && button.dataset.sketchStatus === focusValue)?.focus`, `[...$("sketchTiles").querySelectorAll("[data-sketch-status]")].find`, `$("sketchTiles").querySelectorAll`.

Прямые присваивания полям/свойствам: `$("sketchSection").hidden`, `$("sketchCount").textContent`, `$("sketchTiles").innerHTML`.

## applySketchGroup

[static/app.js:467](../../../static/app.js#L467) · `FunctionDeclaration`.

```javascript
function applySketchGroup(folder, path, record)
```

Применяет полученную группу актуальности эскизов к локальному состоянию.

Использует `item.name.normalize`, `JSON.stringify`.

Непосредственные вызовы: `item.name.normalize`, `JSON.stringify`.

Прямые присваивания полям/свойствам: `item.relevance`.

## refreshSketchRelevance

[static/app.js:480](../../../static/app.js#L480) · `FunctionDeclaration`.

```javascript
async function refreshSketchRelevance(folder)
```

Перечитывает сохранённую актуальность эскизов из базы.

Использует `/api/sketch-relevance`.

Непосредственные вызовы: `request`, `apiUrl`, `Object.entries`, `folder.sketchSavingFolders?.has`, `applySketchGroup`, `renderSketches`.

## saveSketchRelevance

[static/app.js:493](../../../static/app.js#L493) · `FunctionDeclaration`.

```javascript
async function saveSketchRelevance(path, value)
```

Сохраняет актуальность конкретного эскиза с проверочной привязкой.

Использует `/api/sketch-relevance`.

Непосредственные вызовы: `folder?.sketches?.find`, `folder.sketchSavingFolders?.has`, `Set`, `folder.sketchSavingFolders.add`, `renderSketches`, `request`, `Error`, `applySketchGroup`, `apiUrl`, `folder.sketchSavingFolders.delete`.

Прямые присваивания полям/свойствам: `folder.sketchSavingFolders`.

## openSketch

[static/app.js:519](../../../static/app.js#L519) · `FunctionDeclaration`.

```javascript
async function openSketch(path, key)
```

Запрашивает открытие исходного CDR на серверном Mac.

Использует `/api/sketch-open`.

Непосредственные вызовы: `folder?.sketches?.find`, `renderSketches`, `request`, `notify`.

Прямые присваивания полям/свойствам: `item.opening`.

## subfolderButton

[static/app.js:535](../../../static/app.js#L535) · `FunctionDeclaration`.

```javascript
function subfolderButton(item)
```

Строит кнопку подпапки с ролью и доступными действиями.

Использует `Number.isSafeInteger`, `Number`, `escapeHtml`.

Непосредственные вызовы: `Number.isSafeInteger`, `Number`, `escapeHtml`, `icon`, `Boolean`, `state.supplierFavoriteSaving.has`.

## renderSubfolders

[static/app.js:555](../../../static/app.js#L555) · `FunctionDeclaration`.

```javascript
function renderSubfolders()
```

Показывает подпапки текущей папки согласно их ролям.

Использует `/api/thumbnail-cover`.

Непосредственные вызовы: `$("subfolders").classList.toggle`, `$`, `document.activeElement?.closest`, `document.querySelector`, `folder.directories.filter`, `Boolean`, `folder.directories.map(subfolderButton).join`, `folder.directories.map`, `normalize`, `$("frezaTaskSearch").value.trim`, `visibleDirectories.filter((item) => !query || normalize(item.name).includes(query)).sort`, `visibleDirectories.filter`, `$("subfolders").classList.remove`, `tasks.map((item) => '<button type="button" class="subfolder freza-task" data-path="' + escapeHtml(item.path) + '"><span class="freza-task-picture"><img data-thumbnail-folder="' + escapeHtml(item.path) + '" src="' + escapeHtml(apiUrl("/api/thumbnail-cover", item.path)) + '" alt="" loading="lazy" decoding="async"><span class="thumbnail-fallback">' + icon("file") + '</span></span><span>' + escapeHtml(item.name) + '</span>' + icon("chevron") + '</button>').join`, `tasks.map`, `directories.filter((item) => item.supplierFavorite?.is_favorite === true).sort`, `directories.filter`, `isWorkOrderList`, `$("workOrdersSection").setAttribute`, `$("workOrdersSection").classList.toggle`, `workOrders.map(subfolderButton).join`, `workOrders.map`, `folder.directories.map((item) => '<button type="button" class="subfolder" data-path="' + escapeHtml(item.path) + '">' + icon("folder") + '<span>' + escapeHtml(item.name) + '</span>' + icon("chevron") + '</button>').join`, `directories.some`, `["supplier_root", "work_section"].includes`, `directories.map((item, index) => {
    const open = subfolderButton(item);
    const relevance = item.eventRelevance;
    if (!relevance) return (supplierDividerAfter && index === supplierDividerAfter ? '<hr class="work-supplier-divider">' : "") + open;
    const message = item.relevanceSaving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder" data-relevance-state="' + escapeHtml(relevance.value || "none") + '" aria-busy="' + Boolean(item.relevanceSaving) + '">' + open +
      '<div class="event-relevance" role="group" aria-label="Актуальность события ' + escapeHtml(item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-event-path="' + escapeHtml(item.path) + '" data-relevance="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (item.relevanceSaving || relevance.error || !relevance.revision ? " disabled" : "") + '>' + label + '</button>').join("") +
      '</div>' + (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? " error" : "") + '" role="status">' + escapeHtml(message) + '</p>' : "") + '</div>';
  }).join`, `directories.map`, `[...$("subfolders").querySelectorAll("[data-relevance]")].find((button) => button.dataset.eventPath === focusPath && button.dataset.relevance === focusValue)?.focus`, `[...$("subfolders").querySelectorAll("[data-relevance]")].find`, `$("subfolders").querySelectorAll`, `focusSupplierStar`, `[...$("subfolders").querySelectorAll("[data-path]")].find(button => button.dataset.path === focusedFolder)?.focus`, `[...$("subfolders").querySelectorAll("[data-path]")].find`.

Прямые присваивания полям/свойствам: `$("frezaTaskSearchLabel").hidden`, `$("frezaLegacyFolders").hidden`, `$("folderSection").hidden`, `$("workOrdersSection").hidden`, `$("printLegacyFolders").hidden`, `$("frezaLegacyCount").textContent`, `$("frezaLegacyList").innerHTML`, `$("foldersTitle").textContent`, `$("directoryCount").textContent`, `$("subfolders").innerHTML`, `$("workOrdersTitle").textContent`, `$("workOrderFolders").innerHTML`, `$("printLegacyFolderCount").textContent`, `$("printLegacyFolderList").innerHTML`, `document.querySelector(".content-pane").scrollTop`.

## focusSupplierStar

[static/app.js:645](../../../static/app.js#L645) · `FunctionDeclaration`.

```javascript
function focusSupplierStar(path)
```

Возвращает фокус на звезду выбранного раздела поставщика.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `[...$("subfolders").querySelectorAll("[data-supplier-favorite]")].find((button) => button.dataset.supplierFavorite === path)?.focus`, `[...$("subfolders").querySelectorAll("[data-supplier-favorite]")].find`, `$("subfolders").querySelectorAll`, `$`.

## refreshSupplierFavorites

[static/app.js:651](../../../static/app.js#L651) · `FunctionDeclaration`.

```javascript
async function refreshSupplierFavorites(folder)
```

Перечитывает сохранённые звёзды и порядок разделов производства.

Использует `/api/work-supplier-favorites`.

Непосредственные вызовы: `request`, `apiUrl`, `String(item.path).normalize`, `String`, `String(item.supplierFavorite?.revision || "").split`, `String(saved?.revision || "").split`, `Number`, `state.supplierFavoriteSaving.has`, `JSON.stringify`, `renderSubfolders`.

Прямые присваивания полям/свойствам: `item.supplierFavorite`.

## toggleSupplierFavorite

[static/app.js:670](../../../static/app.js#L670) · `FunctionDeclaration`.

```javascript
async function toggleSupplierFavorite(path)
```

Сохраняет изменение избранного раздела поставщика.

Использует `/api/work-supplier-favorite`.

Непосредственные вызовы: `folder?.directories.find`, `state.supplierFavoriteSaving.has`, `state.supplierFavoriteSaving.add`, `renderSubfolders`, `request`, `state.supplierFavoriteSaving.delete`, `refreshSupplierFavorites`, `loadOrders`, `focusSupplierStar`.

Прямые присваивания полям/свойствам: `state.supplierFavoriteFocus`, `item.supplierFavorite`.

## refreshEventRelevance

[static/app.js:698](../../../static/app.js#L698) · `FunctionDeclaration`.

```javascript
async function refreshEventRelevance(folder)
```

Перечитывает актуальность событий из SQLite без повторного чтения файлов.

Использует `/api/event-relevance`.

Непосредственные вызовы: `request`, `apiUrl`, `JSON.stringify`, `renderSubfolders`.

Прямые присваивания полям/свойствам: `item.eventRelevance`.

## saveEventRelevance

[static/app.js:714](../../../static/app.js#L714) · `FunctionDeclaration`.

```javascript
async function saveEventRelevance(path, value)
```

Сохраняет актуальность выбранной папки события.

Использует `/api/event-relevance`.

Непосредственные вызовы: `folder?.directories.find`, `renderSubfolders`, `request`, `apiUrl`.

Прямые присваивания полям/свойствам: `item.relevanceSaving`, `item.eventRelevance`.

## renderFolder

[static/app.js:737](../../../static/app.js#L737) · `FunctionDeclaration`.

```javascript
function renderFolder(preserveForm = false)
```

Собирает представление открытой папки и доступные её роли блоки интерфейса.

Использует `renderMoneyOverview`, `document.dispatchEvent`, `CustomEvent`.

Непосредственные вызовы: `renderMoneyOverview`, `document.dispatchEvent`, `CustomEvent`, `renderClientActivity`, `Boolean`, `Object.hasOwn`, `isWorkOrderPath`, `hasDescendantTodos`, `$`, `$("orderOverview").classList.toggle`, `folder.breadcrumbs.map((part, index) =>
    (index ? '<span class="breadcrumb-divider">/</span>' : "") +
    '<button data-path="' + escapeHtml(part.path) + '"' + (index === folder.breadcrumbs.length - 1 ? ' aria-current="page"' : "") + ">" +
    escapeHtml(part.name) + "</button>").join`, `folder.breadcrumbs.map`, `renderOrderHeading`, `renderOrderCardLinks`, `printCountLabel`, `folder.directories.filter`, `formatSize`, `foldersAnchor.before`, `renderSubfolders`, `renderSketches`, `renderDescendantTodos`, `$("statusForm").classList.toggle`, `["supplier_root", "work_section"].includes`, `renderTodos`, `renderPurchases`, `(card[key] / 100).toFixed`, `renderOrderCalculated`, `renderExportState`, `Object.entries(supplierStatusLabels).map(([key, label]) => '<option value="' + key + '">' + label + '</option>').join`, `Object.entries(supplierStatusLabels).map`, `Object.entries`, `resizeOrderNote`, `renderStatus`, `warnings.push`, `warnings.join`, `["events", "subfolders"].includes`, `renderUpload`, `renderPrintList`, `new URLSearchParams(location.search).get`, `URLSearchParams`, `printFiles().find`, `printFiles`, `run`, `renderFiles`, `renderCardDeadlines`, `mountOrderList`, `isFolderOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `$("orderFinanceOverview").hidden`, `$("purchasePanel").hidden`, `$("orderOverview").hidden`, `$("todoPanel").hidden`, `$("orderTasksColumn").hidden`, `$("breadcrumbs").innerHTML`, `$("clientLabel").textContent`, `$("folderSummary").textContent`, `$("orderDetails").hidden`, `$("folderDetailsTitle").textContent`, `$("statusLabel").hidden`, `$("orderStatusFields").hidden`, `$("supplierStatusLabel").hidden`, `$("supplierStatusLabel").firstChild.textContent`, `$("orderTitleLabel").hidden`, `$("orderTitleLabel").firstChild.textContent`, `$("reconciliationClientLabel").hidden`, `$("financialFields").hidden`, `$("orderNote").placeholder`, `$("removeOrderButton").hidden`, `$("addOrderButton").textContent`, `$("removeOrderButton").textContent`, `$("createObjectFolderButton").hidden`, `$("groupObjectYearsButton").hidden`, `$("createOrderFolderButton").hidden`, `$("createOrderFolderButton").textContent`, `$("createEventFolderButton").hidden`, `$("renameFolderButton").hidden`, `$("deleteEventButton").hidden`, `$("openEventTrash").hidden`, `folder.todo_items`, `folder.purchase_items`, `$("todoNewText").value`, `$("purchaseNewText").value`, `$("orderDetails").open`, `$("orderTitleInput").value`, `$("reconciliationClient").value`, `$(field).value`, `$("addOrderButton").hidden`, `$("statusSelect").value`, `$("supplierStatusSelect").innerHTML`, `$("supplierStatusSelect").value`, `$("supplierStatusSelect").disabled`, `$("supplierStatusSelect").title`, `$("financialStatusSelect").value`, `$("orderNote").value`, `$("loadOrderFilesButton").hidden`, `$("notice").hidden`, `$("notice").textContent`, `$("fileSearch").value`, `$("filesSection").hidden`, `$("uploadDropZone").hidden`, `$("printWorkspace").hidden`, `state.printQuery`, `$("printTaskSearch").value`, `$("printEditorForm").hidden`, `$("printEditorEmpty").hidden`, `$("printEditorEmpty").textContent`.

## resizeOrderNote

[static/app.js:852](../../../static/app.js#L852) · `FunctionDeclaration`.

```javascript
function resizeOrderNote()
```

Подгоняет высоту поля заметки под его текущее содержимое.

Использует `$`, `Math.min`, `Math.max`.

Непосредственные вызовы: `$`, `Math.min`, `Math.max`, `note.value.trim`.

Прямые присваивания полям/свойствам: `note.style.height`.

## renderOrderHeading

[static/app.js:861](../../../static/app.js#L861) · `FunctionDeclaration`.

```javascript
function renderOrderHeading()
```

Показывает заголовок карточки заказа и его независимые отметки.

Использует `$`, `supplierLabel.setAttribute`, `supplierLabel.style.setProperty`.

Непосредственные вызовы: `$`, `supplierLabel.setAttribute`, `supplierLabel.style.setProperty`, `String`, `supplierLabel.classList.toggle`, `Boolean`, `createEvent.before`, `metaParent.append`, `headingMeta.classList.toggle`, `$("orderHeadingTitle").parentElement.classList.toggle`, `button.setAttribute`, `orderRowSaving`.

Прямые присваивания полям/свойствам: `supplierLabel.hidden`, `supplierLabel.textContent`, `$("folderTitleText").textContent`, `$("orderFolderName").hidden`, `$("orderFolderName").textContent`, `button.hidden`, `button.title`, `button.disabled`, `button.firstElementChild.textContent`.

## renderStatus

[static/app.js:897](../../../static/app.js#L897) · `FunctionDeclaration`.

```javascript
function renderStatus()
```

Заполняет редактор сохранённого состояния текущей карточки.

Использует `Boolean`, `Object.hasOwn`, `isWorkOrderPath`.

Непосредственные вызовы: `Boolean`, `Object.hasOwn`, `isWorkOrderPath`, `$`, `renderPurchaseSaveState`, `renderCardDeadlines`.

Прямые присваивания полям/свойствам: `$("statusBadge").hidden`, `$("statusBadge").textContent`, `$("statusBadge").dataset.status`, `$("statusSelect").dataset.status`, `$("financialStatusSelect").dataset.financialStatus`, `$("saveStatusButton").textContent`, `$("todoSaveState").textContent`.

## renderPurchaseSaveState

[static/app.js:914](../../../static/app.js#L914) · `FunctionDeclaration`.

```javascript
function renderPurchaseSaveState()
```

Показывает состояние сохранения закупок и доступность повторной проверки.

Использует `$`.

Непосредственные вызовы: `$`.

Прямые присваивания полям/свойствам: `$("purchaseSaveState").textContent`.

## purchaseSupplierButtons

[static/app.js:921](../../../static/app.js#L921) · `FunctionDeclaration`.

```javascript
function purchaseSupplierButtons(item)
```

Строит переключатели назначений поставщиков одной закупки.

Использует `(state.purchaseSuppliers || []).map`, `(item.suppliers || []).filter`.

Непосредственные вызовы: `(state.purchaseSuppliers || []).map`, `(item.suppliers || []).filter`, `names.map(name => {
    const selected = (item.suppliers || []).includes(name), inactive = !available.includes(name);
    const label = inactive ? "Снять назначение " + name + " · поставщик без звезды или недоступен" : "Отметить поставщика " + name;
    return '<button type="button" data-purchase-supplier="' + escapeHtml(name) + '" aria-pressed="' + selected + '" title="' + escapeHtml(label) + '"' +
      (inactive ? ' class="purchase-supplier-retained"' : '') + '>' + escapeHtml(name) + (inactive ? ' ×' : '') + '</button>';
  }).join`, `names.map`.

## updatePurchaseSupplierButtons

[static/app.js:934](../../../static/app.js#L934) · `FunctionDeclaration`.

```javascript
function updatePurchaseSupplierButtons()
```

Обновляет назначения строки закупки в существующем редакторе.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `focused?.closest`, `document.querySelector`, `$("purchaseList").querySelectorAll`, `$`, `Number`, `row.querySelector`, `purchaseSupplierButtons`, `$("purchaseList").querySelector`, `([...(row?.querySelectorAll("[data-purchase-supplier]") || [])].find(button => button.dataset.purchaseSupplier === name) || row?.querySelector(".todo-text"))?.focus`, `[...(row?.querySelectorAll("[data-purchase-supplier]") || [])].find`, `row?.querySelectorAll`, `row?.querySelector`.

Прямые присваивания полям/свойствам: `group.innerHTML`, `document.querySelector(".content-pane").scrollTop`.

## refreshPurchaseSuppliers

[static/app.js:953](../../../static/app.js#L953) · `FunctionDeclaration`.

```javascript
async function refreshPurchaseSuppliers()
```

Загружает доступные избранные разделы поставщиков.

Использует `/api/purchase-suppliers`.

Непосредственные вызовы: `isWorkOrderPath`, `request`, `updatePurchaseSupplierButtons`, `Number.isSafeInteger`, `[...$("subfolders").querySelectorAll("[data-path]")].find`, `$("subfolders").querySelectorAll`, `$`, `button?.querySelector`, `button.setAttribute`.

Прямые присваивания полям/свойствам: `state.purchaseSupplierRequest`, `state.purchaseSuppliers`, `item.supplierPurchaseCount`, `badge.textContent`, `button.title`.

## renderPurchases

[static/app.js:981](../../../static/app.js#L981) · `FunctionDeclaration`.

```javascript
function renderPurchases()
```

Показывает редактор исходных закупок текущего заказа.

Использует `Array.isArray`, `$`, `Boolean`.

Непосредственные вызовы: `Array.isArray`, `$`, `Boolean`, `items.filter`, `items.map((item, index) => '<div class="todo-row' + (item.done ? ' done' : '') + '" data-purchase-index="' + index + '">' +
    '<input class="todo-check" type="checkbox" aria-label="Закупка выполнена: ' + escapeHtml(item.text) + '"' + (item.done ? ' checked' : '') + '>' +
    '<input class="todo-text" type="text" maxlength="1000" size="' + Math.max(4, Array.from(item.text).length + 1) + '" aria-label="Текст закупки или затраты" value="' + escapeHtml(item.text) + '">' +
    '<div class="purchase-suppliers" role="group" aria-label="Поставщики для закупки: ' + escapeHtml(item.text) + '">' + purchaseSupplierButtons(item) + '</div>' +
    '<button class="todo-delete" type="button" aria-label="Удалить закупку: ' + escapeHtml(item.text) + '">×</button></div>').join`, `items.map`, `renderPurchaseSaveState`.

Прямые присваивания полям/свойствам: `$("purchaseLegacy").hidden`, `$("purchaseLegacyText").textContent`, `$("purchaseAddForm").hidden`, `$("purchaseEmpty").hidden`, `$("purchaseCount").textContent`, `$("purchaseList").innerHTML`.

## applyRemotePurchaseUpdate

[static/app.js:999](../../../static/app.js#L999) · `FunctionDeclaration`.

```javascript
function applyRemotePurchaseUpdate(folder, order)
```

Применяет фоновое изменение закупок с проверкой локального черновика.

Использует `$`, `unchanged`, `JSON.stringify`.

Непосредственные вызовы: `document.activeElement?.closest`, `$`, `unchanged`, `JSON.stringify`, `Array.isArray`, `order.purchase_items.map`, `renderPurchases`, `renderExportState`.

Прямые присваивания полям/свойствам: `folder.order`, `folder.purchase_items`.

## unchanged

[static/app.js:1006](../../../static/app.js#L1006) · `ArrowFunctionExpression`.

```javascript
const unchanged = record =>
```

Сравнивает данные редактора с сохранённым исходным состоянием.

Использует `JSON.stringify`.

Непосредственные вызовы: `JSON.stringify`, `["path", "id", "title", "status", "financial_status", "note", "amount", "costs", "paid", "updated"].map`.

## renderTodos

[static/app.js:1020](../../../static/app.js#L1020) · `FunctionDeclaration`.

```javascript
function renderTodos()
```

Показывает собственные задачи текущей карточки.

Использует `Array.isArray`, `$`, `Boolean`.

Непосредственные вызовы: `Array.isArray`, `$`, `Boolean`, `items.filter`, `items.map((item, index) => '<div class="todo-row' + (item.done ? ' done' : '') + '" data-todo-index="' + index + '">' +
    '<input class="todo-check" type="checkbox" aria-label="Выполнено: ' + escapeHtml(item.text) + '"' + (item.done ? ' checked' : '') + '>' +
    '<input class="todo-text" type="text" maxlength="1000" aria-label="Текст задачи" value="' + escapeHtml(item.text) + '">' +
    '<button class="todo-delete" type="button" aria-label="Удалить задачу: ' + escapeHtml(item.text) + '">×</button></div>').join`, `items.map`.

Прямые присваивания полям/свойствам: `$("todoLegacy").hidden`, `$("todoLegacyText").textContent`, `$("todoAddForm").hidden`, `$("todoEmpty").hidden`, `$("todoEmpty").textContent`, `$("todoCount").textContent`, `$("todoList").innerHTML`.

## hasDescendantTodos

[static/app.js:1037](../../../static/app.js#L1037) · `FunctionDeclaration`.

```javascript
function hasDescendantTodos(folder)
```

Проверяет наличие вложенных задач для показа сводки.

Использует `Boolean`.

Непосредственные вызовы: `Boolean`.

## renderDescendantTodos

[static/app.js:1043](../../../static/app.js#L1043) · `FunctionDeclaration`.

```javascript
function renderDescendantTodos()
```

Показывает задачи вложенных папок с переходом к исходному месту.

Использует `$`, `hasDescendantTodos`, `groups.some`.

Непосредственные вызовы: `$`, `hasDescendantTodos`, `groups.some`, `Boolean`, `groups.map((group) => ({ ...group, items: group.items?.filter((item) => folder.showCompletedTodos || !item.done) ?? null }))
    .filter`, `groups.map`, `groups.reduce`, `visible.map(renderOrderTodoGroup).join`, `visible.map`, `orderTodoSummary`.

Прямые присваивания полям/свойствам: `$("descendantTodos").hidden`, `$("descendantCompletedLabel").hidden`, `$("descendantCompleted").checked`, `$("descendantTodoCount").textContent`, `$("descendantTodoList").innerHTML`, `$("descendantTodoList").scrollTop`, `folder.descendantTodoMarkup`, `$("descendantTodoState").textContent`.

## loadDescendantTodos

[static/app.js:1067](../../../static/app.js#L1067) · `FunctionDeclaration`.

```javascript
async function loadDescendantTodos(folder)
```

Перечитывает SQLite-сводку вложенных задач текущего заказа.

Использует `/api/order-todos`.

Непосредственные вызовы: `hasDescendantTodos`, `request`, `apiUrl`, `renderDescendantTodos`.

Прямые присваивания полям/свойствам: `folder.descendantTodoLoading`, `folder.descendantTodos`, `folder.descendantTodoError`.

## saveTodosSoon

[static/app.js:1085](../../../static/app.js#L1085) · `FunctionDeclaration`.

```javascript
function saveTodosSoon(delay = 0)
```

Планирует отложенное сохранение изменённых задач.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `renderStatus`, `setTimeout`.

Прямые присваивания полям/свойствам: `state.dirty`.

## filteredFiles

[static/app.js:1095](../../../static/app.js#L1095) · `FunctionDeclaration`.

```javascript
function filteredFiles()
```

Отбирает файлы по текущей группе и строке поиска.

Использует `normalize`, `state.fileQuery.trim`, `state.folder.files.filter`.

Непосредственные вызовы: `normalize`, `state.fileQuery.trim`, `state.folder.files.filter`, `files.sort`.

## fileCard

[static/app.js:1108](../../../static/app.js#L1108) · `FunctionDeclaration`.

```javascript
function fileCard(file)
```

Строит карточку файла с превью и сохранённым комментарием.

Использует `/api/thumbnail`, `/api/freza-preview`, `/api/preview`.

Непосредственные вызовы: `apiUrl`, `["image", "cdr"].includes`, `escapeHtml`, `icon`, `state.selectedFiles.has`, `file.comment?.trim`.

## updateFileCommentCaption

[static/app.js:1120](../../../static/app.js#L1120) · `FunctionDeclaration`.

```javascript
function updateFileCommentCaption(path, text, key)
```

Обновляет подпись комментария у соответствующей карточки файла.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `state.folder?.files.find`, `[...$("files").querySelectorAll("[data-file]")].find`, `$("files").querySelectorAll`, `$`, `button.querySelector`, `text.trim`, `caption?.remove`, `document.createElement`, `button.appendChild`.

Прямые присваивания полям/свойствам: `file.comment`, `caption.className`, `caption.textContent`.

## renderFiles

[static/app.js:1138](../../../static/app.js#L1138) · `FunctionDeclaration`.

```javascript
function renderFiles()
```

Показывает отфильтрованные файлы и состояние их загрузки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `filteredFiles`, `Set`, `state.folder.files.map`, `available.has`, `state.selectedFiles.delete`, `renderFileActions`, `$`, `Object.entries(typeLabels)
    .filter(([type]) => type === "all" || state.folder.counts[type] > 0)
    .map(([type, label]) => '<button class="file-filter' + (state.fileType === type ? " active" : "") +
      '" data-type="' + type + '" aria-pressed="' + (state.fileType === type) + '">' + label + '<span>' +
      (type === "all" ? state.folder.fileCount : state.folder.counts[type]) + "</span></button>").join`, `Object.entries(typeLabels)
    .filter(([type]) => type === "all" || state.folder.counts[type] > 0)
    .map`, `Object.entries(typeLabels)
    .filter`, `Object.entries`, `icon`, `Map`, `files.slice`, `groups.has`, `groups.set`, `groups.get(key).push`, `groups.get`, `[...groups.entries()].map(([folder, group]) => {
    const path = [state.folder.path, folder].filter(Boolean).join("/");
    return '<section class="file-group">' +
      (state.fileSort === "folders" ? '<button class="file-group-heading" data-path="' + escapeHtml(path) + '">' +
        icon("folder") + "<span>" + escapeHtml(folder || "В выбранной папке") + '</span><small>' + group.length + "</small></button>" : "") +
      '<div class="file-grid">' + group.map(fileCard).join("") + "</div></section>";
  }).join`, `[...groups.entries()].map`, `groups.entries`, `$("files").querySelectorAll("img").forEach`, `$("files").querySelectorAll`, `refreshThumbnails().catch`, `refreshThumbnails`.

Прямые присваивания полям/свойствам: `$("fileCount").textContent`, `$("fileFilters").innerHTML`, `$("files").innerHTML`.

## refreshThumbnails

[static/app.js:1178](../../../static/app.js#L1178) · `FunctionDeclaration`.

```javascript
async function refreshThumbnails()
```

Обновляет доступность миниатюр для уже показанных файлов.

Использует `/api/thumbnails`, `/api/thumbnail`.

Непосредственные вызовы: `document.querySelectorAll`, `images.slice`, `request`, `batch.map((image) => image.dataset.thumbnailPath).filter`, `batch.map`, `batch.map((image) => image.dataset.thumbnailFolder).filter`, `Map`, `result.items.map`, `items.get`, `image.closest`, `apiUrl`, `container?.classList.add`.

Прямые присваивания полям/свойствам: `image.dataset.thumbnailKey`, `image.loading`, `image.hidden`, `image.onload`, `image.onerror`, `image.src`.

## renderFileActions

[static/app.js:1214](../../../static/app.js#L1214) · `FunctionDeclaration`.

```javascript
function renderFileActions()
```

Обновляет действия над выбранным набором файлов.

Использует `state.folder.files.filter`, `selected.filter`, `filteredFiles`.

Непосредственные вызовы: `state.folder.files.filter`, `selected.filter`, `filteredFiles`, `visible.filter`, `$`, `Boolean`, `$("fileReportState").classList.toggle`, `state.folder.files.some`.

Прямые присваивания полям/свойствам: `$("selectAllFiles").checked`, `$("selectAllFiles").indeterminate`, `$("selectAllFiles").disabled`, `$("fileSelectionCount").textContent`, `$("clearFileSelection").hidden`, `$("createImageReport").disabled`, `$("deleteSelectedFiles").disabled`, `$("createImageReport").textContent`, `$("fileReportState").textContent`, `$("openImageReport").hidden`.

## confirmFileRemoval

[static/app.js:1236](../../../static/app.js#L1236) · `FunctionDeclaration`.

```javascript
async function confirmFileRemoval()
```

Запрашивает предусмотренное подтверждение удаления выбранной цели.

Использует `/api/files-trash-preview`.

Непосредственные вызовы: `folder.files.filter((file) => state.selectedFiles.has(file.path)).map`, `folder.files.filter`, `request`, `$`, `preview.files.map((file) => '<li>' + escapeHtml(file.path) + '</li>').join`, `preview.files.map`, `$("deleteFilesDialog").showModal`.

Прямые присваивания полям/свойствам: `state.fileRemoval`, `$("deleteFilesCount").textContent`, `$("deleteFilesList").innerHTML`, `$("confirmDeleteFiles").disabled`, `$("cancelDeleteFiles").disabled`.

## removeSelectedFiles

[static/app.js:1253](../../../static/app.js#L1253) · `FunctionDeclaration`.

```javascript
async function removeSelectedFiles()
```

Перемещает подтверждённые файлы в корзину менеджера.

Использует `/api/files-trash`.

Непосредственные вызовы: `$`, `request`, `$("deleteFilesDialog").close`, `state.selectedFiles.delete`, `loadOrderFiles`, `$("fileTrashState").classList.toggle`, `Boolean`, `notify`, `renderFileActions`.

Прямые присваивания полям/свойствам: `state.fileRemoving`, `$("confirmDeleteFiles").disabled`, `$("cancelDeleteFiles").disabled`, `$("confirmDeleteFiles").textContent`, `$("fileTrashState").textContent`.

## loadFileTrash

[static/app.js:1281](../../../static/app.js#L1281) · `FunctionDeclaration`.

```javascript
async function loadFileTrash()
```

Загружает сеансы корзины файлов и событий.

Использует `/api/event-trash-list`, `/api/files-trash-list`.

Непосредственные вызовы: `request`, `(data.events || []).map((session) => '<section class="file-trash-session"><strong>Событие · ' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + '</strong><p>' + escapeHtml(session.path) +
    '</p>' + (session.pending ? '<p>Операция прервана. Доступно восстановление.</p>' : '') + '<button class="secondary-button" data-restore-event="' + escapeHtml(session.session) + '">Восстановить событие</button></section>').join`, `(data.events || []).map`, `$`, `data.sessions.map((session) => '<section class="file-trash-session"><strong>' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + ' · файлов: ' + session.count + '</strong><p>' + escapeHtml(session.folder) +
    '</p><ul class="file-operation-list">' + session.files.map((path) => '<li>' + escapeHtml(path) + '</li>').join("") + '</ul><button class="secondary-button" data-restore-session="' + session.session + '">Восстановить</button></section>').join`, `data.sessions.map`.

Прямые присваивания полям/свойствам: `$("fileTrashList").innerHTML`, `$("fileTrashWarning").hidden`, `$("fileTrashWarning").textContent`.

## openFileTrash

[static/app.js:1295](../../../static/app.js#L1295) · `FunctionDeclaration`.

```javascript
async function openFileTrash(eventsOnly = false)
```

Открывает окно корзины и загружает доступное восстановление.

Использует `$`, `loadFileTrash`, `$("fileTrashDialog").showModal`.

Непосредственные вызовы: `$`, `loadFileTrash`, `$("fileTrashDialog").showModal`.

Прямые присваивания полям/свойствам: `state.trashEventsOnly`, `$("fileTrashTitle").textContent`, `$("fileTrashDialogState").textContent`.

## confirmEventRemoval

[static/app.js:1305](../../../static/app.js#L1305) · `FunctionDeclaration`.

```javascript
async function confirmEventRemoval()
```

Запрашивает предусмотренное подтверждение удаления выбранной цели.

Использует `/api/event-trash-preview`.

Непосредственные вызовы: `saveCurrentStatus`, `request`, `$`, `$("deleteEventDialog").showModal`, `$("cancelDeleteEvent").focus`.

Прямые присваивания полям/свойствам: `state.eventRemoval`, `$("deleteEventPath").textContent`, `$("deleteEventCount").textContent`, `$("deleteEventError").hidden`.

## removeEvent

[static/app.js:1321](../../../static/app.js#L1321) · `FunctionDeclaration`.

```javascript
async function removeEvent()
```

Перемещает подтверждённую папку события в корзину.

Использует `/api/event-trash`.

Непосредственные вызовы: `["confirmDeleteEvent", "cancelDeleteEvent"].forEach`, `$`, `request`, `$("deleteEventDialog").close`, `Set`, `[...state.expanded].filter`, `reloadClientTrees`, `navigate`, `loadOrders`, `notify`.

Прямые присваивания полям/свойствам: `state.eventRemoving`, `$("deleteEventError").hidden`, `$("deleteEventError").textContent`, `state.expanded`, `state.dirty`.

## restoreEventSession

[static/app.js:1352](../../../static/app.js#L1352) · `FunctionDeclaration`.

```javascript
async function restoreEventSession(session)
```

Запускает восстановление выбранного сеанса корзины.

Использует `/api/event-trash-restore`.

Непосредственные вызовы: `$("fileTrashList").querySelectorAll("button").forEach`, `$("fileTrashList").querySelectorAll`, `$`, `request`, `loadFileTrash`, `reloadClientTrees`, `loadOrderFiles`, `loadDescendantTodos`, `loadOrders`, `$("fileTrashDialogState").classList.remove`, `$("fileTrashDialogState").classList.add`.

Прямые присваивания полям/свойствам: `state.trashRestoring`, `$("fileTrashDialogState").textContent`.

## restoreFileSession

[static/app.js:1378](../../../static/app.js#L1378) · `FunctionDeclaration`.

```javascript
async function restoreFileSession(session)
```

Запускает восстановление выбранного сеанса корзины.

Использует `/api/files-trash-restore`.

Непосредственные вызовы: `$("fileTrashList").querySelectorAll("button").forEach`, `$("fileTrashList").querySelectorAll`, `$`, `request`, `loadFileTrash`, `loadOrderFiles`, `$("fileTrashDialogState").classList.toggle`, `Boolean`, `$("fileTrashState").classList.toggle`.

Прямые присваивания полям/свойствам: `state.trashRestoring`, `$("fileTrashDialogState").textContent`, `$("fileTrashState").textContent`.

## createImageReport

[static/app.js:1401](../../../static/app.js#L1401) · `FunctionDeclaration`.

```javascript
async function createImageReport()
```

Запрашивает PDF-отчёт по выбранным изображениям и комментариям.

Использует `/api/image-report`.

Непосредственные вызовы: `filteredFiles`, `[...files, ...folder.files.filter((file) => !files.includes(file))].filter((file) => state.selectedFiles.has(file.path)).map`, `[...files, ...folder.files.filter((file) => !files.includes(file))].filter`, `folder.files.filter`, `renderFileActions`, `request`, `loadOrderFiles`, `notify`.

Прямые присваивания полям/свойствам: `state.imageReport`, `report.result`, `report.error`, `report.busy`.

## printFiles

[static/app.js:1424](../../../static/app.js#L1424) · `FunctionDeclaration`.

```javascript
function printFiles()
```

Выбирает поддерживаемые задания печати из открытой папки.

Использует `normalize`, `state.printQuery.trim`.

Непосредственные вызовы: `normalize`, `state.printQuery.trim`, `state.folder.files.filter((file) => !needle || normalize(file.name + " " + (file.title || "") + " " + (file.description || "") + " " + file.folder).includes(needle))
    .sort`, `state.folder.files.filter`.

## renderPrintList

[static/app.js:1432](../../../static/app.js#L1432) · `FunctionDeclaration`.

```javascript
function renderPrintList()
```

Показывает список черновиков и выпущенных заданий печати.

Использует `$`, `printFiles`.

Непосредственные вызовы: `$`, `printFiles`, `files.map((file) => '<button class="print-task-button' +
    (state.printTask?.path === file.path ? " active" : "") + '" data-task="' + escapeHtml(file.path) +
    '" title="' + escapeHtml(file.name) + '"><span>' + icon("file") + '<strong>' +
    escapeHtml(file.title || file.name.replace(/\.(textClipping|txt|text|md|rtf)$/i, "")) + '</strong></span><small>' +
    formatDate(file.modified) + (file.folder ? " · " + escapeHtml(file.folder) : "") + '</small></button>').join`, `files.map`.

Прямые присваивания полям/свойствам: `$("printTaskCount").textContent`, `$("printTaskList").innerHTML`.

## renderPrintSaveState

[static/app.js:1445](../../../static/app.js#L1445) · `FunctionDeclaration`.

```javascript
function renderPrintSaveState()
```

Обновляет состояние сохранения открытого задания печати.

Использует `$`, `$("printSaveState").classList.toggle`, `Boolean`.

Непосредственные вызовы: `$`, `$("printSaveState").classList.toggle`, `Boolean`, `$("printLink").value.trim`, `URL`, `["http:", "https:"].includes`.

Прямые присваивания полям/свойствам: `$("printTaskName").textContent`, `$("printSaveState").textContent`, `$("savePrintTask").textContent`, `$("savePrintTask").disabled`, `$("publishPrintTask").hidden`, `$("publishPrintTask").disabled`, `$("openPrintLink").hidden`, `$("openPrintLink").href`.

## showPrintTask

[static/app.js:1466](../../../static/app.js#L1466) · `FunctionDeclaration`.

```javascript
function showPrintTask(task)
```

Заполняет редактор выбранного задания печати.

Использует `$`, `renderPrintList`, `renderPrintSaveState`.

Непосредственные вызовы: `$`, `renderPrintList`, `renderPrintSaveState`.

Прямые присваивания полям/свойствам: `state.printTask`, `$("printTitle").value`, `$("printLink").value`, `$("printDescription").value`, `$("printEditorForm").hidden`, `$("printEditorEmpty").hidden`.

## renderNewOrderName

[static/app.js:1479](../../../static/app.js#L1479) · `FunctionDeclaration`.

```javascript
function renderNewOrderName()
```

Обновляет предлагаемое имя создаваемой папки по полям формы.

Использует `$`, `$("newOrderTitle").value.trim`.

Непосредственные вызовы: `$`, `$("newOrderTitle").value.trim`.

Прямые присваивания полям/свойствам: `$("newOrderFolderName").textContent`.

## openCreateObject

[static/app.js:1487](../../../static/app.js#L1487) · `FunctionDeclaration`.

```javascript
function openCreateObject()
```

Открывает форму создания объекта в выбранном клиенте.

Использует `$`, `$("createObjectFolderDialog").showModal`, `$("newObjectTitle").focus`.

Непосредственные вызовы: `$`, `$("createObjectFolderDialog").showModal`, `$("newObjectTitle").focus`.

Прямые присваивания полям/свойствам: `state.newObjectParent`, `$("newObjectParent").textContent`, `$("newObjectTitle").value`, `$("newObjectError").hidden`.

## createObject

[static/app.js:1499](../../../static/app.js#L1499) · `FunctionDeclaration`.

```javascript
async function createObject()
```

Создаёт объект по подтверждённым полям формы.

Использует `/api/object-folder-create`.

Непосредственные вызовы: `$("createObjectFolderForm").reportValidity`, `$`, `controls.forEach`, `saveCurrentStatus`, `request`, `$("createObjectFolderDialog").close`, `reloadClientTrees`, `navigate`, `notify`.

Прямые присваивания полям/свойствам: `state.creatingObject`, `$("newObjectError").hidden`, `$("newObjectError").textContent`.

## openObjectYears

[static/app.js:1525](../../../static/app.js#L1525) · `FunctionDeclaration`.

```javascript
async function openObjectYears()
```

Открывает предварительный план группировки заказов объекта по годам.

Использует `/api/object-years`.

Непосредственные вызовы: `saveCurrentStatus`, `request`, `apiUrl`, `$`, `plan.mappings.map(pair=>'<div class="year-group-item"><strong>'+escapeHtml(pair.source.split('/').pop())+'</strong><span>→ '+escapeHtml(pair.year)+'/</span></div>').join`, `plan.mappings.map`, `plan.created_years.map(path=>'<p>Создать папку '+escapeHtml(path.split('/').pop())+'</p>').join`, `plan.created_years.map`, `plan.skipped.join`, `plan.conflicts.join`, `Boolean`, `$("objectYearsDialog").showModal`.

Прямые присваивания полям/свойствам: `state.objectYears`, `$("objectYearsParent").textContent`, `$("objectYearsPlan").innerHTML`, `$("objectYearsSkipped").hidden`, `$("objectYearsSkipped").textContent`, `$("objectYearsError").hidden`, `$("objectYearsError").textContent`, `$("submitObjectYears").disabled`, `$("submitObjectYears").textContent`.

## groupObjectYears

[static/app.js:1544](../../../static/app.js#L1544) · `FunctionDeclaration`.

```javascript
async function groupObjectYears()
```

Выполняет подтверждённую группировку заказов по годам.

Использует `/api/object-years`.

Непосредственные вызовы: `$`, `request`, `$("objectYearsDialog").close`, `Set`, `[...state.expanded].map`, `reloadClientTrees`, `navigate`, `loadOrders`, `notify`.

Прямые присваивания полям/свойствам: `state.groupingYears`, `$("submitObjectYears").disabled`, `$("cancelObjectYears").disabled`, `$("objectYearsError").hidden`, `$("objectYearsError").textContent`, `state.expanded`.

## moved

[static/app.js:1565](../../../static/app.js#L1565) · `ArrowFunctionExpression`.

```javascript
const moved=path=>
```

Обновляет путь элемента интерфейса после подтверждённого переноса папок.

Использует `state.objectYears.mappings.find`, `path.slice`.

Непосредственные вызовы: `state.objectYears.mappings.find`, `path.slice`.

## openCreateOrderFolder

[static/app.js:1575](../../../static/app.js#L1575) · `FunctionDeclaration`.

```javascript
function openCreateOrderFolder()
```

Открывает форму создания нового заказа в объекте.

Использует `["supplier_root", "work_section"].includes`, `$`, `Object.fromEntries`.

Непосредственные вызовы: `["supplier_root", "work_section"].includes`, `$`, `Object.fromEntries`, `new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date()).map`, `new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts`, `Intl.DateTimeFormat`, `Date`, `renderNewOrderName`, `$("createOrderFolderDialog").showModal`, `$("newOrderTitle").focus`.

Прямые присваивания полям/свойствам: `state.newOrderParent`, `$("newOrderDateLabel").textContent`, `$("newOrderTitleLabel").textContent`, `$("createOrderFolderTitle").textContent`, `$("submitCreateOrderFolder").textContent`, `$("newOrderParentLabel").textContent`, `$("newOrderTitle").placeholder`, `$("newOrderDate").value`, `$("newOrderTitle").value`, `$("newOrderParent").textContent`, `$("newOrderError").hidden`.

## createOrderFolder

[static/app.js:1615](../../../static/app.js#L1615) · `FunctionDeclaration`.

```javascript
async function createOrderFolder()
```

Создаёт папку заказа и применяет ответ устойчивой операции.

Использует `/api/order-folder-create`.

Непосредственные вызовы: `$("createOrderFolderForm").reportValidity`, `$`, `Boolean`, `controls.forEach`, `saveCurrentStatus`, `request`, `$("createOrderFolderDialog").close`, `loadTree`, `navigate`, `loadOrders`, `notify`, `isWorkOrderPath`.

Прямые присваивания полям/свойствам: `state.creatingOrderFolder`, `$("submitCreateOrderFolder").textContent`, `$("newOrderError").hidden`, `$("newOrderError").textContent`.

## renderNewEventName

[static/app.js:1647](../../../static/app.js#L1647) · `FunctionDeclaration`.

```javascript
function renderNewEventName()
```

Обновляет предлагаемое имя создаваемой папки по полям формы.

Использует `$`, `$("newEventTitle").value.trim`.

Непосредственные вызовы: `$`, `$("newEventTitle").value.trim`.

Прямые присваивания полям/свойствам: `$("newEventFolderName").textContent`.

## renderEventProposal

[static/app.js:1653](../../../static/app.js#L1653) · `FunctionDeclaration`.

```javascript
function renderEventProposal(previous = new Map())
```

Показывает проверенное предложение имени и пути события.

Использует `$`, `suggestions.map`.

Непосредственные вызовы: `$`, `suggestions.map((item) => {
    const title = previous.get(item.source) ?? item.title;
    return '<div class="event-rename-row" data-number="' + item.number + '"><p class="event-old-name">' + escapeHtml(item.source) + '</p>' +
      '<label>Название события<input data-event-source="' + escapeHtml(item.source) + '" aria-label="Название для ' + escapeHtml(item.source) + '" type="text" maxlength="240" required value="' + escapeHtml(title) + '" placeholder="Укажите название"></label>' +
      '<p class="new-order-preview">→ <strong>' + escapeHtml(item.number + ' - ' + (title || 'Название события')) + '</strong></p></div>';
  }).join`, `suggestions.map`, `renderNewEventName`.

Прямые присваивания полям/свойствам: `$("eventRenameSection").hidden`, `$("confirmEventRenames").checked`, `$("eventRenameList").innerHTML`.

## openCreateEventFolder

[static/app.js:1668](../../../static/app.js#L1668) · `FunctionDeclaration`.

```javascript
async function openCreateEventFolder()
```

Открывает форму создания или переименования события.

Использует `/api/event-folders`.

Непосредственные вызовы: `request`, `apiUrl`, `$`, `renderEventProposal`, `$("createEventFolderDialog").showModal`, `$("newEventTitle").focus`.

Прямые присваивания полям/свойствам: `state.eventPlan`, `$("newEventParent").textContent`, `$("newEventTitle").value`, `$("eventFolderError").hidden`.

## eventAction

[static/app.js:1684](../../../static/app.js#L1684) · `FunctionDeclaration`.

```javascript
async function eventAction(action)
```

Выполняет выбранную операцию формы события по текущей версии.

Использует `/api/event-folder-create`, `/api/event-folders-rename`, `/api/event-folders`.

Непосредственные вызовы: `$`, `form.reportValidity`, `$("createEventFolderDialog").querySelectorAll`, `controls.forEach`, `saveCurrentStatus`, `request`, `[...$("eventRenameList").querySelectorAll("input")].map`, `$("eventRenameList").querySelectorAll`, `apiUrl`, `renderEventProposal`, `loadTree`, `navigate`, `notify`, `$("createEventFolderDialog").close`.

Прямые присваивания полям/свойствам: `state.eventBusy`, `$("eventFolderError").hidden`, `state.eventPlan`, `$("eventFolderError").textContent`.

## refreshEventProposal

[static/app.js:1724](../../../static/app.js#L1724) · `FunctionDeclaration`.

```javascript
async function refreshEventProposal()
```

Перепроверяет предложение события без замены пользовательского ввода.

Использует `/api/event-folders`.

Непосредственные вызовы: `Map`, `[...$("eventRenameList").querySelectorAll("input")].map`, `$("eventRenameList").querySelectorAll`, `$`, `request`, `apiUrl`, `renderEventProposal`.

Прямые присваивания полям/свойствам: `state.eventPlan`, `$("eventFolderError").hidden`.

## openPrintTask

[static/app.js:1734](../../../static/app.js#L1734) · `FunctionDeclaration`.

```javascript
async function openPrintTask(path)
```

Открывает выбранное задание печати в общем редакторе.

Использует `/api/print-task`.

Непосредственные вызовы: `saveCurrentPrintTask`, `$`, `request`, `apiUrl`, `showPrintTask`, `URL`, `url.searchParams.set`, `window.history.replaceState`.

Прямые присваивания полям/свойствам: `$("printEditorForm").hidden`, `$("printEditorEmpty").hidden`, `$("printEditorEmpty").textContent`.

## newPrintTask

[static/app.js:1758](../../../static/app.js#L1758) · `FunctionDeclaration`.

```javascript
async function newPrintTask()
```

Создаёт новый черновик задания печати выбранного типа.

Использует `saveCurrentPrintTask`, `showPrintTask`, `URL`.

Непосредственные вызовы: `saveCurrentPrintTask`, `showPrintTask`, `URL`, `url.searchParams.delete`, `window.history.replaceState`, `$("printTitle").focus`, `$`.

## saveCurrentPrintTask

[static/app.js:1770](../../../static/app.js#L1770) · `FunctionDeclaration`.

```javascript
async function saveCurrentPrintTask(force = false)
```

Сохраняет или выпускает открытое задание печати.

Использует `/api/print-create`, `/api/print-save`.

Непосредственные вызовы: `saveCurrentPrintTask`, `$("printLink").checkValidity`, `$`, `$("printLink").reportValidity`, `Error`, `$("printTitle").value.trim`, `$("printLink").value.trim`, `async () => {
    const saved = await request(task.isNew ? "/api/print-create" : "/api/print-save", {
      path: task.isNew ? folder : task.path, revision: task.revision, title, link, description,
    });
    if (state.printTask === task) {
      Object.assign(task, saved, { isNew: false });
      task.dirty = $("printTitle").value.trim() !== saved.title || $("printLink").value.trim() !== saved.link || $("printDescription").value !== saved.description;
      const url = new URL(location.href);
      url.searchParams.set("task", saved.path);
      window.history.replaceState(null, "", url.pathname + url.search);
    }
    const refreshed = await request(folderUrl(folder));
    Object.assign(state.folder, refreshed, { note: state.folder.note });
    $("folderSummary").textContent = printCountLabel(state.folder.fileCount) + " · название, ссылка и описание";
    renderPrintList();
  }`, `renderPrintSaveState`.

Прямые присваивания полям/свойствам: `state.printSaving`.

## saveCurrentStatus

[static/app.js:1811](../../../static/app.js#L1811) · `FunctionDeclaration`.

```javascript
async function saveCurrentStatus()
```

Сохраняет открытый редактор карточки с проверкой версии.

Использует `/api/reconciliation-save`, `/api/folder-note-save`, `/api/note`.

Непосредственные вызовы: `flushDeadlineComments`, `saveCurrentStatus`, `currentOrderValues`, `$`, `request`, `renderStatus`, `JSON.stringify`, `renderExportState`, `renderOrderHeading`.

Прямые присваивания полям/свойствам: `$("saveStatusButton").disabled`, `$("saveStatusButton").textContent`, `state.saving`, `folder.status`, `folder.financial_status`, `folder.note`, `folder.statusSource`, `folder.order`, `folder.reconciliation`, `folder.folderNote`, `folder.draftCard`, `state.dirty`.

## rubles

[static/app.js:1855](../../../static/app.js#L1855) · `ArrowFunctionExpression`.

```javascript
const rubles = (value) =>
```

Форматирует денежное значение для соответствующего компонента.

Использует `Intl.NumberFormat`.

Непосредственные вызовы: `new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 2 }).format`, `Intl.NumberFormat`.

## currentOrderValues

[static/app.js:1859](../../../static/app.js#L1859) · `FunctionDeclaration`.

```javascript
function currentOrderValues()
```

Собирает значения текущего редактора заказа для сравнения или сохранения.

Использует `$`, `state.folder.todo_items.map`, `Array.isArray`.

Непосредственные вызовы: `$`, `state.folder.todo_items.map`, `Array.isArray`, `Object.hasOwn`, `isWorkOrderPath`, `hasDescendantTodos`, `state.folder.purchase_items.map`.

## renderOrderCalculated

[static/app.js:1873](../../../static/app.js#L1873) · `FunctionDeclaration`.

```javascript
function renderOrderCalculated()
```

Пересчитывает отображаемые прибыль и остаток из полей редактора.

Использует `read`, `$`, `rubles`.

Непосредственные вызовы: `read`, `$`, `rubles`.

Прямые присваивания полям/свойствам: `$("orderProfit").textContent`, `$("orderDebt").textContent`.

## read

[static/app.js:1876](../../../static/app.js#L1876) · `ArrowFunctionExpression`.

```javascript
const read = (id) =>
```

Читает текущее значение поля локального редактора.

Использует `$(id).value.replace(/[\s\u00a0]/g, "").replace`, `$(id).value.replace`, `$`.

Непосредственные вызовы: `$(id).value.replace(/[\s\u00a0]/g, "").replace`, `$(id).value.replace`, `$`, `/^\d+(\.\d{1,2})?$/.test`, `Math.round`, `Number`.

## renderExportState

[static/app.js:1887](../../../static/app.js#L1887) · `FunctionDeclaration`.

```javascript
function renderExportState()
```

Показывает состояние импорта и очереди выпущенных документов.

Использует `$`, `renderPurchaseSaveState`.

Непосредственные вызовы: `$`, `renderPurchaseSaveState`.

Прямые присваивания полям/свойствам: `$("orderExportState").textContent`.

## isObjectOrderList

[static/app.js:1895](../../../static/app.js#L1895) · `FunctionDeclaration`.

```javascript
function isObjectOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## isWorkOrderList

[static/app.js:1901](../../../static/app.js#L1901) · `FunctionDeclaration`.

```javascript
function isWorkOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## isFolderOrderList

[static/app.js:1907](../../../static/app.js#L1907) · `FunctionDeclaration`.

```javascript
function isFolderOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Использует `isObjectOrderList`, `isWorkOrderList`.

Непосредственные вызовы: `isObjectOrderList`, `isWorkOrderList`.

## hasOrderList

[static/app.js:1913](../../../static/app.js#L1913) · `FunctionDeclaration`.

```javascript
function hasOrderList()
```

Проверяет роль и наличие текущего списка заказов.

Использует `isFolderOrderList`.

Непосредственные вызовы: `isFolderOrderList`.

## orderListRows

[static/app.js:1919](../../../static/app.js#L1919) · `FunctionDeclaration`.

```javascript
function orderListRows()
```

Возвращает строки текущего общего, объектного или производственного списка.

Использует `(isFolderOrderList() ? state.objectOrders : state.orders).filter`, `isFolderOrderList`.

Непосредственные вызовы: `(isFolderOrderList() ? state.objectOrders : state.orders).filter`, `isFolderOrderList`.

## findListOrder

[static/app.js:1925](../../../static/app.js#L1925) · `FunctionDeclaration`.

```javascript
function findListOrder(path)
```

Находит текущую строку заказа по устойчивой идентичности.

Использует `orderListRows().find`, `orderListRows`, `state.orders.find`.

Непосредственные вызовы: `orderListRows().find`, `orderListRows`, `state.orders.find`, `state.calendarSupplierOrders.find`.

## orderGroupScope

[static/app.js:1933](../../../static/app.js#L1933) · `FunctionDeclaration`.

```javascript
function orderGroupScope()
```

Вычисляет ключ сохранённого сворачивания групп текущего списка.

Использует `isFolderOrderList`, `isWorkOrderList`, `state.folder.path.normalize`.

Непосредственные вызовы: `isFolderOrderList`, `isWorkOrderList`, `state.folder.path.normalize`.

## orderGroupCollapsed

[static/app.js:1939](../../../static/app.js#L1939) · `FunctionDeclaration`.

```javascript
function orderGroupCollapsed(scope, group)
```

Читает сохранённое состояние сворачивания группы.

Использует `JSON.stringify`, `state.collapsedOrderGroups.has`, `localStorage.getItem`.

Непосредственные вызовы: `JSON.stringify`, `state.collapsedOrderGroups.has`, `localStorage.getItem`, `state.collapsedOrderGroups.set`, `state.collapsedOrderGroups.get`.

## applyOrderGroupVisibility

[static/app.js:1951](../../../static/app.js#L1951) · `FunctionDeclaration`.

```javascript
function applyOrderGroupVisibility(button)
```

Применяет сворачивание к строкам уже построенной группы.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `orderGroupCollapsed`, `button.setAttribute`, `String`, `$("ordersTableBody").querySelectorAll("[data-order-group-row]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`.

## toggleOrderGroup

[static/app.js:1961](../../../static/app.js#L1961) · `FunctionDeclaration`.

```javascript
function toggleOrderGroup(button)
```

Меняет сворачивание группы и сохраняет выбор интерфейса.

Сохраняет локальную настройку интерфейса через localStorage.

Непосредственные вызовы: `JSON.stringify`, `orderGroupCollapsed`, `state.collapsedOrderGroups.set`, `localStorage.setItem`, `notify`, `applyOrderGroupVisibility`.

## focusOrderGroup

[static/app.js:1973](../../../static/app.js#L1973) · `FunctionDeclaration`.

```javascript
function focusOrderGroup(group)
```

Возвращает фокус на заголовок выбранной группы списка.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `[...$("ordersTableBody").querySelectorAll("[data-order-group-toggle]")].find((button) => button.dataset.orderGroupToggle === group)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-group-toggle]")].find`, `$("ordersTableBody").querySelectorAll`, `$`.

## mountOrderList

[static/app.js:1980](../../../static/app.js#L1980) · `FunctionDeclaration`.

```javascript
function mountOrderList()
```

Перемещает общий DOM списка в место текущего представления.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `isObjectOrderList`, `$`, `isWorkOrderList`, `["title", "folder_date"].includes`, `workspace.classList.toggle`, `workspace.querySelector`, `workspace.querySelector('[data-sort="status"]').closest`, `deadlineHeader.after`, `workspace.querySelectorAll("thead th").forEach`, `workspace.querySelectorAll`, `deadlineHeader.before`, `document.querySelector`, `pane.classList.toggle`, `pane.querySelector`, `heading.append`, `heading.firstElementChild.append`, `toolbarSlot.append`, `syncSlot.append`, `window.ManagerInbox?.load`, `$("objectOrdersSlot").append`, `$("workOrdersSlot").append`, `$("folderView").before`, `hasOrderList`, `renderWorkArchive`, `renderHomeCalendar`, `workspace.setAttribute`.

Прямые присваивания полям/свойствам: `state.orderSort`, `state.orderDirection`, `$("orderDateSort").dataset.sort`, `$("orderDateSort").textContent`, `$("orderRelatedHeading").hidden`, `$("supplierStatusHeading").hidden`, `workspace.querySelector('[data-sort="status"]').hidden`, `workspace.querySelector("caption").textContent`, `$("orderSearch").placeholder`, `$("homeToolbarSlot").hidden`, `$("homeSyncSlot").hidden`, `$("homeCalendar").hidden`, `$("inboxPanel").hidden`, `$("objectOrdersSection").hidden`, `workspace.hidden`, `$("syncOrdersButton").hidden`, `state.orderListScope`, `state.orderQuery`, `$("orderSearch").value`.

## loadOrders

[static/app.js:2037](../../../static/app.js#L2037) · `FunctionDeclaration`.

```javascript
async function loadOrders()
```

Перечитывает серверную сводку и обновляет текущие представления заказов.

Использует `/api/orders`, `/api/work-orders`, `/api/object-orders`.

Непосредственные вызовы: `isFolderOrderList`, `isWorkOrderList`, `request`, `renderMoneyOverview`, `apiUrl`, `(object.archived_paths || []).map`, `result.orders.filter`, `renderFavoriteOrders`, `hasOrderList`, `renderOrders`, `renderCardDeadlines`, `[...(result.orders || []), ...(result.favorites || [])].find`, `renderOrderCardLinks`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.calendarPlansError`, `state.objectOrders`, `state.objectOrdersError`, `state.workOrderGroups`, `state.workArchivedOrders`, `state.workArchivedPaths`, `state.orders`, `state.calendarSupplierOrders`, `state.calendarEvents`, `state.calendarInvoicePlans`, `state.calendarPlansLoaded`, `state.deadlineWeekOptions`, `state.favoriteOrders`, `state.unregistrations`, `state.scan`, `state.storage`.

## orderTodoText

[static/app.js:2087](../../../static/app.js#L2087) · `FunctionDeclaration`.

```javascript
function orderTodoText(order)
```

Собирает текст или сводные данные задач строки заказа.

Использует `(order.todo_groups || []).map`.

Непосредственные вызовы: `(order.todo_groups || []).map((group) => [group.label, ...(group.items || []).map((item) => item.text)].join(" ")).join`, `(order.todo_groups || []).map`.

## orderTodoSummary

[static/app.js:2093](../../../static/app.js#L2093) · `FunctionDeclaration`.

```javascript
function orderTodoSummary(order)
```

Собирает текст или сводные данные задач строки заказа.

Использует `groups.reduce`.

Непосредственные вызовы: `groups.reduce`.

## renderOrderTodoButton

[static/app.js:2103](../../../static/app.js#L2103) · `FunctionDeclaration`.

```javascript
function renderOrderTodoButton(order)
```

Строит кнопку количества актуальных задач заказа.

Использует `orderTodoSummary`, `escapeHtml`, `icon`.

Непосредственные вызовы: `orderTodoSummary`, `escapeHtml`, `icon`.

## orderPurchaseSummary

[static/app.js:2111](../../../static/app.js#L2111) · `FunctionDeclaration`.

```javascript
function orderPurchaseSummary(order)
```

Собирает сводку или текст закупок строки заказа.

Использует `(order.purchase_items || []).filter`.

Непосредственные вызовы: `(order.purchase_items || []).filter`.

## orderPurchaseText

[static/app.js:2118](../../../static/app.js#L2118) · `FunctionDeclaration`.

```javascript
function orderPurchaseText(order)
```

Собирает сводку или текст закупок строки заказа.

Использует `(orderPurchaseSummary(order).items || []).map`, `orderPurchaseSummary`.

Непосредственные вызовы: `(orderPurchaseSummary(order).items || []).map((item) => [item.text, ...(item.suppliers || [])].join(" ")).join`, `(orderPurchaseSummary(order).items || []).map`, `orderPurchaseSummary`.

## renderOrderPurchaseButton

[static/app.js:2124](../../../static/app.js#L2124) · `FunctionDeclaration`.

```javascript
function renderOrderPurchaseButton(order)
```

Строит кнопку закупок текущего заказа в списке.

Использует `orderPurchaseSummary`, `escapeHtml`, `icon`.

Непосредственные вызовы: `orderPurchaseSummary`, `escapeHtml`, `icon`.

## renderOrderPurchases

[static/app.js:2131](../../../static/app.js#L2131) · `FunctionDeclaration`.

```javascript
function renderOrderPurchases(order)
```

Показывает сводку закупок в открытом окне заказа.

Использует `orderPurchaseSummary`, `items.map`.

Непосредственные вызовы: `orderPurchaseSummary`, `items.map((item) => '<li><div class="order-purchase-text"><span aria-hidden="true">○</span><span class="visually-hidden">Нужно закупить: </span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></div>' +
      '<div class="order-purchase-suppliers" aria-label="Выбранные поставщики">' + ((item.suppliers || []).length ? item.suppliers.map((name) => '<span>' + escapeHtml(name) + '</span>').join("") : '<span class="no-supplier">Поставщик не выбран</span>') + '</div></li>').join`, `items.map`, `escapeHtml`.

## renderOrderTodoGroup

[static/app.js:2142](../../../static/app.js#L2142) · `FunctionDeclaration`.

```javascript
function renderOrderTodoGroup(group)
```

Строит группу задач с переходом к исходной папке.

Использует `escapeHtml`, `group.items.map`.

Непосредственные вызовы: `escapeHtml`, `group.items.map((item) => '<li' + (item.done ? ' class="done"' : '') + '><span aria-hidden="true">' + (item.done ? '✓' : '○') + '</span><span class="visually-hidden">' + (item.done ? 'Выполнено: ' : 'Нужно сделать: ') + '</span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></li>').join`, `group.items.map`.

## renderOrderTodos

[static/app.js:2152](../../../static/app.js#L2152) · `FunctionDeclaration`.

```javascript
function renderOrderTodos(order)
```

Показывает собственные и вложенные задачи выбранного заказа.

Использует `orderTodoSummary`, `groups.map(renderOrderTodoGroup).join`, `groups.map`.

Непосредственные вызовы: `orderTodoSummary`, `groups.map(renderOrderTodoGroup).join`, `groups.map`, `escapeHtml`.

## renderOrderTodoDialog

[static/app.js:2161](../../../static/app.js#L2161) · `FunctionDeclaration`.

```javascript
function renderOrderTodoDialog()
```

Обновляет открытое окно задач с текущим состоянием заказа.

Использует `$`, `findListOrder`, `$("orderTodoDialog").close`.

Непосредственные вызовы: `$`, `findListOrder`, `$("orderTodoDialog").close`, `$("closeOrderTodos").setAttribute`, `$("orderTodoBody").setAttribute`, `orderPurchaseSummary`, `orderTodoSummary`, `renderOrderPurchases`, `renderOrderTodos`.

Прямые присваивания полям/свойствам: `$("orderTodoKindTitle").textContent`, `$("orderTodoHint").textContent`, `$("orderTodoDialogCount").textContent`, `$("orderTodoOrder").textContent`, `$("orderTodoOrder").title`, `$("orderTodoPath").textContent`, `$("orderTodoPath").title`, `$("orderTodoBody").innerHTML`, `state.orderTodoMarkup`, `$("orderTodoBody").scrollTop`.

## openOrderTodos

[static/app.js:2186](../../../static/app.js#L2186) · `FunctionDeclaration`.

```javascript
function openOrderTodos(path, kind = "todos")
```

Открывает сводку задач или закупок выбранной строки.

Использует `findListOrder`, `$("orderTodoBody").replaceChildren`, `$`.

Непосредственные вызовы: `findListOrder`, `$("orderTodoBody").replaceChildren`, `$`, `$("orderTodoDialog").showModal`, `renderOrderTodoDialog`.

Прямые присваивания полям/свойствам: `state.orderTodoPath`, `state.orderTodoKind`, `state.orderTodoMarkup`, `$("orderTodoBody").scrollTop`.

## orderRowSaving

[static/app.js:2199](../../../static/app.js#L2199) · `FunctionDeclaration`.

```javascript
function orderRowSaving(path)
```

Проверяет наличие незавершённой записи для строки заказа.

Использует `state.markerSaving.has`, `state.favoriteSaving.has`, `state.orderStatusSaving.has`.

Непосредственные вызовы: `state.markerSaving.has`, `state.favoriteSaving.has`, `state.orderStatusSaving.has`, `state.deadlineSaving.has`, `state.calendarMoving.has`.

## orderDeadlineRange

[static/app.js:2205](../../../static/app.js#L2205) · `FunctionDeclaration`.

```javascript
function orderDeadlineRange(weeks)
```

Вычисляет отображаемый диапазон выбранных недель заказа.

Использует `[...weeks].sort`, `Date`, `sorted.at`.

Непосредственные вызовы: `[...weeks].sort`, `Date`, `sorted.at`, `end.setUTCDate`, `end.getUTCDate`, `sorted[0].slice`, `String(end.getUTCDate()).padStart`, `String`, `String(end.getUTCMonth() + 1).padStart`, `end.getUTCMonth`.

## shiftDeadlineWeek

[static/app.js:2222](../../../static/app.js#L2222) · `FunctionDeclaration`.

```javascript
function shiftDeadlineWeek(start, offset)
```

Сдвигает ключ понедельника на заданное число недель.

Использует `Date`, `date.setUTCDate`, `date.getUTCDate`.

Непосредственные вызовы: `Date`, `date.setUTCDate`, `date.getUTCDate`, `date.toISOString().slice`, `date.toISOString`, `end.setUTCDate`, `end.getUTCDate`, `/^\d{4}-\d{2}-\d{2}$/.test`, `end.getUTCFullYear`.

## deadlineWeekInfo

[static/app.js:2233](../../../static/app.js#L2233) · `FunctionDeclaration`.

```javascript
function deadlineWeekInfo(start)
```

Готовит номер, даты и месяц выбранной недели срока.

Использует `Date`, `thursday.setUTCDate`, `thursday.getUTCDate`.

Непосредственные вызовы: `Date`, `thursday.setUTCDate`, `thursday.getUTCDate`, `thursday.getUTCFullYear`, `first.setUTCMonth`, `thursday.getUTCMonth`, `Math.ceil`, `deadlineWeekDates`.

## renderDeadlineMonthLegend

[static/app.js:2248](../../../static/app.js#L2248) · `FunctionDeclaration`.

```javascript
function renderDeadlineMonthLegend(options)
```

Строит легенду месяцев для цветов недель срока.

Использует `Map`, `options.map`.

Непосредственные вызовы: `new Map(options.map((week) => { const info = deadlineWeekInfo(week.start); return [info.monthYear, info]; })).values`, `Map`, `options.map`, `Set`, `months.map`, `months.map((month) =>
    '<span style="--deadline-month-hue:' + month.hue + '" title="' + deadlineMonthNames[month.month] + ' ' + month.year + '">' +
    deadlineMonthNames[month.month] + (years.size > 1 ? ' ' + month.year : '') + '</span>').join`.

## orderListDeadlineOptions

[static/app.js:2258](../../../static/app.js#L2258) · `FunctionDeclaration`.

```javascript
function orderListDeadlineOptions(orders)
```

Выбирает ограниченный набор недель для строки списка.

Использует `Set`, `state.deadlineWeekOptions.map`, `starts.add`.

Непосредственные вызовы: `Set`, `state.deadlineWeekOptions.map`, `starts.add`, `[...starts].sort().map`, `[...starts].sort`.

## renderOrderDeadlines

[static/app.js:2271](../../../static/app.js#L2271) · `FunctionDeclaration`.

```javascript
function renderOrderDeadlines(order, { options = state.deadlineWeekOptions, card = false, disabled = false } = {})
```

Строит кнопки недель и диапазон срока в строке заказа.

Использует `Set`, `[...selected].filter`.

Непосредственные вызовы: `Set`, `[...selected].filter`, `Object.entries(order.calendar_week_events || {}).filter(([, comment]) => comment.trim()).sort`, `Object.entries(order.calendar_week_events || {}).filter`, `Object.entries`, `comments.map(([start, comment]) => deadlineWeekInfo(start).number + '-' + comment.trim()).join`, `comments.map`, `[outsideText, preview].filter(Boolean).join`, `[outsideText, preview].filter`, `[unknown ? outsideText : outside.length ? 'Начало выбранных недель: ' + outside.join(', ') : '',
    ...comments.map(([start, comment]) => 'Неделя ' + deadlineWeekInfo(start).number + ' · ' + deadlineWeekDates(start) + ': ' + comment)].filter(Boolean).join`, `[unknown ? outsideText : outside.length ? 'Начало выбранных недель: ' + outside.join(', ') : '',
    ...comments.map(([start, comment]) => 'Неделя ' + deadlineWeekInfo(start).number + ' · ' + deadlineWeekDates(start) + ': ' + comment)].filter`, `outside.join`, `orderDeadlineRange`, `escapeHtml`, `orderRowSaving`, `options.map((option, index) => {
      const week = deadlineWeekInfo(option.start);
      const past = currentWeek && week.start < currentWeek;
      const overdue = selected.has(week.start) && past;
      const travel = week.start >= deadlineTravelPeriod.start && week.start <= deadlineTravelPeriod.end;
      const travelContinues = travel && options[index + 1]?.start === shiftDeadlineWeek(week.start, 1) && options[index + 1].start <= deadlineTravelPeriod.end;
      const comment = order.calendar_week_events?.[week.start] || "";
      const help = (overdue ? "Просрочено · " : "") + week.label + (travel ? "\n" + deadlineTravelPeriod.label : "") + (comment ? "\n" + comment : "");
      const gap = card && previous && shiftDeadlineWeek(previous, 1) !== week.start ? '<span class="deadline-week-gap" title="Между этими неделями есть пропуск">…</span>' : '';
      previous = week.start;
      return gap + '<button type="button" class="deadline-week' + (week.current ? ' current' : '') + (past ? ' past' : '') + (overdue ? ' overdue' : '') + (travel ? ' travel' : '') + (travelContinues ? ' travel-continues' : '') +
      '" style="--deadline-month-hue:' + week.hue +
      '" data-order-deadline="' + escapeHtml(order.path) + '" data-deadline-week="' + week.start +
      '" data-order-id="' + escapeHtml(order.id) + '" data-revision="' + order.revision + '" aria-pressed="' + selected.has(week.start) +
      '" aria-label="' + escapeHtml("Неделя " + week.number + " · " + help) + '" title="' + escapeHtml(help) +
      '"' + (disabled || unknown || order.registered === false || orderRowSaving(order.path) ? ' disabled' : '') + '>' + week.number + '</button>';
    }).join`, `options.map`.

## deadlineWeekDates

[static/app.js:2313](../../../static/app.js#L2313) · `FunctionDeclaration`.

```javascript
function deadlineWeekDates(week)
```

Вычисляет даты начала и конца недели по её ключу.

Использует `Date`, `end.setUTCDate`, `end.getUTCDate`.

Непосредственные вызовы: `Date`, `end.setUTCDate`, `end.getUTCDate`, `dateLabel`, `end.toISOString().slice`, `end.toISOString`.

## dateLabel

[static/app.js:2318](../../../static/app.js#L2318) · `ArrowFunctionExpression`.

```javascript
const dateLabel = (value) =>
```

Форматирует сохранённую дату для показа пользователю.

Использует `value.slice`.

Непосредственные вызовы: `value.slice`.

## renderCardDeadlines

[static/app.js:2324](../../../static/app.js#L2324) · `FunctionDeclaration`.

```javascript
function renderCardDeadlines()
```

Показывает недели срока в карточке с раскрытием прошлых периодов.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `isWorkOrderPath`, `Boolean`, `orderRowSaving`, `Set`, `visible.add`, `Object.keys`, `shiftDeadlineWeek`, `[...visible].sort().map`, `[...visible].sort`, `renderDeadlineMonthLegend`, `renderOrderDeadlines`, `document.activeElement?.hasAttribute`, `$("orderCardDeadlineList").querySelector("[data-order-calendar-compact]")?.focus`, `$("orderCardDeadlineList").querySelector`, `options.at`, `state.deadlineSaving.has`, `renderDeadlineComments`.

Прямые присваивания полям/свойствам: `panel.hidden`, `folder.deadlineVisibleWeeks`, `$("orderCardDeadlineList").innerHTML`, `$("orderCardDeadlineEarlier").disabled`, `$("orderCardDeadlineLater").disabled`, `$("orderCardDeadlineState").textContent`.

## renderDeadlineComments

[static/app.js:2352](../../../static/app.js#L2352) · `FunctionDeclaration`.

```javascript
function renderDeadlineComments(folder)
```

Показывает редакторы общих недельных событий заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `Map`, `$`, `container.replaceChildren`, `Set`, `selected.has`, `drafts.delete`, `Object.keys`, `drafts.keys`, `[...container.children].map`, `weeks.has`, `row.remove`, `[...weeks].sort`, `drafts.get`, `drafts.set`, `deadlineWeekInfo`, `rows.get`, `document.createElement`, `Array.isArray`, `row.classList.toggle`, `row.querySelector`, `input.setAttribute`, `Boolean`, `container.insertBefore`, `drafts.values`, `values.find`, `values.some`.

Прямые присваивания полям/свойствам: `folder.deadlineCommentDrafts`, `container.dataset.scope`, `draft.value`, `draft.saved`, `row.className`, `row.dataset.weekCommentRow`, `row.innerHTML`, `row.title`, `input.value`, `input.title`, `input.disabled`, `input.readOnly`, `$("orderDeadlineCommentsState").textContent`, `$("retryDeadlineComments").hidden`, `$("retryDeadlineComments").disabled`.

## hasPendingDeadlineComments

[static/app.js:2403](../../../static/app.js#L2403) · `FunctionDeclaration`.

```javascript
function hasPendingDeadlineComments(folder = state.folder)
```

Проверяет наличие несохранённых недельных текстов карточки.

Использует `Boolean`, `[...(folder?.deadlineCommentDrafts?.values() || [])].some`.

Непосредственные вызовы: `Boolean`, `[...(folder?.deadlineCommentDrafts?.values() || [])].some`, `folder?.deadlineCommentDrafts?.values`.

## deadlineCommentInput

[static/app.js:2409](../../../static/app.js#L2409) · `FunctionDeclaration`.

```javascript
function deadlineCommentInput(event)
```

Принимает ввод недельного события в локальный черновик.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `event.target.closest`, `folder?.deadlineCommentDrafts?.get`, `clearTimeout`, `renderDeadlineComments`, `setTimeout`.

Прямые присваивания полям/свойствам: `draft.value`, `draft.dirty`, `draft.error`, `folder.deadlineCommentTimer`.

## applyOrderRecord

[static/app.js:2423](../../../static/app.js#L2423) · `FunctionDeclaration`.

```javascript
function applyOrderRecord(folder, saved)
```

Применяет подтверждённую запись заказа к локальным представлениям.

Использует `orders.find`, `Object.assign`.

Непосредственные вызовы: `orders.find`, `Object.assign`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `folder.order`.

## flushDeadlineComments

[static/app.js:2434](../../../static/app.js#L2434) · `FunctionDeclaration`.

```javascript
function flushDeadlineComments(folder = state.folder)
```

Последовательно сохраняет ожидающие недельные тексты по версиям.

Использует `/api/order-deadline-comment`.

Непосредственные вызовы: `Promise.resolve`, `clearTimeout`, `[...(folder.deadlineCommentDrafts?.values() || [])].some`, `folder.deadlineCommentDrafts?.values`, `async () => {
    while (true) {
      while (state.saving) await state.saving;
      if (state.folder !== folder) throw new Error("Событие осталось в открытой карточке. Вернись к ней для сохранения.");
      const entry = [...folder.deadlineCommentDrafts].find(([, draft]) => draft.dirty);
      if (!entry) return;
      const [week, draft] = entry, value = draft.value, order = folder.order;
      if (folder.deadlineConflict) throw new Error(folder.deadlineError || "Обнови карточку перед сохранением события. Ввод остался в поле.");
      draft.saving = true;
      draft.error = "";
      state.deadlineSaving.add(order.path);
      ++state.ordersRequest;
      const saving = request("/api/order-deadline-comment", { path: order.path, id: order.id, revision: order.revision, week, comment: value }).then((saved) => {
        applyOrderRecord(folder, saved);
        draft.saved = saved.calendar_week_events?.[week] || "";
        if (draft.value === value) draft.value = draft.saved;
        draft.dirty = draft.value !== draft.saved;
      });
      state.saving = saving;
      renderOrderHeading();
      renderCardDeadlines();
      try {
        await saving;
      } catch (error) {
        folder.deadlineConflict = error.status === 409;
        draft.error = error.message + " Текст остался в поле." + (folder.deadlineConflict ? " Обнови карточку перед повтором." : "");
        if (folder.deadlineConflict) folder.deadlineError = draft.error;
        throw error;
      } finally {
        if (state.saving === saving) state.saving = null;
        state.deadlineSaving.delete(order.path);
        draft.saving = false;
        if (state.folder === folder) { renderOrderHeading(); renderStatus(); }
      }
    }
  }`, `pending.finally`.

Прямые присваивания полям/свойствам: `folder.deadlineCommentFlush`.

## expandCardDeadlineWeeks

[static/app.js:2484](../../../static/app.js#L2484) · `FunctionDeclaration`.

```javascript
function expandCardDeadlineWeeks(direction)
```

Раскрывает дополнительные недели срока в карточке.

Использует `[...folder.deadlineVisibleWeeks].sort`, `weeks.at`, `shiftDeadlineWeek`.

Непосредственные вызовы: `[...folder.deadlineVisibleWeeks].sort`, `weeks.at`, `shiftDeadlineWeek`, `folder.deadlineVisibleWeeks.add`, `renderCardDeadlines`.

## focusOrderDeadline

[static/app.js:2497](../../../static/app.js#L2497) · `FunctionDeclaration`.

```javascript
function focusOrderDeadline(path, week)
```

Возвращает фокус на кнопку недели выбранного заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `[...$("ordersTableBody").querySelectorAll("[data-order-deadline]")].find`, `$("ordersTableBody").querySelectorAll`, `$`, `button?.focus`, `Boolean`.

## toggleOrderDeadline

[static/app.js:2507](../../../static/app.js#L2507) · `FunctionDeclaration`.

```javascript
async function toggleOrderDeadline(button)
```

Сохраняет изменение одной недели срока заказа.

Использует `button.getAttribute`, `flushDeadlineComments`, `changeOrderDeadline`.

Непосредственные вызовы: `button.getAttribute`, `flushDeadlineComments`, `changeOrderDeadline`, `Number`.

## toggleCalendarCompact

[static/app.js:2516](../../../static/app.js#L2516) · `FunctionDeclaration`.

```javascript
async function toggleCalendarCompact(button)
```

Сохраняет включение или выключение мелкого заказа календаря.

Использует `/api/order-calendar-compact`.

Непосредственные вызовы: `orderRowSaving`, `flushDeadlineComments`, `findListOrder`, `button.getAttribute`, `state.deadlineSaving.add`, `request("/api/order-calendar-compact", { path, id: order.id, revision: folder?.order?.revision ?? Number(button.dataset.revision), calendar_compact: enabled })
      .then`, `request`, `Number`, `notify`, `loadOrders`, `state.deadlineSaving.delete`, `renderStatus`, `renderCardDeadlines`, `hasOrderList`, `renderOrders`, `$`, `[...root.querySelectorAll("[data-order-calendar-compact]")].find(el => el.dataset.orderCalendarCompact === path)?.focus`, `[...root.querySelectorAll("[data-order-calendar-compact]")].find`, `root.querySelectorAll`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.saving`, `button.disabled`, `folder.deadlineConflict`, `folder.deadlineError`.

## changeOrderDeadline

[static/app.js:2553](../../../static/app.js#L2553) · `FunctionDeclaration`.

```javascript
async function changeOrderDeadline({ path, id, revision, week, selected }, button)
```

Сохраняет изменение одной недели срока заказа.

Использует `/api/order-deadline-week`.

Непосредственные вызовы: `orderRowSaving`, `findListOrder`, `state.deadlineSaving.add`, `renderOrderHeading`, `renderCardDeadlines`, `$("ordersTableBody").querySelectorAll("[data-order-deadline], [data-order-status], [data-order-favorite], [data-order-flag], [data-order-blue-plus], [data-order-dollar]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`, `request("/api/order-deadline-week", { path, id, revision, week, selected }).then`, `request`, `notify`, `loadOrders`, `state.deadlineSaving.delete`, `renderStatus`, `[...$("orderCardDeadlineList").querySelectorAll("[data-deadline-week]")].find`, `$("orderCardDeadlineList").querySelectorAll`, `(focus || $("orderCardDeadlineEarlier")).focus`, `hasOrderList`, `renderOrders`, `focusOrderDeadline`, `$("orderSearch").focus`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `folder.deadlineError`, `state.saving`, `folder.deadlineConflict`.

## renderOrderMarkerButton

[static/app.js:2607](../../../static/app.js#L2607) · `FunctionDeclaration`.

```javascript
function renderOrderMarkerButton(order, kind)
```

Строит кнопку независимой отметки заказа.

Использует `escapeHtml`, `Boolean`, `orderRowSaving`.

Непосредственные вызовы: `escapeHtml`, `Boolean`, `orderRowSaving`, `icon`.

## focusOrderMarker

[static/app.js:2618](../../../static/app.js#L2618) · `FunctionDeclaration`.

```javascript
function focusOrderMarker(path, kind)
```

Возвращает фокус на выбранную отметку после обновления строки.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `[...$("ordersTableBody").querySelectorAll("[data-order-" + marker.suffix + "]")].find((button) => button.dataset[marker.data] === path)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-" + marker.suffix + "]")].find`, `$("ordersTableBody").querySelectorAll`, `$`.

## toggleOrderMarker

[static/app.js:2626](../../../static/app.js#L2626) · `FunctionDeclaration`.

```javascript
async function toggleOrderMarker(button, kind)
```

Сохраняет изменение одной независимой отметки заказа.

Использует `/api/order-`.

Непосредственные вызовы: `findListOrder`, `orderRowSaving`, `Number`, `button.getAttribute`, `state.markerSaving.add`, `button.setAttribute`, `$("ordersTableBody").querySelectorAll("[data-order-flag], [data-order-favorite], [data-order-status], [data-order-deadline], [data-order-blue-plus], [data-order-dollar]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`, `applyOrderRecord`, `request`, `loadOrders`, `state.markerSaving.delete`, `hasOrderList`, `renderOrders`, `focusOrderMarker`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## renderOrderFavoriteButton

[static/app.js:2653](../../../static/app.js#L2653) · `FunctionDeclaration`.

```javascript
function renderOrderFavoriteButton(order)
```

Строит кнопку избранного текущего заказа.

Использует `escapeHtml`, `Boolean`, `orderRowSaving`.

Непосредственные вызовы: `escapeHtml`, `Boolean`, `orderRowSaving`.

## renderOrderRelatedButton

[static/app.js:2661](../../../static/app.js#L2661) · `FunctionDeclaration`.

```javascript
function renderOrderRelatedButton(order)
```

Строит цепочку связанных заказов выбранного объекта.

Использует `Boolean`, `escapeHtml`, `orderRowSaving`.

Непосредственные вызовы: `Boolean`, `escapeHtml`, `orderRowSaving`, `icon`.

## renderCompactOrderLinks

[static/app.js:2673](../../../static/app.js#L2673) · `FunctionDeclaration`.

```javascript
function renderCompactOrderLinks(order)
```

Показывает компактные ссылки главного на его подчинённые заказы.

Использует `items.map`.

Непосредственные вызовы: `items.map(item => '<li>' + icon('link') +
    (item.available ? '<a href="?path=' + encodeURIComponent(item.path) + '" data-related-card-open="' + escapeHtml(item.path) + '" data-related-card-id="' + escapeHtml(item.id) + '">' + escapeHtml(item.title) + '</a>' :
      '<span class="unavailable">' + escapeHtml(item.title) + '</span>') + '</li>').join`, `items.map`.

## renderOrderCardLinks

[static/app.js:2683](../../../static/app.js#L2683) · `FunctionDeclaration`.

```javascript
function renderOrderCardLinks(order = state.folder?.order)
```

Показывает компактные ссылки главного на его подчинённые заказы.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `renderCompactOrderLinks`, `container.contains`, `[...container.querySelectorAll('[data-related-card-id]')].find(link => link.dataset.relatedCardId === active)?.focus`, `[...container.querySelectorAll('[data-related-card-id]')].find`, `container.querySelectorAll`.

Прямые присваивания полям/свойствам: `state.folder.cardLinksRevision`, `container.hidden`, `container.innerHTML`, `state.cardLinksMarkup`.

## renderOrderLinks

[static/app.js:2701](../../../static/app.js#L2701) · `FunctionDeclaration`.

```javascript
function renderOrderLinks()
```

Показывает состав и доступные действия группы связанных заказов.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `Boolean`, `normalize`, `$("orderLinksSearch").value.trim`, `[document.body, $("orderLinksDialog")].includes`, `section`, `[...$("orderLinksOptions").querySelectorAll('[data-related-target]')].find(button => button.dataset.relatedTarget === active)?.focus`, `[...$("orderLinksOptions").querySelectorAll('[data-related-target]')].find`, `$("orderLinksOptions").querySelectorAll`.

Прямые присваивания полям/свойствам: `$("closeOrderLinks").disabled`, `$("refreshOrderLinks").disabled`, `$("initializeOrderLinks").hidden`, `$("initializeOrderLinks").disabled`, `$("orderLinksOrder").textContent`, `$("orderLinksState").textContent`, `$("orderLinksOptions").innerHTML`, `$("orderLinksOptions").scrollTop`.

## section

[static/app.js:2720](../../../static/app.js#L2720) · `ArrowFunctionExpression`.

```javascript
const section = (items, linked) =>
```

Строит отображаемую секцию доступных связанных заказов.

Использует `(items || []).filter`, `visible.map`.

Непосредственные вызовы: `(items || []).filter`, `visible.map(item =>
      '<div class="order-link-option"><div>' + (item.available ? '<a href="?path=' + encodeURIComponent(item.path) + '" data-related-open="' + escapeHtml(item.path) + '">' + escapeHtml(item.title) + '</a>' : '<span>' + escapeHtml(item.title) + '</span>') +
      '<small>' + escapeHtml(item.available ? item.path : item.registered ? 'Заказ больше не находится в этом объекте' : 'Заказ недоступен или убран из списка') +
      '</small></div><div class="order-link-actions">' +
      '<button type="button" class="secondary-button" data-related-target="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml((linked ? 'Убрать связь: ' : 'Связать: ') + item.title) + '"' +
      (edit.saving || edit.loading || edit.conflict || unknown || edit.data?.group_error || edit.data?.needs_primary || !item.editable ? ' disabled' : '') + '>' + (linked ? 'Убрать связь' : 'Связать') + '</button></div></div>').join`, `visible.map`.

## refreshOrderLinks

[static/app.js:2738](../../../static/app.js#L2738) · `FunctionDeclaration`.

```javascript
async function refreshOrderLinks()
```

Перечитывает подтверждённую группу связей из базы.

Использует `/api/order-links`.

Непосредственные вызовы: `renderOrderLinks`, `request`, `apiUrl`, `applyOrderRecord`, `hasOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `edit.loading`, `edit.error`, `edit.data`, `edit.conflict`.

## openOrderLinks

[static/app.js:2762](../../../static/app.js#L2762) · `FunctionDeclaration`.

```javascript
async function openOrderLinks(path)
```

Открывает окно связей выбранного заказа объекта.

Использует `isObjectOrderList`, `findListOrder`, `orderRowSaving`.

Непосредственные вызовы: `isObjectOrderList`, `findListOrder`, `orderRowSaving`, `$`, `$("orderLinksDialog").showModal`, `$("orderLinksSearch").focus`, `refreshOrderLinks`.

Прямые присваивания полям/свойствам: `state.orderLinks`, `$("orderLinksSearch").value`, `$("orderLinksOptions").scrollTop`.

## closeOrderLinks

[static/app.js:2776](../../../static/app.js#L2776) · `FunctionDeclaration`.

```javascript
function closeOrderLinks()
```

Закрывает окно связей и возвращает фокус инициатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$("orderLinksDialog").close`, `$`, `[...$("ordersTableBody").querySelectorAll('[data-order-related]')].find(button => button.dataset.orderRelated === edit.path)?.focus`, `[...$("ordersTableBody").querySelectorAll('[data-order-related]')].find`, `$("ordersTableBody").querySelectorAll`.

Прямые присваивания полям/свойствам: `state.orderLinks`.

## toggleOrderLink

[static/app.js:2786](../../../static/app.js#L2786) · `FunctionDeclaration`.

```javascript
async function toggleOrderLink(identity)
```

Добавляет или снимает выбранную связь в общей группе.

Использует `[...edit.data.items, ...edit.data.candidates].find`, `saveOrderLinksChange`, `edit.data.linked_ids.includes`.

Непосредственные вызовы: `[...edit.data.items, ...edit.data.candidates].find`, `saveOrderLinksChange`, `edit.data.linked_ids.includes`.

Прямые присваивания полям/свойствам: `edit.focusTarget`.

## initializeOrderLinks

[static/app.js:2799](../../../static/app.js#L2799) · `FunctionDeclaration`.

```javascript
async function initializeOrderLinks()
```

Выбирает главного для прежней ненаправленной группы.

Использует `saveOrderLinksChange`.

Непосредственные вызовы: `saveOrderLinksChange`.

## saveOrderLinksChange

[static/app.js:2807](../../../static/app.js#L2807) · `FunctionDeclaration`.

```javascript
async function saveOrderLinksChange(payload)
```

Сохраняет изменение группы связей с проверкой UUID и версии.

Использует `/api/order-links`.

Непосредственные вызовы: `renderOrderLinks`, `request`, `applyOrderRecord`, `hasOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `edit.saving`, `edit.error`, `edit.data`, `edit.conflict`.

## focusOrderFavorite

[static/app.js:2830](../../../static/app.js#L2830) · `FunctionDeclaration`.

```javascript
function focusOrderFavorite(path)
```

Возвращает фокус на звезду избранного заказа.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `hasOrderList`, `$("ordersTableBody").querySelectorAll("[data-order-favorite]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`.

## toggleOrderFavorite

[static/app.js:2839](../../../static/app.js#L2839) · `FunctionDeclaration`.

```javascript
async function toggleOrderFavorite(path)
```

Сохраняет изменение избранного заказа по текущей версии.

Использует `/api/order-favorite`.

Непосредственные вызовы: `flushDeadlineComments`, `findListOrder`, `orderRowSaving`, `state.favoriteSaving.add`, `hasOrderList`, `renderOrders`, `renderOrderHeading`, `renderCardDeadlines`, `request("/api/order-favorite", { path, revision: order.revision, is_favorite: !order.is_favorite }).then`, `request`, `loadOrders`, `state.favoriteSaving.delete`, `renderFavoriteOrders`, `renderExportState`, `renderStatus`, `focusOrderFavorite`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.saving`.

## orderShownOnMain

[static/app.js:2888](../../../static/app.js#L2888) · `FunctionDeclaration`.

```javascript
function orderShownOnMain(order)
```

Проверяет включение заказа в текущую главную таблицу.

Использует `["cancelled", "done"].includes`.

Непосредственные вызовы: `["cancelled", "done"].includes`.

## productionStatusGroups

[static/app.js:2894](../../../static/app.js#L2894) · `FunctionDeclaration`.

```javascript
function productionStatusGroups()
```

Возвращает согласованные группы производственных статусов.

Использует `orderStatusGroups.map`.

Непосредственные вызовы: `orderStatusGroups.map`.

## orderListGroups

[static/app.js:2903](../../../static/app.js#L2903) · `FunctionDeclaration`.

```javascript
function orderListGroups()
```

Распределяет строки текущего списка по группам статусов.

Использует `isObjectOrderList`, `productionStatusGroups().map`, `productionStatusGroups`.

Непосредственные вызовы: `isObjectOrderList`, `productionStatusGroups().map`, `productionStatusGroups`, `Object.keys(statusLabels).filter`, `Object.keys`, `groups.push`, `[...statuses.map((status) => statusLabels[status]), "Не добавлены"].join`, `statuses.map`.

## renderProductionStatusOptions

[static/app.js:2915](../../../static/app.js#L2915) · `FunctionDeclaration`.

```javascript
function renderProductionStatusOptions(selected)
```

Строит варианты производственного статуса для редактора.

Использует `productionStatusGroups().map`, `productionStatusGroups`.

Непосредственные вызовы: `productionStatusGroups().map((group, index) => {
    return '<optgroup label="— ' + (index + 1) + '-я группа —">' + group.statuses.map((status) =>
      '<option value="' + status + '"' + (selected === status ? ' selected' : '') + '>' +
      statusLabels[status] + '</option>').join("") + '</optgroup>';
  }).join`, `productionStatusGroups().map`, `productionStatusGroups`.

## renderOrderProductionStatus

[static/app.js:2925](../../../static/app.js#L2925) · `FunctionDeclaration`.

```javascript
function renderOrderProductionStatus(order)
```

Строит переключатель производственного статуса строки.

Использует `escapeHtml`, `Object.hasOwn`, `orderRowSaving`.

Непосредственные вызовы: `escapeHtml`, `Object.hasOwn`, `orderRowSaving`, `renderProductionStatusOptions`.

## renderSupplierOrderStatus

[static/app.js:2938](../../../static/app.js#L2938) · `FunctionDeclaration`.

```javascript
function renderSupplierOrderStatus(order)
```

Строит самостоятельный статус заказа поставщика.

Использует `Object.hasOwn`, `escapeHtml`, `orderRowSaving`.

Непосредственные вызовы: `Object.hasOwn`, `escapeHtml`, `orderRowSaving`, `Object.entries(supplierStatusLabels).map(([key, label]) =>
      '<option value="' + key + '"' + (status === key ? ' selected' : '') + '>' + label + '</option>').join`, `Object.entries(supplierStatusLabels).map`, `Object.entries`.

## changeOrderProductionStatus

[static/app.js:2951](../../../static/app.js#L2951) · `FunctionDeclaration`.

```javascript
async function changeOrderProductionStatus(select)
```

Сохраняет изменение производственного статуса одной строки.

Использует `/api/order-supplier-status`, `/api/order-status`.

Непосредственные вызовы: `Number`, `orderRowSaving`, `findListOrder`, `state.orderStatusSaving.add`, `select.setAttribute`, `$("ordersTableBody").querySelectorAll("[data-order-favorite], [data-order-deadline], [data-order-flag], [data-order-blue-plus], [data-order-dollar]").forEach`, `$("ordersTableBody").querySelectorAll`, `$`, `request`, `orders.find`, `Object.assign`, `isWorkOrderList`, `state.objectOrders.find`, `state.workArchivedOrders.filter`, `state.workArchivedPaths.push`, `saved.path.normalize`, `renderFavoriteOrders`, `notify`, `loadOrders`, `state.orderStatusSaving.delete`, `hasOrderList`, `renderOrders`, `[...$("ordersTableBody").querySelectorAll("[data-order-status]")].find`, `(next || $("orderSearch")).focus`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `select.disabled`, `state.workArchivedOrders`.

## renderOrderComment

[static/app.js:2994](../../../static/app.js#L2994) · `FunctionDeclaration`.

```javascript
function renderOrderComment(order)
```

Показывает первую строку комментария заказа в таблице.

Использует `String(order.note || "").split(/\r\n?|\n/, 1)[0].trim`, `String(order.note || "").split`, `String`.

Непосредственные вызовы: `String(order.note || "").split(/\r\n?|\n/, 1)[0].trim`, `String(order.note || "").split`, `String`, `escapeHtml`.

## renderOrderLocationLink

[static/app.js:3001](../../../static/app.js#L3001) · `FunctionDeclaration`.

```javascript
function renderOrderLocationLink(label, path)
```

Строит переход к клиенту или объекту заказа.

Использует `escapeHtml`, `encodeURIComponent`.

Непосредственные вызовы: `escapeHtml`, `encodeURIComponent`.

## compareOrders

[static/app.js:3009](../../../static/app.js#L3009) · `FunctionDeclaration`.

```javascript
function compareOrders(a, b, key = state.orderSort, direction = state.orderDirection)
```

Сравнивает значения заказов по выбранному порядку сортировки.

Использует `OrderSorting.compare`.

Непосредственные вызовы: `OrderSorting.compare`.

## renderMoneyOverview

[static/app.js:3015](../../../static/app.js#L3015) · `FunctionDeclaration`.

```javascript
function renderMoneyOverview()
```

Обновляет помесячную сводку из текущих планов платежей.

Использует `MoneyOverview.show`.

Непосредственные вызовы: `MoneyOverview.show`.

## renderHomeCalendar

[static/app.js:3023](../../../static/app.js#L3023) · `FunctionDeclaration`.

```javascript
function renderHomeCalendar()
```

Обновляет календарь из текущей SQLite-сводки главной.

Использует `[...state.orders, ...state.calendarSupplierOrders].map`, `HomeCalendar.show`, `orders.sort`.

Непосредственные вызовы: `[...state.orders, ...state.calendarSupplierOrders].map`, `HomeCalendar.show`, `orders.sort`, `renderCalendarTodoPreview`.

## cancelCalendarTodoPreviewSwitch

[static/app.js:3033](../../../static/app.js#L3033) · `FunctionDeclaration`.

```javascript
function cancelCalendarTodoPreviewSwitch()
```

Отменяет ожидающее переключение окна задач на соседнее событие.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.switchTimer`, `calendarTodoPreview.pendingAnchor`.

## closeCalendarTodoPreview

[static/app.js:3041](../../../static/app.js#L3041) · `FunctionDeclaration`.

```javascript
function closeCalendarTodoPreview(restoreFocus = false)
```

Закрывает окно задач календаря и отменяет отложенные действия.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `cancelCalendarTodoPreviewSwitch`, `$`, `anchor.removeAttribute`, `anchor.focus`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.anchor`, `calendarTodoPreview.pinned`, `$("calendarTodoPreview").hidden`, `calendarTodoPreview.suppressed`.

## positionCalendarTodoPreview

[static/app.js:3057](../../../static/app.js#L3057) · `FunctionDeclaration`.

```javascript
function positionCalendarTodoPreview()
```

Размещает окно задач вплотную к границе исходного события.

Использует `$`, `anchor.getBoundingClientRect`, `preview.getBoundingClientRect`.

Непосредственные вызовы: `$`, `anchor.getBoundingClientRect`, `preview.getBoundingClientRect`, `Math.max`, `Math.min`.

Прямые присваивания полям/свойствам: `preview.style.left`, `preview.style.top`.

## renderCalendarTodoPreview

[static/app.js:3068](../../../static/app.js#L3068) · `FunctionDeclaration`.

```javascript
function renderCalendarTodoPreview()
```

Показывает актуальные задачи заказа исходного события.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `findListOrder`, `closeCalendarTodoPreview`, `anchor.getBoundingClientRect`, `$("calendarViewport").getBoundingClientRect`, `$`, `orderTodoSummary`, `renderOrderTodos`, `body.contains`, `([...body.querySelectorAll('[data-order]')].find((link) => link.dataset.order === path) || body).focus`, `[...body.querySelectorAll('[data-order]')].find`, `body.querySelectorAll`, `positionCalendarTodoPreview`.

Прямые присваивания полям/свойствам: `$("calendarTodoPreviewTitle").textContent`, `$("calendarTodoPreviewCount").textContent`, `body.innerHTML`, `calendarTodoPreview.markup`, `body.scrollTop`.

## openCalendarTodoPreview

[static/app.js:3090](../../../static/app.js#L3090) · `FunctionDeclaration`.

```javascript
function openCalendarTodoPreview(anchor, pinned = false)
```

Открывает или закрепляет окно задач выбранного события.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `cancelCalendarTodoPreviewSwitch`, `clearTimeout`, `closeCalendarTodoPreview`, `$`, `anchor.setAttribute`, `renderCalendarTodoPreview`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.anchor`, `calendarTodoPreview.markup`, `$("calendarTodoPreviewBody").scrollTop`, `calendarTodoPreview.pinned`, `$("calendarTodoPreview").hidden`.

## hoverCalendarTodoPreview

[static/app.js:3109](../../../static/app.js#L3109) · `FunctionDeclaration`.

```javascript
function hoverCalendarTodoPreview(anchor)
```

Планирует открытие или смену окна после устойчивого наведения.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `$("calendarTodoPreview").contains`, `$`, `clearTimeout`, `openCalendarTodoPreview`, `cancelCalendarTodoPreviewSwitch`, `setTimeout`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.pendingAnchor`, `calendarTodoPreview.switchTimer`.

## scheduleCalendarTodoPreviewClose

[static/app.js:3121](../../../static/app.js#L3121) · `FunctionDeclaration`.

```javascript
function scheduleCalendarTodoPreviewClose()
```

Планирует закрытие окна задач после ухода мыши.

Управляет отложенным обновлением через таймер или кадр браузера.

Непосредственные вызовы: `clearTimeout`, `setTimeout`.

Прямые присваивания полям/свойствам: `calendarTodoPreview.timer`.

## renderCalendarEventControls

[static/app.js:3130](../../../static/app.js#L3130) · `FunctionDeclaration`.

```javascript
function renderCalendarEventControls()
```

Обновляет независимые отметки и доступные действия редактора события.

Использует `$`, `Boolean`.

Непосредственные вызовы: `$`, `Boolean`.

Прямые присваивания полям/свойствам: `$("calendarEventText").disabled`, `$("saveCalendarEvent").disabled`, `$("cancelCalendarEvent").disabled`, `$("refreshCalendarEvent").hidden`, `$("refreshCalendarEvent").disabled`, `$("deleteCalendarEvent").hidden`, `$("deleteCalendarEvent").disabled`.

## closeCalendarEventMenu

[static/app.js:3144](../../../static/app.js#L3144) · `FunctionDeclaration`.

```javascript
function closeCalendarEventMenu(restoreFocus = true)
```

Закрывает контекстное меню события и очищает его состояние.

Использует `$`, `(menu.slot.isConnected ? menu.slot : $("calendarViewport")).focus`.

Непосредственные вызовы: `$`, `(menu.slot.isConnected ? menu.slot : $("calendarViewport")).focus`.

Прямые присваивания полям/свойствам: `state.calendarMenu`, `$("calendarEventMenu").hidden`.

## calendarEventEntries

[static/app.js:3153](../../../static/app.js#L3153) · `FunctionDeclaration`.

```javascript
function calendarEventEntries(order, period)
```

Выбирает дневные или недельные записи текущего заказа.

Результат вычисляется из переданных аргументов и текущего состояния компонента.

## applyFreeCalendarEvent

[static/app.js:3159](../../../static/app.js#L3159) · `FunctionDeclaration`.

```javascript
function applyFreeCalendarEvent(saved)
```

Применяет подтверждённое свободное событие к локальной сводке.

Использует `state.calendarEvents.find`, `state.calendarEvents.filter`, `state.calendarEvents.push`.

Непосредственные вызовы: `state.calendarEvents.find`, `state.calendarEvents.filter`, `state.calendarEvents.push`, `state.calendarEvents.sort`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.calendarEvents`.

## applyCalendarInvoicePlan

[static/app.js:3170](../../../static/app.js#L3170) · `FunctionDeclaration`.

```javascript
function applyCalendarInvoicePlan(saved)
```

Применяет подтверждённый план платежа к локальной сводке.

Использует `state.calendarInvoicePlans.find`, `Object.assign`.

Непосредственные вызовы: `state.calendarInvoicePlans.find`, `Object.assign`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## freeCalendarIdentity

[static/app.js:3185](../../../static/app.js#L3185) · `FunctionDeclaration`.

```javascript
function freeCalendarIdentity()
```

Собирает UUID и версию свободного события для частичного запроса.

Использует `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join`.

Непосредственные вызовы: `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join`, `[...bytes].map`, `[hex.slice(0,8), hex.slice(8,12), hex.slice(12,16), hex.slice(16,20), hex.slice(20)].join`, `hex.slice`.

Прямые присваивания полям/свойствам: `bytes[6]`, `bytes[8]`.

## openCalendarEventMenu

[static/app.js:3195](../../../static/app.js#L3195) · `FunctionDeclaration`.

```javascript
function openCalendarEventMenu(slot, x, y)
```

Открывает контекстное меню с действиями для точного вида события.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `closeCalendarTodoPreview`, `state.calendarInvoicePlans.find`, `state.calendarEvents.find`, `findListOrder`, `slot.getAttribute`, `calendarEventEntries`, `state.calendarMoving.has`, `orderRowSaving`, `[0, 1].includes`, `notify`, `closeCalendarEventMenu`, `Boolean`, `order.calendar_inactive?.[period]?.includes`, `order.calendar_completed?.[period]?.includes`, `order.calendar_trip?.[period]?.includes`, `order.calendar_watch_todos?.[period]?.includes`, `$`, `$("calendarEventInactive").setAttribute`, `String`, `$("calendarEventCompleted").setAttribute`, `$("calendarEventTrip").setAttribute`, `$("calendarEventWatchTodos").setAttribute`, `["incoming", "outgoing"].includes`, `$("calendarEventCarryover").setAttribute`, `menu.querySelectorAll("[data-calendar-color]").forEach`, `menu.querySelectorAll`, `menu.getBoundingClientRect`, `Math.max`, `Math.min`, `[...menu.querySelectorAll("button")].find((button) => button.getClientRects().length).focus`, `[...menu.querySelectorAll("button")].find`.

Прямые присваивания полям/свойствам: `state.calendarMenu`, `$("calendarEventMenuName").textContent`, `$("calendarEventDayMoves").hidden`, `$("calendarEventMoveDivider").hidden`, `$("calendarEventWatchTodos").hidden`, `$("calendarEventWatchTodos").disabled`, `$("calendarEventCarryover").hidden`, `$("calendarEventCarryover").disabled`, `$("calendarEventDelete").hidden`, `$("calendarEventColors").hidden`, `menu.hidden`, `menu.style.left`, `menu.style.top`.

## moveCalendarEvent

[static/app.js:3245](../../../static/app.js#L3245) · `FunctionDeclaration`.

```javascript
async function moveCalendarEvent(days)
```

Сохраняет перенос события или плана на день/неделю.

Использует `/api/invoice-plan-calendar-move`, `/api/calendar-move`, `/api/order-calendar-move`.

Непосредственные вызовы: `state.calendarMoving.has`, `orderRowSaving`, `closeCalendarEventMenu`, `state.calendarMoving.add`, `request`, `applyCalendarInvoicePlan`, `applyFreeCalendarEvent`, `applyOrderRecord`, `Date`, `target.setUTCDate`, `target.getUTCDate`, `notify`, `target.toLocaleDateString`, `loadOrders`, `state.calendarMoving.delete`, `renderOrders`, `($("calendarWeeks").querySelector('[data-invoice-plan="' + menu.id + '"]') || $("calendarViewport")).focus`, `$("calendarWeeks").querySelector`, `$`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## toggleCalendarEventFlag

[static/app.js:3276](../../../static/app.js#L3276) · `FunctionDeclaration`.

```javascript
async function toggleCalendarEventFlag(flag)
```

Сохраняет одну независимую отметку выбранного события.

Использует `/api/invoice-plan-calendar-`, `/api/calendar-`, `/api/order-calendar-`.

Непосредственные вызовы: `state.calendarMoving.has`, `orderRowSaving`, `closeCalendarEventMenu`, `state.calendarMoving.add`, `flag.replaceAll`, `request`, `applyCalendarInvoicePlan`, `applyFreeCalendarEvent`, `applyOrderRecord`, `notify`, `loadOrders`, `state.calendarMoving.delete`, `renderOrders`, `$("calendarViewport").focus`, `$`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## applyCalendarDeletion

[static/app.js:3306](../../../static/app.js#L3306) · `FunctionDeclaration`.

```javascript
function applyCalendarDeletion(entry, saved, deleted)
```

Применяет подтверждённое удаление к локальному состоянию календаря.

Использует `state.calendarInvoicePlans.filter`, `state.calendarInvoicePlans.push`, `applyFreeCalendarEvent`.

Непосредственные вызовы: `state.calendarInvoicePlans.filter`, `state.calendarInvoicePlans.push`, `applyFreeCalendarEvent`, `applyOrderRecord`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.calendarInvoicePlans`.

## restoreCalendarDeletion

[static/app.js:3319](../../../static/app.js#L3319) · `FunctionDeclaration`.

```javascript
async function restoreCalendarDeletion(entry, revision)
```

Запрашивает восстановление удалённой записи со всеми отметками.

Использует `/api/calendar-payment-restore`, `/api/calendar-event-restore`, `/api/order-calendar-event-restore`.

Непосредственные вызовы: `state.calendarMoving.has`, `Error`, `state.calendarMoving.add`, `request`, `applyCalendarDeletion`, `notify`, `state.calendarMoving.delete`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## removeCalendarRecord

[static/app.js:3337](../../../static/app.js#L3337) · `FunctionDeclaration`.

```javascript
async function removeCalendarRecord(entry)
```

Удаляет выбранную запись через API её конкретного вида.

Использует `/api/calendar-payment-remove`, `/api/calendar-event-remove`, `/api/order-calendar-event-remove`.

Непосредственные вызовы: `state.calendarInvoicePlans.find`, `['incoming', 'outgoing'].includes`, `Error`, `state.calendarMoving.has`, `state.calendarMoving.add`, `request`, `applyCalendarDeletion`, `notify`, `state.calendarMoving.delete`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## run

[static/app.js:3353](../../../static/app.js#L3353) · `ArrowFunctionExpression`.

```javascript
run: () =>
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `restoreCalendarDeletion`.

Непосредственные вызовы: `restoreCalendarDeletion`.

## deleteCalendarEventFromMenu

[static/app.js:3363](../../../static/app.js#L3363) · `FunctionDeclaration`.

```javascript
async function deleteCalendarEventFromMenu()
```

Удаляет точное событие из открытого меню или редактора.

Использует `findListOrder`, `state.calendarEvents.find`, `calendarEventEntries`.

Непосредственные вызовы: `findListOrder`, `state.calendarEvents.find`, `calendarEventEntries`, `closeCalendarEventMenu`, `removeCalendarRecord`, `notify`, `loadOrders`.

## deleteCalendarEventFromDialog

[static/app.js:3378](../../../static/app.js#L3378) · `FunctionDeclaration`.

```javascript
async function deleteCalendarEventFromDialog()
```

Удаляет точное событие из открытого меню или редактора.

Использует `renderCalendarEventControls`, `removeCalendarRecord`, `closeCalendarEvent`.

Непосредственные вызовы: `renderCalendarEventControls`, `removeCalendarRecord`, `closeCalendarEvent`, `$`.

Прямые присваивания полям/свойствам: `edit.saving`, `edit.conflict`, `$("calendarEventState").textContent`.

## colorCalendarEvent

[static/app.js:3398](../../../static/app.js#L3398) · `FunctionDeclaration`.

```javascript
async function colorCalendarEvent(color)
```

Сохраняет индивидуальный цвет выбранного события.

Использует `/api/calendar-color`, `/api/order-calendar-color`.

Непосредственные вызовы: `state.calendarMoving.has`, `orderRowSaving`, `closeCalendarEventMenu`, `state.calendarMoving.add`, `request`, `applyFreeCalendarEvent`, `applyOrderRecord`, `notify`, `loadOrders`, `state.calendarMoving.delete`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`.

## openCalendarEvent

[static/app.js:3421](../../../static/app.js#L3421) · `FunctionDeclaration`.

```javascript
function openCalendarEvent(slot)
```

Открывает текстовый редактор выбранного события или план платежа.

Использует `closeCalendarEventMenu`, `state.calendarEvents.find`, `findListOrder`.

Непосредственные вызовы: `closeCalendarEventMenu`, `state.calendarEvents.find`, `findListOrder`, `state.calendarMoving.has`, `orderRowSaving`, `calendarEventEntries`, `notify`, `Boolean`, `order.calendar_inactive?.[period]?.includes`, `order.calendar_completed?.[period]?.includes`, `order.calendar_trip?.[period]?.includes`, `order.calendar_watch_todos?.[period]?.includes`, `freeCalendarIdentity`, `$`, `(order.work_supplier ? [order.title, order.work_supplier] : [order.title, order.client, order.object]).filter(Boolean).join`, `(order.work_supplier ? [order.title, order.work_supplier] : [order.title, order.client, order.object]).filter`, `Date`, `Intl.DateTimeFormat`, `end.setUTCDate`, `end.getUTCDate`, `format.format`, `renderCalendarEventControls`, `$("calendarEventDialog").showModal`, `$("calendarEventText").focus`.

Прямые присваивания полям/свойствам: `state.calendarEvent`, `$("calendarEventTitle").textContent`, `$("calendarEventOrder").textContent`, `$("calendarEventDate").textContent`, `$("calendarEventText").value`, `$("calendarEventState").textContent`.

## closeCalendarEvent

[static/app.js:3452](../../../static/app.js#L3452) · `FunctionDeclaration`.

```javascript
function closeCalendarEvent()
```

Закрывает редактор календаря и очищает связанное состояние.

Использует `$("calendarEventDialog").close`, `$`.

Непосредственные вызовы: `$("calendarEventDialog").close`, `$`.

Прямые присваивания полям/свойствам: `state.calendarEvent`.

## saveCalendarEvent

[static/app.js:3460](../../../static/app.js#L3460) · `FunctionDeclaration`.

```javascript
async function saveCalendarEvent()
```

Сохраняет текст события с UUID, периодом и ожидаемой версией.

Использует `/api/calendar-event`, `/api/order-calendar-event`.

Непосредственные вызовы: `$`, `text.trim`, `renderCalendarEventControls`, `request`, `applyFreeCalendarEvent`, `applyOrderRecord`, `closeCalendarEvent`, `renderOrders`, `notify`.

Прямые присваивания полям/свойствам: `$("calendarEventState").textContent`, `edit.saving`, `state.ordersRequest`, `edit.conflict`.

## refreshCalendarEvent

[static/app.js:3488](../../../static/app.js#L3488) · `FunctionDeclaration`.

```javascript
async function refreshCalendarEvent()
```

Перечитывает источник события при конфликте, сохраняя черновик формы.

Использует `/api/calendar-event`, `/api/order`.

Непосредственные вызовы: `renderCalendarEventControls`, `request`, `encodeURIComponent`, `Error`, `Boolean`, `applyFreeCalendarEvent`, `apiUrl`, `calendarEventEntries`, `order.calendar_inactive?.[edit.period]?.includes`, `order.calendar_completed?.[edit.period]?.includes`, `order.calendar_trip?.[edit.period]?.includes`, `order.calendar_watch_todos?.[edit.period]?.includes`, `applyOrderRecord`, `$`, `renderOrders`.

Прямые присваивания полям/свойствам: `edit.saving`, `edit.revision`, `edit.previous`, `edit.inactive`, `edit.completed`, `edit.trip`, `edit.color`, `edit.conflict`, `edit.watch_todos`, `$("calendarEventState").textContent`.

## renderWorkOrders

[static/app.js:3533](../../../static/app.js#L3533) · `FunctionDeclaration`.

```javascript
function renderWorkOrders(orders, options)
```

Обновляет сводку производственных заказов текущего раздела.

Использует `orderGroupScope`, `state.workOrderGroups.map`.

Непосредственные вызовы: `orderGroupScope`, `state.workOrderGroups.map((group) => {
    const rows = orders.filter((order) => order.path.normalize("NFC").split("/").slice(0, -1).join("/") === group.key);
    if (!rows.length) return "";
    const collapsed = orderGroupCollapsed(scope, group.key);
    const style = group.color ? ' style="--supplier-hue:' + Number(group.color.hue) + '"' : '';
    return '<tr class="order-group-divider"' + style + '><th colspan="7"><button type="button" class="order-group-toggle" data-order-group-toggle="' + escapeHtml(group.key) +
      '" data-order-group-scope="' + escapeHtml(scope) + '" aria-expanded="' + !collapsed + '"><span class="order-group-chevron" aria-hidden="true">▸</span><span>' + escapeHtml(group.label) +
      '</span><span class="count-badge">' + rows.length + '</span></button></th><td></td><td class="order-deadline-column">' + renderDeadlineMonthLegend(options) + '</td><td></td></tr>' +
      rows.map((order) => '<tr data-order-group-row="' + escapeHtml(group.key) + '"' + style + (group.color?.neutral ? ' class="supplier-neutral"' : '') + (collapsed ? ' hidden' : '') + '>' +
        '<td class="order-blue-plus-column">' + renderOrderMarkerButton(order, "bluePlus") + '</td><td class="order-dollar-column">' + renderOrderMarkerButton(order, "dollar") + '</td><td class="order-flag-column">' + renderOrderMarkerButton(order, "flag") + '</td>' +
        '<td class="order-favorite-column">' + renderOrderFavoriteButton(order) + '</td><td class="order-todo-column">' + renderOrderTodoButton(order) + '</td>' +
        '<td><button class="order-row-link" data-order="' + escapeHtml(order.path) + '">' + escapeHtml(order.title) + '</button>' + (order.registered === false ? '<span class="order-unregistered-label">Не добавлен в производство</span>' : '') +
        '<span class="order-row-path">' + escapeHtml(order.path) + '</span></td><td class="order-comment-column">' + renderOrderComment(order) + '</td><td>' + renderSupplierOrderStatus(order) + '</td>' +
        '<td class="order-deadline-column">' + renderOrderDeadlines(order, { options }) + '</td><td class="order-updated">' + (order.folder_date ? escapeHtml(order.folder_date.split("-").reverse().join(".")) : '—') + '</td></tr>').join("");
  }).join`, `state.workOrderGroups.map`.

## renderWorkArchive

[static/app.js:3554](../../../static/app.js#L3554) · `FunctionDeclaration`.

```javascript
function renderWorkArchive()
```

Показывает архивные заказы поставщиков с возможностью возврата.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `$`, `isWorkOrderList`, `state.workArchivedOrders.filter(order => order.supplier_status === "archived")
    .sort((a, b) => (b.archived_at || 0) - (a.archived_at || 0) || (b.archive_sequence || 0) - (a.archive_sequence || 0) || compareOrderText(a.path, b.path)).slice`, `state.workArchivedOrders.filter(order => order.supplier_status === "archived")
    .sort`, `state.workArchivedOrders.filter`, `rows.map(order => '<div class="work-archive-row"><div><a class="order-row-link" data-work-archive-order="' + escapeHtml(order.path) +
    '" href="?path=' + encodeURIComponent(order.path) + '">' + escapeHtml(order.title) + '</a><small>' + escapeHtml([order.work_supplier, order.path].filter(Boolean).join(" · ")) +
    '</small></div><span class="work-archive-date">' + (order.archived_at ? escapeHtml(formatDate(order.archived_at)) : '') + '</span><button type="button" class="secondary-button" data-work-archive-restore="' + escapeHtml(order.path) +
    '"' + (orderRowSaving(order.path) || order.registered === false || order.supplier_status === null ? ' disabled' : '') + '>Вернуть в работу</button></div>').join`, `rows.map`, `([...section.querySelectorAll("[data-work-archive-restore]")].find(button => button.dataset.workArchiveRestore === focused) || $("workArchiveHeading")).focus`, `[...section.querySelectorAll("[data-work-archive-restore]")].find`, `section.querySelectorAll`.

Прямые присваивания полям/свойствам: `section.hidden`, `$("workArchiveCount").textContent`, `$("workArchiveList").innerHTML`.

## restoreWorkArchive

[static/app.js:3571](../../../static/app.js#L3571) · `FunctionDeclaration`.

```javascript
async function restoreWorkArchive(button)
```

Снимает архивирование выбранного заказа поставщика.

Использует `/api/order-supplier-status`.

Непосредственные вызовы: `state.workArchivedOrders.find`, `orderRowSaving`, `state.orderStatusSaving.add`, `renderWorkArchive`, `request`, `isWorkOrderList`, `state.workArchivedOrders.filter`, `state.workArchivedPaths.filter`, `state.objectOrders.some`, `state.objectOrders.push`, `applyOrderRecord`, `notify`, `loadOrders`, `state.orderStatusSaving.delete`, `hasOrderList`, `renderOrders`.

Прямые присваивания полям/свойствам: `state.ordersRequest`, `state.workArchivedOrders`, `state.workArchivedPaths`.

## renderOrders

[static/app.js:3601](../../../static/app.js#L3601) · `FunctionDeclaration`.

```javascript
function renderOrders({ force = false } = {})
```

Перестраивает строки текущего списка из локальных данных.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.activeElement?.closest`, `relatedLink.closest('tr').querySelector`, `relatedLink.closest`, `$("ordersWorkspace").querySelector`, `$`, `document.querySelector`, `orderListRows().filter`, `orderListRows`, `isObjectOrderList`, `isWorkOrderList`, `orderListDeadlineOptions`, `renderWorkArchive`, `renderHomeCalendar`, `normalize`, `state.orderQuery.trim`, `orders.filter`, `filtered.sort`, `orderGroupScope`, `orderListGroups().map`, `orderListGroups`, `filtered.forEach`, `renderWorkOrders`, `groups.filter((group) => group.orders.length).map((group) =>
    '<tr class="order-group-divider"><th colspan="' + (object ? 11 : 10) + '"><button type="button" class="order-group-toggle" data-order-group-toggle="' + group.key +
    '" data-order-group-scope="' + escapeHtml(groupScope) + '" aria-expanded="' + !group.collapsed +
    '"><span class="order-group-chevron" aria-hidden="true">▸</span><span>' + escapeHtml(group.label) +
    '</span><span class="count-badge">' + group.orders.length + '</span></button></th><td class="order-deadline-column">' + renderDeadlineMonthLegend(deadlineOptions) + '</td><td colspan="2"></td></tr>' +
    group.orders.map((order) => '<tr data-order-group-row="' + group.key + '"' + (group.collapsed ? ' hidden' : '') + '><td class="order-blue-plus-column">' + renderOrderMarkerButton(order, "bluePlus") + '</td><td class="order-dollar-column">' + renderOrderMarkerButton(order, "dollar") + '</td><td class="order-flag-column">' + renderOrderMarkerButton(order, "flag") + '</td><td class="order-favorite-column">' + renderOrderFavoriteButton(order) + '</td>' + (object ? '<td class="order-related-column">' + renderOrderRelatedButton(order) + '</td>' : '') + '<td class="order-todo-column">' + renderOrderTodoButton(order) + '</td><td class="order-todo-column">' + renderOrderPurchaseButton(order) + '</td><td class="order-client-column">' + renderOrderLocationLink(order.client, order.client_path) + '</td><td class="order-object-column">' + renderOrderLocationLink(order.object, order.object_path) + '</td><td><button class="order-row-link" data-order="' + escapeHtml(order.path) + '">' + escapeHtml(order.title) + '</button>' + (order.registered === false ? '<span class="order-unregistered-label">Не добавлен</span>' : '') + '<span class="order-row-path">' + escapeHtml(order.path) + '</span>' + (object ? renderCompactOrderLinks(order) : '') + '</td><td class="order-comment-column">' + renderOrderComment(order) + '</td><td class="order-deadline-column">' + renderOrderDeadlines(order, { options: deadlineOptions }) + '</td><td>' + renderOrderProductionStatus(order) + '</td>' +
    '<td class="order-updated">' + (order.updated ? formatDate(order.updated) : '—') + (order.sync_pending ? '<span class="sync-pending" title="' + escapeHtml(order.sync_error || "Ожидает выгрузки в папку") + '">' + (order.sync_error ? "В очереди · автоповтор" : "Ожидает выгрузки") + '</span>' : '<span class="sync-complete">' + (order.storage === 'database' ? 'В базе' : 'Выгружено') + '</span>') + '</td></tr>').join("")).join`, `groups.filter((group) => group.orders.length).map`, `groups.filter`, `Boolean`, `pending.filter`, `[scan?.folders ? "Поиск завершён: добавлено " + scan.added + (scan.errors.length ? ", ошибок: " + scan.errors.length : "") : "", errors.length ? "Сохранено в базе · в очереди выгрузки: " + pending.length + " · ошибок: " + errors.length + " · повторим автоматически" : pending.length ? "Ожидает выгрузки: " + pending.length : "Изменения выгружены в папки"].filter(Boolean).join`, `[scan?.folders ? "Поиск завершён: добавлено " + scan.added + (scan.errors.length ? ", ошибок: " + scan.errors.length : "") : "", errors.length ? "Сохранено в базе · в очереди выгрузки: " + pending.length + " · ошибок: " + errors.length + " · повторим автоматически" : pending.length ? "Ожидает выгрузки: " + pending.length : "Изменения выгружены в папки"].filter`, `storage.errors.slice(0, 2).map(item => item.path + ": " + item.error).join`, `storage.errors.slice(0, 2).map`, `storage.errors.slice`, `formatDate`, `Date.parse`, `scan.errors.slice(0, 3).join`, `scan.errors.slice`, `state.unregistrations.some`, `$("ordersWorkspace").querySelectorAll("th").forEach`, `$("ordersWorkspace").querySelectorAll`, `renderOrderTodoDialog`, `focusOrderMarker`, `focusOrderFavorite`, `[...$("ordersTableBody").querySelectorAll("[data-order-related]")].find(button => button.dataset.orderRelated === focusedRelated)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-related]")].find`, `$("ordersTableBody").querySelectorAll`, `[...$("ordersTableBody").querySelectorAll('[data-order]')].find(button => button.dataset.order === focusedRelatedLink.path)?.closest`, `[...$("ordersTableBody").querySelectorAll('[data-order]')].find`, `[...(row?.querySelectorAll('[data-related-card-id]') || [])].find(link => link.dataset.relatedCardId === focusedRelatedLink.id)?.focus`, `[...(row?.querySelectorAll('[data-related-card-id]') || [])].find`, `row?.querySelectorAll`, `focusOrderDeadline`, `[...$("ordersTableBody").querySelectorAll("[data-order-calendar-compact]")].find(el => el.dataset.orderCalendarCompact === focusedCompact)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order-calendar-compact]")].find`, `focusOrderGroup`, `[...$("ordersTableBody").querySelectorAll("[data-order], [data-order-todos]")].find((button) => focusedOrder ? button.dataset.order === focusedOrder : button.dataset.orderTodos === focusedTodos)?.focus`, `[...$("ordersTableBody").querySelectorAll("[data-order], [data-order-todos]")].find`.

Прямые присваивания полям/свойствам: `$(work ? "workOrderDirectoryCount" : object ? "objectOrdersSummary" : "folderSummary").textContent`, `$("ordersTableBody").innerHTML`, `$("ordersEmpty").hidden`, `$("ordersEmptyTitle").textContent`, `$("ordersEmptyHint").textContent`, `$("ordersSyncState").textContent`, `listScroll.scrollLeft`, `pane.scrollTop`.

## showOrders

[static/app.js:3687](../../../static/app.js#L3687) · `FunctionDeclaration`.

```javascript
async function showOrders({ history = true } = {})
```

Открывает главную страницу и загружает её сводку.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `closeCalendarTodoPreview`, `$`, `$("orderTodoDialog").close`, `closePreview`, `saveCurrentPrintTask`, `saveCurrentStatus`, `state.folderRequest?.abort`, `mountOrderList`, `state.selectedFiles.clear`, `$("homeButton").setAttribute`, `document.querySelector(".content-pane").setAttribute`, `document.querySelector`, `window.history.pushState`, `renderTree`, `renderOrders`, `document.dispatchEvent`, `Event`, `loadOrders`.

Прямые присваивания полям/свойствам: `state.navigation`, `state.view`, `state.folder`, `state.imageReport`, `state.printTask`, `state.selected`, `$("folderView").hidden`, `$("ordersWorkspace").hidden`, `$("openFolderButton").hidden`, `$("addOrderButton").hidden`, `$("removeOrderButton").hidden`, `$("createObjectFolderButton").hidden`, `$("groupObjectYearsButton").hidden`, `$("createOrderFolderButton").hidden`, `$("createEventFolderButton").hidden`, `$("renameFolderButton").hidden`, `$("deleteEventButton").hidden`, `$("openEventTrash").hidden`, `$("notice").hidden`, `$("loadOrderFilesButton").hidden`, `$("breadcrumbs").innerHTML`, `$("workSupplierName").hidden`, `$("folderTitleText").textContent`, `$("orderFolderName").hidden`, `$("orderPageFavorite").hidden`, `$("clientLabel").textContent`, `$("scanState").textContent`.

## openLocation

[static/app.js:3735](../../../static/app.js#L3735) · `FunctionDeclaration`.

```javascript
function openLocation()
```

Открывает сохранённое местоположение заказа в дереве.

Использует `URLSearchParams`, `params.has`, `navigate`.

Непосредственные вызовы: `URLSearchParams`, `params.has`, `navigate`, `params.get`, `showOrders`.

## navigate

[static/app.js:3742](../../../static/app.js#L3742) · `FunctionDeclaration`.

```javascript
async function navigate(path, { history = true } = {})
```

Загружает выбранную папку и применяет соответствующий интерфейс.

Использует `/api/order`, `/api/todos-refresh`.

Непосредственные вызовы: `closeCalendarTodoPreview`, `$`, `$("orderTodoDialog").close`, `closePreview`, `saveCurrentPrintTask`, `saveCurrentStatus`, `state.folderRequest?.abort`, `AbortController`, `document.querySelector(".content-pane").setAttribute`, `document.querySelector`, `request`, `apiUrl`, `path.split`, `parts.at`, `parts.map`, `fetch`, `folderUrl`, `response.json`, `Error`, `Boolean`, `$("homeButton").removeAttribute`, `(data.objectOrders?.archived_paths || []).map`, `state.selectedFiles.clear`, `window.history.pushState`, `encodeURIComponent`, `renderTree`, `renderFolder`, `document.dispatchEvent`, `Event`, `run`, `revealPath(data.path, navigation).catch`, `revealPath`, `notify`.

Прямые присваивания полям/свойствам: `state.navigation`, `state.folderRequest`, `$("scanState").textContent`, `data.service`, `state.view`, `$("folderView").hidden`, `$("ordersWorkspace").hidden`, `$("openFolderButton").hidden`, `state.folder`, `state.objectOrders`, `state.objectOrdersError`, `state.workOrderGroups`, `state.workArchivedOrders`, `state.workArchivedPaths`, `state.deadlineWeekOptions`, `$("fileTrashState").textContent`, `state.imageReport`, `state.printTask`, `$("frezaTaskSearch").value`, `$("frezaLegacyFolders").open`, `state.selected`, `state.fileType`, `state.fileQuery`, `state.limit`, `state.dirty`, `document.querySelector(".content-pane").scrollTop`, `$("notice").textContent`, `$("notice").hidden`.

## loadOrderFiles

[static/app.js:3829](../../../static/app.js#L3829) · `FunctionDeclaration`.

```javascript
async function loadOrderFiles(path, navigation)
```

Запрашивает доступный перечень вложений выбранного заказа.

Дожидается серверного ответа; ошибку передаёт вызывающему обработчику.

Непосредственные вызовы: `$`, `fetch`, `folderUrl`, `response.json`, `Error`, `Object.assign`, `renderFolder`.

Прямые присваивания полям/свойствам: `$("loadOrderFilesButton").hidden`, `$("scanState").textContent`, `state.folder.filesLoading`, `state.folder.filesUnavailable`, `state.folder.warnings`.

## openNative

[static/app.js:3853](../../../static/app.js#L3853) · `FunctionDeclaration`.

```javascript
async function openNative(path, reveal = false)
```

Просит сервер открыть проверенную папку или документ на Mac.

Использует `/api/open`.

Непосредственные вызовы: `request`.

## renderFolderRename

[static/app.js:3859](../../../static/app.js#L3859) · `FunctionDeclaration`.

```javascript
function renderFolderRename()
```

Показывает предварительный результат формы переименования.

Использует `folderParent`, `$`, `$("renameFolderName").value.trim().normalize`.

Непосредственные вызовы: `folderParent`, `$`, `$("renameFolderName").value.trim().normalize`, `$("renameFolderName").value.trim`.

Прямые присваивания полям/свойствам: `$("renameFolderDestination").textContent`.

## openFolderRename

[static/app.js:3866](../../../static/app.js#L3866) · `FunctionDeclaration`.

```javascript
async function openFolderRename()
```

Открывает форму переименования выбранной папки.

Использует `/api/folder-rename`.

Непосредственные вызовы: `saveCurrentPrintTask`, `saveCurrentStatus`, `request`, `apiUrl`, `$`, `renderFolderRename`, `$("renameFolderDialog").showModal`, `$("renameFolderName").focus`, `$("renameFolderName").select`.

Прямые присваивания полям/свойствам: `state.folderRename`, `$("renameFolderSource").textContent`, `$("renameFolderName").value`, `$("renameFolderError").hidden`.

## submitFolderRename

[static/app.js:3882](../../../static/app.js#L3882) · `FunctionDeclaration`.

```javascript
async function submitFolderRename()
```

Выполняет подтверждённое переименование и применяет новые пути.

Использует `/api/folder-rename`.

Непосредственные вызовы: `controls.forEach`, `$`, `saveCurrentStatus`, `request`, `$("renameFolderDialog").close`, `Set`, `[...state.expanded].map`, `window.history.replaceState`, `encodeURIComponent`, `reloadClientTrees`, `navigate`, `loadOrders`, `notify`.

Прямые присваивания полям/свойствам: `state.folderRenaming`, `$("renameFolderError").hidden`, `$("renameFolderError").textContent`, `state.expanded`.

## moved

[static/app.js:3903](../../../static/app.js#L3903) · `ArrowFunctionExpression`.

```javascript
const moved = (path) =>
```

Обновляет путь элемента интерфейса после подтверждённого переноса папок.

Использует `path.startsWith`, `path.slice`.

Непосредственные вызовы: `path.startsWith`, `path.slice`.

## showPreview

[static/app.js:3914](../../../static/app.js#L3914) · `FunctionDeclaration`.

```javascript
async function showPreview(path)
```

Открывает подходящий просмотрщик выбранного файла.

Использует `/api/file`, `/api/freza-preview`, `/api/preview`.

Непосредственные вызовы: `saveFileComment`, `state.folder.files.find`, `SpreadsheetPreview.close`, `$`, `formatSize`, `formatDate`, `apiUrl`, `filteredFiles`, `files.findIndex`, `$("previewBody").replaceChildren`, `$("previewDialog").showModal`, `run`, `["image", "cdr"].includes`, `document.createElement`, `media.addEventListener`, `SpreadsheetPreview.open`, `request`, `Error`, `showPdfPages`, `previewUnavailable`, `$("previewBody").appendChild`.

Прямые присваивания полям/свойствам: `state.preview`, `$("previewNative").hidden`, `$("fileCommentLabel").textContent`, `$("fileCommentText").maxLength`, `$("previewTitle").textContent`, `$("previewPath").textContent`, `$("previewMeta").textContent`, `$("previewDownload").href`, `$("previewFolderNotePath").textContent`, `$("previewFolderNote").value`, `$("previewPrevious").disabled`, `$("previewNext").disabled`, `media.src`, `media.alt`, `$("previewBody").textContent`, `media.controls`, `media.preload`, `media.textContent`.

## showInvoicePreview

[static/app.js:3991](../../../static/app.js#L3991) · `FunctionDeclaration`.

```javascript
async function showInvoicePreview(record)
```

Открывает общий PDF-просмотр для сохранённого счёта или вложения.

Использует `/api/invoice-pdf`, `/api/invoice-pdf-info`.

Непосредственные вызовы: `saveFileComment`, `SpreadsheetPreview.close`, `$`, `record.data.date.split("-").reverse().join`, `record.data.date.split("-").reverse`, `record.data.date.split`, `apiUrl`, `$("previewDialog").showModal`, `run`, `request`, `Error`, `showPdfPages`, `previewUnavailable`.

Прямые присваивания полям/свойствам: `state.preview`, `$("previewTitle").textContent`, `$("previewPath").textContent`, `$("previewMeta").textContent`, `$("previewDownload").href`, `$("previewFolderNotePath").textContent`, `$("previewFolderNote").value`, `$("previewPrevious").disabled`, `$("previewNext").disabled`, `$("previewNative").hidden`, `$("fileCommentLabel").textContent`, `$("fileCommentText").maxLength`, `$("previewBody").textContent`.

## renderFileComment

[static/app.js:4022](../../../static/app.js#L4022) · `FunctionDeclaration`.

```javascript
function renderFileComment()
```

Заполняет редактор комментария точного файла.

Использует `Boolean`, `$`, `$("fileCommentState").classList.toggle`.

Непосредственные вызовы: `Boolean`, `$`, `$("fileCommentState").classList.toggle`.

Прямые присваивания полям/свойствам: `$("fileCommentText").disabled`, `$("saveFileComment").disabled`, `$("saveFileComment").textContent`, `$("cancelFileComment").hidden`, `$("cancelFileComment").disabled`, `$("reloadFileComment").hidden`, `$("fileCommentState").textContent`.

## loadFileComment

[static/app.js:4037](../../../static/app.js#L4037) · `FunctionDeclaration`.

```javascript
async function loadFileComment(path, version)
```

Читает комментарий файла и сохраняет его проверочную версию.

Использует `/api/invoice`, `/api/file-comment`.

Непосредственные вызовы: `state.folder?.files.find`, `$`, `renderFileComment`, `request`, `apiUrl`, `Error`, `Object.assign`, `updateFileCommentCaption`.

Прямые присваивания полям/свойствам: `state.fileComment`, `$("fileCommentText").value`, `comment.loading`, `comment.error`.

## saveFileComment

[static/app.js:4063](../../../static/app.js#L4063) · `FunctionDeclaration`.

```javascript
async function saveFileComment()
```

Сохраняет текст комментария по привязке файла и версии.

Использует `/api/invoice-comment`, `/api/file-comment`.

Непосредственные вызовы: `saveFileComment`, `Error`, `request`, `renderFileComment`, `Object.assign`, `document.dispatchEvent`, `Event`, `updateFileCommentCaption`.

Прямые присваивания полям/свойствам: `state.fileCommentSaving`, `comment.error`.

## closePreview

[static/app.js:4097](../../../static/app.js#L4097) · `FunctionDeclaration`.

```javascript
async function closePreview()
```

Закрывает просмотрщик и освобождает его локальные ресурсы.

Использует `saveFileComment`, `$("previewDialog").close`, `$`.

Непосредственные вызовы: `saveFileComment`, `$("previewDialog").close`, `$`.

## showPdfPages

[static/app.js:4104](../../../static/app.js#L4104) · `FunctionDeclaration`.

```javascript
function showPdfPages(file, pages, version)
```

Загружает сведения о PDF и показывает выбранные страницы.

Использует `/api/invoice-pdf-page`, `/api/pdf-page`.

Непосредственные вызовы: `document.createElement`, `previous.setAttribute`, `next.setAttribute`, `String`, `input.setAttribute`, `label.append`, `document.createTextNode`, `toolbar.append`, `canvas.append`, `viewer.append`, `image.addEventListener`, `previous.addEventListener`, `next.addEventListener`, `input.addEventListener`, `$("previewBody").replaceChildren`, `$`, `changePage`.

Прямые присваивания полям/свойствам: `viewer.className`, `toolbar.className`, `previous.textContent`, `next.textContent`, `label.textContent`, `input.type`, `input.min`, `input.max`, `canvas.className`.

## changePage

[static/app.js:4131](../../../static/app.js#L4131) · `FunctionDeclaration`.

```javascript
function changePage(page)
```

Переключает отображаемую страницу текущего документа.

Использует `/api/invoice-pdf-page`, `/api/pdf-page`.

Непосредственные вызовы: `Math.min`, `Math.max`, `String`, `apiUrl`.

Прямые присваивания полям/свойствам: `input.value`, `previous.disabled`, `next.disabled`, `image.alt`, `image.src`, `canvas.scrollTop`.

## previewUnavailable

[static/app.js:4152](../../../static/app.js#L4152) · `FunctionDeclaration`.

```javascript
function previewUnavailable(message)
```

Показывает ошибку или недоступность превью без замены исходника.

Подключает обработчики событий к существующим элементам компонента.

Непосредственные вызовы: `document.createElement`, `$`, `button.addEventListener`, `wrapper.append`, `$("previewBody").replaceChildren`.

Прямые присваивания полям/свойствам: `wrapper.className`, `label.textContent`, `text.textContent`, `button.className`, `button.textContent`, `button.href`.

## setPreviewExpanded

[static/app.js:4171](../../../static/app.js#L4171) · `FunctionDeclaration`.

```javascript
function setPreviewExpanded(expanded)
```

Переключает полнооконный просмотр с сохранением редактора комментария.

Использует `$("previewDialog").classList.toggle`, `$`, `$("previewExpand").setAttribute`.

Непосредственные вызовы: `$("previewDialog").classList.toggle`, `$`, `$("previewExpand").setAttribute`, `String`.

Прямые присваивания полям/свойствам: `$("previewExpand").textContent`, `$("previewExpand").title`.

## stepPreview

[static/app.js:4180](../../../static/app.js#L4180) · `FunctionDeclaration`.

```javascript
function stepPreview(direction)
```

Переходит к предыдущему или следующему файлу текущего набора.

Использует `filteredFiles`, `files.findIndex`, `run`.

Непосредственные вызовы: `filteredFiles`, `files.findIndex`, `run`.

## run

[static/app.js:4189](../../../static/app.js#L4189) · `FunctionDeclaration`.

```javascript
function run(action)
```

Выполняет сохранённое действие отмены или подтверждённую операцию компонента.

Использует `Promise.resolve().then(action).catch`, `Promise.resolve().then`, `Promise.resolve`.

Непосредственные вызовы: `Promise.resolve().then(action).catch`, `Promise.resolve().then`, `Promise.resolve`.

## askRemoveOrder

[static/app.js:4598](../../../static/app.js#L4598) · `FunctionDeclaration`.

```javascript
function askRemoveOrder(path)
```

Открывает предусмотренное подтверждение снятия регистрации заказа.

Использует `state.orders.find`, `notify`, `$`.

Непосредственные вызовы: `state.orders.find`, `notify`, `$`, `isWorkOrderPath`, `$("removeOrderDialog").showModal`, `$("cancelRemoveOrder").focus`.

Прямые присваивания полям/свойствам: `state.removeOrder`, `$("removeOrderName").textContent`, `$("removeOrderPath").textContent`, `$("removeOrderTitle").textContent`, `$("confirmRemoveOrder").textContent`, `$("removeOrderDescription").textContent`.
