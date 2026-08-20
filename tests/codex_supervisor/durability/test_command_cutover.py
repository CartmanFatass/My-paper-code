from pathlib import Path

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.models import AggregateKind, TransitionCause, TransitionRequest
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.durability.transitions import TransitionKernel


def test_command_state_is_versioned(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO managed_actor_commands(
            command_id,binding_id,thread_id,turn_id,raw_message_seq,command_kind,
            payload_json,validation_state,created_at
        ) VALUES ('cmd1','bind1','thr1','turn1',1,'NO_CONTROL_ACTION','{}','RECEIVED','t')"""
    )
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.MANAGED_COMMAND,
                aggregate_id="cmd1",
                expected_state="RECEIVED",
                expected_version=0,
                target_state="VALIDATED",
                cause_kind=TransitionCause.CONTROL_COMMAND,
                cause_ref="validate",
            )
        )
    assert connection.execute("SELECT version, validation_state FROM managed_actor_commands").fetchone()[0] == 1
    count = connection.execute(
        "SELECT COUNT(*) FROM control_transitions WHERE aggregate_id = 'cmd1'"
    ).fetchone()[0]
    assert int(count) == 1
    connection.close()


def test_command_gateway_writes_transition_journal(tmp_path: Path) -> None:
    from tools.codex_supervisor.command_gateway import CommandGateway
    from tools.codex_supervisor.managed_models import CommandValidationState

    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO managed_actor_commands(
            command_id,binding_id,thread_id,turn_id,raw_message_seq,command_kind,
            payload_json,validation_state,created_at
        ) VALUES ('cmd1','bind1','thr1','turn1',1,'NO_CONTROL_ACTION','{}','RECEIVED','t')"""
    )
    connection.commit()

    class _Bindings:
        def __init__(self, store_connection):
            self.store = type("S", (), {"connection": store_connection, "_lock": __import__("threading").Lock()})()

    gateway = CommandGateway(_Bindings(connection), None)  # type: ignore[arg-type]
    gateway._update_command("cmd1", validation_state=CommandValidationState.VALIDATED.value, validated_at="t")
    version, state = connection.execute(
        "SELECT version, validation_state FROM managed_actor_commands"
    ).fetchone()
    assert int(version) == 1
    assert str(state) == "VALIDATED"
    journal = connection.execute(
        "SELECT COUNT(*) FROM control_transitions WHERE aggregate_kind = 'MANAGED_COMMAND' AND to_version = 1"
    ).fetchone()[0]
    assert int(journal) == 1
    connection.close()
