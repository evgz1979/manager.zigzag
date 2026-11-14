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

<a id="symbol-openSettings"></a>

## openSettings

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function openSettings()
```

Открывает настройки без замены содержимого страницы или её черновиков.

Токен и режим смены пароля загружаются только при явном открытии окна.

Непосредственные вызовы: `form.reset`, `dialog.showModal`, `loadSeller`, `fetch`, `response.json`, `document.getElementById`.

Прямые присваивания полям/свойствам: `fields.disabled`, `status.textContent`, `caldavPanel.hidden`, `sellerFields.disabled`, `sellerSave.disabled`, `document.getElementById('managerCalDAVAddress').textContent`, `document.getElementById('managerCalDAVHTTPSLink').href`, `document.getElementById('managerCalDAVHTTPS').hidden`, `document.getElementById('managerCalDAVControls').hidden`, `document.getElementById('managerSettingsAddress').textContent`, `document.getElementById('managerCurrentPasswordLabel').hidden`, `current.required`.

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
