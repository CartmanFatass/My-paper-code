"""Behavioral tests for the non-interfering SHADOW hook entrypoint."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tools.codex_semantic_mvp.store import SemanticStore
from tools.codex_semantic_mvp.hook_entry import handle_hook


SUPPORTED_EVENTS = (
    "SessionStart",
    "SubagentStart",
    "SubagentStop",
    "Stop",
    "PreToolUse",
    "PreCompact",
    "PostCompact",
)


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def hook_payload(event: str) -> dict[str, object]:
    return {
        "hook_event_name": event,
        "session_id": "session-test",
        "turn_id": "turn-test",
        "tool_name": "wait_agent" if event == "PreToolUse" else None,
        "tool_use_id": "tool-test" if event == "PreToolUse" else None,
        "tool_input": {"timeout": 10} if event == "PreToolUse" else None,
    }


def test_shadow_supported_events_are_observational(store: SemanticStore) -> None:
    for event in SUPPORTED_EVENTS:
        result = handle_hook(hook_payload(event), "shadow", store)
        assert result in (None, {"continue": True})
        assert result is None or result.get("decision") != "block"
        assert result is None or "additionalContext" not in result

    events = store.events_after(None)
    assert len(events) == len(SUPPORTED_EVENTS)
    assert {event["payload"]["hook_event_name"] for event in events} == set(SUPPORTED_EVENTS)


def test_shadow_unknown_event_is_fail_open(store: SemanticStore) -> None:
    result = handle_hook({"hook_event_name": "NewEvent"}, "shadow", store)
    assert result in (None, {"continue": True})
    assert result is None or result.get("decision") != "block"
    assert result is None or "additionalContext" not in result
    assert store.events_after(None)[0]["kind"] == "UNKNOWN_HOOK_EVENT"


def test_shadow_missing_store_is_fail_open() -> None:
    result = handle_hook({"hook_event_name": "Stop"}, "shadow", None)
    assert result in (None, {"continue": True})


def test_cli_malformed_json_exits_zero_without_stdout(tmp_path: Path) -> None:
    environment = {"HMASD_CODEX_MVP_STATE_DIR": str(tmp_path / "missing-state")}
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, "-m", "tools.codex_semantic_mvp.hook_entry", "--mode", "shadow"],
        input="{not-json\n",
        text=True,
        capture_output=True,
        env={**__import__("os").environ, **environment},
        cwd=Path(__file__).resolve().parents[2],
        timeout=2,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert time.monotonic() - started < 2


def test_cli_valid_input_only_emits_neutral_json(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    payload = json.dumps(hook_payload("SessionStart"))
    completed = subprocess.run(
        [sys.executable, "-m", "tools.codex_semantic_mvp.hook_entry", "--mode", "shadow"],
        input=payload + "\n",
        text=True,
        capture_output=True,
        env={**__import__("os").environ, "HMASD_CODEX_MVP_STATE_DIR": str(state_dir)},
        cwd=Path(__file__).resolve().parents[2],
        timeout=2,
    )
    assert completed.returncode == 0
    output = json.loads(completed.stdout)
    assert output == {"continue": True}
    assert "additionalContext" not in output
    assert output.get("decision") != "block"
    audit = state_dir / "audit.jsonl"
    assert audit.exists()
    assert json.loads(audit.read_text(encoding="utf-8"))["hook_event_name"] == "SessionStart"


def test_shadow_audit_preview_is_truncated_and_does_not_echo_input(store: SemanticStore) -> None:
    payload = hook_payload("PreToolUse")
    payload["tool_input"] = {"secret": "x" * 10_000}
    result = handle_hook(payload, "shadow", store)
    assert result in (None, {"continue": True})
    event = store.events_after(None)[0]
    preview = event["payload"].get("payload_preview", "")
    assert len(preview) <= 2048
    assert "secret" not in preview


def test_shadow_template_registers_all_events_with_bounded_command(repo_root: Path) -> None:
    template = json.loads(
        (repo_root / ".codex" / "hooks.semantic-mvp.shadow.json").read_text(encoding="utf-8")
    )
    assert set(template["hooks"]) == set(SUPPORTED_EVENTS)
    for event in SUPPORTED_EVENTS:
        command = template["hooks"][event][0]["hooks"][0]
        assert command["type"] == "command"
        assert command["command"] == (
            r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe "
            r"-m tools.codex_semantic_mvp.hook_entry --mode shadow"
        )
        assert command["timeout"] == 5
