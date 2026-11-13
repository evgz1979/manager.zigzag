# static/object-move.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/object-move.js](../../../static/object-move.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-close"></a>

## close

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
function close()
```

Закрывает окно и оставляет доступ к прогрессу, если перенос идёт.

При подтверждённом завершении результат можно открыть по отдельной кнопке.

Непосредственные вызовы: `dialog.close`, `storedJob`.

Прямые присваивания полям/свойствам: `launcher.hidden`.

<a id="symbol-monitor"></a>

## monitor

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
async function monitor(job)
```

Получает прогресс с M4, пока операция не завершится или сервер не вернёт отсутствие задания.

При потере сети повторяет только чтение статуса, сохраняя последнее известное состояние.

Непосредственные вызовы: `Object.assign`, `request`, `apiUrl`, `AbortSignal.timeout`, `renderProgress`, `Promise`.

Прямые присваивания полям/свойствам: `job.unconfirmed`.

<a id="symbol-openForm"></a>

## openForm

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
async function openForm()
```

Открывает подтверждение для объекта, который всё ещё открыт после загрузки формы.

Сохраняет заметку и запрашивает только версию папки и каталог клиентов.

Непосредственные вызовы: `dialog.showModal`, `saveCurrentStatus`, `request`, `apiUrl`, `$`, `client.replaceChildren`, `Option`, `view.clients.map`, `showDestination`, `client.focus`.

Прямые присваивания полям/свойствам: `$("moveObjectSource").textContent`, `$("moveObjectError").hidden`, `$("moveObjectError").textContent`, `form.hidden`, `$("moveObjectProgress").hidden`.

<a id="symbol-renderProgress"></a>

## renderProgress

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
function renderProgress(job, connectionError = "")
```

Показывает актуальную фазу, число файлов, прочитанные байты и текущий путь.

Показывает неопределённый прогресс там, где долю работы ещё нельзя измерить.

Непосредственные вызовы: `$`, `meter.removeAttribute`, `Number.isInteger`, `formatSize`.

Прямые присваивания полям/свойствам: `form.hidden`, `$("moveObjectProgress").hidden`, `$("moveObjectSource").textContent`, `phase.textContent`, `meter.hidden`, `meter.max`, `meter.value`, `$("moveObjectCounts").textContent`, `$("moveObjectCurrent").hidden`, `$("moveObjectCurrent").textContent`, `$("moveObjectProgressError").hidden`, `$("moveObjectProgressError").textContent`, `$("closeMoveObject").textContent`, `$("openMovedObject").hidden`, `launcher.textContent`, `launcher.hidden`.

<a id="symbol-showDestination"></a>

## showDestination

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
function showDestination()
```

Обновляет точный путь назначения перед подтверждением.

Использует полные пути клиента, включая его числовую группу.

Непосредственные вызовы: `$`.

Прямые присваивания полям/свойствам: `destination.hidden`, `destination.textContent`, `$("submitMoveObject").disabled`.

<a id="symbol-storedJob"></a>

## storedJob

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
function storedJob(value)
```

Читает или сохраняет номер операции в текущей вкладке.

Прогресс на сервере продолжается даже без доступа к sessionStorage.

Непосредственные вызовы: `JSON.parse`, `sessionStorage.getItem`, `sessionStorage.removeItem`, `sessionStorage.setItem`, `JSON.stringify`.

<a id="symbol-submit"></a>

## submit

[static/object-move.js](../../../static/object-move.js) · `FunctionDeclaration`.

```javascript
async function submit()
```

Отправляет одно подтверждение и начинает опрос под тем же идентификатором.

При неопределённом сетевом ответе не отправляет перенос повторно.

Непосредственные вызовы: `proposal?.clients.find`, `Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, "0")).join`, `Array.from`, `crypto.getRandomValues`, `Uint8Array`, `storedJob`, `renderProgress`, `fetch`, `JSON.stringify`, `AbortSignal.timeout`, `response.json`, `Object.assign`, `Error`, `monitor`.

Прямые присваивания полям/свойствам: `job.unconfirmed`.
