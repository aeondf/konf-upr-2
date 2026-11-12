"""Запуск визуализатора графа зависимостей."""

import argparse

from pydantic import ValidationError

from depgraph.apt import AptRepository
from depgraph.config import Config
from depgraph.file_repo import FileRepository
from depgraph.graph import DependencyGraph, reverse_edges
from depgraph.repository import Repository, RepositoryError


def parse_arguments() -> argparse.Namespace:
    """Читает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Граф зависимостей пакетов Ubuntu (apt)"
    )
    parser.add_argument("--package", required=True, help="имя пакета")
    parser.add_argument(
        "--repo",
        required=True,
        help="URL файла Packages или путь к тестовому репозиторию",
    )
    parser.add_argument(
        "--test", action="store_true", help="режим тестового репозитория"
    )
    parser.add_argument("--version", help="версия пакета")
    parser.add_argument(
        "--output", default="graph.png", help="файл с изображением графа"
    )
    parser.add_argument(
        "--reverse", action="store_true", help="показать обратные зависимости"
    )
    return parser.parse_args()


def load_config() -> Config | None:
    """Проверяет параметры; при ошибке печатает её и возвращает None."""
    args = parse_arguments()
    try:
        return Config(**vars(args))
    except ValidationError as error:
        for item in error.errors():
            print(f"error: {item['msg'].removeprefix('Value error, ')}")
        return None


def make_repository(config: Config) -> Repository:
    """Создаёт тестовый или настоящий репозиторий в зависимости от режима."""
    if config.test:
        return FileRepository(config.repo)
    return AptRepository(config.repo)


def print_graph(title: str, graph: DependencyGraph, arrow: str) -> None:
    """Печатает заголовок, граф построчно и пакеты в циклах."""
    print(title)
    for line in graph.lines(arrow):
        print(f"  {line}")
    cyclic = graph.cyclic()
    if cyclic:
        print(f"Packages in cycles: {', '.join(cyclic)}")


def show_graph(repository: Repository, package: str, version: str) -> None:
    """Печатает граф зависимостей пакета."""
    graph = DependencyGraph(package, repository.dependencies)
    title = f"Dependency graph of {package} {version}".rstrip() + ":"
    print_graph(title, graph, "->")


def show_reverse(repository: Repository, package: str) -> None:
    """Печатает пакеты, которые прямо или через другие зависят от package."""
    reverse = reverse_edges(repository.names(), repository.dependencies)
    graph = DependencyGraph(package, lambda name: reverse.get(name, []))
    title = f"Reverse dependencies of {package} ({len(graph.edges) - 1}):"
    print_graph(title, graph, "<-")


def main() -> int:
    """Запускает программу и возвращает код завершения."""
    config = load_config()
    if config is None:
        return 1
    repository = make_repository(config)
    try:
        repository.load()
        version = repository.select(config.package, config.version)
    except RepositoryError as error:
        print(f"error: {error}")
        return 1
    if config.reverse:
        show_reverse(repository, config.package)
    else:
        show_graph(repository, config.package, version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
