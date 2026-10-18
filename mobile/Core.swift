import Foundation
import CryptoKit

struct PhoneTask: Codable, Identifiable, Equatable {
    var id: String
    var text: String
    var done: Bool
    var version: Int = 1
}

struct PhoneFile: Codable, Identifiable, Equatable {
    var path: String
    var name: String
    var size: Int64
    var modified: Double
    var token: String
    var comment: String
    var id: String { path }
}

struct PhoneOrder: Codable, Identifiable {
    var id: String
    var path: String
    var title: String
    var client: String
    var status: String
    var financial_status: String
    var note: String
    var revision: Int
    var updated: Double
    var amount: Int64?
    var costs: Int64?
    var paid: Int64?
    var profit: Int64?
    var debt: Int64?
    var tasks: [PhoneTask]?
    var tasks_text: String
    var files: [PhoneFile]
    var files_updated: Double
    var files_error: String
}

struct Receipt: Codable {
    var id: String
    var digest: String
    var root_id: String
    var status: String
    var message: String
}

struct Catalog: Codable {
    var schema: Int
    var root_id: String
    var generation: Int
    var generated: Double
    var orders: [PhoneOrder]
    var receipts: [Receipt]
}

struct PhoneOperation: Codable, Identifiable {
    var schema = 1
    var id = UUID().uuidString.lowercased()
    var root_id: String
    var order_id: String
    var order_path: String?
    var order_title: String?
    var device_id: String
    var sequence: Int
    var created = Date().timeIntervalSince1970
    var kind: String
    var text: String?
    var task_id: String?
    var done: Bool?
    var base_done: Bool?
    var base_version: Int?
    var base_text: String?
    var file_path: String?
    var file_token: String?
    var depends_on: String?
}

struct QueuedOperation: Codable, Identifiable {
    var operation: PhoneOperation
    // Encode ONCE. The exact immutable bytes also authenticate the receipt.
    var bytes: Data
    var sent = false
    var receipt: Receipt?
    var id: String { operation.id }
    var digest: String { SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined() }
}

struct LocalState: Codable {
    var deviceID = UUID().uuidString.lowercased()
    var nextSequence = 1
    var catalog: Catalog?
    var queue: [QueuedOperation] = []
    var drafts: [String: String] = [:]
    var bookmark: Data?
    var received: Double?
}

enum PhoneError: LocalizedError {
    case message(String)
    var errorDescription: String? { if case .message(let text) = self { return text }; return nil }
}

/// Local disk only. All writes go through persist; failure never clears a draft.
/// A damaged state is not silently replaced by an empty queue.
final class PhoneStore {
    let directory: URL
    private(set) var state: LocalState
    private(set) var loadError: String?
    private let encoder: JSONEncoder

    init(directory: URL) {
        self.directory = directory
        encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let file = directory.appendingPathComponent(".state.json")
        do {
            if FileManager.default.fileExists(atPath: file.path) {
                state = try JSONDecoder().decode(LocalState.self, from: Data(contentsOf: file))
            } else { state = LocalState() }
        } catch {
            state = LocalState()
            loadError = "Не удалось прочитать сохранённые данные. Исходный файл сохранён; запись остановлена: \(error.localizedDescription)"
        }
    }

    func persist(_ next: LocalState) throws {
        if let error = loadError { throw PhoneError.message(error) }
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let file = directory.appendingPathComponent(".state.json")
        let data = try encoder.encode(next)
        if FileManager.default.fileExists(atPath: file.path) {
            try Data(contentsOf: file).write(to: directory.appendingPathComponent(".previous.json"), options: .atomic)
        }
        try data.write(to: file, options: .atomic)
        let handle = try FileHandle(forWritingTo: file)
        defer { try? handle.close() }
        try handle.synchronize()
        state = next
    }

    func draft(_ key: String, text: String) throws {
        var next = state
        next.drafts[key] = text
        try persist(next)
    }

    func bookmark(_ data: Data) throws {
        var next = state
        next.bookmark = data
        try persist(next)
    }

    @discardableResult
    func enqueue(orderID: String, kind: String, text: String? = nil, task: PhoneTask? = nil,
                 file: PhoneFile? = nil, draftKey: String? = nil) throws -> String {
        guard let catalog = state.catalog, let order = catalog.orders.first(where: { $0.id == orderID }) else {
            throw PhoneError.message("Сначала получите карточку заказа с Mac")
        }
        if let text {
            let maxLength = kind == "todo_add" ? 1000 : 5000
            guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                  text.count <= maxLength, !text.contains("\0"),
                  kind != "todo_add" || (!text.contains("\n") && !text.contains("\r")) else {
                throw PhoneError.message("Проверьте текст: задача — одна строка до 1000 символов, комментарий — до 5000")
            }
        }
        guard ["order_comment", "file_comment", "todo_add", "todo_set"].contains(kind) else {
            throw PhoneError.message("Неизвестное действие")
        }
        var operation = PhoneOperation(root_id: catalog.root_id, order_id: orderID,
                                       device_id: state.deviceID, sequence: state.nextSequence, kind: kind, text: text)
        operation.order_path = order.path
        operation.order_title = order.title
        if kind == "todo_add" { operation.task_id = UUID().uuidString.lowercased() }
        if kind == "todo_set" {
            guard let task else { throw PhoneError.message("Задача недоступна") }
            operation.task_id = task.id
            operation.done = !task.done
            operation.base_done = task.done
            operation.base_version = task.version
            operation.base_text = task.text
            operation.depends_on = state.queue.last(where: {
                $0.operation.task_id == task.id && $0.receipt == nil
            })?.id
        }
        if kind == "file_comment" {
            guard let file else { throw PhoneError.message("Файл недоступен") }
            operation.file_path = file.path
            operation.file_token = file.token
        }
        var next = state
        next.queue.append(QueuedOperation(operation: operation, bytes: try encoder.encode(operation)))
        next.nextSequence += 1
        if let draftKey { next.drafts.removeValue(forKey: draftKey) }
        try persist(next)
        return operation.id
    }

    func markSent(_ ids: Set<String>) throws {
        var next = state
        for index in next.queue.indices where ids.contains(next.queue[index].id) { next.queue[index].sent = true }
        try persist(next)
    }

    func ingest(_ catalog: Catalog) throws {
        guard catalog.schema == 1, UUID(uuidString: catalog.root_id) != nil, catalog.generation > 0,
              Set(catalog.orders.map(\.id)).count == catalog.orders.count else {
            throw PhoneError.message("Неподдерживаемый каталог обмена")
        }
        for order in catalog.orders {
            func safePath(_ path: String) -> Bool {
                let parts = path.split(separator: "/", omittingEmptySubsequences: false)
                return !parts.isEmpty && parts.allSatisfy { !$0.isEmpty && !$0.hasPrefix(".") && !$0.contains("\0") }
            }
            guard UUID(uuidString: order.id) != nil, safePath(order.path),
                  Set(order.files.map(\.path)).count == order.files.count,
                  order.tasks == nil || Set(order.tasks!.map(\.id)).count == order.tasks!.count else {
                throw PhoneError.message("Некорректные идентификаторы или пути в каталоге")
            }
            for task in order.tasks ?? [] {
                guard UUID(uuidString: task.id) != nil, task.version > 0 else { throw PhoneError.message("Некорректная версия задачи") }
            }
            for file in order.files {
                guard safePath(file.path), file.path.hasPrefix(order.path + "/"),
                      file.path.split(separator: "/").last.map(String.init) == file.name,
                      file.size >= 0, file.token.count == 64,
                      file.token.allSatisfy({ $0.isHexDigit }) else {
                    throw PhoneError.message("Некорректный путь вложения в каталоге")
                }
            }
        }
        if let current = state.catalog {
            guard current.root_id == catalog.root_id else {
                throw PhoneError.message("Это другой архив. Сохранённые данные и очередь не изменены; выберите прежнюю папку")
            }
            if catalog.generation < current.generation { return }
        }
        var next = state
        next.catalog = catalog
        next.received = Date().timeIntervalSince1970
        for receipt in catalog.receipts {
            guard let index = next.queue.firstIndex(where: { $0.id == receipt.id }),
                  receipt.root_id == catalog.root_id, receipt.digest == next.queue[index].digest,
                  ["applied", "conflict"].contains(receipt.status) else { continue }
            next.queue[index].receipt = receipt
        }
        try persist(next)
    }

    var waiting: Int { state.queue.filter { $0.receipt == nil }.count }

    /// Overlay local actions until a catalog confirms application on the Mac.
    func order(_ id: String) -> PhoneOrder? {
        guard var result = state.catalog?.orders.first(where: { $0.id == id }) else { return nil }
        for queued in state.queue where queued.operation.order_id == id && queued.receipt == nil {
            let op = queued.operation
            switch op.kind {
            case "order_comment":
                result.note += (result.note.isEmpty ? "" : "\n\n") + (op.text ?? "")
            case "file_comment":
                if let index = result.files.firstIndex(where: { $0.path == op.file_path }) {
                    result.files[index].comment += (result.files[index].comment.isEmpty ? "" : "\n\n") + (op.text ?? "")
                }
            case "todo_add":
                if result.tasks != nil, let id = op.task_id { result.tasks?.append(PhoneTask(id: id, text: op.text ?? "", done: false)) }
            case "todo_set":
                if let index = result.tasks?.firstIndex(where: { $0.id == op.task_id }) {
                    result.tasks?[index].done = op.done ?? false
                    result.tasks?[index].version += 1
                }
            default: break
            }
        }
        return result
    }

    func cachedURL(_ file: PhoneFile) -> URL {
        let key = SHA256.hash(data: Data((file.path + "\0" + file.token).utf8)).map { String(format: "%02x", $0) }.joined()
        return directory.appendingPathComponent("Attachments").appendingPathComponent(key).appendingPathComponent(file.name)
    }
}
