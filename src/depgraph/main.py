"""Запуск визуализатора графа зависимостей."""

import argparse

from pydantic import ValidationError

from depgraph.apt import AptRepository
from depgraph.config import Config
from depgraph.dot import RenderError, render_png, to_dot
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
        "--reverse", action="store_true", help="нарисовать обратные зависимости"
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


def build_graph(repository: Repository, config: Config) -> DependencyGraph:
    """Строит граф зависимостей пакета, а с --reverse — обратный граф."""
    if not config.reverse:
        return DependencyGraph(config.package, repository.dependencies)
    reverse = reverse_edges(repository.names(), repository.dependencies)
    return DependencyGraph(config.package, lambda name: reverse.get(name, []))


def make_title(config: Config, version: str) -> str:
    """Возвращает подпись к картинке графа."""
    if config.reverse:
        return f"Reverse dependencies of {config.package}"
    return f"Dependencies of {config.package} {version}".rstrip()


def main() -> int:
    """Запускает программу и возвращает код завершения."""
    config = load_config()
    if config is None:
        return 1
    repository = make_repository(config)
    try:
        repository.load()
        version = repository.select(config.package, config.version)
        graph = build_graph(repository, config)
        text = to_dot(graph, make_title(config, version), config.reverse)
        print(text)
        render_png(text, config.output)
    except (RepositoryError, RenderError) as error:
        print(f"error: {error}")
        return 1
    print(f"Image saved to {config.output}, packages: {len(graph.edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
