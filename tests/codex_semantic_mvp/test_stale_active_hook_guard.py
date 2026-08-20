"""Fail-safe handling for stale cached ACTIVE hook commands."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from tools.codex_semantic_mvp import hook_entry
from tools.codex_semantic_mvp.store import SemanticStore


def _config(mode: str) -> str:
    events = (
        ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreCompact", "PostCompact")
        if mode == "active"
        else (
            "SessionStart",
            "SubagentStart",
            "SubagentStop",
            "Stop",
            "PreToolUse",
            "PreCompact",
            "PostCompact",
        )
    )
    command = (
        "C:\\\\Python\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode " + mode
    )
    handlers = "\n".join(
        "\n".join(
            (
                f"[[hooks.{event}]]",
                f"[[hooks.{event}.hooks]]",
                'type = "command"',
                f'command = "{command}"',
                f'commandWindows = "{command}"',
                "timeout = 5",
            )
        )
        for event in events
    )
    return "\n".join(
        (
            "[features]",
            "hooks = true",
            "",
            "[mcp_servers.hmasd_orchestrator]",
            'command = "C:\\\\Python\\\\python.exe"',
            "enabled = true",
            'args = ["-m", "tools.codex_semantic_mvp.mcp_server", "--state-dir", "runtime/codex-semantic-mvp"]',
            "",
            "[hooks]",
            handlers,
            "",
        )
    )


def _payload(event: str) -> dict[str, object]:
    return {
        "hook_event_name": event,
        "session_id": "guard-session",
        "turn_id": "guard-turn",
        "agent_id": "guard-agent",
        "agent_type": "default",
        "last_assistant_message": "untyped result must not be persisted",
    }


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str) -> Path:
    config = tmp_path / "config.toml"
    config.write_text(text, encoding="utf-8")
    monkeypatch.setattr(hook_entry, "SEMANTIC_CONFIG_PATH", config)
    monkeypatch.setattr(hook_entry, "PAUSE_SENTINEL_PATH", tmp_path / "not-paused")
    monkeypatch.setenv("HMASD_CODEX_MVP_STATE_DIR", str(tmp_path / "runtime"))
    return config


@pytest.mark.parametrize("event", ["Stop", "SubagentStop"])
def test_stale_active_command_downgrades_to_shadow_without_semantic_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, event: str
) -> None:
    _configure(monkeypatch, tmp_path, _config("shadow"))

    def store_must_not_initialize(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("stale active invocation must not initialize SemanticStore")

    output = io.StringIO()
    monkeypatch.setattr(hook_entry, "SemanticStore", store_must_not_initialize)
    monkeypatch.setattr(hook_entry.sys, "stdin", io.StringIO(json.dumps(_payload(event))))
    monkeypatch.setattr(hook_entry.sys, "stdout", output)

    assert hook_entry.main(["--mode", "active"]) == 0
    assert json.loads(output.getvalue()) == {"continue": True}
    runtime = tmp_path / "runtime"
    assert not (runtime / "state.sqlite3").exists()
    audit = json.loads((runtime / "audit.jsonl").read_text(encoding="utf-8"))
    assert audit["mode"] == "shadow"
    assert audit["hook_event_name"] == event


def test_true_active_config_preserves_active_behavior(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure(monkeypatch, tmp_path, _config("active"))
    output = io.StringIO()
    monkeypatch.setattr(hook_entry.sys, "stdin", io.StringIO(json.dumps(_payload("SessionStart"))))
    monkeypatch.setattr(hook_entry.sys, "stdout", output)

    assert hook_entry.main(["--mode", "active"]) == 0
    result = json.loads(output.getvalue())
    assert "additionalContext" in result
    store = SemanticStore(tmp_path / "runtime" / "state.sqlite3").initialize()
    try:
        assert store.current_workflow("guard-session") is not None
    finally:
        store.close()


def test_mcp_and_hook_executables_must_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    text = _config("active").replace(
        'command = "C:\\\\Python\\\\python.exe"',
        'command = "C:\\\\OtherPython\\\\python.exe"',
        1,
    )
    _configure(monkeypatch, tmp_path, text)

    def store_must_not_initialize(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("inconsistent active invocation must not initialize SemanticStore")

    output = io.StringIO()
    monkeypatch.setattr(hook_entry, "SemanticStore", store_must_not_initialize)
    monkeypatch.setattr(hook_entry.sys, "stdin", io.StringIO(json.dumps(_payload("Stop"))))
    monkeypatch.setattr(hook_entry.sys, "stdout", output)

    assert hook_entry.main(["--mode", "active"]) == 0
    assert json.loads(output.getvalue()) == {"continue": True}
    assert not (tmp_path / "runtime" / "state.sqlite3").exists()


@pytest.mark.parametrize("kind", ["malformed", "mixed"])
def test_malformed_or_mixed_live_config_neutralizes_active_without_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kind: str
) -> None:
    text = "[features\nhooks = true\n" if kind == "malformed" else _config("shadow").replace(
        "--mode shadow", "--mode active", 1
    )
    _configure(monkeypatch, tmp_path, text)

    def store_must_not_initialize(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("ambiguous active invocation must not initialize SemanticStore")

    output = io.StringIO()
    monkeypatch.setattr(hook_entry, "SemanticStore", store_must_not_initialize)
    monkeypatch.setattr(hook_entry.sys, "stdin", io.StringIO(json.dumps(_payload("Stop"))))
    monkeypatch.setattr(hook_entry.sys, "stdout", output)

    assert hook_entry.main(["--mode", "active"]) == 0
    assert json.loads(output.getvalue()) == {"continue": True}
    assert not (tmp_path / "runtime" / "state.sqlite3").exists()
