from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectError, EffectJournal
from tools.codex_supervisor.durability.models import EffectState


def _journal(tmp_path: Path) -> EffectJournal:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    return EffectJournal(connection)


def _prepare(journal: EffectJournal, key: str = "key1") -> str:
    record = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="turn1",
        binding_id="bind1",
        method="turn/start",
        client_key=key,
        request={"threadId": "thr1", "input": []},
    )
    return record.effect_id


def test_prepare_is_idempotent_by_method_and_client_key(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    first = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="turn1",
        binding_id="bind1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    second = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="turn1",
        binding_id="bind1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    assert first.effect_id == second.effect_id
    assert first.state == EffectState.PREPARED.value
    with pytest.raises(EffectError, match="conflict"):
        journal.prepare_effect(
            owner_kind="WAKE_BATCH",
            owner_id="wake1",
            binding_id="bind1",
            method="turn/start",
            client_key="k1",
            request={"threadId": "thr1"},
        )


def test_only_prepared_can_claim_write(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal)
    claimed = journal.claim_write(
        effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="rpc1",
        raw_request_seq=1,
    )
    assert claimed.state == EffectState.WRITE_STARTED.value
    assert claimed.version == 1
    with pytest.raises(EffectError, match="only PREPARED"):
        journal.claim_write(
            effect_id,
            run_id="run1",
            client_request_id="2",
            request_row_id="rpc2",
            raw_request_seq=2,
        )


def test_write_started_cannot_be_prepared_again(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal, "k2")
    journal.claim_write(
        effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="rpc1",
        raw_request_seq=1,
    )
    with pytest.raises(EffectError, match="cannot prepare again"):
        journal.prepare_effect(
            owner_kind="MANAGED_TURN",
            owner_id="turn1",
            binding_id="bind1",
            method="turn/start",
            client_key="k2",
            request={"threadId": "thr1", "input": []},
        )


def test_timeout_after_write_started_becomes_uncertain(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal)
    journal.claim_write(
        effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="rpc1",
        raw_request_seq=1,
    )
    record = journal.mark_uncertain(effect_id, reason="timeout")
    assert record.state == EffectState.SUBMISSION_UNCERTAIN.value
    assert journal.has_possible_submission(effect_id)


def test_response_becomes_response_observed(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal)
    journal.claim_write(
        effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="rpc1",
        raw_request_seq=1,
    )
    record = journal.observe_response(
        effect_id,
        response={"result": {"turn": {"id": "turnx"}}},
        turn_id="turnx",
        thread_id="thr1",
    )
    assert record.state == EffectState.RESPONSE_OBSERVED.value
    assert record.turn_id == "turnx"


def test_confirmation_requires_evidence_ref(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal)
    journal.claim_write(
        effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="rpc1",
        raw_request_seq=1,
    )
    journal.observe_response(effect_id, response={"ok": True}, turn_id="turnx")
    with pytest.raises(EffectError, match="evidence_ref"):
        journal.confirm_effect(effect_id, evidence_ref="")
    record = journal.confirm_effect(effect_id, evidence_ref="turn:turnx")
    assert record.state == EffectState.EFFECT_CONFIRMED.value


def test_incident_is_terminal(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal)
    journal.claim_write(
        effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="rpc1",
        raw_request_seq=1,
    )
    record = journal.mark_incident(
        effect_id,
        evidence_ref="server_request:sr1",
        incident={"reason": "server_request", "server_request_row_id": "sr1"},
    )
    assert record.state == EffectState.INCIDENT.value
    with pytest.raises(EffectError):
        journal.observe_response(effect_id, response={"ok": True})
    with pytest.raises(EffectError):
        journal.mark_uncertain(effect_id, reason="retry")
    assert journal.has_possible_submission(effect_id)


def test_prepared_without_raw_seq_is_not_possible_submission(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    effect_id = _prepare(journal)
    assert journal.has_possible_submission(effect_id) is False
    cancelled = journal.cancel_before_write(effect_id, cause_ref="pre-write")
    assert cancelled.state == EffectState.CANCELLED_BEFORE_WRITE.value
