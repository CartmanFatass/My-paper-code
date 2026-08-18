from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.mailbox_models import DeliveryState, IntakeState, MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.mailbox_store import MailboxStoreError


def test_enqueue_idempotent_and_transitions(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    first = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:attn:1",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subj",
        payload_ref="ref",
        priority=3,
    )
    second = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:attn:1",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="other",
        payload_ref="other",
    )
    assert first.message_id == second.message_id
    eligible = mailbox.mark_eligible(first.message_id)
    assert eligible.delivery_state is DeliveryState.ELIGIBLE
    batched = mailbox.mark_batched(first.message_id)
    assert batched.delivery_state is DeliveryState.BATCHED
    with pytest.raises(MailboxStoreError, match="delivered or uncertain"):
        mailbox.acknowledge(first.message_id)
    delivered = mailbox.mark_delivered(first.message_id)
    assert delivered.delivery_state is DeliveryState.DELIVERED_TO_TURN
    acked = mailbox.acknowledge(first.message_id)
    assert acked.intake_state is IntakeState.ACKNOWLEDGED
    intaken = mailbox.intake(first.message_id)
    assert intaken.intake_state is IntakeState.INTAKEN
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_dead_letter_and_select_eligible(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:attn:2",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subj",
        payload_ref="ref",
        priority=9,
    )
    selected = mailbox.select_eligible(
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        target_kind="PORTFOLIO",
        target_binding_state="ACTIVE",
        sender_kind_for={},
    )
    assert selected[0].message_id == message.message_id
    assert selected[0].delivery_state is DeliveryState.ELIGIBLE
    mailbox.dead_letter(message.message_id, "revoked target")
    assert mailbox.get(message.message_id).delivery_state is DeliveryState.DEAD_LETTER
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
