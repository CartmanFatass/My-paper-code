from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_contract import (
    CLAIM_SCHEDULES, REGIMES, SPEED_STRATA,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_e2b import (
    E2BAcceptanceError, TestCompleteDataPlane, TestRootLeaseBinding,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_full_panel import (
    FullPanelExecutor, STAGE_TOTALS,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_inference import (
    complete_branch_payload,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_lease import (
    ProductionLeaseError, load_root_lease,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_metrics import (
    FailureAtomicMetricStore, MetricStoreError, RawMetricRow, RecoveryWitnessRow,
    witness_support_metrics,
)


def _branch_row() -> dict[str, object]:
    common = {name: False for name in (
        "protocol_ok", "comp", "witness", "headroom", "precision", "support",
        "rule_fallback_i", "rule_fallback_h", "harm", "package_effect",
        "fork_excluded", "nm_all", "rulequal_i", "rulequal_h", "flexqual", "flex_rel", "core",
    )}
    return {**common, "anchors": {speed: dict(common) for speed in SPEED_STRATA}}


def test_complete_branch_payload_requires_every_cell_and_anchor() -> None:
    vectors = {(regime, schedule): _branch_row() for regime in REGIMES for schedule in CLAIM_SCHEDULES}
    payload = complete_branch_payload(vectors)
    assert payload["complete"] and payload["branch_count"] == 15
    vectors.pop(next(iter(vectors)))
    with pytest.raises(Exception, match="inventory"):
        complete_branch_payload(vectors)


def test_witness_support_rows_bind_dh_da_and_complete_denominators() -> None:
    rows = [RecoveryWitnessRow(0, regime, schedule, speed, 1, 1, 1, 0.001, 0.001)
            for regime in REGIMES for schedule in CLAIM_SCHEDULES for speed in SPEED_STRATA]
    metrics = witness_support_metrics(rows, arm="STRUCTURED")
    assert len(metrics) == 36 and set(metrics.values()) == {1.0}
    with pytest.raises(MetricStoreError, match="predicate"):
        RecoveryWitnessRow(0, REGIMES[0], CLAIM_SCHEDULES[0], SPEED_STRATA[0], 1, 1, 1, 0.0, 0.001).validate()


def test_metric_store_resume_is_idempotent_and_partial_values_are_refused(tmp_path: Path) -> None:
    binding = hashlib.sha256(b"TEST/R06/E2B/METRICS").hexdigest()
    row = RawMetricRow(0, ("FIXTURE", "COUNT"), 0.0)
    store = FailureAtomicMetricStore(tmp_path, binding_sha256=binding, test_only=True)
    first = store.append_shard("one", (row,))
    second = FailureAtomicMetricStore(tmp_path, binding_sha256=binding, test_only=True).append_shard("one", (row,))
    assert first == second
    with pytest.raises(MetricStoreError, match="incomplete"):
        store.complete_estimand_matrix()
    with pytest.raises(MetricStoreError, match="replacement"):
        store.append_shard("one", (RawMetricRow(0, ("FIXTURE", "COUNT"), 1.0),))


def test_production_lease_loader_fails_before_master_when_files_are_absent(tmp_path: Path) -> None:
    with pytest.raises(ProductionLeaseError, match="required"):
        load_root_lease(tmp_path, tmp_path / "lease.json", tmp_path / "request.json")


def test_native_batch_failure_does_not_advance_frontier_and_same_identity_resumes(tmp_path: Path) -> None:
    authority = TestRootLeaseBinding(); failing = TestCompleteDataPlane(tmp_path / "data", fail_once_at=("POPULATION", 0))
    executor = FullPanelExecutor(authority=authority, data_plane=failing, run_root=tmp_path / "run")
    with pytest.raises(E2BAcceptanceError, match="injected"):
        executor.run_slice(max_units=32)
    frontier = json.loads((tmp_path / "run" / "sealed_frontier.json").read_text())
    assert frontier["stage"] == "POPULATION" and frontier["stage_index"] == 0 and frontier["completed_units"] == 0
    resumed = FullPanelExecutor(authority=authority, data_plane=TestCompleteDataPlane(tmp_path / "data"), run_root=tmp_path / "run").run_slice(max_units=32)
    assert resumed["status"] == "SLICE_COMPLETE" and resumed["frontier"]["stage_index"] == 32
    assert resumed["frontier"]["identity_sha256"] == authority.identity_sha256


def test_end_to_end_complete_inventory_and_successor_slice_result_firewall(tmp_path: Path) -> None:
    authority = TestRootLeaseBinding(); plane = TestCompleteDataPlane(tmp_path / "data")
    run_root = tmp_path / "run"
    first = FullPanelExecutor(authority=authority, data_plane=plane, run_root=run_root).run_slice(max_units=STAGE_TOTALS["POPULATION"])
    assert first["status"] == "SLICE_COMPLETE" and first["frontier"]["stage"] == "TRAINING"
    remaining = sum(STAGE_TOTALS.values()) - STAGE_TOTALS["POPULATION"]
    second = FullPanelExecutor(authority=authority, data_plane=plane, run_root=run_root).run_slice(max_units=remaining)
    assert second["status"] == "COMPLETE" and second["frontier"]["completed_units"] == sum(STAGE_TOTALS.values())
    assert second["frontier"]["slice_generation"] == 1
    result = json.loads((run_root / "complete_result.json").read_text())
    assert result["complete"] and result["estimands"] == 6_990 and result["resamples"] == 99_999
    assert result["test_only"] and not result["question_relevant_output"]
