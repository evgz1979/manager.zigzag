# static/settings.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/settings.js:1](../../../static/settings.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## openSettings

[static/settings.js:16](../../../static/settings.js#L16) · `FunctionDeclaration`.

```javascript
async function openSettings()
```

Открывает настройки без замены содержимого страницы или её черновиков.

Токен и режим смены пароля загружаются только при явном открытии окна.

Непосредственные вызовы: `form.reset`, `dialog.showModal`, `fetch`, `response.json`, `document.getElementById`, `(data.require_current_password ? current : password).focus`.

Прямые присваивания полям/свойствам: `fields.disabled`, `status.textContent`, `document.getElementById('managerSettingsAddress').textContent`, `document.getElementById('managerCurrentPasswordLabel').hidden`, `current.required`.

## saveSettings

[static/settings.js:37](../../../static/settings.js#L37) · `FunctionDeclaration`.

```javascript
async function saveSettings(event)
```

Отправляет одну явную смену пароля и очищает поля после подтверждения.

При ошибке соединения не повторяет запрос, поскольку пароль мог уже измениться.

Непосредственные вызовы: `event.preventDefault`, `confirmation.focus`, `AbortController`, `window.setTimeout`, `fetch`, `JSON.stringify`, `response.json`, `form.reset`, `window.clearTimeout`.

Прямые присваивания полям/свойствам: `status.textContent`, `fields.disabled`, `close.disabled`.
