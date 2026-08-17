"""SQLite connection and migration helpers for the semantic MVP.

This database is a delivery and obligation ledger for the control plane.
It is not scientific truth and must not be treated as canonical project memory.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_STATE_PATH = Path("runtime/codex-semantic-mvp/state.sqlite3")
SCHEMA_VERSION = 1

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


def _apply_schema_v1(connection: sqlite3.Connection) -> None:
    """Create or repair the version-1 schema, without dropping user data."""
    for statement in SCHEMA_STATEMENTS[1:]:
        connection.execute(statement)


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
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_meta(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, applied_at),
            )
