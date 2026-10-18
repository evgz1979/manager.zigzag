import Foundation

/// Runs on its own actor. Coordination/download waits never block local editing.
actor DriveTransport {
    struct SyncResult: Sendable {
        var sent: Set<String>
        var catalogData: Data
    }

    func resolve(_ bookmark: Data) throws -> URL {
        var stale = false
        return try URL(resolvingBookmarkData: bookmark, options: [], relativeTo: nil, bookmarkDataIsStale: &stale)
    }

    func available(_ url: URL) throws {
        let values = try url.resourceValues(forKeys: [.isUbiquitousItemKey, .ubiquitousItemDownloadingStatusKey])
        if values.isUbiquitousItem == true && values.ubiquitousItemDownloadingStatus != .current {
            try FileManager.default.startDownloadingUbiquitousItem(at: url)
            throw PhoneError.message("iCloud загружает данные. Локальные записи сохранены; повторите обмен, когда появится связь")
        }
    }

    func read(_ url: URL, limit: Int = 32 * 1024 * 1024) throws -> Data {
        try available(url)
        var coordinationError: NSError?
        var result: Result<Data, Error> = .failure(PhoneError.message("Файл пока недоступен"))
        NSFileCoordinator().coordinate(readingItemAt: url, options: [], error: &coordinationError) { path in
            result = Result {
                let size = try path.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
                guard size <= limit else { throw PhoneError.message("Каталог обмена слишком большой") }
                return try Data(contentsOf: path)
            }
        }
        if let coordinationError { throw coordinationError }
        return try result.get()
    }

    func sync(bookmark: Data, operations: [QueuedOperation], rootID: String?) throws -> SyncResult {
        let root = try resolve(bookmark)
        let access = root.startAccessingSecurityScopedResource()
        defer { if access { root.stopAccessingSecurityScopedResource() } }
        let folder = root.appendingPathComponent(".mobile-sync", isDirectory: true)
        let catalogData = try read(folder.appendingPathComponent(".catalog.json"))
        let catalog = try JSONDecoder().decode(Catalog.self, from: catalogData)
        guard catalog.schema == 1, rootID == nil || rootID == catalog.root_id else {
            throw PhoneError.message("Выбрана другая папка. Очередь не отправлена")
        }
        var sent = Set<String>()
        for queued in operations where queued.receipt == nil {
            guard queued.operation.root_id == catalog.root_id else { throw PhoneError.message("Действие относится к другому архиву") }
            let path = folder.appendingPathComponent(".inbox", isDirectory: true).appendingPathComponent(".\(queued.id).json")
            var coordinationError: NSError?
            var result: Result<Void, Error> = .success(())
            NSFileCoordinator().coordinate(writingItemAt: path, options: [], error: &coordinationError) { url in
                result = Result {
                    if FileManager.default.fileExists(atPath: url.path) {
                        guard try Data(contentsOf: url) == queued.bytes else { throw PhoneError.message("Конфликт файла обмена; исходная запись сохранена") }
                    } else {
                        // moveItem fails if another item already exists; never replace.
                        let temporary = url.deletingLastPathComponent().appendingPathComponent(".\(UUID().uuidString).tmp")
                        defer { try? FileManager.default.removeItem(at: temporary) }
                        try queued.bytes.write(to: temporary, options: .atomic)
                        try FileManager.default.moveItem(at: temporary, to: url)
                    }
                }
            }
            if let coordinationError { throw coordinationError }
            try result.get()
            sent.insert(queued.id)
        }
        // Publication only means the system accepted a local file. A later catalog
        // receipt, not this method, acknowledges application on the Mac.
        return SyncResult(sent: sent, catalogData: catalogData)
    }

    func cache(bookmark: Data, file: PhoneFile, destination: URL) throws {
        guard file.size <= 100 * 1024 * 1024 else { throw PhoneError.message("Для автономного просмотра пока доступны файлы до 100 МБ") }
        let root = try resolve(bookmark)
        let access = root.startAccessingSecurityScopedResource()
        defer { if access { root.stopAccessingSecurityScopedResource() } }
        let parts = file.path.split(separator: "/", omittingEmptySubsequences: false)
        guard !parts.isEmpty, parts.allSatisfy({ !$0.isEmpty && !$0.hasPrefix(".") }) else {
            throw PhoneError.message("Некорректный путь документа")
        }
        var target = root
        for part in parts {
            target.appendPathComponent(String(part))
            if try target.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink == true {
                throw PhoneError.message("Символические ссылки не поддерживаются")
            }
        }
        try available(target)
        var coordinationError: NSError?
        var result: Result<Void, Error> = .success(())
        NSFileCoordinator().coordinate(readingItemAt: target, options: [], error: &coordinationError) { source in
            result = Result {
                let values = try source.resourceValues(forKeys: [.fileSizeKey, .contentModificationDateKey])
                guard Int64(values.fileSize ?? -1) == file.size,
                      abs((values.contentModificationDate?.timeIntervalSince1970 ?? 0) - file.modified) < 2 else {
                    throw PhoneError.message("Файл изменился. Сначала получите новый каталог с Mac")
                }
                try FileManager.default.createDirectory(at: destination.deletingLastPathComponent(), withIntermediateDirectories: true)
                if FileManager.default.fileExists(atPath: destination.path) { return }
                let temporary = destination.deletingLastPathComponent().appendingPathComponent(".download-\(UUID().uuidString)")
                defer { try? FileManager.default.removeItem(at: temporary) }
                try FileManager.default.copyItem(at: source, to: temporary)
                try FileManager.default.moveItem(at: temporary, to: destination)
            }
        }
        if let coordinationError { throw coordinationError }
        try result.get()
    }
}
