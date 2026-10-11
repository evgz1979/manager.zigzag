import AppKit
import PDFKit

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 3, let document = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
    fail("Не удалось прочитать PDF")
}
if document.isLocked { fail("PDF защищён паролем. Откройте его на Mac.") }
if args[2] == "info" {
    print("{\"pages\":\(document.pageCount)}")
} else {
    guard args.count == 4, let index = Int(args[2]), let page = document.page(at: index) else {
        fail("Страница не найдена")
    }
    let bounds = page.bounds(for: .cropBox)
    guard bounds.width > 0, bounds.height > 0 else { fail("Некорректный размер страницы") }
    let scale = min(1600 / bounds.width, 2400 / bounds.height)
    let image = page.thumbnail(of: NSSize(width: bounds.width * scale, height: bounds.height * scale), for: .cropBox)
    guard let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let jpeg = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.9]) else {
        fail("Не удалось показать страницу")
    }
    do {
        try jpeg.write(to: URL(fileURLWithPath: args[3]), options: .atomic)
    } catch {
        fail("Не удалось сохранить просмотр страницы")
    }
}
