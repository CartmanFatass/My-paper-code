"""Observer SQLite ledger. Independent from the semantic control-plane database."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 12

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
        effect_id TEXT,
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
        effect_id TEXT,
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
        prepared_checkpoint_id TEXT,
        prepared_state_version INTEGER NOT NULL DEFAULT 0,
        prepared_epoch_id TEXT,
        prepared_epoch_revision INTEGER,
        prepared_context_trusted INTEGER NOT NULL DEFAULT 0,
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
        verified_epoch_revision INTEGER,
        version INTEGER NOT NULL DEFAULT 0
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
        incident_json TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        effect_id TEXT
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
        version INTEGER NOT NULL DEFAULT 0,
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
        source_resolved_after_submission INTEGER NOT NULL DEFAULT 0,
        delivery_version INTEGER NOT NULL DEFAULT 0,
        intake_version INTEGER NOT NULL DEFAULT 0
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
        lease_holder TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        effect_id TEXT
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
        updated_at TEXT NOT NULL,
        superseded_by_effect_id TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_server_effects (
        effect_id TEXT PRIMARY KEY,
        owner_kind TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        binding_id TEXT,
        predecessor_effect_id TEXT,
        method TEXT NOT NULL,
        client_key TEXT NOT NULL,
        request_json TEXT NOT NULL,
        state TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 0,
        run_id TEXT,
        client_request_id TEXT,
        request_row_id TEXT,
        raw_request_seq INTEGER,
        transport_seq INTEGER,
        thread_id TEXT,
        turn_id TEXT,
        response_json TEXT,
        incident_json TEXT,
        legacy_intent_id TEXT,
        prepared_at TEXT NOT NULL,
        write_started_at TEXT,
        response_observed_at TEXT,
        confirmed_at TEXT,
        reconciled_at TEXT,
        resolved_at TEXT,
        UNIQUE(method, client_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_server_rpc_sequence (
        singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
        next_id INTEGER NOT NULL CHECK(next_id > 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_server_outbox (
        operation_id TEXT PRIMARY KEY,
        dedupe_key TEXT NOT NULL UNIQUE,
        protocol_session_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        binding_id TEXT,
        target TEXT NOT NULL,
        thread_id TEXT,
        rpc_request_id INTEGER NOT NULL UNIQUE,
        method TEXT NOT NULL,
        wire_bytes BLOB NOT NULL,
        delivery_class TEXT NOT NULL CHECK(delivery_class IN ('MUTATION_AT_MOST_ONCE')),
        state TEXT NOT NULL CHECK(state IN ('READY', 'SENDING', 'DONE', 'UNKNOWN')),
        claim_token TEXT,
        created_at TEXT NOT NULL,
        claimed_at TEXT,
        completed_at TEXT,
        outcome TEXT,
        error TEXT,
        response_raw_ref TEXT,
        CHECK((state = 'SENDING') = (claim_token IS NOT NULL))
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS app_server_outbox_session_state
    ON app_server_outbox(protocol_session_id, state)
    """,
    """
    CREATE TABLE IF NOT EXISTS control_transitions (
        transition_id TEXT PRIMARY KEY,
        aggregate_kind TEXT NOT NULL,
        aggregate_id TEXT NOT NULL,
        state_column TEXT NOT NULL,
        from_state TEXT NOT NULL,
        to_state TEXT NOT NULL,
        from_version INTEGER NOT NULL,
        to_version INTEGER NOT NULL,
        cause_kind TEXT NOT NULL,
        cause_ref TEXT NOT NULL,
        evidence_ref TEXT,
        metadata_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(aggregate_kind, aggregate_id, state_column, to_version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operator_resolutions (
        resolution_id TEXT PRIMARY KEY,
        aggregate_kind TEXT NOT NULL,
        aggregate_id TEXT NOT NULL,
        effect_id TEXT,
        operator TEXT NOT NULL,
        disposition TEXT NOT NULL,
        evidence_kind TEXT NOT NULL,
        evidence_ref TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(aggregate_kind, aggregate_id)
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
    """
    CREATE INDEX IF NOT EXISTS app_server_effect_owner
    ON app_server_effects(owner_kind, owner_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS app_server_effect_binding
    ON app_server_effects(binding_id, state)
    """,
    """
    CREATE INDEX IF NOT EXISTS app_server_effect_request
    ON app_server_effects(run_id, client_request_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS control_transition_aggregate
    ON control_transitions(aggregate_kind, aggregate_id, to_version)
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
    "app_server_effects",
    "control_transitions",
    "operator_resolutions",
    "app_server_rpc_sequence",
    "app_server_outbox",
)


def connect(path: str | Path) -> sqlite3.Connection:
    backup_before_v12(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def backup_before_v12(path: str | Path) -> Path | None:
    """Create the stopped-host rollback database before an additive v12 migration."""
    database = Path(path)
    if not database.exists() or database.stat().st_size == 0:
        return None
    source = sqlite3.connect(str(database))
    try:
        try:
            row = source.execute("SELECT MAX(version) FROM schema_meta").fetchone()
            version = int((row or (0,))[0] or 0)
        except sqlite3.DatabaseError:
            version = 0
        if version >= SCHEMA_VERSION:
            return None
        backup = database.with_name(f"{database.name}.v{version}.rollback")
        if backup.exists():
            return backup
        destination = sqlite3.connect(str(backup))
        try:
            source.backup(destination)
        finally:
            destination.close()
        return backup
    finally:
        source.close()


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
    owns_transaction = not connection.in_transaction
    if owns_transaction:
        connection.execute("BEGIN EXCLUSIVE")
    try:
        connection.execute(SCHEMA_STATEMENTS[0])
        current = connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0]
        current = int(current or 0)
        if current > SCHEMA_VERSION:
            raise RuntimeError(
                f"observer schema version {current} is newer than supported {SCHEMA_VERSION}"
            )
        if current == SCHEMA_VERSION:
            present = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            missing_current = set(REQUIRED_TABLES) - present
            if missing_current:
                raise RuntimeError(
                    f"observer v12 schema is incomplete: {sorted(missing_current)}"
                )
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.execute(
            "INSERT OR IGNORE INTO app_server_rpc_sequence(singleton, next_id) VALUES (1, 1)"
        )
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_turn_intent_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_turn_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_command_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verification_receipt_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_checkpoint_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_state_version", "INTEGER")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_epoch_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "verified_epoch_revision", "INTEGER")
        _add_column_if_missing(connection, "managed_actor_bindings", "prepared_checkpoint_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "prepared_state_version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "managed_actor_bindings", "prepared_epoch_id", "TEXT")
        _add_column_if_missing(connection, "managed_actor_bindings", "prepared_epoch_revision", "INTEGER")
        _add_column_if_missing(connection, "managed_actor_bindings", "prepared_context_trusted", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "mailbox_messages", "source_resolved_after_submission", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "wake_batches", "lease_generation", "INTEGER")
        _add_column_if_missing(connection, "wake_batches", "lease_holder", "TEXT")
        _add_column_if_missing(connection, "thread_snapshots", "preview_present", "INTEGER")
        _add_column_if_missing(connection, "thread_snapshots", "preview_byte_length", "INTEGER")
        _add_column_if_missing(connection, "managed_actor_bindings", "version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "managed_turn_intents", "version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "managed_turn_intents", "effect_id", "TEXT")
        _add_column_if_missing(connection, "wake_batches", "version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "wake_batches", "effect_id", "TEXT")
        _add_column_if_missing(connection, "mailbox_messages", "delivery_version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "mailbox_messages", "intake_version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "managed_actor_commands", "version", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "raw_messages", "effect_id", "TEXT")
        _add_column_if_missing(connection, "rpc_requests", "effect_id", "TEXT")
        _add_column_if_missing(connection, "mutation_intents", "superseded_by_effect_id", "TEXT")
        _add_column_if_missing(connection, "app_server_effects", "transport_seq", "INTEGER")
        _add_column_if_missing(connection, "app_server_effects", "predecessor_effect_id", "TEXT")
        connection.execute("DROP INDEX IF EXISTS mutation_intents_open_unique")
        connection.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS mutation_intents_open_unique
            ON mutation_intents(method, client_key)
            WHERE state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED_UNRECONCILED', 'INCIDENT')"""
        )
        _install_transition_guards(connection)
        if current < SCHEMA_VERSION:
            _migrate_legacy_mutation_intents(connection)
        if current < 9:
            _migrate_prepared_context_provenance(connection)
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_meta(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, applied_at),
            )
        missing = set(REQUIRED_TABLES) - {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if missing:
            raise RuntimeError(f"observer v12 schema is incomplete: {sorted(missing)}")
        if owns_transaction:
            connection.commit()
    except BaseException:
        if owns_transaction:
            connection.rollback()
        raise


def _install_transition_guards(connection: sqlite3.Connection) -> None:
    from .durability.graphs import transition_trigger_sql
    from .durability.transitions import AGGREGATE_LOCATORS

    for kind, locator in AGGREGATE_LOCATORS.items():
        drop_sql, create_sql = transition_trigger_sql(
            kind=kind,
            table=locator.table,
            id_column=locator.id_column,
            state_column=locator.state_column,
            version_column=locator.version_column,
        )
        connection.execute(drop_sql)
        connection.execute(create_sql)


def _migrate_legacy_mutation_intents(connection: sqlite3.Connection) -> None:
    tables = {
        str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if "mutation_intents" not in tables or "app_server_effects" not in tables:
        return
    now = datetime.now(timezone.utc).isoformat()
    owner_for = {
        "thread/start": "THREAD_PROVISION",
        "thread/resume": "THREAD_RESUME",
        "turn/start": "MANAGED_TURN",
        "thread/memoryMode/set": "THREAD_MEMORY",
    }
    state_for = {
        "APPLIED": "EFFECT_CONFIRMED",
        "OPERATOR_RESOLVED": "OPERATOR_RESOLVED",
        "INCIDENT": "INCIDENT",
        "SUBMITTED": "SUBMISSION_UNCERTAIN",
        "SUBMITTED_UNRECONCILED": "SUBMISSION_UNCERTAIN",
    }
    rows = connection.execute(
        """SELECT intent_id, method, binding_id, client_key, state, request_json
        FROM mutation_intents WHERE superseded_by_effect_id IS NULL"""
    ).fetchall()
    for row in rows:
        method = str(row["method"])
        client_key = str(row["client_key"])
        existing = connection.execute(
            "SELECT effect_id FROM app_server_effects WHERE method = ? AND client_key = ?",
            (method, client_key),
        ).fetchone()
        if existing is not None:
            connection.execute(
                "UPDATE mutation_intents SET superseded_by_effect_id = ? WHERE intent_id = ?",
                (str(existing[0]), str(row["intent_id"])),
            )
            continue
        effect_id = f"eff_legacy_{uuid.uuid4().hex}"
        owner_kind = owner_for.get(method, "EPHEMERAL_CANARY")
        legacy_state = str(row["state"])
        target_state = state_for.get(legacy_state, "SUBMISSION_UNCERTAIN")
        if legacy_state in {"SUBMITTED", "SUBMITTED_UNRECONCILED"}:
            evidence = connection.execute(
                """SELECT 1 FROM raw_messages
                WHERE canonical_json LIKE ? AND direction = 'stdout' LIMIT 1""",
                (f"%{client_key}%",),
            ).fetchone()
            if evidence is None:
                target_state = "SUBMISSION_UNCERTAIN"
            else:
                target_state = "RESPONSE_OBSERVED"
        request_json = str(row["request_json"] or "{}")
        try:
            json.loads(request_json)
        except Exception:
            request_json = "{}"
        connection.execute(
            """INSERT INTO app_server_effects(
                effect_id, owner_kind, owner_id, binding_id, method, client_key,
                request_json, state, version, legacy_intent_id, prepared_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (
                effect_id,
                owner_kind,
                str(row["intent_id"]),
                None if row["binding_id"] is None else str(row["binding_id"]),
                method,
                client_key,
                request_json,
                target_state,
                str(row["intent_id"]),
                now,
            ),
        )
        connection.execute(
            "UPDATE mutation_intents SET superseded_by_effect_id = ? WHERE intent_id = ?",
            (effect_id, str(row["intent_id"])),
        )


def _migrate_prepared_context_provenance(connection: sqlite3.Connection) -> None:
    """Migrate legacy bindings without manufacturing trusted currentness.

    A legacy ACTIVE binding is preserved only when the supervisor ledger
    independently carries the complete applied verification chain and a
    non-default verified state version.  No prepared tuple is backfilled.
    Every other nonterminal binding is quarantined and any still-PREPARED
    binding-owned effect is cancelled before write in this same transaction.
    """

    from .durability.models import AggregateKind, TransitionCause, TransitionRequest
    from .durability.transitions import TransitionKernel

    kernel = TransitionKernel(connection)
    binding_columns = _table_columns(connection, "managed_actor_bindings")
    rows = connection.execute(
        """SELECT * FROM managed_actor_bindings
        WHERE prepared_context_trusted = 0
          AND binding_state IN ('PREPARED','THREAD_CREATED','VERIFICATION_REQUIRED','ACTIVE')
        ORDER BY created_at, binding_id"""
    ).fetchall()
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        binding_id = str(row["binding_id"])
        verified = None
        if (
            str(row["binding_state"]) == "ACTIVE"
            and row["verification_turn_intent_id"] is not None
            and row["verification_turn_id"] is not None
            and row["verification_command_id"] is not None
            and row["verification_receipt_id"] is not None
            and row["prepared_state_version"] is not None
            and int(row["prepared_state_version"]) > 0
            and row["verified_state_version"] is not None
            and int(row["verified_state_version"]) > 0
        ):
            verified = connection.execute(
                """SELECT 1
                FROM managed_turn_intents i
                JOIN managed_actor_commands c
                  ON c.command_id = ? AND c.binding_id = i.binding_id
                 AND c.turn_id = i.app_server_turn_id
                 AND c.validation_state = 'APPLIED'
                JOIN managed_command_receipts r
                  ON r.receipt_id = ? AND r.command_id = c.command_id
                WHERE i.turn_intent_id = ? AND i.binding_id = ?
                  AND i.submission_state = 'COMPLETED'
                  AND i.app_server_turn_id = ?""",
                (
                    str(row["verification_command_id"]),
                    str(row["verification_receipt_id"]),
                    str(row["verification_turn_intent_id"]),
                    binding_id,
                    str(row["verification_turn_id"]),
                ),
            ).fetchone()
        if verified is not None:
            connection.execute(
                """UPDATE managed_actor_bindings
                SET prepared_context_trusted = 1 WHERE binding_id = ?""",
                (binding_id,),
            )
            connection.execute(
                """INSERT INTO managed_binding_events(
                    binding_id,event_kind,payload_json,created_at
                ) VALUES (?, 'MIGRATION_VERIFIED_PROVENANCE_PRESERVED', '{}', ?)""",
                (binding_id, now),
            )
            continue

        effects = connection.execute(
            """SELECT effect_id, version FROM app_server_effects
            WHERE binding_id = ? AND state = 'PREPARED'
              AND owner_kind IN ('THREAD_PROVISION','THREAD_RESUME','THREAD_MEMORY')""",
            (binding_id,),
        ).fetchall()
        for effect in effects:
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                    aggregate_id=str(effect["effect_id"]),
                    expected_state="PREPARED",
                    expected_version=int(effect["version"] or 0),
                    target_state="CANCELLED_BEFORE_WRITE",
                    cause_kind=TransitionCause.MIGRATION,
                    cause_ref="untrusted_prepared_context",
                    field_updates={"resolved_at": now},
                )
            )
        state = str(row["binding_state"])
        target = "SUSPENDED" if state in {"VERIFICATION_REQUIRED", "ACTIVE"} else "REVOKED"
        timestamp_field = "suspended_at" if target == "SUSPENDED" else "revoked_at"
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.MANAGED_BINDING,
                aggregate_id=binding_id,
                expected_state=state,
                expected_version=int(row["version"] or 0),
                target_state=target,
                cause_kind=TransitionCause.MIGRATION,
                cause_ref="untrusted_prepared_context",
                field_updates={timestamp_field: now}
                if timestamp_field in binding_columns
                else {},
            )
        )
        connection.execute(
            """INSERT INTO managed_binding_events(
                binding_id,event_kind,payload_json,created_at
            ) VALUES (?, 'MIGRATION_UNTRUSTED_CONTEXT_QUARANTINED', ?, ?)""",
            (binding_id, json.dumps({"from_state": state, "to_state": target}), now),
        )
