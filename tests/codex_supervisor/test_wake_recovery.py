import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem, WakeBatchState
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery


def test_prepared_batch_returns_to_eligible_and_delivered_is_preserved(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        mailbox = seeded["mailbox"]
        prepared = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:prep",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="p",
            payload_ref="r",
        )
        delivered = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:del",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="d",
            payload_ref="r2",
        )
        snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        prepared_batch = batches.prepare(
            binding_id=seeded["portfolio_binding_id"],
            thread_id="thr_port",
            snapshot=snapshot,
            messages=[prepared],
        )
        mailbox.mark_eligible(delivered.message_id)
        mailbox.mark_batched(delivered.message_id)
        mailbox.mark_delivered(delivered.message_id)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        recovery = WakeRecovery(seeded["bindings"], mailbox, batches, client)
        await recovery.recover()
        assert batches.get(str(prepared_batch["wake_batch_id"]))["state"] == WakeBatchState.CANCELLED.value
        assert mailbox.get(prepared.message_id).delivery_state.value == "ELIGIBLE"
        assert mailbox.get(delivered.message_id).delivery_state.value == "DELIVERED_TO_TURN"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())
