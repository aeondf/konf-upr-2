"""Тесты проверки параметров запуска."""

import pytest
from pydantic import ValidationError

from depgraph.config import Config

URL = "http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages"
TEST_REPO = "repos/simple.txt"


def test_apt_mode() -> None:
    """Корректные параметры для настоящего репозитория."""
    config = Config(package="curl", repo=URL, version="8.5.0-2ubuntu10")
    assert config.test is False
    assert config.output == "graph.png"


def test_test_mode() -> None:
    """Корректные параметры для тестового репозитория."""
    config = Config(package="A", repo=TEST_REPO, test=True)
    assert config.version is None


@pytest.mark.parametrize("name", ["Curl", "c", "curl!", "-curl", ""])
def test_bad_apt_package(name: str) -> None:
    """Имя пакета Ubuntu: строчные буквы, цифры, + - ."""
    with pytest.raises(ValidationError, match="package"):
        Config(package=name, repo=URL)


@pytest.mark.parametrize("repo", ["ftp://x.org/P", "not-a-url", "http://"])
def test_bad_url(repo: str) -> None:
    """В обычном режиме репозиторий — http(s) адрес."""
    with pytest.raises(ValidationError, match="repo"):
        Config(package="curl", repo=repo)


def test_bad_test_package() -> None:
    """В тестовом режиме имя пакета — заглавные латинские буквы."""
    with pytest.raises(ValidationError, match="capital"):
        Config(package="a", repo=TEST_REPO, test=True)


def test_missing_test_repo() -> None:
    """В тестовом режиме файл репозитория должен существовать."""
    with pytest.raises(ValidationError, match="not found"):
        Config(package="A", repo="repos/nope.txt", test=True)


@pytest.mark.parametrize("version", ["abc", "", "1 2"])
def test_bad_version(version: str) -> None:
    """Версия начинается с цифры и не содержит пробелов."""
    with pytest.raises(ValidationError, match="version"):
        Config(package="curl", repo=URL, version=version)


def test_output_not_png() -> None:
    """Файл изображения — только .png."""
    with pytest.raises(ValidationError, match="png"):
        Config(package="curl", repo=URL, output="graph.jpg")


def test_output_folder_missing() -> None:
    """Папка для файла изображения должна существовать."""
    with pytest.raises(ValidationError, match="folder"):
        Config(package="curl", repo=URL, output="nope/graph.png")
