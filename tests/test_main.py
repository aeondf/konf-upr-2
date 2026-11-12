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


def test_prints_graph(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Печатаются граф зависимостей и пакеты в циклах."""
    code = run_main(monkeypatch, "--package", "curl", "--repo", URL)
    out = capsys.readouterr().out
    assert code == 0
    assert "Dependency graph of curl 8.5.0-2ubuntu10:" in out
    assert "  curl -> libc6, libcurl4t64, zlib1g\n" in out
    assert "  libc6 -> libgcc-s1\n" in out
    assert "Packages in cycles: libc6, libgcc-s1" in out


def test_test_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """В тестовом режиме граф читается из файла."""
    argv = ("--package", "A", "--repo", "repos/diamond.txt", "--test")
    code = run_main(monkeypatch, *argv)
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("Dependency graph of A:\n  A -> B, C\n")
    assert "cycles" not in out


def test_broken_test_repo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ошибка в файле тестового репозитория — сообщение и код 1."""
    argv = ("--package", "A", "--repo", "repos/broken.txt", "--test")
    assert run_main(monkeypatch, *argv) == ERROR_CODE
    assert "broken.txt:2" in capsys.readouterr().out


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


def test_reverse_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """С --reverse печатаются пакеты, зависящие от заданного."""
    argv = ("--package", "D", "--repo", "repos/diamond.txt", "--test")
    code = run_main(monkeypatch, *argv, "--reverse")
    out = capsys.readouterr().out
    assert code == 0
    assert out == (
        "Reverse dependencies of D (3):\n"
        "  D <- B, C\n"
        "  B <- A\n"
        "  C <- A\n"
        "  A <- (none)\n"
    )


def test_reverse_mode_nobody_depends(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """От корневого пакета никто не зависит."""
    argv = ("--package", "A", "--repo", "repos/diamond.txt", "--test")
    run_main(monkeypatch, *argv, "--reverse")
    assert "Reverse dependencies of A (0):" in capsys.readouterr().out


def test_reverse_mode_apt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Обратные зависимости в индексе Ubuntu, с учётом виртуальных пакетов."""
    run_main(monkeypatch, "--package", "libssl3t64", "--repo", URL, "--reverse")
    out = capsys.readouterr().out
    assert "  libssl3t64 <- librtmp1\n" in out
