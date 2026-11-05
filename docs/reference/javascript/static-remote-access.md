# static/remote-access.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/remote-access.js](../../../static/remote-access.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-loginUrl"></a>

## loginUrl

[static/remote-access.js](../../../static/remote-access.js) · `ArrowFunctionExpression`.

```javascript
const loginUrl = () =>
```

Строит безопасный адрес входа с возвратом к текущей странице.

Использует `encodeURIComponent`.

Непосредственные вызовы: `encodeURIComponent`.

<a id="symbol-requireLogin"></a>

## requireLogin

[static/remote-access.js](../../../static/remote-access.js) · `FunctionDeclaration`.

```javascript
function requireLogin()
```

Показывает необходимость входа в отдельной вкладке, сохраняя текущую форму.

Использует `document.createElement`, `notice.setAttribute`, `notice.append`.

Непосредственные вызовы: `document.createElement`, `notice.setAttribute`, `notice.append`, `loginUrl`, `document.body.append`.

Прямые присваивания полям/свойствам: `notice.style.cssText`, `link.href`, `link.target`, `link.rel`, `link.textContent`.
