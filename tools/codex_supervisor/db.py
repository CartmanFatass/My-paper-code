"""Observer SQLite ledger. Independent from the semantic control-plane database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS observer_runs (
        run_id TEXT PRIMARY KEY,
        codex_binary TEXT NOT NULL,
        codex_version TEXT NOT NULL,
        client_name TEXT NOT NULL,
        process_id INTEGER,
        started_at TEXT NOT NULL,
        initialized_at TEXT,
        ended_at TEXT,
        exit_code INTEGER,
        end_kind TEXT,
        runtime_home TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_messages (
        raw_message_seq INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        direction TEXT NOT NULL,
        transport_seq INTEGER NOT NULL,
        rpc_shape TEXT NOT NULL,
        request_id TEXT,
        method TEXT,
        thread_id TEXT,
        turn_id TEXT,
        item_id TEXT,
        canonical_json TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        UNIQUE(run_id, direction, transport_seq),
        FOREIGN KEY(run_id) REFERENCES observer_runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rpc_requests (
        request_row_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        client_request_id TEXT NOT NULL,
        method TEXT NOT NULL,
        request_class TEXT NOT NULL,
        params_json TEXT NOT NULL,
        attempt_count INTEGER NOT NULL,
        sent_at TEXT NOT NULL,
        completed_at TEXT,
        outcome TEXT,
        error_code INTEGER,
        response_json TEXT,
        UNIQUE(run_id, client_request_id),
        FOREIGN KEY(run_id) REFERENCES observer_runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS normalized_events (
        event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        raw_message_seq INTEGER NOT NULL,
        event_kind TEXT NOT NULL,
        thread_id TEXT,
        turn_id TEXT,
        item_id TEXT,
        mechanical_status TEXT,
        payload_json TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        UNIQUE(run_id, raw_message_seq),
        FOREIGN KEY(run_id) REFERENCES observer_runs(run_id),
        FOREIGN KEY(raw_message_seq) REFERENCES raw_messages(raw_message_seq)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS thread_snapshots (
        thread_id TEXT PRIMARY KEY,
        status_type TEXT,
        preview TEXT,
        ephemeral INTEGER,
        path TEXT,
        last_event_seq INTEGER,
        first_observed_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS turn_snapshots (
        turn_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        status TEXT,
        error_json TEXT,
        started_at TEXT,
        completed_at TEXT,
        last_event_seq INTEGER,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS item_snapshots (
        item_id TEXT PRIMARY KEY,
        thread_id TEXT,
        turn_id TEXT,
        item_type TEXT,
        lifecycle TEXT NOT NULL,
        safe_metadata_json TEXT NOT NULL,
        last_event_seq INTEGER,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS server_requests (
        server_request_row_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        server_request_id TEXT NOT NULL,
        method TEXT NOT NULL,
        thread_id TEXT,
        turn_id TEXT,
        request_json TEXT NOT NULL,
        handling TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        process_terminated_at TEXT,
        UNIQUE(run_id, server_request_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reconciliation_runs (
        reconciliation_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        thread_count INTEGER,
        outcome TEXT,
        error_json TEXT
    )
    """,
)

REQUIRED_TABLES = (
    "schema_meta",
    "observer_runs",
    "raw_messages",
    "rpc_requests",
    "normalized_events",
    "thread_snapshots",
    "turn_snapshots",
    "item_snapshots",
    "server_requests",
    "reconciliation_runs",
)


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    applied_at = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute(SCHEMA_STATEMENTS[0])
        current = connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0]
        current = int(current or 0)
        if current > SCHEMA_VERSION:
            raise RuntimeError(
                f"observer schema version {current} is newer than supported {SCHEMA_VERSION}"
            )
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_meta(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, applied_at),
            )
