# scripts/build_documentation.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/build_documentation.py](../../../scripts/build_documentation.py).

Build/check source reference without importing the application or opening data.

Импорты Python, включая локальные: `argparse`, `ast`, `hashlib`, `json`, `os`, `pathlib`, `re`, `shutil`, `subprocess`, `sys`, `urllib.parse`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-api_page"></a>

## api_page

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def api_page(files):
```

Извлекает ветки HTTP-маршрутов из фактических сравнений route/path.

Не принимает упоминание API в сообщении или защите Origin за отдельный маршрут.

Непосредственные вызовы: `next`, `(ROOT / relative).read_text`, `ast.parse`, `ast.walk`, `isinstance`, `set`, `ast.unparse`, `re.search`, `sorted`, `value.value.startswith`, `seen.add`, `list`, `dict.fromkeys`, `ast.unparse(call.func).startswith`, `owner_link`, `test.replace`, `', '.join`, `'\n'.join`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join(out)
```

<a id="symbol-check_links"></a>

## check_links

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def check_links(files):
```

Проверяет локальные файлы и устойчивые ссылки на существующие объявления.

Старые #L разрешены только в истории; внешние адреса и прочие heading-якоря не проверяются.

Непосредственные вызовы: `by_reference.setdefault((REFERENCE / file['reference']).resolve(), set()).update`, `by_reference.setdefault`, `(REFERENCE / file['reference']).resolve`, `set`, `sorted`, `(ROOT / 'docs').rglob`, `re.sub`, `path.read_text`, `re.findall`, `re.match`, `target.strip`, `target.partition`, `destination.exists`, `errors.append`, `str`, `path.relative_to`, `re.fullmatch`, `int`, `len`, `destination.read_text().splitlines`, `destination.read_text`, `anchor.startswith`, `by_reference.get`, `destination.resolve`.

Выражения возврата (ветки читаются в исходнике):

```python
errors
```

<a id="symbol-collect_inventory"></a>

## collect_inventory

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def collect_inventory(node, babel=None):
```

Собирает текущие объявления всех поддерживаемых языков без исполнения приложения.

Физические строки остаются в памяти для ошибок, владельцев веток и команды --locate.

Непосредственные вызовы: `dict`, `str`, `Path(babel).resolve`, `Path`, `subprocess.run`, `embedded_inventory`, `sorted`, `ROOT.glob`, `(ROOT / 'scripts').glob`, `(ROOT / 'static').glob`, `python_inventory`, `json.loads`, `native_inventory`, `(ROOT / 'mobile').glob`, `groups.items`, `prepare_reference`.

Выражения возврата (ветки читаются в исходнике):

```python
groups
```

<a id="symbol-description"></a>

## description

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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

<a id="symbol-embedded_inventory"></a>

## embedded_inventory

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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

<a id="symbol-facts"></a>

## facts

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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

<a id="symbol-inventory_json"></a>

## inventory_json

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def inventory_json(groups):
```

Записывает компактный индекс объявлений: один символ на строку JSON.

Индекс не содержит физических строк, дат сборки или хешей целых исходников.

Непосредственные вызовы: `enumerate`, `groups.items`, `out.append`, `json.dumps`, `len`, `'\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join([*out, '  }', '}', ''])
```

<a id="symbol-main"></a>

## main

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def main():
```

Собирает справочники и сравнивает их с сохранённым результатом при --check.

Меняет только docs/reference; --locate печатает текущую позицию символа без записи файлов.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_mutually_exclusive_group`, `mode.add_argument`, `parser.add_argument`, `shutil.which`, `parser.parse_args`, `parser.error`, `collect_inventory`, `args.locate.partition`, `groups.values`, `print`, `str`, `groups.items`, `sum`, `len`, `index.append`, `module_page`, `errors.append`, `'\n'.join`, `api_page`, `schema_page`, `usage_page`, `inventory_json`, `set`, `REFERENCE.rglob`, `REFERENCE.glob`, `sorted`, `path.relative_to`, `outputs.items`, `path.exists`, `path.read_text`, `path.parent.mkdir`, `path.write_text`, `check_links`, `', '.join`.

Выражения возврата (ветки читаются в исходнике):

```python
0
1
```

<a id="symbol-module_page"></a>

## module_page

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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

<a id="symbol-native_inventory"></a>

## native_inventory

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def native_inventory(path):
```

Перечисляет объявления Swift и C по поддерживаемым формам проекта.

Свойства, верхнеуровневые операторы и анонимные замыкания описываются у владельца.

Непосредственные вызовы: `path.read_text().splitlines`, `path.read_text`, `enumerate`, `NATIVE_PATTERN.match`, `re.match`, `len`, `match[1].expandtabs`, `parents.pop`, `line.strip`, `lines[following].strip`, `symbols.append`, `'.'.join`, `signature.split`, `description`, `parents.append`, `path.relative_to(ROOT).as_posix`, `path.relative_to`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': path.relative_to(ROOT).as_posix(), 'symbols': symbols}
```

<a id="symbol-own_nodes"></a>

## own_nodes

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def own_nodes(node):
```

Обходит тело одного объявления без включения тел вложенных функций и классов.

Это синтаксический анализ непосредственных операций, а не динамический call graph.

Непосредственные вызовы: `ast.iter_child_nodes`, `isinstance`, `own_nodes`.

<a id="symbol-owner_link"></a>

## owner_link

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def owner_link(file, line, folder):
```

Находит ближайшее объявление, которому принадлежит HTTP-ветка или SQL-строка.

Физические координаты используются только во время разбора и не попадают в справочник.

Непосредственные вызовы: `symbol.get`, `source_link`, `max`, `reference_link`.

Выражения возврата (ветки читаются в исходнике):

```python
source_link(file['path'], folder)
reference_link(file, symbol, folder)
```

<a id="symbol-prepare_reference"></a>

## prepare_reference

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def prepare_reference(file, group):
```

Назначает объявлениям постоянные якоря и порядок независимо от позиции в исходнике.

Одноимённые перегрузки различаются сигнатурой; строки и хеш целого файла не сохраняются.

Непосредственные вызовы: `reference_name`, `counts.get`, `set`, `quote`, `re.sub`, `hashlib.sha256(signature.encode()).hexdigest`, `hashlib.sha256`, `signature.encode`, `ValueError`, `anchors.add`, `file['symbols'].sort`.

Явные исключения: `ValueError`.

<a id="symbol-python_inventory"></a>

## python_inventory

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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

<a id="symbol-python_inventory.Visitor"></a>

## python_inventory.Visitor

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `class`.

```python
class Visitor(ast.NodeVisitor):
```

Сохраняет квалифицированные имена методов и вложенных Python-функций.

Стек родителей разделяет одинаковые короткие имена разных классов.

<a id="symbol-python_inventory.Visitor.__init__"></a>

## python_inventory.Visitor.__init__

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def __init__(self):
```

Создаёт пустой стек области видимости анализируемого файла.

Внешняя коллекция symbols получает результаты обхода.

Прямые присваивания полям/свойствам: `self.parents`.

<a id="symbol-python_inventory.Visitor.visit_definition"></a>

## python_inventory.Visitor.visit_definition

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def visit_definition(self, node):
```

Регистрирует объявление и затем обходит его вложенные области.

Сигнатура берётся из AST, номера строк — из текущего исходника.

Непосредственные вызовы: `min`, `getattr`, `isinstance`, `', '.join`, `ast.unparse`, `symbols.append`, `'.'.join`, `description`, `facts`, `self.parents.append`, `self.generic_visit`, `self.parents.pop`.

<a id="symbol-reference_link"></a>

## reference_link

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def reference_link(file, symbol, folder):
```

Создаёт ссылку на постоянный якорь описания функции или класса.

Имя и якорь берутся из текущей инвентаризации, без сохранённых координат исходника.

Непосредственные вызовы: `os.path.relpath`.

Выражения возврата (ветки читаются в исходнике):

```python
'[' + symbol['name'] + '](' + target + '#' + symbol['anchor'] + ')'
```

<a id="symbol-reference_name"></a>

## reference_name

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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

<a id="symbol-schema_page"></a>

## schema_page

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def schema_page(files):
```

Извлекает SQL DDL из строк исходников без подключения к рабочей SQLite.

Динамические шаблоны отмечаются отдельно; фактические данные не читаются.

Непосредственные вызовы: `ast.parse`, `(ROOT / file['path']).read_text`, `ast.walk`, `ast.iter_child_nodes`, `isinstance`, `''.join`, `ast.unparse`, `re.search`, `snippets.append`, `parents.get`, `len`, `sorted`, `owner_link`, `sql.strip`, `'\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
'\n'.join(out)
```

<a id="symbol-source_link"></a>

## source_link

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

```python
def source_link(path, folder):
```

Создаёт относительную Markdown-ссылку на исходный файл без физической строки.

Точное объявление определяется именем в справочнике или командой --locate.

Непосредственные вызовы: `os.path.relpath`.

Выражения возврата (ветки читаются в исходнике):

```python
'[' + path + '](' + target + ')'
```

<a id="symbol-usage_page"></a>

## usage_page

[scripts/build_documentation.py](../../../scripts/build_documentation.py) · `function`.

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
