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


def test_uncertain_wake_is_not_resent(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        config = make_observer_config(tmp_path)
        extra = {
            "FAKE_APP_SERVER_MODE": "mutation_overload",
            "FAKE_THREAD_STATUS": "idle",
            "FAKE_LOADED_THREADS": "thr_port",
        }
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
            source_event_key="op:uncertain",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="u",
            payload_ref="r",
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
        )
        with pytest.raises(WakeSchedulerError, match="provider-rejected"):
            await scheduler.once()
        open_batch = dict(seeded["supervisor"].connection.execute(
            "SELECT * FROM wake_batches WHERE binding_id = ? ORDER BY prepared_at DESC LIMIT 1",
            (seeded["portfolio_binding_id"],),
        ).fetchone())
        assert open_batch["state"] == "INCIDENT"
        with pytest.raises(WakeSchedulerError, match="requires client and lease"):
            await scheduler.submit_batch(str(open_batch["wake_batch_id"]), "no")
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM app_server_outbox WHERE method = 'turn/start'"
        ).fetchone()[0] == 1
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())
