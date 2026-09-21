import json

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05 import study


def tiny_config(**overrides):
    values = dict(source_macros=16, target_macros=8, contexts=4, skill_ticks=3)
    values.update(overrides)
    return study.Config(**values)


def tiny_specs():
    return [
        study.Spec("response_all", "response", 2),
        study.Spec("fingerprint_full", "law", 2),
        study.Spec("fingerprint_recent", "cell", 2, 4),
    ]


def test_correlated_law_family_and_three_tick_terminal_holds():
    slots = study._rng_slots(tiny_config(), seed=19)
    for law in (slots["source_law"], slots["target_law"]):
        np.testing.assert_allclose(law.sum(axis=1), 1.0)
        np.testing.assert_array_equal(np.sort(law[:, 3]), study.P11_VALUES)
    assert not np.array_equal(slots["source_law"], slots["target_law"])

    transition = study.simulate_terminal_macro(
        action=study.COOPERATIVE,
        outcome=3,
        completion_ticks=np.array([1, 3]),
    )
    np.testing.assert_array_equal(
        transition["primitive_actions"], [[1, 0], [0, 0], [0, 1]]
    )
    np.testing.assert_array_equal(
        transition["post_positions"], [[1, 0], [1, 0], [1, 1]]
    )
    safe = study.simulate_terminal_macro(
        action=study.SAFE, outcome=3, completion_ticks=np.array([1, 1])
    )
    assert not safe["primitive_actions"].any()
    assert not safe["post_positions"].any()


def test_one_common_collection_and_causal_preoutcome_law_for_all_fits():
    config = tiny_config()
    result = study.run_block(config, seed=31, specs=tiny_specs())
    common = result["common"]
    assert set(result["fits"]) == {spec.id for spec in tiny_specs()}
    np.testing.assert_array_equal(
        common["collection_action"], common["collector_uniform"] >= 0.5
    )
    np.testing.assert_array_equal(common["version"], common["phase"])
    np.testing.assert_array_equal(common["context"], common["phase_index"] % 4)
    np.testing.assert_array_equal(common["estimated_law"][0], np.full(4, 0.25))
    assert common["law_counts_before"][0] == 0

    # Reconstruct every stored pre-outcome law estimate from earlier cooperative rows only.
    counts = np.zeros((2, 4, 4), dtype=np.int64)
    prior_centers = np.full((2, 4), 0.25)
    for index in range(config.total_macros):
        version = int(common["version"][index])
        context = int(common["context"][index])
        if index == config.source_macros:
            source_posteriors = (counts[0] + 0.5) / (
                counts[0].sum(axis=1, keepdims=True) + 2
            )
            prior_centers[1] = source_posteriors.mean(axis=0)
        expected = (counts[version, context] + 2 * prior_centers[version]) / (
            counts[version, context].sum() + 2
        )
        np.testing.assert_allclose(common["estimated_law"][index], expected)
        assert common["law_counts_before"][index] == counts[version, context].sum()
        if common["collection_action"][index] == study.COOPERATIVE:
            counts[version, context, common["outcome"][index]] += 1
    np.testing.assert_array_equal(common["law_final_counts"], counts)
    # Version one freezes an equal-context mean of source posteriors before target feedback.
    target_center = prior_centers[1]
    np.testing.assert_allclose(common["law_prior_center"][config.source_macros], target_center)
    np.testing.assert_allclose(common["estimated_law"][config.source_macros], target_center)
    np.testing.assert_allclose(common["law_prior_centers"][1], target_center)


def test_response_decomposition_and_exact_regret_identities():
    config = tiny_config()
    spec = study.Spec("response_all", "response", 2)
    result = study.run_block(config, seed=7, specs=[spec])
    common = result["common"]
    curves = result["fits"][spec.id]["curves"]
    np.testing.assert_allclose(
        curves["response_prediction_error"] + curves["law_prediction_error"],
        curves["cooperative_prediction_error"],
        rtol=0,
        atol=2e-16,
    )
    rows = np.arange(config.total_macros)
    chosen = common["exact_values"][rows, curves["greedy_action"]]
    np.testing.assert_array_equal(curves["expected_return"], chosen)
    np.testing.assert_allclose(
        curves["regret"], common["exact_values"].max(axis=1) - chosen
    )
    np.testing.assert_array_equal(
        curves["sign_mistake"],
        curves["greedy_action"]
        != (common["exact_values"][:, 1] > common["exact_values"][:, 0]),
    )


def test_result_contract_counts_movement_and_numeric_evidence():
    config = tiny_config(source_macros=12, target_macros=8)
    result = study.run_block(config, seed=23, specs=tiny_specs())
    summary, common = result["summary"], result["common"]
    required = {
        "collection_action",
        "reward",
        "phase",
        "context",
        "version",
        "age",
        "estimated_law",
        "law_counts_before",
        "true_law",
        "pre_positions",
        "primitive_actions",
        "post_positions",
    }
    assert required <= set(common)
    assert summary["counts"] == {
        "source_macros": 12,
        "target_macros": 8,
        "total_macros": 20,
        "primitive_ticks": 60,
        "sampled_reward_labels": 20,
        "collection_action_counts": np.bincount(
            common["collection_action"], minlength=2
        ).tolist(),
        "source_collection_action_counts": np.bincount(
            common["collection_action"][:12], minlength=2
        ).tolist(),
        "target_collection_action_counts": np.bincount(
            common["collection_action"][12:], minlength=2
        ).tolist(),
        "law_posterior_updates": int((common["collection_action"] == 1).sum()),
        "law_fits": 1,
        "decision_fits": 3,
        "evaluation_panels": 60,
        "known_response_diagnostic_panels": 20,
        "evaluation_reward_draws": 0,
        "evaluation_learner_updates": 0,
    }
    assert summary["law_diagnostic"]["initial_to_final_l2_movement"] > 0
    assert set(summary["known_response_diagnostic"]["target_by_endpoint"]) == {
        "first64",
        "full",
        "late64",
    }
    for spec in tiny_specs():
        fit = result["fits"][spec.id]
        assert fit["curves"]["raw_predictions"].shape == (20, 2)
        assert fit["curves"]["clipped_predictions"].shape == (20, 2)
        assert fit["curves"]["greedy_action"].shape == (20,)
        assert fit["curves"]["exact_values"].shape == (20, 2)
        assert fit["summary"]["learner_observations"] == 20
        assert fit["summary"]["posterior_updates"] + fit["summary"][
            "regression_statistic_updates"
        ] == 20
        assert fit["summary"]["initial_to_final_l2_movement"] > 0
        assert fit["summary"]["compute_wall_seconds"] >= 0
        assert "learner expiry" in fit["summary"]["compute_wall_scope"]
        assert set(fit["summary"]["target_by_endpoint"]) == {
            "first64",
            "full",
            "late64",
        }
        assert all(array.dtype != object for array in fit["curves"].values())
        assert all(array.dtype != object for array in fit["state"].values())
        json.dumps(fit["summary"], allow_nan=False)
    json.dumps(summary, allow_nan=False)


def test_default_contract_and_invalid_tiny_horizons():
    config = study.Config()
    assert (config.source_macros, config.target_macros, config.contexts, config.skill_ticks) == (
        2048,
        256,
        4,
        3,
    )
    assert config.total_macros == 2304
    with pytest.raises(ValueError, match="divisible"):
        study.run_block(tiny_config(source_macros=10), seed=1, specs=tiny_specs())
    with pytest.raises(ValueError, match="unique"):
        spec = tiny_specs()[0]
        study.run_block(tiny_config(), seed=1, specs=[spec, spec])
