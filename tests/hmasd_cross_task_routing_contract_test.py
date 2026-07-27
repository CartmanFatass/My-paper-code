from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-cross-task-routing/SKILL.md"
UI = ROOT / ".agents/skills/hmasd-cross-task-routing/agents/openai.yaml"
PROBE = (
    ROOT / ".agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py"
)
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/RESEARCH_OPERATIONS_MANAGER.md",
)
PAYLOAD_SURFACES = PERSISTENT_ROLES + (
    ROOT / ".agents/skills/hmasd-review-round/SKILL.md",
    ROOT / ".agents/skills/hmasd-review-round/agents/openai.yaml",
)


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "Fixed session addresses",
        "fixed session addresses only",
        "Pre-send live-settings preservation",
        "SQLite `mode=ro`",
        "visible `send_message_to_thread`",
        "returned `model` as `model`",
        "returned `thinking` as `thinking`",
        "ROUTE_SENT",
        "ROUTE_SOURCE_MISMATCH",
        "ROUTE_UNAVAILABLE",
        "ROUTE_SETTINGS_UNAVAILABLE",
        "ROUTE_SETTINGS_DRIFT",
        "codex_delegation.source_thread_id",
        "explicit user-directed workflow-design commit",
        "live_target_model",
        "live_target_effort",
        "live_target_thinking",
        "never retry or resend automatically",
    )
    for token in required:
        assert token in text, token
    for retired in (
        "ROLE_ROUTE_PROBE",
        "ROLE_ROUTE_CONFIRM",
        "ROLE_ROUTE_ANNOUNCE",
        "Conversation-local route cache",
        "fixed route triples",
        "user supplies the new session, model and effort",
    ):
        assert retired not in text, retired


def test_cross_task_routing_skill_is_explicit_only() -> None:
    interface = yaml.safe_load(UI.read_text(encoding="utf-8"))
    assert interface["policy"]["allow_implicit_invocation"] is False
    assert "$hmasd-cross-task-routing" in interface["interface"]["default_prompt"]


def test_router_contains_fixed_sessions_without_model_or_effort() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")
    required = (
        "cross_task_routing=fixed_role_sessions_plus_pre_send_live_settings_probe",
        "cross_task_model_thinking_preservation=pre_send_read_only_probe_explicit_echo",
        "workflow_design_manager_session=019f9d2f-e0ea-7411-9fd7-386f45f76909",
        "code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d",
        "research_operations_manager_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b",
    )
    for token in required:
        assert agents.count(token) == 1, token
    for session in (
        "019f9d2f-e0ea-7411-9fd7-386f45f76909",
        "019f9e4f-f4d0-7fe0-b214-c47fd034e84d",
        "019f9c6a-9401-7ae0-ace5-dd827dccba2b",
    ):
        assert skill.count(session) == 1, session
    for retired in (
        "workflow_design_manager_route=",
        "code_project_manager_route=",
        "research_operations_manager_route=",
    ):
        assert retired not in agents, retired


def test_persistent_roles_use_fixed_sessions_and_live_settings_without_cache() -> None:
    for path in PERSISTENT_ROLES:
        text = path.read_text(encoding="utf-8")
        assert "cross_task_routing_skill=hmasd-cross-task-routing" in text
        assert (
            "cross_task_target_identity=fixed_router_role_session" in text
            or "cross_task_target_identity=exact_fixed_requester_role_session" in text
        )
        assert "cross_task_route_cache=forbidden" in text
        assert (
            "cross_task_model_thinking_preservation="
            "pre_send_read_only_probe_explicit_echo"
        ) in text


def test_review_registry_is_local_to_operations_manager_transport() -> None:
    registry = json.loads(
        (ROOT / "docs/external-review/REVIEWER_CONVERSATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    contract = registry["transport_contract"]
    assert registry["schema_version"] == 38
    assert contract["transport_owner"] == "research_operations_manager"
    assert "intertask_transport_contract" not in registry
    for retired in (
        "cross_task_routing_skill",
        "target_identity",
        "live_settings_probe",
        "payload_route_settings",
    ):
        assert retired not in contract


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
            ("live", str(cwd), 0, "gpt-5.6-sol", "medium", 100),
            ("archived", str(cwd), 1, "gpt-5.6-sol", "high", 101),
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


def test_live_settings_probe_is_read_only_and_supports_drift_diagnostic(
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
    assert payload["thinking"] == "medium"

    code, payload = _probe(
        state,
        cwd,
        "live",
        "--expect-model",
        "gpt-5.6-sol",
        "--expect-thinking",
        "high",
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


def test_route_settings_are_forbidden_from_message_payload_surfaces() -> None:
    for path in PAYLOAD_SURFACES:
        text = path.read_text(encoding="utf-8")
        for forbidden in (
            "live_target_model=",
            "live_target_effort=",
            "live_target_thinking=",
            "return_model=",
            "return_effort=",
        ):
            assert forbidden not in text, (path, forbidden)
