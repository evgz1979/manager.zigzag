# static/calendar-telegram.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/calendar-telegram.js:1](../../../static/calendar-telegram.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## get

[static/calendar-telegram.js:5](../../../static/calendar-telegram.js#L5) · `ArrowFunctionExpression`.

```javascript
const get = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

## readSettings

[static/calendar-telegram.js:10](../../../static/calendar-telegram.js#L10) · `FunctionDeclaration`.

```javascript
async function readSettings()
```

Читает безопасное состояние подключения Telegram для интерфейса.

Использует `/api/calendar-telegram-settings`.

Непосредственные вызовы: `fetch`, `Error`, `response.json`.

## showSettings

[static/calendar-telegram.js:17](../../../static/calendar-telegram.js#L17) · `FunctionDeclaration`.

```javascript
function showSettings(current)
```

Показывает текущие параметры и ошибки настройки Telegram.

Использует `get`, `dialog.showModal`.

Непосредственные вызовы: `get`, `dialog.showModal`.

Прямые присваивания полям/свойствам: `connected.hidden`, `connected.textContent`.

## openSettings

[static/calendar-telegram.js:25](../../../static/calendar-telegram.js#L25) · `FunctionDeclaration`.

```javascript
async function openSettings()
```

Открывает окно настройки бота и личного чата.

Использует `showSettings`, `readSettings`, `notify`.

Непосредственные вызовы: `showSettings`, `readSettings`, `notify`.

## setSettingsBusy

[static/calendar-telegram.js:31](../../../static/calendar-telegram.js#L31) · `FunctionDeclaration`.

```javascript
function setSettingsBusy(value)
```

Блокирует действия формы на время текущего запроса.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `dialog.querySelectorAll`, `dialog.setAttribute`, `String`.

Прямые присваивания полям/свойствам: `control.disabled`.

## settingsRequest

[static/calendar-telegram.js:38](../../../static/calendar-telegram.js#L38) · `FunctionDeclaration`.

```javascript
async function settingsRequest(action)
```

Отправляет запрос серверу и преобразует HTTP-ошибку в исключение интерфейса.

Использует `/api/calendar-telegram-settings`.

Непосредственные вызовы: `fetch`, `JSON.stringify`, `get("calendarTelegramToken").value.trim`, `get`, `get("calendarTelegramChatId").value.trim`, `response.json`, `Error`.
