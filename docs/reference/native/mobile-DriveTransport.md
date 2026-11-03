# mobile/DriveTransport.swift

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [mobile/DriveTransport.swift:1](../../../mobile/DriveTransport.swift#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## DriveTransport

[mobile/DriveTransport.swift:6](../../../mobile/DriveTransport.swift#L6) · `actor`.

```swift
actor DriveTransport
```

Изолирует координацию iCloud в отдельном Swift actor.

Ожидание файлов не выполняется в локальном редакторе PhoneStore.

## SyncResult

[mobile/DriveTransport.swift:9](../../../mobile/DriveTransport.swift#L9) · `struct`.

```swift
struct SyncResult: Sendable
```

Передаёт результат одного цикла файлового обмена.

Содержит опубликованные UUID и полученные байты каталога Mac.

## resolve

[mobile/DriveTransport.swift:16](../../../mobile/DriveTransport.swift#L16) · `func`.

```swift
func resolve(_ bookmark: Data) throws -> URL
```

Разрешает сохранённый bookmark в URL выбранного корня.

Неверное разрешение передаётся вызывающему коду через throws.

## available

[mobile/DriveTransport.swift:23](../../../mobile/DriveTransport.swift#L23) · `func`.

```swift
func available(_ url: URL) throws
```

Проверяет готовность iCloud-файла к согласованному чтению.

При незавершённой загрузке инициирует скачивание и сообщает о необходимости повтора.

## read

[mobile/DriveTransport.swift:33](../../../mobile/DriveTransport.swift#L33) · `func`.

```swift
func read(_ url: URL, limit: Int = 32 * 1024 * 1024) throws -> Data
```

Читает ограниченный файл через NSFileCoordinator.

Ошибки координации, недоступность и превышение размера передаются через throws.

## sync

[mobile/DriveTransport.swift:50](../../../mobile/DriveTransport.swift#L50) · `func`.

```swift
func sync(bookmark: Data, operations: [QueuedOperation], rootID: String?) throws -> SyncResult
```

Выполняет один цикл обмена через выбранную папку iCloud.

Публикация операции и подтверждение её применения различаются; Mac-обмен отложен.

## cache

[mobile/DriveTransport.swift:90](../../../mobile/DriveTransport.swift#L90) · `func`.

```swift
func cache(bookmark: Data, file: PhoneFile, destination: URL) throws
```

Сохраняет выбранный оригинал для автономного просмотра на телефоне.

Проверяет допустимость файла и сохраняет в отдельный локальный каталог вложений.
