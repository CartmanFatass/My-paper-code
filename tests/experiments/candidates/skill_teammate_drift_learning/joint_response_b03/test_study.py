import json

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.joint_response_b03 import study


def tiny_config(**overrides):
    values = dict(
        source_macros=12,
        target_macros=8,
        skill_ticks=3,
        recent_window=4,
        prior_strength=2,
    )
    values.update(overrides)
    return study.Config(**values)


def test_source_product_curve_is_rank_deficient_and_target_leaves_it():
    config = tiny_config(source_macros=128, target_macros=16)
    schedule = study.context_schedule(config)
    source_u = schedule["u"][: config.source_macros]
    source_v = schedule["v"][: config.source_macros]
    np.testing.assert_allclose(source_u * source_v, 0.16, rtol=0, atol=3e-17)
    assert len(set(zip(schedule["u"], schedule["v"]))) == config.total_macros
    assert 0.82 < schedule["u"][config.source_macros] < 0.83
    assert 0.84 < schedule["v"][config.source_macros] < 0.85
    assert schedule["u"][-1] < 0.92 and schedule["v"][-1] < 0.94

    source_phi = np.stack(
        [study.joint_probabilities(u, v) for u, v in zip(source_u, source_v)]
    )
    assert np.linalg.matrix_rank(source_phi) == 3
    null = np.array([-0.16, -0.16, -0.16, 0.84])
    np.testing.assert_allclose(source_phi @ null, 0.0, rtol=0, atol=8e-17)

    # Two reward tables agree on the source curve but imply different target action.
    true_means = np.array([0.05, 0.05, 0.05, 0.95])
    alternative = true_means - 0.5 * null
    source_values = source_phi @ true_means
    np.testing.assert_allclose(source_values, source_phi @ alternative, atol=1e-16)
    target_phi = study.joint_probabilities(0.87, 0.89)
    assert target_phi @ true_means > study.SAFE_REWARD_MEAN
    assert target_phi @ alternative < study.SAFE_REWARD_MEAN


def test_three_tick_closed_loop_moves_once_then_physically_holds():
    cooperative = study.simulate_terminal_macro(
        skill=study.COOPERATIVE,
        p=0.5,
        q=0.5,
        primitive_uniform=np.array([[0.1, 0.9], [0.0, 0.8], [0.0, 0.1]]),
        reward_uniform=0.94,
    )
    np.testing.assert_array_equal(
        cooperative["primitive_actions"], [[1, 0], [0, 0], [0, 1]]
    )
    np.testing.assert_array_equal(
        cooperative["pre_positions"], [[0, 0], [1, 0], [1, 0]]
    )
    np.testing.assert_array_equal(
        cooperative["post_positions"], [[1, 0], [1, 0], [1, 1]]
    )
    assert cooperative["reward_probability"] == 0.95
    assert cooperative["reward"] == 1

    safe = study.simulate_terminal_macro(
        skill=study.SAFE,
        p=0.5,
        q=0.5,
        primitive_uniform=np.zeros((3, 2)),
        reward_uniform=0.7,
    )
    assert not safe["primitive_actions"].any()
    assert not safe["post_positions"].any()
    assert safe["reward_probability"] == 0.60
    assert safe["reward"] == 0

    completions = np.array([0.25, 0.64, 0.9])
    per_tick = study.completion_probability_to_tick_probability(completions, 3)
    np.testing.assert_allclose(1.0 - (1.0 - per_tick) ** 3, completions)


def test_priors_joint_projection_additive_limitation_and_solve_counts():
    config = tiny_config(recent_window=2)
    for arm in study.ARMS:
        learner = study._Learner(arm, config)
        np.testing.assert_array_equal(learner.predict_raw(0.4, 0.4), [0.5, 0.5])

    joint = study._Learner("joint_response", config)
    rewards = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 1}
    for (x, y), reward in rewards.items():
        assert joint.update(
            skill=study.COOPERATIVE, x=x, y=y, u=0.4, v=0.4, reward=reward
        ) == 0
    posterior = (np.array([0.0, 0.0, 0.0, 1.0]) + 1.0) / 3.0
    expected = study.joint_probabilities(0.8, 0.9) @ posterior
    assert joint.predict_raw(0.8, 0.9)[study.COOPERATIVE] == expected

    conditional = np.array([[0.05, 0.05], [0.05, 0.95]])
    interaction_contrast = (
        conditional[1, 1] - conditional[1, 0]
        - conditional[0, 1] + conditional[0, 0]
    )
    assert interaction_contrast == pytest.approx(0.9)
    # Every additive b0+bX*X+bY*Y table has zero interaction contrast.
    additive = np.array([[0.2, 0.3], [0.4, 0.5]])
    assert additive[1, 1] - additive[1, 0] - additive[0, 1] + additive[0, 0] == 0

    full = study._Learner("fingerprint_full", config)
    assert full.update(skill=0, x=0, y=0, u=0.4, v=0.4, reward=1) == 1
    assert full.solves == 1
    recent = study._Learner("fingerprint_recent", config)
    recent.update(skill=0, x=0, y=0, u=0.4, v=0.4, reward=1)
    recent.update(skill=0, x=0, y=0, u=0.5, v=0.3, reward=0)
    # Evicting skill 0 while inserting skill 1 changes and solves both tables.
    assert recent.update(skill=1, x=1, y=1, u=0.8, v=0.8, reward=1) == 2


def test_same_seed_all_arms_receive_identical_causal_data():
    config = tiny_config()
    results = {
        arm: study.run_fit(config, arm=arm, seed=93001) for arm in study.ARMS
    }
    reference = results[study.ARMS[0]]["transitions"]
    for arm, result in results.items():
        assert set(result["transitions"]) == set(reference)
        for key in reference:
            np.testing.assert_array_equal(result["transitions"][key], reference[key])
        curves = result["curves"]
        assert curves["learner_updates_before_panel"] == list(range(config.total_macros))
        assert curves["raw_predictions"][0] == [0.5, 0.5]
        assert curves["clipped_predictions"][0] == [0.5, 0.5]
        assert curves["greedy_action"][0] == study.SAFE
        assert curves["collection_skill"] == reference["collection_skill"].tolist()
        assert curves["sampled_reward"] == reference["reward"].tolist()
        assert curves["outcomes"] == reference["outcomes"].tolist()
    np.testing.assert_array_equal(
        reference["collection_skill"], reference["skill_uniform"] >= 0.5
    )


@pytest.mark.parametrize("arm", ["recent", "fingerprint_recent"])
def test_recent_window_evicts_every_observation_outside_shared_window(arm):
    config = tiny_config(source_macros=5, target_macros=3, recent_window=3)
    result = study.run_fit(config, arm=arm, seed=8)
    state = result["learner_state"]
    transitions = result["transitions"]
    assert state["window_update_index"].tolist() == [5, 6, 7]
    np.testing.assert_array_equal(state["window_skill"], transitions["collection_skill"][-3:])
    np.testing.assert_array_equal(state["window_reward"], transitions["reward"][-3:])
    assert state["counts"].sum() == 3
    if arm == "fingerprint_recent":
        expected_features = []
        for index in range(5, 8):
            skill = int(transitions["collection_skill"][index])
            expected_features.append(
                study._saturated_feature(
                    skill, float(transitions["u"][index]), float(transitions["v"][index])
                )
            )
        np.testing.assert_allclose(state["window_features"], expected_features)
        rebuilt_xtx = np.zeros_like(state["xtx"])
        for skill, feature in zip(state["window_skill"], state["window_features"]):
            rebuilt_xtx[skill] += np.outer(feature, feature)
        np.testing.assert_allclose(state["xtx"], rebuilt_xtx, rtol=0, atol=2e-16)


def test_summary_endpoints_support_movement_and_arrays_reconstruct_exactly():
    config = tiny_config(source_macros=10, target_macros=6, recent_window=4)
    result = study.run_fit(
        config,
        arm="fingerprint_full",
        seed=11,
        object_name="CUSTOM_B03",
    )
    summary = result["summary"]
    curves = result["curves"]
    transitions = result["transitions"]
    assert summary["object"] == "CUSTOM_B03"
    assert summary["counts"] == {
        "source_macros": 10,
        "target_macros": 6,
        "total_macros": 16,
        "primitive_ticks": 48,
        "sampled_reward_labels": 16,
        "learner_updates": 16,
        "evaluation_panels": 16,
        "evaluation_sampled_rewards": 0,
        "evaluation_learner_updates": 0,
        "regression_solves": 16,
    }
    assert summary["source_regression_solve_count"] == 10
    assert summary["target_regression_solve_count"] == 6
    assert summary["source_estimate_l2_movement"] >= 0.0
    assert summary["target_estimate_l2_movement"] >= 0.0
    assert summary["source_support"]["sample_count"] == 10
    assert summary["target_support"]["sample_count"] == 6
    assert sum(summary["source_support"]["skill_counts"]) == 10
    assert sum(summary["target_support"]["skill_counts"]) == 6

    raw = np.asarray(curves["raw_predictions"])
    clipped = np.asarray(curves["clipped_predictions"])
    truth = np.asarray(curves["true_values"])
    actions = np.asarray(curves["greedy_action"])
    np.testing.assert_array_equal(clipped, np.clip(raw, 0.0, 1.0))
    reconstructed_native = truth[np.arange(config.total_macros), actions]
    reconstructed_mae = np.abs(clipped - truth).mean(axis=1)
    np.testing.assert_allclose(curves["expected_native_return"], reconstructed_native)
    np.testing.assert_allclose(curves["value_mae"], reconstructed_mae)
    target = slice(config.source_macros, config.total_macros)
    assert summary["primary_native_return"] == reconstructed_native[target].mean()
    assert summary["full_target_native_return"] == reconstructed_native[target].mean()
    assert summary["late_target_native_return"] == reconstructed_native[target].mean()
    assert summary["primary_value_mae"] == reconstructed_mae[target].mean()
    assert summary["full_target_value_mae"] == reconstructed_mae[target].mean()
    assert summary["late_target_value_mae"] == reconstructed_mae[target].mean()

    for index, (u, v) in enumerate(zip(transitions["u"], transitions["v"])):
        np.testing.assert_allclose(truth[index], study.exact_skill_values(float(u), float(v)))
    assert all(array.dtype != object for array in transitions.values())
    assert all(array.dtype != object for array in result["learner_state"].values())
    json.dumps(curves, allow_nan=False)
    json.dumps(summary, allow_nan=False)


def test_invalid_scope_is_rejected_without_a_fit():
    with pytest.raises(ValueError, match="source_macros"):
        study.run_fit(tiny_config(source_macros=0), arm="uniform", seed=1)
    with pytest.raises(ValueError, match="arm"):
        study.run_fit(tiny_config(), arm="not-an-arm", seed=1)
    with pytest.raises(ValueError, match="object_name"):
        study.run_fit(tiny_config(), arm="uniform", seed=1, object_name="")


@pytest.mark.parametrize("arm", ["fingerprint_full", "fingerprint_recent", "additive_response"])
def test_online_ridge_equals_independent_augmented_batch_least_squares(arm):
    config = tiny_config(recent_window=3)
    records = [
        (0, 0, 0, .25, .64, 1),
        (1, 1, 0, .40, .40, 0),
        (1, 0, 1, .64, .25, 1),
        (0, 0, 0, .85, .87, 0),
        (1, 1, 1, .90, .92, 1),
    ]
    learner = study._Learner(arm, config)
    for skill, x, y, u, v, reward in records:
        learner.update(skill=skill, x=x, y=y, u=u, v=v, reward=reward)
    retained = records[-3:] if arm == "fingerprint_recent" else records
    dimension = 3 if arm == "additive_response" else 4
    prior = np.array([.5, 0, 0]) if dimension == 3 else np.full(4, .5)
    for skill in (0, 1):
        features, rewards = [], []
        for actual_skill, x, y, u, v, reward in retained:
            if actual_skill != skill:
                continue
            if skill == 0:
                row = [1] + [0] * (dimension - 1)
            elif dimension == 3:
                row = [1, x, y]
            else:
                row = [(1-u)*(1-v), (1-u)*v, u*(1-v), u*v]
            features.append(row)
            rewards.append(reward)
        design = np.asarray(features, dtype=np.float64).reshape(-1, dimension)
        augmented_design = np.vstack((design, np.sqrt(2) * np.eye(dimension)))
        augmented_labels = np.concatenate((rewards, np.sqrt(2) * prior))
        expected = np.linalg.lstsq(augmented_design, augmented_labels, rcond=None)[0]
        np.testing.assert_allclose(learner.coefficients[skill], expected, rtol=1e-14, atol=1e-15)
        np.testing.assert_allclose(learner.xtx[skill], design.T @ design, atol=1e-15)
        np.testing.assert_allclose(learner.xty[skill], design.T @ rewards, atol=1e-15)


def test_fixed_default_config_and_disjoint_endpoint_slices(monkeypatch):
    default = study.Config()
    assert (default.source_macros, default.target_macros, default.skill_ticks) == (2048, 256, 3)
    assert (default.recent_window, default.prior_strength) == (64, 2)
    called = []
    original = study._endpoint

    def record(curves, start, stop):
        called.append((start, stop))
        return original(curves, start, stop)

    monkeypatch.setattr(study, "_endpoint", record)
    # A short deterministic fixture checks indexing, not a production score.
    study.run_fit(tiny_config(source_macros=3, target_macros=80), arm="uniform", seed=9)
    assert called == [(3, 67), (3, 83), (19, 83)]
