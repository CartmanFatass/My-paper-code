from __future__ import annotations

import base64
import json
import struct
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.analysis import (
    summarize_parameter_distance_checkpoints,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    PARAMETER_DISTANCE_RAW_SCHEMA, PARAMETER_DISTANCE_STATE_SCHEMA,
    TEST_SEED_LABEL, UPDATES,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError,
)
import experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer as trainer_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    _parameter_distance_from_state_pair, create_paired_parameter_state_container_once,
    exact_parameter_layout, parameter_distance_raw_record_from_bindings,
    validate_parameter_distance_availability_index,
    validate_formal_parameter_distance_inventory,
    validate_parameter_distance_raw_record, write_parameter_distance_raw_record_once,
)


def _bits(value: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def _states():
    phy = np.zeros(35_513, dtype="<f4")
    edge = np.zeros(35_513, dtype="<f4")
    phy[5], edge[5] = np.float32(-2.0), np.float32(1.0)
    phy[26_982], edge[26_982] = np.float32(1.0), np.float32(0.0)
    return phy.tobytes(), edge.tobytes()


def _inline(state: bytes, *, seed: str, update: int, arm: str):
    return {
        "binding_kind": "INLINE_PARAMETER_BYTES",
        "parameter_bytes_b64": base64.b64encode(state).decode("ascii"),
        "seed_block": seed, "training_update": update, "arm_id": arm,
        "decoded_parameter_byte_count": 142_052, "state_stage": "POSTPROJECTION",
    }


def _inline_row(*, seed=TEST_SEED_LABEL, update=3, kappa=3, phy=None, edge=None):
    phy0, edge0 = _states()
    phy = phy0 if phy is None else phy
    edge = edge0 if edge is None else edge
    return parameter_distance_raw_record_from_bindings(
        seed_label=seed, update=update, first_tight_contact_update=kappa,
        phy_state_binding=_inline(phy, seed=seed, update=update, arm="PHY_TRUST"),
        edge_state_binding=_inline(edge, seed=seed, update=update, arm="EDGE_FLEX"),
        test_only_component=True,
    )


def test_exact_parameter_distance_is_signed_f64_and_only_three_linf_components():
    phy, edge = _states()
    direct = _parameter_distance_from_state_pair(phy, edge)
    assert direct["available"] is True
    signed = np.frombuffer(direct["signed_difference_f64_le_bytes"], dtype="<f8")
    assert signed.shape == (35_513,)
    assert signed[5] == -3.0 and signed[26_982] == 1.0
    assert direct["derived"] == {
        "linf_full_binary64_bits_u64": _bits(3.0),
        "linf_beta_binary64_bits_u64": _bits(1.0),
        "linf_nonbeta_binary64_bits_u64": _bits(3.0),
        "full_parameter_bytes_equal": False,
        "first_argmax_full_flat_index": 5,
        "first_argmax_beta_flat_index": 26_982,
        "first_argmax_nonbeta_flat_index": 5,
    }
    assert set(direct["derived"]).isdisjoint({"l1", "l2", "ratio", "normalized"})
    layout = exact_parameter_layout()
    assert layout["parameter_count"] == 35_513
    assert layout["parameter_byte_count"] == 142_052
    assert (layout["beta_flat_start"], layout["beta_flat_end_exclusive"]) == (26_982, 27_000)
    assert (layout["beta_byte_start"], layout["beta_byte_end_exclusive"]) == (107_928, 108_000)


def test_signed_zero_is_numeric_zero_but_literal_state_bytes_remain_unequal():
    phy = np.zeros(35_513, dtype="<f4")
    edge = np.zeros(35_513, dtype="<f4")
    edge[0] = np.float32(-0.0)
    direct = _parameter_distance_from_state_pair(phy.tobytes(), edge.tobytes())
    assert direct["derived"]["linf_full_binary64_bits_u64"] == _bits(0.0)
    assert direct["derived"]["full_parameter_bytes_equal"] is False


def test_paired_state_and_raw_records_are_create_once_atomic_and_literal_readback(tmp_path):
    phy, edge = _states()
    container_root = (tmp_path / "paired-state").resolve()
    state = create_paired_parameter_state_container_once(
        container_root, seed_label=TEST_SEED_LABEL, update=3,
        phy_state_bytes=phy, edge_state_bytes=edge, test_only_component=True,
    )
    row = parameter_distance_raw_record_from_bindings(
        seed_label=TEST_SEED_LABEL, update=3, first_tight_contact_update=3,
        phy_state_binding=state["bindings"]["PHY_TRUST"],
        edge_state_binding=state["bindings"]["EDGE_FLEX"],
        test_only_component=True,
    )
    assert row["schema"] == PARAMETER_DISTANCE_RAW_SCHEMA
    path = (tmp_path / "raw-update-003.json").resolve()
    validated = write_parameter_distance_raw_record_once(
        path, row, test_only_component=True,
    )
    assert validated["available"] is True
    assert validate_parameter_distance_raw_record(
        json.loads(path.read_text(encoding="utf-8")), test_only_component=True,
    )["available"] is True
    with pytest.raises(B01ContractError, match="not fresh"):
        write_parameter_distance_raw_record_once(path, row, test_only_component=True)
    with pytest.raises(B01ContractError, match="not fresh"):
        create_paired_parameter_state_container_once(
            container_root, seed_label=TEST_SEED_LABEL, update=3,
            phy_state_bytes=phy, edge_state_bytes=edge, test_only_component=True,
        )


def test_raw_publish_failure_quarantines_creating_file(monkeypatch, tmp_path):
    row = _inline_row()
    path = (tmp_path / "raw-fails.json").resolve()

    def fail_publish(staging, target):
        raise OSError("deliberate publish failure")

    monkeypatch.setattr(trainer_module, "_atomic_parameter_record_publish", fail_publish)
    with pytest.raises(OSError, match="deliberate"):
        write_parameter_distance_raw_record_once(path, row, test_only_component=True)
    assert not path.exists()
    assert path.with_name(path.name + ".incomplete").exists()
    assert not path.with_name(path.name + ".creating").exists()


def test_raw_post_publish_readback_failure_quarantines_exact_new_final(monkeypatch, tmp_path):
    row = _inline_row()
    path = (tmp_path / "raw-readback-fails.json").resolve()
    actual = trainer_module.validate_parameter_distance_raw_record
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise B01ContractError("deliberate readback failure")
        return actual(*args, **kwargs)

    monkeypatch.setattr(trainer_module, "validate_parameter_distance_raw_record", fail_second)
    with pytest.raises(B01ContractError, match="deliberate readback"):
        write_parameter_distance_raw_record_once(path, row, test_only_component=True)
    assert not path.exists()
    assert path.with_name(path.name + ".incomplete").exists()


def test_state_container_post_publish_failure_quarantines_exact_new_directory(monkeypatch, tmp_path):
    phy, edge = _states()
    root = (tmp_path / "state-readback-fails").resolve()

    def fail_resolve(*args, **kwargs):
        raise B01ContractError("deliberate state readback failure")

    monkeypatch.setattr(trainer_module, "_resolve_parameter_state_binding", fail_resolve)
    with pytest.raises(B01ContractError, match="deliberate state readback"):
        create_paired_parameter_state_container_once(
            root, seed_label=TEST_SEED_LABEL, update=3,
            phy_state_bytes=phy, edge_state_bytes=edge, test_only_component=True,
        )
    assert not root.exists()
    assert root.with_name(root.name + ".incomplete").exists()


def test_inline_and_state_ref_nonfinite_are_scoped_not_global(tmp_path):
    phy, edge = _states()
    corrupt = bytearray(phy)
    corrupt[:4] = np.asarray([np.nan], dtype="<f4").tobytes()
    row = _inline_row(phy=bytes(corrupt), edge=edge)
    # Builder returns an unavailable record for direct nonfinite input.
    assert row["availability_reason"] == "PARAMETER_DISTANCE_NONFINITE_RECORD"

    valid = _inline_row(phy=phy, edge=edge)
    valid["phy_state_binding"] = _inline(
        bytes(corrupt), seed=TEST_SEED_LABEL, update=3, arm="PHY_TRUST",
    )
    result = validate_parameter_distance_raw_record(valid, test_only_component=True)
    assert result["available"] is False
    assert result["availability_reason"] == "PARAMETER_DISTANCE_NONFINITE_RECORD"

    container = tmp_path / "nonfinite-ref"
    container.mkdir()
    (container / "PHY_TRUST.f32").write_bytes(bytes(corrupt))
    (container / "EDGE_FLEX.f32").write_bytes(edge)
    (container / "index.json").write_text(json.dumps({
        "schema": PARAMETER_DISTANCE_STATE_SCHEMA, "seed_block": TEST_SEED_LABEL,
        "training_update": 3, "state_stage": "POSTPROJECTION",
        "arm_files": {"PHY_TRUST": "PHY_TRUST.f32", "EDGE_FLEX": "EDGE_FLEX.f32"},
        "decoded_parameter_byte_count": 142_052,
        "resume_or_evaluation_capable": False, "complete": True,
    }), encoding="utf-8")
    ref = deepcopy(valid)
    ref["phy_state_binding"] = {
        "binding_kind": "IMMUTABLE_STATE_REF", "container_schema": PARAMETER_DISTANCE_STATE_SCHEMA,
        "container_path": str((container / "index.json").resolve()),
        "seed_block": TEST_SEED_LABEL, "training_update": 3, "arm_id": "PHY_TRUST",
        "field": "arm_state_bytes", "decoded_parameter_byte_count": 142_052,
        "state_stage": "POSTPROJECTION",
    }
    result = validate_parameter_distance_raw_record(ref, test_only_component=True)
    assert result["availability_reason"] == "PARAMETER_DISTANCE_NONFINITE_RECORD"


def test_missing_malformed_or_derived_drift_is_measurement_defect(tmp_path):
    row = _inline_row()
    altered = deepcopy(row)
    altered["derived"]["linf_full_binary64_bits_u64"] = _bits(99.0)
    result = validate_parameter_distance_raw_record(altered, test_only_component=True)
    assert result["availability_reason"] == "PARAMETER_DISTANCE_MEASUREMENT_DEFECT"
    missing = deepcopy(row)
    missing["phy_state_binding"] = {
        "binding_kind": "IMMUTABLE_STATE_REF", "container_schema": PARAMETER_DISTANCE_STATE_SCHEMA,
        "container_path": str((tmp_path / "absent.json").resolve()),
        "seed_block": TEST_SEED_LABEL, "training_update": 3, "arm_id": "PHY_TRUST",
        "field": "arm_state_bytes", "decoded_parameter_byte_count": 142_052,
        "state_stage": "POSTPROJECTION",
    }
    result = validate_parameter_distance_raw_record(missing, test_only_component=True)
    assert result["availability_reason"] == "PARAMETER_DISTANCE_MEASUREMENT_DEFECT"

    bad_container = tmp_path / "aliased-arm-ref"
    bad_container.mkdir()
    phy, _ = _states()
    (bad_container / "same.f32").write_bytes(phy)
    (bad_container / "index.json").write_text(json.dumps({
        "schema": PARAMETER_DISTANCE_STATE_SCHEMA, "seed_block": TEST_SEED_LABEL,
        "training_update": 3, "state_stage": "POSTPROJECTION",
        "arm_files": {"PHY_TRUST": "same.f32", "EDGE_FLEX": "same.f32"},
        "decoded_parameter_byte_count": 142_052,
        "resume_or_evaluation_capable": False, "complete": True,
    }), encoding="utf-8")
    aliased = deepcopy(row)
    aliased["phy_state_binding"] = {
        "binding_kind": "IMMUTABLE_STATE_REF", "container_schema": PARAMETER_DISTANCE_STATE_SCHEMA,
        "container_path": str((bad_container / "index.json").resolve()),
        "seed_block": TEST_SEED_LABEL, "training_update": 3, "arm_id": "PHY_TRUST",
        "field": "arm_state_bytes", "decoded_parameter_byte_count": 142_052,
        "state_stage": "POSTPROJECTION",
    }
    result = validate_parameter_distance_raw_record(aliased, test_only_component=True)
    assert result["availability_reason"] == "PARAMETER_DISTANCE_MEASUREMENT_DEFECT"


def test_manifest_binding_rejects_initial_004_and_test_label(b01_manifest):
    phy, edge = _states()
    for seed in (
        "FRRIE-B01-FRESH-BLOCK-001", "FRRIE-B01-FRESH-BLOCK-004", TEST_SEED_LABEL,
    ):
        row = {
            **_inline_row(), "seed_block": seed,
            "phy_state_binding": _inline(phy, seed=seed, update=3, arm="PHY_TRUST"),
            "edge_state_binding": _inline(edge, seed=seed, update=3, arm="EDGE_FLEX"),
        }
        with pytest.raises(B01ContractError, match="paired-shard-derived κ"):
            validate_parameter_distance_raw_record(row, manifest=b01_manifest)
    with pytest.raises(B01ContractError, match="explicit TEST"):
        validate_parameter_distance_raw_record(_inline_row())


def test_availability_index_and_checkpoint_reducer_never_impute_zero(tmp_path):
    row = _inline_row(update=32, kappa=3)
    path = (tmp_path / "raw-032.json").resolve()
    write_parameter_distance_raw_record_once(path, row, test_only_component=True)
    locators = [
        {"seed_block": TEST_SEED_LABEL, "training_update": update,
         "raw_record_path": str(path) if update == 32 else None}
        for update in range(1, UPDATES + 1)
    ]
    index = validate_parameter_distance_availability_index(
        locators, seed_label=TEST_SEED_LABEL, first_tight_contact_update=3,
        test_only_component=True,
    )
    assert index["records"][0]["availability_reason"] == "PRE_TIGHT_CONTACT"
    assert index["records"][2]["availability_reason"] == "PARAMETER_DISTANCE_MEASUREMENT_DEFECT"
    assert index["records"][31]["available"] is True
    assert index["available_count"] == 1
    summary = summarize_parameter_distance_checkpoints(
        {TEST_SEED_LABEL: index}, seed_order=[TEST_SEED_LABEL],
    )
    cp0, cp32 = summary["checkpoints"][0], summary["checkpoints"][1]
    assert cp0["status"] == "NO_POSTCONTACT_SEEDS"
    assert cp32["status"] == "DESCRIPTIVE_AVAILABLE"
    assert cp32["available_seed_count"] == 1
    assert cp32["components"]["LINF_FULL"]["mean_binary64_bits_u64"] == _bits(3.0)
    assert summary["temporal_reducer"] is None
    assert summary["branch_or_gate"] is False


def test_formal_inventory_derives_kappa_only_from_revalidated_paired_512_shards(
    monkeypatch, b01_manifest,
):
    seed = b01_manifest["execution_labels"][0]
    calls = []

    def validated(shards):
        calls.append(shards)
        return {
            "schema": "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1",
            "seed_label": seed, "kappa": 3,
            "training_validation_replay_complete": False,
        }

    monkeypatch.setattr(trainer_module, "validate_paired_training_shards", validated)
    rows = [
        {"seed_block": seed, "training_update": update, "raw_record_path": None}
        for update in range(1, UPDATES + 1)
    ]
    result = validate_formal_parameter_distance_inventory(
        rows, seed_label=seed, manifest=b01_manifest,
        paired_training_shards={"PHY_TRUST": "direct", "EDGE_FLEX": "direct"},
    )
    assert calls == [{"PHY_TRUST": "direct", "EDGE_FLEX": "direct"}]
    assert result["first_tight_contact_update"] == 3
    assert result["required_postcontact_updates"] == list(range(3, 513))
    assert result["caller_supplied_kappa_accepted"] is False
    assert result["records"][1]["availability_reason"] == "PRE_TIGHT_CONTACT"
    assert result["records"][2]["availability_reason"] == "PARAMETER_DISTANCE_MEASUREMENT_DEFECT"
    with pytest.raises(B01ContractError, match="must derive κ"):
        validate_parameter_distance_availability_index(
            rows, seed_label=seed, first_tight_contact_update=3,
            manifest=b01_manifest,
        )
