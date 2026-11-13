"""Тесты запуска программы."""

from pathlib import Path

import pytest

from depgraph.dot import RenderError
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


@pytest.fixture(autouse=True)
def images(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Вместо вызова Graphviz запоминает, куда сохранялась бы картинка."""
    saved: list[str] = []
    monkeypatch.setattr(
        "depgraph.main.render_png", lambda _, output: saved.append(output)
    )
    return saved


def test_prints_dot_and_saves_image(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    images: list[str],
) -> None:
    """Печатается граф на языке Graphviz, картинка сохраняется в --output."""
    code = run_main(monkeypatch, "--package", "curl", "--repo", URL)
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("digraph dependencies {\n")
    assert '    label="Dependencies of curl 8.5.0-2ubuntu10";\n' in out
    assert '    "curl" -> "libcurl4t64";\n' in out
    assert '    "libc6" [color=red];\n' in out
    assert out.endswith("}\nImage saved to graph.png, packages: 6\n")
    assert images == ["graph.png"]


def test_output_option(
    monkeypatch: pytest.MonkeyPatch, images: list[str], tmp_path: Path
) -> None:
    """Картинка сохраняется в файл, указанный в --output."""
    output = str(tmp_path / "curl.png")
    run_main(
        monkeypatch, "--package", "curl", "--repo", URL, "--output", output
    )
    assert images == [output]


def test_test_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """В тестовом режиме граф читается из файла."""
    argv = ("--package", "A", "--repo", "repos/diamond.txt", "--test")
    code = run_main(monkeypatch, *argv)
    out = capsys.readouterr().out
    assert code == 0
    assert '    label="Dependencies of A";\n' in out
    assert '    "A" -> "B";\n    "A" -> "C";\n' in out
    assert "red" not in out


def test_render_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ошибка Graphviz — сообщение и код 1."""

    def broken(*_: str) -> None:
        raise RenderError("Graphviz is not installed: command 'dot' not found")

    monkeypatch.setattr("depgraph.main.render_png", broken)
    argv = ("--package", "A", "--repo", "repos/diamond.txt", "--test")
    assert run_main(monkeypatch, *argv) == ERROR_CODE
    assert "error: Graphviz is not installed" in capsys.readouterr().out


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
    """С --reverse рисуются пакеты, которые зависят от заданного."""
    argv = ("--package", "D", "--repo", "repos/diamond.txt", "--test")
    code = run_main(monkeypatch, *argv, "--reverse")
    out = capsys.readouterr().out
    assert code == 0
    assert '    label="Reverse dependencies of D";\n' in out
    for arrow in ('"B" -> "D"', '"C" -> "D"', '"A" -> "B"', '"A" -> "C"'):
        assert f"    {arrow};\n" in out
    assert out.endswith("packages: 4\n")


def test_reverse_mode_nobody_depends(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """От корневого пакета никто не зависит — один узел без стрелок."""
    argv = ("--package", "A", "--repo", "repos/diamond.txt", "--test")
    run_main(monkeypatch, *argv, "--reverse")
    out = capsys.readouterr().out
    assert "->" not in out
    assert out.endswith("packages: 1\n")


def test_reverse_mode_apt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Обратные зависимости в индексе Ubuntu, с учётом виртуальных пакетов."""
    run_main(monkeypatch, "--package", "libssl3t64", "--repo", URL, "--reverse")
    assert '    "librtmp1" -> "libssl3t64";\n' in capsys.readouterr().out
