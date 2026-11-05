# static/settings.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/settings.js](../../../static/settings.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-openSettings"></a>

## openSettings

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function openSettings()
```

Открывает настройки без замены содержимого страницы или её черновиков.

Токен и режим смены пароля загружаются только при явном открытии окна.

Непосредственные вызовы: `form.reset`, `dialog.showModal`, `fetch`, `response.json`, `document.getElementById`, `(data.require_current_password ? current : password).focus`.

Прямые присваивания полям/свойствам: `fields.disabled`, `status.textContent`, `document.getElementById('managerSettingsAddress').textContent`, `document.getElementById('managerCurrentPasswordLabel').hidden`, `current.required`.

<a id="symbol-saveSettings"></a>

## saveSettings

[static/settings.js](../../../static/settings.js) · `FunctionDeclaration`.

```javascript
async function saveSettings(event)
```

Отправляет одну явную смену пароля и очищает поля после подтверждения.

При ошибке соединения не повторяет запрос, поскольку пароль мог уже измениться.

Непосредственные вызовы: `event.preventDefault`, `confirmation.focus`, `AbortController`, `window.setTimeout`, `fetch`, `JSON.stringify`, `response.json`, `form.reset`, `window.clearTimeout`.

Прямые присваивания полям/свойствам: `status.textContent`, `fields.disabled`, `close.disabled`.
