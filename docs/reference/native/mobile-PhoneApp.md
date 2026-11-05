# mobile/PhoneApp.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Composer"></a>

## Composer

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct Composer: View
```

Показывает поле текстового действия и кнопку добавления.

Черновик связан с устойчивым ключом локального хранилища.

<a id="symbol-FileView"></a>

## FileView

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct FileView: View
```

Показывает сведения файла и действия автономного просмотра.

Оригинал копируется только по явному действию пользователя.

<a id="symbol-FolderPicker"></a>

## FolderPicker

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct FolderPicker: UIViewControllerRepresentable
```

Оборачивает системный выбор папки в SwiftUI.

Координатор передаёт выбранный URL обработчику модели.

<a id="symbol-FolderPicker.Coordinator"></a>

## FolderPicker.Coordinator

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `class`.

```swift
final class Coordinator: NSObject, UIDocumentPickerDelegate
```

Связывает делегат системного контроллера с SwiftUI-обёрткой.

Хранит выбранный URL либо обработчик получения папки.

<a id="symbol-FolderPicker.Coordinator.documentPicker"></a>

## FolderPicker.Coordinator.documentPicker

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL])
```

Принимает выбранный системным диалогом URL папки.

Передаёт первый допустимый результат обработчику выбранного корня.

<a id="symbol-FolderPicker.Coordinator.init"></a>

## FolderPicker.Coordinator.init

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `init`.

```swift
init(selected: @escaping (URL) -> Void)
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

<a id="symbol-FolderPicker.makeCoordinator"></a>

## FolderPicker.makeCoordinator

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func makeCoordinator() -> Coordinator
```

Создаёт объект делегата для системного UIKit-контроллера.

SwiftUI удерживает координатор на время жизни представления.

<a id="symbol-FolderPicker.makeUIViewController"></a>

## FolderPicker.makeUIViewController

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func makeUIViewController(context: Context) -> UIDocumentPickerViewController
```

Создаёт системный контроллер выбора папки или Quick Look.

Тип контроллера и его делегат определены окружающим представлением.

<a id="symbol-FolderPicker.updateUIViewController"></a>

## FolderPicker.updateUIViewController

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func updateUIViewController(_ controller: UIDocumentPickerViewController, context: Context)
```

Реализует обязательный хук обновления UIKit-представления.

Тело пусто: текущему обёрнутому контроллеру не требуется дополнительное обновление.

<a id="symbol-LocalPreview"></a>

## LocalPreview

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct LocalPreview: UIViewControllerRepresentable
```

Открывает локально сохранённое вложение через Quick Look.

Использует URL автономной копии, а не запись в исходный документ.

<a id="symbol-LocalPreview.Coordinator"></a>

## LocalPreview.Coordinator

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `class`.

```swift
final class Coordinator: NSObject, QLPreviewControllerDataSource
```

Связывает делегат системного контроллера с SwiftUI-обёрткой.

Хранит выбранный URL либо обработчик получения папки.

<a id="symbol-LocalPreview.Coordinator.init"></a>

## LocalPreview.Coordinator.init

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `init`.

```swift
init(_ url: URL)
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

<a id="symbol-LocalPreview.Coordinator.numberOfPreviewItems"></a>

## LocalPreview.Coordinator.numberOfPreviewItems

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func numberOfPreviewItems(in controller: QLPreviewController) -> Int
```

Возвращает количество документов текущего Quick Look.

Для этой обёртки доступен ровно один локальный файл.

<a id="symbol-LocalPreview.Coordinator.previewController"></a>

## LocalPreview.Coordinator.previewController

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem
```

Возвращает выбранный локальный URL как документ Quick Look.

Приведение к NSURL реализует ожидаемый QLPreviewItem.

<a id="symbol-LocalPreview.makeCoordinator"></a>

## LocalPreview.makeCoordinator

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func makeCoordinator() -> Coordinator
```

Создаёт объект делегата для системного UIKit-контроллера.

SwiftUI удерживает координатор на время жизни представления.

<a id="symbol-LocalPreview.makeUIViewController"></a>

## LocalPreview.makeUIViewController

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func makeUIViewController(context: Context) -> QLPreviewController
```

Создаёт системный контроллер выбора папки или Quick Look.

Тип контроллера и его делегат определены окружающим представлением.

<a id="symbol-LocalPreview.updateUIViewController"></a>

## LocalPreview.updateUIViewController

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func updateUIViewController(_ controller: QLPreviewController, context: Context)
```

Реализует обязательный хук обновления UIKit-представления.

Тело пусто: текущему обёрнутому контроллеру не требуется дополнительное обновление.

<a id="symbol-OrderListView"></a>

## OrderListView

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct OrderListView: View
```

Показывает каталог заказов телефона с поиском.

Использует последнюю принятую локальную копию каталога.

<a id="symbol-OrderView"></a>

## OrderView

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct OrderView: View
```

Показывает карточку заказа, задачи и вложения телефона.

Локальные действия проходят через PhoneModel и устойчивую очередь.

<a id="symbol-OrderView.money"></a>

## OrderView.money

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func money(_ value: Int64?) -> String
```

Форматирует денежное значение для PDF или карточки телефона.

Использует сохранённое числовое значение; расчёты базы этим не изменяются.

<a id="symbol-PhoneModel"></a>

## PhoneModel

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `class`.

```swift
final class PhoneModel: ObservableObject
```

Связывает SwiftUI с локальным хранилищем и транспортом телефона.

Изменения сначала сохраняются локально; серверный обмен сейчас приостановлен.

<a id="symbol-PhoneModel.cache"></a>

## PhoneModel.cache

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func cache(_ file: PhoneFile) async
```

Сохраняет выбранный оригинал для автономного просмотра на телефоне.

Проверяет допустимость файла и сохраняет в отдельный локальный каталог вложений.

<a id="symbol-PhoneModel.draft"></a>

## PhoneModel.draft

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func draft(_ key: String) -> Binding<String>
```

Читает или сохраняет текстовый черновик по устойчивому ключу.

SwiftUI Binding и PhoneStore используют один ключ локального состояния.

<a id="symbol-PhoneModel.flushDrafts"></a>

## PhoneModel.flushDrafts

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func flushDrafts() throws
```

Сохраняет текущие текстовые черновики из модели на локальный диск.

Ошибка сохранения не должна превращать введённый текст в пустое состояние.

<a id="symbol-PhoneModel.init"></a>

## PhoneModel.init

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `init`.

```swift
init()
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

<a id="symbol-PhoneModel.isCached"></a>

## PhoneModel.isCached

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func isCached(_ file: PhoneFile) -> Bool
```

Проверяет наличие сохранённой автономной копии вложения.

Путь вычисляется по имени, исходному пути и токену версии файла.

<a id="symbol-PhoneModel.order"></a>

## PhoneModel.order

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func order(_ id: String) -> PhoneOrder?
```

Возвращает карточку заказа с наложенными ожидающими действиями телефона.

Неподтверждённые операции остаются видимыми до получения receipt Mac.

<a id="symbol-PhoneModel.selectFolder"></a>

## PhoneModel.selectFolder

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func selectFolder(_ url: URL)
```

Сохраняет bookmark выбранного пользователем корня документов.

Доступ выдаётся системным выбором папки с security-scoped разрешением.

<a id="symbol-PhoneModel.submit"></a>

## PhoneModel.submit

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func submit(orderID: String, kind: String, key: String, file: PhoneFile? = nil)
```

Ставит текстовое действие пользователя в устойчивую очередь телефона.

Черновик очищается после успешного локального сохранения операции.

<a id="symbol-PhoneModel.sync"></a>

## PhoneModel.sync

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func sync() async
```

Выполняет один цикл обмена через выбранную папку iCloud.

Публикация операции и подтверждение её применения различаются; Mac-обмен отложен.

<a id="symbol-PhoneModel.toggle"></a>

## PhoneModel.toggle

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `func`.

```swift
func toggle(orderID: String, task: PhoneTask)
```

Ставит изменение выполнения задачи в локальную очередь телефона.

Передаёт исходные идентификатор, текст и версию для проверки на Mac.

<a id="symbol-QueueView"></a>

## QueueView

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct QueueView: View
```

Показывает ожидающие и подтверждённые операции телефона.

Сохранённые конфликты доступны для чтения и ручного разбора.

<a id="symbol-RootView"></a>

## RootView

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct RootView: View
```

Собирает вкладки сохранённого приложения iPhone.

Передаёт общую PhoneModel дочерним экранам через окружение.

<a id="symbol-SettingsView"></a>

## SettingsView

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct SettingsView: View
```

Показывает выбор папки и состояние настроек телефона.

Системный picker выдаёт доступ к выбранному корню iCloud.

<a id="symbol-SyncSummary"></a>

## SyncSummary

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct SyncSummary: View
```

Показывает состояние локального каталога и обмена телефона.

Данные берутся из сохранённого PhoneStore и текущей модели.

<a id="symbol-ZigzagPhoneApp"></a>

## ZigzagPhoneApp

[mobile/PhoneApp.swift](../../../mobile/PhoneApp.swift) · `struct`.

```swift
struct ZigzagPhoneApp: App
```

Объявляет точку входа сохранённого приложения iPhone.

Создаёт модель и корневое SwiftUI-представление приложения.
