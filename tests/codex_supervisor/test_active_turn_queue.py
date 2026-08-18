import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem, ThreadWakeReadiness
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery


def test_active_turn_is_queued_not_steered(tmp_path: Path, monkeypatch) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        monkeypatch.setenv("FAKE_APP_SERVER_MODE", "handshake_ok")
        monkeypatch.setenv("FAKE_THREAD_STATUS", "active")
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok", "FAKE_THREAD_STATUS": "active"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        recovery = WakeRecovery(
            seeded["bindings"],
            seeded["mailbox"],
            WakeBatchStore(seeded["supervisor"], seeded["mailbox"]),
            client,
        )
        readiness = await recovery.classify(seeded["root_binding_id"])
        assert readiness is ThreadWakeReadiness.ACTIVE_TURN
        seeded["mailbox"].enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:active",
            target_actor_context_id=seeded["root"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="wait",
            payload_ref="ref",
        )
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())
