"""Параметры запуска и их проверка."""

import re
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator, model_validator

APT_NAME = re.compile(r"[a-z0-9][a-z0-9+.-]+")
TEST_NAME = re.compile(r"[A-Z]+")
VERSION = re.compile(r"[0-9][A-Za-z0-9.+~:-]*")
URL_SCHEMES = ("http", "https")
IMAGE_SUFFIX = ".png"


def check_test_mode(package: str, repo: str) -> None:
    """Проверяет параметры для тестового репозитория."""
    if not TEST_NAME.fullmatch(package):
        raise ValueError(
            f"package: {package!r} must be capital Latin letters in test mode"
        )
    if not Path(repo).is_file():
        raise ValueError(f"repo: file {repo!r} not found")


def check_apt_mode(package: str, repo: str) -> None:
    """Проверяет параметры для настоящего репозитория Ubuntu."""
    if not APT_NAME.fullmatch(package):
        raise ValueError(f"package: invalid package name {package!r}")
    url = urlparse(repo)
    if url.scheme not in URL_SCHEMES or not url.netloc:
        raise ValueError(f"repo: {repo!r} is not an http(s) URL")


class Config(BaseModel):
    """Проверенные параметры командной строки."""

    package: str
    repo: str
    test: bool = False
    version: str | None = None
    output: str = "graph.png"
    reverse: bool = False

    @field_validator("version")
    @classmethod
    def check_version(cls, value: str | None) -> str | None:
        """Проверяет формат версии пакета."""
        if value is not None and not VERSION.fullmatch(value):
            raise ValueError(f"version: invalid version {value!r}")
        return value

    @field_validator("output")
    @classmethod
    def check_output(cls, value: str) -> str:
        """Проверяет имя файла для изображения графа."""
        path = Path(value)
        if path.suffix != IMAGE_SUFFIX:
            raise ValueError(f"output: {value!r} must be a .png file")
        if not path.parent.is_dir():
            raise ValueError(f"output: folder {str(path.parent)!r} not found")
        return value

    @model_validator(mode="after")
    def check_package_and_repo(self) -> "Config":
        """Проверяет имя пакета и репозиторий с учётом режима работы."""
        if self.test:
            check_test_mode(self.package, self.repo)
        else:
            check_apt_mode(self.package, self.repo)
        return self
