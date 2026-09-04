"""Focused exact-semantic and publication tests for ACVC certificate R02."""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

import experiments.candidates.acvc.history_headroom_certificate_r02.experiment as experiment

from experiments.candidates.acvc.history_headroom_certificate_r02.experiment import (
    ACTIONS,
    AGES,
    CALIBRATED,
    CONFIDENCES,
    EXECUTE,
    HORIZON,
    PROBE,
    REGIMES,
    UNINFORMATIVE,
    VETO,
    action_values,
    apply_result_rule,
    current_unsafe_probability,
    det_cf_action,
    det_cf_probability,
    encoded,
    enumerate_anchor_mass,
    evaluate_det_cf,
    evaluate_lower,
    likelihood,
    marginal_verdict,
    oracle_cells,
    posterior_anchor,
    solve_upper,
    synthetic_cells,
)


def fraction(record: dict[str, object]) -> Fraction:
    return Fraction(int(record["numerator"]), int(record["denominator"]))


@pytest.fixture(scope="module")
def policy_results() -> tuple[dict[str, object], dict[str, object]]:
    return evaluate_det_cf(), evaluate_lower()


def test_exact_likelihood_and_host_normalization() -> None:
    assert likelihood(CALIBRATED, 1, 1, Fraction(7, 10), 0) == Fraction(21, 250)
    for regime in REGIMES:
        for confidence in CONFIDENCES:
            for age in AGES:
                assert sum(
                    likelihood(regime, verdict, unsafe, confidence, age)
                    for verdict in (0, 1) for unsafe in (0, 1)
                ) == 1
                assert all(
                    isinstance(likelihood(regime, verdict, unsafe, confidence, age), Fraction)
                    for verdict in (0, 1) for unsafe in (0, 1)
                )


def test_veto_anchor_uses_frame_only_and_never_truth() -> None:
    for verdict in (0, 1):
        for confidence in CONFIDENCES:
            anchors = {
                posterior_anchor(verdict, confidence, age, None) for age in AGES
            }
            assert len(anchors) == 1
            expected = marginal_verdict(CALIBRATED, verdict, confidence) / (
                marginal_verdict(CALIBRATED, verdict, confidence)
                + marginal_verdict(UNINFORMATIVE, verdict, confidence)
            )
            assert anchors == {expected}
    assert posterior_anchor(1, Fraction(9, 10), 0, 0) != posterior_anchor(
        1, Fraction(9, 10), 0, 1,
    )


def test_det_cf_exact_parity_with_frozen_formula() -> None:
    prior = Fraction(3, 25)
    for verdict in (0, 1):
        for confidence in CONFIDENCES:
            accuracy = (confidence + Fraction(1, 2)) / 2
            numerator = prior * (accuracy if verdict else 1 - accuracy)
            denominator = numerator + (1 - prior) * (
                1 - accuracy if verdict else accuracy
            )
            p_issue = numerator / denominator
            for age in AGES:
                expected = Fraction(1, 2) + (
                    p_issue - Fraction(1, 2)
                ) * Fraction(4, 5) ** age
                assert det_cf_probability(verdict, confidence, age) == expected
                values = action_values(expected)
                assert det_cf_action(verdict, confidence, age) == ACTIONS[
                    max(range(3), key=lambda index: values[index])
                ]


def test_lower_anchor_is_first_step_only_and_harm_normalizes(
    policy_results: tuple[dict[str, object], dict[str, object]],
) -> None:
    det, lower = policy_results
    assert len({anchor for _, anchor in enumerate_anchor_mass()}) == 24
    boundary = lower["information_boundary"]
    assert boundary == {
        "anchor_uses_only_first_opportunity": True,
        "later_frame_update_is_transient": True,
        "later_outcomes_change_anchor": False,
        "hidden_regime_used_for_action": False,
        "truth_inserted_after_veto": False,
    }
    for policy in (det, lower):
        assert sum(fraction(value) for value in policy["action_rates"].values()) == 1
        assert 0 <= fraction(policy["unsafe_execution_rate"]) <= 1
        assert 0 <= fraction(policy["clean_opportunity_loss"])
    assert fraction(lower["normalization"]["episode_opportunity_mass"]) == HORIZON
    assert fraction(lower["normalization"]["later_event_mass_per_opportunity"]) == 1
    assert lower["exact_lower_action_score_evaluations"] == 864


def test_upper_exact_primal_dual_and_coefficient_table() -> None:
    cells = synthetic_cells()[:4]
    caps = (
        sum(cell.weight * cell.unsafe[1] for cell in cells),
        sum(cell.weight * cell.clean_loss[1] for cell in cells),
    )
    certificate = solve_upper(cells, caps, time.perf_counter() + 30.0)
    assert len(certificate["coefficient_table"]) == 4
    assert certificate["primal"]["feasible"] is True
    assert certificate["dual"]["feasible"] is True
    assert certificate["complementary_slackness"]["all_zero"] is True
    assert certificate["equal_primal_dual_objective"] is True
    assert fraction(certificate["primal"]["objective"]) == fraction(
        certificate["dual"]["objective"]
    )
    assert all(
        fraction(row["normalization_residual"]) == 0
        for row in certificate["primal"]["rows"]
    )


def test_forced_det_advantage_and_lexicographic_witness(
    policy_results: tuple[dict[str, object], dict[str, object]],
) -> None:
    _, lower = policy_results
    rows = lower["disagreement"]["states"]
    assert rows
    for row in rows:
        history = row["first_opportunity_history"]
        context = row["later_current_context"]
        belief = fraction(history["anchor_belief"])
        p = current_unsafe_probability(
            belief, int(context["verdict"]), fraction(context["confidence"]), int(context["age"]),
        )
        expected = (
            action_values(p)[ACTIONS.index(row["lower_action"])]
            - action_values(p)[ACTIONS.index(row["forced_det_cf_action"])]
        )
        assert fraction(row["forced_det_cf_native_q_advantage"]) == expected > 0
    witness = lower["history_action_witness"]
    assert witness is not None
    assert witness["left_action"] != witness["right_action"]
    assert fraction(witness["left_positive_mass"]) > 0
    assert fraction(witness["right_positive_mass"]) > 0
    assert witness["selection_order"] == (
        "(left_visible_history,right_visible_history,current_context)"
    )


def test_dual_candidate_slots_each_evaluate_once(monkeypatch: pytest.MonkeyPatch) -> None:
    cells = synthetic_cells()[:2]
    caps = (
        sum(cell.weight * cell.unsafe[1] for cell in cells),
        sum(cell.weight * cell.clean_loss[1] for cell in cells),
    )
    calls = 0
    original = experiment._dual_value

    def counted(*args: object, **kwargs: object) -> Fraction:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(experiment, "_dual_value", counted)
    result = experiment.dual_candidate_search(cells, caps, time.perf_counter() + 10.0)
    assert calls == result["candidate_slots"]
    assert result["exact_action_score_evaluations"] == calls * len(cells) * 3


def test_ordered_branch_mapping_including_hc_c_precedence() -> None:
    common = {
        "disagreement_mass": Fraction(1, 10),
        "witness_exists": True,
        "aggregate_advantage": Fraction(1, 100),
    }
    assert apply_result_rule(
        delta_lower=Fraction(1, 4), delta_upper=Fraction(1, 2),
        lower_compatible=True, **common,
    )["branch"].startswith("HC-A")
    assert apply_result_rule(
        delta_lower=Fraction(1, 3), delta_upper=Fraction(1, 5),
        lower_compatible=False, **common,
    )["branch"].startswith("HC-C")
    assert apply_result_rule(
        delta_lower=Fraction(1, 3), delta_upper=Fraction(1, 2),
        lower_compatible=False, **common,
    )["branch"].startswith("HC-B")
    assert apply_result_rule(
        delta_lower=Fraction(1, 10), delta_upper=Fraction(1, 2),
        lower_compatible=True, **common,
    )["branch"].startswith("HC-D")
    assert apply_result_rule(
        delta_lower=Fraction(1, 3), delta_upper=Fraction(1, 2),
        lower_compatible=True, integrity_failures=("missing field",), **common,
    )["branch"].startswith("HC-X")


def test_reduced_result_blind_publication_smoke(tmp_path: Path) -> None:
    output = tmp_path / "publication"
    runner = Path(__file__).resolve().parents[5] / "scripts" / (
        "run_acvc_history_headroom_certificate_r02.py"
    )
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, str(runner), "smoke", "--output-root", str(output)],
        check=True, capture_output=True, text=True,
    )
    assert time.perf_counter() - started < 60.0
    response = json.loads(completed.stdout)
    assert response["result_blind"] is True
    summaries = list(output.glob("summary.json"))
    assert summaries == [output / "summary.json"]
    record = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert record["result_blind"] is True
    assert record["mocked_formal_publication"] is True
    assert record["result_bearing"] is False
    assert record["scientific_polarity"] is None
    assert record["static_work_counts"]["cells"] == 24
    assert record["static_work_counts"]["latent_first_step_atoms"] == 48
    assert record["static_work_counts"]["visible_anchors"] == 24
    assert record["static_work_counts"]["regimes"] == 2
    assert record["static_work_counts"]["episode_opportunities"] == 12
    assert record["static_work_counts"]["lower_action_score_evaluations"] == 864
    assert record["static_work_counts"]["history_pair_context_scans"] == 24 * 23 // 2 * 12
    assert record["static_work_counts"]["minimum_lower_input_numerator_bits"] >= 512
    assert record["static_work_counts"]["minimum_lower_input_denominator_bits"] >= 512
    assert record["static_work_counts"]["minimum_upper_input_numerator_bits"] >= 512
    assert record["static_work_counts"]["minimum_upper_input_denominator_bits"] >= 512


def valid_admission(path: Path) -> Path:
    path.write_text(json.dumps({
        "passed": True,
        "available_physical_bytes": 5 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
    }), encoding="utf-8")
    return path


def test_mocked_formal_success_pops_private_fractions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = valid_admission(tmp_path / "admission.json")
    det = {
        "_return": Fraction(1), "_unsafe_rate": Fraction(1, 10),
        "_clean_rate": Fraction(1, 5), "action_rates": {"A": encoded(Fraction(1))},
    }
    lower = {
        "_return": Fraction(2), "_unsafe_rate": Fraction(1, 10),
        "_clean_rate": Fraction(1, 5),
        "action_rates": {"A": encoded(Fraction(1))},
        "anchor_histories": [{} for _ in range(24)],
        "history_action_witness": {"synthetic": True},
        "exact_lower_action_score_evaluations": 864,
        "disagreement": {
            "opportunity_mass": encoded(Fraction(1, 10)),
            "probability_weighted_forced_det_cf_advantage": encoded(Fraction(1, 20)),
        },
    }
    monkeypatch.setattr(experiment, "evaluate_det_cf", lambda: dict(det))
    monkeypatch.setattr(experiment, "evaluate_lower", lambda: dict(lower))
    monkeypatch.setattr(experiment, "solve_upper", lambda *_args, **_kwargs: {
        "per_opportunity_objective": Fraction(1, 4),
        "primal": {"objective": encoded(Fraction(1, 4))},
        "dual": {"objective": encoded(Fraction(1, 4))},
    })
    monkeypatch.setattr(experiment, "probability_checks", lambda _cells: {
        "all_exactly_normalized": True,
    })
    monkeypatch.setattr(experiment, "_peak_rss_bytes", lambda: 1024)
    summary = experiment.run_result(
        tmp_path / "formal-mock", admission_receipt=receipt,
        launch_sha="exact-sha-from-runner", argv=("runner", "result"),
    )
    text = summary.read_text(encoding="utf-8")
    record = json.loads(text)
    assert record["launch_sha"] == "exact-sha-from-runner"
    assert record["static_work_counts"]["latent_first_step_atoms"] == 48
    assert record["resources"]["wall_seconds"] is not None
    assert record["resources"]["peak_rss_bytes"] == 1024
    assert record["learner_exposure"]["initialization_l2"] == "N/A"
    assert record["learner_exposure"]["parameter_displacement_l2"] == 0
    assert "_return" not in text
    assert "_unsafe_rate" not in text
    assert "_clean_rate" not in text

    monkeypatch.setattr(
        experiment, "evaluate_det_cf", lambda: {**det, "unexpected_fraction": Fraction(1, 7)},
    )
    serialization_root = tmp_path / "serialization-failure"
    with pytest.raises(TypeError):
        experiment.run_result(
            serialization_root, admission_receipt=receipt,
            launch_sha="exact-sha-serialization", argv=("runner", "result"),
        )
    assert not (serialization_root / "summary.json").exists()
    monkeypatch.setattr(experiment, "evaluate_det_cf", lambda: dict(det))

    ticks = iter((0.0, 121.0))
    monkeypatch.setattr(experiment.time, "perf_counter", lambda: next(ticks))
    capped = experiment.run_result(
        tmp_path / "formal-cap", admission_receipt=receipt,
        launch_sha="exact-sha-capped", argv=("runner", "result"),
    )
    capped_record = json.loads(capped.read_text(encoding="utf-8"))
    assert capped_record["result_rule"]["branch"].startswith("HC-X")
    assert capped_record["available_stage_counts"]["terminal_stage"] == "POST-PUBLICATION-CAP"
    assert capped_record["available_stage_counts"]["lower_action_score_evaluations"] == 864
    assert capped_record["static_work_counts"]["latent_first_step_atoms"] == 48
    assert capped_record["resources"]["wall_seconds"] == 121.0
    assert capped_record["scientific_polarity"] is None


def test_formal_exception_and_admission_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    refused = tmp_path / "refused.json"
    refused.write_text(json.dumps({"passed": False}), encoding="utf-8")
    refused_root = tmp_path / "refused-root"
    with pytest.raises(RuntimeError, match="admission"):
        experiment.run_result(
            refused_root, admission_receipt=refused,
            launch_sha="sha-refused", argv=("runner",),
        )
    assert not refused_root.exists()

    receipt = valid_admission(tmp_path / "admission.json")
    monkeypatch.setattr(
        experiment, "evaluate_det_cf",
        lambda: (_ for _ in ()).throw(ArithmeticError("synthetic certificate failure")),
    )
    terminal = experiment.run_result(
        tmp_path / "expected", admission_receipt=receipt,
        launch_sha="sha-expected", argv=("runner",),
    )
    record = json.loads(terminal.read_text(encoding="utf-8"))
    assert record["complete"] is False
    assert record["result_rule"]["branch"].startswith("HC-X")
    assert record["scientific_polarity"] is None
    assert all(value is None for value in record["primary"].values())
    assert record["available_stage_counts"]["lower_action_score_evaluations"] is None
    assert record["static_work_counts"]["latent_first_step_atoms"] == 48
    assert record["learner_exposure"]["initialization_scale"] == "N/A"

    monkeypatch.setattr(
        experiment, "evaluate_det_cf",
        lambda: (_ for _ in ()).throw(TypeError("unexpected implementation failure")),
    )
    unexpected = tmp_path / "unexpected"
    with pytest.raises(TypeError, match="unexpected implementation failure"):
        experiment.run_result(
            unexpected, admission_receipt=receipt,
            launch_sha="sha-unexpected", argv=("runner",),
        )
    assert not (unexpected / "summary.json").exists()
