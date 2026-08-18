import json
from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.wake_batches import WakeBatchStore


def _envelope(action: str, payload: dict) -> str:
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": action,
        "payload": payload,
    }
    return "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(body) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"


def test_ack_intake_and_cross_binding_reject(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:cmd",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
        priority=4,
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
    )
    mailbox.mark_delivered(message.message_id)
    batches.set_state(str(batch["wake_batch_id"]), state="COMPLETED")
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
    applied = gateway.ingest_final_item(
        thread_id="thr_port",
        turn_id="turn_ack",
        raw_message_seq=1,
        item_type="agentMessage",
        lifecycle="COMPLETED",
        text=_envelope("MAILBOX_ACK", {"message_ids": [message.message_id]}),
    )
    assert applied["validation_state"] == "APPLIED"
    assert mailbox.get(message.message_id).intake_state.value == "ACKNOWLEDGED"
    intake = gateway.ingest_final_item(
        thread_id="thr_port",
        turn_id="turn_in",
        raw_message_seq=2,
        item_type="agentMessage",
        lifecycle="COMPLETED",
        text=_envelope(
            "MAILBOX_INTAKE",
            {"items": [{"message_id": message.message_id, "intake_kind": "READ_AND_ROUTED", "result_ref": "ref"}]},
        ),
    )
    assert intake["validation_state"] == "APPLIED"
    with pytest.raises(CommandGatewayError, match="not owned"):
        gateway.ingest_final_item(
            thread_id="thr_root",
            turn_id="turn_x",
            raw_message_seq=3,
            item_type="agentMessage",
            lifecycle="COMPLETED",
            text=_envelope("MAILBOX_ACK", {"message_ids": [message.message_id]}),
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
