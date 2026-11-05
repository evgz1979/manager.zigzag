# static/calendar-telegram.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/calendar-telegram.js](../../../static/calendar-telegram.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-get"></a>

## get

[static/calendar-telegram.js](../../../static/calendar-telegram.js) · `ArrowFunctionExpression`.

```javascript
const get = (id) =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

<a id="symbol-openSettings"></a>

## openSettings

[static/calendar-telegram.js](../../../static/calendar-telegram.js) · `FunctionDeclaration`.

```javascript
async function openSettings()
```

Открывает окно настройки бота и личного чата.

Использует `showSettings`, `readSettings`, `notify`.

Непосредственные вызовы: `showSettings`, `readSettings`, `notify`.

<a id="symbol-readSettings"></a>

## readSettings

[static/calendar-telegram.js](../../../static/calendar-telegram.js) · `FunctionDeclaration`.

```javascript
async function readSettings()
```

Читает безопасное состояние подключения Telegram для интерфейса.

Использует `/api/calendar-telegram-settings`.

Непосредственные вызовы: `fetch`, `Error`, `response.json`.

<a id="symbol-setSettingsBusy"></a>

## setSettingsBusy

[static/calendar-telegram.js](../../../static/calendar-telegram.js) · `FunctionDeclaration`.

```javascript
function setSettingsBusy(value)
```

Блокирует действия формы на время текущего запроса.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `dialog.querySelectorAll`, `dialog.setAttribute`, `String`.

Прямые присваивания полям/свойствам: `control.disabled`.

<a id="symbol-settingsRequest"></a>

## settingsRequest

[static/calendar-telegram.js](../../../static/calendar-telegram.js) · `FunctionDeclaration`.

```javascript
async function settingsRequest(action)
```

Отправляет запрос серверу и преобразует HTTP-ошибку в исключение интерфейса.

Использует `/api/calendar-telegram-settings`.

Непосредственные вызовы: `fetch`, `JSON.stringify`, `get("calendarTelegramToken").value.trim`, `get`, `get("calendarTelegramChatId").value.trim`, `response.json`, `Error`.

<a id="symbol-showSettings"></a>

## showSettings

[static/calendar-telegram.js](../../../static/calendar-telegram.js) · `FunctionDeclaration`.

```javascript
function showSettings(current)
```

Показывает текущие параметры и ошибки настройки Telegram.

Использует `get`, `dialog.showModal`.

Непосредственные вызовы: `get`, `dialog.showModal`.

Прямые присваивания полям/свойствам: `connected.hidden`, `connected.textContent`.
