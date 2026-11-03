# calendar_delivery.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [calendar_delivery.py:1](../../../calendar_delivery.py#L1).

JavaScript внутри автономного HTML-шаблона; контекст данных и запуск описаны у Python-владельца.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## makeCalendar

[calendar_delivery.py:78](../../../calendar_delivery.py#L78) · `embedded JavaScript`.

```javascript
async function makeCalendar()
```

Строит общий PNG из переданного SQLite-снимка без пользовательской вкладки.

Сверяет период и передаёт base64 через единственный канал сообщений WebKit.
