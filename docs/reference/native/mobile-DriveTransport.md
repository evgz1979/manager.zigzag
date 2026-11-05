# mobile/DriveTransport.swift

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-DriveTransport"></a>

## DriveTransport

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `actor`.

```swift
actor DriveTransport
```

Изолирует координацию iCloud в отдельном Swift actor.

Ожидание файлов не выполняется в локальном редакторе PhoneStore.

<a id="symbol-DriveTransport.SyncResult"></a>

## DriveTransport.SyncResult

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `struct`.

```swift
struct SyncResult: Sendable
```

Передаёт результат одного цикла файлового обмена.

Содержит опубликованные UUID и полученные байты каталога Mac.

<a id="symbol-DriveTransport.available"></a>

## DriveTransport.available

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `func`.

```swift
func available(_ url: URL) throws
```

Проверяет готовность iCloud-файла к согласованному чтению.

При незавершённой загрузке инициирует скачивание и сообщает о необходимости повтора.

<a id="symbol-DriveTransport.cache"></a>

## DriveTransport.cache

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `func`.

```swift
func cache(bookmark: Data, file: PhoneFile, destination: URL) throws
```

Сохраняет выбранный оригинал для автономного просмотра на телефоне.

Проверяет допустимость файла и сохраняет в отдельный локальный каталог вложений.

<a id="symbol-DriveTransport.read"></a>

## DriveTransport.read

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `func`.

```swift
func read(_ url: URL, limit: Int = 32 * 1024 * 1024) throws -> Data
```

Читает ограниченный файл через NSFileCoordinator.

Ошибки координации, недоступность и превышение размера передаются через throws.

<a id="symbol-DriveTransport.resolve"></a>

## DriveTransport.resolve

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `func`.

```swift
func resolve(_ bookmark: Data) throws -> URL
```

Разрешает сохранённый bookmark в URL выбранного корня.

Неверное разрешение передаётся вызывающему коду через throws.

<a id="symbol-DriveTransport.sync"></a>

## DriveTransport.sync

[mobile/DriveTransport.swift](../../../mobile/DriveTransport.swift) · `func`.

```swift
func sync(bookmark: Data, operations: [QueuedOperation], rootID: String?) throws -> SyncResult
```

Выполняет один цикл обмена через выбранную папку iCloud.

Публикация операции и подтверждение её применения различаются; Mac-обмен отложен.
