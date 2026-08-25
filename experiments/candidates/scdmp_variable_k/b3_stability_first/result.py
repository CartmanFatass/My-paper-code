from __future__ import annotations

import copy
import math

from .config import (
    ADAM, ALGORITHM_SEEDS, ARMS, BATCH_NAMESPACE_BASE, CALIBRATION_DOSE,
    CALIBRATION_MIN_RATIO, CANDIDATE, CORPUS_NAMESPACE_BASE,
    INITIALIZATION_NAMESPACE_BASE, MICROSTEP_LEDGER, MICROSTEP_TOTAL,
    NUMPY_VERSION, OPTIMIZER_UPDATES, ORDERED_PARAMETER_NAMES, REVISION,
    SCORED_NAMESPACE_BASE, TORCH_VERSION,
)
from .lifecycle import Lifecycle


def _validate_calibration_table(calibrations: list[dict[str, object]]) -> None:
    expected_cells = [(seed, arm) for seed in ALGORITHM_SEEDS for arm in ARMS]
    observed_cells = [(int(row["algorithm_seed"]), str(row["arm"])) for row in calibrations]
    if observed_cells != expected_cells:
        raise RuntimeError("result requires the ordered complete 24-cell calibration table")


def frozen_treatment_configuration() -> dict[str, object]:
    return {"candidate": CANDIDATE, "revision": REVISION,
            "algorithm_seeds": list(ALGORITHM_SEEDS), "arm_order": list(ARMS),
            "training_schedule": {"major_axis": "update", "updates": OPTIMIZER_UPDATES,
                                  "arm_order": list(ARMS)},
            "calibration_rule": {"dose": CALIBRATION_DOSE,
                                 "minimum_auxiliary_to_endpoint_ratio": CALIBRATION_MIN_RATIO,
                                 "coefficient_immutable_after_update_zero": True},
            "optimizer": copy.deepcopy(ADAM),
            "ordered_parameter_names": list(ORDERED_PARAMETER_NAMES),
            "versions": {"numpy": NUMPY_VERSION, "torch": TORCH_VERSION},
            "rng_namespace_bases": {"initialization": INITIALIZATION_NAMESPACE_BASE,
                "batch_order": BATCH_NAMESPACE_BASE, "corpus_resets": CORPUS_NAMESPACE_BASE,
                "scored_regimes": SCORED_NAMESPACE_BASE}}


def invalid_calibration_packet(lifecycle: Lifecycle, *, static: dict[str, object],
                               coordinate_manifest: dict[str, object],
                               calibrations: list[dict[str, object]],
                               resources: dict[str, object], frontier_path: str,
                               activity_sidecar: str,
                               anomalies: list[dict[str, object]]) -> dict[str, object]:
    _validate_calibration_table(calibrations)
    retained = copy.deepcopy(calibrations)
    for row in retained:
        row["finite_facts"] = {
            name: isinstance(row.get(name), (int, float)) and math.isfinite(float(row[name]))
            for name in ("B_s", "T_s", "A_s_m_cal", "lambda_s_m")
        }
    invalid = [row for row in retained if not bool(row["calibration_valid"])]
    if not invalid:
        raise RuntimeError("invalid-calibration discriminator requires at least one invalid cell")
    lifecycle.complete_invalid_calibration(len(invalid))
    terminal_anomaly = {"kind": "invalid_update_zero_calibration",
        "invalid_cell_count": len(invalid), "training_invoked": False,
        "evaluation_invoked": False, "repair_or_substitution_invoked": False}
    return {"artifact_kind": "SCDMP_B3_INVALID_CALIBRATION_DISCRIMINATOR",
            "candidate": CANDIDATE, "revision": REVISION, "complete": True,
            "scientific_activity_started": lifecycle.scientific_activity_started,
            "question_relevant_output_exists": True,
            "partial_selection_permitted": False,
            "discriminator": "complete_24_cell_update_zero_calibration_invalid",
            "lifecycle": lifecycle.facts(), "static_conformance": static,
            "frozen_treatment_configuration": frozen_treatment_configuration(),
            "fresh_coordinate_manifest": coordinate_manifest,
            "calibration_table": retained,
            "invalid_cells": invalid,
            "configuration_and_activity_facts": {
                "calibration_cells_attempted": len(retained),
                "training_invoked": False, "evaluation_invoked": False,
                "repair_reseed_substitution_invoked": False,
            },
            "training": None, "checkpoints": None, "support_panels": None,
            "audit_panels": None, "scored_panels": None, "inference": None,
            "adverse_inference": None, "null_inference": None,
            "scientific_interpretation": None,
            "interpretation_owner": "EM_semigroup_consistent_duration_model_policy",
            "resources": resources, "retained_frontier": frontier_path,
            "activity_sidecar": activity_sidecar,
            "anomalies": [*copy.deepcopy(anomalies), terminal_anomaly]}


def complete_packet(lifecycle: Lifecycle, *, static: dict[str, object],
                    coordinate_manifest: dict[str, object], calibrations: list[dict[str, object]],
                    seeds: list[dict[str, object]], inference: dict[str, object],
                    resources: dict[str, object], ledger: dict[str, int],
                    frontier_path: str, activity_sidecar: str,
                    anomalies: list[dict[str, object]]) -> dict[str, object]:
    _validate_calibration_table(calibrations)
    if [int(packet["algorithm_seed"]) for packet in seeds] != list(ALGORITHM_SEEDS):
        raise RuntimeError("complete packet requires all eight B3 seeds in order")
    for packet in seeds:
        if set(packet["checkpoints"]) != set(ARMS):
            raise RuntimeError("complete packet requires all three final checkpoints per seed")
        for arm in ARMS:
            trace = packet["training"]["gradient_trace"][arm]
            if len(trace) != OPTIMIZER_UPDATES:
                raise RuntimeError("complete packet requires every 1,000-update trace")
    if ledger != MICROSTEP_LEDGER or sum(ledger.values()) != MICROSTEP_TOTAL:
        raise RuntimeError("complete packet requires exact analytic ledger counts")
    lifecycle.complete()
    return {"artifact_kind": "SCDMP_B3_COMPLETE_ATOMIC_RESULT",
            "candidate": CANDIDATE, "revision": REVISION, "complete": True,
            "scientific_activity_started": True,
            "question_relevant_output_exists": True,
            "partial_selection_permitted": False,
            "scientific_interpretation": None,
            "interpretation_owner": "EM_semigroup_consistent_duration_model_policy",
            "lifecycle": lifecycle.facts(), "static_conformance": static,
            "frozen_treatment_configuration": frozen_treatment_configuration(),
            "fresh_coordinate_manifest": coordinate_manifest,
            "calibration_table": calibrations, "seeds": seeds,
            "inference": inference, "resources": resources,
            "analytic_environment_ledger": ledger,
            "retained_frontier": frontier_path, "activity_sidecar": activity_sidecar,
            "anomalies": anomalies}
