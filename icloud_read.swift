import Foundation
import Darwin

// Только чтение одного файла с явным пределом. Таймаут процесса задаёт вызывающий Python.
do {
    guard CommandLine.arguments.count == 3,
          let limit = Int(CommandLine.arguments[2]), limit > 0, limit <= 20_971_520 else {
        throw NSError(domain: "ZigzagRead", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "Некорректный запрос чтения"])
    }
    let url = URL(fileURLWithPath: CommandLine.arguments[1])
    let original = try FileManager.default.attributesOfItem(atPath: url.path)
    guard original[.type] as? FileAttributeType == .typeRegular else {
        throw NSError(domain: "ZigzagRead", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "Нужен обычный файл"])
    }
    if FileManager.default.isUbiquitousItem(at: url) {
        try FileManager.default.startDownloadingUbiquitousItem(at: url)
    }
    var coordinationError: NSError?
    var readError: Error?
    var contents: Data?
    let coordinator = NSFileCoordinator(filePresenter: nil)
    coordinator.coordinate(readingItemAt: url, options: [], error: &coordinationError) { localURL in
        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: localURL.path)
            guard attributes[.type] as? FileAttributeType == .typeRegular,
                  let size = attributes[.size] as? NSNumber, size.intValue <= limit else {
                throw NSError(domain: "ZigzagRead", code: 2,
                              userInfo: [NSLocalizedDescriptionKey: "Нужен обычный файл в пределах указанного размера"])
            }
            let file = try FileHandle(forReadingFrom: localURL)
            defer { try? file.close() }
            let data = try file.read(upToCount: limit + 1) ?? Data()
            guard data.count <= limit, data.count == size.intValue else {
                throw NSError(domain: "ZigzagRead", code: 3,
                              userInfo: [NSLocalizedDescriptionKey: "Файл вырос во время чтения"])
            }
            contents = data
        } catch { readError = error }
    }
    if let error = coordinationError { throw error }
    if let error = readError { throw error }
    guard let data = contents else {
        throw NSError(domain: "ZigzagRead", code: 4,
                      userInfo: [NSLocalizedDescriptionKey: "iCloud не предоставил файл"])
    }
    FileHandle.standardOutput.write(data)
} catch {
    FileHandle.standardError.write(Data((error.localizedDescription + "\n").utf8))
    exit(1)
}
