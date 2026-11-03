#!/usr/bin/env python3
"""Build/check source reference without importing the application or opening data."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'docs/reference'
NATIVE_PATTERN = re.compile(r'^(\s*)(?:(?:public|private|fileprivate|static|final|override|mutating|nonisolated)\s+)*(func|class|struct|enum|actor|init)\b\s*(\w+)?')


# Возвращает две строки назначения перед объявлением Python или нативного кода.
# Декораторы учитываются вызывающим кодом; старые docstring не подменяются.
def description(lines, start, prefix):
    before = lines[max(0, start - 3):start - 1]
    return [line.strip()[len(prefix):].strip() for line in before] if len(before) == 2 and all(line.strip().startswith(prefix + ' ') for line in before) else []


# Обходит тело одного объявления без включения тел вложенных функций и классов.
# Это синтаксический анализ непосредственных операций, а не динамический call graph.
def own_nodes(node):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield child
        yield from own_nodes(child)


# Собирает вызовы, return, raise и прямые присваивания полям Python-объявления.
# Ограничение вложенных тел не приписывает их операции внешнему владельцу.
def facts(node):
    calls, returns, raises, writes = [], [], [], []
    for item in own_nodes(node):
        if isinstance(item, ast.Call):
            calls.append(ast.unparse(item.func))
        elif isinstance(item, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = item.targets if isinstance(item, ast.Assign) else [item.target]
            writes += [ast.unparse(target) for target in targets if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id in ['self', 'cls']]
        elif isinstance(item, ast.Return) and item.value:
            returns.append(ast.unparse(item.value))
        elif isinstance(item, ast.Raise) and item.exc:
            raises.append(ast.unparse(item.exc.func if isinstance(item.exc, ast.Call) else item.exc))
    return {key: list(dict.fromkeys(values)) for key, values in [('calls', calls), ('returns', returns), ('raises', raises), ('writes', writes)]}


# Строит инвентаризацию всех именованных объявлений собственного Python-файла.
# Читает AST и комментарии, но не исполняет модуль и его конфигурацию.
def python_inventory(path):
    source = path.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)
    symbols = []

    # Сохраняет квалифицированные имена методов и вложенных Python-функций.
    # Стек родителей разделяет одинаковые короткие имена разных классов.
    class Visitor(ast.NodeVisitor):
        # Создаёт пустой стек области видимости анализируемого файла.
        # Внешняя коллекция symbols получает результаты обхода.
        def __init__(self):
            self.parents = []

        # Регистрирует объявление и затем обходит его вложенные области.
        # Сигнатура берётся из AST, номера строк — из текущего исходника.
        def visit_definition(self, node):
            start = min([node.lineno] + [item.lineno for item in getattr(node, 'decorator_list', [])])
            args = ', '.join(ast.unparse(base) for base in node.bases) if isinstance(node, ast.ClassDef) else ast.unparse(node.args)
            symbols.append({'name': '.'.join([*self.parents, node.name]), 'line': node.lineno, 'end_line': node.end_lineno,
                            'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                            'signature': ('class ' + node.name + ('(' + args + ')' if args else '') if isinstance(node, ast.ClassDef) else ('async def ' if isinstance(node, ast.AsyncFunctionDef) else 'def ') + node.name + '(' + args + ')' + (' -> ' + ast.unparse(node.returns) if node.returns else '')) + ':', 'description': description(lines, start, '#'), **facts(node)})
            self.parents.append(node.name)
            self.generic_visit(node)
            self.parents.pop()

        visit_FunctionDef = visit_definition
        visit_AsyncFunctionDef = visit_definition
        visit_ClassDef = visit_definition

    Visitor().visit(tree)
    imports = sorted({alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
                     | {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module})
    return {'path': path.relative_to(ROOT).as_posix(), 'summary': ast.get_docstring(tree) or '', 'imports': imports, 'symbols': symbols}


# Перечисляет объявления Swift и C по поддерживаемым формам проекта.
# Свойства, верхнеуровневые операторы и анонимные замыкания описываются у владельца.
def native_inventory(path):
    lines = path.read_text().splitlines()
    symbols = []
    for index, line in enumerate(lines):
        match = NATIVE_PATTERN.match(line) if path.suffix == '.swift' else re.match(r'^(\s*)(?:static )?(?:void|int) (\w+)\(', line)
        if not match:
            continue
        kind = match[2] if path.suffix == '.swift' else 'function'
        name = ('init' if kind == 'init' else match[3]) if path.suffix == '.swift' else match[2]
        signature = line.strip()
        following = index
        while '{' not in signature and following + 1 < len(lines):
            following += 1
            signature += ' ' + lines[following].strip()
        symbols.append({'name': name, 'line': index + 1, 'type': kind,
                        'signature': signature.split(' {')[0], 'description': description(lines, index + 1, '//'), 'calls': []})
    return {'path': path.relative_to(ROOT).as_posix(), 'symbols': symbols}


# Находит именованные JS-функции, встроенные в HTML-шаблоны Python/HTML.
# Анонимные обработчики относятся к владельцу, строки кода не исполняются.
def embedded_inventory(path):
    lines = path.read_text().splitlines()
    symbols = []
    for index, line in enumerate(lines):
        match = re.match(r'^\s*(?:async\s+)?function\s+(\w+)\s*\(', line)
        if match:
            symbols.append({'name': match[1], 'line': index + 1, 'type': 'embedded JavaScript',
                            'signature': line.strip().split(' {')[0], 'description': description(lines, index + 1, '//'), 'calls': []})
    return {'path': path.relative_to(ROOT).as_posix(), 'summary': 'JavaScript внутри автономного HTML-шаблона; контекст данных и запуск описаны у Python-владельца.', 'symbols': symbols}


# Формирует стабильное имя справочника отдельного исходного файла.
# Префикс scripts/mobile исключает совпадения одинаковых базовых имён.
def reference_name(file):
    return file['path'].rsplit('.', 1)[0].replace('/', '-') + '.md'


# Создаёт относительную Markdown-ссылку на файл и фактическую строку кода.
# Номер проверяется по текущей инвентаризации, а не по прежнему снимку.
def source_link(path, line, folder):
    target = os.path.relpath(ROOT / path, folder)
    return '[' + path + ':' + str(line) + '](' + target + '#L' + str(line) + ')'


# Строит страницу справочника одного модуля по его текущим объявлениям.
# Вызовы и return представлены как синтаксические сведения с явными пределами.
def module_page(file, folder):
    out = ['# ' + file['path'], '', 'Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).', '',
           'Исходник: ' + source_link(file['path'], 1, folder) + '.', '']
    if file.get('summary'):
        out += [file['summary'], '']
    if file.get('imports'):
        out += ['Импорты Python, включая локальные: ' + ', '.join('`' + name + '`' for name in file['imports']) + '.', '']
    if not file['symbols']:
        out += ['Именованных классов/функций нет: программа выполняет верхнеуровневый сценарий. См. [объяснение нативного запуска](../../language/swift-c.md).', '']
    else:
        out += ['Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.', '']
    for symbol in file['symbols']:
        out += ['## ' + symbol['name'], '', source_link(file['path'], symbol['line'], folder) + ' · `' + symbol['type'] + '`.', '',
                '```' + ('javascript' if symbol['type'] == 'embedded JavaScript' else 'python' if file['path'].endswith('.py') else 'javascript' if file['path'].endswith('.js') else 'swift' if file['path'].endswith('.swift') else 'c'), symbol['signature'], '```', '',
                '\n\n'.join(symbol['description']), '']
        for key, title in [('calls', 'Непосредственные вызовы'), ('raises', 'Явные исключения'), ('writes', 'Прямые присваивания полям/свойствам')]:
            values = symbol.get(key, [])
            if values:
                out += [title + ': ' + ', '.join('`' + value.replace('`', "'") + '`' for value in values) + '.', '']
        returns = symbol.get('returns', [])
        if returns:
            out += ['Выражения возврата (ветки читаются в исходнике):', '', '```python', '\n'.join(value if len(value) <= 600 else value[:597] + '...' for value in returns), '```', '']
    return '\n'.join(out).rstrip() + '\n'


# Извлекает ветки HTTP-маршрутов из фактических сравнений route/path.
# Не принимает упоминание API в сообщении или защите Origin за отдельный маршрут.
def api_page():
    out = ['# HTTP API: точки входа', '', 'Получено статически из веток обработчиков. Параметры ниже — строковые ключи payload/get, найденные внутри ветки, а не автоматически доказанная обязательная JSON-схема. Точные проверки находятся по ссылке и в вызываемом доменном методе.', '',
           'На внешнем слушателе все маршруты наследуют проверки входа. HEAD использует общую GET-маршрутизацию. Защитные проверки, общие лимиты тела и специальные загрузки могут находиться перед перечисленными ветками.', '']
    for relative in ['server.py', 'remote_access.py']:
        source = (ROOT / relative).read_text()
        tree = ast.parse(source)
        for method in [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in ['handle_get', 'do_POST', 'get_remote', 'receive_calendar_telegram', 'receive_upload', 'receive_telegram_settings']]:
            seen = set()
            for node in ast.walk(method):
                if not isinstance(node, ast.If):
                    continue
                test = ast.unparse(node.test)
                if not re.search(r'\b(route|path)\s*(==|in)\s*', test):
                    continue
                routes = sorted({value.value for value in ast.walk(node.test) if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value.startswith(('/api/', '/_auth/'))})
                for route in routes:
                    if route in seen:
                        continue
                    seen.add(route)
                    params = sorted({argument.value for statement in node.body for call in ast.walk(statement) if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == 'payload' and call.func.attr == 'get' for argument in call.args[:1] if isinstance(argument, ast.Constant) and isinstance(argument.value, str)})
                    branch = [item for statement in node.body for item in ast.walk(statement)]
                    params = sorted(set(params) | {item.slice.value for item in branch if isinstance(item, ast.Subscript) and isinstance(item.value, ast.Name) and item.value.id == 'payload' and isinstance(item.slice, ast.Constant) and isinstance(item.slice.value, str)})
                    query_params = sorted({call.args[0].value for call in branch if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == 'query' and call.func.attr == 'get' and call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str)})
                    calls = list(dict.fromkeys(ast.unparse(call.func) for call in branch if isinstance(call, ast.Call) and not ast.unparse(call.func).startswith(('payload.', 'query.', 'self.send_json', 'json.', 'db.'))))
                    responses = list(dict.fromkeys(ast.unparse(call) for call in branch if isinstance(call, ast.Call) and ast.unparse(call.func) == 'self.send_json'))
                    verb = 'GET / HEAD' if method.name in ['handle_get', 'get_remote'] else 'POST'
                    out += ['## ' + verb + ' ' + route, '', source_link(relative, node.lineno, REFERENCE) + ' · `' + method.name + '`.', '',
                            'Условие: `' + test.replace('`', "'") + '`.', '']
                    if params:
                        out += ['Ключи payload, читаемые в ветке: ' + ', '.join('`' + value + '`' for value in params) + '.', '']
                    if query_params:
                        out += ['Ключи query, читаемые в ветке: ' + ', '.join('`' + value + '`' for value in query_params) + '.', '']
                    if responses:
                        out += ['Выражения JSON-ответа (значения раскрываются в вызываемом методе):', '', '```python', '\n'.join(value if len(value) <= 800 else value[:797] + '...' for value in responses), '```', '']
                    if calls:
                        out += ['Вызовы ветки: ' + ', '.join('`' + value + '`' for value in calls) + '.', '']
    out += ['## Специальные обработчики и ограничения перечня', '',
            'Потоковые `/api/file-upload`, `/api/calendar-telegram` и настройка Telegram обрабатываются также отдельными receive-методами до общего JSON-dispatch. `/_auth/login`, `/_auth/session`, `/_auth/logout` проверяются в `remote_access.py`. GET/POST одной строки могут иметь разные правила. Список веток не является разрешением выполнять произвольные POST.', '']
    return '\n'.join(out)


# Извлекает SQL DDL из строк исходников без подключения к рабочей SQLite.
# Динамические шаблоны отмечаются отдельно; фактические данные не читаются.
def schema_page(files):
    out = ['# SQLite: схема из исходников', '', 'Статический справочник CREATE/ALTER/INDEX/TRIGGER из собственных Python-файлов. Динамические имена и f-строки показаны как шаблоны. Наличие DDL в совместимой ветке не означает, что она исполняется в текущем режиме. [Как работает хранение](../language/sqlite.md).', '']
    for file in files:
        tree = ast.parse((ROOT / file['path']).read_text())
        snippets = []
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                template = ''.join(part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else '{' + ast.unparse(part.value) + '}' if isinstance(part, ast.FormattedValue) else '' for part in node.values)
                if re.search(r'\b(CREATE\s+(?:TABLE|TRIGGER|(?:UNIQUE\s+)?INDEX)|ALTER\s+TABLE)\b', template, re.I):
                    snippets.append((node.lineno, '-- Динамический шаблон\n' + template))
            if isinstance(node, ast.Constant) and not isinstance(parents.get(node), ast.JoinedStr) and isinstance(node.value, str) and re.search(r'\b(CREATE\s+(?:TABLE|TRIGGER|(?:UNIQUE\s+)?INDEX)|ALTER\s+TABLE)\b', node.value, re.I):
                if len(node.value) > 5000:
                    continue
                snippets.append((node.lineno, node.value))
        if snippets:
            out += ['## ' + file['path'], '']
        for line, sql in sorted(set(snippets)):
            out += [source_link(file['path'], line, REFERENCE), '', '```sql', sql.strip(), '```', '']
    return '\n'.join(out)


# Показывает входящие Python-импорты и отдельные точки запуска каждого модуля.
# Статическая связь не доказывает исполнение ветки и не разрешает удаление кода.
def usage_page(files):
    production, tests = {}, {}
    for path in sorted([*ROOT.glob('*.py'), *(ROOT / 'scripts').glob('*.py'), *(ROOT / 'tests').glob('*.py')]):
        target = tests if 'tests' in path.relative_to(ROOT).parts else production
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
            for name in names:
                target.setdefault(name.split('.')[0], set()).add(path.relative_to(ROOT).as_posix())
    out = ['# Использование модулей', '', 'Входящие импорты собственного Python, включая локальные; отдельно — тесты и прямой CLI. Это синтаксические свидетельства, а не профиль рабочего процесса. Динамические загрузки копий отката и вызовы subprocess дополнительно описаны в [старом коде](../legacy-code.md) и [архитектуре](../architecture.md).', '', '| Модуль | Импортируется рабочим кодом / утилитами | Тестовые модули | Прямой запуск |', '| --- | --- | ---: | --- |']
    for file in files:
        name = Path(file['path']).stem
        inbound = sorted(production.get(name, set()))
        direct = '__name__' in (ROOT / file['path']).read_text() and '__main__' in (ROOT / file['path']).read_text()
        out.append('| [' + file['path'] + '](python/' + reference_name(file) + ') | ' + (', '.join('`' + value + '`' for value in inbound) or 'Прямой import не найден; см. точку запуска') + ' | ' + str(len(tests.get(name, set()))) + ' | ' + ('Да' if direct else 'Нет') + ' |')
    out += ['', 'JavaScript-подключение: `static/index.html` задаёт основной порядок скриптов, `hidden-orders.html` — отдельную страницу; `spreadsheet-preview.js` создаёт Worker, `remote_access.py` добавляет скрипт входа только во внешний HTML. `calendar_delivery.py` встраивает общие модули в автономный HTML WebKit. Swift вызывается соответствующими Python-адаптерами через native_renderers, C компилируется удалённым deploy-помощником. Подробные цепочки — в [сценариях](../flows.md).', '']
    return '\n'.join(out)


# Проверяет локальные Markdown-ссылки и номера строк исходников.
# Внешние адреса и смысл пользовательских HTML-якорей здесь не проверяются.
def check_links(files):
    errors = []
    by_path = {}
    for file in files:
        by_path.setdefault((ROOT / file['path']).resolve(), []).extend(file['symbols'])
    for path in [ROOT / 'README.md', ROOT / 'mobile/README.md', *sorted((ROOT / 'docs').rglob('*.md'))]:
        content = re.sub(r'(?ms)^```[^\n]*\n.*?^```[ \t]*(?:\n|$)', '', path.read_text())
        content = re.sub(r'`[^`\n]*`', '', content)
        for label, target in re.findall(r'(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)', content):
            if re.match(r'[a-z][a-z0-9+.-]*:', target, re.I) or target.startswith('#'):
                continue
            target = target.strip('<>')
            name, _, anchor = target.partition('#')
            destination = path.parent / name
            if not destination.exists():
                errors.append(str(path.relative_to(ROOT)) + ': missing ' + target)
            elif re.fullmatch(r'L\d+', anchor):
                number = int(anchor[1:])
                if not 1 <= number <= len(destination.read_text().splitlines()):
                    errors.append(str(path.relative_to(ROOT)) + ': invalid line ' + target)
                candidates = [symbol for symbol in by_path.get(destination.resolve(), []) if symbol['name'] == label or symbol['name'] == label.rsplit('.', 1)[-1]]
                if candidates and number not in {symbol['line'] for symbol in candidates}:
                    errors.append(str(path.relative_to(ROOT)) + ': stale symbol line ' + label + ' ' + target)
    return errors


# Собирает справочники и сравнивает их с сохранённым результатом при --check.
# Меняет только docs/reference; приложение, база, документы и секреты не открываются.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--node', default=shutil.which('node'))
    parser.add_argument('--babel', help='Path to bundled Playwright lib/transform/babelBundle.js')
    args = parser.parse_args()
    if not args.node:
        parser.error('Node is required; pass --node or add the bundled runtime to PATH')
    env = dict(os.environ)
    if args.babel:
        env['MANAGER_DOCUMENTATION_BABEL'] = str(Path(args.babel).resolve())
    result = subprocess.run([args.node, str(ROOT / 'scripts/documentation_js.cjs')], capture_output=True, text=True, check=True, env=env)
    embedded = [embedded_inventory(path) for path in sorted([*ROOT.glob('*.py'), *(ROOT / 'scripts').glob('*.py'), *(ROOT / 'static').glob('*.html')])]
    groups = {'python': [python_inventory(path) for path in sorted([*ROOT.glob('*.py'), *(ROOT / 'scripts').glob('*.py')])],
              'javascript': json.loads(result.stdout),
              'native': [native_inventory(path) for path in sorted([*ROOT.glob('*.swift'), *(ROOT / 'mobile').glob('*.swift'), ROOT / 'scripts/manager_launcher.c']) if path.name not in ['CoreTests.swift', 'ProtocolProbe.swift']], 'embedded': [file for file in embedded if file['symbols']]}
    outputs = {}
    index = ['# Справочник исходников', '', 'Срез кода: **3 ноября 2026 года**. Сгенерировано `scripts/build_documentation.py` из текущего AST/объявлений и двухстрочных комментариев. [Архитектура](../architecture.md), [языки](../language/README.md), [старый код](../legacy-code.md).', '',
             '[HTTP-маршруты](http-api.md) · [SQLite DDL](sqlite-schema.md) · [использование модулей](module-usage.md) · [машинная инвентаризация](inventory.json).', '',
             'Включены собственные Python-модули и эксплуатационные скрипты, именованные JS-функции/методы, Swift-типы/методы и функции C-обёртки. Тестовые методы, vendor, анонимные callbacks и вычисляемые свойства не считаются отдельными объявлениями; тесты и встроенные HTML-сценарии объясняются в тематических документах.', '']
    manifest = {'version': 1, 'date': '2026-11-03', 'groups': {}}
    errors = []
    for group, files in groups.items():
        count = sum(len(file['symbols']) for file in files)
        index += ['## ' + {'python': 'Python', 'javascript': 'JavaScript', 'native': 'Swift и C', 'embedded': 'Встроенный JavaScript'}[group], '',
                  str(len(files)) + ' файлов; ' + str(count) + ' именованных объявлений.', '', '| Модуль | Объявлений |', '| --- | ---: |']
        manifest['groups'][group] = []
        for file in files:
            relative = group + '/' + reference_name(file)
            index.append('| [' + file['path'] + '](' + relative + ') | ' + str(len(file['symbols'])) + ' |')
            outputs[REFERENCE / relative] = module_page(file, (REFERENCE / relative).parent)
            manifest['groups'][group].append({'path': file['path'], 'sha256': hashlib.sha256((ROOT / file['path']).read_bytes()).hexdigest(), 'symbols': [{key: symbol[key] for key in ['name', 'line', 'type']} for symbol in file['symbols']]})
            for symbol in file['symbols']:
                if len(symbol['description']) != 2:
                    errors.append(file['path'] + ':' + str(symbol['line']) + ': expected two description lines')
        index.append('')
    outputs[REFERENCE / 'README.md'] = '\n'.join(index)
    outputs[REFERENCE / 'http-api.md'] = api_page()
    outputs[REFERENCE / 'sqlite-schema.md'] = schema_page(groups['python'])
    outputs[REFERENCE / 'module-usage.md'] = usage_page(groups['python'])
    outputs[REFERENCE / 'inventory.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    expected = set(outputs)
    existing = set(REFERENCE.rglob('*.md')) | set(REFERENCE.glob('*.json'))
    for path in sorted(existing - expected):
        errors.append('Unexpected reference file: ' + str(path.relative_to(ROOT)))
    for path, body in outputs.items():
        if args.check:
            if not path.exists() or path.read_text() != body:
                errors.append('Stale reference: ' + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
    errors += check_links([file for files in groups.values() for file in files])
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Documentation OK: ' + ', '.join(group + '=' + str(sum(len(file['symbols']) for file in files)) for group, files in groups.items()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
