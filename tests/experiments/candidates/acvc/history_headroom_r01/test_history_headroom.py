"""Exact host, policy, publication, and result-rule tests for ACVC headroom R01."""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.acvc.history_headroom_r01 import experiment as EXP  # noqa: E402
from experiments.candidates.acvc.uncertain_delayed_veto_r01 import (  # noqa: E402
    experiment as PRIOR,
)


def passing_admission(path: Path) -> Path:
    path.write_text(json.dumps({
        "passed": True,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "available_physical_bytes": 8 * 1024 ** 3,
        "effective_available_bytes": 7 * 1024 ** 3,
        "assessed_at_utc": "2026-09-04T12:00:00Z",
    }), encoding="utf-8")
    return path


def test_exact_likelihoods_normalize_and_match_analytic_uninformative_case():
    for regime in EXP.REGIMES:
        for confidence in EXP.CONFIDENCES:
            for age in EXP.AGES:
                total = sum(
                    EXP.likelihood(regime, verdict, unsafe, confidence, age)
                    for verdict in (0, 1) for unsafe in (0, 1)
                )
                assert total == 1
                for verdict in (0, 1):
                    assert sum(
                        EXP.likelihood(regime, verdict, unsafe, confidence, age)
                        for unsafe in (0, 1)
                    ) == EXP.marginal_verdict(regime, verdict, confidence)
    assert EXP.marginal_verdict(EXP.UNINFORMATIVE, 0, Fraction(7, 10)) == Fraction(1, 2)
    assert EXP.marginal_verdict(EXP.UNINFORMATIVE, 1, Fraction(9, 10)) == Fraction(1, 2)
    assert EXP.likelihood(
        EXP.UNINFORMATIVE, 1, 1, Fraction(9, 10), 0,
    ) == Fraction(3, 50)


def test_bayes_recursion_one_step_and_exact_tie_order():
    solver = EXP.ExactSolver()
    belief = Fraction(1, 2)
    expected = Fraction(0)
    for confidence in EXP.CONFIDENCES:
        for age in EXP.AGES:
            for verdict in (0, 1):
                decision = solver.decision(1, belief, verdict, confidence, age)
                p_b = sum(
                    belief * EXP.marginal_verdict(EXP.CALIBRATED, verdict, confidence)
                    + (1 - belief) * EXP.marginal_verdict(
                        EXP.UNINFORMATIVE, verdict, confidence,
                    )
                    for _ in (0,)
                )
                expected += EXP.P_CONFIDENCE_AGE * p_b * max(decision.q_values)
    assert solver.value(0, belief) == 0
    assert solver.value(1, belief) == expected
    assert solver.value(1, belief) == EXP.evaluate_det_cf(1)["_expected_return"]
    assert EXP.ACTIONS[max(range(3), key=lambda index: (1, 1, 0)[index])] == EXP.EXECUTE


def test_veto_does_not_insert_truth_but_revealing_actions_do():
    solver = EXP.ExactSolver()
    decision = solver.decision(2, Fraction(4, 7), 1, Fraction(9, 10), 0)
    assert EXP.transition_belief(decision, EXP.VETO, 0) == decision.frame_belief
    assert EXP.transition_belief(decision, EXP.VETO, 1) == decision.frame_belief
    assert EXP.transition_belief(decision, EXP.PROBE, 0) == decision.reveal_beliefs[0]
    assert EXP.transition_belief(decision, EXP.EXECUTE, 1) == decision.reveal_beliefs[1]
    assert decision.reveal_beliefs[0] != decision.reveal_beliefs[1]


def test_det_cf_is_action_identical_to_unchanged_r01_comparator():
    verdicts = np.array([[False, True] * 6], dtype=bool)
    confidences = np.array([[0.7, 0.7, 0.7, 0.7, 0.7, 0.7,
                             0.9, 0.9, 0.9, 0.9, 0.9, 0.9]], dtype=np.float32)
    ages = np.array([[0, 0, 1, 1, 2, 2] * 2], dtype=np.int8)
    blueprints = PRIOR.Blueprints(
        calibrated=np.array([True]),
        issuance_unsafe=np.zeros((1, 12), dtype=bool),
        current_unsafe=np.zeros((1, 12), dtype=bool),
        confidence=confidences,
        age=ages,
        verdict=verdicts,
    )
    prior_actions = PRIOR.det_cf_actions(blueprints)[0].tolist()
    exact_actions = [
        EXP.ACTIONS.index(EXP.det_cf_action(
            int(verdicts[0, index]),
            Fraction(str(float(confidences[0, index]))).limit_denominator(10),
            int(ages[0, index]),
        ))
        for index in range(12)
    ]
    assert exact_actions == prior_actions


@pytest.mark.parametrize((
    "delta", "disagreement", "treatment_unsafe", "treatment_clean", "branch",
), [
    (Fraction(1, 4), Fraction(1, 100), Fraction(3, 50), Fraction(1, 5),
     "HR-A / MATERIAL_COMPATIBLE_HEADROOM"),
    (Fraction(1, 4), Fraction(1, 100), Fraction(61, 1000), Fraction(1, 5),
     "HR-B / MATERIAL_HEADROOM_ONLY_WITH_HARM_TRADEOFF"),
    (Fraction(1, 10), Fraction(1, 100), Fraction(0), Fraction(0),
     "HR-C / SUBMATERIAL_HEADROOM"),
    (Fraction(99, 1000), Fraction(1, 100), Fraction(0), Fraction(0),
     "HR-D / NO_ACTIONABLE_HEADROOM"),
    (Fraction(1), Fraction(0), Fraction(0), Fraction(0),
     "HR-D / NO_ACTIONABLE_HEADROOM"),
])
def test_ordered_result_boundaries(
    delta, disagreement, treatment_unsafe, treatment_clean, branch,
):
    result = EXP.apply_result_rule(
        delta=delta,
        disagreement_mass=disagreement,
        treatment_unsafe=treatment_unsafe,
        det_unsafe=Fraction(1, 25),
        treatment_clean_loss=treatment_clean,
        det_clean_loss=Fraction(3, 20),
    )
    assert result["branch"] == branch


def test_integrity_and_cap_failure_precede_scientific_branches():
    assert EXP.resource_integrity_failures(120.0, EXP.RSS_CAP_BYTES) == ()
    assert EXP.resource_integrity_failures(120.01, None) == (
        "wall time exceeded 120 seconds",
    )
    assert EXP.resource_integrity_failures(1.0, EXP.RSS_CAP_BYTES + 1) == (
        "peak RSS exceeded 1.5 GiB",
    )
    result = EXP.apply_result_rule(
        delta=Fraction(1), disagreement_mass=Fraction(1),
        treatment_unsafe=Fraction(0), det_unsafe=Fraction(0),
        treatment_clean_loss=Fraction(0), det_clean_loss=Fraction(0),
        integrity_failures=("wall time exceeded 120 seconds",),
    )
    assert result["branch"] == "HR-X / NO_OBSERVATION"
    below = EXP.apply_result_rule(
        delta=Fraction(-1, 100), disagreement_mass=Fraction(1),
        treatment_unsafe=Fraction(0), det_unsafe=Fraction(0),
        treatment_clean_loss=Fraction(0), det_clean_loss=Fraction(0),
    )
    assert below["branch"] == "HR-X / NO_OBSERVATION"


@pytest.mark.parametrize("field", [
    "passed", "physical_floor_pass", "effective_floor_pass",
    "available_physical_bytes", "effective_available_bytes",
])
def test_admission_refusal_happens_before_output_creation(tmp_path, field):
    receipt = tmp_path / "admission.json"
    record = {
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
        "available_physical_bytes": 8 * 1024 ** 3,
        "effective_available_bytes": 8 * 1024 ** 3,
    }
    record[field] = False if "pass" in field or field == "passed" else 1024
    receipt.write_text(json.dumps(record), encoding="utf-8")
    output = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="4 GiB"):
        EXP.run_object(output, admission_receipt=receipt, toy=True)
    assert not output.exists()


def test_reduced_horizon_toy_publication_is_non_result_bearing(tmp_path):
    receipt = passing_admission(tmp_path / "admission.json")
    output = tmp_path / "run"
    started = time.perf_counter()
    completed = subprocess.run([
        sys.executable, str(PROJECT_ROOT / "scripts/run_acvc_history_headroom_r01.py"),
        "--output-root", str(output), "--admission-receipt", str(receipt), "--toy",
    ], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True, timeout=60)
    elapsed = time.perf_counter() - started
    record = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert elapsed < 60
    assert json.loads(completed.stdout)["summary"] == str(output / "summary.json")
    assert record["technical_only"] is True and record["toy"] is True
    assert record["result_bearing"] is False and record["complete"] is False
    assert record["evidence_class"] is None and record["result_rule"] is None
    assert record["horizon"] == EXP.TOY_HORIZON
    assert record["primary"]["J_H"]["denominator"] > 0
    assert record["primary"]["J_D"]["denominator"] > 0
    assert record["bellman"]["exact_complete_policy_recursion"] is True
    assert record["bellman"]["approximate_pruning"] is False
    assert all(
        row["start_mass"]["numerator"] == row["start_mass"]["denominator"]
        for row in record["policies"]["HIST-BAYES-DP"]["forward_probability_normalization"]
    )
    assert record["information_boundary"]["truth_inserted_after_veto"] is False
    history = record["policies"]["HIST-BAYES-DP"]
    assert (history["history_action_witness"] is None) != (
        history["no_witness_certificate"] is None
    )
    assert record["cost_law"]["measured_work_units"] > 0
    assert record["resources"]["wall_seconds"] > 0
