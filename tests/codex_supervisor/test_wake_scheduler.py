from __future__ import annotations

import asyncio
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


def test_idle_binding_gets_one_exactly_once_wake(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path), config, tmp_path, tmp_path / "err.log",
            extra_env={
                "FAKE_APP_SERVER_MODE": "handshake_ok",
                "FAKE_THREAD_STATUS": "idle",
                "FAKE_LOADED_THREADS": "thr_port",
            },
            stdin_close_timeout=0.4, terminate_timeout=0.4,
        )
        await transport.start()
        client = AppServerClient(transport, config)
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
            seeded["bindings"], mailbox, batches, SchedulerLeases(seeded["supervisor"]),
            WakeRecovery(seeded["bindings"], mailbox, batches, client),
            SemanticScanner(mailbox, seeded["bridge"]), seeded["bridge"], client,
            instance_id="sched-1",
        )
        scheduled = (await scheduler.once())["scheduled"]
        assert scheduled is not None and scheduled["state"] == "ACTIVE"
        assert scheduled["app_server_turn_id"] == "turn_canary"
        operation_id = str(scheduled["effect_id"])
        operation = seeded["supervisor"].connection.execute(
            "SELECT state, outcome, method FROM app_server_outbox WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        assert tuple(operation) == ("DONE", "OK", "turn/start")
        messages = mailbox.list_messages(
            target_actor_context_id=seeded["portfolio"].actor_context_id
        )
        assert messages[0].delivery_state.value == "DELIVERED_TO_TURN"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_wake_context_drift_is_rejected_before_outbox_ready(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:drift",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="wake",
        payload_ref="ref",
    )
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    leases = SchedulerLeases(seeded["supervisor"])
    lease = leases.acquire(binding_id, "sched-drift")
    batch = batches.prepare(
        binding_id=binding_id,
        thread_id="thr_port",
        snapshot=seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id),
        messages=[message],
        lease_generation=int(lease["generation"]),
        lease_holder="sched-drift",
    )
    seeded["supervisor"].connection.execute(
        "UPDATE managed_context_injections SET state_version = state_version + 1 WHERE turn_intent_id = ?",
        (batch["wake_batch_id"],),
    )
    seeded["supervisor"].connection.commit()
    scheduler = WakeScheduler(
        seeded["bindings"], mailbox, batches, leases,
        WakeRecovery(seeded["bindings"], mailbox, batches, None),
        SemanticScanner(mailbox, seeded["bridge"]), seeded["bridge"], None,
        instance_id="sched-drift",
    )
    with pytest.raises(WakeSchedulerError, match="context changed"):
        scheduler._validate_once(binding_id, str(batch["wake_batch_id"]), int(lease["generation"]))
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM app_server_outbox"
    ).fetchone()[0] == 0
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
