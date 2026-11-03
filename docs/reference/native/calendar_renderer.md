# calendar_renderer.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [calendar_renderer.swift:1](../../../calendar_renderer.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## fail

[calendar_renderer.swift:6](../../../calendar_renderer.swift#L6) · `func`.

```swift
func fail() -> Never
```

Завершает помощник с диагностикой в stderr и ненулевым кодом.

Вызывающий Python получает отказ вместо частичного успешного результата.

## CalendarRenderer

[calendar_renderer.swift:13](../../../calendar_renderer.swift#L13) · `class`.

```swift
final class CalendarRenderer: NSObject, WKNavigationDelegate, WKScriptMessageHandler
```

Рендерит автономный HTML календаря в отдельном WKWebView.

PNG возвращается через обработчик сообщения JavaScript в stdout процесса.

## init

[calendar_renderer.swift:17](../../../calendar_renderer.swift#L17) · `init`.

```swift
override init()
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

## webView

[calendar_renderer.swift:27](../../../calendar_renderer.swift#L27) · `func`.

```swift
func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

## webView

[calendar_renderer.swift:32](../../../calendar_renderer.swift#L32) · `func`.

```swift
func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

## webView

[calendar_renderer.swift:35](../../../calendar_renderer.swift#L35) · `func`.

```swift
func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

## webView

[calendar_renderer.swift:38](../../../calendar_renderer.swift#L38) · `func`.

```swift
func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void)
```

Обрабатывает событие навигации изолированного WKWebView.

Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.

## userContentController

[calendar_renderer.swift:43](../../../calendar_renderer.swift#L43) · `func`.

```swift
func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage)
```

Принимает PNG от JavaScript общего снимка календаря.

Проверяет base64 и предел 10 МБ; пишет байты в stdout и завершает процесс.
