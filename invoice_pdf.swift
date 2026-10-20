import AppKit
import CoreText
import PDFKit

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8)); exit(1)
}
let args = CommandLine.arguments
guard args.count == 3, let bytes = try? Data(contentsOf: URL(fileURLWithPath: args[1])),
      let data = (try? JSONSerialization.jsonObject(with: bytes)) as? [String: Any],
      let seller = data["seller"] as? [String: String], let items = data["items"] as? [[String: Any]],
      let total = data["total"] as? Int else { fail("Не удалось прочитать счёт") }
func s(_ key: String) -> String { data[key] as? String ?? "" }
func money(_ cents: Int) -> String {
    let formatter = NumberFormatter(); formatter.numberStyle = .decimal
    formatter.groupingSeparator = " "; formatter.decimalSeparator = ","
    formatter.minimumFractionDigits = 2; formatter.maximumFractionDigits = 2
    return formatter.string(from: NSDecimalNumber(value: cents).dividing(by: 100)) ?? ""
}
func date(_ value: String) -> String { value.split(separator: "-").reversed().joined(separator: ".") }
let contract = s("kind") == "contract"
let pageW: CGFloat = 595.28, pageH: CGFloat = 841.89, margin: CGFloat = 30, contentW: CGFloat = 535.28
struct Text {
    let string: NSAttributedString
    let x: CGFloat, top: CGFloat, width: CGFloat, height: CGFloat
}
struct Rule { let x: CGFloat, top: CGFloat, width: CGFloat, shade: Bool }
var texts: [Text] = [], rules: [Rule] = [], bottom: CGFloat = 0
var base: CGFloat = 10
func attributed(_ text: String, _ size: CGFloat, _ bold: Bool, _ right: Bool) -> NSAttributedString {
    let p = NSMutableParagraphStyle(); p.alignment = right ? .right : .left
    p.lineBreakMode = .byWordWrapping; p.lineSpacing = 1.8
    return NSAttributedString(string: text, attributes: [.font: bold ? NSFont.boldSystemFont(ofSize: size) : NSFont.systemFont(ofSize: size),
            .foregroundColor: NSColor.black, .paragraphStyle: p])
}
@discardableResult
func text(_ value: String, _ x: CGFloat, _ top: CGFloat, _ width: CGFloat,
          _ size: CGFloat? = nil, bold: Bool = false, right: Bool = false) -> CGFloat {
    if value.isEmpty { return 0 }
    let a = attributed(value, size ?? base, bold, right)
    let frame = CTFramesetterCreateWithAttributedString(a)
    let h = ceil(CTFramesetterSuggestFrameSizeWithConstraints(frame, CFRange(location: 0, length: a.length), nil,
                    CGSize(width: width, height: 10000), nil).height) + 2
    texts.append(Text(string: a, x: x, top: top, width: width, height: h))
    return h
}
func rule(_ top: CGFloat) { rules.append(Rule(x: margin, top: top, width: contentW, shade: false)) }
func layout(_ font: CGFloat) {
    base = font; texts = []; rules = []
    var y = margin
    let title = (contract ? "Счёт-договор" : "Счёт на оплату") + " № " + s("number")
    y += text(title, margin, y, contentW, 17, bold: true) + 2
    let subtitle = "от " + date(s("date")) + (s("due_date").isEmpty ? "" : "   ·   Оплатить до " + date(s("due_date")))
    y += text(subtitle, margin, y, contentW, base) + 9
    rule(y); y += 9
    y += text("Исполнитель: " + (seller["name"] ?? ""), margin, y, contentW, bold: true) + 2
    var details = "ИНН " + (seller["inn"] ?? "")
    if !(seller["kpp"] ?? "").isEmpty { details += " · КПП " + seller["kpp"]! }
    if !(seller["address"] ?? "").isEmpty { details += " · " + seller["address"]! }
    y += text(details, margin, y, contentW, base - 0.3) + 4
    y += text((seller["bank"] ?? "") + " · БИК " + (seller["bik"] ?? ""), margin, y, contentW, base - 0.3) + 1
    y += text("Р/с " + (seller["account"] ?? "") + " · К/с " + (seller["correspondent"] ?? ""), margin, y, contentW, base - 0.3) + 10
    y += text("Покупатель: " + s("buyer_name"), margin, y, contentW, bold: true) + 2
    let buyer = [(s("buyer_inn").isEmpty ? "" : "ИНН " + s("buyer_inn")),
                 (s("buyer_kpp").isEmpty ? "" : "КПП " + s("buyer_kpp")), s("buyer_address")].filter { !$0.isEmpty }.joined(separator: " · ")
    y += text(buyer, margin, y, contentW, base - 0.3) + (buyer.isEmpty ? 7 : 10)
    let widths: [CGFloat] = [24, 260.28, 43, 38, 80, 90]
    let headers = ["№", "Товары, работы, услуги", "Кол-во", "Ед.", "Цена, ₽", "Сумма, ₽"]
    var x = margin
    rules.append(Rule(x: margin, top: y, width: contentW, shade: true))
    for i in 0..<6 {
        text(headers[i], x + 4, y + 5, widths[i] - 8, base - 1, bold: true, right: i >= 2)
        x += widths[i]
    }
    y += 24; rule(y)
    for (index, item) in items.enumerated() {
        let qty = (item["quantity"] as? String ?? "").replacingOccurrences(of: ".", with: ",")
        let price = NSDecimalNumber(string: item["price"] as? String ?? "0").multiplying(by: 100).intValue
        let values = [String(index + 1), item["name"] as? String ?? "", qty, item["unit"] as? String ?? "", money(price), money(item["amount"] as? Int ?? 0)]
        x = margin; var rowH: CGFloat = 21
        for i in 0..<6 {
            let h = text(values[i], x + 4, y + 5, widths[i] - 8, base - 0.3, right: i >= 2)
            rowH = max(rowH, h + 10); x += widths[i]
        }
        y += rowH; rule(y)
    }
    y += 10
    let totalHeight = text("Итого к оплате: " + money(total) + " ₽", margin, y, contentW, 13, bold: true, right: true)
    text("Позиций: " + String(items.count) + " · Без НДС", margin, y + 2, 180, base - 0.3)
    y += totalHeight + 10
    if !s("note").isEmpty { y += text(s("note"), margin, y, contentW) + 9 }
    if contract {
        y += text("Условия договора", margin, y, contentW, base, bold: true) + 4
        y += text("Начало работ: " + date(s("work_start")) + ". Окончание работ: " + date(s("work_end")) + ".", margin, y, contentW, base - 0.3) + 4
        y += text(s("terms"), margin, y, contentW, base - 0.3) + 13
    } else { y += 5 }
    y += text("Исполнитель: __________________  " + (seller["signer"] ?? ""), margin, y, contentW, base) + 4
    if contract { y += text("Заказчик: __________________", margin, y + 6, contentW, base) + 6 }
    if data["preview"] as? Bool == true { y += text("ПРЕДПРОСМОТР · ЧЕРНОВИК", margin, y + 8, contentW, 9, bold: true) + 8 }
    bottom = y
}
for size: CGFloat in [10, 9.5, 9, 8.5] {
    layout(size)
    if bottom <= pageH - margin { break }
}
guard bottom <= pageH - margin else {
    fail("Содержимое не помещается на одну страницу. Сократи позиции, реквизиты или условия; черновик сохранён.")
}
var bounds = CGRect(x: 0, y: 0, width: pageW, height: pageH)
let output = URL(fileURLWithPath: args[2])
guard let ctx = CGContext(output as CFURL, mediaBox: &bounds, nil) else { fail("Не удалось создать PDF") }
ctx.beginPDFPage(nil); ctx.textMatrix = .identity
ctx.setFillColor(CGColor(gray: 1, alpha: 1)); ctx.fill(bounds)
for r in rules {
    if r.shade {
        ctx.setFillColor(CGColor(gray: 0.94, alpha: 1))
        ctx.fill(CGRect(x: r.x, y: pageH - r.top - 24, width: r.width, height: 24))
    } else {
        ctx.setStrokeColor(CGColor(gray: 0.75, alpha: 1)); ctx.setLineWidth(0.4)
        ctx.move(to: CGPoint(x: r.x, y: pageH - r.top)); ctx.addLine(to: CGPoint(x: r.x + r.width, y: pageH - r.top)); ctx.strokePath()
    }
}
for t in texts {
    let framesetter = CTFramesetterCreateWithAttributedString(t.string)
    let rect = CGRect(x: t.x, y: pageH - t.top - t.height, width: t.width, height: t.height)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: t.string.length), CGPath(rect: rect, transform: nil), nil)
    guard CTFrameGetVisibleStringRange(frame).length == t.string.length else { fail("Текст не поместился в PDF") }
    CTFrameDraw(frame, ctx)
}
ctx.endPDFPage(); ctx.closePDF()
guard let pdf = PDFDocument(url: output), pdf.pageCount == 1 else { fail("Не удалось проверить одностраничный PDF") }
print("{\"pages\":1}")
