"""Behavioral tests for the non-interfering SHADOW hook entrypoint."""

from __future__ import annotations

import json
import io
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tools.codex_semantic_mvp import hook_entry
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


@pytest.fixture(autouse=True)
def unpaused_semantic_hooks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(hook_entry, "PAUSE_SENTINEL_PATH", tmp_path / "absent-hooks-pause-sentinel")


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

    # Shadow audits are runtime-only.  They must not accumulate semantic
    # workflow ledger events or turn ordinary hook observation into an
    # obligation/continuation surface.
    assert store.events_after(None) == []
    audit_records = [json.loads(line) for line in (store.path.parent / "audit.jsonl").read_text().splitlines()]
    assert len(audit_records) == len(SUPPORTED_EVENTS)
    assert {record["hook_event_name"] for record in audit_records} == set(SUPPORTED_EVENTS)


def test_shadow_unknown_event_is_fail_open(store: SemanticStore) -> None:
    result = handle_hook({"hook_event_name": "NewEvent"}, "shadow", store)
    assert result in (None, {"continue": True})
    assert result is None or result.get("decision") != "block"
    assert result is None or "additionalContext" not in result
    assert store.events_after(None) == []
    audit = json.loads((store.path.parent / "audit.jsonl").read_text())
    assert audit["event"] == "UNKNOWN_HOOK_EVENT"


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
    # The repository-level pause sentinel may short-circuit the subprocess;
    # either way shadow must not initialize a semantic SQLite ledger.
    assert not (state_dir / "state.sqlite3").exists()


def test_shadow_audit_preview_is_truncated_and_does_not_echo_input(store: SemanticStore) -> None:
    payload = hook_payload("PreToolUse")
    payload["tool_input"] = {"secret": "x" * 10_000}
    result = handle_hook(payload, "shadow", store)
    assert result in (None, {"continue": True})
    audit = json.loads((store.path.parent / "audit.jsonl").read_text())
    preview = audit.get("payload_preview", "")
    assert len(preview) <= 2048
    assert "secret" not in preview


def test_shadow_never_mutates_existing_semantic_ledger(store: SemanticStore) -> None:
    workflow_id = store.open_workflow(
        session_id="existing-session", opened_turn_id="turn-0", scope="session", objective="existing"
    )
    task_id = store.register_task(workflow_id, "task-0", "default", "existing")
    before = store.workflow_state(workflow_id)

    for event in SUPPORTED_EVENTS:
        assert handle_hook(hook_payload(event), "shadow", store) == {"continue": True}

    after = store.workflow_state(workflow_id)
    assert after == before


def test_shadow_main_never_initializes_semantic_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def store_must_not_initialize(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("shadow must not initialize SemanticStore")

    output = io.StringIO()
    monkeypatch.setattr(hook_entry, "SemanticStore", store_must_not_initialize)
    monkeypatch.setattr(hook_entry.sys, "stdin", io.StringIO(json.dumps(hook_payload("Stop"))))
    monkeypatch.setattr(hook_entry.sys, "stdout", output)
    monkeypatch.setenv("HMASD_CODEX_MVP_STATE_DIR", str(tmp_path / "shadow-runtime"))

    assert hook_entry.main(["--mode", "shadow"]) == 0
    assert json.loads(output.getvalue()) == {"continue": True}
    assert not (tmp_path / "shadow-runtime" / "state.sqlite3").exists()


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
