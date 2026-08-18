import json
from pathlib import Path

import pytest

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.managed_models import HistoryTrust, ThreadOrigin


def _ready_binding(tmp_path: Path):
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
    store.attach_thread(binding_id, "thr_cmd")
    store.mark_verification_required(binding_id)
    return seeded, store, CommandGateway(store, seeded["bridge"])


def test_no_control_action_and_duplicate(tmp_path: Path) -> None:
    seeded, store, gateway = _ready_binding(tmp_path)
    first = gateway.ingest_final_item(
        thread_id="thr_cmd",
        turn_id="turn_1",
        raw_message_seq=9,
        item_type="agentMessage",
        lifecycle="COMPLETED",
        text="no envelope",
    )
    assert first["validation_state"] == "APPLIED"
    second = gateway.ingest_final_item(
        thread_id="thr_cmd",
        turn_id="turn_1",
        raw_message_seq=9,
        item_type="agentMessage",
        lifecycle="COMPLETED",
        text="no envelope",
    )
    assert second["validation_state"] == "DUPLICATE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_reanchor_and_stale_and_unbound_thread(tmp_path: Path) -> None:
    seeded, store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "state_version": int(checkpoint["state_version"]),
            "epoch_id": checkpoint.get("epoch_id"),
            "epoch_revision": checkpoint.get("epoch_revision"),
        },
        "payload": {},
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(payload) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    applied = gateway.ingest_final_item(
        thread_id="thr_cmd",
        turn_id="turn_ack",
        raw_message_seq=3,
        item_type="agentMessage",
        lifecycle="COMPLETED",
        text=text,
    )
    assert applied["validation_state"] == "APPLIED"
    with pytest.raises(CommandGatewayError):
        gateway.ingest_final_item(
            thread_id="thr_other",
            turn_id="turn_ack",
            raw_message_seq=4,
            item_type="agentMessage",
            lifecycle="COMPLETED",
            text="x",
        )
    with pytest.raises(CommandGatewayError):
        gateway.ingest_final_item(
            thread_id="thr_cmd",
            turn_id="turn_bad",
            raw_message_seq=5,
            item_type="agentMessage",
            lifecycle="STARTED",
            text="x",
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
