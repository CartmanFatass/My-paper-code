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
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="bind1",
        method="turn/start",
        client_key="legacy-k1",
        request={},
    )
    connection.execute(
        """INSERT INTO mutation_intents(
            intent_id,method,binding_id,client_key,state,request_json,created_at,updated_at,superseded_by_effect_id
        ) VALUES ('mut1','turn/start','bind1','k1','APPLIED','{}','t','t',?)""",
        (effect.effect_id,),
    )
    connection.commit()
    row = connection.execute("SELECT superseded_by_effect_id FROM mutation_intents").fetchone()
    assert row[0] == effect.effect_id
    connection.close()
