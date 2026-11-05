# static/mobile.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/mobile.js](../../../static/mobile.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-byId"></a>

## byId

[static/mobile.js](../../../static/mobile.js) · `ArrowFunctionExpression`.

```javascript
const byId = id =>
```

Находит элемент интерфейса по устойчивому DOM-идентификатору.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `document.getElementById`.

<a id="symbol-refresh"></a>

## refresh

[static/mobile.js](../../../static/mobile.js) · `FunctionDeclaration`.

```javascript
async function refresh()
```

Перечитывает данные открытого компонента по установленным правилам в модуле приостановленного обмена iPhone.

Использует `/api/mobile-status`.

Непосредственные вызовы: `fetch`, `response.json`, `Error`, `new Date(status.last_sync * 1000).toLocaleString`, `Date`, `byId`.

Прямые присваивания полям/свойствам: `byId('mobileStatus').textContent`, `byId('mobileEnable').hidden`, `byId('mobilePause').hidden`, `byId('mobileRefresh').disabled`.

<a id="symbol-update"></a>

## update

[static/mobile.js](../../../static/mobile.js) · `FunctionDeclaration`.

```javascript
async function update(payload)
```

Применяет подтверждённое частичное изменение к компоненту в модуле приостановленного обмена iPhone.

Использует `/api/mobile-sync`.

Непосредственные вызовы: `fetch`, `JSON.stringify`, `response.json`, `Error`, `refresh`, `byId`.

Прямые присваивания полям/свойствам: `byId('mobileStatus').textContent`.
