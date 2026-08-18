import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler


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
