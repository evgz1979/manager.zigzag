# static/navigation.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/navigation.js](../../../static/navigation.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-setOpen"></a>

## setOpen

[static/navigation.js](../../../static/navigation.js) · `FunctionDeclaration`.

```javascript
function setOpen(value)
```

Открывает или закрывает узкое меню, управляя фокусом и блокировкой фона.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `sidebar.contains`, `workspace.classList.toggle`, `toggle.setAttribute`, `String`, `sidebar.removeAttribute`, `sidebar.setAttribute`, `close.focus`, `toggle.focus`, `document.getElementById("homeButton").focus`, `document.getElementById`, `document.dispatchEvent`, `Event`.

Прямые присваивания полям/свойствам: `header.inert`, `content.inert`, `sidebar.inert`.
