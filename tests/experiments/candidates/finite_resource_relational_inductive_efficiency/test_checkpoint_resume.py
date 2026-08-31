import json

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.checkpoint import CheckpointMismatch, restore_checkpoint, serialize_checkpoint, write_checkpoint_atomic
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import canonical_json_bytes


def _work(arm, *, flops=10):
    return {
        "arm_id": arm, "update": 12, "environment_slots": 64,
        "learned_decisions": 64, "backward_calls": 12, "adam_steps": 12,
        "parameter_bytes": 142052, "flops": flops, "workers": 1,
        "threads": 1, "native_width": 8, "dtype": "float32",
        "checkpoint_io": 1, "evaluation_opportunities": 2048,
        "tape_contract": {"schema": "TEST_TAPE_V1", "coordinate": 12},
    }


def _checkpoint():
    return serialize_checkpoint(
        manifest_contract={"schema": "TEST_MANIFEST_V1"},
        native_contract={"schema": "TEST_NATIVE_V1"},
        seed_packet_contract={"schema": "TEST_PACKET_V1"},
        update=12, frontiers={
            "training_update": 12, "minibatch_cursor": 0,
            "environment_cursor": 64, "evaluation_checkpoint_cursor": 1,
        }, arm_state_bytes={"PHY_TRUST": b"p", "EDGE_FLEX": b"e"},
        optimizer_state_bytes={"PHY_TRUST": b"op", "EDGE_FLEX": b"oe"},
        work_receipts={"PHY_TRUST": _work("PHY_TRUST"), "EDGE_FLEX": _work("EDGE_FLEX")},
        rng_frontier={
            "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1", "stateless": True,
            "tape_contract": {"schema": "TEST_TAPE_V1", "coordinate": 12},
        },
    )


def test_checkpoint_roundtrip_and_direct_contract_mismatch():
    data = _checkpoint()
    restored = restore_checkpoint(
        data, manifest_contract={"schema": "TEST_MANIFEST_V1"},
        native_contract={"schema": "TEST_NATIVE_V1"},
        seed_packet_contract={"schema": "TEST_PACKET_V1"}, expected_update=12,
    )
    assert restored["arm_state_bytes"]["PHY_TRUST"] == b"p"
    tampered = data.replace(b'"update":12', b'"update":13')
    with pytest.raises(CheckpointMismatch):
        restore_checkpoint(
            tampered, manifest_contract={"schema": "TEST_MANIFEST_V1"},
            native_contract={"schema": "TEST_NATIVE_V1"},
            seed_packet_contract={"schema": "TEST_PACKET_V1"}, expected_update=12,
        )


@pytest.mark.parametrize("mutation", ["update", "frontier", "rng", "work"])
def test_restore_revalidates_every_replay_and_work_contract(mutation):
    envelope = json.loads(_checkpoint().decode("ascii"))
    payload = envelope["payload"]
    if mutation == "update":
        payload["update"] = 999
    elif mutation == "frontier":
        payload["frontiers"] = "not-a-frontier"
    elif mutation == "rng":
        payload["rng_frontier"] = "not-an-rng-frontier"
    else:
        payload["work_receipts"]["EDGE_FLEX"]["flops"] += 1
    with pytest.raises(CheckpointMismatch):
        restore_checkpoint(
            canonical_json_bytes(envelope), manifest_contract={"schema": "TEST_MANIFEST_V1"},
            native_contract={"schema": "TEST_NATIVE_V1"},
            seed_packet_contract={"schema": "TEST_PACKET_V1"}, expected_update=12,
        )


def test_checkpoint_publication_is_create_only(tmp_path):
    path = tmp_path / "checkpoint.json"
    write_checkpoint_atomic(path, _checkpoint())
    with pytest.raises(CheckpointMismatch, match="create-only"):
        write_checkpoint_atomic(path, _checkpoint())
