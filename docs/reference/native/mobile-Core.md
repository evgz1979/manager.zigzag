# mobile/Core.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [mobile/Core.swift](../../../mobile/Core.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Catalog"></a>

## Catalog

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct Catalog: Codable
```

Описывает версионный каталог заказов и подтверждений Mac.

Схема и root_id проверяются до замены локального каталога телефона.

<a id="symbol-LocalState"></a>

## LocalState

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct LocalState: Codable
```

Объединяет устойчивое состояние телефона: каталог, очередь и черновики.

Сохраняется целиком через PhoneStore.persist до обновления памяти.

<a id="symbol-PhoneError"></a>

## PhoneError

[mobile/Core.swift](../../../mobile/Core.swift) · `enum`.

```swift
enum PhoneError: LocalizedError
```

Представляет понятную пользователю ошибку локального приложения.

LocalizedError предоставляет сообщение для состояния интерфейса.

<a id="symbol-PhoneFile"></a>

## PhoneFile

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct PhoneFile: Codable, Identifiable, Equatable
```

Описывает вложение заказа и привязку к версии исходного файла.

Путь используется как id; размер, время и token проверяются при действиях.

<a id="symbol-PhoneOperation"></a>

## PhoneOperation

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct PhoneOperation: Codable, Identifiable
```

Описывает одно неизменяемое действие телефона для Mac.

UUID, sequence и исходная версия защищают от дубля и применения к другой задаче.

<a id="symbol-PhoneOrder"></a>

## PhoneOrder

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct PhoneOrder: Codable, Identifiable
```

Описывает доступную телефону копию карточки заказа.

Содержит задачи, вложения и время их последнего обновления.

<a id="symbol-PhoneStore"></a>

## PhoneStore

[mobile/Core.swift](../../../mobile/Core.swift) · `class`.

```swift
final class PhoneStore
```

Хранит локальные данные и очередь операций телефона на диске.

Все изменения проходят через persist; повреждение не заменяется пустой очередью.

<a id="symbol-PhoneStore.bookmark"></a>

## PhoneStore.bookmark

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func bookmark(_ data: Data) throws
```

Сохраняет security-scoped bookmark выбранной папки.

Изменение проходит через общий устойчивый persist.

<a id="symbol-PhoneStore.cachedURL"></a>

## PhoneStore.cachedURL

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func cachedURL(_ file: PhoneFile) -> URL
```

Вычисляет локальный путь автономной копии конкретной версии вложения.

SHA-256 от пути и token разделяет версии; имя файла сохраняется в конце.

<a id="symbol-PhoneStore.draft"></a>

## PhoneStore.draft

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func draft(_ key: String, text: String) throws
```

Читает или сохраняет текстовый черновик по устойчивому ключу.

SwiftUI Binding и PhoneStore используют один ключ локального состояния.

<a id="symbol-PhoneStore.enqueue"></a>

## PhoneStore.enqueue

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func enqueue(orderID: String, kind: String, text: String? = nil, task: PhoneTask? = nil, file: PhoneFile? = nil, draftKey: String? = nil) throws -> String
```

Создаёт и сохраняет неизменяемое действие телефона с уникальным UUID.

Проверяет вид операции и сохраняет исходные признаки задачи или файла.

<a id="symbol-PhoneStore.ingest"></a>

## PhoneStore.ingest

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func ingest(_ catalog: Catalog) throws
```

Проверяет новый каталог и принимает подтверждения операций телефона.

Чужой архив, неверные UUID, пути или digest не изменяют очередь.

<a id="symbol-PhoneStore.ingest.safePath"></a>

## PhoneStore.ingest.safePath

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func safePath(_ path: String) -> Bool
```

Проверяет относительный путь вложения или заказа из каталога.

Запрещает пустые и скрытые компоненты и нулевые символы.

<a id="symbol-PhoneStore.init"></a>

## PhoneStore.init

[mobile/Core.swift](../../../mobile/Core.swift) · `init`.

```swift
init(directory: URL)
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

<a id="symbol-PhoneStore.markSent"></a>

## PhoneStore.markSent

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func markSent(_ ids: Set<String>) throws
```

Помечает операции как опубликованные в папку обмена.

Флаг sent ещё не означает receipt применения операции сервером Mac.

<a id="symbol-PhoneStore.order"></a>

## PhoneStore.order

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func order(_ id: String) -> PhoneOrder?
```

Возвращает карточку заказа с наложенными ожидающими действиями телефона.

Неподтверждённые операции остаются видимыми до получения receipt Mac.

<a id="symbol-PhoneStore.persist"></a>

## PhoneStore.persist

[mobile/Core.swift](../../../mobile/Core.swift) · `func`.

```swift
func persist(_ next: LocalState) throws
```

Атомарно сохраняет новое локальное состояние до изменения памяти.

Если запись не удалась, прежнее состояние и черновики остаются доступны.

<a id="symbol-PhoneTask"></a>

## PhoneTask

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct PhoneTask: Codable, Identifiable, Equatable
```

Описывает задачу телефона с устойчивой идентичностью и версией.

Codable сохраняет текст и выполнение для каталога и локального состояния.

<a id="symbol-QueuedOperation"></a>

## QueuedOperation

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct QueuedOperation: Codable, Identifiable
```

Хранит действие, точные байты отправки и полученное подтверждение.

Digest считается от однажды сериализованных байтов, а не от повторной кодировки.

<a id="symbol-Receipt"></a>

## Receipt

[mobile/Core.swift](../../../mobile/Core.swift) · `struct`.

```swift
struct Receipt: Codable
```

Описывает подтверждение применения либо конфликт операции на Mac.

UUID, digest и root_id связывают ответ с точными неизменяемыми байтами запроса.
