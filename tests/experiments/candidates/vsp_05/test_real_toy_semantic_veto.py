from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.vsp_05.real_toy_semantic_veto import (
    ARMS,
    DET_ARM,
    HandoffDelayTracker,
    REGISTERED_CONFIG,
    SMOKE_CONFIG,
    _empty_counts,
    _record_selected_action,
    proposed_successor,
    run_experiment,
    write_result,
)
from experiments.candidates.vsp_05.semantic_veto_policy import (
    FEATURE_DIM,
    HARD_POSITION_THRESHOLD,
    HARD_VELOCITY_THRESHOLD,
    REJECT_THRESHOLD,
    TRUTH_POSITION_THRESHOLD,
    TRUTH_VELOCITY_THRESHOLD,
    classify_receipt,
    deterministic_sham_labels,
    select_semantic_action,
    semantic_feature,
    train_logistic_veto,
)


@pytest.fixture(scope="module")
def smoke_result():
    return run_experiment(SMOKE_CONFIG, code_revision="TEST")


def test_feature_is_exact_current_time_age_free_vector():
    value = semantic_feature(-0.5, 0.25, 1, 2)
    assert value.dtype == np.float32
    assert value.shape == (FEATURE_DIM,)
    assert value.tolist() == [-0.5, 0.25, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]


@pytest.mark.parametrize(
    "args,error",
    [
        ((np.nan, 0.0, 0, 1), ValueError),
        ((0.0, np.inf, 0, 1), ValueError),
        ((0.0, 0.0, True, 1), TypeError),
        ((0.0, 0.0, 0, 3), ValueError),
    ],
)
def test_feature_rejects_malformed_values(args, error):
    with pytest.raises(error):
        semantic_feature(*args)


def test_frozen_receipt_thresholds_are_symmetric_and_unresolved_is_explicit():
    assert HARD_POSITION_THRESHOLD == 1.0 / 8.0
    assert TRUTH_POSITION_THRESHOLD == 1.0 / 4.0
    assert HARD_VELOCITY_THRESHOLD == 1.0 / 4.0
    assert TRUTH_VELOCITY_THRESHOLD == 1.0 / 16.0

    negative_truth = classify_receipt(0, -TRUTH_POSITION_THRESHOLD, 1.0)
    positive_truth = classify_receipt(2, TRUTH_POSITION_THRESHOLD, -1.0)
    assert negative_truth == positive_truth
    assert negative_truth.gate and negative_truth.truth and negative_truth.label == 0

    negative_alias = classify_receipt(0, -HARD_POSITION_THRESHOLD, 1.0)
    positive_alias = classify_receipt(2, HARD_POSITION_THRESHOLD, -1.0)
    assert negative_alias == positive_alias
    assert negative_alias.gate and not negative_alias.truth and negative_alias.label == 1

    hold_truth = classify_receipt(1, 0.9, TRUTH_VELOCITY_THRESHOLD)
    hold_alias = classify_receipt(1, -0.9, HARD_VELOCITY_THRESHOLD)
    unresolved = classify_receipt(1, 0.0, HARD_VELOCITY_THRESHOLD + 1e-6)
    assert hold_truth.label == 0 and hold_alias.label == 1
    assert unresolved.label is None and not unresolved.gate


def test_gate_det_reject_and_abstain_actions_are_exact():
    gate_zero = classify_receipt(2, 0.0, 1.0)
    assert select_semantic_action(
        current_skill=0,
        proposed_skill=2,
        receipt=gate_zero,
        learned_veto=True,
        alias_probability=None,
    ).selected_skill == 0

    gate_one = classify_receipt(2, TRUTH_POSITION_THRESHOLD, 1.0)
    det = select_semantic_action(
        current_skill=0,
        proposed_skill=2,
        receipt=gate_one,
        learned_veto=False,
        alias_probability=None,
    )
    reject = select_semantic_action(
        current_skill=0,
        proposed_skill=2,
        receipt=gate_one,
        learned_veto=True,
        alias_probability=REJECT_THRESHOLD,
    )
    abstain = select_semantic_action(
        current_skill=0,
        proposed_skill=2,
        receipt=gate_one,
        learned_veto=True,
        alias_probability=REJECT_THRESHOLD - 1e-6,
    )
    assert (det.selected_skill, det.rejected) == (2, False)
    assert (reject.selected_skill, reject.rejected) == (0, True)
    assert (abstain.selected_skill, abstain.rejected) == (2, False)


def test_gate_zero_hold_is_not_counted_as_changed_or_premature():
    receipt = classify_receipt(2, 0.0, 1.0)
    decision = select_semantic_action(
        current_skill=0,
        proposed_skill=2,
        receipt=receipt,
        learned_veto=True,
        alias_probability=None,
    )
    counts = _empty_counts()
    _record_selected_action(
        counts, current_skill=0, receipt=receipt, decision=decision
    )
    assert counts["changed_actions"] == 0
    assert counts["premature_handoffs"] == 0
    assert counts["safe_holds"] == 0


def test_event_rank_delay_tracks_first_truth_and_censoring():
    truth = classify_receipt(2, TRUTH_POSITION_THRESHOLD, 1.0)
    tracker = HandoffDelayTracker.create()
    first = tracker.next_rank("owner")
    tracker.observe(
        lifecycle_key="owner",
        event_rank=first,
        current_skill=0,
        proposed_skill=2,
        receipt=truth,
        decision=select_semantic_action(
            current_skill=0,
            proposed_skill=2,
            receipt=truth,
            learned_veto=True,
            alias_probability=REJECT_THRESHOLD,
        ),
    )
    assert tracker.summary() == {
        "observed": 0,
        "censored": 1,
        "sum_event_ranks": 0,
        "mean_event_ranks": None,
    }
    second = tracker.next_rank("owner")
    tracker.observe(
        lifecycle_key="owner",
        event_rank=second,
        current_skill=0,
        proposed_skill=2,
        receipt=truth,
        decision=select_semantic_action(
            current_skill=0,
            proposed_skill=2,
            receipt=truth,
            learned_veto=True,
            alias_probability=0.0,
        ),
    )
    assert tracker.summary() == {
        "observed": 1,
        "censored": 0,
        "sum_event_ranks": 1,
        "mean_event_ranks": 1.0,
    }


def test_successor_rule_is_fixed_current_process_only():
    assert proposed_successor(position=0.0, velocity=0.0, current_skill=None) == 2
    assert proposed_successor(position=-0.5, velocity=0.8, current_skill=2) == 0
    assert proposed_successor(position=0.5, velocity=-0.8, current_skill=0) == 2
    assert proposed_successor(position=0.5, velocity=0.8, current_skill=2) == 0


def test_sham_permutation_is_deterministic_and_multiset_preserving():
    labels = [0, 1, 1, 0, 1, 0, 0]
    first = deterministic_sham_labels(labels, 12345)
    second = deterministic_sham_labels(labels, 12345)
    assert np.array_equal(first, second)
    assert sorted(first.tolist()) == sorted(labels)


def test_zero_support_trainer_keeps_finite_zero_model_and_exact_updates():
    model, diagnostics = train_logistic_veto(
        np.empty((0, FEATURE_DIM), dtype=np.float32),
        [],
        optimizer_steps=5,
    )
    assert diagnostics.records == 0
    assert diagnostics.positive_labels == 0
    assert diagnostics.optimizer_updates == 5
    assert diagnostics.initial_loss == 0.0
    assert diagnostics.final_loss == 0.0
    assert diagnostics.weight_l2 == 0.0
    assert diagnostics.bias == 0.0
    assert model.alias_probability(np.zeros(FEATURE_DIM, dtype=np.float32)) == 0.5


def test_registered_budget_formula_is_exact():
    assert REGISTERED_CONFIG.counts() == {
        "training_transitions": 7680,
        "evaluation_transitions": 23040,
        "total_transitions": 30720,
        "optimizer_updates": 768,
        "training_episodes": 96,
        "evaluated_episodes": 288,
    }


def test_smoke_run_uses_real_runtime_and_stays_inside_declared_counts(smoke_result):
    assert smoke_result["stage"] == "experiment"
    assert smoke_result["actual_counts"] == SMOKE_CONFIG.counts()
    assert smoke_result["actual_counts"]["total_transitions"] > 0
    assert smoke_result["actual_counts"]["optimizer_updates"] > 0
    assert smoke_result["actual_counts"]["evaluated_episodes"] > 0
    assert all(smoke_result["real_calls"].values())
    assert smoke_result["call_counts"]["trainer"] == 2
    assert smoke_result["call_counts"]["evaluation_runner"] == len(ARMS)
    assert smoke_result["call_counts"]["environment_transition"] == 640
    assert smoke_result["call_counts"]["supplied_executor"] == 640
    assert smoke_result["call_counts"]["variable_roster_event_core_transaction"] == 640
    assert all(
        row["collection"]["real_environment"]
        and row["collection"]["real_variable_roster_core"]
        and row["collection"]["real_supplied_executor"]
        for row in smoke_result["training"]
    )
    # Zero support is a valid fixed-budget result and is represented honestly.
    for arm in ARMS:
        rate = smoke_result["aggregates"][arm]["premature_handoff_rate"]
        assert rate["denominator"] == smoke_result["aggregates"][arm]["support"]["gated"]
        if rate["denominator"] == 0:
            assert rate["value"] is None


def test_smoke_json_is_reloadable_and_canonical(tmp_path, smoke_result):
    destination = tmp_path / "result.json"
    write_result(destination, smoke_result)
    loaded = json.loads(destination.read_text(encoding="utf-8"))
    assert loaded == smoke_result
    assert destination.read_text(encoding="utf-8").endswith("\n")


def test_candidate_has_no_production_import_or_prohibited_feature(tmp_path):
    del tmp_path
    root = Path(__file__).resolve().parents[4]
    production = root / "ha_ctse_process"
    needle = "experiments.candidates.vsp_05.real_toy_semantic_veto"
    assert not any(
        needle in path.read_text(encoding="utf-8")
        for path in production.rglob("*.py")
    )
    policy_source = (
        root / "experiments/candidates/vsp_05/semantic_veto_policy.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "physical_time",
        "skill_active_age",
        "remaining_horizon",
        "episode_index",
        "reward",
        "return_target",
        "terminal",
        "global_rng",
        "history",
        "recurrent",
    ):
        assert forbidden not in policy_source
    assert DET_ARM in ARMS
