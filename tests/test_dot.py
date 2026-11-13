"""Тесты описания графа на языке Graphviz и сохранения PNG."""

import shutil
from pathlib import Path

import pytest

from depgraph.dot import RenderError, render_png, to_dot
from depgraph.graph import DependencyGraph, reverse_edges

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
CYCLE = {"D": ["A"], "A": ["B"], "B": ["C"], "C": ["A"]}
PNG_SIGNATURE = b"\x89PNG"

needs_graphviz = pytest.mark.skipif(
    shutil.which("dot") is None, reason="Graphviz is not installed"
)


def neighbours(edges: dict[str, list[str]]):
    """Функция соседей для словаря рёбер."""
    return lambda name: edges.get(name, [])


def test_diamond_to_dot() -> None:
    """Каждый пакет — узел, каждая зависимость — стрелка."""
    graph = DependencyGraph("A", neighbours(DIAMOND))
    assert to_dot(graph, "Dependencies of A") == "\n".join(
        [
            "digraph dependencies {",
            '    label="Dependencies of A";',
            "    labelloc=t;",
            "    node [shape=box, style=rounded];",
            '    "A" [style="rounded,filled", fillcolor=lightblue];',
            '    "B";',
            '    "C";',
            '    "D";',
            '    "A" -> "B";',
            '    "A" -> "C";',
            '    "B" -> "D";',
            '    "C" -> "D";',
            "}",
        ]
    )


def test_cycle_nodes_are_red() -> None:
    """Пакеты в цикле красные, D ведёт в цикл снаружи и остаётся обычным."""
    text = to_dot(DependencyGraph("D", neighbours(CYCLE)), "cycle")
    assert '    "A" [color=red];' in text
    assert '    "C" -> "A";' in text
    assert '    "D" [style="rounded,filled", fillcolor=lightblue];' in text


def test_root_in_cycle() -> None:
    """Корень, который зависит сам от себя, и закрашен, и красный."""
    graph = DependencyGraph("A", neighbours({"A": ["A"]}))
    text = to_dot(graph, "self")
    assert "fillcolor=lightblue, color=red];" in text
    assert '    "A" -> "A";' in text


def test_package_without_dependencies() -> None:
    """Пакет без зависимостей рисуется одним узлом без стрелок."""
    text = to_dot(DependencyGraph("D", neighbours(DIAMOND)), "D")
    assert '    "D" [style="rounded,filled", fillcolor=lightblue];' in text
    assert "->" not in text


def test_reverse_arrows_point_to_dependency() -> None:
    """В обратном графе стрелка всё равно идёт от пакета к его зависимости."""
    reverse = reverse_edges(list(DIAMOND), neighbours(DIAMOND))
    graph = DependencyGraph("D", neighbours(reverse))
    text = to_dot(graph, "Reverse dependencies of D", reverse=True)
    assert '    "B" -> "D";' in text
    assert '    "A" -> "C";' in text
    assert '    "D" -> "B";' not in text


def test_versions_in_labels() -> None:
    """Версия пишется в узле второй строкой под именем пакета."""
    graph = DependencyGraph("A", neighbours(DIAMOND))
    text = to_dot(graph, "A", {"A": "1.0", "B": "2.0-1"})
    assert '    "A" [label="A\\n1.0", style="rounded,filled"' in text
    assert '    "B" [label="B\\n2.0-1"];' in text
    assert '    "C";' in text


@needs_graphviz
def test_render_png(tmp_path: Path) -> None:
    """Graphviz сохраняет настоящий PNG-файл."""
    output = tmp_path / "graph.png"
    graph = DependencyGraph("A", neighbours(DIAMOND))
    render_png(to_dot(graph, "Dependencies of A"), str(output))
    assert output.read_bytes().startswith(PNG_SIGNATURE)


@needs_graphviz
def test_render_bad_text(tmp_path: Path) -> None:
    """Ошибка в тексте графа — понятная ошибка, а не падение программы."""
    with pytest.raises(RenderError, match="dot failed"):
        render_png("digraph {", str(tmp_path / "graph.png"))


def test_render_without_graphviz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Если Graphviz не установлен, программа так и говорит."""
    monkeypatch.setattr("depgraph.dot.shutil.which", lambda _: None)
    with pytest.raises(RenderError, match="not installed"):
        render_png("digraph {}", str(tmp_path / "graph.png"))
