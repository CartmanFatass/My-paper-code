"""Static contracts for portable CLI lifecycle hooks."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = ROOT / ".codex" / "hooks.json"


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key}={_text(item)}" for key, item in value.items())
    return str(value)


def _commands(entries: object) -> list[dict]:
    result: list[dict] = []
    if not isinstance(entries, list):
        return result
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        hooks = entry.get("hooks", [])
        if isinstance(hooks, list):
            result.extend(item for item in hooks if isinstance(item, dict))
    return result


def test_hook_map_is_empty_and_non_authoritative() -> None:
    payload = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
    hooks = payload["hooks"]
    assert hooks == {}
    assert _commands(hooks) == []


def test_disabled_hooks_do_not_parse_sessions_or_dispatch_readiness() -> None:
    payload = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
    hooks = payload["hooks"]
    serialized = _text(hooks).lower()
    assert hooks == {}
    for marker in (
        "pretooluse",
        "subagentstart",
        "subagentstop",
        "stop",
        "hmasd_subagent_start.py",
        "hmasd_subagent_stop.py",
        "hmasd_execution_readiness.py",
        "agent_type",
        "agent_id",
    ):
        assert marker not in serialized


def test_disabled_hooks_remain_identity_neutral_and_lightweight() -> None:
    payload = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
    hooks = payload["hooks"]
    serialized = _text(hooks).lower()
    assert hooks == {}
    assert "agent_type" not in serialized
    assert "agent_id" not in serialized
    assert "canonical" not in serialized
    assert "acceptance" not in serialized
    assert "heartbeat" not in serialized


def test_project_launcher_exists_and_does_not_mutate_user_environment() -> None:
    launcher = ROOT / "scripts" / "invoke_hmasd_hook.ps1"
    assert launcher.is_file()
    text = launcher.read_text(encoding="utf-8")
    assert "HMASD_PYTHON" in text
    assert re.search(r"(?i)python(?:\.exe)?|py\s+-3", text)
    assert "Set-Item" not in text and "setx" not in text.lower()
