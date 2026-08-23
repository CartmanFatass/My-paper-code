import json
import sqlite3
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import (
    claim_wake_write_start_for_tests,
    record_completed_agent_item,
)
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.mailbox_models import (
    IntakeState,
    MailboxMessageKind,
    MailboxSourceSystem,
)
from tools.codex_supervisor.wake_batches import WakeBatchStore


def _envelope(action: str, payload: dict, snapshot) -> str:
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": action,
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": payload,
    }
    return (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(body)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )


def _seed_delivered_batch(tmp_path: Path):
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    messages = [
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key=f"atomic:{index}",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref=f"subject-{index}",
            payload_ref=f"payload-{index}",
            priority=4,
        )
        for index in range(2)
    ]
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=messages,
    )
    for message in messages:
        mailbox.mark_delivered(message.message_id)
    wake_id = str(batch["wake_batch_id"])
    claimed = claim_wake_write_start_for_tests(
        batches,
        wake_id,
        lease_holder=batch["lease_holder"],
        lease_generation=batch["lease_generation"],
    )
    EffectJournal(seeded["supervisor"].connection).confirm_effect(
        str(claimed["effect_id"]),
        evidence_ref="turn:turn_atomic_batch",
    )
    batches.set_state(
        wake_id,
        state="SUBMITTED",
        expected_state="SUBMITTING",
        app_server_turn_id="turn_atomic_batch",
    )
    batches.set_state(wake_id, state="ACTIVE", expected_state="SUBMITTED")
    batches.set_state(wake_id, state="COMPLETED", expected_state="ACTIVE")
    return seeded, messages, snapshot


def _record_command(
    seeded,
    *,
    action: str,
    payload: dict,
    snapshot,
    item_id: str,
    turn_id: str = "turn_atomic_batch",
) -> int:
    return record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id=turn_id,
        text=_envelope(action, payload, snapshot),
        item_id=item_id,
    )


def _close(seeded) -> None:
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def _command_payload(action: str, message_ids: list[str]) -> dict:
    if action == "MAILBOX_ACK":
        return {"message_ids": message_ids}
    return {
        "items": [
            {"message_id": message_id, "intake_kind": "READ_AND_ROUTED"}
            for message_id in message_ids
        ]
    }


def _complete_wake(seeded, batches, batch: dict, *, turn_id: str) -> None:
    wake_id = str(batch["wake_batch_id"])
    claimed = claim_wake_write_start_for_tests(
        batches,
        wake_id,
        lease_holder=batch["lease_holder"],
        lease_generation=batch["lease_generation"],
    )
    EffectJournal(seeded["supervisor"].connection).confirm_effect(
        str(claimed["effect_id"]),
        evidence_ref=f"turn:{turn_id}",
    )
    batches.set_state(
        wake_id,
        state="SUBMITTED",
        expected_state="SUBMITTING",
        app_server_turn_id=turn_id,
    )
    batches.set_state(wake_id, state="ACTIVE", expected_state="SUBMITTED")
    batches.set_state(wake_id, state="COMPLETED", expected_state="ACTIVE")


def _insert_delivery_history(
    seeded,
    *,
    suffix: str,
    binding_id: str,
    thread_id: str,
    turn_id: str,
    message_id: str,
    state: str = "COMPLETED",
) -> None:
    connection = seeded["supervisor"].connection
    with connection:
        connection.execute(
            """INSERT INTO wake_batches (
                wake_batch_id, binding_id, thread_id, state,
                client_user_message_id, app_server_turn_id, prepared_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"wake_history_{suffix}",
                binding_id,
                thread_id,
                state,
                f"hmasd-wake:wake_history_{suffix}",
                turn_id,
                f"2026-08-23T12:00:00+00:00-{suffix}",
            ),
        )
        connection.execute(
            """INSERT INTO wake_batch_messages (wake_batch_id, message_id, ordinal)
            VALUES (?, ?, 0)""",
            (f"wake_history_{suffix}", message_id),
        )


def _assert_action_applied(mailbox, message_id: str, action: str) -> None:
    expected = (
        IntakeState.ACKNOWLEDGED
        if action == "MAILBOX_ACK"
        else IntakeState.INTAKEN
    )
    assert mailbox.get(message_id).intake_state is expected


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_cancelled_attempt_is_ignored_for_successful_replacement_delivery(
    tmp_path: Path,
    action: str,
) -> None:
    from tools.codex_supervisor.durability.effects import cancel_prepared_wake

    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=f"replacement:{action}",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="replacement-subject",
        payload_ref="replacement-payload",
        priority=4,
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    cancelled = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
    )
    cancel_prepared_wake(
        seeded["supervisor"].connection,
        str(cancelled["wake_batch_id"]),
        cause_ref="test-requeue-before-write",
    )
    replacement = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[mailbox.get(message.message_id)],
    )
    mailbox.mark_delivered(message.message_id)
    _complete_wake(seeded, batches, replacement, turn_id="turn_replacement_delivery")
    seq = _record_command(
        seeded,
        action=action,
        payload=_command_payload(action, [message.message_id]),
        snapshot=snapshot,
        item_id=f"item_replacement_{action}",
        turn_id="turn_replacement_delivery",
    )

    applied = CommandGateway(
        seeded["bindings"], seeded["bridge"], mailbox
    ).ingest_final_item(raw_message_seq=seq)

    assert applied["validation_state"] == "APPLIED"
    _assert_action_applied(mailbox, message.message_id, action)
    assert seeded["supervisor"].connection.execute(
        "SELECT state FROM wake_batches WHERE wake_batch_id = ?",
        (cancelled["wake_batch_id"],),
    ).fetchone()[0] == "CANCELLED"
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_contradictory_relevant_delivery_turns_fail_without_mailbox_effects(
    tmp_path: Path,
    action: str,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    message_id = messages[0].message_id
    _insert_delivery_history(
        seeded,
        suffix=f"contradictory_{action}",
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        turn_id="turn_contradictory_delivery",
        message_id=message_id,
        state="ACTIVE",
    )
    seq = _record_command(
        seeded,
        action=action,
        payload=_command_payload(action, [message_id]),
        snapshot=snapshot,
        item_id=f"item_contradictory_{action}",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)

    with pytest.raises(CommandGatewayError, match="wake history is ambiguous"):
        gateway.ingest_final_item(raw_message_seq=seq)

    assert mailbox.get(message_id).intake_state is IntakeState.NOT_ACKNOWLEDGED
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 0
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM control_transitions WHERE aggregate_kind = 'MAILBOX_INTAKE'"
    ).fetchone()[0] == 0
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_single_relevant_delivery_remains_compatible(
    tmp_path: Path,
    action: str,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    message_id = messages[0].message_id
    seq = _record_command(
        seeded,
        action=action,
        payload=_command_payload(action, [message_id]),
        snapshot=snapshot,
        item_id=f"item_single_delivery_{action}",
    )

    applied = CommandGateway(
        seeded["bindings"], seeded["bridge"], mailbox
    ).ingest_final_item(raw_message_seq=seq)

    assert applied["validation_state"] == "APPLIED"
    _assert_action_applied(mailbox, message_id, action)
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_other_binding_delivery_history_does_not_change_exact_binding_selection(
    tmp_path: Path,
    action: str,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    message_id = messages[0].message_id
    _insert_delivery_history(
        seeded,
        suffix=f"other_binding_{action}",
        binding_id=seeded["root_binding_id"],
        thread_id="thr_root",
        turn_id="turn_other_binding_delivery",
        message_id=message_id,
    )
    seq = _record_command(
        seeded,
        action=action,
        payload=_command_payload(action, [message_id]),
        snapshot=snapshot,
        item_id=f"item_binding_isolation_{action}",
    )

    applied = CommandGateway(
        seeded["bindings"], seeded["bridge"], mailbox
    ).ingest_final_item(raw_message_seq=seq)

    assert applied["validation_state"] == "APPLIED"
    _assert_action_applied(mailbox, message_id, action)
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_direct_delivery_without_wake_history_remains_compatible(
    tmp_path: Path,
    action: str,
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=f"direct:{action}",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="direct-subject",
        payload_ref="direct-payload",
        priority=4,
    )
    mailbox.mark_eligible(message.message_id)
    mailbox.mark_batched(message.message_id)
    mailbox.mark_delivered(message.message_id)
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    seq = _record_command(
        seeded,
        action=action,
        payload=_command_payload(action, [message.message_id]),
        snapshot=snapshot,
        item_id=f"item_direct_{action}",
        turn_id="turn_direct_delivery",
    )

    applied = CommandGateway(
        seeded["bindings"], seeded["bridge"], mailbox
    ).ingest_final_item(raw_message_seq=seq)

    assert applied["validation_state"] == "APPLIED"
    _assert_action_applied(mailbox, message.message_id, action)
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_valid_first_invalid_later_rolls_back_complete_batch(
    tmp_path: Path,
    action: str,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    if action == "MAILBOX_ACK":
        payload = {"message_ids": [messages[0].message_id, "msg_missing"]}
        error = "unknown mailbox message"
    else:
        payload = {
            "items": [
                {"message_id": messages[0].message_id, "intake_kind": "READ"},
                {"message_id": messages[1].message_id, "intake_kind": ""},
            ]
        }
        error = "intake_kind"
    seq = _record_command(
        seeded,
        action=action,
        payload=payload,
        snapshot=snapshot,
        item_id=f"item_invalid_later_{action}",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
    managed_receipts_before = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_command_receipts"
    ).fetchone()[0]

    with pytest.raises(CommandGatewayError, match=error):
        gateway.ingest_final_item(raw_message_seq=seq)

    assert [mailbox.get(message.message_id).intake_state for message in messages] == [
        IntakeState.NOT_ACKNOWLEDGED,
        IntakeState.NOT_ACKNOWLEDGED,
    ]
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 0
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM control_transitions WHERE aggregate_kind = 'MAILBOX_INTAKE'"
    ).fetchone()[0] == 0
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_command_receipts"
    ).fetchone()[0] == managed_receipts_before
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_all_valid_batch_commits_atomically_and_exact_replay_is_idempotent(
    tmp_path: Path,
    action: str,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    if action == "MAILBOX_ACK":
        payload = {"message_ids": [message.message_id for message in messages]}
        expected_state = IntakeState.ACKNOWLEDGED
        expected_transitions = 2
    else:
        payload = {
            "items": [
                {"message_id": message.message_id, "intake_kind": "READ_AND_ROUTED"}
                for message in messages
            ]
        }
        expected_state = IntakeState.INTAKEN
        expected_transitions = 4
    seq = _record_command(
        seeded,
        action=action,
        payload=payload,
        snapshot=snapshot,
        item_id=f"item_all_valid_{action}",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
    managed_receipts_before = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_command_receipts"
    ).fetchone()[0]

    applied = gateway.ingest_final_item(raw_message_seq=seq)
    replayed = gateway.ingest_final_item(raw_message_seq=seq)

    assert applied["validation_state"] == "APPLIED"
    assert replayed["validation_state"] == "DUPLICATE"
    assert [mailbox.get(message.message_id).intake_state for message in messages] == [
        expected_state,
        expected_state,
    ]
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 2
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM control_transitions WHERE aggregate_kind = 'MAILBOX_INTAKE'"
    ).fetchone()[0] == expected_transitions
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_command_receipts"
    ).fetchone()[0] == managed_receipts_before + 1
    _close(seeded)


@pytest.mark.parametrize("action", ["MAILBOX_ACK", "MAILBOX_INTAKE"])
def test_duplicate_message_in_batch_is_rejected_without_effect(
    tmp_path: Path,
    action: str,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    message_id = messages[0].message_id
    if action == "MAILBOX_ACK":
        payload = {"message_ids": [message_id, message_id]}
    else:
        payload = {
            "items": [
                {"message_id": message_id, "intake_kind": "READ"},
                {"message_id": message_id, "intake_kind": "READ_AND_ROUTED"},
            ]
        }
    seq = _record_command(
        seeded,
        action=action,
        payload=payload,
        snapshot=snapshot,
        item_id=f"item_duplicate_{action}",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)

    with pytest.raises(CommandGatewayError, match="duplicate message_ids"):
        gateway.ingest_final_item(raw_message_seq=seq)

    assert mailbox.get(message_id).intake_state is IntakeState.NOT_ACKNOWLEDGED
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 0
    _close(seeded)


def test_failure_after_first_staged_transition_and_receipt_rolls_back_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    original = mailbox._record_command_receipt_in_transaction
    calls = {"count": 0}

    def fail_after_first_receipt(**kwargs):
        receipt = original(**kwargs)
        calls["count"] += 1
        if calls["count"] == 1:
            raise CommandGatewayError("injected mailbox batch failure")
        return receipt

    monkeypatch.setattr(
        mailbox,
        "_record_command_receipt_in_transaction",
        fail_after_first_receipt,
    )
    seq = _record_command(
        seeded,
        action="MAILBOX_ACK",
        payload={"message_ids": [message.message_id for message in messages]},
        snapshot=snapshot,
        item_id="item_injected_failure",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)

    with pytest.raises(CommandGatewayError, match="injected mailbox batch failure"):
        gateway.ingest_final_item(raw_message_seq=seq)

    assert [mailbox.get(message.message_id).intake_state for message in messages] == [
        IntakeState.NOT_ACKNOWLEDGED,
        IntakeState.NOT_ACKNOWLEDGED,
    ]
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 0
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM control_transitions WHERE aggregate_kind = 'MAILBOX_INTAKE'"
    ).fetchone()[0] == 0
    _close(seeded)


def test_independent_observer_never_sees_committed_partial_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded, messages, snapshot = _seed_delivered_batch(tmp_path)
    mailbox = seeded["mailbox"]
    original = mailbox._record_command_receipt_in_transaction
    observed: list[tuple[list[str], int]] = []

    def observe_after_first_staged_receipt(**kwargs):
        receipt = original(**kwargs)
        if not observed:
            observer = sqlite3.connect(
                f"file:{seeded['supervisor'].path}?mode=ro",
                uri=True,
            )
            try:
                placeholders = ", ".join("?" for _ in messages)
                states = [
                    str(row[0])
                    for row in observer.execute(
                        f"SELECT intake_state FROM mailbox_messages WHERE message_id IN ({placeholders}) ORDER BY message_id",
                        [message.message_id for message in messages],
                    ).fetchall()
                ]
                receipt_count = int(
                    observer.execute(
                        "SELECT COUNT(*) FROM mailbox_command_receipts"
                    ).fetchone()[0]
                )
                observed.append((states, receipt_count))
            finally:
                observer.close()
        return receipt

    monkeypatch.setattr(
        mailbox,
        "_record_command_receipt_in_transaction",
        observe_after_first_staged_receipt,
    )
    seq = _record_command(
        seeded,
        action="MAILBOX_ACK",
        payload={"message_ids": [message.message_id for message in messages]},
        snapshot=snapshot,
        item_id="item_concurrent_observer",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)

    applied = gateway.ingest_final_item(raw_message_seq=seq)

    assert applied["validation_state"] == "APPLIED"
    assert observed == [(["NOT_ACKNOWLEDGED", "NOT_ACKNOWLEDGED"], 0)]
    assert [mailbox.get(message.message_id).intake_state for message in messages] == [
        IntakeState.ACKNOWLEDGED,
        IntakeState.ACKNOWLEDGED,
    ]
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 2
    _close(seeded)
