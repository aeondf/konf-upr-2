"""Тесты обхода в ширину и графа зависимостей."""

from depgraph.graph import DependencyGraph, bfs

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
CYCLE = {"D": ["A"], "A": ["B"], "B": ["C"], "C": ["A"]}


def neighbours(edges: dict[str, list[str]]):
    """Функция соседей для словаря рёбер."""
    return lambda name: edges.get(name, [])


def test_bfs_order() -> None:
    """Обход в ширину: сначала прямые зависимости, потом их зависимости."""
    assert list(bfs("A", neighbours(DIAMOND))) == ["A", "B", "C", "D"]


def test_bfs_visits_shared_node_once() -> None:
    """Общая зависимость обрабатывается один раз."""
    calls: list[str] = []

    def counting(name: str) -> list[str]:
        calls.append(name)
        return DIAMOND[name]

    bfs("A", counting)
    assert calls.count("D") == 1


def test_bfs_stops_on_cycle() -> None:
    """Цикл не приводит к бесконечному обходу."""
    assert list(bfs("D", neighbours(CYCLE))) == ["D", "A", "B", "C"]


def test_bfs_unknown_package_is_leaf() -> None:
    """Пакет без описания — лист графа."""
    assert bfs("Z", neighbours(DIAMOND)) == {"Z": []}


def test_graph_lines() -> None:
    """Граф печатается построчно, пустые зависимости — (none)."""
    graph = DependencyGraph("A", neighbours(DIAMOND))
    assert graph.lines() == [
        "A -> B, C",
        "B -> D",
        "C -> D",
        "D -> (none)",
    ]


def test_no_cycles() -> None:
    """В ромбе циклов нет."""
    assert DependencyGraph("A", neighbours(DIAMOND)).cyclic() == []


def test_cycle_members() -> None:
    """В цикл входят A, B, C, но не D, который ведёт в цикл снаружи."""
    graph = DependencyGraph("D", neighbours(CYCLE))
    assert graph.cyclic() == ["A", "B", "C"]


def test_self_dependency() -> None:
    """Пакет, зависящий сам от себя, — тоже цикл."""
    graph = DependencyGraph("A", neighbours({"A": ["A", "B"]}))
    assert graph.cyclic() == ["A"]
