from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.mailbox_store import MailboxStore
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.wake_batches import WakeBatchError, WakeBatchStore, wake_client_user_message_id


def test_wake_batch_and_effect_share_client_key(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    journal = EffectJournal(store.connection)
    wake_id = "wake1"
    key = wake_client_user_message_id(wake_id)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id=wake_id,
        binding_id="bind1",
        method="turn/start",
        client_key=key,
        request={"threadId": "thr1"},
    )
    assert effect.client_key == key
    store.close()


def test_wake_claim_requires_explicit_lease(tmp_path: Path) -> None:
    from tests.codex_supervisor.helpers import claim_wake_write_start_for_tests

    store = ObserverStore(tmp_path)
    mailbox = MailboxStore(store)
    batches = WakeBatchStore(store, mailbox)
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1"},
    )
    store.connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,
            lease_holder,lease_generation,effect_id
        ) VALUES ('wake1','bind1','thr1','PREPARED','hmasd-wake:wake1','t','holder',3,?)""",
        (effect.effect_id,),
    )
    store.connection.commit()
    with pytest.raises(WakeBatchError):
        claim_wake_write_start_for_tests(batches, "wake1", lease_holder=None, lease_generation=None)
    claimed = claim_wake_write_start_for_tests(batches, "wake1", lease_holder="holder", lease_generation=3)
    assert claimed["state"] == "SUBMITTING"
    assert journal.get(effect.effect_id).state == "WRITE_STARTED"
    store.close()


def test_write_started_wake_is_never_automatically_requeued(tmp_path: Path) -> None:
    journal = EffectJournal(connect(tmp_path / "s.sqlite3") if False else ObserverStore(tmp_path).connection)
    store = ObserverStore(tmp_path)
    journal = EffectJournal(store.connection)
    initialize_database(store.connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={},
    )
    journal._claim_write(
        effect.effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="r1",
        raw_request_seq=1,
    )
    assert journal.has_possible_submission(effect.effect_id)
    with pytest.raises(Exception):
        journal._claim_write(
            effect.effect_id,
            run_id="run1",
            client_request_id="2",
            request_row_id="r2",
            raw_request_seq=2,
        )
    store.close()


def test_recovery_never_submits_an_existing_effect(tmp_path: Path) -> None:
    from tools.codex_supervisor.durability.reconciliation import EffectReconciler, ReconciliationError

    store = ObserverStore(tmp_path)
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={},
    )
    reconciler = EffectReconciler(store.connection)
    import asyncio

    with pytest.raises(ReconciliationError, match="PREPARED"):
        asyncio.run(reconciler.reconcile(effect.effect_id))
    store.close()
