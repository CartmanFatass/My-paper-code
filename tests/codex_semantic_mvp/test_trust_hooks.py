"""Unit coverage for exact-five/exact-four hook trust allowlisting."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.codex_semantic_mvp.constants import ACTIVE_HOOK_EVENTS
from tools.codex_semantic_mvp.trust_hooks import (
    AppServerError,
    _trusted_hash_key_path,
    expected_config_path,
    expected_hook_key,
    select_and_validate_hooks,
)


def _hook(
    repo_root: Path,
    event: str,
    *,
    mode: str = "active",
    extra_command: str = "",
    source: Path | None = None,
    trusted: bool = False,
) -> dict[str, object]:
    config = expected_config_path(repo_root)
    return {
        "eventName": event,
        "command": (
            f"C:\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode {mode}{extra_command}"
        ),
        "sourcePath": str(source or config),
        "key": expected_hook_key(repo_root, event),
        "currentHash": "sha256:abc",
        "trustStatus": "trusted" if trusted else "untrusted",
    }


def test_select_and_validate_accepts_exact_active_set(repo_root: Path) -> None:
    hooks = [_hook(repo_root, event) for event in ACTIVE_HOOK_EVENTS]
    selected = select_and_validate_hooks([{"hooks": hooks}], repo_root)
    assert [item["eventName"] for item in selected] == list(ACTIVE_HOOK_EVENTS)
    assert [_trusted_hash_key_path(str(item["key"])) for item in selected] == [
        "hooks.state.'" + expected_hook_key(repo_root, event) + "'.trusted_hash"
        for event in ACTIVE_HOOK_EVENTS
    ]


def test_select_and_validate_rejects_pretooluse_in_active(repo_root: Path) -> None:
    hooks = [_hook(repo_root, event) for event in ACTIVE_HOOK_EVENTS]
    hooks.append(_hook(repo_root, "PreToolUse"))
    with pytest.raises(AppServerError, match="mode|expected exact"):
        select_and_validate_hooks([{"hooks": hooks}], repo_root)


def test_select_and_validate_rejects_wrong_source_or_key(repo_root: Path, tmp_path: Path) -> None:
    hooks = [_hook(repo_root, event) for event in ACTIVE_HOOK_EVENTS]
    hooks[0]["sourcePath"] = str(tmp_path / "other.toml")
    with pytest.raises(AppServerError, match="allowlist extras"):
        select_and_validate_hooks([{"hooks": hooks}], repo_root)


def test_trusted_hash_key_path_quotes_dotted_config_identity(repo_root: Path) -> None:
    key = expected_hook_key(repo_root, "SessionStart")
    assert ".codex" in key
    path = _trusted_hash_key_path(key)
    assert path.startswith("hooks.state.'")
    assert path.endswith("'.trusted_hash")
    assert "hooks.state.C:" not in path
