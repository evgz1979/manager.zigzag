# invoice_pdf.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [invoice_pdf.swift](../../../invoice_pdf.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Rule"></a>

## Rule

[invoice_pdf.swift](../../../invoice_pdf.swift) · `struct`.

```swift
struct Rule
```

Хранит параметры линии или затенённой полосы PDF счёта.

Отрисовывается после расчёта итоговой высоты документа.

<a id="symbol-Text"></a>

## Text

[invoice_pdf.swift](../../../invoice_pdf.swift) · `struct`.

```swift
struct Text
```

Хранит измеренную текстовую область для последующей отрисовки PDF.

Координаты, размер и атрибуты определяются во время предварительной раскладки.

<a id="symbol-attributed"></a>

## attributed

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func attributed(_ text: String, _ size: CGFloat, _ bold: Bool, _ right: Bool) -> NSAttributedString
```

Строит атрибутированный текст с нужным шрифтом и выравниванием.

Возвращает NSAttributedString для измерения и отрисовки PDF.

<a id="symbol-date"></a>

## date

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func date(_ value: String) -> String
```

Переставляет компоненты даты счёта для печатного отображения.

Использует формат входной строки с разделителем дефис.

<a id="symbol-fail"></a>

## fail

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func fail(_ message: String) -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

<a id="symbol-layout"></a>

## layout

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func layout(_ font: CGFloat)
```

Рассчитывает размещение реквизитов, позиций и итогов PDF.

Обновляет накопленные области текста и линий для выбранного размера шрифта.

<a id="symbol-money"></a>

## money

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func money(_ cents: Int) -> String
```

Форматирует денежное значение для PDF или карточки телефона.

Использует сохранённое числовое значение; расчёты базы этим не изменяются.

<a id="symbol-rule"></a>

## rule

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func rule(_ top: CGFloat)
```

Добавляет горизонтальную линию в план PDF-документа.

Геометрия использует текущие поля страницы и ширину содержимого.

<a id="symbol-s"></a>

## s

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func s(_ key: String) -> String
```

Извлекает строковое поле входного документа счёта.

Отсутствующее или нестроковое значение становится пустой строкой.

<a id="symbol-text"></a>

## text

[invoice_pdf.swift](../../../invoice_pdf.swift) · `func`.

```swift
func text(_ value: String, _ x: CGFloat, _ top: CGFloat, _ width: CGFloat, _ size: CGFloat? = nil, bold: Bool = false, right: Bool = false) -> CGFloat
```

Измеряет текст и добавляет область в план PDF-документа.

При отрисовке используется ранее вычисленная геометрия и выбранный шрифт.
