from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.mailbox_models import (
    MailboxMessageKind,
    MailboxSourceSystem,
    WakeIncidentDisposition,
)
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, ThreadOrigin
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns, client_user_message_id
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.session_guard import ManagedAppServerSession, mark_related_incidents
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchError, WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeIncidentError, WakeRecovery


def _close(seeded) -> None:
    for session in list(ManagedAppServerSession._by_client.values()):
        session.close()
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def _prepared_wake(tmp_path: Path, *, lease_holder: str | None, lease_generation: int | None):
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=f"op:finalx4:{lease_holder}:{lease_generation}",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=lease_generation,
        lease_holder=lease_holder,
    )
    return seeded, mailbox, batches, str(batch["wake_batch_id"]), message


def test_null_lease_claim_cannot_bypass_nonnull_batch_lease(tmp_path: Path) -> None:
    seeded, _mailbox, batches, wake_batch_id, _message = _prepared_wake(
        tmp_path,
        lease_holder="current",
        lease_generation=2,
    )
    with pytest.raises(WakeBatchError, match="PREPARED"):
        batches.claim_first_submission(
            wake_batch_id,
            lease_holder=None,
            lease_generation=None,
        )
    row = batches.get(wake_batch_id)
    assert row is not None
    assert row["state"] == "PREPARED"
    attempts = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id = ?",
        (wake_batch_id,),
    ).fetchone()[0]
    assert int(attempts) == 0
    _close(seeded)


def test_unleased_batch_accepts_only_null_lease_claim(tmp_path: Path) -> None:
    seeded, _mailbox, batches, wake_batch_id, _message = _prepared_wake(
        tmp_path,
        lease_holder=None,
        lease_generation=None,
    )
    with pytest.raises(WakeBatchError, match="PREPARED"):
        batches.claim_first_submission(
            wake_batch_id,
            lease_holder="sched",
            lease_generation=1,
        )
    row = batches.get(wake_batch_id)
    assert row is not None
    assert row["state"] == "PREPARED"
    claimed = batches.claim_first_submission(
        wake_batch_id,
        lease_holder=None,
        lease_generation=None,
    )
    assert claimed["state"] == "SUBMITTING"
    _close(seeded)


def test_pre_response_wake_incident_does_not_strand_batched_messages(tmp_path: Path) -> None:
    seeded, mailbox, batches, wake_batch_id, message = _prepared_wake(
        tmp_path,
        lease_holder="sched",
        lease_generation=1,
    )
    batches.claim_first_submission(
        wake_batch_id,
        lease_holder="sched",
        lease_generation=1,
    )
    mark_related_incidents(
        seeded["supervisor"],
        {
            "id": "sreq_pre",
            "method": "item/command/request",
            "params": {"threadId": "thr_port"},
        },
    )
    batch = batches.get(wake_batch_id)
    assert batch is not None
    assert batch["state"] == "INCIDENT"
    assert batches.open_batch_for_binding(seeded["portfolio_binding_id"]) is None
    stored = mailbox.get(message.message_id)
    assert stored is not None
    assert stored.delivery_state.value == "BATCHED"
    selected = mailbox.select_eligible(
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        target_kind="PORTFOLIO",
        target_binding_state="ACTIVE",
        sender_kind_for={},
    )
    assert message.message_id not in {item.message_id for item in selected}
    recovery = WakeRecovery(seeded["bindings"], mailbox, batches)
    resolved = recovery.resolve_incident(
        wake_batch_id,
        operator="operator",
        disposition=WakeIncidentDisposition.NO_SUBMISSION_EVIDENCE,
    )
    assert resolved["state"] == "CANCELLED"
    restored = mailbox.get(message.message_id)
    assert restored is not None
    assert restored.delivery_state.value == "ELIGIBLE"
    _close(seeded)


def test_operator_can_resolve_unsubmitted_wake_incident_to_eligible(tmp_path: Path) -> None:
    seeded, mailbox, batches, wake_batch_id, message = _prepared_wake(
        tmp_path,
        lease_holder="sched",
        lease_generation=1,
    )
    batches.set_state(wake_batch_id, state="INCIDENT", incident_json='{"reason":"server_request"}')
    recovery = WakeRecovery(seeded["bindings"], mailbox, batches)
    updated = recovery.resolve_incident(
        wake_batch_id,
        operator="operator",
        disposition="NO_SUBMISSION_EVIDENCE",
    )
    assert updated["state"] == "CANCELLED"
    stored = mailbox.get(message.message_id)
    assert stored is not None
    assert stored.delivery_state.value == "ELIGIBLE"
    selected = mailbox.select_eligible(
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        target_kind="PORTFOLIO",
        target_binding_state="ACTIVE",
        sender_kind_for={},
    )
    assert message.message_id in {item.message_id for item in selected}
    _close(seeded)


def test_operator_cannot_requeue_incident_with_possible_submission(tmp_path: Path) -> None:
    seeded, mailbox, batches, wake_batch_id, message = _prepared_wake(
        tmp_path,
        lease_holder="sched",
        lease_generation=1,
    )
    batches.set_state(
        wake_batch_id,
        state="INCIDENT",
        app_server_turn_id="turn_seen",
        submitted_at="t",
        incident_json='{"reason":"server_request"}',
    )
    mailbox.mark_delivered(message.message_id)
    recovery = WakeRecovery(seeded["bindings"], mailbox, batches)
    with pytest.raises(WakeIncidentError, match="possible submission"):
        recovery.resolve_incident(
            wake_batch_id,
            operator="operator",
            disposition=WakeIncidentDisposition.NO_SUBMISSION_EVIDENCE,
        )
    batch = batches.get(wake_batch_id)
    assert batch is not None
    assert batch["state"] == "INCIDENT"
    stored = mailbox.get(message.message_id)
    assert stored is not None
    assert stored.delivery_state.value == "DELIVERED_TO_TURN"
    _close(seeded)


def test_canary_does_not_start_turn_after_thread_start_server_request_and_response(
    tmp_path: Path,
) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path)
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=ObserverStore(tmp_path / "runtime"),
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "server_request_then_thread_start_response"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        result = await service.run_ephemeral_canary(timeout_seconds=5)
        assert result.outcome == "incident"
        assert result.incident == "server_request"
        methods = [
            row[0]
            for row in service.store.connection.execute(
                "SELECT method FROM raw_messages WHERE direction='stdin'"
            )
        ]
        assert methods.count("thread/start") == 1
        assert methods.count("turn/start") == 0
        service.store.close()

    asyncio.run(body())


def test_overload_marks_matching_mutation_uncertain(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = store.prepare_binding(
            snapshot,
            repo_root=str(tmp_path),
            thread_cwd=str(tmp_path),
            created_by_operator="operator",
            thread_origin=ThreadOrigin.NEW,
            history_trust=HistoryTrust.FRESH,
        )
        store.attach_thread_for_tests(binding_id, "thr_canary")
        store.mark_verification_required(binding_id)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "mutation_overload"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="bootstrap",
        )
        with pytest.raises(ManagedTurnError, match="uncertain"):
            await turns.submit(intent_id, "hello")
        row = turns._row(intent_id)
        assert row["submission_state"] == "SUBMISSION_UNCERTAIN"
        mutation = seeded["supervisor"].connection.execute(
            """SELECT state FROM mutation_intents
            WHERE method = 'turn/start' AND client_key = ?""",
            (client_user_message_id(intent_id),),
        ).fetchone()
        assert mutation is not None
        assert str(mutation[0]) == "SUBMISSION_UNCERTAIN"
        await transport.stop()
        _close(seeded)

    asyncio.run(body())
