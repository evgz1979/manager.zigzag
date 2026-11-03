# thumbnail_preview.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [thumbnail_preview.swift:1](../../../thumbnail_preview.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## fail

[thumbnail_preview.swift:9](../../../thumbnail_preview.swift#L9) · `func`.

```swift
func fail(_ message: String) -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

## jpeg

[thumbnail_preview.swift:16](../../../thumbnail_preview.swift#L16) · `func`.

```swift
func jpeg(_ image: CGImage, to output: URL) throws
```

Кодирует подготовленное изображение в JPEG-файл превью.

Ошибка ImageIO передаётся как throws и не подменяет исходный документ.
