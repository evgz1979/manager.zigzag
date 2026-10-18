import Foundation

/// Used only by protocol_check.py with a temporary fake archive, never in the app.
@main
struct ProtocolProbe {
    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1])
        let mode = CommandLine.arguments[2]
        let store = PhoneStore(directory: root.appendingPathComponent("phone-local"))
        let exchange = root.appendingPathComponent(".mobile-sync")
        let catalog = try JSONDecoder().decode(Catalog.self, from: Data(contentsOf: exchange.appendingPathComponent(".catalog.json")))
        try store.ingest(catalog)
        let order = store.state.catalog!.orders[0]
        if mode == "queue" {
            try store.draft("survives", text: "Черновик 🧵")
            try store.enqueue(orderID: order.id, kind: "order_comment", text: "С iPhone 🧵\nВторая строка")
            try store.enqueue(orderID: order.id, kind: "file_comment", text: "Комментарий к файлу", file: order.files[0])
            try store.enqueue(orderID: order.id, kind: "todo_add", text: "Новая задача iPhone")
            let added = store.order(order.id)!.tasks!.last!
            try store.enqueue(orderID: order.id, kind: "todo_set", task: added)
            for item in store.state.queue {
                try item.bytes.write(to: exchange.appendingPathComponent(".inbox/.\(item.id).json"), options: .atomic)
            }
            precondition(store.waiting == 4)
        } else {
            precondition(store.waiting == 0, "All four operations must be authenticated by Mac receipts")
            precondition(store.state.queue.count == 4, "Acknowledged operations remain readable")
            precondition(store.state.drafts["survives"] == "Черновик 🧵")
            precondition(store.order(order.id)!.tasks!.last!.done)
            precondition(store.order(order.id)!.files[0].comment == "Комментарий к файлу")
            precondition(store.order(order.id)!.note.components(separatedBy: "С iPhone").count == 2)
            print("Python ↔ Swift: comments, file comments, To-do, offline restart, raw-byte receipts, repeated delivery — OK")
        }
    }
}
