from pathlib import Path
import threading

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.models import AggregateKind, TransitionCause, TransitionRequest
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.durability.transitions import TransitionError, TransitionKernel


def test_two_transition_cas_callers_have_one_winner(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at
        ) VALUES ('wake1','bind1','thr1','PREPARED','k1','t')"""
    )
    connection.commit()
    connection.close()
    results: list[str] = []
    barrier = threading.Barrier(2)
    lock = threading.Lock()

    def worker() -> None:
        local = connect(path)
        initialize_database(local)
        kernel = TransitionKernel(local)
        barrier.wait()
        try:
            with DurabilityTransaction(local):
                kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.WAKE_BATCH,
                        aggregate_id="wake1",
                        expected_state="PREPARED",
                        expected_version=0,
                        target_state="SUBMITTING",
                        cause_kind=TransitionCause.APP_SERVER_EFFECT,
                        cause_ref="race",
                    )
                )
            with lock:
                results.append("win")
        except TransitionError:
            with lock:
                results.append("lose")
        local.close()

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    second.start()
    first.join()
    second.join()
    assert results.count("win") == 1
    assert results.count("lose") == 1
