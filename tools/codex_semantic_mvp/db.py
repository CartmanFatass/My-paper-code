"""SQLite connection and migration helpers for the semantic MVP.

This database is a delivery and obligation ledger for the control plane.
It is not scientific truth and must not be treated as canonical project memory.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_STATE_PATH = Path("runtime/codex-semantic-mvp/state.sqlite3")
SCHEMA_VERSION = 3

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workflows (
        workflow_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        opened_turn_id TEXT NOT NULL,
        scope TEXT NOT NULL,
        objective TEXT NOT NULL,
        state TEXT NOT NULL,
        state_version INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS one_active_workflow_per_session
    ON workflows(session_id) WHERE state = 'ACTIVE'
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        workflow_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        expected_agent_type TEXT NOT NULL,
        objective TEXT NOT NULL,
        required INTEGER NOT NULL,
        agent_id TEXT,
        lifecycle TEXT NOT NULL,
        created_at TEXT NOT NULL,
        returned_at TEXT,
        PRIMARY KEY (workflow_id, task_id),
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        agent_type TEXT NOT NULL,
        raw_message TEXT NOT NULL,
        typed_json TEXT,
        schema_valid INTEGER NOT NULL,
        raw_sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(workflow_id, task_id, raw_sha256),
        FOREIGN KEY (workflow_id, task_id) REFERENCES tasks(workflow_id, task_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS obligations (
        obligation_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        owner TEXT NOT NULL,
        subject TEXT NOT NULL,
        reason TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        state TEXT NOT NULL,
        resolution_json TEXT,
        created_at TEXT NOT NULL,
        resolved_at TEXT,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intakes (
        intake_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        report_id TEXT NOT NULL UNIQUE,
        intake_kind TEXT NOT NULL,
        translation_json TEXT NOT NULL,
        next_action_json TEXT,
        note TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id),
        FOREIGN KEY (report_id) REFERENCES reports(report_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        workflow_id TEXT,
        kind TEXT NOT NULL,
        subject_id TEXT,
        payload_json TEXT NOT NULL,
        dedupe_key TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS hook_guards (
        guard_key TEXT PRIMARY KEY,
        event_name TEXT NOT NULL,
        count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS closure_receipts (
        receipt_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL UNIQUE,
        closure_kind TEXT NOT NULL,
        summary TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
)


def connect(path: str | Path = DEFAULT_STATE_PATH) -> sqlite3.Connection:
    """Open a configured SQLite connection, creating its parent directory."""
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        str(db_path), timeout=5.0, check_same_thread=False, isolation_level="DEFERRED"
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


SCHEMA_V2_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS actor_contexts (
        actor_context_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        agent_id TEXT,
        canonical_path TEXT,
        actor_kind TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        direction_id TEXT,
        parent_actor_context_id TEXT,
        counterpart_actor_context_id TEXT,
        identity_source TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_actor_agent
    ON actor_contexts(session_id, agent_id)
    WHERE agent_id IS NOT NULL AND agent_id <> ''
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_actor_path
    ON actor_contexts(session_id, canonical_path)
    WHERE canonical_path IS NOT NULL AND canonical_path <> ''
    """,
    """
    CREATE TABLE IF NOT EXISTS plan_epochs (
        epoch_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_kind TEXT NOT NULL,
        revision INTEGER NOT NULL,
        objective TEXT NOT NULL,
        authority_refs_json TEXT NOT NULL,
        frozen_invariants_json TEXT NOT NULL,
        exit_boundary TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS one_open_epoch_per_actor
    ON plan_epochs(actor_context_id)
    WHERE state = 'OPEN'
    """,
    """
    CREATE TABLE IF NOT EXISTS semantic_commits (
        semantic_commit_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_id TEXT NOT NULL,
        commit_kind TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        source_refs_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS context_checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_id TEXT,
        epoch_revision INTEGER,
        state_version INTEGER NOT NULL,
        semantic_commit_id TEXT,
        capsule_kind TEXT NOT NULL,
        capsule_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(actor_context_id, epoch_id, epoch_revision, state_version, semantic_commit_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reanchor_acks (
        ack_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        checkpoint_id TEXT NOT NULL,
        state_version INTEGER NOT NULL,
        epoch_id TEXT,
        epoch_revision INTEGER,
        actor_turn_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(actor_context_id, checkpoint_id, actor_turn_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS packet_refs (
        packet_id TEXT PRIMARY KEY,
        packet_kind TEXT NOT NULL,
        source_actor_context_id TEXT NOT NULL,
        target_actor_context_id TEXT NOT NULL,
        direction_id TEXT,
        marker TEXT NOT NULL UNIQUE,
        payload_ref TEXT NOT NULL,
        delivery_state TEXT NOT NULL,
        intake_state TEXT NOT NULL,
        decision_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
)

V2_COLUMNS = {
    "workflows": (("actor_context_id", "TEXT"),),
    "tasks": (("child_actor_context_id", "TEXT"), ("invoker_actor_context_id", "TEXT")),
    "reports": (("reporter_actor_context_id", "TEXT"),),
    "obligations": (
        ("owner_actor_context_id", "TEXT"),
        ("source_actor_context_id", "TEXT"),
    ),
    "events": (("actor_context_id", "TEXT"),),
}

SCHEMA_V3_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS promotion_proposals (
        promotion_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_id TEXT NOT NULL,
        promotion_kind TEXT NOT NULL,
        target_ref TEXT,
        summary TEXT NOT NULL,
        rationale TEXT NOT NULL,
        source_refs_json TEXT NOT NULL,
        owner_actor_context_id TEXT NOT NULL,
        state TEXT NOT NULL,
        disposition_json TEXT,
        canonical_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS epoch_rollovers (
        rollover_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        from_epoch_id TEXT NOT NULL,
        from_epoch_revision INTEGER NOT NULL,
        next_epoch_kind TEXT NOT NULL,
        next_objective TEXT NOT NULL,
        carry_obligation_ids_json TEXT NOT NULL,
        carry_packet_ids_json TEXT NOT NULL,
        carry_frontier_json TEXT NOT NULL,
        promotion_ids_json TEXT NOT NULL,
        forgotten_refs_json TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        applied_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS context_retention_marks (
        retention_mark_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        object_kind TEXT NOT NULL,
        object_id TEXT NOT NULL,
        retention_class TEXT NOT NULL,
        active_in_working_set INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL,
        archived_at TEXT,
        UNIQUE(actor_context_id, object_kind, object_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS context_gc_runs (
        gc_run_id TEXT PRIMARY KEY,
        actor_context_id TEXT,
        mode TEXT NOT NULL,
        plan_json TEXT NOT NULL,
        applied INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
)

V3_COLUMNS = {
    "plan_epochs": (
        ("navigation_refs_json", "TEXT"),
        ("procedure_refs_json", "TEXT"),
    ),
}


def _apply_schema_v1(connection: sqlite3.Connection) -> None:
    """Create or repair the version-1 schema, without dropping user data."""
    has_actor_index = connection.execute(
        """SELECT 1 FROM sqlite_master
        WHERE type = 'index' AND name = 'one_active_workflow_per_actor'"""
    ).fetchone()
    for statement in SCHEMA_STATEMENTS[1:]:
        if has_actor_index and "one_active_workflow_per_session" in statement:
            continue
        connection.execute(statement)


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table})")
    }


def migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
    """Add actor-scoped objects without rewriting historical payload bytes."""
    from datetime import datetime, timezone
    import uuid

    for statement in SCHEMA_V2_TABLES:
        connection.execute(statement)
    for table, columns in V2_COLUMNS.items():
        existing = _column_names(connection, table)
        for name, decl in columns:
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    now = datetime.now(timezone.utc).isoformat()
    sessions = connection.execute(
        "SELECT DISTINCT session_id FROM workflows ORDER BY session_id"
    ).fetchall()
    for (session_id,) in sessions:
        if not session_id:
            continue
        existing_actor = connection.execute(
            """SELECT actor_context_id FROM actor_contexts
            WHERE session_id = ? AND actor_kind = 'SESSION_ROOT_UNCLASSIFIED'""",
            (session_id,),
        ).fetchone()
        if existing_actor is None:
            actor_id = f"actor_{uuid.uuid4().hex}"
            connection.execute(
                """INSERT INTO actor_contexts (
                    actor_context_id, session_id, agent_id, canonical_path, actor_kind,
                    scope_key, direction_id, parent_actor_context_id,
                    counterpart_actor_context_id, identity_source, state,
                    created_at, updated_at
                ) VALUES (?, ?, NULL, NULL, 'SESSION_ROOT_UNCLASSIFIED', ?, NULL, NULL, NULL,
                          'MIGRATION_V1', 'ACTIVE', ?, ?)""",
                (actor_id, session_id, f"session:{session_id}", now, now),
            )
        else:
            actor_id = existing_actor[0]
        connection.execute(
            """UPDATE workflows SET actor_context_id = ?
            WHERE session_id = ? AND (actor_context_id IS NULL OR actor_context_id = '')""",
            (actor_id, session_id),
        )
        connection.execute(
            """UPDATE obligations SET owner_actor_context_id = (
                SELECT actor_context_id FROM workflows
                WHERE workflows.workflow_id = obligations.workflow_id
            )
            WHERE owner_actor_context_id IS NULL OR owner_actor_context_id = ''""",
        )

    connection.execute("DROP INDEX IF EXISTS one_active_workflow_per_session")
    connection.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS one_active_workflow_per_actor
        ON workflows(actor_context_id)
        WHERE state = 'ACTIVE'"""
    )


def migrate_v2_to_v3(connection: sqlite3.Connection) -> None:
    """Add promotion, rollover, and retention objects without deleting rows."""
    for statement in SCHEMA_V3_TABLES:
        connection.execute(statement)
    for table, columns in V3_COLUMNS.items():
        existing = _column_names(connection, table)
        for name, decl in columns:
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    connection.execute(
        "UPDATE plan_epochs SET navigation_refs_json = '[]' WHERE navigation_refs_json IS NULL"
    )
    connection.execute(
        "UPDATE plan_epochs SET procedure_refs_json = '[]' WHERE procedure_refs_json IS NULL"
    )


def initialize_database(connection: sqlite3.Connection) -> None:
    """Apply the idempotent, versioned MVP schema in one transaction."""
    from datetime import datetime, timezone

    applied_at = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute(SCHEMA_STATEMENTS[0])
        current = connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0]
        current = int(current or 0)
        if current > SCHEMA_VERSION:
            raise RuntimeError(
                f"database schema version {current} is newer than supported {SCHEMA_VERSION}"
            )
        # Version 0 is the pre-migration marker used by the first draft.  The
        # migration only creates missing objects and never drops or rewrites
        # existing rows, so reopening an interrupted/partial database is safe.
        _apply_schema_v1(connection)
        if current < 2:
            migrate_v1_to_v2(connection)
        if current < 3:
            migrate_v2_to_v3(connection)
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_meta(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, applied_at),
            )
