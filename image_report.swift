import Foundation
import CoreGraphics
import CoreText
import ImageIO

struct Item: Decodable {
    let path: String
    let comment: String
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count == 3,
      let data = try? Data(contentsOf: URL(fileURLWithPath: args[1])),
      let items = try? JSONDecoder().decode([Item].self, from: data), !items.isEmpty else {
    fail("Не удалось прочитать список изображений")
}
let width: CGFloat = 595.28, height: CGFloat = 841.89, margin: CGFloat = 36
var bounds = CGRect(x: 0, y: 0, width: width, height: height)
let output = URL(fileURLWithPath: args[2])
guard let context = CGContext(output as CFURL, mediaBox: &bounds, nil) else {
    fail("Не удалось создать PDF")
}
let font = CTFontCreateWithName("Helvetica" as CFString, 12, nil)
let attributes: [NSAttributedString.Key: Any] = [
    NSAttributedString.Key(kCTFontAttributeName as String): font,
    NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 0.12, alpha: 1)
]
var pages = 0
func beginPage() {
    context.beginPDFPage(nil)
    context.setFillColor(CGColor(gray: 1, alpha: 1))
    context.fill(bounds)
    context.textMatrix = .identity
    pages += 1
}

for item in items {
    autoreleasepool {
        guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: item.path) as CFURL, nil),
              let image = CGImageSourceCreateThumbnailAtIndex(source, 0, [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceThumbnailMaxPixelSize: 2400
              ] as CFDictionary) else {
            fail("Не удалось прочитать изображение: " + URL(fileURLWithPath: item.path).lastPathComponent)
        }
        let text = NSAttributedString(string: item.comment, attributes: attributes)
        let framesetter = CTFramesetterCreateWithAttributedString(text)
        let contentWidth = width - 2 * margin
        let hasText = !item.comment.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        let measured = hasText ? CTFramesetterSuggestFrameSizeWithConstraints(framesetter, CFRange(location: 0, length: 0), nil,
            CGSize(width: contentWidth, height: 10_000_000), nil).height + 8 : 0
        let reserved = min(measured, 180)
        let gap: CGFloat = hasText ? 16 : 0
        let imageHeight = height - 2 * margin - reserved - gap
        let scale = min(contentWidth / CGFloat(image.width), imageHeight / CGFloat(image.height))
        let imageSize = CGSize(width: CGFloat(image.width) * scale, height: CGFloat(image.height) * scale)
        let imageRect = CGRect(x: (width - imageSize.width) / 2, y: height - margin - imageSize.height,
                               width: imageSize.width, height: imageSize.height)
        beginPage()
        context.interpolationQuality = .high
        context.draw(image, in: imageRect)
        var offset = 0
        var textTop = imageRect.minY - gap
        while hasText && offset < text.length {
            let rect = CGRect(x: margin, y: margin, width: contentWidth, height: textTop - margin)
            let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: offset, length: 0), CGPath(rect: rect, transform: nil), nil)
            let count = CTFrameGetVisibleStringRange(frame).length
            guard count > 0 else { fail("Не удалось разместить комментарий в PDF") }
            CTFrameDraw(frame, context)
            offset += count
            if offset < text.length {
                context.endPDFPage()
                beginPage()
                textTop = height - margin
            }
        }
        context.endPDFPage()
    }
}
context.closePDF()
guard let document = CGPDFDocument(output as CFURL), document.numberOfPages == pages, pages > 0 else {
    fail("Не удалось проверить созданный PDF")
}
print("{\"pages\":\(pages)}")
