from pathlib import Path

import pytest

from tools.codex_supervisor.db import REQUIRED_TABLES, SCHEMA_VERSION, connect, initialize_database
from tools.codex_supervisor.managed_models import BindingState, ManagedActorKind
from tools.codex_supervisor.store import ObserverStore


V1_ONLY_STATEMENTS = (
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
)


def _seed_v1(path: Path) -> None:
    connection = connect(path)
    with connection:
        for statement in V1_ONLY_STATEMENTS:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_meta(version, applied_at) VALUES (1, 't')")
        connection.execute(
            "INSERT INTO observer_runs(run_id,codex_binary,codex_version,client_name,started_at,runtime_home) VALUES ('run1','b','v','c','t','h')"
        )
        connection.execute(
            "INSERT INTO thread_snapshots(thread_id,first_observed_at,updated_at) VALUES ('thr_old','t','t')"
        )
        connection.execute(
            "INSERT INTO turn_snapshots(turn_id,thread_id,status,updated_at) VALUES ('turn_old','thr_old','inProgress','t')"
        )
        connection.execute(
            "INSERT INTO item_snapshots(item_id,lifecycle,safe_metadata_json,updated_at) VALUES ('itm_old','STARTED','{}','t')"
        )
    connection.close()


def test_v1_migrates_additively(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    _seed_v1(path)
    connection = connect(path)
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(REQUIRED_TABLES) <= tables
    assert connection.execute("SELECT run_id FROM observer_runs").fetchone()[0] == "run1"
    assert connection.execute("SELECT thread_id FROM thread_snapshots").fetchone()[0] == "thr_old"
    assert connection.execute("SELECT turn_id FROM turn_snapshots").fetchone()[0] == "turn_old"
    assert connection.execute("SELECT item_id FROM item_snapshots").fetchone()[0] == "itm_old"
    assert connection.execute("SELECT COUNT(*) FROM managed_actor_bindings").fetchone()[0] == 0
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    connection.close()


def test_newer_schema_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    with connection:
        connection.execute("CREATE TABLE schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        connection.execute("INSERT INTO schema_meta(version, applied_at) VALUES (99, 't')")
    with pytest.raises(RuntimeError, match="newer than supported"):
        initialize_database(connection)
    connection.close()


def test_fresh_store_is_schema_2(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    version = store.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0]
    assert version == SCHEMA_VERSION == 8
    assert ManagedActorKind.OPERATIONAL_ROOT.value == "OPERATIONAL_ROOT"
    assert BindingState.PREPARED.value == "PREPARED"
    store.close()


def test_v5_to_v6_rebuilds_mutation_open_unique_predicate(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    with connection:
        connection.execute(
            "CREATE TABLE schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        connection.execute("INSERT INTO schema_meta(version, applied_at) VALUES (5, 't')")
        connection.execute(
            """CREATE TABLE mutation_intents (
                intent_id TEXT PRIMARY KEY,
                method TEXT NOT NULL,
                binding_id TEXT,
                client_key TEXT NOT NULL,
                state TEXT NOT NULL,
                request_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE UNIQUE INDEX mutation_intents_open_unique
            ON mutation_intents(method, client_key)
            WHERE state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN')"""
        )
    old_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND name='mutation_intents_open_unique'"
    ).fetchone()[0]
    assert "SUBMITTED_UNRECONCILED" not in old_sql
    assert "INCIDENT" not in old_sql
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    rebuilt = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND name='mutation_intents_open_unique'"
    ).fetchone()[0]
    assert "SUBMITTED_UNRECONCILED" in rebuilt
    assert "INCIDENT" in rebuilt
    connection.close()
