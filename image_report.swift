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
let width: CGFloat = 595.28, height: CGFloat = 841.89, margin: CGFloat = 28, gutter: CGFloat = 20
let cellWidth = (width - 2 * margin - gutter) / 2
let cellHeight = (height - 2 * margin - gutter) / 2
let imageBoxHeight: CGFloat = 260
var bounds = CGRect(x: 0, y: 0, width: width, height: height)
let output = URL(fileURLWithPath: args[2])
guard let context = CGContext(output as CFURL, mediaBox: &bounds, nil) else {
    fail("Не удалось создать PDF")
}
let font = CTFontCreateWithName("Helvetica" as CFString, 11, nil)
let attributes: [NSAttributedString.Key: Any] = [
    NSAttributedString.Key(kCTFontAttributeName as String): font,
    NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 0.12, alpha: 1)
]
var pages = 0
var slot = 4
func nextCell() -> CGRect {
    if slot == 4 {
        if pages > 0 { context.endPDFPage() }
        context.beginPDFPage(nil)
        context.setFillColor(CGColor(gray: 1, alpha: 1))
        context.fill(bounds)
        context.textMatrix = .identity
        pages += 1
        slot = 0
    }
    let column = slot % 2, row = slot / 2
    slot += 1
    return CGRect(x: margin + CGFloat(column) * (cellWidth + gutter),
                  y: height - margin - CGFloat(row) * (cellHeight + gutter) - cellHeight,
                  width: cellWidth, height: cellHeight)
}

func reportImage(_ path: String) -> CGImage {
    guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: 1200
          ] as CFDictionary),
          let bitmap = CGContext(data: nil, width: thumbnail.width, height: thumbnail.height,
            bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue) else {
        fail("Не удалось прочитать изображение: " + URL(fileURLWithPath: path).lastPathComponent)
    }
    let rect = CGRect(x: 0, y: 0, width: thumbnail.width, height: thumbnail.height)
    bitmap.setFillColor(CGColor(gray: 1, alpha: 1))
    bitmap.fill(rect)
    bitmap.draw(thumbnail, in: rect)
    let data = NSMutableData()
    guard let rgb = bitmap.makeImage(),
          let destination = CGImageDestinationCreateWithData(data, "public.jpeg" as CFString, 1, nil) else {
        fail("Не удалось подготовить изображение для PDF")
    }
    CGImageDestinationAddImage(destination, rgb, [kCGImageDestinationLossyCompressionQuality: 0.72] as CFDictionary)
    guard CGImageDestinationFinalize(destination),
          let provider = CGDataProvider(data: data),
          let jpeg = CGImage(jpegDataProviderSource: provider, decode: nil, shouldInterpolate: true, intent: .defaultIntent) else {
        fail("Не удалось сжать изображение для PDF")
    }
    return jpeg
}

for item in items {
    autoreleasepool {
        let image = reportImage(item.path)
        let text = NSAttributedString(string: item.comment, attributes: attributes)
        let framesetter = CTFramesetterCreateWithAttributedString(text)
        let hasText = !item.comment.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        var cell = nextCell()
        let scale = min(cell.width / CGFloat(image.width), imageBoxHeight / CGFloat(image.height))
        let imageSize = CGSize(width: CGFloat(image.width) * scale, height: CGFloat(image.height) * scale)
        let imageRect = CGRect(x: cell.midX - imageSize.width / 2, y: cell.maxY - imageBoxHeight / 2 - imageSize.height / 2,
                               width: imageSize.width, height: imageSize.height)
        context.interpolationQuality = .high
        context.draw(image, in: imageRect)
        var offset = 0
        var textTop = cell.maxY - imageBoxHeight - 12
        while hasText && offset < text.length {
            let rect = CGRect(x: cell.minX, y: cell.minY, width: cell.width, height: textTop - cell.minY)
            let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: offset, length: 0), CGPath(rect: rect, transform: nil), nil)
            let count = CTFrameGetVisibleStringRange(frame).length
            guard count > 0 else { fail("Не удалось разместить комментарий в PDF") }
            CTFrameDraw(frame, context)
            offset += count
            if offset < text.length {
                cell = nextCell()
                textTop = cell.maxY
            }
        }
    }
}
if pages > 0 { context.endPDFPage() }
context.closePDF()
guard let document = CGPDFDocument(output as CFURL), document.numberOfPages == pages, pages > 0 else {
    fail("Не удалось проверить созданный PDF")
}
print("{\"pages\":\(pages)}")
