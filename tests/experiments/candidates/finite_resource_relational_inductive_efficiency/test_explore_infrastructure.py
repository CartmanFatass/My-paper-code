from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.explore_infrastructure import (
    B_CURVE_SCHEMA,
    B_QUARANTINE_SCHEMA,
    B_SPEC_SCHEMA,
    B_TELEMETRY_SCHEMA,
    ExploreContractError,
    ExplorePublicationError,
    ProcessTreePeakMonitor,
    ProcessTreeSample,
    claim_explore_namespace,
    finalize_paired_curve,
    recursive_byte_census,
    validate_explore_spec,
    validate_paired_curve,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.preflight import (
    _actual_package_source_inventory,
)


def _spec_value(tmp_path: Path) -> dict[str, object]:
    return {
        "schema": B_SPEC_SCHEMA,
        "study_id": "TEST-B-STUDY",
        "evidence_class": "B_EXPLORE",
        "claim_ceiling": "TEST_ONLY_PRELIMINARY_SIGNAL",
        "arms": ["PHY_TRUST", "EDGE_FLEX"],
        "competence_arm": "EDGE_FLEX",
        "seeds": ["SEED-A", "SEED-B"],
        "checkpoints": [3, 7],
        "cells": [
            {"cell_id": "TRAIN-5-INTACT", "roster": 5, "split": "TRAIN", "intervention": "INTACT"},
            {"cell_id": "HELD-8-CUT", "roster": 8, "split": "HELDOUT", "intervention": "REASSOCIATED"},
        ],
        "counter_semantics": "CUMULATIVE_AT_CHECKPOINT",
        "adaptation_record": {
            "previous_named_run": None,
            "changes": ["TEST_ONLY initial named run"],
            "reason": "TEST_ONLY infrastructure exercise",
        },
        "stopping_rule": {"name": "EXTERNALLY_FROZEN_TEST_STOP", "maximum_checkpoint": 7},
        "interpretation_rule": {"name": "TEST_ONLY_NO_SCIENTIFIC_INTERPRETATION"},
        "resource_admission_rule": {
            "receipt_schema": "TEST_ONLY_ADMIT_MEMORY_RECEIPT_V1",
            "minimum_physical_available_bytes": 4 * 1024**3,
            "minimum_effective_available_bytes": 4 * 1024**3,
            "fresh_per_invocation": True,
        },
        "competence_rule": {"name": "EXTERNALLY_FROZEN_TEST_RULE", "threshold": 0.25},
        "reassociation_rule": {"name": "EXTERNALLY_FROZEN_TEST_CUT"},
        "raw_value_rule": {"name": "EXTERNALLY_FROZEN_TEST_RAW_VALUE"},
        "budget": {
            "wall_seconds": 10,
            "peak_rss_bytes": 20,
            "scratch_peak_bytes": 30,
            "durable_peak_bytes": 40,
            "read_bytes": 50,
            "write_bytes": 60,
            "transitions": 70,
            "optimizer_updates": 80,
            "evaluations": 90,
        },
        "performance_disposition": "REPAIR_REQUIRED",
        "performance_reason": "TEST_ONLY has no measured production path",
        "run_root": str(tmp_path / "b-run"),
    }


def _telemetry(scale: int = 1) -> dict[str, object]:
    return {
        "wall_seconds": float(scale),
        "cpu_seconds": float(scale) / 2.0,
        "cpu_occupancy_fraction": 0.5,
        "peak_rss_bytes": 100 * scale,
        "scratch_peak_bytes": 10 * scale,
        "durable_peak_bytes": 20 * scale,
        "read_bytes": 30 * scale,
        "write_bytes": 40 * scale,
        "worker_peak": 1,
        "sample_count": 2,
    }


def _curve(spec) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for arm, seed, checkpoint, cell_id in spec.expected_coordinates():
        rows.append(
            {
                "arm_id": arm,
                "seed_id": seed,
                "checkpoint": checkpoint,
                "cell_id": cell_id,
                "transitions": checkpoint * 100,
                "optimizer_updates": checkpoint,
                "evaluations": 4,
                "native_return": float(checkpoint),
                "projection_contact": {"observed": True, "count": 0, "opportunities": checkpoint},
                "edge_competence": {"observed": True, "value": 0.5, "passed": True},
                "reassociation": {"observed": True, "native_return": float(checkpoint) - 0.1},
                "raw_value_control": {"observed": True, "value": 0.75, "passed": True},
                "work_exposure": {
                    "information_items": checkpoint * 10,
                    "parameter_count": 123,
                    "parameter_bytes": 492,
                    "optimizer_updates": checkpoint,
                    "environment_interactions": checkpoint * 100,
                    "evaluations": 4,
                    "tuning_opportunities": 0,
                    "static_flops": {"observed": True, "value": checkpoint * 1000},
                    "workers": 1,
                    "threads": 1,
                },
                "telemetry": _telemetry(checkpoint),
                "validity": {"valid": True, "issues": []},
            }
        )
    inventory = [
        {"invocation_id": f"INV-{seed}", "seed_id": seed, "phase": "TEST_ONLY_TRAIN_EVAL"}
        for seed in spec.seeds
    ]
    receipts = [
        {
            "invocation_id": row["invocation_id"],
            "receipt_path": str(spec.run_root.parent / "receipts" / f"{row['invocation_id']}.json"),
            "receipt_schema": spec.resource_admission_rule["receipt_schema"],
            "physical_available_bytes": 5 * 1024**3,
            "effective_available_bytes": 5 * 1024**3,
            "fresh": True,
            "passed": True,
        }
        for row in inventory
    ]
    return {
        "schema": B_CURVE_SCHEMA,
        "complete": True,
        "study_id": spec.study_id,
        "claim_ceiling": spec.claim_ceiling,
        "rows": rows,
        "stage_telemetry": [{"stage_id": "TRAIN", "telemetry": _telemetry()}],
        "end_to_end_telemetry": _telemetry(2),
        "invocation_inventory": inventory,
        "invocation_receipts": receipts,
        "validity": {"valid": True, "issues": []},
        "observations": {"note": "TEST_ONLY direct observations; no scientific interpretation"},
    }


def _publishable_spec(tmp_path: Path):
    value = _spec_value(tmp_path)
    value["performance_disposition"] = "PILOT_ONLY"
    value["performance_reason"] = "TEST_ONLY bounded pilot evidence"
    return validate_explore_spec(value)


def test_b_spec_supplies_no_scientific_defaults_and_firewalls_c_schemas(tmp_path: Path) -> None:
    value = _spec_value(tmp_path)
    spec = validate_explore_spec(value)
    assert spec.seeds == ("SEED-A", "SEED-B")
    assert spec.checkpoints == (3, 7)
    assert tuple(cell.roster for cell in spec.cells) == (5, 8)
    assert spec.performance_disposition == "REPAIR_REQUIRED"

    c_schema = dict(value, schema="FRRIE_MANIFEST_V2")
    with pytest.raises(ExploreContractError, match="independent B schema"):
        validate_explore_spec(c_schema)
    missing = dict(value)
    missing.pop("checkpoints")
    with pytest.raises(ExploreContractError, match="fields must be exactly"):
        validate_explore_spec(missing)
    no_disposition = dict(value, performance_disposition="")
    with pytest.raises(ExploreContractError, match="performance_disposition"):
        validate_explore_spec(no_disposition)
    fractional_count = dict(value, budget=dict(value["budget"], transitions=1.5))
    with pytest.raises(ExploreContractError, match="budget.transitions"):
        validate_explore_spec(fractional_count)
    with_baseline = dict(value, checkpoints=[0, 7])
    assert validate_explore_spec(with_baseline).checkpoints == (0, 7)
    negative_checkpoint = dict(value, checkpoints=[-1, 7])
    with pytest.raises(ExploreContractError, match="checkpoint must be a nonnegative integer"):
        validate_explore_spec(negative_checkpoint)
    no_adaptation_record = dict(value, adaptation_record={})
    with pytest.raises(ExploreContractError, match="adaptation_record"):
        validate_explore_spec(no_adaptation_record)


def test_b_module_is_not_absorbed_into_frozen_c_source_inventory() -> None:
    inventory = _actual_package_source_inventory()
    assert "explore_infrastructure.py" not in inventory
    assert not any(path.startswith("b01/") for path in inventory)


def test_paired_curve_requires_complete_ordered_cross_product_and_matched_work(tmp_path: Path) -> None:
    spec = validate_explore_spec(_spec_value(tmp_path))
    curve = _curve(spec)
    validated = validate_paired_curve(curve, spec)
    assert len(validated["rows"]) == 16

    partial = dict(curve, rows=list(curve["rows"])[:-1])
    with pytest.raises(ExploreContractError, match="partial, duplicated, extra"):
        validate_paired_curve(partial, spec)

    mismatched = dict(curve, rows=[
        dict(row, work_exposure=dict(row["work_exposure"])) for row in curve["rows"]
    ])
    mismatched["rows"][8]["transitions"] += 1
    mismatched["rows"][8]["work_exposure"]["environment_interactions"] += 1
    with pytest.raises(ExploreContractError, match="paired work differs"):
        validate_paired_curve(mismatched, spec)

    exposure_mismatch = dict(curve, rows=[dict(row) for row in curve["rows"]])
    exposure_mismatch["rows"] = [dict(row, work_exposure=dict(row["work_exposure"])) for row in curve["rows"]]
    exposure_mismatch["rows"][8]["work_exposure"]["parameter_bytes"] += 4
    with pytest.raises(ExploreContractError, match="paired work differs"):
        validate_paired_curve(exposure_mismatch, spec)


def test_missing_observation_is_invalid_even_when_validity_claims_true(tmp_path: Path) -> None:
    spec = validate_explore_spec(_spec_value(tmp_path))
    curve = _curve(spec)
    curve["rows"][0]["projection_contact"] = {
        "observed": False,
        "count": 0,
        "opportunities": 1,
    }
    with pytest.raises(ExploreContractError, match="projection contact must be directly observed"):
        validate_paired_curve(curve, spec)


def test_invocation_receipts_exactly_cover_fresh_memory_admissions(tmp_path: Path) -> None:
    spec = validate_explore_spec(_spec_value(tmp_path))
    curve = _curve(spec)
    missing = dict(curve, invocation_receipts=curve["invocation_receipts"][:-1])
    with pytest.raises(ExploreContractError, match="exactly cover"):
        validate_paired_curve(missing, spec)

    failed = dict(
        curve,
        invocation_receipts=[dict(row) for row in curve["invocation_receipts"]],
    )
    failed["invocation_receipts"][0]["effective_available_bytes"] = 4 * 1024**3 - 1
    failed["invocation_receipts"][0]["passed"] = False
    with pytest.raises(ExploreContractError, match="fresh passing memory receipt"):
        validate_paired_curve(failed, spec)

    duplicate = dict(
        curve,
        invocation_receipts=[dict(row) for row in curve["invocation_receipts"]],
    )
    duplicate["invocation_receipts"][1]["receipt_path"] = duplicate["invocation_receipts"][0]["receipt_path"]
    with pytest.raises(ExploreContractError, match="unique fresh receipt path"):
        validate_paired_curve(duplicate, spec)


def test_namespace_is_create_once_and_incomplete_curve_is_quarantined(tmp_path: Path) -> None:
    spec = _publishable_spec(tmp_path)
    namespace = claim_explore_namespace(spec)
    assert namespace.result.is_dir() and namespace.quarantine.is_dir()
    with pytest.raises(ExplorePublicationError, match="already exists"):
        claim_explore_namespace(spec)

    curve = _curve(spec)
    curve["rows"] = curve["rows"][:-1]
    with pytest.raises(ExploreContractError, match="partial, duplicated, extra"):
        finalize_paired_curve(namespace, curve, spec)
    quarantine = namespace.quarantine / "incomplete_curve.json"
    assert json.loads(quarantine.read_text(encoding="ascii"))["schema"] == B_QUARANTINE_SCHEMA
    assert not (namespace.result / "paired_curve.json").exists()


def test_complete_curve_publishes_once_without_quarantine(tmp_path: Path) -> None:
    spec = _publishable_spec(tmp_path)
    namespace = claim_explore_namespace(spec)
    target = finalize_paired_curve(namespace, _curve(spec), spec)
    assert target == namespace.result / "paired_curve.json"
    assert json.loads(target.read_text(encoding="ascii"))["complete"] is True
    assert not (namespace.quarantine / "incomplete_curve.json").exists()
    with pytest.raises(ExplorePublicationError, match="already exists"):
        finalize_paired_curve(namespace, _curve(spec), spec)


def test_repair_required_disposition_withholds_result_and_quarantines(tmp_path: Path) -> None:
    spec = validate_explore_spec(_spec_value(tmp_path))
    namespace = claim_explore_namespace(spec)
    with pytest.raises(ExploreContractError, match="REPAIR_REQUIRED"):
        finalize_paired_curve(namespace, _curve(spec), spec)
    assert (namespace.quarantine / "incomplete_curve.json").is_file()
    assert not (namespace.result / "paired_curve.json").exists()


def test_process_tree_monitor_records_stage_and_end_to_end_peaks(tmp_path: Path) -> None:
    samples = [
        ProcessTreeSample(10.0, 100, 2.0, 20, 30, 1, 4, 5),
        ProcessTreeSample(11.0, 250, 2.5, 25, 50, 2, 8, 12),
        ProcessTreeSample(12.0, 200, 3.0, 40, 70, 1, 7, 11),
    ]
    cursor = 0

    def fake_sampler(_scratch: Path, _durable: Path) -> ProcessTreeSample:
        nonlocal cursor
        sample = samples[min(cursor, len(samples) - 1)]
        cursor += 1
        return sample

    monitor = ProcessTreePeakMonitor(
        scratch_root=tmp_path / "scratch",
        durable_root=tmp_path / "durable",
        interval_seconds=0.01,
        sampler=fake_sampler,
    )
    monitor.set_stage("TRAIN")
    monitor.start()
    time.sleep(0.015)
    monitor.set_stage("EVALUATE")
    report = monitor.stop()
    assert report["schema"] == B_TELEMETRY_SCHEMA
    assert report["end_to_end"]["peak_rss_bytes"] == 250
    assert report["end_to_end"]["scratch_peak_bytes"] == 8
    assert report["end_to_end"]["durable_peak_bytes"] == 12
    assert report["end_to_end"]["read_bytes"] == 20
    assert report["end_to_end"]["write_bytes"] == 40
    assert [row["stage_id"] for row in report["stages"]] == ["TRAIN", "EVALUATE"]


def test_recursive_byte_census_is_direct_and_missing_is_zero(tmp_path: Path) -> None:
    assert recursive_byte_census(tmp_path / "absent") == 0
    root = tmp_path / "scratch"
    (root / "nested").mkdir(parents=True)
    (root / "a.bin").write_bytes(b"abc")
    (root / "nested" / "b.bin").write_bytes(b"12345")
    assert recursive_byte_census(root) == 8
