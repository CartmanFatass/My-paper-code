"""Result-blind local E2A acceptance for the integrated R06 data plane."""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import tempfile

from .production_backend import artifact_identity, flow_local_native_abi_self_audit
from .production_contract import CLAIM_SCHEDULES, REGIMES, SPEED_STRATA, TestAuthority, complete_inventory
from .production_data_plane import R06ProductionDataPlane
from .production_estimands import assemble_complete_block_rows
from .production_full_panel import FullPanelExecutor, production_surface_manifest
from .production_inference import BRANCHES, classify_atomic, complete_branch_payload, complete_estimand_manifest
from .production_lease import lease_loader_binding_manifest
from .production_metrics import (
    FailureAtomicMetricStore, MetricStoreError, RawMetricRow, RecoveryWitnessRow,
    required_block_metric_keys, witness_support_metrics,
)


class E2AAuditError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _all_false() -> dict[str, bool]:
    return {name: False for name in (
        "protocol_ok", "comp", "witness", "headroom", "precision", "support",
        "rule_fallback_i", "rule_fallback_h", "harm", "package_effect",
        "fork_excluded", "nm_all", "rulequal_i", "rulequal_h", "flexqual",
        "flex_rel", "core",
    )}


def _branch_fixture(branch: int) -> dict[str, bool]:
    row = _all_false(); row["headroom"] = True; row["precision"] = True
    if branch >= 2: row["protocol_ok"] = True
    if branch >= 3: row["comp"] = True
    if branch >= 4: row["witness"] = True
    if branch == 4: row["headroom"] = False; return row
    if branch >= 6: row["support"] = True
    if branch == 5: return row
    if branch == 6: row["harm"] = True
    elif branch == 7: row["package_effect"] = True
    elif branch == 8: row["fork_excluded"] = True
    elif branch == 9: row["rulequal_i"] = True
    elif branch == 10: row["rulequal_h"] = True
    elif branch == 11: row["flexqual"] = True
    elif branch == 12: row["flex_rel"] = True
    elif branch == 13: row["core"] = True
    elif branch == 14: row["nm_all"] = True
    return row


def run_e2a_local_self_audit(repository_root: Path) -> dict[str, object]:
    authority = TestAuthority(); authority.require_test_only()
    package = Path(__file__).parent
    native = artifact_identity(); native_audit = flow_local_native_abi_self_audit()

    # Persistence/resume is exercised on one synthetic, non-question-relevant
    # coordinate.  The incomplete store must refuse value exposure.
    binding = hashlib.sha256(b"TEST/DISH/RBHR/R06/E2A/METRIC-STORE").hexdigest()
    with tempfile.TemporaryDirectory(prefix="dish-r06-e2a-") as temporary:
        root = Path(temporary)
        store = FailureAtomicMetricStore(root, binding_sha256=binding, test_only=True)
        first = store.append_shard("fixture", (RawMetricRow(0, ("FIXTURE", "COUNT"), 0.0),))
        resumed = FailureAtomicMetricStore(root, binding_sha256=binding, test_only=True)
        duplicate = resumed.append_shard("fixture", (RawMetricRow(0, ("FIXTURE", "COUNT"), 0.0),))
        partial_refused = False
        try:
            resumed.complete_estimand_matrix()
        except MetricStoreError:
            partial_refused = True

    metrics = {key: 0.0 for key in required_block_metric_keys()}
    assembled = assemble_complete_block_rows(metrics)
    manifest = complete_estimand_manifest()
    if tuple(assembled) != manifest:
        raise E2AAuditError("raw metric to 6,990 ordering differs")

    witness_rows = tuple(
        RecoveryWitnessRow(0, regime, schedule, speed, 1, 1, 1, 1e-3, 1e-3)
        for regime in REGIMES for schedule in CLAIM_SCHEDULES for speed in SPEED_STRATA
    )
    witness = witness_support_metrics(witness_rows, arm="STRUCTURED")

    reached = {}
    for branch in range(1, 16):
        observed, label = classify_atomic(_branch_fixture(branch)); reached[str(branch)] = label
        if observed != branch:
            raise E2AAuditError(f"branch fixture {branch} reached {observed}")
    base = _branch_fixture(15)
    vectors = {
        (regime, schedule): {**base, "anchors": {speed: dict(base) for speed in SPEED_STRATA}}
        for regime in REGIMES for schedule in CLAIM_SCHEDULES
    }
    payload = complete_branch_payload(vectors)

    data_plane_source = inspect.getsource(R06ProductionDataPlane)
    executor_source = inspect.getsource(FullPanelExecutor)
    source_paths = tuple(package / name for name in (
        "production_data_plane.py", "production_lease.py", "production_full_panel.py",
        "production_metrics.py", "production_estimands.py", "production_inference.py",
        "production_backend.py", "production_recurrent_trainer.py", "production_evaluator.py",
        "production_real_sham.py",
    ))
    sources = {str(path.relative_to(repository_root)).replace("\\", "/"): _sha256(path) for path in source_paths}
    result = {
        "schema": "DISH_RBHR_R06_E2A_RESULT_BLIND_LOCAL_SELF_AUDIT_V1",
        "inventory": complete_inventory(),
        "surface_manifest": production_surface_manifest(),
        "lease_loader": lease_loader_binding_manifest(),
        "native": native, "native_local_audit": native_audit,
        "surface_checks": {
            "concrete_data_plane": all(name in data_plane_source for name in (
                "_population_batch", "_training_batch", "_evaluation_batch", "_fork_batch", "inference_unit")),
            "lease_loader_without_request": lease_loader_binding_manifest()["request_created"] is False,
            "failure_atomic_native_batch_orchestration": "_execute_batch" in executor_source and "native batch receipt inventory" in executor_source,
            "failure_atomic_metric_persistence_resume": first == duplicate and partial_refused,
            "raw_metric_to_6990": len(assembled) == 6_990,
            "complete_witness_support": len(witness) == 36,
            "dh_da_predicate": all(row.behavior_changing == 1 for row in witness_rows),
            "complete_15_branch_payload": payload["branch_count"] == 15 and len(reached) == 15 and set(reached.values()) == set(BRANCHES),
        },
        "branch_fixture_catalog": reached,
        "estimand_manifest_sha256": hashlib.sha256(("\n".join(manifest) + "\n").encode("ascii")).hexdigest(),
        "source_sha256": sources,
        "fixture_only": True, "result_blind": True, "partial_values_exposed": False,
        "lease_request_created": False, "lease_issued": False, "master_materialized": False,
        "identity_created": False, "coordinate_created": False, "tape_created": False,
        "model_created": False, "checkpoint_created": False, "training_activity": False,
        "evaluation_activity": False, "inference_activity": False,
        "question_relevant_output": False, "r05_action": False,
    }
    if not all(result["surface_checks"].values()):
        raise E2AAuditError("one or more E2A surface checks failed")
    return result


__all__ = ["E2AAuditError", "run_e2a_local_self_audit"]
