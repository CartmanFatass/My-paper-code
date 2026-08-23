import asyncio
import sqlite3
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError


def test_idle_binding_gets_one_wake(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        config = make_observer_config(tmp_path)
        extra = {"FAKE_APP_SERVER_MODE": "handshake_ok", "FAKE_THREAD_STATUS": "idle", "FAKE_LOADED_THREADS": "thr_port"}
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env=extra,
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        mailbox = seeded["mailbox"]
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:wake",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="wake",
            payload_ref="ref",
            priority=8,
        )
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        scheduler = WakeScheduler(
            seeded["bindings"],
            mailbox,
            batches,
            SchedulerLeases(seeded["supervisor"]),
            WakeRecovery(seeded["bindings"], mailbox, batches, client),
            SemanticScanner(mailbox, seeded["bridge"]),
            seeded["bridge"],
            client,
            instance_id="sched-1",
        )
        result = await scheduler.once()
        scheduled = result["scheduled"]
        assert scheduled is not None
        assert scheduled["state"] == "ACTIVE"
        assert scheduled["app_server_turn_id"] == "turn_canary"
        messages = mailbox.list_messages(target_actor_context_id=seeded["portfolio"].actor_context_id)
        assert messages[0].delivery_state.value == "DELIVERED_TO_TURN"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def _assert_semantic_writer_blocked(path: Path) -> None:
    writer = sqlite3.connect(path, timeout=0.0, isolation_level=None)
    try:
        writer.execute("PRAGMA busy_timeout = 0")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            writer.execute("BEGIN IMMEDIATE")
    finally:
        writer.close()


@pytest.mark.parametrize(
    "drift",
    ["missing", "checkpoint_id", "state_version", "epoch_id", "epoch_revision"],
)
def test_wake_context_binding_missing_or_drift_cancels_and_requeues(
    tmp_path: Path, drift: str
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    actor_id = seeded["portfolio"].actor_context_id
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=f"op:{drift}",
        target_actor_context_id=actor_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="wake",
        payload_ref="ref",
        priority=8,
    )
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    leases = SchedulerLeases(seeded["supervisor"])
    lease = leases.acquire(binding_id, "sched-fence")
    snapshot = seeded["bridge"].snapshot(actor_id)
    batch = batches.prepare(
        binding_id=binding_id,
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=int(lease["generation"]),
        lease_holder="sched-fence",
    )
    batch_id = str(batch["wake_batch_id"])
    connection = seeded["supervisor"].connection
    if drift == "missing":
        connection.execute(
            "DELETE FROM managed_context_injections WHERE turn_intent_id = ?", (batch_id,)
        )
    else:
        value = snapshot.state_version + 1 if drift == "state_version" else 1 if drift == "epoch_revision" else f"stale-{drift}"
        connection.execute(
            f"UPDATE managed_context_injections SET {drift} = ? WHERE turn_intent_id = ?",
            (value, batch_id),
        )
    connection.commit()
    scheduler = WakeScheduler(
        seeded["bindings"], mailbox, batches, leases,
        WakeRecovery(seeded["bindings"], mailbox, batches, client=None),  # type: ignore[arg-type]
        SemanticScanner(mailbox, seeded["bridge"]), seeded["bridge"],
        client=None, instance_id="sched-fence",
    )
    with pytest.raises(WakeSchedulerError, match="context binding|currentness"):
        scheduler._assert_submit_fence(
            binding_id, int(lease["generation"]), wake_batch_id=batch_id
        )
    assert batches.get(batch_id)["state"] == "CANCELLED"
    assert mailbox.get(message.message_id).delivery_state.value == "ELIGIBLE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_wake_guard_spans_write_started_and_ends_before_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        binding_id = str(seeded["portfolio_binding_id"])
        actor_id = seeded["portfolio"].actor_context_id
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:guard",
            target_actor_context_id=actor_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="wake",
            payload_ref="ref",
            priority=8,
        )
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        leases = SchedulerLeases(seeded["supervisor"])
        lease = leases.acquire(binding_id, "sched-guard")
        batch = batches.prepare(
            binding_id=binding_id,
            thread_id="thr_port",
            snapshot=seeded["bridge"].snapshot(actor_id),
            messages=[message],
            lease_generation=int(lease["generation"]),
            lease_holder="sched-guard",
        )
        seeded["supervisor"].start_run(
            codex_binary="fixture", codex_version="v", client_name="guard", process_id=None
        )
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err-wake-guard.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        observed = {"before": False, "after": False, "released_at_send": False}
        original_write_start = seeded["supervisor"].record_effect_write_start

        def checked_write_start(**kwargs):
            _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
            observed["before"] = True
            result = original_write_start(**kwargs)
            _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
            observed["after"] = True
            return result

        monkeypatch.setattr(
            seeded["supervisor"], "record_effect_write_start", checked_write_start
        )
        original_send = client.send_prepared

        async def checked_send(prepared):
            writer = sqlite3.connect(
                seeded["bridge"].semantic_state_path,
                timeout=0.0,
                isolation_level=None,
            )
            try:
                writer.execute("BEGIN IMMEDIATE")
                writer.rollback()
                observed["released_at_send"] = True
            finally:
                writer.close()
            await original_send(prepared)

        client.send_prepared = checked_send  # type: ignore[method-assign]
        scheduler = WakeScheduler(
            seeded["bindings"],
            mailbox,
            batches,
            leases,
            WakeRecovery(seeded["bindings"], mailbox, batches, client),
            SemanticScanner(mailbox, seeded["bridge"]),
            seeded["bridge"],
            client,
            instance_id="sched-guard",
        )
        await scheduler.submit_batch(
            str(batch["wake_batch_id"]),
            str(batch["input_text"]),
            lease_generation=int(lease["generation"]),
        )
        assert observed == {"before": True, "after": True, "released_at_send": True}
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_wake_drift_immediately_before_guard_writes_no_effect_and_requeues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        from tools.codex_supervisor.durability.effects import EffectJournal
        from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner

        seeded = seed_active_root_portfolio(tmp_path)
        binding_id = str(seeded["portfolio_binding_id"])
        actor_id = seeded["portfolio"].actor_context_id
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:drift-at-guard",
            target_actor_context_id=actor_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="wake",
            payload_ref="ref",
            priority=8,
        )
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        leases = SchedulerLeases(seeded["supervisor"])
        lease = leases.acquire(binding_id, "sched-drift")
        batch = batches.prepare(
            binding_id=binding_id,
            thread_id="thr_port",
            snapshot=seeded["bridge"].snapshot(actor_id),
            messages=[message],
            lease_generation=int(lease["generation"]),
            lease_holder="sched-drift",
        )
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err-wake-drift.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, seeded["supervisor"])
        original_submit = owner.submit_effect

        async def drift_then_submit(*args, **kwargs):
            with seeded["semantic"]._lock, seeded["semantic"].connection:
                seeded["semantic"].connection.execute(
                    "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                    (actor_id,),
                )
            return await original_submit(*args, **kwargs)

        monkeypatch.setattr(owner, "submit_effect", drift_then_submit)
        scheduler = WakeScheduler(
            seeded["bindings"],
            mailbox,
            batches,
            leases,
            WakeRecovery(seeded["bindings"], mailbox, batches, client),
            SemanticScanner(mailbox, seeded["bridge"]),
            seeded["bridge"],
            client,
            instance_id="sched-drift",
        )
        with pytest.raises(WakeSchedulerError, match="currentness"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "CANCELLED"
        assert mailbox.get(message.message_id).delivery_state.value == "ELIGIBLE"
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "CANCELLED_BEFORE_WRITE"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?",
            (batch["effect_id"],),
        ).fetchone()[0] == 0
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())
