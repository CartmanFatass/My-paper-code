from datetime import datetime, timezone
from pathlib import Path

import sqlite3

from tools.codex_semantic_mvp.db import (
    SCHEMA_STATEMENTS,
    SCHEMA_V2_TABLES,
    SCHEMA_VERSION,
    V2_COLUMNS,
    initialize_database,
)
from tools.codex_semantic_mvp.store import SemanticStore


def _v2_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    for statement in SCHEMA_V2_TABLES:
        connection.execute(statement)
    for table, columns in V2_COLUMNS.items():
        existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        for name, decl in columns:
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    connection.execute("DROP INDEX IF EXISTS one_active_workflow_per_session")
    connection.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS one_active_workflow_per_actor
        ON workflows(actor_context_id) WHERE state = 'ACTIVE'"""
    )
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        "INSERT INTO schema_meta(version, applied_at) VALUES (2, ?)",
        (now,),
    )
    return connection


def _seed_v2(connection: sqlite3.Connection) -> None:
    now = datetime.now(timezone.utc).isoformat()
    actors = (
        ("actor_port", "s-port", "PORTFOLIO"),
        ("actor_root", "s-root", "OPERATIONAL_ROOT"),
        ("actor_em", "s-root", "EM"),
        ("actor_cm", "s-root", "CM"),
    )
    for actor_id, session_id, kind in actors:
        connection.execute(
            """INSERT INTO actor_contexts (
                actor_context_id, session_id, actor_kind, scope_key, identity_source,
                state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'TEST', 'ACTIVE', ?, ?)""",
            (actor_id, session_id, kind, f"scope:{actor_id}", now, now),
        )
        connection.execute(
            """INSERT INTO workflows (
                workflow_id, session_id, opened_turn_id, scope, objective, state,
                state_version, actor_context_id, created_at, updated_at
            ) VALUES (?, ?, 't0', 'scope', 'obj', 'ACTIVE', 1, ?, ?, ?)""",
            (f"wf-{actor_id}", session_id, actor_id, now, now),
        )
        connection.execute(
            """INSERT INTO plan_epochs (
                epoch_id, actor_context_id, epoch_kind, revision, objective,
                authority_refs_json, frozen_invariants_json, exit_boundary, state,
                created_at, updated_at
            ) VALUES (?, ?, 'DIRECTION_STAGE', 1, 'obj', '[]', '[]', 'exit', 'OPEN', ?, ?)""",
            (f"epoch-{actor_id}", actor_id, now, now),
        )
        connection.execute(
            """INSERT INTO semantic_commits (
                semantic_commit_id, actor_context_id, epoch_id, commit_kind,
                payload_json, source_refs_json, created_at
            ) VALUES (?, ?, ?, 'EM_DIRECTION_FRONTIER', '{}', '[]', ?)""",
            (f"sc-{actor_id}", actor_id, f"epoch-{actor_id}", now),
        )
        connection.execute(
            """INSERT INTO context_checkpoints (
                checkpoint_id, actor_context_id, epoch_id, epoch_revision,
                state_version, semantic_commit_id, capsule_kind, capsule_json, created_at
            ) VALUES (?, ?, ?, 1, 1, ?, 'TEST', '{}', ?)""",
            (f"cp-{actor_id}", actor_id, f"epoch-{actor_id}", f"sc-{actor_id}", now),
        )
    connection.execute(
        """INSERT INTO packet_refs (
            packet_id, packet_kind, source_actor_context_id, target_actor_context_id,
            marker, payload_ref, delivery_state, intake_state, created_at, updated_at
        ) VALUES ('pkt-1', 'EM_TO_CM', 'actor_em', 'actor_cm', 'm1', 'ref',
                  'PREPARED', 'NOT_INTAKEN', ?, ?)""",
        (now, now),
    )
    connection.execute(
        """INSERT INTO obligations (
            obligation_id, workflow_id, kind, owner, subject, reason, source_ref,
            state, owner_actor_context_id, created_at
        ) VALUES ('obl-keep', 'wf-actor_em', 'REPORT_INTAKE_REQUIRED', 'em', 'rep',
                  'keep', 'rep', 'OPEN', 'actor_em', ?)""",
        (now,),
    )


def test_v2_fixture_migrates_without_losing_rows(tmp_path: Path) -> None:
    path = tmp_path / "legacy-v2.sqlite3"
    connection = _v2_connection(path)
    _seed_v2(connection)
    connection.commit()
    actors_before = connection.execute("SELECT COUNT(*) FROM actor_contexts").fetchone()[0]
    connection.close()

    store = SemanticStore(path).initialize()
    assert SCHEMA_VERSION == 3
    assert store.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 3
    assert store.connection.execute("SELECT COUNT(*) FROM actor_contexts").fetchone()[0] == actors_before
    assert store.connection.execute("SELECT COUNT(*) FROM obligations").fetchone()[0] == 1
    tables = {
        row[0]
        for row in store.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {
        "promotion_proposals",
        "epoch_rollovers",
        "context_retention_marks",
        "context_gc_runs",
    } <= tables
    epoch = store.connection.execute(
        "SELECT navigation_refs_json, procedure_refs_json FROM plan_epochs LIMIT 1"
    ).fetchone()
    assert epoch[0] == "[]"
    assert epoch[1] == "[]"
    assert store.connection.execute("SELECT COUNT(*) FROM promotion_proposals").fetchone()[0] == 0
    store.close()


def test_interrupted_v3_migration_completes(tmp_path: Path) -> None:
    path = tmp_path / "partial.sqlite3"
    connection = _v2_connection(path)
    _seed_v2(connection)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS promotion_proposals (
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
        )"""
    )
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """INSERT INTO promotion_proposals (
            promotion_id, actor_context_id, epoch_id, promotion_kind, summary,
            rationale, source_refs_json, owner_actor_context_id, state, created_at, updated_at
        ) VALUES ('promo-keep', 'actor_em', 'epoch-actor_em', 'EPHEMERAL', 'note',
                  'keep', '[]', 'actor_em', 'PROPOSED', ?, ?)""",
        (now, now),
    )
    connection.commit()
    connection.close()

    store = SemanticStore(path).initialize()
    assert store.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 3
    assert (
        store.connection.execute(
            "SELECT COUNT(*) FROM promotion_proposals WHERE promotion_id = 'promo-keep'"
        ).fetchone()[0]
        == 1
    )
    store.close()


def test_initialize_database_is_idempotent_at_v3(tmp_path: Path) -> None:
    path = tmp_path / "fresh.sqlite3"
    first = SemanticStore(path).initialize()
    initialize_database(first.connection)
    assert first.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 3
    first.close()
