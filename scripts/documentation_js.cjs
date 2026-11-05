/* Development-only inventory: application code is parsed, never executed. */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const root = path.resolve(__dirname, '..');
const resolver = createRequire(path.join(root, 'package.json'));
let bundle = process.env.MANAGER_DOCUMENTATION_BABEL;
if (!bundle) {
  try { bundle = path.join(path.dirname(resolver.resolve('playwright/package.json')), 'lib/transform/babelBundle.js'); }
  catch (_) { throw new Error('Set MANAGER_DOCUMENTATION_BABEL or NODE_PATH to the bundled Playwright package directory'); }
}
const { babelParse } = require(bundle);

// Извлекает ровно две строки комментария перед именованным объявлением.
// Учитывает обычные // и двухстрочный /* */ перед методом внутри выражения.
function description(code, start) {
  const before = code.slice(0, start);
  const plain = before.match(/\/\/ ([^\n]+)\n[ \t]*\/\/ ([^\n]+)\n[ \t]*$/);
  if (plain) return plain.slice(1);
  const block = before.match(/\/\* ([^\n]+)\n[ \t]*\* ([^\n]+) \*\/\s*$/);
  return block ? block.slice(1) : [];
}

// Собирает непосредственные вызовы и присваивания свойствам без вложенных функций.
// Не разрешает динамические свойства и не исполняет код приложения.
function callsIn(node, code) {
  const calls = new Set(), writes = new Set();
  // Обходит AST одного владельца и пропускает вложенные function/method.
  // Накапливает вызовы и записи в отдельных Set внешней функции.
  function scan(value) {
    if (!value || typeof value !== 'object') return;
    if (Array.isArray(value)) { value.forEach(scan); return; }
    if (value !== node && /Function|Method/.test(value.type)) return;
    if (['CallExpression', 'NewExpression', 'OptionalCallExpression'].includes(value.type)) {
      calls.add(code.slice(value.callee.start, value.callee.end));
    }
    if (value.type === 'AssignmentExpression' && /MemberExpression/.test(value.left.type)) writes.add(code.slice(value.left.start, value.left.end));
    if (value.type === 'UpdateExpression' && /MemberExpression/.test(value.argument.type)) writes.add(code.slice(value.argument.start, value.argument.end));
    for (const [key, child] of Object.entries(value)) {
      if (!['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) scan(child);
    }
  }
  scan(node);
  return { calls: [...calls], writes: [...writes] };
}

// Разбирает один собственный JS-файл и выделяет именованные callable-объявления.
// Анонимные callbacks и IIFE относятся к владельцу, сторонний vendor не читается.
function inventory(file) {
  const code = fs.readFileSync(path.join(root, file), 'utf8');
  const tree = babelParse(code, file);
  const symbols = [];
  // Определяет имя и границу объявления по родительским узлам Babel AST.
  // Квалифицирует вложенные имена; физическая строка нужна только диагностике и поиску.
  function walk(node, parent, ancestors = [], scope = []) {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) { node.forEach(child => walk(child, parent, ancestors, scope)); return; }
    let name, declaration = node;
    if (['FunctionDeclaration', 'ClassDeclaration'].includes(node.type)) name = node.id?.name;
    if (['FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
      if (parent?.type === 'VariableDeclarator' && parent.init === node) {
        name = parent.id.name;
        declaration = ancestors.at(-1)?.type === 'VariableDeclaration' ? ancestors.at(-1) : parent;
      }
      if (parent?.type === 'ObjectProperty' && parent.value === node) {
        name = parent.key.name || parent.key.value;
        declaration = parent;
      }
    }
    if (['ObjectMethod', 'ClassMethod', 'ClassPrivateMethod'].includes(node.type)) name = node.key.name || node.key.id?.name || node.key.value;
    if (name) {
      symbols.push({ name: [...scope, name].join('.'), line: declaration.loc.start.line, end_line: node.loc.end.line, type: node.type,
        signature: code.slice(declaration.start, node.body?.start || node.end).trim(),
        description: description(code, declaration.start), ...callsIn(node.body, code) });
    }
    for (const [key, child] of Object.entries(node)) {
      if (!['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes(key) && typeof child === 'object') walk(child, node, [...ancestors, parent], name ? [...scope, name] : scope);
    }
  }
  walk(tree, null);
  return { path: file, symbols };
}

process.stdout.write(JSON.stringify(fs.readdirSync(path.join(root, 'static')).filter(name => name.endsWith('.js')).sort().map(name => 'static/' + name).concat(['scripts/documentation_js.cjs']).map(inventory)));
