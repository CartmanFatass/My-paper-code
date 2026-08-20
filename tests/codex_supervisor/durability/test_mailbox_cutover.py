from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.mailbox_models import DeliveryState, IntakeState, MailboxMessageKind
from tools.codex_supervisor.mailbox_store import MailboxStore, MailboxStoreError
from tools.codex_supervisor.store import ObserverStore


def test_mailbox_delivery_transition_requires_version(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    mailbox = MailboxStore(store)
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k1",
        target_actor_context_id="act1",
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
        priority=1,
    )
    mailbox.mark_eligible(message.message_id)
    version = store.connection.execute(
        "SELECT delivery_version FROM mailbox_messages WHERE message_id = ?",
        (message.message_id,),
    ).fetchone()[0]
    assert version == 1
    store.close()


def test_mailbox_intake_cannot_skip_ack(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    mailbox = MailboxStore(store)
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k2",
        target_actor_context_id="act1",
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
        priority=1,
    )
    with pytest.raises(MailboxStoreError):
        mailbox._set_intake(message.message_id, IntakeState.INTAKEN)
    store.close()


def test_prepared_batch_cancel_is_atomic(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    mailbox = MailboxStore(store)
    first = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k3",
        target_actor_context_id="act1",
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
        priority=1,
    )
    second = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k4",
        target_actor_context_id="act1",
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
        priority=1,
    )
    mailbox.mark_eligible(first.message_id)
    mailbox.mark_eligible(second.message_id)
    mailbox.mark_batched(first.message_id)
    mailbox.mark_batched(second.message_id)
    store.connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at
        ) VALUES ('wake1','bind1','thr1','PREPARED','hmasd-wake:wake1','t')"""
    )
    store.connection.execute(
        "INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1', ?, 0)",
        (first.message_id,),
    )
    store.connection.execute(
        "INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1', ?, 1)",
        (second.message_id,),
    )
    store.connection.commit()
    assert mailbox.cancel_prepared_batch_source_resolved("wake1", {first.message_id}) is True
    assert mailbox.get(first.message_id).delivery_state is DeliveryState.CANCELLED_SOURCE_RESOLVED
    assert mailbox.get(second.message_id).delivery_state is DeliveryState.ELIGIBLE
    assert store.connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "CANCELLED"
    store.close()
