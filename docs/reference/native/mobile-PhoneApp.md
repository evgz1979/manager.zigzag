# mobile/PhoneApp.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [mobile/PhoneApp.swift:1](../../../mobile/PhoneApp.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## PhoneModel

[mobile/PhoneApp.swift:9](../../../mobile/PhoneApp.swift#L9) · `class`.

```swift
final class PhoneModel: ObservableObject
```

Связывает SwiftUI с локальным хранилищем и транспортом телефона.

Изменения сначала сохраняются локально; серверный обмен сейчас приостановлен.

## init

[mobile/PhoneApp.swift:21](../../../mobile/PhoneApp.swift#L21) · `init`.

```swift
init()
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

## order

[mobile/PhoneApp.swift:33](../../../mobile/PhoneApp.swift#L33) · `func`.

```swift
func order(_ id: String) -> PhoneOrder?
```

Возвращает карточку заказа с наложенными ожидающими действиями телефона.

Неподтверждённые операции остаются видимыми до получения receipt Mac.

## flushDrafts

[mobile/PhoneApp.swift:37](../../../mobile/PhoneApp.swift#L37) · `func`.

```swift
func flushDrafts() throws
```

Сохраняет текущие текстовые черновики из модели на локальный диск.

Ошибка сохранения не должна превращать введённый текст в пустое состояние.

## draft

[mobile/PhoneApp.swift:45](../../../mobile/PhoneApp.swift#L45) · `func`.

```swift
func draft(_ key: String) -> Binding<String>
```

Читает или сохраняет текстовый черновик по устойчивому ключу.

SwiftUI Binding и PhoneStore используют один ключ локального состояния.

## submit

[mobile/PhoneApp.swift:55](../../../mobile/PhoneApp.swift#L55) · `func`.

```swift
func submit(orderID: String, kind: String, key: String, file: PhoneFile? = nil)
```

Ставит текстовое действие пользователя в устойчивую очередь телефона.

Черновик очищается после успешного локального сохранения операции.

## toggle

[mobile/PhoneApp.swift:69](../../../mobile/PhoneApp.swift#L69) · `func`.

```swift
func toggle(orderID: String, task: PhoneTask)
```

Ставит изменение выполнения задачи в локальную очередь телефона.

Передаёт исходные идентификатор, текст и версию для проверки на Mac.

## selectFolder

[mobile/PhoneApp.swift:81](../../../mobile/PhoneApp.swift#L81) · `func`.

```swift
func selectFolder(_ url: URL)
```

Сохраняет bookmark выбранного пользователем корня документов.

Доступ выдаётся системным выбором папки с security-scoped разрешением.

## sync

[mobile/PhoneApp.swift:94](../../../mobile/PhoneApp.swift#L94) · `func`.

```swift
func sync() async
```

Выполняет один цикл обмена через выбранную папку iCloud.

Публикация операции и подтверждение её применения различаются; Mac-обмен отложен.

## cache

[mobile/PhoneApp.swift:113](../../../mobile/PhoneApp.swift#L113) · `func`.

```swift
func cache(_ file: PhoneFile) async
```

Сохраняет выбранный оригинал для автономного просмотра на телефоне.

Проверяет допустимость файла и сохраняет в отдельный локальный каталог вложений.

## isCached

[mobile/PhoneApp.swift:125](../../../mobile/PhoneApp.swift#L125) · `func`.

```swift
func isCached(_ file: PhoneFile) -> Bool
```

Проверяет наличие сохранённой автономной копии вложения.

Путь вычисляется по имени, исходному пути и токену версии файла.

## ZigzagPhoneApp

[mobile/PhoneApp.swift:131](../../../mobile/PhoneApp.swift#L131) · `struct`.

```swift
struct ZigzagPhoneApp: App
```

Объявляет точку входа сохранённого приложения iPhone.

Создаёт модель и корневое SwiftUI-представление приложения.

## RootView

[mobile/PhoneApp.swift:146](../../../mobile/PhoneApp.swift#L146) · `struct`.

```swift
struct RootView: View
```

Собирает вкладки сохранённого приложения iPhone.

Передаёт общую PhoneModel дочерним экранам через окружение.

## SyncSummary

[mobile/PhoneApp.swift:174](../../../mobile/PhoneApp.swift#L174) · `struct`.

```swift
struct SyncSummary: View
```

Показывает состояние локального каталога и обмена телефона.

Данные берутся из сохранённого PhoneStore и текущей модели.

## OrderListView

[mobile/PhoneApp.swift:189](../../../mobile/PhoneApp.swift#L189) · `struct`.

```swift
struct OrderListView: View
```

Показывает каталог заказов телефона с поиском.

Использует последнюю принятую локальную копию каталога.

## OrderView

[mobile/PhoneApp.swift:233](../../../mobile/PhoneApp.swift#L233) · `struct`.

```swift
struct OrderView: View
```

Показывает карточку заказа, задачи и вложения телефона.

Локальные действия проходят через PhoneModel и устойчивую очередь.

## money

[mobile/PhoneApp.swift:238](../../../mobile/PhoneApp.swift#L238) · `func`.

```swift
func money(_ value: Int64?) -> String
```

Форматирует денежное значение для PDF или карточки телефона.

Использует сохранённое числовое значение; расчёты базы этим не изменяются.

## Composer

[mobile/PhoneApp.swift:302](../../../mobile/PhoneApp.swift#L302) · `struct`.

```swift
struct Composer: View
```

Показывает поле текстового действия и кнопку добавления.

Черновик связан с устойчивым ключом локального хранилища.

## FileView

[mobile/PhoneApp.swift:320](../../../mobile/PhoneApp.swift#L320) · `struct`.

```swift
struct FileView: View
```

Показывает сведения файла и действия автономного просмотра.

Оригинал копируется только по явному действию пользователя.

## QueueView

[mobile/PhoneApp.swift:359](../../../mobile/PhoneApp.swift#L359) · `struct`.

```swift
struct QueueView: View
```

Показывает ожидающие и подтверждённые операции телефона.

Сохранённые конфликты доступны для чтения и ручного разбора.

## SettingsView

[mobile/PhoneApp.swift:392](../../../mobile/PhoneApp.swift#L392) · `struct`.

```swift
struct SettingsView: View
```

Показывает выбор папки и состояние настроек телефона.

Системный picker выдаёт доступ к выбранному корню iCloud.

## FolderPicker

[mobile/PhoneApp.swift:417](../../../mobile/PhoneApp.swift#L417) · `struct`.

```swift
struct FolderPicker: UIViewControllerRepresentable
```

Оборачивает системный выбор папки в SwiftUI.

Координатор передаёт выбранный URL обработчику модели.

## makeCoordinator

[mobile/PhoneApp.swift:421](../../../mobile/PhoneApp.swift#L421) · `func`.

```swift
func makeCoordinator() -> Coordinator
```

Создаёт объект делегата для системного UIKit-контроллера.

SwiftUI удерживает координатор на время жизни представления.

## makeUIViewController

[mobile/PhoneApp.swift:424](../../../mobile/PhoneApp.swift#L424) · `func`.

```swift
func makeUIViewController(context: Context) -> UIDocumentPickerViewController
```

Создаёт системный контроллер выбора папки или Quick Look.

Тип контроллера и его делегат определены окружающим представлением.

## updateUIViewController

[mobile/PhoneApp.swift:431](../../../mobile/PhoneApp.swift#L431) · `func`.

```swift
func updateUIViewController(_ controller: UIDocumentPickerViewController, context: Context)
```

Реализует обязательный хук обновления UIKit-представления.

Тело пусто: текущему обёрнутому контроллеру не требуется дополнительное обновление.

## Coordinator

[mobile/PhoneApp.swift:434](../../../mobile/PhoneApp.swift#L434) · `class`.

```swift
final class Coordinator: NSObject, UIDocumentPickerDelegate
```

Связывает делегат системного контроллера с SwiftUI-обёрткой.

Хранит выбранный URL либо обработчик получения папки.

## init

[mobile/PhoneApp.swift:438](../../../mobile/PhoneApp.swift#L438) · `init`.

```swift
init(selected: @escaping (URL) -> Void)
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

## documentPicker

[mobile/PhoneApp.swift:441](../../../mobile/PhoneApp.swift#L441) · `func`.

```swift
func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL])
```

Принимает выбранный системным диалогом URL папки.

Передаёт первый допустимый результат обработчику выбранного корня.

## LocalPreview

[mobile/PhoneApp.swift:449](../../../mobile/PhoneApp.swift#L449) · `struct`.

```swift
struct LocalPreview: UIViewControllerRepresentable
```

Открывает локально сохранённое вложение через Quick Look.

Использует URL автономной копии, а не запись в исходный документ.

## makeCoordinator

[mobile/PhoneApp.swift:453](../../../mobile/PhoneApp.swift#L453) · `func`.

```swift
func makeCoordinator() -> Coordinator
```

Создаёт объект делегата для системного UIKit-контроллера.

SwiftUI удерживает координатор на время жизни представления.

## makeUIViewController

[mobile/PhoneApp.swift:456](../../../mobile/PhoneApp.swift#L456) · `func`.

```swift
func makeUIViewController(context: Context) -> QLPreviewController
```

Создаёт системный контроллер выбора папки или Quick Look.

Тип контроллера и его делегат определены окружающим представлением.

## updateUIViewController

[mobile/PhoneApp.swift:463](../../../mobile/PhoneApp.swift#L463) · `func`.

```swift
func updateUIViewController(_ controller: QLPreviewController, context: Context)
```

Реализует обязательный хук обновления UIKit-представления.

Тело пусто: текущему обёрнутому контроллеру не требуется дополнительное обновление.

## Coordinator

[mobile/PhoneApp.swift:466](../../../mobile/PhoneApp.swift#L466) · `class`.

```swift
final class Coordinator: NSObject, QLPreviewControllerDataSource
```

Связывает делегат системного контроллера с SwiftUI-обёрткой.

Хранит выбранный URL либо обработчик получения папки.

## init

[mobile/PhoneApp.swift:470](../../../mobile/PhoneApp.swift#L470) · `init`.

```swift
init(_ url: URL)
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

## numberOfPreviewItems

[mobile/PhoneApp.swift:473](../../../mobile/PhoneApp.swift#L473) · `func`.

```swift
func numberOfPreviewItems(in controller: QLPreviewController) -> Int
```

Возвращает количество документов текущего Quick Look.

Для этой обёртки доступен ровно один локальный файл.

## previewController

[mobile/PhoneApp.swift:476](../../../mobile/PhoneApp.swift#L476) · `func`.

```swift
func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem
```

Возвращает выбранный локальный URL как документ Quick Look.

Приведение к NSURL реализует ожидаемый QLPreviewItem.
