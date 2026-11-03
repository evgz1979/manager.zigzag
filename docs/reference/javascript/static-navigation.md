# static/navigation.js

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [static/navigation.js:1](../../../static/navigation.js#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## setOpen

[static/navigation.js:13](../../../static/navigation.js#L13) · `FunctionDeclaration`.

```javascript
function setOpen(value)
```

Открывает или закрывает узкое меню, управляя фокусом и блокировкой фона.

Обращается к DOM текущего документа или переданного контейнера.

Непосредственные вызовы: `sidebar.contains`, `workspace.classList.toggle`, `toggle.setAttribute`, `String`, `sidebar.removeAttribute`, `sidebar.setAttribute`, `close.focus`, `toggle.focus`, `document.getElementById("homeButton").focus`, `document.getElementById`.

Прямые присваивания полям/свойствам: `header.inert`, `content.inert`, `sidebar.inert`.
