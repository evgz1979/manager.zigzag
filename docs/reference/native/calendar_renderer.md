# calendar_renderer.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_renderer.swift](../../../calendar_renderer.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-CalendarRenderer"></a>

## CalendarRenderer

[calendar_renderer.swift](../../../calendar_renderer.swift) · `class`.

```swift
final class CalendarRenderer: NSObject, WKNavigationDelegate, WKScriptMessageHandler
```

Рендерит автономный HTML календаря в отдельном WKWebView.

PNG возвращается через обработчик сообщения JavaScript в stdout процесса.

<a id="symbol-CalendarRenderer.init"></a>

## CalendarRenderer.init

[calendar_renderer.swift](../../../calendar_renderer.swift) · `init`.

```swift
override init()
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

<a id="symbol-CalendarRenderer.userContentController"></a>

## CalendarRenderer.userContentController

[calendar_renderer.swift](../../../calendar_renderer.swift) · `func`.

```swift
func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage)
```

Принимает PNG от JavaScript общего снимка календаря.

Проверяет base64 и предел 10 МБ; пишет байты в stdout и завершает процесс.

<a id="symbol-CalendarRenderer.webView-13857fa54331"></a>

## CalendarRenderer.webView

[calendar_renderer.swift](../../../calendar_renderer.swift) · `func`.

```swift
func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

<a id="symbol-CalendarRenderer.webView-6f4b18b5c611"></a>

## CalendarRenderer.webView

[calendar_renderer.swift](../../../calendar_renderer.swift) · `func`.

```swift
func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

<a id="symbol-CalendarRenderer.webView-8f1111111d9a"></a>

## CalendarRenderer.webView

[calendar_renderer.swift](../../../calendar_renderer.swift) · `func`.

```swift
func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

<a id="symbol-CalendarRenderer.webView-f57af9318001"></a>

## CalendarRenderer.webView

[calendar_renderer.swift](../../../calendar_renderer.swift) · `func`.

```swift
func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

<a id="symbol-fail"></a>

## fail

[calendar_renderer.swift](../../../calendar_renderer.swift) · `func`.

```swift
func fail() -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.
