# static/client-badge.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/client-badge.js](../../../static/client-badge.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-foreground"></a>

## foreground

[static/client-badge.js](../../../static/client-badge.js) · `FunctionDeclaration`.

```javascript
function foreground(color)
```

Выбирает читаемый цвет текста для заданного фона RGB.

Сравнивает яркость фона с порогом контраста для чёрного и белого текста.

Непосредственные вызовы: `color.slice(1).match(/../g).map`, `color.slice(1).match`, `color.slice`.

<a id="symbol-markup"></a>

## markup

[static/client-badge.js](../../../static/client-badge.js) · `FunctionDeclaration`.

```javascript
function markup(label, path)
```

Экранирует подпись и связывает её с полным NFC-путём клиента.

Без пути возвращает обычный текст, а цвет берётся из общих стилей.

Непосредственные вызовы: `String(label ?? '').replace`, `String`, `/^[.#]/.test`, `path.normalize('NFC').replace`, `path.normalize`.

<a id="symbol-render"></a>

## render

[static/client-badge.js](../../../static/client-badge.js) · `FunctionDeclaration`.

```javascript
function render()
```

Обновляет общие стили по сохранённым путям клиентов.

Меняет только таблицу стилей, сохраняя узлы ссылок, выделение и фокус.

Непосредственные вызовы: `document.createElement`, `document.head.append`, `[...colors].filter(([, color]) => /^#[0-9a-f]{6}$/.test(color)).map(([path, color]) =>
      '[data-client-badge="${CSS.escape(path)}"]{--client-badge-bg:${color};--client-badge-fg:${foreground(color)};--client-badge-padding:5px;--client-badge-row-padding:2px;--client-badge-edge:inset 0 0 0 1px #0002}'
    ).join`, `[...colors].filter(([, color]) => /^#[0-9a-f]{6}$/.test(color)).map`, `[...colors].filter`.

Прямые присваивания полям/свойствам: `stylesheet.textContent`.

<a id="symbol-replace"></a>

## replace

[static/client-badge.js](../../../static/client-badge.js) · `FunctionDeclaration`.

```javascript
function replace(records)
```

Применяет свежий полный снимок вручную заданных цветов.

Отсутствующий путь сбрасывает оформление плашки.

Непосредственные вызовы: `Map`, `Object.entries`, `render`.

<a id="symbol-set"></a>

## set

[static/client-badge.js](../../../static/client-badge.js) · `FunctionDeclaration`.

```javascript
function set(path, color)
```

Применяет подтверждённое сервером изменение одного клиента.

Пустой цвет убирает оформление во всех уже отрисованных подписях.

Непосредственные вызовы: `path.normalize`, `colors.set`, `colors.delete`, `render`.
