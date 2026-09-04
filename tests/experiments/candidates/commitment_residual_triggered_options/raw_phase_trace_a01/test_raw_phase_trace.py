from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

from experiments.candidates.commitment_residual_triggered_options.raw_phase_trace_a01 import experiment
from scripts import run_crto_raw_phase_trace_a01 as runner


def test_exact_panel_namespace_and_prospective_counts() -> None:
    rows = experiment.selected_population_spec()
    assert len(rows) == 64
    assert sum(row["split"] == "TRAIN" for row in rows) == 48
    assert sum(row["split"] == "EVAL" for row in rows) == 16
    assert sum(row["side"] == "KEEP" for row in rows) == 32
    assert sum(row["side"] == "REPLAN" for row in rows) == 32
    assert all(row["source_slot"] in range(8) for row in rows)
    assert all(832 <= row["episode_index"] <= 895 for row in rows)
    assert experiment.SOURCE_NAMESPACE == 2026083192
    assert experiment.LEARNER_NAMESPACE == 2026090401
    cost = experiment.project_cost()
    assert cost["fixed_planning_law"] == "3 * 434.7066687 = 1304.1200061 seconds"
    assert cost["projected_raw_trace_arm_seconds"] == 1304.1200061
    assert cost["projection_within_cap"] is True
    assert cost["prospective_work_counts"] == {
        "predictor_tapes": 128, "predictor_updates": 100,
        "predictor_batch_size": 128, "predictor_processed_examples": 12800,
        "raw_gate_updates": 264, "raw_gate_batch_size": 32,
        "raw_gate_processed_examples": 8448, "checkpoint_count": 13,
        "checkpoint_evaluation_rows": 208, "true_residual_updates": 0,
        "true_residual_evaluation_rows": 0, "calibrated_derangement_updates": 0,
        "calibrated_derangement_evaluation_rows": 0,
    }


def test_trace_exposure_phase_cursor_and_initial_anchor() -> None:
    cost = experiment.project_cost()
    assert cost["initialization_anchor"]["matches"] is True
    for name, expected in experiment.INITIAL_ANCHOR.items():
        assert math.isclose(
            cost["initialization_anchor"]["observed"][name], expected,
            rel_tol=1e-7, abs_tol=0.0,
        )
    lines = cost["prospective_exposure_lines"]
    assert [line["update"] for line in lines] == list(range(252, 265))
    assert [line["update_mod_3"] for line in lines] == [u % 3 for u in range(252, 265)]
    assert [line["post_update_cyclic_cursor"] for line in lines] == [
        (32 * u) % 48 for u in range(252, 265)
    ]
    assert [line["processed_examples"] for line in lines] == [32 * u for u in range(252, 265)]
    assert [line["nominal_lr_exposure"] for line in lines] == [0.001 * u for u in range(252, 265)]


def _anchor_metrics(*, keep_exact: int = 8,
                    replan_regret: float = 0.0066464623737892345) -> dict[str, object]:
    return {
        "sides": {
            "KEEP": {"exact_action_count": keep_exact, "mean_regret": 0.0},
            "REPLAN": {"exact_action_count": 4, "mean_regret": replan_regret},
        },
        "equal_side_regret": 0.5 * replan_regret,
    }


def test_update_256_anchor_checks_counts_and_absolute_tolerance() -> None:
    assert experiment.update_256_anchor_matches(_anchor_metrics())
    assert experiment.update_256_anchor_matches(
        _anchor_metrics(replan_regret=0.0066464623737892345 + 0.9e-12)
    )
    assert not experiment.update_256_anchor_matches(
        _anchor_metrics(replan_regret=0.0066464623737892345 + 2.1e-12)
    )
    assert not experiment.update_256_anchor_matches(_anchor_metrics(keep_exact=7))


def test_information_boundary_and_branch_precedence() -> None:
    report = experiment.information_boundary_report()
    assert experiment.information_boundary_is_valid(report)
    assert experiment.apply_result_rule(
        information_boundary_valid=True, completeness_issues=[],
    ) == "A01-RAW-PHASE-TRACE-MEASURED"
    assert experiment.apply_result_rule(
        information_boundary_valid=True, completeness_issues=["missing"],
    ) == "A01-RAW-PHASE-INCOMPLETE"
    assert experiment.apply_result_rule(
        information_boundary_valid=False, completeness_issues=["missing"],
    ) == "A01-RAW-PHASE-INFORMATION-BOUNDARY-INVALID"
    leaked = dict(report)
    leaked["eval_affects_raw_training"] = True
    assert not experiment.information_boundary_is_valid(leaked)
    exposed = dict(report)
    exposed["true_residual_gate_updates"] = 1
    assert not experiment.information_boundary_is_valid(exposed)


def test_trace_measurement_rule_rejects_illegal_or_negative_rows() -> None:
    row = {
        "legal_mask": [True, True, False, False, False, False, False, False],
        "raw_selected_action_index": 0, "legal_g16": {"KEEP": 0.2, "TRACK-L": 0.1},
        "native_regret": 0.0,
    }
    metrics = {str(update): {
        "rows": [dict(row) for _ in range(16)],
        "sides": {side: {"row_count": 8} for side in ("KEEP", "REPLAN")},
    } for update in experiment.TRACE_UPDATES}
    exposures = [{
        "update": update,
        "parameter_displacement_l2_over_initial_l2": 0.1,
        "parameter_displacement_linf_over_initial_linf": 0.1,
    } for update in experiment.TRACE_UPDATES]
    assert experiment.trace_measurement_issues(metrics, exposures) == []
    metrics["256"]["rows"][0]["raw_selected_action_index"] = 2
    assert experiment.trace_measurement_issues(metrics, exposures) == [
        "UPDATE_256_ILLEGAL_OR_NONFINITE_ROW_MEASUREMENT"
    ]


def test_toy_runner_end_to_end_under_60_seconds(tmp_path: Path, monkeypatch) -> None:
    constructed = 0
    original_gate = experiment.CommonHistoryGate

    def counting_gate(*args, **kwargs):
        nonlocal constructed
        constructed += 1
        return original_gate(*args, **kwargs)

    monkeypatch.setattr(experiment, "CommonHistoryGate", counting_gate)
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
        "available_physical_bytes": 8 * 1024**3,
        "effective_available_bytes": 8 * 1024**3,
        "assessed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }), encoding="utf-8")
    output = tmp_path / "run"
    assert runner.main([
        "run", "--seed", "0", "--admission-receipt", str(receipt),
        "--output-dir", str(output), "--execution-node", "local_windows", "--toy",
    ]) == 0
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["result_branch"] == "A01-RAW-PHASE-INCOMPLETE"
    assert summary["completeness_issues"] == ["TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION"]
    assert summary["representation"] == "RAW"
    assert summary["absent_representations"] == ["TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT"]
    assert summary["work_counts"]["true_residual_gate_updates"] == 0
    assert summary["work_counts"]["calibrated_derangement_evaluation_rows"] == 0
    assert list(summary["trace"]) == ["1", "2", "3"]
    assert all(len(checkpoint["rows"]) == 6 for checkpoint in summary["trace"].values())
    first_row = summary["trace"]["1"]["rows"][0]
    assert {"legal_mask", "legal_g16", "oracle_action", "oracle_g16",
            "raw_selected_action", "raw_selected_g16", "native_regret",
            "exact_action_correct"}.issubset(first_row)
    assert summary["information_boundary"]["evaluations_started_after_all_snapshots_created"]
    assert summary["resources"]["wall_seconds"] < 60.0
    assert constructed == 1
