"""Observer SQLite ledger. Independent from the semantic control-plane database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 6

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
        updated_at TEXT NOT NULL,
        preview_present INTEGER,
        preview_byte_length INTEGER
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
    """
    CREATE TABLE IF NOT EXISTS managed_actor_bindings (
        binding_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL UNIQUE,
        actor_kind TEXT NOT NULL,
        semantic_scope_key TEXT NOT NULL,
        direction_id TEXT,
        thread_id TEXT UNIQUE,
        thread_origin TEXT NOT NULL,
        history_trust TEXT NOT NULL,
        binding_state TEXT NOT NULL,
        memory_policy_state TEXT NOT NULL,
        repo_root TEXT NOT NULL,
        thread_cwd TEXT NOT NULL,
        created_by_operator TEXT NOT NULL,
        created_at TEXT NOT NULL,
        thread_created_at TEXT,
        verified_at TEXT,
        activated_at TEXT,
        suspended_at TEXT,
        revoked_at TEXT,
        last_verified_at TEXT,
        last_thread_status TEXT,
        last_turn_id TEXT,
        verification_turn_intent_id TEXT,
        verification_turn_id TEXT,
        verification_command_id TEXT,
        verification_receipt_id TEXT,
        verified_checkpoint_id TEXT,
        verified_state_version INTEGER,
        verified_epoch_id TEXT,
        verified_epoch_revision INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS managed_binding_events (
        binding_event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
        binding_id TEXT NOT NULL,
        event_kind TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS managed_turn_intents (
        turn_intent_id TEXT PRIMARY KEY,
        binding_id TEXT NOT NULL,
        intent_kind TEXT NOT NULL,
        client_user_message_id TEXT NOT NULL UNIQUE,
        checkpoint_id TEXT,
        expected_state_version INTEGER,
        expected_epoch_id TEXT,
        expected_epoch_revision INTEGER,
        input_ref TEXT NOT NULL,
        submission_state TEXT NOT NULL,
        app_server_thread_id TEXT NOT NULL,
        app_server_turn_id TEXT,
        app_server_request_id TEXT,
        prepared_at TEXT NOT NULL,
        submitted_at TEXT,
        observed_at TEXT,
        completed_at TEXT,
        completion_status TEXT,
        incident_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS managed_context_injections (
        injection_id TEXT PRIMARY KEY,
        turn_intent_id TEXT NOT NULL,
        binding_id TEXT NOT NULL,
        checkpoint_id TEXT,
        state_version INTEGER,
        epoch_id TEXT,
        epoch_revision INTEGER,
        canonical_refs_json TEXT NOT NULL,
        open_obligation_ids_json TEXT NOT NULL,
        mailbox_message_ids_json TEXT NOT NULL,
        input_byte_length INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS managed_actor_commands (
        command_id TEXT PRIMARY KEY,
        binding_id TEXT NOT NULL,
        thread_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        raw_message_seq INTEGER NOT NULL,
        command_kind TEXT NOT NULL,
        expected_checkpoint_id TEXT,
        expected_state_version INTEGER,
        expected_epoch_id TEXT,
        expected_epoch_revision INTEGER,
        payload_json TEXT NOT NULL,
        validation_state TEXT NOT NULL,
        rejection_reason TEXT,
        created_at TEXT NOT NULL,
        validated_at TEXT,
        applied_at TEXT,
        UNIQUE(binding_id, turn_id, raw_message_seq)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS managed_command_receipts (
        receipt_id TEXT PRIMARY KEY,
        command_id TEXT NOT NULL UNIQUE,
        effect_kind TEXT NOT NULL,
        semantic_ref TEXT,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mailbox_messages (
        message_id TEXT PRIMARY KEY,
        source_system TEXT NOT NULL,
        source_event_key TEXT NOT NULL UNIQUE,
        sender_actor_context_id TEXT,
        target_actor_context_id TEXT NOT NULL,
        message_kind TEXT NOT NULL,
        subject_ref TEXT NOT NULL,
        payload_ref TEXT NOT NULL,
        direction_id TEXT,
        epoch_id TEXT,
        priority INTEGER NOT NULL,
        delivery_state TEXT NOT NULL,
        intake_state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        eligible_at TEXT,
        batched_at TEXT,
        delivered_at TEXT,
        acknowledged_at TEXT,
        intaken_at TEXT,
        applied_at TEXT,
        dead_letter_reason TEXT,
        source_resolved_after_submission INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS semantic_scan_cursors (
        scanner_id TEXT PRIMARY KEY,
        last_scan_at TEXT,
        last_obligation_observed_at TEXT,
        last_packet_observed_at TEXT,
        last_report_observed_at TEXT,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wake_batches (
        wake_batch_id TEXT PRIMARY KEY,
        binding_id TEXT NOT NULL,
        thread_id TEXT NOT NULL,
        state TEXT NOT NULL,
        client_user_message_id TEXT NOT NULL UNIQUE,
        app_server_request_id TEXT,
        app_server_turn_id TEXT,
        prepared_at TEXT NOT NULL,
        submitted_at TEXT,
        observed_at TEXT,
        completed_at TEXT,
        completion_status TEXT,
        incident_json TEXT,
        lease_generation INTEGER,
        lease_holder TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wake_batch_messages (
        wake_batch_id TEXT NOT NULL,
        message_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL,
        PRIMARY KEY(wake_batch_id, message_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wake_attempts (
        wake_attempt_id TEXT PRIMARY KEY,
        wake_batch_id TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        request_id TEXT,
        outcome TEXT NOT NULL,
        error_json TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(wake_batch_id, attempt_number)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scheduler_leases (
        lease_key TEXT PRIMARY KEY,
        holder_instance_id TEXT NOT NULL,
        acquired_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        generation INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mailbox_command_receipts (
        receipt_id TEXT PRIMARY KEY,
        command_id TEXT NOT NULL,
        message_id TEXT NOT NULL,
        action TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(command_id, message_id, action)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mutation_intents (
        intent_id TEXT PRIMARY KEY,
        method TEXT NOT NULL,
        binding_id TEXT,
        client_key TEXT NOT NULL,
        state TEXT NOT NULL,
        request_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS wake_batches_one_open_per_binding
    ON wake_batches(binding_id)
    WHERE state IN ('PREPARED', 'SUBMITTING', 'SUBMITTED', 'SUBMISSION_UNCERTAIN', 'ACTIVE')
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS mutation_intents_open_unique
    ON mutation_intents(method, client_key)
    WHERE state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED_UNRECONCILED', 'INCIDENT')
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
    "managed_actor_bindings",
    "managed_binding_events",
    "managed_turn_intents",
    "managed_context_injections",
    "managed_actor_commands",
    "managed_command_receipts",
    "mailbox_messages",
    "semantic_scan_cursors",
    "wake_batches",
    "wake_batch_messages",
    "wake_attempts",
    "scheduler_leases",
    "mailbox_command_receipts",
    "mutation_intents",
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


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _add_column_if_missing(connection: sqlite3.Connection, table: str, name: str, decl: str) -> None:
    if table not in {
        str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }:
        return
    if name not in _table_columns(connection, table):
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


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
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_turn_intent_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_turn_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_command_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_receipt_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_checkpoint_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_state_version", "INTEGER")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_epoch_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_epoch_revision", "INTEGER")
        _add_column_if_missing(connection, "mailbox_messages", "source_resolved_after_submission", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "wake_batches", "lease_generation", "INTEGER")
        _add_column_if_missing(connection, "wake_batches", "lease_holder", "TEXT")
        _add_column_if_missing(connection, "thread_snapshots", "preview_present", "INTEGER")
        _add_column_if_missing(connection, "thread_snapshots", "preview_byte_length", "INTEGER")
        connection.execute("DROP INDEX IF EXISTS mutation_intents_open_unique")
        connection.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS mutation_intents_open_unique
            ON mutation_intents(method, client_key)
            WHERE state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED_UNRECONCILED', 'INCIDENT')"""
        )
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_meta(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, applied_at),
            )
