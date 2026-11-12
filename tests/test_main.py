"""Тесты запуска программы."""

import pytest

from depgraph.main import main

URL = "http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages"
ERROR_CODE = 1


def run_main(monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    """Запускает main() с заданными параметрами."""
    monkeypatch.setattr("sys.argv", ["main.py", *argv])
    return main()


def test_prints_parameters(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Параметры печатаются в формате ключ=значение."""
    code = run_main(monkeypatch, "--package", "curl", "--repo", URL)
    out = capsys.readouterr().out
    assert code == 0
    assert "package=curl\n" in out
    assert f"repo={URL}\n" in out
    assert "test=False\n" in out
    assert "version=None\n" in out
    assert "output=graph.png\n" in out


def test_error_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Неверный параметр — сообщение и код 1."""
    code = run_main(monkeypatch, "--package", "Bad!", "--repo", URL)
    assert code == ERROR_CODE
    assert capsys.readouterr().out.startswith("error: package:")
