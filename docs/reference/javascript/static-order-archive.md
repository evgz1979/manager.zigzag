# static/order-archive.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/order-archive.js](../../../static/order-archive.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-confirm"></a>

## confirm

[static/order-archive.js](../../../static/order-archive.js) · `FunctionDeclaration`.

```javascript
async function confirm()
```

Отправляет подтверждение один раз и сохраняет номер для чтения результата.

При неопределённом ответе продолжает только опрос.

Непосредственные вызовы: `remember`, `showProgress`, `request`, `AbortSignal.timeout`, `showFailure`, `monitor`.

<a id="symbol-monitor"></a>

## monitor

[static/order-archive.js](../../../static/order-archive.js) · `FunctionDeclaration`.

```javascript
async function monitor()
```

Опрашивает состояние принятого задания, не отправляя повторную запись.

После успешной проверки возвращает страницу к родительской папке.

Непосредственные вызовы: `request`, `apiUrl`, `AbortSignal.timeout`, `showFailure`, `showProgress`, `Promise`, `remember`, `dialog.close`, `new URLSearchParams(location.search).get`, `URLSearchParams`, `navigate`, `reloadClientTrees`, `loadOrders`, `notify`, `Boolean`.

Прямые присваивания полям/свойствам: `state.dirty`.

<a id="symbol-openConfirmation"></a>

## openConfirmation

[static/order-archive.js](../../../static/order-archive.js) · `FunctionDeclaration`.

```javascript
async function openConfirmation()
```

Показывает исходный путь и точный путь ZIP перед подтверждением.

Сохраняет заметку и проверяет, что за это время пользователь остался в заказе.

Непосредственные вызовы: `$`, `saveCurrentStatus`, `request`, `apiUrl`, `dialog.showModal`, `cancel.focus`.

Прямые присваивания полям/свойствам: `$("archiveOrderSource").textContent`, `$("archiveOrderDestination").textContent`, `status.hidden`, `failure.hidden`, `submit.disabled`, `submit.hidden`, `cancel.disabled`, `cancel.textContent`.

<a id="symbol-remember"></a>

## remember

[static/order-archive.js](../../../static/order-archive.js) · `FunctionDeclaration`.

```javascript
function remember(value)
```

Сохраняет номер принятой операции для повторного открытия вкладки.

При недоступном хранилище серверная работа продолжается.

Непосредственные вызовы: `JSON.parse`, `sessionStorage.getItem`, `sessionStorage.setItem`, `JSON.stringify`, `sessionStorage.removeItem`.

<a id="symbol-showFailure"></a>

## showFailure

[static/order-archive.js](../../../static/order-archive.js) · `FunctionDeclaration`.

```javascript
function showFailure(message)
```

Прекращает опрос и показывает ошибку рядом с исходным путём.

Новая попытка всегда открывает новое подтверждение.

Непосредственные вызовы: `remember`, `cancel.focus`.

Прямые присваивания полям/свойствам: `status.hidden`, `failure.hidden`, `failure.textContent`, `submit.hidden`, `cancel.disabled`, `cancel.textContent`.

<a id="symbol-showProgress"></a>

## showProgress

[static/order-archive.js](../../../static/order-archive.js) · `FunctionDeclaration`.

```javascript
function showProgress(message)
```

Показывает текущую фазу архивации или ошибку соединения.

Подтверждение блокируется до завершения уже принятого действия.

Прямые присваивания полям/свойствам: `status.hidden`, `status.textContent`, `failure.hidden`, `submit.disabled`, `cancel.disabled`.
