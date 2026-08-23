from pathlib import Path

import pytest

from tools.codex_supervisor.config import ObserverConfigError, default_runtime_home, load_observer_config


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
    assert config.first_reconciliation_timeout_seconds == 120.0
    assert config.startup_ready_timeout_seconds == 150.0
    assert config.startup_ready_timeout_seconds > 20.0
    assert config.runtime_home.is_absolute()
    raw = (repo_root / ".codex/app-server-observer.toml").read_text(encoding="utf-8")
    for forbidden in ("thread_id", "session_id", "actor_context_id", "token", "password"):
        assert forbidden not in raw.lower()


@pytest.mark.parametrize(
    "replacement",
    [
        ("first_reconciliation_timeout_seconds = 120.0", "first_reconciliation_timeout_seconds = 10.0"),
        ("startup_ready_timeout_seconds = 150.0", "startup_ready_timeout_seconds = 100.0"),
    ],
)
def test_inconsistent_startup_timeout_contract_fails_closed(
    repo_root: Path, tmp_path: Path, replacement: tuple[str, str]
) -> None:
    test_repo = tmp_path / "repo"
    config_dir = test_repo / ".codex"
    config_dir.mkdir(parents=True)
    raw = (repo_root / ".codex/app-server-observer.toml").read_text(encoding="utf-8")
    (config_dir / "app-server-observer.toml").write_text(
        raw.replace(*replacement), encoding="utf-8"
    )
    with pytest.raises(ObserverConfigError):
        load_observer_config(test_repo, runtime_home=tmp_path / "runtime")
