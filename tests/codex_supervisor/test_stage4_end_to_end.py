import asyncio
import json
from pathlib import Path

from tests.codex_supervisor.helpers import ingest_recorded_command, make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.command_gateway import CommandGateway
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.managed_packet_send import ManagedPacketSender
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler


def test_root_and_portfolio_independent_wake(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        (tmp_path / "typed.md").write_text("canary", encoding="utf-8")
        config = make_observer_config(tmp_path)
        extra = {"FAKE_APP_SERVER_MODE": "handshake_ok", "FAKE_THREAD_STATUS": "idle", "FAKE_LOADED_THREADS": "thr_root,thr_port"}
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
        sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
        sender.send(
            source_binding_id=seeded["root_binding_id"],
            packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
            target_alias="PORTFOLIO",
            payload_ref="typed.md",
            marker="ROOT_TO_PORTFOLIO_REVIEW:e2e",
        )
        mailbox = seeded["mailbox"]
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
        first = await scheduler.once()
        assert first["scheduled"]["binding_id"] == seeded["portfolio_binding_id"]
        gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox, sender)
        delivered = [item for item in mailbox.list_messages() if item.delivery_state.value == "DELIVERED_TO_TURN"]
        ack = {
            "schema_version": "1.0",
            "packet_kind": "MANAGED_ACTOR_COMMAND",
            "action_kind": "MAILBOX_ACK",
            "expected": {
                "checkpoint_id": (ack_snapshot := seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)).checkpoint_id,
                "state_version": ack_snapshot.state_version,
                "epoch_id": ack_snapshot.epoch_id,
                "epoch_revision": ack_snapshot.epoch_revision,
            },
            "payload": {"message_ids": [delivered[0].message_id]},
        }
        ingest_recorded_command(
            gateway,
            seeded["supervisor"],
            thread_id="thr_port",
            turn_id=str(first["scheduled"]["app_server_turn_id"]),
            text="<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(ack) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>",
            item_id="itm_e2e_ack",
        )
        scheduler.observe_completion(str(first["scheduled"]["wake_batch_id"]), "completed")
        second = await scheduler.once()
        assert second["scheduled"] is None or second["scheduled"].get("binding_id") != first["scheduled"]["binding_id"]
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())
