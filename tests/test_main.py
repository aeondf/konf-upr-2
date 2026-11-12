"""Тесты запуска программы."""

from pathlib import Path

import pytest

from depgraph.main import main

DATA = Path(__file__).parent / "data" / "Packages"

URL = "http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages"
ERROR_CODE = 1


def run_main(monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    """Запускает main() с заданными параметрами."""
    monkeypatch.setattr("sys.argv", ["main.py", *argv])
    return main()


@pytest.fixture(autouse=True)
def local_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """Вместо скачивания по сети читает локальный образец индекса."""
    monkeypatch.setattr(
        "depgraph.apt.urlopen", lambda *_, **__: DATA.open("rb")
    )


def test_prints_direct_dependencies(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Печатаются версия пакета и его прямые зависимости."""
    code = run_main(monkeypatch, "--package", "curl", "--repo", URL)
    out = capsys.readouterr().out
    assert code == 0
    assert "Package: curl 8.5.0-2ubuntu10" in out
    assert "Direct dependencies (3):\n  libc6\n  libcurl4t64\n  zlib1g\n" in out


def test_package_not_found(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Пакета нет в репозитории — сообщение и код 1."""
    code = run_main(monkeypatch, "--package", "nope", "--repo", URL)
    assert code == ERROR_CODE
    assert "not found" in capsys.readouterr().out


def test_error_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Неверный параметр — сообщение и код 1."""
    code = run_main(monkeypatch, "--package", "Bad!", "--repo", URL)
    assert code == ERROR_CODE
    assert capsys.readouterr().out.startswith("error: package:")
