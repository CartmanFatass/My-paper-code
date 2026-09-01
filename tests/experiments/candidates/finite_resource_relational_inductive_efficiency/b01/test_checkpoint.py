from __future__ import annotations

import json
import subprocess
import struct
import sys
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_BYTE_COUNT,
    OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import (
    decode_checkpoint, encode_checkpoint, reopen_decode_restore_checkpoint,
    reopen_decode_restore_test_checkpoint0,
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


def _audit():
    return {
        "first_tight_contact_update": None,
        "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 0,
        "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0,
        "cumulative_tight_displacement": 0.0,
    }


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
