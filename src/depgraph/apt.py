"""Репозиторий Ubuntu: чтение индекса пакетов в формате apt."""

import gzip
import lzma
from urllib.error import URLError
from urllib.request import urlopen

from depgraph.repository import Repository, RepositoryError

TIMEOUT = 60
MAX_SHOWN_VERSIONS = 5


def download(url: str) -> str:
    """Скачивает индекс пакетов и распаковывает его, если он сжат."""
    try:
        with urlopen(url, timeout=TIMEOUT) as response:
            data = response.read()
    except (URLError, TimeoutError, ValueError) as error:
        raise RepositoryError(f"cannot download {url}: {error}") from None
    try:
        if url.endswith(".gz"):
            data = gzip.decompress(data)
        elif url.endswith(".xz"):
            data = lzma.decompress(data)
    except (OSError, lzma.LZMAError) as error:
        raise RepositoryError(f"cannot unpack {url}: {error}") from None
    return data.decode("utf-8", errors="replace")


def parse_block(block: str) -> dict[str, str]:
    """Разбирает одно описание пакета из строк «Поле: значение»."""
    fields: dict[str, str] = {}
    key = ""
    for line in block.splitlines():
        if line.startswith((" ", "\t")) and key:
            fields[key] += " " + line.strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            fields[key] = value.strip()
    return fields


def parse_packages(text: str) -> dict[str, list[dict[str, str]]]:
    """Разбирает индекс: имя пакета → описания всех его версий."""
    packages: dict[str, list[dict[str, str]]] = {}
    for block in text.split("\n\n"):
        fields = parse_block(block)
        if "Package" in fields:
            packages.setdefault(fields["Package"], []).append(fields)
    return packages


def parse_depends(value: str) -> list[str]:
    """Достаёт имена пакетов из поля Depends."""
    names: list[str] = []
    for item in value.split(","):
        first = item.split("|")[0]
        name = first.split("(")[0].split(":")[0].strip()
        if name and name not in names:
            names.append(name)
    return names


def find_providers(packages: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    """Сопоставляет виртуальному пакету настоящий из поля Provides."""
    providers: dict[str, str] = {}
    for name, versions in packages.items():
        for virtual in parse_depends(versions[-1].get("Provides", "")):
            providers.setdefault(virtual, name)
    return providers


class AptRepository(Repository):
    """Индекс пакетов настоящего репозитория Ubuntu."""

    def __init__(self, url: str) -> None:
        """Запоминает адрес файла Packages."""
        self.url = url
        self.packages: dict[str, list[dict[str, str]]] = {}
        self.providers: dict[str, str] = {}

    def load(self) -> None:
        """Скачивает и разбирает индекс пакетов."""
        self.packages = parse_packages(download(self.url))
        if not self.packages:
            raise RepositoryError(f"{self.url}: no packages found")
        self.providers = find_providers(self.packages)

    def select(self, name: str, version: str | None) -> str:
        """Оставляет у пакета только нужную версию и возвращает её."""
        versions = self.packages.get(name)
        if not versions:
            raise RepositoryError(f"package {name!r} not found")
        chosen = versions[-1]
        if version is not None:
            chosen = self._find_version(name, version, versions)
        self.packages[name] = [chosen]
        return chosen.get("Version", "")

    def dependencies(self, name: str) -> list[str]:
        """Возвращает прямые зависимости: Pre-Depends и Depends."""
        versions = self.packages.get(name)
        if not versions:
            return []
        fields = versions[-1]
        pre_depends = fields.get("Pre-Depends", "")
        names = parse_depends(pre_depends + "," + fields.get("Depends", ""))
        real = [self._real_name(name) for name in names]
        return list(dict.fromkeys(real))

    def _real_name(self, name: str) -> str:
        if name in self.packages:
            return name
        return self.providers.get(name, name)

    def _find_version(
        self, name: str, version: str, versions: list[dict[str, str]]
    ) -> dict[str, str]:
        for fields in versions:
            if fields.get("Version") == version:
                return fields
        known = [fields.get("Version", "?") for fields in versions]
        shown = ", ".join(known[-MAX_SHOWN_VERSIONS:])
        raise RepositoryError(
            f"version {version!r} of {name!r} not found; "
            f"available ({len(known)}): {shown}"
        )
