"""TDD coverage for the SQLite event and obligation store."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from tools.codex_semantic_mvp.models import (
    IntakeKind,
    ObligationKind,
    ReturnKind,
    SubagentReturnPacket,
)
from tools.codex_semantic_mvp.protocol import ProtocolError
from tools.codex_semantic_mvp.store import SemanticStore


def packet(workflow_id: str, task_id: str) -> SubagentReturnPacket:
    return SubagentReturnPacket(
        schema_version="1.0",
        packet_kind="SUBAGENT_RETURN",
        workflow_id=workflow_id,
        task_id=task_id,
        return_kind=ReturnKind.COMPLETED_ASSIGNMENT,
        observed_facts=(),
        interpretive_claims=(),
        remaining_unknowns=(),
        suggested_next_actions=(),
        research_frontier=None,
        global_disposition="NOT_ASSERTED",
    )


@pytest.fixture
def store(tmp_path):
    result = SemanticStore(tmp_path / "state.sqlite3")
    result.initialize()
    return result


def test_initialize_creates_tables_and_is_idempotent(tmp_path):
    path = tmp_path / "state.sqlite3"
    first = SemanticStore(path)
    first.initialize()
    first_tables = first.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    first.close()

    second = SemanticStore(path)
    second.initialize()
    second_tables = second.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    assert first_tables == second_tables
    assert {row[0] for row in second_tables} >= {
        "schema_meta",
        "workflows",
        "tasks",
        "reports",
        "obligations",
        "intakes",
        "events",
        "hook_guards",
        "closure_receipts",
        "actor_contexts",
        "plan_epochs",
        "semantic_commits",
        "context_checkpoints",
        "reanchor_acks",
        "packet_refs",
    }


def test_connection_enables_foreign_keys_wal_and_full_sync(store):
    assert store.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert store.connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert store.connection.execute("PRAGMA synchronous").fetchone()[0] == 2
    assert store.connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_schema_columns_indexes_and_versioned_reopen_migration(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    legacy = sqlite3.connect(path)
    legacy.execute("CREATE TABLE schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
    legacy.execute("INSERT INTO schema_meta(version, applied_at) VALUES (0, 'legacy')")
    legacy.commit()
    legacy.close()

    reopened = SemanticStore(path).initialize()
    tables = {
        row[0]
        for row in reopened.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert tables >= {
        "schema_meta", "workflows", "tasks", "reports", "obligations",
        "intakes", "events", "hook_guards", "closure_receipts",
        "actor_contexts", "plan_epochs", "semantic_commits",
        "context_checkpoints", "reanchor_acks", "packet_refs",
    }
    expected_columns = {
        "schema_meta": {"version", "applied_at"},
        "workflows": {
            "workflow_id", "session_id", "opened_turn_id", "scope", "objective",
            "state", "state_version", "actor_context_id", "created_at", "updated_at",
        },
        "tasks": {
            "workflow_id", "task_id", "expected_agent_type", "objective", "required",
            "agent_id", "lifecycle", "created_at", "returned_at",
            "child_actor_context_id", "invoker_actor_context_id",
        },
        "reports": {
            "report_id", "workflow_id", "task_id", "agent_id", "agent_type",
            "raw_message", "typed_json", "schema_valid", "raw_sha256", "created_at",
            "reporter_actor_context_id",
        },
        "obligations": {
            "obligation_id", "workflow_id", "kind", "owner", "subject", "reason",
            "source_ref", "state", "resolution_json", "created_at", "resolved_at",
            "owner_actor_context_id", "source_actor_context_id",
        },
        "intakes": {
            "intake_id", "workflow_id", "report_id", "intake_kind", "translation_json",
            "next_action_json", "note", "created_at",
        },
        "events": {
            "seq", "event_id", "workflow_id", "kind", "subject_id", "payload_json",
            "dedupe_key", "created_at", "actor_context_id",
        },
        "hook_guards": {"guard_key", "event_name", "count", "created_at", "updated_at"},
        "closure_receipts": {"receipt_id", "workflow_id", "closure_kind", "summary", "created_at"},
    }
    for table, columns in expected_columns.items():
        actual = {
            row[1] for row in reopened.connection.execute(f"PRAGMA table_info({table})")
        }
        assert actual == columns
    assert reopened.connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'one_active_workflow_per_actor'"
    ).fetchone()
    assert reopened.connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'one_active_workflow_per_session'"
    ).fetchone() is None
    assert reopened.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 2


def test_typed_report_requires_protocol_validation_and_identity(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    with pytest.raises(ProtocolError):
        store.record_report("wf-1", "task-1", "agent-1", "worker", "raw", None)
    malformed = {"schema_version": "1.0", "packet_kind": "SUBAGENT_RETURN"}
    with pytest.raises(ProtocolError):
        store.record_report("wf-1", "task-1", "agent-1", "worker", "raw-2", malformed)
    assert store.connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0
    assert store.workflow_state("wf-1")["tasks"][0]["lifecycle"] == "DECLARED"


def test_one_active_workflow_per_session_is_enforced(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    with pytest.raises(sqlite3.IntegrityError):
        store.open_workflow("wf-2", "session-1", "turn-2", "scope", "objective")


def test_duplicate_subagent_stop_event_is_deduplicated(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    first = store.record_agent_started("wf-1", "task-1", "agent-1", "worker")
    second = store.record_agent_started("wf-1", "task-1", "agent-1", "worker")
    assert first is not None
    assert second is None
    events = store.events_after("wf-1", 0)
    assert [event["kind"] for event in events].count("SUBAGENT_START") == 1


def test_duplicate_report_subagent_stop_is_deduplicated_by_raw_hash(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    raw = "the exact child message"
    first = store.record_report(
        "wf-1", "task-1", "agent-1", "worker", raw, packet("wf-1", "task-1")
    )
    second = store.record_report(
        "wf-1", "task-1", "agent-1", "worker", raw, packet("wf-1", "task-1")
    )
    assert second == first
    assert store.connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 1
    assert store.connection.execute(
        "SELECT COUNT(*) FROM events WHERE kind = 'REPORT_AVAILABLE'"
    ).fetchone()[0] == 1


def test_valid_report_and_root_intake_obligation_commit_together(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    raw = "prose with BLOCKED\n\x00\uFFFD"
    report_id = store.record_report(
        "wf-1", "task-1", "agent-1", "worker", raw, packet("wf-1", "task-1")
    )
    state = store.workflow_state("wf-1")
    assert report_id
    assert state["tasks"][0]["lifecycle"] == "RETURNED_TYPED"
    assert [item["kind"] for item in state["open_obligations"]] == [
        "ROOT_INTAKE_REQUIRED"
    ]
    assert state["open_obligations"][0]["subject"] == report_id


def test_intake_resolves_only_its_report_obligation(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    store.register_task("wf-1", "task-2", "worker", "inspect", True)
    report_id = store.record_report(
        "wf-1", "task-1", "agent-1", "worker", "same raw", packet("wf-1", "task-1")
    )
    unrelated_id = store.open_obligation(
        "wf-1",
        ObligationKind.PORTFOLIO_REVIEW_REQUIRED,
        "portfolio",
        "direction-1",
        "review needed",
        "manual",
    )
    intake_id = store.record_intake(
        "wf-1",
        report_id,
        IntakeKind.INTEGRATE,
        {"exact_observed_fact": "fact", "global_effect": "NONE"},
        {"owner": "/root", "action": "continue"},
        "accepted for intake",
    )
    assert intake_id
    state = store.workflow_state("wf-1")
    assert [item["subject"] for item in state["open_obligations"]] == ["direction-1"]
    assert state["obligation_count"] == 1
    assert unrelated_id
    opened = [
        event for event in store.events_after("wf-1", 0)
        if event["kind"] == "OBLIGATION_OPENED" and event["subject_id"] == unrelated_id
    ]
    assert opened[0]["payload"]["kind"] == ObligationKind.PORTFOLIO_REVIEW_REQUIRED.value


def test_event_sequences_increase_and_raw_report_is_exact(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    store.record_agent_started("wf-1", "task-1", "agent-1", "worker")
    raw = "前缀\r\nBLOCKED\x00\ufffd"
    report_id = store.record_untyped_return(
        "wf-1", "task-1", "agent-1", "worker", raw
    )
    row = store.connection.execute(
        "SELECT raw_message, schema_valid FROM reports WHERE report_id = ?", (report_id,)
    ).fetchone()
    assert row[0] == raw
    assert row[1] == 0
    seqs = [event["seq"] for event in store.events_after("wf-1", 0)]
    assert seqs == sorted(seqs)
    assert len(seqs) == len(set(seqs))


def test_guard_once_returns_true_only_on_first_use(store):
    assert store.acquire_guard_once("session-1:turn-1", "STOP") is True
    assert store.acquire_guard_once("session-1:turn-1", "STOP") is False
    assert store.acquire_guard_once("session-1:turn-1", "STOP") is False


def test_concurrent_events_and_guard_duplicates_are_safe(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")

    connections = [SemanticStore(store.path).initialize() for _ in range(20)]

    def write(pair):
        index, connection = pair
        try:
            event_id = f"event-{index}"
            connection.append_event("wf-1", "CANARY", event_id, {"index": index}, event_id)
            return connection.acquire_guard_once("same-guard", "CANARY")
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(write, enumerate(connections)))
    assert sum(results) == 1
    events = store.events_after("wf-1", 0)
    assert len([event for event in events if event["kind"] == "CANARY"]) == 20


def test_report_obligation_event_are_atomic_on_exception(store, monkeypatch):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    baseline_events = store.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    original = store._insert_obligation

    def explode(*args, **kwargs):
        raise RuntimeError("injected")

    monkeypatch.setattr(store, "_insert_obligation", explode)
    with pytest.raises(RuntimeError, match="injected"):
        store.record_report(
            "wf-1", "task-1", "agent-1", "worker", "raw", packet("wf-1", "task-1")
        )
    assert store.connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0
    assert store.connection.execute("SELECT COUNT(*) FROM obligations").fetchone()[0] == 0
    assert store.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == baseline_events
    monkeypatch.setattr(store, "_insert_obligation", original)


@pytest.mark.parametrize("bad_state", ["SUCCESS", "FAILURE", "BLOCKED", "RETIRED"])
def test_semantic_dispositions_are_not_accepted_as_task_lifecycle(store, bad_state):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", True)
    with pytest.raises(ValueError):
        store._set_task_lifecycle("wf-1", "task-1", bad_state)


def test_empty_session_close_rejects_any_open_task(store):
    store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    store.register_task("wf-1", "task-1", "worker", "inspect", False)
    with pytest.raises(ValueError, match="not complete"):
        store.create_closure_receipt("wf-1", "EMPTY_SESSION_ENDED", "should fail")
    store.record_agent_started("wf-1", "task-1", "agent-1", "worker")
    with pytest.raises(ValueError, match="not complete"):
        store.create_closure_receipt("wf-1", "COMPLETED", "should fail")


def test_current_workflow_prefers_active_then_latest(store):
    first = store.open_workflow("wf-1", "session-1", "turn-1", "scope", "objective")
    assert store.current_workflow("session-1")["workflow_id"] == first
    store.create_closure_receipt(first, "EMPTY_SESSION_ENDED", "empty")
    second = store.open_workflow("wf-2", "session-1", "turn-2", "scope", "next")
    current = store.current_workflow("session-1")
    assert current["workflow_id"] == second
    assert current["state"] == "ACTIVE"
