"""Тесты чтения индекса пакетов Ubuntu."""

import gzip
from pathlib import Path

import pytest

from depgraph.apt import AptRepository, parse_block, parse_depends
from depgraph.repository import RepositoryError

DATA = Path(__file__).parent / "data" / "Packages"
TOOL_VERSIONS = 2


def make_repository(url: str) -> AptRepository:
    """Создаёт и загружает репозиторий по адресу."""
    repository = AptRepository(url)
    repository.load()
    return repository


@pytest.fixture
def repository() -> AptRepository:
    """Репозиторий из локального образца индекса."""
    return make_repository(DATA.as_uri())


def test_parse_block() -> None:
    """Поля разбираются, строки-продолжения склеиваются."""
    fields = parse_block("Package: a\nDepends: b,\n c\nVersion: 1")
    assert fields == {"Package": "a", "Depends": "b, c", "Version": "1"}


def test_parse_depends() -> None:
    """Версии, архитектуры и альтернативы отбрасываются, дубли убираются."""
    value = "libnew | libalt, python3:any (>= 3.6), libc6 (>= 2.34), libnew"
    assert parse_depends(value) == ["libnew", "python3", "libc6"]


def test_parse_depends_empty() -> None:
    """Пустое поле — нет зависимостей."""
    assert parse_depends(",") == []


def test_load_counts_versions(repository: AptRepository) -> None:
    """Все версии одного пакета сохраняются."""
    assert len(repository.packages["tool"]) == TOOL_VERSIONS


def test_direct_dependencies(repository: AptRepository) -> None:
    """Прямые зависимости curl."""
    repository.select("curl", None)
    assert repository.dependencies("curl") == [
        "libc6",
        "libcurl4t64",
        "zlib1g",
    ]


def test_latest_version_by_default(repository: AptRepository) -> None:
    """Без --version берётся последняя версия из индекса."""
    assert repository.select("tool", None) == "2.0-1"
    assert repository.dependencies("tool") == [
        "dpkg",
        "libnew",
        "python3",
        "libc6",
    ]


def test_selected_version(repository: AptRepository) -> None:
    """Зависимости берутся у указанной версии."""
    assert repository.select("tool", "1.0-1") == "1.0-1"
    assert repository.dependencies("tool") == ["libold", "libc6"]


def test_unknown_version(repository: AptRepository) -> None:
    """Неизвестная версия — ошибка со списком доступных."""
    with pytest.raises(RepositoryError, match="available"):
        repository.select("tool", "9.9")


def test_unknown_package(repository: AptRepository) -> None:
    """Неизвестный пакет — ошибка."""
    with pytest.raises(RepositoryError, match="not found"):
        repository.select("nope", None)


def test_dependencies_of_missing_package(repository: AptRepository) -> None:
    """У пакета, которого нет в индексе, зависимостей нет."""
    assert repository.dependencies("zlib1g") == []


def test_gzip_index(tmp_path: Path) -> None:
    """Сжатый индекс .gz распаковывается."""
    path = tmp_path / "Packages.gz"
    path.write_bytes(gzip.compress(DATA.read_bytes()))
    assert "curl" in make_repository(path.as_uri()).packages


def test_broken_gzip(tmp_path: Path) -> None:
    """Повреждённый архив — ошибка."""
    path = tmp_path / "Packages.gz"
    path.write_bytes(b"not a gzip")
    with pytest.raises(RepositoryError, match="unpack"):
        make_repository(path.as_uri())


def test_missing_url(tmp_path: Path) -> None:
    """Недоступный адрес — ошибка."""
    with pytest.raises(RepositoryError, match="download"):
        make_repository((tmp_path / "nope").as_uri())


def test_empty_index(tmp_path: Path) -> None:
    """Файл без пакетов — ошибка."""
    path = tmp_path / "Packages"
    path.write_text("hello\n")
    with pytest.raises(RepositoryError, match="no packages"):
        make_repository(path.as_uri())


def test_virtual_package_is_replaced(repository: AptRepository) -> None:
    """Виртуальный пакет заменяется настоящим, повторы убираются."""
    assert repository.dependencies("librtmp1") == ["libc6", "libssl3t64"]


def test_names(repository: AptRepository) -> None:
    """Список всех пакетов индекса."""
    assert "curl" in repository.names()
    assert "libssl3" not in repository.names()
