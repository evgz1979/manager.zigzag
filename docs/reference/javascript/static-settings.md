# static/settings.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/settings.js](../../../static/settings.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-changeCalendarPassword"></a>

## changeCalendarPassword

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function changeCalendarPassword(action)
```

Меняет отдельный пароль приложения через текущую сессию настроек.

Показывает пароль один раз и сохраняет его только до закрытия окна.

Непосредственные вызовы: `window.confirm`, `fetch`, `JSON.stringify`, `response.json`, `caldavPassword.focus`, `caldavPassword.select`.

Прямые присваивания полям/свойствам: `caldavGenerate.disabled`, `caldavRevoke.disabled`, `close.disabled`, `caldavStatus.textContent`, `caldavPassword.value`, `caldavPassword.parentElement.hidden`.

<a id="symbol-loadSeller"></a>

## loadSeller

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function loadSeller(preserve = false)
```

Загружает общие реквизиты отдельно от настроек пароля и открытого счёта.

Явная проверка конфликта сохраняет ввод и показывает актуальные значения перед повторной записью.

Непосредственные вызовы: `fetch`, `response.json`, `Error`, `sellerFields.querySelectorAll`, `Object.entries(sellerLabels).map(([key, caption]) => caption + ': ' + (data.seller[key] || '—')).join`, `Object.entries(sellerLabels).map`, `Object.entries`.

Прямые присваивания полям/свойствам: `sellerStatus.textContent`, `input.value`, `sellerFields.disabled`, `sellerSave.disabled`.

<a id="symbol-loadWeekHighlights"></a>

## loadWeekHighlights

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function loadWeekHighlights()
```

Читает актуальную версию при открытии вкладки или явной загрузке сохранённых недель.

Переключение разделов настроек сохраняет редактор и черновик в том же сеансе.

Непосредственные вызовы: `updateWeekHighlights`, `renderWeekHighlights`, `fetch`, `response.json`, `Error`, `Set`, `applyDeadlineHighlights`.

Прямые присваивания полям/свойствам: `edit.loading`, `highlightStatus.textContent`, `edit.pageSize`, `edit.currentWeek`, `edit.firstWeek`, `edit.saved`, `edit.weeks`, `edit.revision`, `edit.blocked`.

<a id="symbol-openSettings"></a>

## openSettings

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function openSettings()
```

Открывает настройки без замены содержимого страницы или её черновиков.

Токен и режим смены пароля загружаются только при явном открытии окна.

Непосредственные вызовы: `form.reset`, `selectSettingsTab`, `dialog.showModal`, `loadSeller`, `fetch`, `response.json`, `document.getElementById`.

Прямые присваивания полям/свойствам: `fields.disabled`, `status.textContent`, `caldavTab.hidden`, `sellerFields.disabled`, `sellerSave.disabled`, `document.getElementById('managerCalDAVAddress').textContent`, `document.getElementById('managerCalDAVHTTPSLink').href`, `document.getElementById('managerCalDAVHTTPS').hidden`, `document.getElementById('managerCalDAVControls').hidden`, `document.getElementById('managerSettingsAddress').textContent`, `document.getElementById('managerCurrentPasswordLabel').hidden`, `current.required`.

<a id="symbol-renderWeekHighlights"></a>

## renderWeekHighlights

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
function renderWeekHighlights(edit)
```

Строит страницу из недель того же размера и с той же легендой, что в списке заказов.

Перелистывание меняет видимые недели и сохраняет весь черновик.

Непосредственные вызовы: `Array.from({ length: edit.pageSize }, (_, index) => ({
      start: shiftDeadlineWeek(edit.firstWeek, index),
    })).filter`, `Array.from`, `document.getElementById`, `renderDeadlineMonthLegend`, `options.map(({ start }) => {
      const week = deadlineWeekInfo(start);
      const classes = 'deadline-week' + (start === edit.currentWeek ? ' current' : start < edit.currentWeek ? ' past' : '');
      return '<button type="button" data-highlight-week="' + start + '" data-base-class="' + classes +
        '" style="--deadline-month-hue:' + week.hue + '" title="' + week.label +
        '" aria-label="Неделя ' + week.number + ' · ' + week.label + '">' + week.number + '</button>';
    }).join`, `options.map`, `updateWeekHighlights`.

Прямые присваивания полям/свойствам: `document.getElementById('deadlineHighlightMonths').innerHTML`, `highlightWeeks.innerHTML`, `highlightWeeks.parentElement.scrollLeft`.

<a id="symbol-saveSeller"></a>

## saveSeller

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function saveSeller(event)
```

Сохраняет единые реквизиты по ожидаемой версии, не переписывая счета.

Ошибка оставляет поля; ни конфликт, ни потеря ответа не вызывают автоматического повтора.

Непосредственные вызовы: `event.preventDefault`, `Object.fromEntries`, `[...sellerFields.querySelectorAll('input')].map`, `sellerFields.querySelectorAll`, `fetch`, `JSON.stringify`, `response.json`, `Error`.

Прямые присваивания полям/свойствам: `sellerFields.disabled`, `sellerSave.disabled`, `close.disabled`, `sellerStatus.textContent`.

<a id="symbol-saveSettings"></a>

## saveSettings

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function saveSettings(event)
```

Отправляет одну явную смену пароля и очищает поля после подтверждения.

При ошибке соединения не повторяет запрос, поскольку пароль мог уже измениться.

Непосредственные вызовы: `event.preventDefault`, `confirmation.focus`, `AbortController`, `window.setTimeout`, `fetch`, `JSON.stringify`, `response.json`, `form.reset`, `window.clearTimeout`.

Прямые присваивания полям/свойствам: `status.textContent`, `fields.disabled`, `close.disabled`, `caldavPassword.value`, `caldavPassword.parentElement.hidden`, `caldavStatus.textContent`.

<a id="symbol-saveWeekHighlights"></a>

## saveWeekHighlights

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function saveWeekHighlights()
```

Сохраняет сразу все отмеченные недели по прочитанной версии.

При конфликте и потере ответа оставляет черновик видимым до загрузки текущих отметок.

Непосредственные вызовы: `updateWeekHighlights`, `fetch`, `JSON.stringify`, `[...edit.weeks].sort`, `response.json`, `Error`, `applyDeadlineHighlights`.

Прямые присваивания полям/свойствам: `edit.saving`, `close.disabled`, `highlightStatus.textContent`, `edit.revision`, `edit.saved`, `edit.blocked`.

<a id="symbol-selectSettingsTab"></a>

## selectSettingsTab

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
function selectSettingsTab(selected)
```

Показывает выбранный раздел настроек и обновляет доступность вкладок для клавиатуры.

Скрытые формы остаются в окне вместе с введёнными значениями и состоянием запросов.

Непосредственные вызовы: `tab.setAttribute`, `String`, `document.getElementById`, `tab.getAttribute`, `Set`, `loadWeekHighlights`.

Прямые присваивания полям/свойствам: `tab.tabIndex`, `document.getElementById(tab.getAttribute('aria-controls')).hidden`, `content.scrollTop`.

<a id="symbol-updateWeekHighlights"></a>

## updateWeekHighlights

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
function updateWeekHighlights(edit)
```

Обновляет выбор недель и доступность действий, сохраняя фокус внутри сетки.

Полоса отражает черновик, запись разрешена только после чтения версии.

Непосредственные вызовы: `deadlineHighlightClass`, `week.setAttribute`, `String`, `edit.weeks.has`, `shiftDeadlineWeek`, `edit.saved.every`, `Boolean`.

Прямые присваивания полям/свойствам: `week.className`, `week.disabled`, `highlightEarlier.disabled`, `highlightLater.disabled`, `highlightSave.disabled`, `highlightReload.hidden`, `highlightReload.disabled`.
