# image_report.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [image_report.swift:1](../../../image_report.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## Item

[image_report.swift:8](../../../image_report.swift#L8) · `struct`.

```swift
struct Item: Decodable
```

Описывает входное изображение PDF-отчёта и его комментарий.

Decodable разбирает поля из JSON, переданного процессу через stdin.

## fail

[image_report.swift:15](../../../image_report.swift#L15) · `func`.

```swift
func fail(_ message: String) -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

## nextCell

[image_report.swift:44](../../../image_report.swift#L44) · `func`.

```swift
func nextCell() -> CGRect
```

Выбирает следующую область изображения на странице PDF-отчёта.

При заполнении страницы начинает следующую и обновляет позицию сетки.

## reportImage

[image_report.swift:63](../../../image_report.swift#L63) · `func`.

```swift
func reportImage(_ path: String) -> CGImage
```

Читает изображение и подготавливает CGImage для PDF-отчёта.

Ошибка декодирования завершает помощник через fail.
