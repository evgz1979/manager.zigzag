# calendar_delivery.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_delivery.py](../../../calendar_delivery.py).

JavaScript внутри автономного HTML-шаблона; контекст данных и запуск описаны у Python-владельца.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-makeCalendar"></a>

## makeCalendar

[calendar_delivery.py](../../../calendar_delivery.py) · `embedded JavaScript`.

```javascript
async function makeCalendar()
```

Строит общий PNG из переданного SQLite-снимка без пользовательской вкладки.

Сверяет период и передаёт base64 через единственный канал сообщений WebKit.
