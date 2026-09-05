from __future__ import annotations

import base64
import json
import subprocess
import struct
import sys
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import (
    checkpoint as checkpoint_module,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import (
    PARAMETER_BYTE_COUNT,
)

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_BYTE_COUNT,
    OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import (
    continuation_state_from_decoded_checkpoint,
    decode_checkpoint, encode_checkpoint, reopen_decode_restore_checkpoint,
    reopen_decode_restore_test_checkpoint, reopen_decode_restore_test_checkpoint0,
    restore_trainer_continuation_state, validate_checkpoint_resume_bridge,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import B01ContractError


def _zero_optimizer() -> bytes:
    payload = bytes(OPTIMIZER_PAYLOAD_BYTE_COUNT)
    value = struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
        OPTIMIZER_PAYLOAD_BYTE_COUNT,
    ) + payload
    assert len(value) == OPTIMIZER_STATE_BYTE_COUNT
    return value


def _optimizer_at(update: int) -> bytes:
    value = bytearray(_zero_optimizer())
    struct.pack_into("<Q", value, len(value) - 8, update)
    return bytes(value)


def _work():
    row = {
        "training_update": 0, "episodes": 0, "environment_slots": 0,
        "backward_calls": 0, "adam_steps": 0, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": 0,
        },
        "worker_count": 4, "thread_count": 1,
    }
    return {"PHY_TRUST": dict(row), "EDGE_FLEX": dict(row)}


def _work_at(update: int):
    row = {
        "training_update": update,
        "episodes": update * 64,
        "environment_slots": update * 4_928,
        "backward_calls": update,
        "adam_steps": update,
        "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0,
            "observe_calls": 0,
            "step_calls": 0,
            "environment_slots": update * 4_928,
        },
        "worker_count": 4,
        "thread_count": 1,
    }
    return {"PHY_TRUST": dict(row), "EDGE_FLEX": dict(row)}


def _checkpoint_and_resume_coordinates(
    *, update, b01_test_manifest, b01_resource_binding,
):
    phy, edge = initialize_paired_arms(
        AddressedRNG(b"V" * 32), "FRRIE-B01-CHECKPOINT-BRIDGE"
    )
    model_bytes = {
        "PHY_TRUST": phy.parameter_bytes(),
        "EDGE_FLEX": edge.parameter_bytes(),
    }
    optimizer_bytes = {
        "PHY_TRUST": _optimizer_at(update),
        "EDGE_FLEX": _optimizer_at(update),
    }
    data = encode_checkpoint(
        manifest=b01_test_manifest,
        seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
        update=update,
        arm_state_bytes=model_bytes,
        optimizer_state_bytes=optimizer_bytes,
        work=_work_at(update),
        invocation_binding=b01_resource_binding,
        projection_audit=_audit(),
    )

    def state():
        return {
            arm: {
                "model_state_bytes": model_bytes[arm],
                "optimizer_state_bytes": optimizer_bytes[arm],
            }
            for arm in ("PHY_TRUST", "EDGE_FLEX")
        }

    coordinates = {}
    if update == 0:
        coordinates["uninterrupted_update_001_prestate"] = state()
    else:
        coordinates[f"uninterrupted_update_{update:03d}_postprojection"] = state()
    if update < 512:
        next_update = update + 1
        if update > 0:
            coordinates[f"uninterrupted_update_{next_update:03d}_prestate"] = state()
        coordinates[f"resumed_update_{next_update:03d}_prestate"] = state()
    return data, coordinates


@pytest.mark.parametrize("update", [0, 32, 64, 128, 256, 512])
def test_codec_only_resume_bridge_proves_all_six_checkpoint_byte_laws(
    update, b01_test_manifest, b01_resource_binding,
):
    data, coordinates = _checkpoint_and_resume_coordinates(
        update=update,
        b01_test_manifest=b01_test_manifest,
        b01_resource_binding=b01_resource_binding,
    )
    receipt = validate_checkpoint_resume_bridge(
        data,
        manifest=b01_test_manifest,
        expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
        expected_update=update,
        expected_test_only=True,
        state_coordinates=coordinates,
    )
    assert receipt == {
        "schema": "FRRIE_B01_CHECKPOINT_RESUME_BRIDGE_COMPONENT_V1",
        "seed_label": "FRRIE-B01-TEST-ONLY-BLOCK-001",
        "checkpoint": update,
        "coordinate_order": list(coordinates),
        "checkpoint_decode_complete": True,
        "provided_resume_prestate_bytes_validated": update < 512,
        "terminal_no_next_bridge": update == 512,
        "codec_only": True,
        "training_transition_proven": False,
        "training_validation_replay_complete": False,
        "production_token": False,
    }


@pytest.mark.parametrize("arm", ["PHY_TRUST", "EDGE_FLEX"])
@pytest.mark.parametrize("field", ["model_state_bytes", "optimizer_state_bytes"])
def test_resume_bridge_rejects_every_direct_byte_field_tamper(
    arm, field, b01_test_manifest, b01_resource_binding,
):
    data, coordinates = _checkpoint_and_resume_coordinates(
        update=32,
        b01_test_manifest=b01_test_manifest,
        b01_resource_binding=b01_resource_binding,
    )
    for coordinate in tuple(coordinates):
        tampered = {
            name: {
                item_arm: dict(blobs)
                for item_arm, blobs in states.items()
            }
            for name, states in coordinates.items()
        }
        original = tampered[coordinate][arm][field]
        tampered[coordinate][arm][field] = bytes([original[0] ^ 1]) + original[1:]
        with pytest.raises(B01ContractError, match="direct .* bytes differ"):
            validate_checkpoint_resume_bridge(
                data,
                manifest=b01_test_manifest,
                expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
                expected_update=32,
                expected_test_only=True,
                state_coordinates=tampered,
            )


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_resume_bridge_rejects_missing_or_extra_coordinate(
    mutation, b01_test_manifest, b01_resource_binding,
):
    data, coordinates = _checkpoint_and_resume_coordinates(
        update=64,
        b01_test_manifest=b01_test_manifest,
        b01_resource_binding=b01_resource_binding,
    )
    if mutation == "missing":
        coordinates.pop(next(iter(coordinates)))
    else:
        coordinates["unregistered_coordinate"] = next(iter(coordinates.values()))
    with pytest.raises(B01ContractError, match="coordinate inventory differs"):
        validate_checkpoint_resume_bridge(
            data,
            manifest=b01_test_manifest,
            expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
            expected_update=64,
            expected_test_only=True,
            state_coordinates=coordinates,
        )


@pytest.mark.parametrize("tamper", ["step", "frontier"])
def test_resume_bridge_rejects_wrong_checkpoint_step_or_frontier(
    tamper, b01_test_manifest, b01_resource_binding,
):
    data, coordinates = _checkpoint_and_resume_coordinates(
        update=128,
        b01_test_manifest=b01_test_manifest,
        b01_resource_binding=b01_resource_binding,
    )
    payload = json.loads(data)
    if tamper == "step":
        blob = bytearray(base64.b64decode(
            payload["optimizer_state_b64"]["PHY_TRUST"]
        ))
        struct.pack_into("<Q", blob, len(blob) - 8, 127)
        payload["optimizer_state_b64"]["PHY_TRUST"] = base64.b64encode(
            blob
        ).decode("ascii")
    else:
        payload["frontier"]["training_episode_cursor"] -= 1
    tampered = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    with pytest.raises(B01ContractError):
        validate_checkpoint_resume_bridge(
            tampered,
            manifest=b01_test_manifest,
            expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
            expected_update=128,
            expected_test_only=True,
            state_coordinates=coordinates,
        )


def _audit():
    return {
        "first_tight_contact_update": None,
        "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 0,
        "tight_projection_changed_indices": [],
        "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0,
        "cumulative_tight_displacement": 0.0,
    }


class _AuditTarget:
    def __init__(self):
        self.state = None

    def restore_checkpoint_continuation_state(self, state):
        self.state = dict(state)

    def checkpoint_continuation_state(self):
        return self.state


def test_continuation_state_binds_exact_audit_work_frontier_and_explicit_api():
    audit = _audit()
    audit.update({
        "first_tight_contact_update": 17,
        "tight_projection_changed_coordinates": 3,
        "tight_projection_changed_indices": [0, 7, 17],
        "maximum_tight_overshoot": 0.01,
        "cumulative_tight_displacement": 0.02,
    })
    decoded = {
        "seed_label": "FRRIE-B01-TEST-ONLY-BLOCK-001", "update": 32,
        "frontier": {
            "training_update": 32, "training_episode_cursor": 2_048,
            "evaluation_checkpoint_cursor": 0, "completed_checkpoints": [0, 32],
        },
        "work": _work_at(32), "projection_audit": audit,
        "arm_state_bytes": {}, "optimizer_state_bytes": {},
    }
    state = continuation_state_from_decoded_checkpoint(decoded)
    assert state["tight_projection_changed_indices"] == [0, 7, 17]
    assert state["first_tight_contact_update"] == 17
    target = _AuditTarget()
    receipt = restore_trainer_continuation_state(target, decoded)
    assert receipt["complete"] is True and receipt["direct_readback_equal"] is True
    assert target.state == state
    with pytest.raises(B01ContractError, match="explicit checkpoint continuation"):
        restore_trainer_continuation_state(object(), decoded)
    bad = dict(decoded)
    bad["projection_audit"] = {**audit, "tight_projection_changed_indices": [0, 17]}
    with pytest.raises(B01ContractError, match="inventory differs"):
        continuation_state_from_decoded_checkpoint(bad)
    legacy = dict(decoded)
    legacy["projection_audit"] = {
        key: value for key, value in audit.items()
        if key != "tight_projection_changed_indices"
    }
    with pytest.raises(B01ContractError, match="lacks exact continuation"):
        continuation_state_from_decoded_checkpoint(legacy)


def test_checkpoint_zero_roundtrip_binds_pair_manifest_work_and_resource(
    b01_test_manifest, b01_resource_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-PAIR")
    data = encode_checkpoint(
        manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
        work=_work(), invocation_binding=b01_resource_binding,
        projection_audit=_audit(),
    )
    decoded = decode_checkpoint(
        data, manifest=b01_test_manifest,
        expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", expected_update=0,
        expected_test_only=True,
    )
    assert decoded["arm_state_bytes"]["PHY_TRUST"] == phy.parameter_bytes()
    assert decoded["optimizer_state_bytes"]["EDGE_FLEX"] == _zero_optimizer()


def test_panel_checkpoint_literal_reopen_decode_and_paired_restore(
    tmp_path, b01_manifest, b01_production_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-B01-RESTORE-PANEL")
    data = encode_checkpoint(
        manifest=b01_manifest, seed_label="FRRIE-B01-FRESH-BLOCK-001", update=0,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
        work=_work(), invocation_binding=b01_production_binding, projection_audit=_audit(),
    )
    path = (tmp_path / "literal-checkpoint-0.json").resolve()
    path.write_bytes(data)
    receipt = reopen_decode_restore_checkpoint(
        path, manifest=b01_manifest, seed_label="FRRIE-B01-FRESH-BLOCK-001", update=0,
    )
    assert receipt["literal_byte_count"] == len(data)
    assert receipt["paired_decode_complete"] is True
    assert receipt["paired_restore_complete"] is True


def test_explicit_test_checkpoint0_reopen_does_not_open_formal_panel_helper(
    tmp_path, b01_test_manifest, b01_resource_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-PAIR")
    data = encode_checkpoint(
        manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
        work=_work(), invocation_binding=b01_resource_binding, projection_audit=_audit(),
    )
    path = (tmp_path / "test-checkpoint0.json").resolve()
    path.write_bytes(data)
    with pytest.raises(B01ContractError, match="namespace"):
        reopen_decode_restore_checkpoint(
            path, manifest=b01_test_manifest,
            seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
        )
    receipt_path = (tmp_path / "adjacent-admit-memory.json").resolve()
    completed = subprocess.run(
        [sys.executable, str(Path("scripts/hmasd_resource_preflight.py").resolve()),
         "admit-memory", "--out", str(receipt_path)],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    receipt = reopen_decode_restore_test_checkpoint0(
        path, manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
    )
    assert receipt["checkpoint"] == 0 and receipt["paired_restore_complete"] is True
    general = reopen_decode_restore_test_checkpoint(
        path, manifest=b01_test_manifest,
        seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
    )
    assert general == receipt


def test_checkpoint_rejects_partial_pair_and_manifest_tamper(
    b01_test_manifest, b01_resource_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-PAIR")
    kwargs = dict(
        manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
        arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
        optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
        work=_work(), invocation_binding=b01_resource_binding,
        projection_audit=_audit(),
    )
    with pytest.raises(B01ContractError):
        encode_checkpoint(**dict(kwargs, optimizer_state_bytes={"PHY_TRUST": _zero_optimizer()}))
    data = encode_checkpoint(**kwargs)
    payload = json.loads(data)
    payload["manifest_contract"]["namespace"] = "NOT_TEST"
    tampered = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    with pytest.raises(B01ContractError, match="manifest binding"):
        decode_checkpoint(
            tampered, manifest=b01_test_manifest,
            expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", expected_update=0,
            expected_test_only=True,
        )


def test_checkpoint_requires_exact_4928_slots_and_projection_bounds(
    b01_test_manifest, b01_resource_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-PAIR")
    work = _work()
    work["PHY_TRUST"]["environment_slots"] = 1
    with pytest.raises(B01ContractError, match="completed-update frontier"):
        encode_checkpoint(
            manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
            arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
            optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
            work=work, invocation_binding=b01_resource_binding, projection_audit=_audit(),
        )


def test_production_checkpoint_accepts_only_current_phase_labels(
    b01_manifest, b01_production_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-PAIR")
    with pytest.raises(B01ContractError, match="execution phase"):
        encode_checkpoint(
            manifest=b01_manifest, seed_label="FRRIE-B01-FRESH-BLOCK-004", update=0,
            arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
            optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
            work=_work(), invocation_binding=b01_production_binding, projection_audit=_audit(),
        )


def test_decode_rejects_mutually_substituted_payload_and_expected_seed_outside_phase(
    b01_manifest, b01_production_binding,
):
    seed = b01_manifest["execution_labels"][0]
    phy, edge = initialize_paired_arms(
        AddressedRNG(b"T" * 32), "FRRIE-B01-DECODE-PHASE-MEMBERSHIP"
    )
    data = encode_checkpoint(
        manifest=b01_manifest, seed_label=seed, update=0,
        arm_state_bytes={
            "PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes(),
        },
        optimizer_state_bytes={
            "PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer(),
        },
        work=_work(), invocation_binding=b01_production_binding,
        projection_audit=_audit(),
    )
    payload = json.loads(data)
    substituted = "FRRIE-B01-FRESH-BLOCK-004"
    assert substituted not in b01_manifest["execution_labels"]
    payload["seed_label"] = substituted
    tampered = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
    ).encode("ascii")
    with pytest.raises(B01ContractError, match="outside this execution phase"):
        decode_checkpoint(
            tampered, manifest=b01_manifest, expected_seed_label=substituted,
            expected_update=0, expected_test_only=False,
        )


def test_no_contact_checkpoint_rejects_full_state_divergence(
    b01_test_manifest, b01_resource_binding,
):
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-PAIR")
    other, _ = initialize_paired_arms(AddressedRNG(b"U" * 32), "FRRIE-TEST-ONLY-B01-OTHER")
    with pytest.raises(B01ContractError, match="full paired"):
        encode_checkpoint(
            manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
            arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": other.parameter_bytes()},
            optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
            work=_work(), invocation_binding=b01_resource_binding, projection_audit=_audit(),
        )
    audit = _audit()
    audit["tight_projection_changed_coordinates"] = 19
    with pytest.raises(B01ContractError, match="18 beta"):
        encode_checkpoint(
            manifest=b01_test_manifest, seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=0,
            arm_state_bytes={"PHY_TRUST": phy.parameter_bytes(), "EDGE_FLEX": edge.parameter_bytes()},
            optimizer_state_bytes={"PHY_TRUST": _zero_optimizer(), "EDGE_FLEX": _zero_optimizer()},
            work=_work(), invocation_binding=b01_resource_binding, projection_audit=audit,
        )


def test_new_contact_checkpoint_cannot_encode_count_only_unrestorable_audit(
    b01_test_manifest, b01_resource_binding, monkeypatch,
):
    monkeypatch.setattr(
        checkpoint_module.LearnedArm, "from_parameter_bytes",
        lambda arm, data: object(),
    )
    model = bytes(PARAMETER_BYTE_COUNT)
    audit = {
        "first_tight_contact_update": 17,
        "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 1,
        "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.01,
        "cumulative_tight_displacement": 0.01,
    }
    with pytest.raises(B01ContractError, match="exact changed-coordinate"):
        encode_checkpoint(
            manifest=b01_test_manifest,
            seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001", update=32,
            arm_state_bytes={
                "PHY_TRUST": model, "EDGE_FLEX": model,
            },
            optimizer_state_bytes={
                "PHY_TRUST": _optimizer_at(32), "EDGE_FLEX": _optimizer_at(32),
            },
            work=_work_at(32), invocation_binding=b01_resource_binding,
            projection_audit=audit,
        )
