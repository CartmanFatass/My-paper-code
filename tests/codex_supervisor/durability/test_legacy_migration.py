from pathlib import Path

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectJournal


def test_legacy_rows_are_not_deleted(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO mutation_intents(
            intent_id,method,binding_id,client_key,state,request_json,created_at,updated_at
        ) VALUES ('mut1','turn/start','bind1','k1','APPLIED','{}','t','t')"""
    )
    connection.commit()
    initialize_database(connection)
    assert connection.execute("SELECT COUNT(*) FROM mutation_intents").fetchone()[0] == 1
    connection.close()


def test_legacy_applied_can_be_superseded_by_effect(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO mutation_intents(
            intent_id,method,binding_id,client_key,state,request_json,created_at,updated_at
        ) VALUES ('mut1','turn/start','bind1','k1','APPLIED','{}','t','t')"""
    )
    connection.commit()
    initialize_database(connection)
    row = connection.execute("SELECT superseded_by_effect_id FROM mutation_intents").fetchone()
    assert row[0]
    effect = connection.execute(
        "SELECT state, client_key FROM app_server_effects WHERE effect_id = ?",
        (row[0],),
    ).fetchone()
    assert str(effect[0]) == "EFFECT_CONFIRMED"
    assert str(effect[1]) == "k1"
    connection.close()
