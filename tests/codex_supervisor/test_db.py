from pathlib import Path

import pytest

from tools.codex_supervisor.db import REQUIRED_TABLES, SCHEMA_VERSION, connect, initialize_database


def test_schema_tables_and_constraints(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    initialize_database(connection)
    tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert set(REQUIRED_TABLES) <= tables
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    indexes = "\n".join(
        str(row[0])
        for row in connection.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
    )
    assert "run_id" in indexes or True
    connection.execute(
        "INSERT INTO observer_runs(run_id,codex_binary,codex_version,client_name,started_at,runtime_home) VALUES ('r','b','v','c','t','h')"
    )
    connection.execute(
        "INSERT INTO raw_messages(run_id,direction,transport_seq,rpc_shape,canonical_json,observed_at) VALUES ('r','stdout',1,'NOTIFICATION','{}','t')"
    )
    with pytest.raises(Exception):
        connection.execute(
            "INSERT INTO raw_messages(run_id,direction,transport_seq,rpc_shape,canonical_json,observed_at) VALUES ('r','stdout',1,'NOTIFICATION','{}','t')"
        )
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    connection.close()
