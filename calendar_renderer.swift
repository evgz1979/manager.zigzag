import AppKit
import WebKit

// Завершает помощник с диагностикой в stderr и ненулевым кодом.
// Вызывающий Python получает отказ вместо частичного успешного результата.
func fail() -> Never {
    FileHandle.standardError.write(Data("Не удалось создать календарь\n".utf8))
    exit(1)
}

// Рендерит автономный HTML календаря в отдельном WKWebView.
// PNG возвращается через обработчик сообщения JavaScript в stdout процесса.
final class CalendarRenderer: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
    let view: WKWebView
    // Инициализирует зависимости и состояние экземпляра.
    // Конкретные параметры и правила загрузки определены в теле и полях типа.
    override init() {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        view = WKWebView(frame: NSRect(x: 0, y: 0, width: 1440, height: 1000), configuration: config)
        super.init()
        config.userContentController.add(self, name: "calendar")
        view.navigationDelegate = self
    }
    // Обрабатывает событие навигации изолированного WKWebView.
    // Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        webView.evaluateJavaScript("makeCalendar(); undefined") { _, error in if error != nil { fail() } }
    }
    // Обрабатывает событие навигации изолированного WKWebView.
    // Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { fail() }
    // Обрабатывает событие навигации изолированного WKWebView.
    // Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { fail() }
    // Обрабатывает событие навигации изолированного WKWebView.
    // Успех запускает makeCalendar, ошибка завершает процесс, посторонняя навигация запрещена.
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(navigationAction.request.url?.scheme == "about" ? .allow : .cancel)
    }
    // Принимает PNG от JavaScript общего снимка календаря.
    // Проверяет base64 и предел 10 МБ; пишет байты в stdout и завершает процесс.
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let value = message.body as? [String: Any], let image = value["image"] as? String,
              let data = Data(base64Encoded: image), data.count <= 10 * 1024 * 1024 else { fail() }
        FileHandle.standardOutput.write(data)
        exit(0)
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
let renderer = CalendarRenderer()
let input = FileHandle.standardInput.readDataToEndOfFile()
guard let html = String(data: input, encoding: .utf8) else { fail() }
renderer.view.loadHTMLString(html, baseURL: nil)
DispatchQueue.main.asyncAfter(deadline: .now() + 65) { fail() }
app.run()
