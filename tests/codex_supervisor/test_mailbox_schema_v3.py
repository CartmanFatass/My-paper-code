from pathlib import Path

from tools.codex_supervisor.db import REQUIRED_TABLES, SCHEMA_VERSION, connect, initialize_database
from tools.codex_supervisor.mailbox_models import DeliveryState, MailboxMessageKind
from tools.codex_supervisor.store import ObserverStore


V2_TABLES = (
    "CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)",
    """CREATE TABLE IF NOT EXISTS managed_actor_bindings (
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
        created_at TEXT NOT NULL
    )""",
)


def test_v2_migrates_additively_to_v3(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    with connection:
        for statement in V2_TABLES:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_meta(version, applied_at) VALUES (2, 't')")
        connection.execute(
            """INSERT INTO managed_actor_bindings (
                binding_id, actor_context_id, actor_kind, semantic_scope_key,
                thread_origin, history_trust, binding_state, memory_policy_state,
                repo_root, thread_cwd, created_by_operator, created_at
            ) VALUES ('bind1','act1','OPERATIONAL_ROOT','scope','NEW','FRESH','PREPARED','UNVERIFIED','r','c','op','t')"""
        )
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 3
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(REQUIRED_TABLES) <= tables
    assert connection.execute("SELECT binding_id FROM managed_actor_bindings").fetchone()[0] == "bind1"
    assert connection.execute("SELECT COUNT(*) FROM mailbox_messages").fetchone()[0] == 0
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    connection.close()


def test_fresh_store_is_schema_3(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    assert store.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 3
    assert MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW.value == "ROOT_TO_PORTFOLIO_REVIEW"
    assert DeliveryState.ENQUEUED.value == "ENQUEUED"
    store.close()
