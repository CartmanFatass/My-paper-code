"""Migration coverage for actor-scoped schema version 2."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from tools.codex_semantic_mvp.db import SCHEMA_STATEMENTS, SCHEMA_VERSION, initialize_database
from tools.codex_semantic_mvp.store import SemanticStore


def _v1_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    connection.execute(
        "INSERT INTO schema_meta(version, applied_at) VALUES (1, ?)",
        (datetime.now(timezone.utc).isoformat(),),
    )
    return connection


def _insert_v1_session(
    connection: sqlite3.Connection,
    *,
    session_id: str,
    workflow_id: str,
    include_task: bool,
) -> dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """INSERT INTO workflows
        (workflow_id, session_id, opened_turn_id, scope, objective, state,
         state_version, created_at, updated_at)
        VALUES (?, ?, 'turn-open', 'scope', 'objective', 'ACTIVE', 1, ?, ?)""",
        (workflow_id, session_id, now, now),
    )
    payload = {"hook_event_name": "SessionStart", "note": "keep-bytes"}
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    connection.execute(
        """INSERT INTO events
        (event_id, workflow_id, kind, subject_id, payload_json, dedupe_key, created_at)
        VALUES (?, ?, 'SESSION_STARTED', ?, ?, ?, ?)""",
        (f"evt-{session_id}", workflow_id, session_id, payload_json, f"HOOK:{session_id}", now),
    )
    result = {"workflow_id": workflow_id, "payload_json": payload_json}
    if include_task:
        connection.execute(
            """INSERT INTO tasks
            (workflow_id, task_id, expected_agent_type, objective, required, lifecycle, created_at)
            VALUES (?, 'task-1', 'worker', 'inspect', 1, 'DECLARED', ?)""",
            (workflow_id, now),
        )
        connection.execute(
            """INSERT INTO reports
            (report_id, workflow_id, task_id, agent_id, agent_type, raw_message, typed_json,
             schema_valid, raw_sha256, created_at)
            VALUES ('rep-1', ?, 'task-1', 'agent-1', 'worker', 'raw', NULL, 0, 'abc', ?)""",
            (workflow_id, now),
        )
        connection.execute(
            """INSERT INTO obligations
            (obligation_id, workflow_id, kind, owner, subject, reason, source_ref, state, created_at)
            VALUES ('obl-1', ?, 'ROOT_INTAKE_REQUIRED', '/root', 'rep-1',
                    'needs intake', 'rep-1', 'OPEN', ?)""",
            (workflow_id, now),
        )
        result.update({"task_id": "task-1", "report_id": "rep-1", "obligation_id": "obl-1"})
    return result


def test_schema_version_is_two_on_fresh_initialize(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    assert SCHEMA_VERSION == 2
    assert store.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 2
    store.close()


def test_v1_database_migrates_without_losing_rows(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    legacy = _v1_connection(path)
    first = _insert_v1_session(
        legacy, session_id="session-a", workflow_id="wf-a", include_task=True
    )
    second = _insert_v1_session(
        legacy, session_id="session-b", workflow_id="wf-b", include_task=False
    )
    legacy.commit()
    before_payloads = {
        row["event_id"]: row["payload_json"]
        for row in legacy.execute("SELECT event_id, payload_json FROM events")
    }
    legacy.close()

    store = SemanticStore(path).initialize()
    actors = store.connection.execute(
        """SELECT session_id, actor_kind, scope_key, identity_source, state
        FROM actor_contexts ORDER BY session_id"""
    ).fetchall()
    assert [tuple(row) for row in actors] == [
        ("session-a", "SESSION_ROOT_UNCLASSIFIED", "session:session-a", "MIGRATION_V1", "ACTIVE"),
        ("session-b", "SESSION_ROOT_UNCLASSIFIED", "session:session-b", "MIGRATION_V1", "ACTIVE"),
    ]
    workflows = {
        row["workflow_id"]: row["actor_context_id"]
        for row in store.connection.execute("SELECT workflow_id, actor_context_id FROM workflows")
    }
    assert workflows["wf-a"]
    assert workflows["wf-b"]
    assert workflows["wf-a"] != workflows["wf-b"]
    obligation = store.connection.execute(
        "SELECT owner_actor_context_id FROM obligations WHERE obligation_id = 'obl-1'"
    ).fetchone()
    assert obligation[0] == workflows["wf-a"]
    after_payloads = {
        row["event_id"]: row["payload_json"]
        for row in store.connection.execute("SELECT event_id, payload_json FROM events")
    }
    assert after_payloads == before_payloads
    assert first["payload_json"] == after_payloads["evt-session-a"]
    assert second["payload_json"] == after_payloads["evt-session-b"]
    assert store.connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'one_active_workflow_per_session'"
    ).fetchone() is None
    assert store.connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'one_active_workflow_per_actor'"
    ).fetchone()
    store.close()


def test_active_workflow_uniqueness_is_actor_local(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    store.open_workflow("wf-1", "session-shared", "turn-1", "scope", "objective")
    actor_a = store.connection.execute(
        "SELECT actor_context_id FROM workflows WHERE workflow_id = 'wf-1'"
    ).fetchone()[0]
    now = datetime.now(timezone.utc).isoformat()
    actor_b = "actor_other"
    store.connection.execute(
        """INSERT INTO actor_contexts (
            actor_context_id, session_id, actor_kind, scope_key, identity_source,
            state, created_at, updated_at
        ) VALUES (?, 'session-shared', 'EM', 'direction:risp', 'TEST', 'ACTIVE', ?, ?)""",
        (actor_b, now, now),
    )
    store.connection.execute(
        """INSERT INTO workflows
        (workflow_id, session_id, opened_turn_id, scope, objective, state,
         state_version, actor_context_id, created_at, updated_at)
        VALUES ('wf-2', 'session-shared', 'turn-2', 'scope', 'objective', 'ACTIVE', 1, ?, ?, ?)""",
        (actor_b, now, now),
    )
    store.connection.commit()
    active = store.connection.execute(
        "SELECT workflow_id FROM workflows WHERE session_id = 'session-shared' AND state = 'ACTIVE'"
    ).fetchall()
    assert {row[0] for row in active} == {"wf-1", "wf-2"}
    try:
        store.connection.execute(
            """INSERT INTO workflows
            (workflow_id, session_id, opened_turn_id, scope, objective, state,
             state_version, actor_context_id, created_at, updated_at)
            VALUES ('wf-3', 'session-shared', 'turn-3', 'scope', 'objective', 'ACTIVE', 1, ?, ?, ?)""",
            (actor_a, now, now),
        )
        store.connection.commit()
        raise AssertionError("expected unique actor workflow constraint")
    except sqlite3.IntegrityError:
        store.connection.rollback()
    store.close()
