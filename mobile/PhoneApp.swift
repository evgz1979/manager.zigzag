#if os(iOS)
import SwiftUI
import UniformTypeIdentifiers
import QuickLook

@MainActor
// Связывает SwiftUI с локальным хранилищем и транспортом телефона.
// Изменения сначала сохраняются локально; серверный обмен сейчас приостановлен.
final class PhoneModel: ObservableObject {
    let store: PhoneStore
    let drive = DriveTransport()
    @Published var state: LocalState
    @Published var drafts: [String: String]
    @Published var message = ""
    @Published var syncing = false
    @Published var downloading: Set<String> = []
    @Published var localError = ""

    // Инициализирует зависимости и состояние экземпляра.
    // Конкретные параметры и правила загрузки определены в теле и полях типа.
    init() {
        let directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("ZigzagPhone")
        store = PhoneStore(directory: directory)
        state = store.state
        drafts = store.state.drafts
        localError = store.loadError ?? ""
    }

    var waiting: Int { store.waiting }
    var conflicts: Int { state.queue.filter { $0.receipt?.status == "conflict" }.count }
    // Возвращает карточку заказа с наложенными ожидающими действиями телефона.
    // Неподтверждённые операции остаются видимыми до получения receipt Mac.
    func order(_ id: String) -> PhoneOrder? { store.order(id) }

    // Сохраняет текущие текстовые черновики из модели на локальный диск.
    // Ошибка сохранения не должна превращать введённый текст в пустое состояние.
    func flushDrafts() throws {
        var next = store.state
        next.drafts = drafts
        try store.persist(next)
    }

    // Читает или сохраняет текстовый черновик по устойчивому ключу.
    // SwiftUI Binding и PhoneStore используют один ключ локального состояния.
    func draft(_ key: String) -> Binding<String> {
        Binding(get: { self.drafts[key] ?? "" }, set: { value in
            self.drafts[key] = value
            do { try self.flushDrafts(); self.state = self.store.state; self.localError = "" }
            catch { self.localError = "Текст пока не сохранён на диск: \(error.localizedDescription)" }
        })
    }

    // Ставит текстовое действие пользователя в устойчивую очередь телефона.
    // Черновик очищается после успешного локального сохранения операции.
    func submit(orderID: String, kind: String, key: String, file: PhoneFile? = nil) {
        do {
            try flushDrafts()
            try store.enqueue(orderID: orderID, kind: kind, text: drafts[key] ?? "", file: file, draftKey: key)
            drafts.removeValue(forKey: key)
            state = store.state
            localError = ""
            message = "Сохранено на iPhone. Ожидает подтверждения Mac"
            Task { await sync() }
        } catch { localError = error.localizedDescription }
    }

    // Ставит изменение выполнения задачи в локальную очередь телефона.
    // Передаёт исходные идентификатор, текст и версию для проверки на Mac.
    func toggle(orderID: String, task: PhoneTask) {
        do {
            try flushDrafts()
            try store.enqueue(orderID: orderID, kind: "todo_set", task: task)
            state = store.state
            localError = ""
            Task { await sync() }
        } catch { localError = error.localizedDescription }
    }

    // Сохраняет bookmark выбранного пользователем корня документов.
    // Доступ выдаётся системным выбором папки с security-scoped разрешением.
    func selectFolder(_ url: URL) {
        let access = url.startAccessingSecurityScopedResource()
        defer { if access { url.stopAccessingSecurityScopedResource() } }
        do {
            try flushDrafts()
            try store.bookmark(url.bookmarkData(options: .minimalBookmark, includingResourceValuesForKeys: nil, relativeTo: nil))
            state = store.state
            Task { await sync() }
        } catch { localError = error.localizedDescription }
    }

    // Выполняет один цикл обмена через выбранную папку iCloud.
    // Публикация операции и подтверждение её применения различаются; Mac-обмен отложен.
    func sync() async {
        guard !syncing, let bookmark = state.bookmark else { return }
        syncing = true
        defer { syncing = false }
        do {
            try flushDrafts()
            let result = try await drive.sync(bookmark: bookmark, operations: store.state.queue, rootID: store.state.catalog?.root_id)
            try store.markSent(result.sent)
            try store.ingest(JSONDecoder().decode(Catalog.self, from: result.catalogData))
            state = store.state
            message = waiting == 0 ? "Получены данные Mac" : "Записи сохранены. Ожидают подтверждения Mac: \(waiting)"
        } catch {
            state = store.state
            message = "Обмен отложен. \(error.localizedDescription)"
        }
    }

    // Сохраняет выбранный оригинал для автономного просмотра на телефоне.
    // Проверяет допустимость файла и сохраняет в отдельный локальный каталог вложений.
    func cache(_ file: PhoneFile) async {
        guard let bookmark = state.bookmark, !downloading.contains(file.id) else { return }
        downloading.insert(file.id)
        defer { downloading.remove(file.id) }
        do {
            try await drive.cache(bookmark: bookmark, file: file, destination: store.cachedURL(file))
            message = "Файл сохранён для просмотра без интернета"
        } catch { message = error.localizedDescription }
    }

    // Проверяет наличие сохранённой автономной копии вложения.
    // Путь вычисляется по имени, исходному пути и токену версии файла.
    func isCached(_ file: PhoneFile) -> Bool { FileManager.default.fileExists(atPath: store.cachedURL(file).path) }
}

@main
// Объявляет точку входа сохранённого приложения iPhone.
// Создаёт модель и корневое SwiftUI-представление приложения.
struct ZigzagPhoneApp: App {
    @StateObject private var model = PhoneModel()
    @Environment(\.scenePhase) private var scenePhase
    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(model)
                .onChange(of: scenePhase) { _, phase in
                    if phase == .active { Task { await model.sync() } }
                }
        }
    }
}

// Собирает вкладки сохранённого приложения iPhone.
// Передаёт общую PhoneModel дочерним экранам через окружение.
struct RootView: View {
    @EnvironmentObject private var model: PhoneModel
    var body: some View {
        TabView {
            OrderListView().tabItem { Label("Заказы", systemImage: "folder") }
            QueueView().tabItem { Label("Изменения", systemImage: "arrow.triangle.2.circlepath") }
                .badge(model.waiting + model.conflicts)
            SettingsView().tabItem { Label("Настройка", systemImage: "gearshape") }
        }
        .tint(Color(red: 0.08, green: 0.43, blue: 0.34))
        .safeAreaInset(edge: .top) {
            if !model.localError.isEmpty {
                Text(model.localError).font(.footnote).foregroundStyle(.red).padding(10)
                    .frame(maxWidth: .infinity).background(.regularMaterial).textSelection(.enabled)
            }
        }
        .task {
            await model.sync()
            while !Task.isCancelled {
                do { try await Task.sleep(for: .seconds(60)) } catch { break }
                await model.sync()
            }
        }
    }
}

// Показывает состояние локального каталога и обмена телефона.
// Данные берутся из сохранённого PhoneStore и текущей модели.
struct SyncSummary: View {
    @EnvironmentObject private var model: PhoneModel
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            if let generated = model.state.catalog?.generated {
                Text("Данные Mac от \(Date(timeIntervalSince1970: generated).formatted(date: .abbreviated, time: .shortened))")
            } else { Text("Карточки ещё не загружены") }
            if model.waiting > 0 { Text("Ожидают подтверждения Mac: \(model.waiting)").foregroundStyle(.orange) }
            if !model.message.isEmpty { Text(model.message) }
        }.font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
    }
}

// Показывает каталог заказов телефона с поиском.
// Использует последнюю принятую локальную копию каталога.
struct OrderListView: View {
    @EnvironmentObject private var model: PhoneModel
    @State private var search = ""
    var orders: [PhoneOrder] {
        (model.state.catalog?.orders ?? []).compactMap { model.order($0.id) }.filter {
            search.isEmpty || "\($0.title) \($0.path) \($0.note)".localizedCaseInsensitiveContains(search)
        }
    }
    var body: some View {
        NavigationStack {
            List {
                Section { SyncSummary() }
                if model.state.catalog == nil {
                    ContentUnavailableView("Заказы с собой", systemImage: "iphone", description: Text("На Mac подготовьте обмен в разделе «iPhone · обмен». Затем в настройке здесь выберите папку «Зигзаг» из iCloud Drive. Для первой загрузки нужна связь."))
                }
                ForEach(orders) { order in
                    NavigationLink { OrderView(orderID: order.id) } label: {
                        VStack(alignment: .leading, spacing: 5) {
                            Text(order.title).font(.headline)
                            Text(order.client).font(.subheadline).foregroundStyle(.secondary)
                            HStack {
                                Text(order.status)
                                Text("·")
                                Text(order.financial_status)
                            }.font(.caption).foregroundStyle(.secondary)
                            if let tasks = order.tasks, !tasks.isEmpty {
                                Text("To-do: \(tasks.filter(\.done).count) из \(tasks.count)").font(.caption)
                            }
                        }.padding(.vertical, 3)
                    }
                }
            }
            .navigationTitle("Зигзаг")
            .searchable(text: $search, prompt: "Заказ, клиент, заметка")
            .refreshable { await model.sync() }
            .toolbar { Button { Task { await model.sync() } } label: {
                if model.syncing { ProgressView() } else { Image(systemName: "arrow.clockwise") }
            }.disabled(model.syncing || model.state.bookmark == nil).accessibilityLabel("Синхронизировать") }
        }
    }
}

// Показывает карточку заказа, задачи и вложения телефона.
// Локальные действия проходят через PhoneModel и устойчивую очередь.
struct OrderView: View {
    @EnvironmentObject private var model: PhoneModel
    let orderID: String
    // Форматирует денежное значение для PDF или карточки телефона.
    // Использует сохранённое числовое значение; расчёты базы этим не изменяются.
    func money(_ value: Int64?) -> String {
        guard let value else { return "Не указано" }
        return (Double(value) / 100).formatted(.currency(code: "RUB"))
    }
    var body: some View {
        Group {
            if let order = model.order(orderID) {
                List {
                    Section { SyncSummary(); Text(order.path).font(.caption).textSelection(.enabled) }
                    Section("Карточка") {
                        LabeledContent("Производство", value: order.status)
                        LabeledContent("Оплата", value: order.financial_status)
                        LabeledContent("Сумма", value: money(order.amount))
                        LabeledContent("Затраты", value: money(order.costs))
                        LabeledContent("Прибыль", value: money(order.profit))
                        LabeledContent("Оплачено", value: money(order.paid))
                        LabeledContent("Остаток", value: money(order.debt))
                    }
                    Section("Заметка заказа") {
                        Text(order.note.isEmpty ? "Пока нет заметки" : order.note).textSelection(.enabled)
                    }
                    Section("Добавить комментарий к заказу") {
                        Composer(orderID: orderID, kind: "order_comment", key: "order:\(orderID)")
                    }
                    Section("To-do") {
                        if let tasks = order.tasks {
                            ForEach(tasks) { task in
                                Button { model.toggle(orderID: orderID, task: task) } label: {
                                    HStack(alignment: .top) {
                                        Image(systemName: task.done ? "checkmark.circle.fill" : "circle")
                                        Text(task.text).strikethrough(task.done).foregroundStyle(.primary)
                                    }
                                }.accessibilityLabel("\(task.text), \(task.done ? "выполнено" : "не выполнено")")
                            }
                            Composer(orderID: orderID, kind: "todo_add", key: "todo:\(orderID)")
                        } else {
                            Text(order.tasks_text).textSelection(.enabled)
                            Text("Прежний текст задач доступен для чтения").font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    Section("Файлы · \(order.files.count)") {
                        if !order.files_error.isEmpty { Text(order.files_error).font(.caption).foregroundStyle(.orange) }
                        if order.files_updated > 0 {
                            Text("Список от \(Date(timeIntervalSince1970: order.files_updated).formatted(date: .abbreviated, time: .shortened))").font(.caption).foregroundStyle(.secondary)
                        }
                        ForEach(order.files) { file in
                            NavigationLink { FileView(orderID: orderID, filePath: file.path) } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    Label(file.name, systemImage: model.isCached(file) ? "checkmark.circle" : "doc")
                                    if !file.comment.isEmpty { Text(file.comment).font(.caption).foregroundStyle(.secondary).lineLimit(3) }
                                }
                            }
                        }
                    }
                }.navigationTitle(order.title).navigationBarTitleDisplayMode(.inline)
            } else {
                ContentUnavailableView("Заказ убран из списка", systemImage: "folder", description: Text("Ваши комментарии и задачи остались во вкладке «Изменения»."))
            }
        }
    }
}

// Показывает поле текстового действия и кнопку добавления.
// Черновик связан с устойчивым ключом локального хранилища.
struct Composer: View {
    @EnvironmentObject private var model: PhoneModel
    let orderID: String
    let kind: String
    let key: String
    var file: PhoneFile? = nil
    var body: some View {
        TextField(kind == "todo_add" ? "Новая задача" : "Новый комментарий", text: model.draft(key), axis: .vertical)
            .lineLimit(2...8)
        Button(kind == "todo_add" ? "Добавить задачу" : "Добавить комментарий") {
            model.submit(orderID: orderID, kind: kind, key: key, file: file)
        }.disabled((model.drafts[key] ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        Text("Ввод сохраняется на iPhone. После добавления — в очередь обмена.").font(.caption).foregroundStyle(.secondary)
    }
}

// Показывает сведения файла и действия автономного просмотра.
// Оригинал копируется только по явному действию пользователя.
struct FileView: View {
    @EnvironmentObject private var model: PhoneModel
    let orderID: String
    let filePath: String
    @State private var preview = false
    var file: PhoneFile? { model.order(orderID)?.files.first { $0.path == filePath } }
    var body: some View {
        Group {
            if let file {
                List {
                    Section {
                        Text(file.path).font(.caption).textSelection(.enabled)
                        Text(ByteCountFormatter.string(fromByteCount: file.size, countStyle: .file)).foregroundStyle(.secondary)
                        if model.isCached(file) {
                            Button("Открыть сохранённую копию") { preview = true }
                            Label("Доступен без интернета", systemImage: "checkmark.circle").font(.caption)
                        } else {
                            Button { Task { await model.cache(file) } } label: {
                                if model.downloading.contains(file.id) { ProgressView("Сохранение…") }
                                else { Label("Сохранить для просмотра без связи", systemImage: "arrow.down.circle") }
                            }.disabled(model.downloading.contains(file.id))
                            Text("Для первой загрузки файла нужна связь. Комментарий можно добавить и без загрузки оригинала.").font(.caption).foregroundStyle(.secondary)
                        }
                        if !model.message.isEmpty { Text(model.message).font(.caption).foregroundStyle(.secondary) }
                    }
                    Section("Заметка заказа") { Text(model.order(orderID)?.note ?? "").textSelection(.enabled) }
                    Section("Комментарий к файлу") { Text(file.comment.isEmpty ? "Пока нет комментария" : file.comment).textSelection(.enabled) }
                    Section("Добавить комментарий") {
                        Composer(orderID: orderID, kind: "file_comment", key: "file:\(orderID):\(filePath)", file: file)
                    }
                }.navigationTitle(file.name).navigationBarTitleDisplayMode(.inline)
                    .sheet(isPresented: $preview) { LocalPreview(url: model.store.cachedURL(file)) }
            } else { Text("Файл отсутствует в последнем каталоге. Ваш ввод сохранён во вкладке «Изменения» или в черновике.") }
        }
    }
}

// Показывает ожидающие и подтверждённые операции телефона.
// Сохранённые конфликты доступны для чтения и ручного разбора.
struct QueueView: View {
    @EnvironmentObject private var model: PhoneModel
    var body: some View {
        NavigationStack {
            List {
                Section { SyncSummary() }
                if model.state.queue.isEmpty { Text("Новых комментариев и задач пока нет") }
                ForEach(model.state.queue.reversed()) { queued in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(queued.operation.kind.hasPrefix("todo") ? "To-do" : "Комментарий").font(.headline)
                        Text(model.state.catalog?.orders.first { $0.id == queued.operation.order_id }?.title ?? queued.operation.order_title ?? "Заказ из прежнего каталога").font(.caption)
                        if let path = queued.operation.order_path { Text(path).font(.caption2).foregroundStyle(.secondary) }
                        if let path = queued.operation.file_path { Text(path).font(.caption).foregroundStyle(.secondary) }
                        Text(queued.operation.text ?? queued.operation.base_text ?? "Отметка задачи").textSelection(.enabled)
                        Text(queued.receipt?.message ?? (queued.sent ? "Сохранено для передачи через iCloud. Ожидает Mac" : "Сохранено на iPhone. Ожидает обмена"))
                            .font(.caption).foregroundStyle(queued.receipt?.status == "conflict" ? .orange : .secondary)
                        Text(Date(timeIntervalSince1970: queued.operation.created), style: .date).font(.caption2).foregroundStyle(.secondary)
                    }.padding(.vertical, 4)
                }
                if !model.drafts.filter({ !$0.value.isEmpty }).isEmpty {
                    Section("Черновики") {
                        ForEach(model.drafts.keys.sorted(), id: \.self) { key in
                            if let text = model.drafts[key], !text.isEmpty { Text(text).textSelection(.enabled) }
                        }
                    }
                }
            }.navigationTitle("Изменения").refreshable { await model.sync() }
        }
    }
}

// Показывает выбор папки и состояние настроек телефона.
// Системный picker выдаёт доступ к выбранному корню iCloud.
struct SettingsView: View {
    @EnvironmentObject private var model: PhoneModel
    @State private var picker = false
    var body: some View {
        NavigationStack {
            Form {
                Section("Папка обмена") {
                    Text("На Mac откройте «iPhone · обмен» и нажмите «Подготовить обмен». Здесь выберите ту же папку «Зигзаг» в iCloud Drive.")
                    Button(model.state.bookmark == nil ? "Выбрать папку «Зигзаг»" : "Выбрать папку заново") { picker = true }
                    Button("Синхронизировать") { Task { await model.sync() } }.disabled(model.syncing || model.state.bookmark == nil)
                }
                Section { SyncSummary() }
                Section("Без связи") {
                    Text("Полученные карточки, комментарии, задачи и черновики хранятся на телефоне. Отдельные файлы скачивайте заранее кнопкой «Сохранить для просмотра без связи».")
                    Text("Пока Mac выключен или iCloud недоступен, новые записи остаются в очереди. Не удаляйте приложение с непереданными изменениями.")
                    Text("Синхронизация выполняется при открытии и по кнопке. Время фонового обмена зависит от iOS.")
                }
            }.navigationTitle("Настройка")
                .sheet(isPresented: $picker) { FolderPicker { url in model.selectFolder(url) } }
        }
    }
}

// Оборачивает системный выбор папки в SwiftUI.
// Координатор передаёт выбранный URL обработчику модели.
struct FolderPicker: UIViewControllerRepresentable {
    var selected: (URL) -> Void
    // Создаёт объект делегата для системного UIKit-контроллера.
    // SwiftUI удерживает координатор на время жизни представления.
    func makeCoordinator() -> Coordinator { Coordinator(selected: selected) }
    // Создаёт системный контроллер выбора папки или Quick Look.
    // Тип контроллера и его делегат определены окружающим представлением.
    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.folder], asCopy: false)
        picker.delegate = context.coordinator
        return picker
    }
    // Реализует обязательный хук обновления UIKit-представления.
    // Тело пусто: текущему обёрнутому контроллеру не требуется дополнительное обновление.
    func updateUIViewController(_ controller: UIDocumentPickerViewController, context: Context) {}
    // Связывает делегат системного контроллера с SwiftUI-обёрткой.
    // Хранит выбранный URL либо обработчик получения папки.
    final class Coordinator: NSObject, UIDocumentPickerDelegate {
        let selected: (URL) -> Void
        // Инициализирует зависимости и состояние экземпляра.
        // Конкретные параметры и правила загрузки определены в теле и полях типа.
        init(selected: @escaping (URL) -> Void) { self.selected = selected }
        // Принимает выбранный системным диалогом URL папки.
        // Передаёт первый допустимый результат обработчику выбранного корня.
        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            if let url = urls.first { selected(url) }
        }
    }
}

// Открывает локально сохранённое вложение через Quick Look.
// Использует URL автономной копии, а не запись в исходный документ.
struct LocalPreview: UIViewControllerRepresentable {
    let url: URL
    // Создаёт объект делегата для системного UIKit-контроллера.
    // SwiftUI удерживает координатор на время жизни представления.
    func makeCoordinator() -> Coordinator { Coordinator(url) }
    // Создаёт системный контроллер выбора папки или Quick Look.
    // Тип контроллера и его делегат определены окружающим представлением.
    func makeUIViewController(context: Context) -> QLPreviewController {
        let controller = QLPreviewController()
        controller.dataSource = context.coordinator
        return controller
    }
    // Реализует обязательный хук обновления UIKit-представления.
    // Тело пусто: текущему обёрнутому контроллеру не требуется дополнительное обновление.
    func updateUIViewController(_ controller: QLPreviewController, context: Context) {}
    // Связывает делегат системного контроллера с SwiftUI-обёрткой.
    // Хранит выбранный URL либо обработчик получения папки.
    final class Coordinator: NSObject, QLPreviewControllerDataSource {
        let url: URL
        // Инициализирует зависимости и состояние экземпляра.
        // Конкретные параметры и правила загрузки определены в теле и полях типа.
        init(_ url: URL) { self.url = url }
        // Возвращает количество документов текущего Quick Look.
        // Для этой обёртки доступен ровно один локальный файл.
        func numberOfPreviewItems(in controller: QLPreviewController) -> Int { 1 }
        // Возвращает выбранный локальный URL как документ Quick Look.
        // Приведение к NSURL реализует ожидаемый QLPreviewItem.
        func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem { url as NSURL }
    }
}
#endif
