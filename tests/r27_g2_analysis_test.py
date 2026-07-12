from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from ha_ctse_process.r27_g2_analysis import (
    ACTION_DISTANCE_MIN,
    B3_FAKE_LABEL_SEED,
    B3_FIT_SEED,
    B3_LEARNING_RATE,
    B3_MAX_STEPS,
    B3_MIN_DELTA,
    B3_PATIENCE_VALIDATIONS,
    B3_VALIDATE_EVERY,
    B3_WEIGHT_DECAY,
    BOOTSTRAP_REPS,
    BOOTSTRAP_SEEDS,
    CHANCE_ACCURACY,
    DECODER_SCORE_MIN,
    FAKE_ACCURACY_MAX,
    HOLD_RATIO_MIN,
    LABEL_PAIRS,
    RHO_MIN,
    SKL_MIN,
    TRAIN_TEST_GAP_MAX,
    EvidenceError,
    GateAInput,
    GateB1Input,
    GateB2Input,
    GateB3Input,
    GateCInput,
    SupportEvidence,
    UnderpoweredEvidenceError,
    ValidityEvidence,
    assess_support,
    classify_checkpoint,
    classify_family,
    enumerated_pair_action_distance,
    enumerated_pair_skl,
    evaluate_gate_a,
    evaluate_gate_b1,
    evaluate_gate_b2,
    evaluate_gate_b3,
    evaluate_gate_c,
    h40_effect_distance,
    late_action_features,
    reset_cluster_bootstrap,
    standardized_rms_distance,
    trajectory_distance,
)


SMALL_BOOTSTRAP_REPS = 200


def _reset_ids() -> np.ndarray:
    return np.arange(64, dtype=np.int64)


def _labels() -> tuple[np.ndarray, np.ndarray]:
    reset_ids = _reset_ids()
    natural = np.empty((64, 6), dtype=np.int64)
    target = np.empty((64, 6, 3), dtype=np.int64)
    for reset_index, reset_id in enumerate(reset_ids):
        for agent in range(6):
            natural[reset_index, agent] = (int(reset_id) + agent) % 4
            target[reset_index, agent] = [
                label for label in range(4) if label != natural[reset_index, agent]
            ]
    return natural, target


def _adequate_support():
    return assess_support(
        SupportEvidence(
            reset_ids=_reset_ids(),
            hold_cell_present=np.ones((64, 6, 4), dtype=np.bool_),
            pair_contrast_present=np.ones((64, 6), dtype=np.bool_),
        )
    )


def _passing_gates():
    reset_ids = _reset_ids()
    gate_a = evaluate_gate_a(
        GateAInput(
            reset_ids=reset_ids,
            active_pair_skl=np.full((64, 6, 6), 0.04),
            inactive_pair_skl=np.zeros((64, 6, 6)),
            active_pair_stdmean_distance=np.full((64, 6, 6), 0.30),
        ),
        bootstrap_reps=SMALL_BOOTSTRAP_REPS,
    )
    active_skl = np.full((64, 6, 4, 40, 6), 0.04)
    active_skl[:, :, :, 30:40, :] = 0.03
    gate_b1 = evaluate_gate_b1(
        GateB1Input(
            reset_ids=reset_ids,
            active_pair_skl=active_skl,
            inactive_pair_skl=np.zeros_like(active_skl),
            active_pair_action_distance=np.full_like(active_skl, 0.30),
        ),
        bootstrap_reps=SMALL_BOOTSTRAP_REPS,
    )
    natural, target = _labels()
    gate_b2 = evaluate_gate_b2(
        GateB2Input(
            reset_ids=reset_ids,
            natural_labels=natural,
            target_labels=target,
            d_hold=np.full((64, 6, 3), 0.40),
            d_pulse=np.full((64, 6, 3), 0.10),
        ),
        bootstrap_reps=SMALL_BOOTSTRAP_REPS,
    )
    gate_c = evaluate_gate_c(
        GateCInput(
            reset_ids=reset_ids,
            natural_labels=natural,
            target_labels=target,
            e_hold=np.full((64, 6, 3), 0.40),
            e_pulse=np.full((64, 6, 3), 0.10),
        ),
        bootstrap_reps=SMALL_BOOTSTRAP_REPS,
    )
    return gate_a, gate_b1, gate_b2, gate_c


def _decoder_evidence() -> GateB3Input:
    reset_ids = _reset_ids()
    features = np.zeros((64, 6, 4, 12), dtype=np.float64)
    labels = np.broadcast_to(np.arange(4, dtype=np.int64), (64, 6, 4)).copy()
    rng = np.random.default_rng(9182)
    for reset_index in range(64):
        for agent in range(6):
            for label in range(4):
                features[reset_index, agent, label, label] = 4.0
                features[reset_index, agent, label, 4 + agent] = 0.05
                features[reset_index, agent, label] += rng.normal(0.0, 0.01, 12)
    return GateB3Input(reset_ids=reset_ids, features=features, labels=labels)


def test_scientific_defaults_are_the_frozen_contract():
    assert BOOTSTRAP_REPS == 10_000
    assert BOOTSTRAP_SEEDS == {
        "A": 27031,
        "B1": 27041,
        "B2": 27051,
        "B3": 27061,
        "C": 27071,
    }
    assert (SKL_MIN, ACTION_DISTANCE_MIN, RHO_MIN, HOLD_RATIO_MIN) == (
        0.02,
        0.20,
        0.50,
        1.50,
    )
    assert (DECODER_SCORE_MIN, CHANCE_ACCURACY, FAKE_ACCURACY_MAX) == (
        0.40,
        0.25,
        0.35,
    )
    assert TRAIN_TEST_GAP_MAX == 0.20
    assert (B3_FIT_SEED, B3_FAKE_LABEL_SEED) == (27022, 27023)
    assert (B3_LEARNING_RATE, B3_WEIGHT_DECAY) == (3e-3, 1e-4)
    assert (B3_MAX_STEPS, B3_VALIDATE_EVERY) == (1_000, 5)
    assert (B3_PATIENCE_VALIDATIONS, B3_MIN_DELTA) == (20, 1e-4)


def test_metric_builders_use_six_pairs_rms_scale_and_fixed_feature_order():
    means = np.zeros((2, 4, 4), dtype=np.float64)
    means[:, 1, 0] = 1.0
    logstd = np.zeros_like(means)
    pair_skl = enumerated_pair_skl(means, logstd)
    assert pair_skl.shape == (2, 6)
    assert tuple(LABEL_PAIRS) == ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    assert pair_skl[:, 0] == pytest.approx(0.5)

    action = np.zeros((1, 4, 4), dtype=np.float64)
    action[:, 1, :] = 2.0
    distance = enumerated_pair_action_distance(action, np.full(4, 2.0))
    assert distance[0, 0] == pytest.approx(1.0)
    assert standardized_rms_distance(action[:, 0], action[:, 1], np.full(4, 2.0)) == pytest.approx([1.0])

    time = np.arange(10, dtype=np.float64)
    actions = np.stack((time, np.full(10, 2.0), -time, np.zeros(10)), axis=1)
    features = late_action_features(actions)
    assert features.shape == (12,)
    assert features[[0, 3, 6, 9]] == pytest.approx([4.5, 2.0, -4.5, 0.0])
    assert features[[2, 5, 8, 11]] == pytest.approx([1.0, 0.0, -1.0, 0.0])

    branch_actions = np.ones((2, 3, 40, 4), dtype=np.float64)
    reference_actions = np.zeros((2, 40, 4), dtype=np.float64)
    assert trajectory_distance(
        branch_actions, reference_actions, np.ones(4)
    ) == pytest.approx(np.ones((2, 3)))
    branch_observation = np.ones((2, 3, 5), dtype=np.float64)
    reference_observation = np.zeros((2, 5), dtype=np.float64)
    assert h40_effect_distance(
        branch_observation, reference_observation, np.ones(5)
    ) == pytest.approx(np.ones((2, 3)))


def test_reset_bootstrap_is_deterministic_and_support_counts_distinct_resets():
    first = reset_cluster_bootstrap(
        np.arange(8, dtype=np.float64), reps=SMALL_BOOTSTRAP_REPS, seed=27031
    )
    second = reset_cluster_bootstrap(
        np.arange(8, dtype=np.float64), reps=SMALL_BOOTSTRAP_REPS, seed=27031
    )
    assert first == second
    assert first.estimate == pytest.approx(3.5)

    support = _adequate_support()
    assert support.adequate
    assert support.valid_resets == 64
    assert support.prefix_counts == (22, 21, 21)
    assert support.b3_split_counts == (40, 12, 12)
    assert support.b3_prefix_counts == ((14, 13, 13), (4, 4, 4), (4, 4, 4))

    pair_present = np.ones((64, 6), dtype=np.bool_)
    pair_present[39:, 0] = False
    underpowered = assess_support(
        SupportEvidence(
            reset_ids=_reset_ids(),
            hold_cell_present=np.ones((64, 6, 4), dtype=np.bool_),
            pair_contrast_present=pair_present,
        )
    )
    assert not underpowered.adequate
    assert underpowered.pair_counts[0] == 39
    assert any("reset support 39 < 40" in reason for reason in underpowered.reasons)


def test_gate_estimators_follow_reset_agent_pair_hierarchies():
    gate_a, gate_b1, gate_b2, gate_c = _passing_gates()
    assert gate_a.passed
    assert gate_a.mean_skl == pytest.approx(0.04)
    assert gate_a.active_minus_inactive.lower > 0.0
    assert gate_b1.passed
    assert gate_b1.rho == pytest.approx(0.75)
    assert sum(result.passed for result in gate_b1.agents) == 6
    assert sum(result.passed for result in gate_b1.pairs) == 6
    assert gate_b2.passed and gate_b2.ratio == pytest.approx(4.0)
    assert all(result.support_resets == 64 for result in gate_b2.pairs)
    assert gate_c.passed and gate_c.ratio == pytest.approx(4.0)


def test_b3_fixed_split_decoder_passes_signal_and_rejects_fake_mapping():
    result = evaluate_gate_b3(
        _decoder_evidence(), bootstrap_reps=SMALL_BOOTSTRAP_REPS
    )
    assert result.passed
    assert result.accuracy >= 0.95
    assert result.macro_f1 >= 0.95
    assert result.accuracy_interval.lower > 0.25
    assert result.fake_accuracy <= 0.35
    assert sum(item.test_accuracy >= 0.40 for item in result.decoders) == 6
    assert all(item.train_minus_test <= 0.20 for item in result.decoders)
    assert all(item.optimizer_steps <= 1_000 for item in result.decoders)


def test_b3_refuses_underpowered_fixed_split_before_fitting():
    evidence = _decoder_evidence()
    keep = ~np.isin(evidence.reset_ids, [0, 3])
    with pytest.raises(UnderpoweredEvidenceError, match="test prefix stratum 0"):
        evaluate_gate_b3(
            GateB3Input(
                reset_ids=evidence.reset_ids[keep],
                features=evidence.features[keep],
                labels=evidence.labels[keep],
            ),
            bootstrap_reps=10,
        )


def test_nonfinite_and_malformed_evidence_fail_closed():
    active = np.full((64, 6, 6), 0.04)
    active[0, 0, 0] = np.nan
    with pytest.raises(EvidenceError, match="non-finite"):
        evaluate_gate_a(
            GateAInput(
                reset_ids=_reset_ids(),
                active_pair_skl=active,
                inactive_pair_skl=np.zeros((64, 6, 6)),
                active_pair_stdmean_distance=np.ones((64, 6, 6)),
            ),
            bootstrap_reps=10,
        )
    with pytest.raises(EvidenceError, match="distinct within reset-agent"):
        natural, target = _labels()
        target[0, 0] = [0, 0, 0]
        evaluate_gate_b2(
            GateB2Input(
                reset_ids=_reset_ids(),
                natural_labels=natural,
                target_labels=target,
                d_hold=np.ones((64, 6, 3)),
                d_pulse=np.zeros((64, 6, 3)),
            ),
            bootstrap_reps=10,
        )


def test_checkpoint_and_family_precedence_are_exact():
    gate_a, gate_b1, gate_b2, gate_c = _passing_gates()
    gate_b3 = evaluate_gate_b3(_decoder_evidence(), bootstrap_reps=50)
    support = _adequate_support()
    validity = ValidityEvidence(passed=True)
    passed = classify_checkpoint(
        validity=validity,
        support=support,
        gate_a=gate_a,
        gate_b1=gate_b1,
        gate_b2=gate_b2,
        gate_b3=gate_b3,
        gate_c=gate_c,
    )
    assert passed.outcome == "PERSISTENT_BEHAVIOR_AND_EFFECT"
    assert passed.gate_b is True

    invalid = classify_checkpoint(
        validity=ValidityEvidence(passed=False, failures=("RNG mismatch",)),
        support=support,
    )
    assert invalid.outcome == "INVALID"
    suspect = classify_checkpoint(
        validity=validity,
        support=support,
        gate_a=replace(gate_a, passed=False),
    )
    assert suspect.outcome == "INVALID_SUSPECT"
    repeated = classify_checkpoint(
        validity=validity,
        support=support,
        gate_a=replace(gate_a, passed=False),
        gate_a_valid_repetition=True,
    )
    assert repeated.outcome == "NO_BRANCHPOINT_STATIC_REPLICATION"

    no_effect = classify_checkpoint(
        validity=validity,
        support=support,
        gate_a=gate_a,
        gate_b1=gate_b1,
        gate_b2=gate_b2,
        gate_b3=gate_b3,
        gate_c=replace(gate_c, passed=False),
    )
    assert no_effect.outcome == "PERSISTENT_ACTION_NO_EFFECT"
    family = classify_family((passed, passed, no_effect))
    assert family.outcome == "PASS_BEHAVIOR_EFFECT"
    assert classify_family((passed, no_effect, no_effect)).outcome == "PASS_BEHAVIOR_NO_STABLE_EFFECT"
    assert classify_family((repeated, repeated, passed)).outcome == "FAIL_BEHAVIOR_FAMILY"
