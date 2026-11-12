"""Запуск визуализатора графа зависимостей."""

import argparse

from pydantic import ValidationError

from depgraph.apt import AptRepository
from depgraph.config import Config
from depgraph.repository import RepositoryError


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


def show_direct_dependencies(config: Config) -> int:
    """Печатает прямые зависимости пакета из репозитория Ubuntu."""
    repository = AptRepository(config.repo)
    try:
        repository.load()
        version = repository.select(config.package, config.version)
    except RepositoryError as error:
        print(f"error: {error}")
        return 1
    dependencies = repository.dependencies(config.package)
    print(f"Package: {config.package} {version}")
    print(f"Direct dependencies ({len(dependencies)}):")
    for name in dependencies:
        print(f"  {name}")
    return 0


def main() -> int:
    """Запускает программу и возвращает код завершения."""
    config = load_config()
    if config is None:
        return 1
    if config.test:
        print("error: test mode is not supported yet")
        return 1
    return show_direct_dependencies(config)


if __name__ == "__main__":
    raise SystemExit(main())
