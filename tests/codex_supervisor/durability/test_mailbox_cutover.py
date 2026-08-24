from pathlib import Path
import hashlib
import json

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectJournal
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
    store.connection.execute(
        """INSERT INTO managed_actor_bindings(
            binding_id,actor_context_id,actor_kind,semantic_scope_key,thread_id,
            thread_origin,history_trust,binding_state,memory_policy_state,
            repo_root,thread_cwd,created_by_operator,created_at
        ) VALUES ('bind1','act1','ROOT','root','thr1','NEW','FRESH','ACTIVE',
                  'OPERATOR_CONFIRMED_GLOBAL_DISABLED','r','r','op','t')"""
    )
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
    effect = EffectJournal(store.connection).prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
            request={
                "threadId": "thr1",
                "input": [{"type": "text", "text": "wake"}],
                "approvalPolicy": "never",
                "clientUserMessageId": "hmasd-wake:wake1",
            },
    )
    store.connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,effect_id
        ) VALUES ('wake1','bind1','thr1','PREPARED','hmasd-wake:wake1','t',?)""",
        (effect.effect_id,),
    )
    store.connection.execute(
        "INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1', ?, 0)",
        (first.message_id,),
    )
    store.connection.execute(
        "INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1', ?, 1)",
        (second.message_id,),
    )
    input_bytes = b"wake"
    store.connection.execute(
        """INSERT INTO managed_context_injections(
            injection_id,turn_intent_id,binding_id,canonical_refs_json,
            open_obligation_ids_json,mailbox_message_ids_json,input_byte_length,
            input_bytes,input_sha256,created_at
        ) VALUES ('inj-wake1','wake1','bind1','[]','[]',?,?,?,?, 't')""",
        (
            json.dumps([first.message_id, second.message_id]),
            len(input_bytes),
            input_bytes,
            hashlib.sha256(input_bytes).hexdigest(),
        ),
    )
    store.connection.execute(
        "UPDATE wake_batches SET context_injection_id='inj-wake1' WHERE wake_batch_id='wake1'"
    )
    EffectJournal(store.connection).seal_effect(effect.effect_id)
    store.connection.commit()
    assert mailbox.cancel_prepared_batch_source_resolved("wake1", {first.message_id}) is True
    assert mailbox.get(first.message_id).delivery_state is DeliveryState.CANCELLED_SOURCE_RESOLVED
    assert mailbox.get(second.message_id).delivery_state is DeliveryState.ELIGIBLE
    assert store.connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "CANCELLED"
    assert EffectJournal(store.connection).get(effect.effect_id).state == "CANCELLED_BEFORE_WRITE"
    store.close()
