"""Граф зависимостей и обход в ширину."""

from collections import deque
from collections.abc import Callable

Neighbours = Callable[[str], list[str]]


def bfs(start: str, neighbours: Neighbours) -> dict[str, list[str]]:
    """Обходит граф в ширину без рекурсии; возвращает найденные рёбра."""
    edges: dict[str, list[str]] = {}
    queue = deque([start])
    while queue:
        name = queue.popleft()
        if name in edges:
            continue
        edges[name] = neighbours(name)
        queue.extend(edges[name])
    return edges


class DependencyGraph:
    """Граф зависимостей: пакет → пакеты, от которых он зависит."""

    def __init__(self, root: str, neighbours: Neighbours) -> None:
        """Строит граф от пакета root обходом в ширину."""
        self.root = root
        self.edges = bfs(root, neighbours)

    def lines(self) -> list[str]:
        """Возвращает граф построчно: «пакет -> зависимости»."""
        result = []
        for name, dependencies in self.edges.items():
            targets = ", ".join(dependencies) if dependencies else "(none)"
            result.append(f"{name} -> {targets}")
        return result

    def cyclic(self) -> list[str]:
        """Возвращает пакеты, которые через зависимости ведут сами к себе."""
        return [
            name
            for name, dependencies in self.edges.items()
            if any(name in bfs(dep, self._next) for dep in dependencies)
        ]

    def _next(self, name: str) -> list[str]:
        return self.edges.get(name, [])
