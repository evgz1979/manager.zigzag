# invoice_pdf.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [invoice_pdf.swift:1](../../../invoice_pdf.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## fail

[invoice_pdf.swift:7](../../../invoice_pdf.swift#L7) · `func`.

```swift
func fail(_ message: String) -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

## s

[invoice_pdf.swift:17](../../../invoice_pdf.swift#L17) · `func`.

```swift
func s(_ key: String) -> String
```

Извлекает строковое поле входного документа счёта.

Отсутствующее или нестроковое значение становится пустой строкой.

## money

[invoice_pdf.swift:20](../../../invoice_pdf.swift#L20) · `func`.

```swift
func money(_ cents: Int) -> String
```

Форматирует денежное значение для PDF или карточки телефона.

Использует сохранённое числовое значение; расчёты базы этим не изменяются.

## date

[invoice_pdf.swift:28](../../../invoice_pdf.swift#L28) · `func`.

```swift
func date(_ value: String) -> String
```

Переставляет компоненты даты счёта для печатного отображения.

Использует формат входной строки с разделителем дефис.

## Text

[invoice_pdf.swift:33](../../../invoice_pdf.swift#L33) · `struct`.

```swift
struct Text
```

Хранит измеренную текстовую область для последующей отрисовки PDF.

Координаты, размер и атрибуты определяются во время предварительной раскладки.

## Rule

[invoice_pdf.swift:39](../../../invoice_pdf.swift#L39) · `struct`.

```swift
struct Rule
```

Хранит параметры линии или затенённой полосы PDF счёта.

Отрисовывается после расчёта итоговой высоты документа.

## attributed

[invoice_pdf.swift:44](../../../invoice_pdf.swift#L44) · `func`.

```swift
func attributed(_ text: String, _ size: CGFloat, _ bold: Bool, _ right: Bool) -> NSAttributedString
```

Строит атрибутированный текст с нужным шрифтом и выравниванием.

Возвращает NSAttributedString для измерения и отрисовки PDF.

## text

[invoice_pdf.swift:53](../../../invoice_pdf.swift#L53) · `func`.

```swift
func text(_ value: String, _ x: CGFloat, _ top: CGFloat, _ width: CGFloat, _ size: CGFloat? = nil, bold: Bool = false, right: Bool = false) -> CGFloat
```

Измеряет текст и добавляет область в план PDF-документа.

При отрисовке используется ранее вычисленная геометрия и выбранный шрифт.

## rule

[invoice_pdf.swift:65](../../../invoice_pdf.swift#L65) · `func`.

```swift
func rule(_ top: CGFloat)
```

Добавляет горизонтальную линию в план PDF-документа.

Геометрия использует текущие поля страницы и ширину содержимого.

## layout

[invoice_pdf.swift:68](../../../invoice_pdf.swift#L68) · `func`.

```swift
func layout(_ font: CGFloat)
```

Рассчитывает размещение реквизитов, позиций и итогов PDF.

Обновляет накопленные области текста и линий для выбранного размера шрифта.
