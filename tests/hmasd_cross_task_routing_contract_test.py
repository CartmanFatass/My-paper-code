from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-cross-task-routing/SKILL.md"
UI = ROOT / ".agents/skills/hmasd-cross-task-routing/agents/openai.yaml"
PROBE = (
    ROOT
    / ".agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py"
)
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/EXTERNAL_REVIEW_OPERATOR.md",
)


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "Conversation-local route cache",
        "at most three candidates",
        "within 120 wall-clock seconds",
        "Polling is forbidden",
        "ROLE_ROUTE_PROBE",
        "ROLE_ROUTE_CONFIRM",
        "ROLE_ROUTE_ANNOUNCE",
        "codex_delegation.source_thread_id",
        "ROUTE_CONFIRMED",
        "ROUTE_AMBIGUOUS",
        "ROUTE_UNAVAILABLE",
        "Live settings preservation",
        "SQLite `mode=ro`",
        "ROUTE_SETTINGS_UNAVAILABLE",
        "ROUTE_SETTINGS_DRIFT",
        "exact `model` as `model`",
        "exact `thinking` as `thinking`",
        "do not automatically resend",
    )
    for token in required:
        assert token in text, token


def test_cross_task_routing_skill_is_explicit_only() -> None:
    interface = yaml.safe_load(UI.read_text(encoding="utf-8"))
    assert interface["policy"]["allow_implicit_invocation"] is False
    assert "$hmasd-cross-task-routing" in interface["interface"]["default_prompt"]


def test_persistent_roles_do_not_pin_live_session_model_or_effort() -> None:
    forbidden = re.compile(
        r"(?m)^(?:session|model|reasoning_effort|\w+_(?:target|return)_"
        r"(?:session|model|effort))="
    )
    for path in PERSISTENT_ROLES:
        text = path.read_text(encoding="utf-8")
        assert forbidden.search(text) is None, path
        assert "cross_task_routing_skill=hmasd-cross-task-routing" in text
        assert (
            "cross_task_model_thinking_preservation="
            "live_state_probe_explicit_echo"
        ) in text


def test_static_review_registry_contains_no_live_codex_route() -> None:
    registry = json.loads(
        (ROOT / "docs/external-review/REVIEWER_CONVERSATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    contract = registry["intertask_transport_contract"]
    assert registry["schema_version"] == 35
    assert contract["cross_task_routing_skill"] == "$hmasd-cross-task-routing"
    assert (
        contract["model_thinking_preservation"]
        == "live_state_probe_explicit_echo"
    )
    assert contract["live_settings_source"] == "read_only_local_codex_state"
    assert contract["live_settings_cache"] == "forbidden"
    assert contract["routine_postcheck"] == "forbidden"
    assert (
        contract["settings_drift_action"]
        == "diagnose_once_after_send_error_or_observed_anomaly_no_resend"
    )
    forbidden = {
        "operator_task_id",
        "operator_model",
        "operator_effort",
        "project_manager_return_task_id",
        "project_manager_return_model",
        "project_manager_return_effort",
    }
    assert forbidden.isdisjoint(contract)


def _make_state(path: Path, cwd: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE threads ("
        "id TEXT PRIMARY KEY, cwd TEXT, archived INTEGER, model TEXT, "
        "reasoning_effort TEXT, updated_at_ms INTEGER)"
    )
    connection.executemany(
        "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?)",
        (
            ("live", str(cwd), 0, "gpt-5.6-sol", "xhigh", 100),
            ("archived", str(cwd), 1, "gpt-5.6-sol", "xhigh", 101),
            ("incomplete", str(cwd), 0, "gpt-5.6-sol", None, 102),
        ),
    )
    connection.commit()
    connection.close()


def _probe(state: Path, cwd: Path, thread_id: str, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        (
            sys.executable,
            str(PROBE),
            "--state-db",
            str(state),
            "--thread-id",
            thread_id,
            "--expect-cwd",
            str(cwd),
            *extra,
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


def test_live_settings_probe_is_read_only_and_supports_anomaly_diagnostic(
    tmp_path: Path,
) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    state = tmp_path / "state.sqlite"
    _make_state(state, cwd)
    before = state.read_bytes()

    code, payload = _probe(state, cwd, "live")
    assert code == 0
    assert payload["status"] == "LIVE_SETTINGS"
    assert payload["model"] == "gpt-5.6-sol"
    assert payload["thinking"] == "xhigh"

    code, payload = _probe(
        state,
        cwd,
        "live",
        "--expect-model",
        "gpt-5.6-sol",
        "--expect-thinking",
        "medium",
    )
    assert code != 0
    assert payload["status"] == "SETTINGS_DRIFT"
    assert state.read_bytes() == before


def test_live_settings_probe_fails_closed(tmp_path: Path) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    state = tmp_path / "state.sqlite"
    _make_state(state, cwd)

    expected = {
        "missing": "THREAD_NOT_FOUND",
        "archived": "THREAD_ARCHIVED",
        "incomplete": "THREAD_SETTINGS_INCOMPLETE",
    }
    for thread_id, status in expected.items():
        code, payload = _probe(state, cwd, thread_id)
        assert code != 0
        assert payload["status"] == status

    other = tmp_path / "other"
    other.mkdir()
    code, payload = _probe(state, other, "live")
    assert code != 0
    assert payload["status"] == "THREAD_WORKSPACE_MISMATCH"
