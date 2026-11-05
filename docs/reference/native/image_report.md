# image_report.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [image_report.swift](../../../image_report.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Item"></a>

## Item

[image_report.swift](../../../image_report.swift) · `struct`.

```swift
struct Item: Decodable
```

Описывает входное изображение PDF-отчёта и его комментарий.

Decodable разбирает поля из JSON, переданного процессу через stdin.

<a id="symbol-fail"></a>

## fail

[image_report.swift](../../../image_report.swift) · `func`.

```swift
func fail(_ message: String) -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

<a id="symbol-nextCell"></a>

## nextCell

[image_report.swift](../../../image_report.swift) · `func`.

```swift
func nextCell() -> CGRect
```

Выбирает следующую область изображения на странице PDF-отчёта.

При заполнении страницы начинает следующую и обновляет позицию сетки.

<a id="symbol-reportImage"></a>

## reportImage

[image_report.swift](../../../image_report.swift) · `func`.

```swift
func reportImage(_ path: String) -> CGImage
```

Читает изображение и подготавливает CGImage для PDF-отчёта.

Ошибка декодирования завершает помощник через fail.
