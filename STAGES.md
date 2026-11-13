# Этапы по коммитам

Каждый этап — несколько коммитов-шагов, последний закрывает этап.
Переключиться на конец этапа и вернуться обратно:

```sh
git checkout 742a862   # этап 1
git checkout 40b0ba1   # этап 2
git checkout 505b6c9   # этап 3
git checkout b963b04   # этап 4
git checkout efb2f18   # этап 5
git checkout main      # вернуться к последней версии
```

После переключения просто запускайте `./run.sh` — `uv` сам поставит
нужные зависимости. Перед переключением не должно быть
незакоммиченных изменений, иначе git откажется.

| Этап | Коммит | Что программа выводит |
|---|---|---|
| 1 | `742a862` | параметры в виде `ключ=значение` |
| 2 | `40b0ba1` | прямые зависимости пакета |
| 3 | `505b6c9` | весь граф построчно и пакеты в циклах |
| 4 | `b963b04` | то же + `--reverse`: кто зависит от пакета |
| 5 | `efb2f18` | текст на языке Graphviz + картинка PNG |

Ниже для каждого этапа: шаги (коммиты), как запустить, что видно и
что поменялось в коде.

---

## Этап 1. Параметры командной строки

```sh
git checkout 742a862
```

**Шаги:**

| Коммит | Что сделано |
|---|---|
| `cd955fc` | заготовка проекта: `pyproject.toml`, `run.sh`, ruff, pytest |
| `011a66e` | `config.py` — проверка параметров; `main.py` — печать параметров |
| `742a862` | README и `scripts/stage1.sh` |

**Как запустить:**

```sh
./run.sh --package curl --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --version 8.5.0-2ubuntu10
./run.sh --package curl --repo ftp://x
./run.sh --package curl --repo http://x --output a.jpg
sh scripts/stage1.sh
```

**Что видно:**

```
package=curl
repo=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
test=False
version=8.5.0-2ubuntu10
output=graph.png

error: repo: 'ftp://x' is not an http(s) URL
error: output: 'a.jpg' must be a .png file
```

**Код.** argparse читает параметры, pydantic их проверяет. Каждое поле
`Config` — один параметр, у каждого своя проверка:

```python
class Config(BaseModel):
    package: str
    repo: str
    test: bool = False
    version: str | None = None
    output: str = "graph.png"

    @field_validator("output")
    @classmethod
    def check_output(cls, value: str) -> str:
        path = Path(value)
        if path.suffix != IMAGE_SUFFIX:
            raise ValueError(f"output: {value!r} must be a .png file")
        ...
```

`main()` на этом этапе только печатает параметры:

```python
def main() -> int:
    config = load_config()
    if config is None:
        return 1
    for key, value in config.model_dump().items():
        print(f"{key}={value}")
    return 0
```

---

## Этап 2. Сбор данных

```sh
git checkout 40b0ba1
```

**Шаги:**

| Коммит | Что сделано |
|---|---|
| `01ea33e` | `repository.py` — общий класс репозитория; `apt.py` — скачивание и разбор индекса Ubuntu |
| `e14eeb4` | `main.py` печатает прямые зависимости вместо параметров |
| `40b0ba1` | README и `scripts/stage2.sh` |

**Как запустить** (нужен интернет):

```sh
./run.sh --package wget --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
sh scripts/stage2.sh
```

**Что видно:**

```
Package: wget 1.21.4-1ubuntu4
Direct dependencies (7):
  libc6
  libidn2-0
  libpcre2-8-0
  libpsl5t64
  libssl3t64
  libuuid1
  zlib1g
```

**Код.** Индекс скачивается `urllib` и разбирается вручную. Главное —
вытащить имена из строки `Depends`:

```python
def parse_depends(value: str) -> list[str]:
    names: list[str] = []
    for item in value.split(","):
        first = item.split("|")[0]
        name = first.split("(")[0].split(":")[0].strip()
        if name and name not in names:
            names.append(name)
    return names
```

`"libc6 (>= 2.34), libssl3 | libssl1.1"` → `["libc6", "libssl3"]`:
режем по запятым, из `a | b` берём `a`, отбрасываем `(>= ...)` и `:any`.

**Что поменялось в `main()`:** печать параметров (этап 1) заменена на
печать зависимостей — по заданию вывод параметров нужен «только для
этого этапа».

```python
# было (этап 1)
for key, value in config.model_dump().items():
    print(f"{key}={value}")

# стало (этап 2)
dependencies = repository.dependencies(config.package)
print(f"Package: {config.package} {version}")
print(f"Direct dependencies ({len(dependencies)}):")
for name in dependencies:
    print(f"  {name}")
```

---

## Этап 3. Граф, циклы, тестовый режим

```sh
git checkout 505b6c9
```

**Шаги:**

| Коммит | Что сделано |
|---|---|
| `599e5a3` | исправление: виртуальные пакеты (`libssl3`) заменяются настоящими (`libssl3t64`) через `Provides` |
| `4aa6c7e` | `graph.py` — обход в ширину и поиск циклов |
| `8ff02ab` | `file_repo.py` — тестовый репозиторий из файла, папка `repos/` |
| `a38c5e2` | `main.py` печатает весь граф и пакеты в циклах |
| `505b6c9` | README и `scripts/stage3.sh` |

**Как запустить:**

```sh
./run.sh --package wget --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
./run.sh --package A --repo repos/cycle.txt --test
sh scripts/stage3.sh
```

**Что видно:**

```
Dependency graph of wget 1.21.4-1ubuntu4:
  wget -> libc6, libidn2-0, libpcre2-8-0, libpsl5t64, libssl3t64, libuuid1, zlib1g
  libc6 -> libgcc-s1
  libidn2-0 -> libc6, libunistring5
  ...
  gcc-14-base -> (none)
Packages in cycles: libc6, libgcc-s1

Dependency graph of A:
  A -> B
  B -> C
  C -> A
Packages in cycles: A, B, C
```

**Код.** Обход в ширину без рекурсии — очередь и словарь уже
обработанных пакетов:

```python
def bfs(start: str, neighbours: Neighbours) -> dict[str, list[str]]:
    edges: dict[str, list[str]] = {}
    queue = deque([start])
    while queue:
        name = queue.popleft()
        if name in edges:
            continue
        edges[name] = neighbours(name)
        queue.extend(edges[name])
    return edges
```

`if name in edges: continue` — защита от циклов: пакет, который уже
обработан, второй раз не раскрывается.

Тестовый режим — второй вид репозитория с теми же методами, что у
`AptRepository`. Поэтому `main()` не важно, откуда берутся данные:

```python
def make_repository(config: Config) -> Repository:
    if config.test:
        return FileRepository(config.repo)
    return AptRepository(config.repo)
```

**Что поменялось в `main()`:** вместо прямых зависимостей — весь граф.

```python
# было (этап 2)
dependencies = repository.dependencies(config.package)
for name in dependencies:
    print(f"  {name}")

# стало (этап 3)
graph = DependencyGraph(package, repository.dependencies)
for line in graph.lines():
    print(f"  {line}")
cyclic = graph.cyclic()
if cyclic:
    print(f"Packages in cycles: {', '.join(cyclic)}")
```

---

## Этап 4. Обратные зависимости

```sh
git checkout b963b04
```

**Шаги:**

| Коммит | Что сделано |
|---|---|
| `70273a7` | `graph.py` — функция `reverse_edges`, переворачивает рёбра |
| `0225b1d` | параметр `--reverse` в `main.py` |
| `b963b04` | README и `scripts/stage4.sh` |

**Как запустить:**

```sh
./run.sh --package D --repo repos/diamond.txt --test --reverse
./run.sh --package curl --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --reverse
sh scripts/stage4.sh
```

**Что видно:**

```
Reverse dependencies of D (3):
  D <- B, C
  B <- A
  C <- A
  A <- (none)
```

**Код.** Рёбра переворачиваются, а обход — тот же `bfs` из этапа 3:

```python
def reverse_edges(names: list[str], neighbours: Neighbours) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {}
    for name in names:
        for dependency in neighbours(name):
            reverse.setdefault(dependency, []).append(name)
    return reverse
```

```python
reverse = reverse_edges(repository.names(), repository.dependencies)
graph = DependencyGraph(package, lambda name: reverse.get(name, []))
```

**Что поменялось в `main()`:** появилась развилка.

```python
if config.reverse:
    show_reverse(repository, config.package)
else:
    show_graph(repository, config.package, version)
```

---

## Этап 5. Визуализация

```sh
git checkout efb2f18
```

**Шаги:**

| Коммит | Что сделано |
|---|---|
| `cd085f7` | `dot.py` — текст на языке Graphviz и сохранение PNG |
| `fd18114` | `main.py` печатает текст Graphviz и сохраняет картинку вместо списков |
| `85845cf` | `scripts/stage5.sh` и картинки в `examples/` |
| `edad2bf` | `scripts/compare.sh` — сравнение с `apt-cache` и `debtree` |
| `efb2f18` | README: визуализация и сравнение |
| `c8883ac` | у репозитория появился метод `version(name)` — версия пакета |
| `0c93123` | версии пакетов на картинке: подпись узла `имя` + `версия` |
| `e76f3aa` | картинки в `examples/` перерисованы с версиями |

**Как запустить** (нужен Graphviz: `brew install graphviz`):

```sh
./run.sh --package A --repo repos/diamond.txt --test --output diamond.png
open diamond.png
./run.sh --package wget --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --output wget.png
sh scripts/stage5.sh     # картинки jq, wget, curl в examples/
sh scripts/compare.sh    # сравнение со штатными инструментами (нужен Docker)
```

**Что видно:**

```
digraph dependencies {
    label="Dependencies of A";
    labelloc=t;
    node [shape=box, style=rounded];
    "A" [style="rounded,filled", fillcolor=lightblue];
    "B";
    "C";
    "D";
    "A" -> "B";
    "A" -> "C";
    "B" -> "D";
    "C" -> "D";
}
Image saved to diamond.png, packages: 4
```

и файл `diamond.png` с картинкой. У тестовых пакетов версий нет, а у
реальных версия пишется в узле под именем:

```
    "wget" [label="wget\n1.21.4-1ubuntu4", style="rounded,filled", fillcolor=lightblue];
    "libc6" [label="libc6\n2.39-0ubuntu8", color=red];
```

**Код.** Каждый пакет — строка-узел, каждая зависимость — строка-стрелка:

```python
def to_dot(graph: DependencyGraph, title: str, reverse: bool = False) -> str:
    cyclic = graph.cyclic()
    lines = ["digraph dependencies {", f'    label="{title}";', ...]
    for name in graph.edges:
        lines.append(f'    "{name}"{node_style(name, graph.root, cyclic)};')
    for name, neighbours in graph.edges.items():
        for other in neighbours:
            source, target = (other, name) if reverse else (name, other)
            lines.append(f'    "{source}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines)
```

Версию пакета знает репозиторий — у реального это поле `Version` из
индекса, у тестового версий нет:

```python
class AptRepository(Repository):
    def version(self, name: str) -> str:
        versions = self.packages.get(name)
        if not versions:
            return ""
        return versions[-1].get("Version", "")


class FileRepository(Repository):
    def version(self, name: str) -> str:
        return ""
```

`main()` собирает версии всех пакетов графа и передаёт их в `to_dot`,
а там версия становится второй строкой подписи узла:

```python
versions = {name: repository.version(name) for name in graph.edges}
text = to_dot(graph, title, versions, config.reverse)
```

```python
if version:
    styles.append(f'label="{name}\\n{version}"')
```

Картинку рисует программа `dot` из Graphviz:

```python
subprocess.run(["dot", "-Tpng", "-o", output], input=text, ...)
```

**Что поменялось в `main()`:** вывод построчно (этапы 3–4) заменён на
текст Graphviz и картинку. `--reverse` остался — теперь он рисует
обратный граф. Метод `lines()` больше не нужен и удалён.

```python
# было (этапы 3–4)
for line in graph.lines(arrow):
    print(f"  {line}")

# стало (этап 5)
versions = {name: repository.version(name) for name in graph.edges}
text = to_dot(graph, make_title(config, version), versions, config.reverse)
print(text)
render_png(text, config.output)
```
