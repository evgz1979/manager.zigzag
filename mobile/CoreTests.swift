import Foundation
import CryptoKit

@main
struct CoreTests {
    static func check(_ condition: @autoclosure () -> Bool, _ message: String) {
        precondition(condition(), message)
    }

    static func main() async throws {
        let base = FileManager.default.temporaryDirectory.appendingPathComponent("zigzag-phone-tests-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: base) }
        let orderID = UUID().uuidString.lowercased()
        let rootID = UUID().uuidString.lowercased()
        let task = PhoneTask(id: UUID().uuidString.lowercased(), text: "С Mac", done: false)
        let order = PhoneOrder(id: orderID, path: "Клиент/Объект/2026-10-18", title: "Заказ", client: "Клиент",
                               status: "Новый", financial_status: "Оплачен", note: "Mac", revision: 1, updated: 100,
                               tasks: [task], tasks_text: "- [ ] С Mac", files: [], files_updated: 100, files_error: "")
        let catalog = Catalog(schema: 1, root_id: rootID, generation: 1, generated: 100, orders: [order], receipts: [])
        let store = PhoneStore(directory: base)
        try store.ingest(catalog)
        try store.draft("comment", text: "Черновик без сети")
        let commentID = try store.enqueue(orderID: orderID, kind: "order_comment", text: "Комментарий без сети")
        try store.enqueue(orderID: orderID, kind: "todo_add", text: "С iPhone")
        let added = store.order(orderID)!.tasks!.last!
        let toggleID = try store.enqueue(orderID: orderID, kind: "todo_set", task: added)
        check(store.order(orderID)!.tasks!.last!.done, "Offline toggle must be visible")
        check(store.state.queue.last!.operation.depends_on == store.state.queue[1].id, "Toggle must depend on its addition")
        check(store.order(orderID)!.note == "Mac\n\nКомментарий без сети", "Offline comment must be visible")

        let restarted = PhoneStore(directory: base)
        check(restarted.waiting == 3, "Queue must survive process restart")
        check(restarted.state.drafts["comment"] == "Черновик без сети", "Unsubmitted draft must survive restart")
        check(restarted.state.queue.last!.id == toggleID, "Operation identity must survive restart")
        check(restarted.state.queue[0].bytes == store.state.queue[0].bytes, "Retry must use identical bytes")
        try restarted.markSent(Set([commentID]))
        check(restarted.waiting == 3, "Writing into Drive must not acknowledge Mac application")

        var received = catalog
        received.generation = 2
        received.orders[0].note = "Mac\n\nКомментарий без сети"
        let queued = restarted.state.queue[0]
        received.receipts = [Receipt(id: queued.id, digest: queued.digest, root_id: rootID, status: "applied", message: "Применено")]
        try restarted.ingest(received)
        check(restarted.waiting == 2, "Only an authenticated Mac receipt acknowledges the operation")
        check(restarted.order(orderID)!.note == received.orders[0].note, "Acknowledged comment must not be duplicated by the overlay")
        try restarted.ingest(catalog)
        check(restarted.state.catalog!.generation == 2, "Delayed old catalog must not roll back data")

        var wrong = received
        wrong.root_id = UUID().uuidString.lowercased()
        do { try restarted.ingest(wrong); preconditionFailure("Different archive must be rejected") }
        catch is PhoneError {}
        check(restarted.waiting == 2, "Archive mismatch must preserve pending work")

        var forged = received
        forged.generation = 3
        forged.receipts = [Receipt(id: toggleID, digest: "wrong", root_id: rootID, status: "applied", message: "Подмена")]
        try restarted.ingest(forged)
        check(restarted.waiting == 2, "Receipt for different bytes must be ignored")

        // Corruption blocks writes instead of silently replacing an old queue.
        let before = try Data(contentsOf: base.appendingPathComponent(".state.json"))
        try Data("broken".utf8).write(to: base.appendingPathComponent(".state.json"))
        let damaged = PhoneStore(directory: base)
        check(damaged.loadError != nil, "Corruption must be reported")
        do { try damaged.draft("x", text: "new"); preconditionFailure("Damaged data must not be overwritten") }
        catch is PhoneError {}
        let damagedBytes = try String(contentsOf: base.appendingPathComponent(".state.json"), encoding: .utf8)
        check(damagedBytes == "broken", "Original bytes must remain")
        try before.write(to: base.appendingPathComponent(".state.json"))

        // Exercise the real coordinator/transport on an ordinary local folder.
        // iCloud provider timing and picker permissions still require an iPhone.
        let driveRoot = base.appendingPathComponent("drive")
        let inbox = driveRoot.appendingPathComponent(".mobile-sync/.inbox")
        try FileManager.default.createDirectory(at: inbox, withIntermediateDirectories: true)
        try JSONEncoder().encode(received).write(to: driveRoot.appendingPathComponent(".mobile-sync/.catalog.json"))
        let bookmark = try driveRoot.bookmarkData(options: .minimalBookmark, includingResourceValuesForKeys: nil, relativeTo: nil)
        let transport = DriveTransport()
        let sent = try await transport.sync(bookmark: bookmark, operations: restarted.state.queue, rootID: rootID)
        check(sent.sent.count == 2, "Transport must only publish unacknowledged actions")
        _ = try await transport.sync(bookmark: bookmark, operations: restarted.state.queue, rootID: rootID)
        let pending = restarted.state.queue[1]
        let published = inbox.appendingPathComponent(".\(pending.id).json")
        let uploaded = try Data(contentsOf: published)
        check(uploaded == pending.bytes, "Transport must preserve exact operation bytes on retries")
        try Data("conflict".utf8).write(to: published)
        do {
            _ = try await transport.sync(bookmark: bookmark, operations: restarted.state.queue, rootID: rootID)
            preconditionFailure("Different content must not be overwritten")
        } catch is PhoneError {}
        let unchanged = try Data(contentsOf: published)
        check(unchanged == Data("conflict".utf8), "Conflicting Drive bytes must remain intact")
        print("Phone core: offline queue, drafts, restart, dependencies, receipts, stale catalogs, archive mismatch and corruption — OK")
    }
}
