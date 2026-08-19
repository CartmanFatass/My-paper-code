from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.models import (
    AggregateKind,
    TransitionCause,
    TransitionRequest,
)
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.durability.transitions import TransitionError, TransitionKernel


def _open(tmp_path: Path):
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    initialize_database(connection)
    return connection


def _insert_wake(connection, wake_id: str = "wake1", state: str = "PREPARED") -> None:
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES (?,?,?,?,?,?,0)""",
        (wake_id, "bind1", "thr1", state, f"key-{wake_id}", "t"),
    )


def _insert_message(connection, message_id: str = "msg1", delivery: str = "BATCHED") -> None:
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            message_id,
            "OPERATOR",
            f"src-{message_id}",
            "act1",
            "OPERATOR_ATTENTION_REQUEST",
            "s",
            "p",
            1,
            delivery,
            "NOT_ACKNOWLEDGED",
            "t",
        ),
    )


def _resolution(connection, kind: str, aggregate_id: str) -> None:
    connection.execute(
        """INSERT INTO operator_resolutions(
            resolution_id,aggregate_kind,aggregate_id,operator,disposition,
            evidence_kind,evidence_ref,payload_json,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
        (f"res-{aggregate_id}", kind, aggregate_id, "op", "NO_SUBMISSION_EVIDENCE", "NONE", "ref", "{}", "t"),
    )


def test_correct_state_and_version_transition(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection)
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection):
        result = kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="PREPARED",
                expected_version=0,
                target_state="SUBMITTING",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref="effect1",
            )
        )
    assert result.from_state == "PREPARED"
    assert result.to_state == "SUBMITTING"
    assert result.from_version == 0
    assert result.to_version == 1
    row = connection.execute("SELECT state, version FROM wake_batches WHERE wake_batch_id='wake1'").fetchone()
    assert tuple(row) == ("SUBMITTING", 1)
    audit = connection.execute("SELECT from_state, to_state, to_version FROM control_transitions").fetchone()
    assert tuple(audit) == ("PREPARED", "SUBMITTING", 1)
    connection.close()


def test_stale_version_rejects(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection)
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="PREPARED",
                expected_version=0,
                target_state="SUBMITTING",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref="e1",
            )
        )
    with DurabilityTransaction(connection), pytest.raises(TransitionError, match="CAS failed"):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="SUBMITTING",
                expected_version=0,
                target_state="SUBMITTED",
                cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                cause_ref="e1",
            )
        )
    connection.close()


def test_wrong_state_rejects(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection, state="SUBMITTING")
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection), pytest.raises(TransitionError, match="CAS failed"):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="PREPARED",
                expected_version=0,
                target_state="SUBMITTING",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref="e1",
            )
        )
    connection.close()


def test_illegal_edge_rejects(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection)
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection), pytest.raises(TransitionError, match="illegal WAKE_BATCH"):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="PREPARED",
                expected_version=0,
                target_state="COMPLETED",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref="e1",
            )
        )
    connection.close()


def test_incident_automatic_exit_rejects(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection, state="INCIDENT")
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection), pytest.raises(TransitionError, match="operator-only"):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="INCIDENT",
                expected_version=0,
                target_state="CANCELLED",
                cause_kind=TransitionCause.RECONCILIATION,
                cause_ref="auto",
            )
        )
    connection.close()


def test_operator_only_edge_without_resolution_rejects(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection, state="INCIDENT")
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection), pytest.raises(TransitionError, match="operator_resolutions"):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="INCIDENT",
                expected_version=0,
                target_state="CANCELLED",
                cause_kind=TransitionCause.OPERATOR_RESOLUTION,
                cause_ref="res-missing",
            )
        )
    connection.close()


def test_multi_transition_rolls_back_on_exception(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection, state="INCIDENT")
    _insert_message(connection)
    connection.commit()
    kernel = TransitionKernel(connection)

    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        with DurabilityTransaction(connection):
            _resolution(connection, "WAKE_BATCH", "wake1")
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.WAKE_BATCH,
                    aggregate_id="wake1",
                    expected_state="INCIDENT",
                    expected_version=0,
                    target_state="CANCELLED",
                    cause_kind=TransitionCause.OPERATOR_RESOLUTION,
                    cause_ref="res-wake1",
                )
            )
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                    aggregate_id="msg1",
                    expected_state="BATCHED",
                    expected_version=0,
                    target_state="ELIGIBLE",
                    cause_kind=TransitionCause.OPERATOR_NO_SUBMISSION,
                    cause_ref="res-wake1",
                )
            )
            raise Boom("injected after first transitions")
    wake = connection.execute("SELECT state, version FROM wake_batches").fetchone()
    message = connection.execute("SELECT delivery_state, delivery_version FROM mailbox_messages").fetchone()
    assert tuple(wake) == ("INCIDENT", 0)
    assert tuple(message) == ("BATCHED", 0)
    assert connection.execute("SELECT COUNT(*) FROM operator_resolutions").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM control_transitions").fetchone()[0] == 0
    connection.close()


def test_multi_transition_commits_resolution_and_messages(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _insert_wake(connection, state="INCIDENT")
    _insert_message(connection)
    connection.commit()
    kernel = TransitionKernel(connection)
    with DurabilityTransaction(connection):
        _resolution(connection, "WAKE_BATCH", "wake1")
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id="wake1",
                expected_state="INCIDENT",
                expected_version=0,
                target_state="CANCELLED",
                cause_kind=TransitionCause.OPERATOR_RESOLUTION,
                cause_ref="res-wake1",
            )
        )
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                aggregate_id="msg1",
                expected_state="BATCHED",
                expected_version=0,
                target_state="ELIGIBLE",
                cause_kind=TransitionCause.OPERATOR_NO_SUBMISSION,
                cause_ref="res-wake1",
            )
        )
    wake = connection.execute("SELECT state, version FROM wake_batches").fetchone()
    message = connection.execute("SELECT delivery_state, delivery_version FROM mailbox_messages").fetchone()
    assert tuple(wake) == ("CANCELLED", 1)
    assert tuple(message) == ("ELIGIBLE", 1)
    assert connection.execute("SELECT COUNT(*) FROM operator_resolutions").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM control_transitions").fetchone()[0] == 2
    connection.close()
