import base64
import json
import struct
from dataclasses import asdict
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import LearnedArm, PARAMETER_BYTE_COUNT
from experiments.candidates.finite_resource_relational_inductive_efficiency.checkpoint import FRRIE_CHECKPOINT_V2, CheckpointMismatch, block_checkpoint_path, learned_arm_state_bytes, restore_checkpoint, restore_learned_arms, serialize_checkpoint, write_block_checkpoint_atomic, write_checkpoint_atomic
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import FRRIE_CHECKPOINT_V1, FRRIE_MANIFEST_V1, FRRIE_MANIFEST_V2, ContractError, INFERENCE_CONTRACT, LEARNED_ARMS, REQUIRED_SEED_BLOCKS, THRESHOLDS, canonical_json_bytes, manifest_packet_contract
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import expected_native_contract
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION
from experiments.candidates.finite_resource_relational_inductive_efficiency.work import checkpoint_cumulative_work, planned_work


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


def _arms():
    from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
    phy, edge = initialize_paired_arms(
        AddressedRNG(b"C" * 32), "FRRIE-CHECKPOINT-STATE-TEST"
    )
    return {phy.arm_id: phy, edge.arm_id: edge}


def _packet(manifest):
    return {
        "schema": "FRRIE_SEALED_SEED_PACKET_V2",
        "version": 2,
        "manifest_contract": manifest_packet_contract(manifest),
        "blocks": list(manifest["seed_blocks"]),
        "addressed_rng_roots": [f"{index:064x}" for index in range(1, 25)],
        "generation_provenance": "TEST_ONLY_CHECKPOINT_GENERATION_PROVENANCE",
        "no_prior_use": True,
        "sealed": True,
        "complete": True,
    }


def _optimizer_blob(*, step=512):
    payload = b"\0" * (OPTIMIZER_PAYLOAD_BYTE_COUNT - 8) + struct.pack("<Q", step)
    return struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION, len(payload)
    ) + payload


def _production_checkpoint(manifest, seed_block=None):
    seed_block = manifest["seed_blocks"][0] if seed_block is None else seed_block
    state = learned_arm_state_bytes(_arms())
    return serialize_checkpoint(
        manifest_contract=manifest,
        native_contract=asdict(expected_native_contract(manifest["compute"])),
        seed_packet_contract=_packet(manifest),
        seed_packet_path=manifest["sealed_seed_packet"]["path"],
        seed_block=seed_block,
        update=512,
        frontiers={
            "training_update": 512,
            "minibatch_cursor": 0,
            "factual_episode_cursor": 512 * 64,
            "factual_environment_slot_cursor": 393_216,
            "alternative_suffix_environment_slot_cursor": 1_490_944,
            "evaluation_checkpoint_cursor": 0,
        },
        arm_state_bytes=state,
        optimizer_state_bytes={arm: _optimizer_blob() for arm in LEARNED_ARMS},
        work_receipts=checkpoint_cumulative_work(manifest["compute"]),
        rng_frontier={
            "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1",
            "stateless": True,
            "tape_contract": {"schema": "FRRIE_TEST_TAPE_V1", "coordinate": 512},
        },
    )


def _restore_production(data, manifest, seed_block=None, packet=None, native=None):
    seed_block = manifest["seed_blocks"][0] if seed_block is None else seed_block
    return restore_checkpoint(
        data,
        manifest_contract=manifest,
        native_contract=(
            asdict(expected_native_contract(manifest["compute"]))
            if native is None else native
        ),
        seed_packet_contract=_packet(manifest) if packet is None else packet,
        seed_packet_path=manifest["sealed_seed_packet"]["path"],
        expected_seed_block=seed_block,
        expected_update=512,
    )


def _production_manifest(manifest_factory):
    """Adapt the shared factory while concurrent contract-fixture edits settle."""
    manifest = manifest_factory()
    manifest.pop("generic_competence", None)
    manifest.pop("work_to_threshold", None)
    manifest.pop("work_parity", None)
    manifest["schema"] = FRRIE_MANIFEST_V2
    manifest["seed_blocks"] = list(REQUIRED_SEED_BLOCKS)
    manifest["training"]["checkpoints"] = [512]
    manifest["thresholds"] = deepcopy(THRESHOLDS)
    manifest["inference"] = deepcopy(INFERENCE_CONTRACT)
    manifest["planned_work"] = planned_work(manifest["compute"])
    return manifest


def test_checkpoint_roundtrip_and_direct_contract_mismatch():
    data = _checkpoint()
    assert json.loads(data.decode("ascii"))["schema"] == FRRIE_CHECKPOINT_V2
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


def test_checkpoint_v1_and_production_manifest_v1_are_rejected_as_legacy():
    envelope = json.loads(_checkpoint().decode("ascii"))
    envelope["schema"] = FRRIE_CHECKPOINT_V1
    with pytest.raises(CheckpointMismatch, match="schema/completeness"):
        restore_checkpoint(
            canonical_json_bytes(envelope),
            manifest_contract={"schema": "TEST_MANIFEST_V1"},
            native_contract={"schema": "TEST_NATIVE_V1"},
            seed_packet_contract={"schema": "TEST_PACKET_V1"},
            expected_update=12,
        )
    with pytest.raises(CheckpointMismatch, match="rejected legacy scaffold"):
        serialize_checkpoint(
            manifest_contract={"schema": FRRIE_MANIFEST_V1},
            native_contract={"schema": "TEST_NATIVE_V1"},
            seed_packet_contract={"schema": "TEST_PACKET_V1"},
            update=12,
            frontiers={
                "training_update": 12, "minibatch_cursor": 0,
                "environment_cursor": 64, "evaluation_checkpoint_cursor": 1,
            },
            arm_state_bytes={"PHY_TRUST": b"p", "EDGE_FLEX": b"e"},
            optimizer_state_bytes={"PHY_TRUST": b"op", "EDGE_FLEX": b"oe"},
            work_receipts={arm: _work(arm) for arm in LEARNED_ARMS},
            rng_frontier={
                "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1", "stateless": True,
                "tape_contract": {"schema": "TEST_TAPE_V1", "coordinate": 12},
            },
        )


def test_actual_learned_arm_bytes_roundtrip_through_canonical_checkpoint():
    original = _arms()
    state = learned_arm_state_bytes(original)
    assert all(len(blob) == PARAMETER_BYTE_COUNT for blob in state.values())
    data = serialize_checkpoint(
        manifest_contract={"schema": "TEST_MANIFEST_V1"},
        native_contract={"schema": "TEST_NATIVE_V1"},
        seed_packet_contract={"schema": "TEST_PACKET_V1"},
        update=12,
        frontiers={
            "training_update": 12, "minibatch_cursor": 0,
            "environment_cursor": 64, "evaluation_checkpoint_cursor": 1,
        },
        arm_state_bytes=state,
        optimizer_state_bytes={arm: b"opaque" for arm in LEARNED_ARMS},
        work_receipts={arm: _work(arm) for arm in LEARNED_ARMS},
        rng_frontier={
            "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1", "stateless": True,
            "tape_contract": {"schema": "TEST_TAPE_V1", "coordinate": 12},
        },
    )
    payload = restore_checkpoint(
        data,
        manifest_contract={"schema": "TEST_MANIFEST_V1"},
        native_contract={"schema": "TEST_NATIVE_V1"},
        seed_packet_contract={"schema": "TEST_PACKET_V1"},
        expected_update=12,
    )
    restored = restore_learned_arms(payload["arm_state_bytes"])
    assert learned_arm_state_bytes(restored) == state
    assert {arm_id: arm.projection_box for arm_id, arm in restored.items()} == {
        "PHY_TRUST": (-0.15, 0.15), "EDGE_FLEX": (-1.5, 1.5),
    }


def test_learned_arm_restore_rejects_wrong_length_and_nonfinite_bytes():
    blob = next(iter(learned_arm_state_bytes(_arms()).values()))
    with pytest.raises(ContractError, match="exactly 142052 bytes"):
        LearnedArm.from_parameter_bytes("PHY_TRUST", blob[:-1])
    nonfinite = bytearray(blob)
    nonfinite[:4] = np.float32(np.nan).tobytes()
    with pytest.raises(ContractError, match="finite FP32"):
        LearnedArm.from_parameter_bytes("PHY_TRUST", bytes(nonfinite))


@pytest.mark.parametrize("layout", ["dtype", "order"])
def test_parameter_serialization_rejects_dtype_or_order_drift(layout):
    arm = _arms()["PHY_TRUST"]
    name = "message_encoder.weight_ih"
    if layout == "dtype":
        arm.parameters[name] = arm.parameters[name].astype(">f4")
    else:
        arm.parameters[name] = np.asfortranarray(arm.parameters[name])
    with pytest.raises(ContractError, match="C-order little-endian FP32"):
        arm.parameter_bytes()


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


def test_real_frrie_checkpoint_is_post_train_and_pre_evaluation(manifest_factory):
    manifest = _production_manifest(manifest_factory)
    payload = _restore_production(_production_checkpoint(manifest), manifest)
    assert manifest["planned_work"]["PHY_TRUST"]["evaluation_opportunities"] == 8 * 256
    assert payload["seed_block"] == manifest["seed_blocks"][0]
    assert set(payload["seed_packet_contract"]) == {
        "packet_path", "schema", "version", "block_index", "block_label",
        "generation_provenance", "no_prior_use",
    }
    assert "addressed_rng_roots" not in payload["seed_packet_contract"]
    assert payload["frontiers"] == {
        "training_update": 512,
        "minibatch_cursor": 0,
        "factual_episode_cursor": 512 * 64,
        "factual_environment_slot_cursor": 393_216,
        "alternative_suffix_environment_slot_cursor": 1_490_944,
        "evaluation_checkpoint_cursor": 0,
    }
    assert all(
        payload["work_receipts"]["arms"][arm]["checkpoint_io"] == 1
        and payload["work_receipts"]["arms"][arm]["evaluation_opportunities"] == 0
        for arm in LEARNED_ARMS
    )


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("frontiers", "training_update", 511),
        ("frontiers", "minibatch_cursor", 1),
        ("frontiers", "factual_episode_cursor", 512 * 64 - 1),
        ("frontiers", "factual_environment_slot_cursor", 393_215),
        ("frontiers", "alternative_suffix_environment_slot_cursor", 1_490_943),
        ("frontiers", "evaluation_checkpoint_cursor", 1),
        ("receipt", "factual_train_environment_slots", 2),
        ("receipt", "alternative_suffix_environment_slots", 2),
        ("receipt", "learned_eval_environment_slots", 24_576),
        ("receipt", "environment_slots", 2),
        ("receipt", "base_policy_decisions", 2),
        ("receipt", "suffix_future_policy_decisions", 2),
        ("receipt", "learned_eval_policy_decisions", 313_344),
        ("receipt", "shadow_audit_policy_decisions", 2),
        ("receipt", "learned_decisions", 2),
        ("receipt", "backward_calls", 511),
        ("receipt", "adam_steps", 511),
        ("receipt", "parameter_bytes", 1),
        ("receipt", "workers", 2),
        ("receipt", "threads", 2),
        ("receipt", "native_width", 16),
        ("receipt", "dtype", "float64"),
        ("receipt", "checkpoint_io", 0),
        ("receipt", "evaluation_opportunities", 8 * 256),
    ],
)
def test_real_frrie_checkpoint_rejects_frontier_and_counter_tampering(
    manifest_factory, section, field, value,
):
    manifest = _production_manifest(manifest_factory)
    envelope = json.loads(_production_checkpoint(manifest).decode("ascii"))
    if section == "frontiers":
        envelope["payload"]["frontiers"][field] = value
    else:
        envelope["payload"]["work_receipts"]["arms"]["PHY_TRUST"][field] = value
    with pytest.raises(CheckpointMismatch):
        _restore_production(canonical_json_bytes(envelope), manifest)


@pytest.mark.parametrize("mutation", ["block", "native", "seed_binding"])
def test_real_frrie_checkpoint_rejects_block_native_and_seed_binding_tampering(
    manifest_factory, mutation,
):
    manifest = _production_manifest(manifest_factory)
    envelope = json.loads(_production_checkpoint(manifest).decode("ascii"))
    if mutation == "block":
        envelope["payload"]["seed_block"] = manifest["seed_blocks"][1]
    elif mutation == "native":
        envelope["payload"]["native_contract"]["native_width"] += 1
    else:
        envelope["payload"]["seed_packet_contract"]["block_index"] = 1
    with pytest.raises(CheckpointMismatch):
        _restore_production(canonical_json_bytes(envelope), manifest)


def test_restore_revalidates_current_seed_packet_path_and_expected_block(manifest_factory):
    manifest = _production_manifest(manifest_factory)
    data = _production_checkpoint(manifest)
    changed_packet = _packet(manifest)
    changed_packet["generation_provenance"] = "DIFFERENT_CURRENT_PACKET"
    with pytest.raises(CheckpointMismatch, match="seed_packet_contract mismatch"):
        _restore_production(data, manifest, packet=changed_packet)
    with pytest.raises(CheckpointMismatch, match="seed block mismatch"):
        _restore_production(data, manifest, seed_block=manifest["seed_blocks"][1])
    with pytest.raises(CheckpointMismatch, match="packet path"):
        restore_checkpoint(
            data,
            manifest_contract=manifest,
            native_contract=asdict(expected_native_contract(manifest["compute"])),
            seed_packet_contract=_packet(manifest),
            seed_packet_path=manifest["roots"]["output"],
            expected_seed_block=manifest["seed_blocks"][0],
            expected_update=512,
        )


@pytest.mark.parametrize("mutation", ["step", "nonfinite"])
def test_real_frrie_checkpoint_rejects_optimizer_step_and_nonfinite_moments(
    manifest_factory, mutation,
):
    manifest = _production_manifest(manifest_factory)
    envelope = json.loads(_production_checkpoint(manifest).decode("ascii"))
    blob = bytearray(base64.b64decode(
        envelope["payload"]["optimizer_state_bytes"]["PHY_TRUST"], validate=True
    ))
    if mutation == "step":
        blob[-8:] = struct.pack("<Q", 511)
    else:
        blob[16:20] = np.float32(np.nan).tobytes()
    envelope["payload"]["optimizer_state_bytes"]["PHY_TRUST"] = base64.b64encode(
        blob
    ).decode("ascii")
    with pytest.raises(CheckpointMismatch, match="optimizer|Adam"):
        _restore_production(canonical_json_bytes(envelope), manifest)


def test_block_checkpoint_inventory_is_exactly_24_create_only_paths(manifest_factory):
    manifest = _production_manifest(manifest_factory)
    root = Path(manifest["roots"]["checkpoint"]).resolve(strict=False)
    inventory = [block_checkpoint_path(manifest, block) for block in manifest["seed_blocks"]]
    assert len(inventory) == len(set(inventory)) == 24
    assert [path.parent.name for path in inventory] == manifest["seed_blocks"]
    assert all(
        path.name == "update-512.json" and path.is_relative_to(root)
        for path in inventory
    )
    with pytest.raises(CheckpointMismatch, match="outside the manifest inventory"):
        block_checkpoint_path(manifest, "../outside")

    data = _production_checkpoint(manifest)
    with pytest.raises(CheckpointMismatch, match="publication path binding"):
        write_block_checkpoint_atomic(manifest, manifest["seed_blocks"][1], data)
    target = write_block_checkpoint_atomic(manifest, manifest["seed_blocks"][0], data)
    assert target == inventory[0] and target.read_bytes() == data
    with pytest.raises(CheckpointMismatch, match="create-only"):
        write_block_checkpoint_atomic(manifest, manifest["seed_blocks"][0], data)


def test_checkpoint_publication_is_create_only(tmp_path):
    path = tmp_path / "checkpoint.json"
    write_checkpoint_atomic(path, _checkpoint())
    with pytest.raises(CheckpointMismatch, match="create-only"):
        write_checkpoint_atomic(path, _checkpoint())
