from pathlib import Path

from tools.codex_supervisor.config import default_runtime_home, load_observer_config


def test_default_runtime_home_is_external(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    home = default_runtime_home()
    assert home == tmp_path / "Local" / "HMASD" / "codex-supervisor"


def test_repo_config_contains_no_runtime_identity(repo_root: Path) -> None:
    config = load_observer_config(repo_root, runtime_home=Path("C:/Users/Public/HMASD-observer-test"))
    assert config.client_name == "hmasd-codex-app-server-observer"
    assert config.experimental_api is False
    assert config.max_jsonl_line_bytes == 16_777_216
    assert config.unexpected_server_request_policy == "terminate"
    assert config.runtime_home.is_absolute()
    raw = (repo_root / ".codex/app-server-observer.toml").read_text(encoding="utf-8")
    for forbidden in ("thread_id", "session_id", "actor_context_id", "token", "password"):
        assert forbidden not in raw.lower()
