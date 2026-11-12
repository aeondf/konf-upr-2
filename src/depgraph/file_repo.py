"""Тестовый репозиторий: граф пакетов из текстового файла."""

import re
from pathlib import Path

from depgraph.repository import Repository, RepositoryError

NAME = re.compile(r"[A-Z]+")


class FileRepository(Repository):
    """Пакеты с именами из заглавных латинских букв, описанные в файле."""

    def __init__(self, path: str) -> None:
        """Запоминает путь к файлу описания графа."""
        self.path = Path(path)
        self.packages: dict[str, list[str]] = {}

    def load(self) -> None:
        """Читает строки вида «A: B C» — пакет A зависит от B и C."""
        lines = self.path.read_text().splitlines()
        for number, line in enumerate(lines, start=1):
            line = line.strip()
            if line and not line.startswith("#"):
                self._add(line, number)
        if not self.packages:
            raise RepositoryError(f"{self.path}: no packages found")
        for dependencies in list(self.packages.values()):
            for name in dependencies:
                self.packages.setdefault(name, [])

    def select(self, name: str, version: str | None) -> str:
        """Проверяет, что пакет есть; версий в тестовом режиме нет."""
        if name not in self.packages:
            raise RepositoryError(f"package {name!r} not found")
        return ""

    def dependencies(self, name: str) -> list[str]:
        """Возвращает прямые зависимости пакета."""
        return self.packages.get(name, [])

    def _add(self, line: str, number: int) -> None:
        name, colon, rest = line.partition(":")
        names = [name.strip(), *rest.split()]
        if not colon or not all(NAME.fullmatch(item) for item in names):
            raise RepositoryError(
                f"{self.path}:{number}: expected 'NAME: DEPENDENCIES' "
                f"with capital Latin letters, got {line!r}"
            )
        if names[0] in self.packages:
            raise RepositoryError(
                f"{self.path}:{number}: package {names[0]} is described twice"
            )
        self.packages[names[0]] = names[1:]
