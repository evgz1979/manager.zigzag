# scripts/documentation_js.cjs

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/documentation_js.cjs:1](../../../scripts/documentation_js.cjs#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## description

[scripts/documentation_js.cjs:16](../../../scripts/documentation_js.cjs#L16) · `FunctionDeclaration`.

```c
function description(code, start)
```

Извлекает ровно две строки комментария перед именованным объявлением.

Учитывает обычные // и двухстрочный /* */ перед методом внутри выражения.

Непосредственные вызовы: `code.slice`, `before.match`, `plain.slice`, `block.slice`.

## callsIn

[scripts/documentation_js.cjs:26](../../../scripts/documentation_js.cjs#L26) · `FunctionDeclaration`.

```c
function callsIn(node, code)
```

Собирает непосредственные вызовы и присваивания свойствам без вложенных функций.

Не разрешает динамические свойства и не исполняет код приложения.

Непосредственные вызовы: `Set`, `scan`.

## scan

[scripts/documentation_js.cjs:30](../../../scripts/documentation_js.cjs#L30) · `FunctionDeclaration`.

```c
function scan(value)
```

Обходит AST одного владельца и пропускает вложенные function/method.

Накапливает вызовы и записи в отдельных Set внешней функции.

Непосредственные вызовы: `Array.isArray`, `value.forEach`, `/Function|Method/.test`, `['CallExpression', 'NewExpression', 'OptionalCallExpression'].includes`, `calls.add`, `code.slice`, `/MemberExpression/.test`, `writes.add`, `Object.entries`, `['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes`, `scan`.

## inventory

[scripts/documentation_js.cjs:49](../../../scripts/documentation_js.cjs#L49) · `FunctionDeclaration`.

```c
function inventory(file)
```

Разбирает один собственный JS-файл и выделяет именованные callable-объявления.

Анонимные callbacks и IIFE относятся к владельцу, сторонний vendor не читается.

Непосредственные вызовы: `fs.readFileSync`, `path.join`, `babelParse`, `walk`.

## walk

[scripts/documentation_js.cjs:55](../../../scripts/documentation_js.cjs#L55) · `FunctionDeclaration`.

```c
function walk(node, parent, ancestors = [])
```

Определяет имя и границу объявления по родительским узлам Babel AST.

Сохраняет фактическую строку функции после вставленных комментариев.

Непосредственные вызовы: `Array.isArray`, `node.forEach`, `['FunctionDeclaration', 'ClassDeclaration'].includes`, `['FunctionExpression', 'ArrowFunctionExpression'].includes`, `ancestors.at`, `['ObjectMethod', 'ClassMethod', 'ClassPrivateMethod'].includes`, `symbols.push`, `code.slice(declaration.start, node.body?.start || node.end).trim`, `code.slice`, `description`, `callsIn`, `Object.entries`, `['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes`, `walk`.
