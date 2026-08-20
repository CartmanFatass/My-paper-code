from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.operator_resolution import (
    OperatorResolutionError,
    OperatorResolutionService,
    ResolutionDisposition,
)


def _open(tmp_path: Path):
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT','hmasd-wake:wake1','t',1)"""
    )
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES ('msg1','OPERATOR','src1','act1','OPERATOR_ATTENTION_REQUEST','s','p',1,'BATCHED','NOT_ACKNOWLEDGED','t')"""
    )
    connection.execute(
        "INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1','msg1',0)"
    )
    connection.commit()
    return connection


def test_prepared_effect_can_return_messages_to_eligible(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1"},
    )
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id = 'wake1'", (effect.effect_id,))
    connection.commit()
    service = OperatorResolutionService(connection)
    service.resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.NO_SUBMISSION_EVIDENCE,
        evidence_kind="NONE",
        evidence_ref="none",
    )
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "CANCELLED"
    assert connection.execute("SELECT delivery_state FROM mailbox_messages").fetchone()[0] == "ELIGIBLE"
    assert connection.execute("SELECT state FROM app_server_effects").fetchone()[0] == "CANCELLED_BEFORE_WRITE"
    connection.close()


def test_write_started_effect_cannot_use_no_submission_resolution(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(
        effect.effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="r1",
        raw_request_seq=1,
    )
    journal.mark_incident(effect.effect_id, evidence_ref="sr1", incident={"reason": "server_request"})
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id = 'wake1'", (effect.effect_id,))
    connection.commit()
    service = OperatorResolutionService(connection)
    with pytest.raises(OperatorResolutionError, match="write_started"):
        service.resolve_wake(
            "wake1",
            operator="op",
            disposition=ResolutionDisposition.NO_SUBMISSION_EVIDENCE,
            evidence_kind="NONE",
            evidence_ref="none",
        )
    connection.close()


def test_operator_resolution_is_one_shot(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    service = OperatorResolutionService(connection)
    service.resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.ABANDON,
        evidence_kind="OPERATOR",
        evidence_ref="abandon",
    )
    with pytest.raises(OperatorResolutionError, match="already has an operator resolution"):
        service.resolve_wake(
            "wake1",
            operator="op",
            disposition=ResolutionDisposition.ABANDON,
            evidence_kind="OPERATOR",
            evidence_ref="abandon",
        )
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "ABANDONED"
    connection.close()


def test_abandoned_incident_cannot_be_reopened(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    service = OperatorResolutionService(connection)
    service.resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.ABANDON,
        evidence_kind="OPERATOR",
        evidence_ref="abandon",
    )
    with pytest.raises(Exception, match="illegal WAKE_BATCH"):
        connection.execute("UPDATE wake_batches SET state='ACTIVE', version = version + 1")
    connection.close()


def test_operator_resolution_is_atomic(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    service = OperatorResolutionService(connection)

    class Boom(Exception):
        pass

    original = service.kernel.apply

    def exploding(*args, **kwargs):
        result = original(*args, **kwargs)
        raise Boom("after first transition")

    service.kernel.apply = exploding  # type: ignore[method-assign]
    with pytest.raises(Boom):
        service.resolve_wake(
            "wake1",
            operator="op",
            disposition=ResolutionDisposition.ABANDON,
            evidence_kind="OPERATOR",
            evidence_ref="abandon",
        )
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "INCIDENT"
    assert connection.execute("SELECT delivery_state FROM mailbox_messages").fetchone()[0] == "BATCHED"
    assert connection.execute("SELECT COUNT(*) FROM operator_resolutions").fetchone()[0] == 0
    connection.close()
