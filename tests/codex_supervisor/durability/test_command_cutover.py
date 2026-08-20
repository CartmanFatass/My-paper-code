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
    connection.close()
