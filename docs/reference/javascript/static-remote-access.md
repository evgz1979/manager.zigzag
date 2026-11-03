# static/remote-access.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/remote-access.js:1](../../../static/remote-access.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## loginUrl

[static/remote-access.js:7](../../../static/remote-access.js#L7) · `ArrowFunctionExpression`.

```javascript
const loginUrl = () =>
```

Строит безопасный адрес входа с возвратом к текущей странице.

Использует `encodeURIComponent`.

Непосредственные вызовы: `encodeURIComponent`.

## requireLogin

[static/remote-access.js:10](../../../static/remote-access.js#L10) · `FunctionDeclaration`.

```javascript
function requireLogin()
```

Показывает необходимость входа в отдельной вкладке, сохраняя текущую форму.

Использует `document.createElement`, `notice.setAttribute`, `notice.append`.

Непосредственные вызовы: `document.createElement`, `notice.setAttribute`, `notice.append`, `loginUrl`, `document.body.append`.

Прямые присваивания полям/свойствам: `notice.style.cssText`, `link.href`, `link.target`, `link.rel`, `link.textContent`.
