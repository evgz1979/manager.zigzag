# scripts/documentation_js.cjs

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/documentation_js.cjs](../../../scripts/documentation_js.cjs).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-callsIn"></a>

## callsIn

[scripts/documentation_js.cjs](../../../scripts/documentation_js.cjs) · `FunctionDeclaration`.

```c
function callsIn(node, code)
```

Собирает непосредственные вызовы и присваивания свойствам без вложенных функций.

Не разрешает динамические свойства и не исполняет код приложения.

Непосредственные вызовы: `Set`, `scan`.

<a id="symbol-callsIn.scan"></a>

## callsIn.scan

[scripts/documentation_js.cjs](../../../scripts/documentation_js.cjs) · `FunctionDeclaration`.

```c
function scan(value)
```

Обходит AST одного владельца и пропускает вложенные function/method.

Накапливает вызовы и записи в отдельных Set внешней функции.

Непосредственные вызовы: `Array.isArray`, `value.forEach`, `/Function|Method/.test`, `['CallExpression', 'NewExpression', 'OptionalCallExpression'].includes`, `calls.add`, `code.slice`, `/MemberExpression/.test`, `writes.add`, `Object.entries`, `['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes`, `scan`.

<a id="symbol-description"></a>

## description

[scripts/documentation_js.cjs](../../../scripts/documentation_js.cjs) · `FunctionDeclaration`.

```c
function description(code, start)
```

Извлекает ровно две строки комментария перед именованным объявлением.

Учитывает обычные // и двухстрочный /* */ перед методом внутри выражения.

Непосредственные вызовы: `code.slice`, `before.match`, `plain.slice`, `block.slice`.

<a id="symbol-inventory"></a>

## inventory

[scripts/documentation_js.cjs](../../../scripts/documentation_js.cjs) · `FunctionDeclaration`.

```c
function inventory(file)
```

Разбирает один собственный JS-файл и выделяет именованные callable-объявления.

Анонимные callbacks и IIFE относятся к владельцу, сторонний vendor не читается.

Непосредственные вызовы: `fs.readFileSync`, `path.join`, `babelParse`, `walk`.

<a id="symbol-inventory.walk"></a>

## inventory.walk

[scripts/documentation_js.cjs](../../../scripts/documentation_js.cjs) · `FunctionDeclaration`.

```c
function walk(node, parent, ancestors = [], scope = [])
```

Определяет имя и границу объявления по родительским узлам Babel AST.

Квалифицирует вложенные имена; физическая строка нужна только диагностике и поиску.

Непосредственные вызовы: `Array.isArray`, `node.forEach`, `['FunctionDeclaration', 'ClassDeclaration'].includes`, `['FunctionExpression', 'ArrowFunctionExpression'].includes`, `ancestors.at`, `['ObjectMethod', 'ClassMethod', 'ClassPrivateMethod'].includes`, `symbols.push`, `[...scope, name].join`, `code.slice(declaration.start, node.body?.start || node.end).trim`, `code.slice`, `description`, `callsIn`, `Object.entries`, `['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes`, `walk`.
