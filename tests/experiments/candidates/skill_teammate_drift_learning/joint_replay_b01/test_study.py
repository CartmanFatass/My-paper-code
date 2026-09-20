import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.joint_replay_b01 import study


def small_config(**overrides):
    values = {
        "version_schedule": ("A", "B", "A"),
        "episodes_per_block": 1,
        "macros_per_episode": 2,
        "macro_duration": 3,
        "batch_size": 8,
        "recent_capacity": 2,
        "evaluation_interval": 1,
        "primary_evaluation_episodes": (),
    }
    values.update(overrides)
    return study.Config(**values)


def test_primitive_policy_support_normalization_and_physical_hold():
    for goal in (study.LEFT, study.RIGHT):
        for position in range(5):
            probabilities = [
                study.primitive_action_probability(position, goal, action, 0.8)
                for action in (study.MOVE_LEFT, study.HOLD, study.MOVE_RIGHT)
            ]
            assert sum(probabilities) == 1.0
            target = 0 if goal == study.LEFT else 4
            if position == target:
                assert probabilities == [0.0, 1.0, 0.0]
    assert study.apply_primitive_action(2, study.MOVE_LEFT) == 1
    assert study.apply_primitive_action(2, study.HOLD) == 2
    assert study.apply_primitive_action(2, study.MOVE_RIGHT) == 3
    assert study.native_service_reward(0, 4) == 1.0
    assert study.native_service_reward(0, 0) == 0.5
    assert study.native_service_reward(2, 3) == 0.0


def test_full_likelihood_changes_when_only_teammate_goal_policy_changes():
    positions = np.array([[2, 2], [1, 3], [0, 4]], dtype=np.int8)
    actions = np.array([[-1, 1], [-1, 1], [0, 0]], dtype=np.int8)
    common = dict(
        teammate_goal=study.RIGHT,
        ego_goal=study.LEFT,
        pre_positions=positions,
        primitive_actions=actions,
        ego_move_probability=0.8,
        teammate_move_probability=0.8,
    )
    behavior = study.trajectory_likelihood(
        **common, teammate_right_probability=0.8
    )
    changed_teammate = study.trajectory_likelihood(
        **common, teammate_right_probability=0.2
    )
    assert behavior["ego_primitive"] == changed_teammate["ego_primitive"]
    assert behavior["teammate_primitive"] == changed_teammate["teammate_primitive"]
    assert behavior["teammate_primitive"] > 0.0  # fixed factor was evaluated
    assert changed_teammate["total"] / behavior["total"] == 0.25
    changed_both = study.trajectory_likelihood(
        **{**common, "ego_move_probability": 0.6}, teammate_right_probability=0.2
    )
    np.testing.assert_allclose(
        changed_both["total"] / behavior["total"],
        (0.6 / 0.8) ** 2 * (0.2 / 0.8),
        rtol=0, atol=1e-16,
    )


def test_global_weight_normalization_survives_singleton_entry_grouping():
    q_values = np.zeros((2, 5, 5, 2), dtype=np.float64)
    study.simultaneous_q_update(
        q_values,
        remaining=np.array([1, 1]),
        ego_position=np.array([0, 1]),
        teammate_position=np.array([0, 0]),
        action=np.array([0, 0]),
        reward=np.array([1.0, 1.0]),
        next_remaining=np.array([0, 0]),
        next_ego_position=np.array([0, 1]),
        next_teammate_position=np.array([0, 0]),
        terminal=np.array([True, True]),
        weights=np.array([0.5, 1.5]),  # already global-mean normalized
        alpha=0.1,
        continuation_discount=0.5,
    )
    assert q_values[1, 0, 0, 0] == 0.05
    assert np.isclose(q_values[1, 1, 0, 0], 0.15, rtol=0.0, atol=1e-16)
    assert not q_values[0].any()


def test_targets_precede_simultaneous_updates_and_terminal_never_bootstraps():
    q_values = np.zeros((3, 5, 5, 2), dtype=np.float64)
    q_values[0, 0, 0] = 1000.0  # must be ignored by the terminal sample
    study.simultaneous_q_update(
        q_values,
        remaining=np.array([1, 2]),
        ego_position=np.array([0, 1]),
        teammate_position=np.array([0, 0]),
        action=np.array([0, 0]),
        reward=np.array([1.0, 0.0]),
        next_remaining=np.array([0, 1]),
        next_ego_position=np.array([0, 0]),
        next_teammate_position=np.array([0, 0]),
        terminal=np.array([True, False]),
        weights=np.ones(2),
        alpha=0.5,
        continuation_discount=0.9,
    )
    assert q_values[1, 0, 0, 0] == 0.5
    assert q_values[2, 1, 0, 0] == 0.0  # saw the pre-update remaining=1 row


def test_exact_evaluator_mixes_teammate_goal_once_per_macro():
    config = small_config(
        version_schedule=("A",), macros_per_episode=1, evaluation_interval=1
    )
    transition, reward = study.macro_model(config, 0)
    np.testing.assert_allclose(transition.sum(axis=-1), 1.0, rtol=0, atol=5e-16)
    right_probability = config.teammate_right_probabilities[0]
    manually_mixed_left_reward = (
        (1.0 - right_probability) * reward[study.LEFT, study.LEFT]
        + right_probability * reward[study.LEFT, study.RIGHT]
    )
    q_values = np.zeros((2, 5, 5, 2), dtype=np.float64)
    evaluated = study.exact_policy_evaluation(q_values, config, 0)
    assert evaluated["discounted_service_return"] == float(
        manually_mixed_left_reward.mean()
    )
    repeated = study.exact_policy_evaluation(q_values, config, 0)
    np.testing.assert_array_equal(evaluated["values"], repeated["values"])
    optimum = study.exact_optimal_evaluation(config, 0)
    assert optimum["discounted_service_return"] >= evaluated["discounted_service_return"]

    two_macro = small_config(
        version_schedule=("A",), macros_per_episode=2, evaluation_interval=1
    )
    mixed_transition, mixed_reward = study._mixed_macro_model(two_macro, 0)
    zero_q = np.zeros((3, 5, 5, 2), dtype=np.float64)
    two_evaluated = study.exact_policy_evaluation(zero_q, two_macro, 0)
    one_macro_values = mixed_reward[study.LEFT]
    manual_two_macro = one_macro_values + two_macro.gamma ** 3 * (
        mixed_transition[study.LEFT] @ one_macro_values
    )
    assert two_evaluated["discounted_service_return"] == float(
        manual_two_macro.mean()
    )


def test_macro_model_matches_independent_physical_branch_enumeration():
    # This reference does not call the candidate action-probability, reward,
    # transition or matrix-composition helpers. It evolves probability mass on
    # the literal line while holding the sampled teammate endpoint for 3 ticks.
    config = small_config()
    for version in (0, 1):
        matrix, macro_rewards = study._mixed_macro_model(config, version)
        own_p = config.ego_move_probabilities[version]
        peer_q = config.teammate_right_probabilities[version]
        for goal in (0, 1):
            for x0 in range(5):
                for x1 in range(5):
                    terminal_mass = np.zeros(25)
                    expected_reward = 0.0
                    for peer_goal, goal_mass in ((0, 1 - peer_q), (1, peer_q)):
                        distribution = {(x0, x1): goal_mass}
                        for tick in range(3):
                            following = {}
                            for (x, y), mass in distribution.items():
                                own_target, peer_target = 4 * goal, 4 * peer_goal
                                own_choices = (
                                    [(x, 1.0)] if x == own_target else
                                    [(x, 1 - own_p), (x + (1 if goal else -1), own_p)]
                                )
                                peer_choices = (
                                    [(y, 1.0)] if y == peer_target else
                                    [(y, 0.2), (y + (1 if peer_goal else -1), 0.8)]
                                )
                                for nx, px in own_choices:
                                    for ny, py in peer_choices:
                                        probability = mass * px * py
                                        endpoints = int(nx == 0 or ny == 0)
                                        endpoints += int(nx == 4 or ny == 4)
                                        expected_reward += (
                                            probability * 0.5 * endpoints * 0.95 ** tick
                                        )
                                        following[nx, ny] = (
                                            following.get((nx, ny), 0.0) + probability
                                        )
                            distribution = following
                        for (nx, ny), mass in distribution.items():
                            terminal_mass[5 * nx + ny] += mass
                    np.testing.assert_allclose(
                        matrix[goal, 5 * x0 + x1], terminal_mass,
                        rtol=0, atol=2e-14,
                    )
                    np.testing.assert_allclose(
                        macro_rewards[goal, 5 * x0 + x1], expected_reward,
                        rtol=0, atol=2e-14,
                    )


def test_fingerprint_replay_keeps_old_matching_context_and_excludes_incompatible():
    versions = np.array([0, 0, 1, 1, 0], dtype=np.int8)
    eligible = study.replay_eligible_indices(
        "fingerprint",
        versions,
        current_version=0,
        current_index=4,
        recent_capacity=2,
    )
    assert eligible.tolist() == [0, 1, 4]
    recent = study.replay_eligible_indices(
        "recent", versions, current_version=0, current_index=4, recent_capacity=2
    )
    assert recent.tolist() == [3, 4]
    for arm in ("joint_is", "uniform"):
        full = study.replay_eligible_indices(
            arm, versions, current_version=0, current_index=4, recent_capacity=2
        )
        assert full.tolist() == [0, 1, 2, 3, 4]

    result = study.run_fit(small_config(), arm="fingerprint", seed=41)
    transitions = result["transitions"]
    assert np.array_equal(
        transitions["replay_sample_versions"],
        np.broadcast_to(
            transitions["collection_version"][:, None],
            transitions["replay_sample_versions"].shape,
        ),
    )
    assert np.array_equal(
        transitions["replay_table_indices"],
        transitions["replay_sample_versions"],
    )


def test_stable_joint_weights_are_bit_identical_to_uniform_learning():
    config = small_config(
        version_schedule=("A",),
        episodes_per_block=4,
        macros_per_episode=3,
        recent_capacity=3,
        evaluation_interval=2,
    )
    joint = study.run_fit(config, arm="joint_is", seed=90210)
    uniform = study.run_fit(config, arm="uniform", seed=90210)
    np.testing.assert_array_equal(joint["q_values"], uniform["q_values"])
    np.testing.assert_array_equal(
        joint["transitions"]["replay_indices"],
        uniform["transitions"]["replay_indices"],
    )
    np.testing.assert_array_equal(
        joint["transitions"]["primitive_actions"],
        uniform["transitions"]["primitive_actions"],
    )
    assert (joint["transitions"]["replay_raw_ratios"] == 1.0).all()
    assert (joint["transitions"]["replay_normalized_weights"] == 1.0).all()


def test_drifting_joint_loop_retains_the_complete_behavior_ratio():
    config = small_config()
    result = study.run_fit(config, arm="joint_is", seed=41)
    transitions = result["transitions"]
    for update, samples in enumerate(transitions["replay_indices"]):
        current = int(transitions["collection_version"][update])
        expected = []
        for sample in samples:
            past = int(transitions["collection_version"][sample])
            peer_goal = int(transitions["teammate_goal"][sample])
            now_q = config.teammate_right_probabilities[current]
            old_q = config.teammate_right_probabilities[past]
            ratio = now_q / old_q if peer_goal else (1 - now_q) / (1 - old_q)
            now_p = config.ego_move_probabilities[current]
            old_p = config.ego_move_probabilities[past]
            target = 4 * int(transitions["ego_goal"][sample])
            # The unchanged teammate primitive factors cancel. At an endpoint,
            # actual ego hold also has probability 1 under both controllers.
            for position, action in zip(
                transitions["pre_positions"][sample, :, 0],
                transitions["primitive_actions"][sample, :, 0],
            ):
                if position != target:
                    ratio *= now_p / old_p if action else (1 - now_p) / (1 - old_p)
            expected.append(ratio)
        expected = np.asarray(expected)
        np.testing.assert_allclose(
            transitions["replay_raw_ratios"][update], expected,
            rtol=2e-15, atol=0,
        )
        np.testing.assert_allclose(
            transitions["replay_normalized_weights"][update],
            expected / expected.mean(), rtol=2e-15, atol=0,
        )
    assert np.any(transitions["replay_raw_ratios"] != 1.0)


def test_fit_counts_movement_rng_addresses_and_transition_audit_arrays():
    config = small_config()
    result = study.run_fit(config, arm="recent", seed=123)
    summary = result["summary"]
    transitions = result["transitions"]
    assert summary["object"] == "STDL_JOINT_REPLAY_B01"
    assert summary["counts"] == {
        "episodes": 3,
        "macro_transitions": 6,
        "primitive_transitions": 18,
        "minibatch_updates": 6,
        "replay_sample_uses": 48,
        "evaluation_panels": 4,
        "evaluation_episodes_simulated": 0,
        "evaluation_parameter_updates": 0,
    }
    assert summary["movement"]["final_q_l2_movement"] > 0.0
    assert summary["movement"]["terminal_q_linf"] == 0.0
    assert not result["q_values"][0].any()
    assert all(array.dtype != object for array in transitions.values())
    assert transitions["primitive_actions"].shape == (6, 3, 2)
    assert transitions["primitive_uniform"].shape == (6, 3, 2, 2)
    assert transitions["terminal"].sum() == config.total_episodes
    for current_index, samples in enumerate(transitions["replay_indices"]):
        assert samples.min() >= max(0, current_index + 1 - config.recent_capacity)
        assert samples.max() <= current_index

    slots = study.common_random_slots(config, 123)
    np.testing.assert_array_equal(
        transitions["episode_reset_positions"], slots["reset_positions"]
    )
    np.testing.assert_array_equal(
        transitions["primitive_uniform"],
        slots["primitive_uniform"].reshape(6, 3, 2, 2),
    )
    for index in range(config.total_macros):
        version = int(transitions["collection_version"][index])
        likelihood = study.trajectory_likelihood(
            teammate_goal=int(transitions["teammate_goal"][index]),
            ego_goal=int(transitions["ego_goal"][index]),
            pre_positions=transitions["pre_positions"][index],
            primitive_actions=transitions["primitive_actions"][index],
            ego_move_probability=config.ego_move_probabilities[version],
            teammate_right_probability=config.teammate_right_probabilities[version],
            teammate_move_probability=config.teammate_move_probability,
        )
        assert likelihood["total"] == transitions[
            "behavior_trajectory_likelihood"
        ][index]


def test_reward_upper_initialization_is_exact_including_gamma_one():
    config = small_config(
        initialization="reward_upper",
        gamma=0.5,
        macro_duration=2,
        macros_per_episode=3,
    )
    q_values = study.initialize_q_values(config, "uniform")
    assert not q_values[0].any()
    for remaining in range(1, 4):
        expected = sum(0.5 ** tick for tick in range(2 * remaining))
        assert (q_values[remaining] == expected).all()

    undiscounted = study.initialize_q_values(
        small_config(
            initialization="reward_upper",
            gamma=1.0,
            macro_duration=2,
            macros_per_episode=3,
        ),
        "uniform",
    )
    for remaining in range(1, 4):
        assert (undiscounted[remaining] == 2 * remaining).all()

    fingerprint = study.initialize_q_values(config, "fingerprint")
    np.testing.assert_array_equal(fingerprint[0], fingerprint[1])
    assert not np.shares_memory(fingerprint[0], fingerprint[1])
    before = fingerprint[1].copy()
    fingerprint[0, 1, 0, 0, 0] -= 1.0
    np.testing.assert_array_equal(fingerprint[1], before)

    with pytest.raises(ValueError, match="initialization"):
        study.validate_config(small_config(initialization="invalid"))


def test_default_and_explicit_zero_initialization_have_identical_behavior():
    implicit = small_config()
    explicit = small_config(initialization="zero")
    assert implicit == explicit
    implicit_result = study.run_fit(implicit, arm="uniform", seed=77)
    explicit_result = study.run_fit(explicit, arm="uniform", seed=77)
    np.testing.assert_array_equal(
        implicit_result["q_values"], explicit_result["q_values"]
    )
    assert implicit_result["curves"] == explicit_result["curves"]
    assert implicit_result["summary"] == explicit_result["summary"]
    for key in implicit_result["transitions"]:
        np.testing.assert_array_equal(
            implicit_result["transitions"][key],
            explicit_result["transitions"][key],
        )


def test_optimistic_stable_joint_and_uniform_remain_bit_identical():
    config = small_config(
        initialization="reward_upper",
        version_schedule=("A",),
        episodes_per_block=4,
        macros_per_episode=3,
        recent_capacity=3,
        evaluation_interval=2,
    )
    joint = study.run_fit(config, arm="joint_is", seed=92001)
    uniform = study.run_fit(config, arm="uniform", seed=92001)
    np.testing.assert_array_equal(joint["q_values"], uniform["q_values"])
    np.testing.assert_array_equal(
        joint["transitions"]["replay_indices"],
        uniform["transitions"]["replay_indices"],
    )
    np.testing.assert_array_equal(
        joint["transitions"]["primitive_actions"],
        uniform["transitions"]["primitive_actions"],
    )
    assert joint["curves"]["q_l2_movement"] == uniform["curves"][
        "q_l2_movement"
    ]


def test_fingerprint_tables_retain_updates_across_version_switch():
    common = dict(
        initialization="reward_upper",
        episodes_per_block=1,
        macros_per_episode=2,
        batch_size=8,
        recent_capacity=2,
        evaluation_interval=1,
        primary_evaluation_episodes=(),
    )
    only_a = study.run_fit(
        study.Config(version_schedule=("A",), **common),
        arm="fingerprint",
        seed=91,
    )
    a_then_b = study.run_fit(
        study.Config(version_schedule=("A", "B"), **common),
        arm="fingerprint",
        seed=91,
    )
    # The A table receives no B-block updates and is neither aliased nor reset.
    np.testing.assert_array_equal(
        a_then_b["q_values"][0], only_a["q_values"][0]
    )
    initial = study.initialize_q_values(
        study.Config(version_schedule=("A", "B"), **common), "fingerprint"
    )
    assert np.any(a_then_b["q_values"][0] != initial[0])
    assert np.any(a_then_b["q_values"][1] != initial[1])


def test_optimistic_movement_coverage_and_object_identity_are_truthful():
    config = small_config(initialization="reward_upper")
    result = study.run_fit(
        config,
        arm="fingerprint",
        seed=1234,
        object_name="STDL_JOINT_REPLAY_B02",
    )
    summary = result["summary"]
    curves = result["curves"]
    transitions = result["transitions"]
    initial = study.initialize_q_values(config, "fingerprint")
    change = result["q_values"] - initial
    assert summary["object"] == "STDL_JOINT_REPLAY_B02"
    assert summary["movement"]["initial_q_l2"] == np.linalg.norm(initial)
    assert summary["movement"]["initial_q_l2_norm"] == np.linalg.norm(initial)
    assert summary["movement"]["initial_q_nonzero_entries"] == np.count_nonzero(
        initial
    )
    assert summary["movement"]["final_q_l2_movement"] == np.linalg.norm(change)
    assert summary["movement"]["final_changed_q_entries"] == np.count_nonzero(
        change
    )
    assert curves["q_l2_movement"][0] == 0.0
    assert curves["q_changed_entries"][0] == 0
    assert all(value == np.linalg.norm(initial) for value in curves["q_initial_l2_norm"])

    for panel, current_version in zip(
        curves["evaluation_episode"], curves["version_index"]
    ):
        diagnostic = curves["collection_diagnostics"][
            curves["evaluation_episode"].index(panel)
        ]
        stop = panel * config.macros_per_episode
        selected = [
            index for index in range(stop)
            if int(transitions["collection_version"][index]) == current_version
        ]
        assert diagnostic["current_version_sample_count"] == len(selected)
        if not selected:
            assert diagnostic["collected_right_fraction"] is None
            assert diagnostic["distinct_state_action_entries"] == 0
            assert diagnostic["both_actions_state_time_cells"] == 0
            continue
        entries = {
            (
                int(transitions["remaining"][index]),
                int(transitions["start_positions"][index, 0]),
                int(transitions["start_positions"][index, 1]),
                int(transitions["ego_goal"][index]),
            )
            for index in selected
        }
        action_sets = {}
        for remaining, ego, teammate, action in entries:
            action_sets.setdefault((remaining, ego, teammate), set()).add(action)
        right_fraction = np.mean(
            transitions["ego_goal"][selected].astype(np.int64) == study.RIGHT
        )
        assert diagnostic["collected_right_fraction"] == right_fraction
        assert diagnostic["distinct_state_action_entries"] == len(entries)
        assert diagnostic["both_actions_state_time_cells"] == sum(
            actions == {study.LEFT, study.RIGHT} for actions in action_sets.values()
        )

    final_version = curves["version_index"][-1]
    final_q = result["q_values"][final_version]
    final_initial = initial[final_version]
    final_diagnostic = curves["collection_diagnostics"][-1]
    assert final_diagnostic["greedy_right_fraction_nonterminal_cells"] == np.mean(
        np.argmax(final_q[1:], axis=-1) == study.RIGHT
    )
    assert final_diagnostic[
        "changed_current_table_nonterminal_q_entries"
    ] == np.count_nonzero(final_q[1:] != final_initial[1:])
    assert summary["final_collection_diagnostics"] == final_diagnostic
