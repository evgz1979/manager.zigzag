import AppKit
import AVFoundation
import ImageIO
import PDFKit
import QuickLookThumbnailing

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data(("ZIGZAG_THUMBNAIL_ERROR: " + message + "\n").utf8))
    exit(1)
}

func jpeg(_ image: CGImage, to output: URL) throws {
    let bitmap = NSBitmapImageRep(cgImage: image)
    guard let data = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.82]) else {
        throw NSError(domain: "Thumbnail", code: 1)
    }
    try data.write(to: output, options: .atomic)
}

let args = CommandLine.arguments
guard args.count == 4 || args.count == 5 else { fail("Не указан файл") }
let original = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])
let staging = URL(fileURLWithPath: args[3], isDirectory: true)
let manager = FileManager.default
let ext = original.pathExtension.lowercased()
let copyOnly = args.count == 5 && args[4] == "copy"
let local = copyOnly ? output : staging.appendingPathComponent("source." + ext)

// Reading through Foundation materializes iCloud bytes. Decoders only receive
// a local temporary file, never an iCloud URL or an unhydrated clone.
do {
    let attrs = try manager.attributesOfItem(atPath: original.path)
    guard attrs[.type] as? FileAttributeType == .typeRegular else { fail("Нужен обычный файл") }
    if manager.isUbiquitousItem(at: original) { try manager.startDownloadingUbiquitousItem(at: original) }
    var coordinationError: NSError?
    var readError: Error?
    NSFileCoordinator(filePresenter: nil).coordinate(readingItemAt: original, options: [], error: &coordinationError) { url in
        do {
            let attrs = try manager.attributesOfItem(atPath: url.path)
            guard attrs[.type] as? FileAttributeType == .typeRegular,
                  let size = attrs[.size] as? NSNumber, size.int64Value <= 2_147_483_648 else {
                throw NSError(domain: "Thumbnail", code: 2)
            }
            let reader = try FileHandle(forReadingFrom: url)
            defer { try? reader.close() }
            guard manager.createFile(atPath: local.path, contents: nil) else { throw NSError(domain: "Thumbnail", code: 3) }
            let writer = try FileHandle(forWritingTo: local)
            defer { try? writer.close() }
            var total: Int64 = 0
            while let data = try reader.read(upToCount: 1_048_576), !data.isEmpty {
                total += Int64(data.count)
                guard total <= 2_147_483_648 else { throw NSError(domain: "Thumbnail", code: 4) }
                try writer.write(contentsOf: data)
            }
            guard total == size.int64Value else { throw NSError(domain: "Thumbnail", code: 5) }
        } catch { readError = error }
    }
    if let error = coordinationError { throw error }
    if let error = readError { throw error }
} catch {
    fail("Не удалось получить файл из iCloud; повторим автоматически")
}
if copyOnly { exit(0) }

do {
    if ["mov", "mp4", "m4v", "webm", "avi"].contains(ext) {
        let generator = AVAssetImageGenerator(asset: AVURLAsset(url: local))
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 640, height: 640)
        let image: CGImage
        do { image = try generator.copyCGImage(at: CMTime(seconds: 1, preferredTimescale: 600), actualTime: nil) }
        catch { image = try generator.copyCGImage(at: .zero, actualTime: nil) }
        try jpeg(image, to: output)
        exit(0)
    }
    if ext == "pdf" {
        guard let pdf = PDFDocument(data: try Data(contentsOf: local)), !pdf.isLocked,
              let page = pdf.page(at: 0) else { fail("PDF защищён или не читается") }
        let bounds = page.bounds(for: .cropBox)
        guard bounds.width > 0, bounds.height > 0 else { fail("Некорректный размер PDF") }
        let scale = min(640 / bounds.width, 640 / bounds.height)
        let image = page.thumbnail(of: NSSize(width: bounds.width * scale, height: bounds.height * scale), for: .cropBox)
        var rect = CGRect(origin: .zero, size: image.size)
        guard let cg = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else { fail("Не удалось показать PDF") }
        try jpeg(cg, to: output)
        exit(0)
    }
    if let source = CGImageSourceCreateWithURL(local as CFURL, nil),
       let image = CGImageSourceCreateThumbnailAtIndex(source, 0, [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: 640,
            kCGImageSourceShouldCacheImmediately: true
       ] as CFDictionary) {
        try jpeg(image, to: output)
        exit(0)
    }
} catch { fail("Не удалось создать миниатюру; повторим автоматически") }

// Quick Look supplies document thumbnails where macOS has a suitable provider.
// Request only a thumbnail: a generic file icon must not be stored as a success.
let request = QLThumbnailGenerator.Request(fileAt: local, size: CGSize(width: 640, height: 640), scale: 1, representationTypes: .thumbnail)
QLThumbnailGenerator.shared.generateBestRepresentation(for: request) { result, error in
    guard let result = result, result.type == .thumbnail else { fail("Для этого формата пока нет превью") }
    do { try jpeg(result.cgImage, to: output); exit(0) }
    catch { fail("Не удалось сохранить миниатюру") }
}
RunLoop.main.run()
