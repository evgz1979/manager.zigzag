import AppKit
import PDFKit
import Vision

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data(("ZIGZAG_PDF_ERROR: " + message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 3 else { fail("Не указан файл PDF") }
let url = URL(fileURLWithPath: args[1])
let manager = FileManager.default
var contents: Data?
do {
    let attributes = try manager.attributesOfItem(atPath: url.path)
    guard attributes[.type] as? FileAttributeType == .typeRegular else {
        fail("Для просмотра нужен обычный файл PDF")
    }
    if manager.isUbiquitousItem(at: url) {
        try manager.startDownloadingUbiquitousItem(at: url)
    }
    var coordinationError: NSError?
    var readError: Error?
    let coordinator = NSFileCoordinator(filePresenter: nil)
    coordinator.coordinate(readingItemAt: url, options: [], error: &coordinationError) { localURL in
        do {
            let file = try FileHandle(forReadingFrom: localURL)
            defer { try? file.close() }
            contents = try file.readToEnd() ?? Data()
        } catch { readError = error }
    }
    if let error = coordinationError { throw error }
    if let error = readError { throw error }
} catch {
    fail("Не удалось получить PDF из папки. iCloud может ещё загружать файл; попробуй открыть его повторно.")
}
// PDFKit must receive the bytes already read by Foundation. Opening the iCloud
// URL inside CoreGraphics can fail in the background service even for a valid PDF.
guard let data = contents, let document = PDFDocument(data: data) else {
    fail("Не удалось прочитать PDF")
}
if document.isLocked { fail("PDF защищён паролем. Откройте его на Mac.") }
if args[2] == "info" {
    print("{\"pages\":\(document.pageCount)}")
} else if args[2] == "invoice-text" {
    var texts: [String] = []
    let indexes = Set(Array(0..<min(document.pageCount, 20)) + Array(max(0, document.pageCount - 3)..<document.pageCount)).sorted()
    for index in indexes {
        guard let page = document.page(at: index) else { continue }
        let text = page.string ?? ""
        if text.trimmingCharacters(in: .whitespacesAndNewlines).count > 20 {
            texts.append(String(text.prefix(30000)))
        } else if index < 2 || index >= document.pageCount - 1 {
            let image = page.thumbnail(of: NSSize(width: 1800, height: 2400), for: .mediaBox)
            var rect = CGRect(origin: .zero, size: image.size)
            if let cgImage = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) {
                let request = VNRecognizeTextRequest()
                request.recognitionLevel = .accurate
                request.recognitionLanguages = ["ru-RU", "en-US"]
                request.usesLanguageCorrection = false
                try? VNImageRequestHandler(cgImage: cgImage).perform([request])
                texts.append((request.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n"))
            }
        }
    }
    print(String(texts.joined(separator: "\n").prefix(500000)))
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
