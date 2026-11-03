# mobile/Core.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [mobile/Core.swift:1](../../../mobile/Core.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## PhoneTask

[mobile/Core.swift:6](../../../mobile/Core.swift#L6) · `struct`.

```swift
struct PhoneTask: Codable, Identifiable, Equatable
```

Описывает задачу телефона с устойчивой идентичностью и версией.

Codable сохраняет текст и выполнение для каталога и локального состояния.

## PhoneFile

[mobile/Core.swift:15](../../../mobile/Core.swift#L15) · `struct`.

```swift
struct PhoneFile: Codable, Identifiable, Equatable
```

Описывает вложение заказа и привязку к версии исходного файла.

Путь используется как id; размер, время и token проверяются при действиях.

## PhoneOrder

[mobile/Core.swift:27](../../../mobile/Core.swift#L27) · `struct`.

```swift
struct PhoneOrder: Codable, Identifiable
```

Описывает доступную телефону копию карточки заказа.

Содержит задачи, вложения и время их последнего обновления.

## Receipt

[mobile/Core.swift:51](../../../mobile/Core.swift#L51) · `struct`.

```swift
struct Receipt: Codable
```

Описывает подтверждение применения либо конфликт операции на Mac.

UUID, digest и root_id связывают ответ с точными неизменяемыми байтами запроса.

## Catalog

[mobile/Core.swift:61](../../../mobile/Core.swift#L61) · `struct`.

```swift
struct Catalog: Codable
```

Описывает версионный каталог заказов и подтверждений Mac.

Схема и root_id проверяются до замены локального каталога телефона.

## PhoneOperation

[mobile/Core.swift:72](../../../mobile/Core.swift#L72) · `struct`.

```swift
struct PhoneOperation: Codable, Identifiable
```

Описывает одно неизменяемое действие телефона для Mac.

UUID, sequence и исходная версия защищают от дубля и применения к другой задаче.

## QueuedOperation

[mobile/Core.swift:96](../../../mobile/Core.swift#L96) · `struct`.

```swift
struct QueuedOperation: Codable, Identifiable
```

Хранит действие, точные байты отправки и полученное подтверждение.

Digest считается от однажды сериализованных байтов, а не от повторной кодировки.

## LocalState

[mobile/Core.swift:108](../../../mobile/Core.swift#L108) · `struct`.

```swift
struct LocalState: Codable
```

Объединяет устойчивое состояние телефона: каталог, очередь и черновики.

Сохраняется целиком через PhoneStore.persist до обновления памяти.

## PhoneError

[mobile/Core.swift:120](../../../mobile/Core.swift#L120) · `enum`.

```swift
enum PhoneError: LocalizedError
```

Представляет понятную пользователю ошибку локального приложения.

LocalizedError предоставляет сообщение для состояния интерфейса.

## PhoneStore

[mobile/Core.swift:129](../../../mobile/Core.swift#L129) · `class`.

```swift
final class PhoneStore
```

Хранит локальные данные и очередь операций телефона на диске.

Все изменения проходят через persist; повреждение не заменяется пустой очередью.

## init

[mobile/Core.swift:137](../../../mobile/Core.swift#L137) · `init`.

```swift
init(directory: URL)
```

Инициализирует зависимости и состояние экземпляра.

Конкретные параметры и правила загрузки определены в теле и полях типа.

## persist

[mobile/Core.swift:154](../../../mobile/Core.swift#L154) · `func`.

```swift
func persist(_ next: LocalState) throws
```

Атомарно сохраняет новое локальное состояние до изменения памяти.

Если запись не удалась, прежнее состояние и черновики остаются доступны.

## draft

[mobile/Core.swift:171](../../../mobile/Core.swift#L171) · `func`.

```swift
func draft(_ key: String, text: String) throws
```

Читает или сохраняет текстовый черновик по устойчивому ключу.

SwiftUI Binding и PhoneStore используют один ключ локального состояния.

## bookmark

[mobile/Core.swift:179](../../../mobile/Core.swift#L179) · `func`.

```swift
func bookmark(_ data: Data) throws
```

Сохраняет security-scoped bookmark выбранной папки.

Изменение проходит через общий устойчивый persist.

## enqueue

[mobile/Core.swift:188](../../../mobile/Core.swift#L188) · `func`.

```swift
func enqueue(orderID: String, kind: String, text: String? = nil, task: PhoneTask? = nil, file: PhoneFile? = nil, draftKey: String? = nil) throws -> String
```

Создаёт и сохраняет неизменяемое действие телефона с уникальным UUID.

Проверяет вид операции и сохраняет исходные признаки задачи или файла.

## markSent

[mobile/Core.swift:235](../../../mobile/Core.swift#L235) · `func`.

```swift
func markSent(_ ids: Set<String>) throws
```

Помечает операции как опубликованные в папку обмена.

Флаг sent ещё не означает receipt применения операции сервером Mac.

## ingest

[mobile/Core.swift:243](../../../mobile/Core.swift#L243) · `func`.

```swift
func ingest(_ catalog: Catalog) throws
```

Проверяет новый каталог и принимает подтверждения операций телефона.

Чужой архив, неверные UUID, пути или digest не изменяют очередь.

## safePath

[mobile/Core.swift:251](../../../mobile/Core.swift#L251) · `func`.

```swift
func safePath(_ path: String) -> Bool
```

Проверяет относительный путь вложения или заказа из каталога.

Запрещает пустые и скрытые компоненты и нулевые символы.

## order

[mobile/Core.swift:295](../../../mobile/Core.swift#L295) · `func`.

```swift
func order(_ id: String) -> PhoneOrder?
```

Возвращает карточку заказа с наложенными ожидающими действиями телефона.

Неподтверждённые операции остаются видимыми до получения receipt Mac.

## cachedURL

[mobile/Core.swift:321](../../../mobile/Core.swift#L321) · `func`.

```swift
func cachedURL(_ file: PhoneFile) -> URL
```

Вычисляет локальный путь автономной копии конкретной версии вложения.

SHA-256 от пути и token разделяет версии; имя файла сохраняется в конце.
