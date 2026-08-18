import json
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import ingest_recorded_command, record_completed_agent_item
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
    store.attach_thread_for_tests(binding_id, "thr_cmd")
    store.mark_verification_required(binding_id)
    return seeded, store, CommandGateway(store, seeded["bridge"])


def test_no_control_action_and_duplicate(tmp_path: Path) -> None:
    seeded, store, gateway = _ready_binding(tmp_path)
    first = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_1",
        text="no envelope",
        item_id="itm_turn_1",
    )
    assert first["validation_state"] == "APPLIED"
    raw_seq = seeded["supervisor"].connection.execute(
        "SELECT raw_message_seq FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()[0]
    second = gateway.ingest_final_item(raw_message_seq=int(raw_seq))
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
    applied = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_ack",
        text=text,
        item_id="itm_ack",
    )
    assert applied["validation_state"] == "APPLIED"
    with pytest.raises(CommandGatewayError):
        ingest_recorded_command(
            gateway,
            seeded["supervisor"],
            thread_id="thr_other",
            turn_id="turn_ack2",
            text="x",
            item_id="itm_other",
        )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_bad",
        text="x",
        item_id="itm_bad",
    )
    seeded["supervisor"].connection.execute(
        "UPDATE item_snapshots SET lifecycle = 'STARTED' WHERE item_id = 'itm_bad'"
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(CommandGatewayError):
        gateway.ingest_final_item(raw_message_seq=seq)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
