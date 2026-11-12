"""Тесты тестового репозитория из файла."""

from pathlib import Path

import pytest

from depgraph.file_repo import FileRepository
from depgraph.repository import RepositoryError


def load(tmp_path: Path, text: str) -> FileRepository:
    """Сохраняет описание графа в файл и загружает его."""
    path = tmp_path / "repo.txt"
    path.write_text(text)
    repository = FileRepository(str(path))
    repository.load()
    return repository


def test_dependencies(tmp_path: Path) -> None:
    """Строка «A: B C» — пакет A зависит от B и C."""
    repository = load(tmp_path, "A: B C\nB:\n")
    assert repository.dependencies("A") == ["B", "C"]
    assert repository.dependencies("B") == []


def test_comments_and_blank_lines(tmp_path: Path) -> None:
    """Комментарии и пустые строки пропускаются."""
    repository = load(tmp_path, "# граф\n\nA: B\n")
    assert repository.dependencies("A") == ["B"]


def test_undescribed_package_is_known(tmp_path: Path) -> None:
    """Пакет, который встречается только в зависимостях, тоже известен."""
    repository = load(tmp_path, "A: Z\n")
    assert repository.select("Z", None) == ""
    assert repository.dependencies("Z") == []


def test_unknown_package(tmp_path: Path) -> None:
    """Пакета нет в графе — ошибка."""
    repository = load(tmp_path, "A: B\n")
    with pytest.raises(RepositoryError, match="not found"):
        repository.select("X", None)


@pytest.mark.parametrize("line", ["a: B", "A: b", "A B", "A: B1"])
def test_bad_line(tmp_path: Path, line: str) -> None:
    """Неверная строка — ошибка с номером строки."""
    with pytest.raises(RepositoryError, match="repo.txt:2"):
        load(tmp_path, f"C: D\n{line}\n")


def test_described_twice(tmp_path: Path) -> None:
    """Пакет описан дважды — ошибка."""
    with pytest.raises(RepositoryError, match="twice"):
        load(tmp_path, "A: B\nA: C\n")


def test_empty_file(tmp_path: Path) -> None:
    """Файл без пакетов — ошибка."""
    with pytest.raises(RepositoryError, match="no packages"):
        load(tmp_path, "# пусто\n")


def test_names(tmp_path: Path) -> None:
    """Список пакетов включает и неописанные."""
    assert load(tmp_path, "A: B\n").names() == ["A", "B"]
