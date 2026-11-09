# static/invoice-products.js

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [static/invoice-products.js](../../../static/invoice-products.js).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-api"></a>

## api

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
async function api(payload)
```

Читает или явно сохраняет общий каталог с прежней защитой внешней сессии.

При конфликте и сетевой ошибке не повторяет запрос; версия передаётся вызывающим кодом.

Непосредственные вызовы: `fetch`, `JSON.stringify`, `response.json`, `Error`.

<a id="symbol-el"></a>

## el

[static/invoice-products.js](../../../static/invoice-products.js) · `ArrowFunctionExpression`.

```javascript
const el = id =>
```

Находит постоянный узел панели товаров или её отдельной формы.

Узлы не заменяются при загрузке каталога, поэтому ввод и фокус формы сохраняются.

Непосредственные вызовы: `document.getElementById`.

<a id="symbol-groups"></a>

## groups

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
function groups(select, all = false)
```

Строит варианты плоских групп, сохраняя выбранное значение, включая пустую группу.

Используется только при явной загрузке и сохранении; опрос счетов select не перестраивает.

Непосредственные вызовы: `catalog.groups.map(group => '<option value="' + group.id + '">' + html(group.name) + '</option>').join`, `catalog.groups.map`, `[...select.options].some`.

Прямые присваивания полям/свойствам: `select.innerHTML`, `select.value`.

<a id="symbol-html"></a>

## html

[static/invoice-products.js](../../../static/invoice-products.js) · `ArrowFunctionExpression`.

```javascript
const html = value =>
```

Экранирует текст каталога перед включением в разметку.

Пользовательские названия, группы и цены никогда не интерпретируются как HTML.

Непосредственные вызовы: `String(value).replace`, `String`.

<a id="symbol-init"></a>

## init

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
function init(callback, identity)
```

Подключает панель к редактору и устанавливает обработчики один раз.

Принимает добавление позиции и генератор UUID редактора, не зависящий от HTTPS-контекста.

Непосредственные вызовы: `el`, `el('newInvoiceProduct').addEventListener`, `el('newInvoiceProductGroup').addEventListener`, `el('editInvoiceProductGroup').addEventListener`, `el('refreshInvoiceProducts').addEventListener`, `el('invoiceProductGroup').addEventListener`, `el('invoiceProductsSearch').addEventListener`, `el('invoiceProductsList').addEventListener`, `el('invoiceProductForm').addEventListener`, `el('reloadInvoiceProduct').addEventListener`, `el('cancelInvoiceProduct').addEventListener`, `el('invoiceProductDialog').addEventListener`.

Прямые присваивания полям/свойствам: `el('newInvoiceProduct').disabled`, `el('newInvoiceProductGroup').disabled`.

<a id="symbol-load"></a>

## load

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
async function load()
```

Загружает последнюю версию общего каталога при открытии окна или явном обновлении.

Ответ прежней загрузки игнорируется; поля счёта и открытого товара не заменяются.

Непосредственные вызовы: `el`, `api`, `groups`, `render`.

Прямые присваивания полям/свойствам: `el('invoiceProductsState').textContent`, `el('newInvoiceProduct').disabled`, `el('newInvoiceProductGroup').disabled`.

<a id="symbol-open"></a>

## open

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
function open(kind, item = null)
```

Открывает отдельную форму группы или товара, в том числе из ручной строки счёта.

Версия фиксируется до ввода; UUID создаёт прежний генератор редактора, доступный и по HTTP LAN.

Непосредственные вызовы: `createIdentity`, `el`, `groups`, `el('invoiceProductDialog').querySelectorAll`, `el('invoiceProductDialog').showModal`, `el('invoiceProductName').focus`.

Прямые присваивания полям/свойствам: `el('invoiceProductTitle').textContent`, `el('invoiceProductName').maxLength`, `el('invoiceProductName').value`, `el('invoiceProductParent').value`, `el('invoiceProductUnit').value`, `el('invoiceProductPrice').value`, `node.hidden`, `el('invoiceProductState').textContent`, `el('reloadInvoiceProduct').hidden`.

<a id="symbol-render"></a>

## render

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
function render()
```

Показывает товары выбранной группы и поиска без изменения строк счёта.

Каждый товар имеет отдельные действия добавления и правки; сохранённая цена показана в рублях.

Непосредственные вызовы: `el`, `el('invoiceProductsSearch').value.trim().toLocaleLowerCase`, `el('invoiceProductsSearch').value.trim`, `catalog?.groups.some`, `(catalog?.products || []).filter`, `products.map(item => '<div class="invoice-product-row"><button type="button" class="invoice-product-add" data-product-add="' + item.id + '"' +
      (editable ? '' : ' disabled') + ' title="Добавить в счёт"><span>' + html(item.name) + '</span><small>' +
      html(new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(item.price))) + ' ₽' +
      (item.unit ? ' / ' + html(item.unit) : '') + '</small></button><button class="icon-button" type="button" data-product-edit="' + item.id + '" aria-label="Изменить товар ' + html(item.name) + '" title="Изменить товар">✎</button></div>').join`, `products.map`.

Прямые присваивания полям/свойствам: `el('editInvoiceProductGroup').disabled`, `el('invoiceProductsList').innerHTML`, `el('invoiceProductsState').textContent`.

<a id="symbol-review"></a>

## review

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
async function review()
```

Перечитывает конфликтующий каталог с сохранением введённого названия и цены.

Показывает актуальную запись и только затем разрешает явное сохранение с новой версией.

Непосредственные вызовы: `el`, `load`, `catalog[editing.kind === 'group' ? 'groups' : 'products'].find`, `groups`.

Прямые присваивания полям/свойствам: `el('saveInvoiceProduct').disabled`, `el('reloadInvoiceProduct').disabled`, `editing.revision`, `el('invoiceProductState').textContent`, `el('reloadInvoiceProduct').hidden`.

<a id="symbol-save"></a>

## save

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
async function save(event)
```

Отправляет одну явную правку товара или группы и обновляет доступные позиции.

Ошибка сохраняет весь ввод и UUID; повтор возможен только действием пользователя.

Непосредственные вызовы: `event.preventDefault`, `el`, `Object.assign`, `api`, `groups`, `render`, `el('invoiceProductDialog').close`.

Прямые присваивания полям/свойствам: `el('invoiceProductFields').disabled`, `el('saveInvoiceProduct').disabled`, `el('cancelInvoiceProduct').disabled`, `el('invoiceProductState').textContent`, `el('invoiceProductGroup').value`, `el('reloadInvoiceProduct').hidden`.

<a id="symbol-setEditable"></a>

## setEditable

[static/invoice-products.js](../../../static/invoice-products.js) · `FunctionDeclaration`.

```javascript
function setEditable(value)
```

Меняет доступность добавления без перестроения панели и потери фокуса.

Выпущенный счёт и процесс выпуска не допускают новых строк.

Непосредственные вызовы: `el('invoiceProductsList').querySelectorAll`, `el`.

Прямые присваивания полям/свойствам: `button.disabled`.
