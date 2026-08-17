"""Behavioral tests for ACTIVE typed subagent lifecycle hooks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.codex_semantic_mvp.hook_entry import handle_hook
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def valid_message(workflow_id: str, task_id: str) -> str:
    packet = {
        "schema_version": "1.0",
        "packet_kind": "SUBAGENT_RETURN",
        "workflow_id": workflow_id,
        "task_id": task_id,
        "return_kind": "COMPLETED_ASSIGNMENT",
        "observed_facts": [],
        "interpretive_claims": [],
        "remaining_unknowns": [],
        "suggested_next_actions": [],
        "research_frontier": None,
        "global_disposition": "NOT_ASSERTED",
    }
    return "evidence prose\n<HMASD_SUBAGENT_RETURN_V1>" + json.dumps(packet) + "</HMASD_SUBAGENT_RETURN_V1>"


def payload(event: str, **extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "hook_event_name": event,
        "session_id": "session-active",
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "agent_type": "default",
        "stop_hook_active": False,
    }
    value.update(extra)
    return value


def managed(store: SemanticStore) -> tuple[str, str]:
    workflow_id = store.open_workflow(
        session_id="session-active",
        opened_turn_id="turn-open",
        scope="test",
        objective="test objective",
    )
    task_id = store.register_task(workflow_id, "task-1", "default", "child task")
    return workflow_id, task_id


def test_unmanaged_start_is_noop(store: SemanticStore) -> None:
    result = handle_hook(payload("SubagentStart", session_id=""), "active", store)
    assert result in (None, {"continue": True})
    assert result is None or "additionalContext" not in result


def test_session_start_opens_always_on_workflow(store: SemanticStore) -> None:
    result = handle_hook(payload("SessionStart"), "active", store)
    assert result == {"continue": True}
    workflow = store.connection.execute(
        "SELECT * FROM workflows WHERE session_id = ? AND state = 'ACTIVE'",
        ("session-active",),
    ).fetchone()
    assert workflow is not None
    assert workflow["scope"] == "session"
    assert workflow["objective"] == "always-on managed semantic session"


def test_subagent_start_auto_opens_and_adds_contract(store: SemanticStore) -> None:
    result = handle_hook(payload("SubagentStart"), "active", store)
    assert result and result["continue"] is True
    assert "HMASD_SUBAGENT_RETURN_V1" in result["additionalContext"]
    second = handle_hook(payload("SubagentStart"), "active", store)
    assert second and "HMASD_SUBAGENT_RETURN_V1" in second["additionalContext"]
    count = store.connection.execute(
        "SELECT COUNT(*) FROM workflows WHERE session_id = ? AND state = 'ACTIVE'",
        ("session-active",),
    ).fetchone()[0]
    assert count == 1


def test_stop_autocompletes_empty_always_on_workflow(store: SemanticStore) -> None:
    handle_hook(payload("SessionStart"), "active", store)
    result = handle_hook(payload("Stop"), "active", store)
    assert result == {"continue": True}
    row = store.connection.execute(
        "SELECT state FROM workflows WHERE session_id = ?",
        ("session-active",),
    ).fetchone()
    assert row["state"] == "CLOSED"


def test_managed_start_adds_generic_contract(store: SemanticStore) -> None:
    managed(store)
    result = handle_hook(payload("SubagentStart"), "active", store)
    assert result and result["continue"] is True
    context = result["additionalContext"]
    assert isinstance(context, str)
    assert "This parent session is using the HMASD managed semantic protocol." in context
    assert "end with exactly one HMASD_SUBAGENT_RETURN_V1 envelope" in context
    assert "LOCAL_AUTHORITY_BOUNDARY" in context


def test_valid_report_is_allowed_and_creates_obligation(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    result = handle_hook(
        payload("SubagentStop", last_assistant_message=valid_message(workflow_id, task_id)),
        "active",
        store,
    )
    assert result == {"continue": True}
    state = store.workflow_state(workflow_id)
    assert state["tasks"][0]["lifecycle"] == "RETURNED_TYPED"
    assert state["obligation_count"] == 1
    assert store.events_after(workflow_id)[-1]["kind"] == "REPORT_AVAILABLE"


def test_missing_report_repairs_once_then_returns_untyped(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    first = handle_hook(
        payload("SubagentStop", task_id=task_id, last_assistant_message="BLOCKED; stop everything"),
        "active",
        store,
    )
    assert first and first["decision"] == "block"
    assert "Do not redo the investigation" in first["reason"]
    assert "workflow_id" in first["reason"]
    assert "global_disposition" in first["reason"]
    assert all(word not in first["reason"] for word in ("BLOCKED", "stop everything"))

    second = handle_hook(
        payload(
            "SubagentStop",
            task_id=task_id,
            stop_hook_active=True,
            last_assistant_message="BLOCKED; stop everything",
        ),
        "active",
        store,
    )
    assert second == {"continue": True}
    assert store.workflow_state(workflow_id)["tasks"][0]["lifecycle"] == "RETURNED_UNTYPED"
    assert store.events_after(workflow_id)[-1]["kind"] == "UNTYPED_REPORT_AVAILABLE"


def test_changed_invalid_message_cannot_get_second_repair_block(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    first = handle_hook(
        payload("SubagentStop", task_id=task_id, last_assistant_message="first invalid output"),
        "active",
        store,
    )
    assert first and first["decision"] == "block"

    second = handle_hook(
        payload(
            "SubagentStop",
            task_id=task_id,
            last_assistant_message="a different invalid output",
        ),
        "active",
        store,
    )
    assert second == {"continue": True}
    assert store.workflow_state(workflow_id)["tasks"][0]["lifecycle"] == "RETURNED_UNTYPED"
    assert [event["kind"] for event in store.events_after(workflow_id)].count(
        "REPORT_FORMAT_REPAIR_REQUESTED"
    ) == 1


def test_binding_mismatch_is_audited_and_not_recorded(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    result = handle_hook(
        payload(
            "SubagentStop",
            agent_type="wrong-agent",
            task_id=task_id,
            last_assistant_message=valid_message(workflow_id, task_id),
        ),
        "active",
        store,
    )
    assert result == {"continue": True}
    assert store.workflow_state(workflow_id)["tasks"][0]["lifecycle"] == "DECLARED"
    assert store.events_after(workflow_id)[-1]["kind"] == "HOOK_BINDING_MISMATCH"


def test_already_bound_agent_is_preserved_as_untyped(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    store.record_agent_started(workflow_id, task_id, "agent-original", "default")
    result = handle_hook(
        payload(
            "SubagentStop",
            agent_id="agent-other",
            task_id=task_id,
            last_assistant_message=valid_message(workflow_id, task_id),
        ),
        "active",
        store,
    )
    assert result == {"continue": True}
    task = store.workflow_state(workflow_id)["tasks"][0]
    assert task["agent_id"] == "agent-original"
    assert task["lifecycle"] == "RETURNED_UNTYPED"
    assert store.events_after(workflow_id)[-1]["kind"] == "HOOK_BINDING_MISMATCH"


def test_active_template_uses_active_mode(repo_root: Path) -> None:
    template = json.loads(
        (repo_root / ".codex" / "hooks.semantic-mvp.active.json").read_text(encoding="utf-8")
    )
    for groups in template["hooks"].values():
        assert groups[0]["hooks"][0]["command"].endswith("--mode active")


def test_stop_blocks_once_for_running_required_task(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    store.record_agent_started(workflow_id, task_id, "agent-1", "default")

    result = handle_hook(payload("Stop"), "active", store)

    assert result and result["decision"] == "block"
    assert "HMASD_OBLIGATION_CONTINUATION_V1" in result["reason"]
    assert store.events_after(workflow_id)[-1]["kind"] == "STOP_GUARD_CONTINUATION"


@pytest.mark.parametrize("lifecycle", ["RETURNED_TYPED", "RETURNED_UNTYPED"])
def test_stop_blocks_once_for_report_awaiting_intake(
    store: SemanticStore, lifecycle: str
) -> None:
    workflow_id, task_id = managed(store)
    if lifecycle == "RETURNED_TYPED":
        message = valid_message(workflow_id, task_id)
        handle_hook(payload("SubagentStop", last_assistant_message=message), "active", store)
    else:
        handle_hook(
            payload("SubagentStop", task_id=task_id, last_assistant_message="untyped"),
            "active",
            store,
        )
        handle_hook(
            payload(
                "SubagentStop",
                task_id=task_id,
                stop_hook_active=True,
                last_assistant_message="untyped",
            ),
            "active",
            store,
        )

    result = handle_hook(payload("Stop"), "active", store)

    assert result and result["decision"] == "block"
    assert store.events_after(workflow_id)[-1]["kind"] == "STOP_GUARD_CONTINUATION"


def test_stop_blocks_for_explicit_portfolio_review_obligation(store: SemanticStore) -> None:
    workflow_id, _ = managed(store)
    store.open_obligation(
        workflow_id,
        "PORTFOLIO_REVIEW_REQUIRED",
        "/portfolio",
        "direction-1",
        "review required",
        "test",
    )

    result = handle_hook(payload("Stop"), "active", store)

    assert result and result["decision"] == "block"


def test_stop_allows_after_closure_receipt(store: SemanticStore) -> None:
    workflow_id = store.open_workflow(
        session_id="session-active",
        opened_turn_id="turn-open",
        scope="test",
        objective="test objective",
    )
    store.create_closure_receipt(workflow_id, "COMPLETED", "all work complete")

    result = handle_hook(payload("Stop"), "active", store)

    assert result == {"continue": True}


def test_stop_second_pass_allows_and_records_loop_prevented(store: SemanticStore) -> None:
    workflow_id, _ = managed(store)
    first = handle_hook(payload("Stop"), "active", store)
    second = handle_hook(payload("Stop", stop_hook_active=True), "active", store)

    assert first and first["decision"] == "block"
    assert second == {"continue": True}
    assert store.events_after(workflow_id)[-1]["kind"] == "LOOP_PREVENTED"


def test_stop_state_version_allows_one_new_continuation(store: SemanticStore) -> None:
    workflow_id, task_id = managed(store)
    first = handle_hook(payload("Stop"), "active", store)
    store.record_agent_started(workflow_id, task_id, "agent-1", "default")
    second = handle_hook(payload("Stop"), "active", store)

    assert first and first["decision"] == "block"
    assert second and second["decision"] == "block"
    assert [event["kind"] for event in store.events_after(workflow_id)].count(
        "STOP_GUARD_CONTINUATION"
    ) == 2


def test_stop_store_exception_fails_open_with_exception_class_and_no_secret(
    store: SemanticStore, tmp_path: Path
) -> None:
    managed(store)
    class SecretSQLiteError(RuntimeError):
        pass

    def explode(_workflow_id: str) -> dict[str, object]:
        raise SecretSQLiteError("password=super-secret")

    store.workflow_state = explode  # type: ignore[method-assign]
    result = handle_hook(payload("Stop"), "active", store)

    assert result == {"continue": True}
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "STOP_GUARD_FAIL_OPEN" in audit
    assert "SecretSQLiteError" in audit
    assert "super-secret" not in audit
