# scripts/build_documentation.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/build_documentation.py:1](../../../scripts/build_documentation.py#L1).

Build/check source reference without importing the application or opening data.

Импорты Python, включая локальные: `argparse`, `ast`, `hashlib`, `json`, `os`, `pathlib`, `re`, `shutil`, `subprocess`, `sys`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## description

[scripts/build_documentation.py:21](../../../scripts/build_documentation.py#L21) · `function`.

```python
def description(lines, start, prefix):
```

Возвращает две строки назначения перед объявлением Python или нативного кода.

Декораторы учитываются вызывающим кодом; старые docstring не подменяются.

Непосредственные вызовы: `max`, `len`, `all`, `line.strip().startswith`, `line.strip`, `line.strip()[len(prefix):].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
[line.strip()[len(prefix):].strip() for line in before] if len(before) == 2 and all((line.strip().startswith(prefix + ' ') for line in before)) else []
```

## own_nodes

[scripts/build_documentation.py:28](../../../scripts/build_documentation.py#L28) · `function`.

```python
def own_nodes(node):
```

Обходит тело одного объявления без включения тел вложенных функций и классов.

Это синтаксический анализ непосредственных операций, а не динамический call graph.

Непосредственные вызовы: `ast.iter_child_nodes`, `isinstance`, `own_nodes`.

## facts

[scripts/build_documentation.py:38](../../../scripts/build_documentation.py#L38) · `function`.

```python
def facts(node):
```

Собирает вызовы, return, raise и прямые присваивания полям Python-объявления.

Ограничение вложенных тел не приписывает их операции внешнему владельцу.

Непосредственные вызовы: `own_nodes`, `isinstance`, `calls.append`, `ast.unparse`, `returns.append`, `raises.append`, `list`, `dict.fromkeys`.

Выражения возврата (ветки читаются в исходнике):

```python
{key: list(dict.fromkeys(values)) for (key, values) in [('calls', calls), ('returns', returns), ('raises', raises), ('writes', writes)]}
```

## python_inventory

[scripts/build_documentation.py:55](../../../scripts/build_documentation.py#L55) · `function`.

```python
def python_inventory(path):
```

Строит инвентаризацию всех именованных объявлений собственного Python-файла.

Читает AST и комментарии, но не исполняет модуль и его конфигурацию.

Непосредственные вызовы: `path.read_text`, `source.splitlines`, `ast.parse`, `Visitor().visit`, `Visitor`, `sorted`, `ast.walk`, `isinstance`, `path.relative_to(ROOT).as_posix`, `path.relative_to`, `ast.get_docstring`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path.relative_to(ROOT).as_posix(), 'summary': ast.get_docstring(tree) or '', 'imports': imports, 'symbols': symbols}
```

## python_inventory.Visitor

[scripts/build_documentation.py:63](../../../scripts/build_documentation.py#L63) · `class`.

```python
class Visitor(ast.NodeVisitor):
```

Сохраняет квалифицированные имена методов и вложенных Python-функций.

Стек родителей разделяет одинаковые короткие имена разных классов.

## python_inventory.Visitor.__init__

[scripts/build_documentation.py:66](../../../scripts/build_documentation.py#L66) · `function`.

```python
def __init__(self):
```

Создаёт пустой стек области видимости анализируемого файла.

Внешняя коллекция symbols получает результаты обхода.

Прямые присваивания полям/свойствам: `self.parents`.

## python_inventory.Visitor.visit_definition

[scripts/build_documentation.py:71](../../../scripts/build_documentation.py#L71) · `function`.

```python
def visit_definition(self, node):
```

Регистрирует объявление и затем обходит его вложенные области.

Сигнатура берётся из AST, номера строк — из текущего исходника.

Непосредственные вызовы: `min`, `getattr`, `isinstance`, `', '.join`, `ast.unparse`, `symbols.append`, `'.'.join`, `description`, `facts`, `self.parents.append`, `self.generic_visit`, `self.parents.pop`.

## native_inventory

[scripts/build_documentation.py:93](../../../scripts/build_documentation.py#L93) · `function`.

```python
def native_inventory(path):
```

Перечисляет объявления Swift и C по поддерживаемым формам проекта.

Свойства, верхнеуровневые операторы и анонимные замыкания описываются у владельца.

Непосредственные вызовы: `path.read_text().splitlines`, `path.read_text`, `enumerate`, `NATIVE_PATTERN.match`, `re.match`, `line.strip`, `len`, `lines[following].strip`, `symbols.append`, `signature.split`, `description`, `path.relative_to(ROOT).as_posix`, `path.relative_to`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path.relative_to(ROOT).as_posix(), 'symbols': symbols}
```

## embedded_inventory

[scripts/build_documentation.py:114](../../../scripts/build_documentation.py#L114) · `function`.

```python
def embedded_inventory(path):
```

Находит именованные JS-функции, встроенные в HTML-шаблоны Python/HTML.

Анонимные обработчики относятся к владельцу, строки кода не исполняются.

Непосредственные вызовы: `path.read_text().splitlines`, `path.read_text`, `enumerate`, `re.match`, `symbols.append`, `line.strip().split`, `line.strip`, `description`, `path.relative_to(ROOT).as_posix`, `path.relative_to`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path.relative_to(ROOT).as_posix(), 'summary': 'JavaScript внутри автономного HTML-шаблона; контекст данных и запуск описаны у Python-владельца.', 'symbols': symbols}
```

## reference_name

[scripts/build_documentation.py:127](../../../scripts/build_documentation.py#L127) · `function`.

```python
def reference_name(file):
```

Формирует стабильное имя справочника отдельного исходного файла.

Префикс scripts/mobile исключает совпадения одинаковых базовых имён.

Непосредственные вызовы: `file['path'].rsplit('.', 1)[0].replace`, `file['path'].rsplit`.

Выражения возврата (ветки читаются в исходнике):

```python
file['path'].rsplit('.', 1)[0].replace('/', '-') + '.md'
```

## source_link

[scripts/build_documentation.py:133](../../../scripts/build_documentation.py#L133) · `function`.

```python
def source_link(path, line, folder):
```

Создаёт относительную Markdown-ссылку на файл и фактическую строку кода.

Номер проверяется по текущей инвентаризации, а не по прежнему снимку.

Непосредственные вызовы: `os.path.relpath`, `str`.

Выражения возврата (ветки читаются в исходнике):

```python
'[' + path + ':' + str(line) + '](' + target + '#L' + str(line) + ')'
```

## module_page

[scripts/build_documentation.py:140](../../../scripts/build_documentation.py#L140) · `function`.

```python
def module_page(file, folder):
```

Строит страницу справочника одного модуля по его текущим объявлениям.

Вызовы и return представлены как синтаксические сведения с явными пределами.

Непосредственные вызовы: `source_link`, `file.get`, `', '.join`, `file['path'].endswith`, `'\n\n'.join`, `symbol.get`, `value.replace`, `'\n'.join`, `len`, `'\n'.join(out).rstrip`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join(out).rstrip() + '\n'
```

## api_page

[scripts/build_documentation.py:167](../../../scripts/build_documentation.py#L167) · `function`.

```python
def api_page():
```

Извлекает ветки HTTP-маршрутов из фактических сравнений route/path.

Не принимает упоминание API в сообщении или защите Origin за отдельный маршрут.

Непосредственные вызовы: `(ROOT / relative).read_text`, `ast.parse`, `ast.walk`, `isinstance`, `set`, `ast.unparse`, `re.search`, `sorted`, `value.value.startswith`, `seen.add`, `list`, `dict.fromkeys`, `ast.unparse(call.func).startswith`, `source_link`, `test.replace`, `', '.join`, `'\n'.join`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join(out)
```

## schema_page

[scripts/build_documentation.py:210](../../../scripts/build_documentation.py#L210) · `function`.

```python
def schema_page(files):
```

Извлекает SQL DDL из строк исходников без подключения к рабочей SQLite.

Динамические шаблоны отмечаются отдельно; фактические данные не читаются.

Непосредственные вызовы: `ast.parse`, `(ROOT / file['path']).read_text`, `ast.walk`, `ast.iter_child_nodes`, `isinstance`, `''.join`, `ast.unparse`, `re.search`, `snippets.append`, `parents.get`, `len`, `sorted`, `set`, `source_link`, `sql.strip`, `'\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join(out)
```

## usage_page

[scripts/build_documentation.py:234](../../../scripts/build_documentation.py#L234) · `function`.

```python
def usage_page(files):
```

Показывает входящие Python-импорты и отдельные точки запуска каждого модуля.

Статическая связь не доказывает исполнение ветки и не разрешает удаление кода.

Непосредственные вызовы: `sorted`, `ROOT.glob`, `(ROOT / 'scripts').glob`, `(ROOT / 'tests').glob`, `path.relative_to`, `ast.parse`, `path.read_text`, `ast.walk`, `isinstance`, `target.setdefault(name.split('.')[0], set()).add`, `target.setdefault`, `name.split`, `set`, `path.relative_to(ROOT).as_posix`, `Path`, `production.get`, `(ROOT / file['path']).read_text`, `out.append`, `reference_name`, `', '.join`, `str`, `len`, `tests.get`, `'\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join(out)
```

## check_links

[scripts/build_documentation.py:255](../../../scripts/build_documentation.py#L255) · `function`.

```python
def check_links(files):
```

Проверяет локальные Markdown-ссылки и номера строк исходников.

Внешние адреса и смысл пользовательских HTML-якорей здесь не проверяются.

Непосредственные вызовы: `by_path.setdefault((ROOT / file['path']).resolve(), []).extend`, `by_path.setdefault`, `(ROOT / file['path']).resolve`, `sorted`, `(ROOT / 'docs').rglob`, `re.sub`, `path.read_text`, `re.findall`, `re.match`, `target.startswith`, `target.strip`, `target.partition`, `destination.exists`, `errors.append`, `str`, `path.relative_to`, `re.fullmatch`, `int`, `len`, `destination.read_text().splitlines`, `destination.read_text`, `by_path.get`, `destination.resolve`, `label.rsplit`.

Выражения возврата (ветки читаются в исходнике):

```python
errors
```

## main

[scripts/build_documentation.py:283](../../../scripts/build_documentation.py#L283) · `function`.

```python
def main():
```

Собирает справочники и сравнивает их с сохранённым результатом при --check.

Меняет только docs/reference; приложение, база, документы и секреты не открываются.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_argument`, `shutil.which`, `parser.parse_args`, `parser.error`, `dict`, `str`, `Path(args.babel).resolve`, `Path`, `subprocess.run`, `embedded_inventory`, `sorted`, `ROOT.glob`, `(ROOT / 'scripts').glob`, `(ROOT / 'static').glob`, `python_inventory`, `json.loads`, `native_inventory`, `(ROOT / 'mobile').glob`, `groups.items`, `sum`, `len`, `reference_name`, `index.append`, `module_page`, `manifest['groups'][group].append`, `hashlib.sha256((ROOT / file['path']).read_bytes()).hexdigest`, `hashlib.sha256`, `(ROOT / file['path']).read_bytes`, `errors.append`, `'\n'.join`, `api_page`, `schema_page`, `usage_page`, `json.dumps`, `set`, `REFERENCE.rglob`, `REFERENCE.glob`, `path.relative_to`, `outputs.items`, `path.exists`, `path.read_text`, `path.parent.mkdir`, `path.write_text`, `check_links`, `groups.values`, `print`, `', '.join`.

Выражения возврата (ветки читаются в исходнике):

```python
1
0
```
