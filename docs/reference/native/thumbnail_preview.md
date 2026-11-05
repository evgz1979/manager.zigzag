# thumbnail_preview.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [thumbnail_preview.swift](../../../thumbnail_preview.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-fail"></a>

## fail

[thumbnail_preview.swift](../../../thumbnail_preview.swift) · `func`.

```swift
func fail(_ message: String) -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

<a id="symbol-jpeg"></a>

## jpeg

[thumbnail_preview.swift](../../../thumbnail_preview.swift) · `func`.

```swift
func jpeg(_ image: CGImage, to output: URL) throws
```

Кодирует подготовленное изображение в JPEG-файл превью.

Ошибка ImageIO передаётся как throws и не подменяет исходный документ.
