"""Описание графа на языке Graphviz и сохранение картинки в PNG."""

import shutil
import subprocess

from depgraph.graph import DependencyGraph


class RenderError(Exception):
    """Ошибка при рисовании картинки графа."""


def node_style(name: str, version: str, root: str, cyclic: list[str]) -> str:
    """Возвращает оформление узла: версия, закрашенный корень, красный цикл."""
    styles = []
    if version:
        styles.append(f'label="{name}\\n{version}"')
    if name == root:
        styles.append('style="rounded,filled", fillcolor=lightblue')
    if name in cyclic:
        styles.append("color=red")
    return f" [{', '.join(styles)}]" if styles else ""


def to_dot(
    graph: DependencyGraph,
    title: str,
    versions: dict[str, str] | None = None,
    reverse: bool = False,
) -> str:
    """Описывает граф на языке Graphviz: узлы — пакеты, стрелки — связи."""
    versions = versions or {}
    cyclic = graph.cyclic()
    lines = [
        "digraph dependencies {",
        f'    label="{title}";',
        "    labelloc=t;",
        "    node [shape=box, style=rounded];",
    ]
    for name in graph.edges:
        style = node_style(name, versions.get(name, ""), graph.root, cyclic)
        lines.append(f'    "{name}"{style};')
    for name, neighbours in graph.edges.items():
        for other in neighbours:
            source, target = (other, name) if reverse else (name, other)
            lines.append(f'    "{source}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines)


def render_png(text: str, output: str) -> None:
    """Рисует граф программой dot из Graphviz и сохраняет его в PNG."""
    if shutil.which("dot") is None:
        raise RenderError("Graphviz is not installed: command 'dot' not found")
    result = subprocess.run(
        ["dot", "-Tpng", "-o", output],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RenderError(f"dot failed: {result.stderr.strip()}")
