from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import write_fake_codex
from tools.codex_supervisor.codex_binary import CodexBinaryError, read_codex_version, resolve_codex_binary


def test_explicit_binary_wins(tmp_path: Path) -> None:
    binary = write_fake_codex(tmp_path)
    assert resolve_codex_binary(binary) == binary.resolve()


def test_codex_bin_environment_is_second(monkeypatch, tmp_path: Path) -> None:
    binary = write_fake_codex(tmp_path)
    monkeypatch.setenv("CODEX_BIN", str(binary))
    monkeypatch.delenv("PATH", raising=False)
    assert resolve_codex_binary() == binary.resolve()


def test_path_lookup_is_third(monkeypatch, tmp_path: Path) -> None:
    binary = write_fake_codex(tmp_path)
    monkeypatch.delenv("CODEX_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    resolved = resolve_codex_binary()
    assert resolved.name.lower().startswith("codex")


def test_missing_binary_raises_clear_error(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_BIN", raising=False)
    monkeypatch.setenv("PATH", "")
    with pytest.raises(CodexBinaryError, match="no Codex binary"):
        resolve_codex_binary()


def test_version_is_readable(tmp_path: Path) -> None:
    binary = write_fake_codex(tmp_path)
    assert "codex-fake" in read_codex_version(binary)
