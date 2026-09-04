from __future__ import annotations

import numpy as np
import pytest

from envs.pettingzoo.continuous_alice_bob import ContinuousAliceBobEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from tools.benchmarks import benchmark_uav_path_loss_cache as benchmark


def _assert_nested_equal(reference, optimized):
    if isinstance(reference, dict):
        assert reference.keys() == optimized.keys()
        for key in reference:
            _assert_nested_equal(reference[key], optimized[key])
    elif isinstance(reference, np.ndarray):
        np.testing.assert_array_equal(reference, optimized)
    elif isinstance(reference, (tuple, list)):
        assert len(reference) == len(optimized)
        for first, second in zip(reference, optimized):
            _assert_nested_equal(first, second)
    else:
        assert reference == optimized


def _assert_rng_state_equal(first, second):
    assert first[0] == second[0]
    np.testing.assert_array_equal(first[1], second[1])
    assert first[2:] == second[2:]


@pytest.mark.parametrize(
    ("environment_type", "kwargs"),
    (
        (UAVBaseStationEnv, {"n_uavs": 4, "n_users": 12}),
        (
            UAVCooperativeNetworkEnv,
            {"n_uavs": 4, "n_users": 12, "n_ground_bs": 2},
        ),
        (
            UAVMultiHopEnv,
            {
                "n_uavs": 5,
                "n_users": 15,
                "n_ground_bs": 4,
                "n_clusters": 3,
            },
        ),
    ),
)
@pytest.mark.parametrize("channel_model", ("free_space", "3gpp-36777"))
def test_reference_and_cache_paths_are_bitwise_equivalent(
    environment_type, kwargs, channel_model
):
    reference = environment_type(
        seed=71,
        channel_model=channel_model,
        step_path_loss_cache=False,
        **kwargs,
    )
    optimized = environment_type(
        seed=71,
        channel_model=channel_model,
        step_path_loss_cache=True,
        **kwargs,
    )
    _assert_nested_equal(reference.reset(seed=72), optimized.reset(seed=72))

    actions = {
        agent: np.array([0.01, -0.02, 0.03], dtype=float)
        for agent in reference.agents
    }
    for _ in range(2):
        _assert_nested_equal(reference.step(actions), optimized.step(actions))
        _assert_rng_state_equal(
            reference.np_random.get_state(), optimized.np_random.get_state()
        )


def test_3gpp_realization_is_sampled_once_per_link_and_generation():
    env = MultiUAVEnv(
        n_uavs=2,
        n_users=2,
        seed=9,
        channel_model="3gpp-36777",
        use_shadowing=True,
        step_path_loss_cache=False,
    )
    uav_pos = env.uav_positions[0]
    user_pos = env.user_positions[0]
    state_before = env.np_random.get_state()
    first = env._compute_path_loss(uav_pos, user_pos)
    second = env._compute_path_loss(uav_pos, user_pos)
    assert first == second
    _assert_rng_state_equal(state_before, env.np_random.get_state())

    env._begin_path_loss_step()
    state_before_new_generation = env.np_random.get_state()
    third = env._compute_path_loss(uav_pos, user_pos)
    state_after_new_generation = env.np_random.get_state()
    assert third == env._compute_path_loss(uav_pos, user_pos)
    with pytest.raises(AssertionError):
        _assert_rng_state_equal(state_before_new_generation, state_after_new_generation)
    _assert_rng_state_equal(state_after_new_generation, env.np_random.get_state())


def test_cache_misses_after_position_config_roster_and_step_changes():
    env = MultiUAVEnv(n_uavs=2, n_users=2, seed=5, step_path_loss_cache=True)
    first_pos = env.uav_positions[0].copy()
    second_pos = env.user_positions[0].copy()
    env._compute_path_loss(first_pos, second_pos)
    hits = env._path_loss_cache_hits
    env._compute_path_loss(first_pos, second_pos)
    assert env._path_loss_cache_hits == hits + 1

    misses = env._path_loss_cache_misses
    moved = first_pos.copy()
    moved[0] += 1.0
    env._compute_path_loss(moved, second_pos)
    assert env._path_loss_cache_misses == misses + 1

    misses = env._path_loss_cache_misses
    original_indexed = env._cached_uav_user_path_loss(0, 0)
    env.uav_positions[0, 0] += 2.0
    moved_indexed = env._cached_uav_user_path_loss(0, 0)
    assert env._path_loss_cache_misses == misses + 1
    assert moved_indexed != original_indexed

    misses = env._path_loss_cache_misses
    env.carrier_frequency *= 1.01
    env._compute_path_loss(first_pos, second_pos)
    assert env._path_loss_cache_misses == misses + 1

    misses = env._path_loss_cache_misses
    env.agents = env.agents[:-1]
    env._compute_path_loss(first_pos, second_pos)
    assert env._path_loss_cache_misses == misses + 1

    generation = env._path_loss_cache_generation
    actions = {agent: np.zeros(3, dtype=float) for agent in env.agents}
    env.step(actions)
    assert env._path_loss_cache_generation == generation + 1


def test_environment_seeding_does_not_mutate_global_numpy_rng():
    np.random.seed(20260815)
    state_before = np.random.get_state()
    MultiUAVEnv(n_uavs=2, n_users=4, user_distribution="cluster", seed=1)
    UAVCooperativeNetworkEnv(n_uavs=2, n_users=4, n_ground_bs=10, seed=2)
    UAVMultiHopEnv(
        n_uavs=3,
        n_users=6,
        n_ground_bs=5,
        n_clusters=2,
        seed=3,
    )
    alice_bob = ContinuousAliceBobEnv()
    alice_bob.reset(seed=4)
    _assert_rng_state_equal(state_before, np.random.get_state())


def test_same_seed_is_independent_of_intervening_global_rng_draws():
    first = MultiUAVEnv(
        n_uavs=3,
        n_users=9,
        user_distribution="cluster",
        seed=44,
    )
    np.random.uniform(size=1000)
    second = MultiUAVEnv(
        n_uavs=3,
        n_users=9,
        user_distribution="cluster",
        seed=44,
    )
    np.testing.assert_array_equal(first.uav_positions, second.uav_positions)
    np.testing.assert_array_equal(first.user_positions, second.user_positions)
    np.testing.assert_array_equal(first.sinr_matrix, second.sinr_matrix)


def test_cache_switch_fails_closed_on_non_boolean_values():
    assert MultiUAVEnv(n_uavs=1, n_users=1).step_path_loss_cache is True
    with pytest.raises(TypeError, match="step_path_loss_cache"):
        MultiUAVEnv(step_path_loss_cache="yes")


@pytest.mark.parametrize(
    ("environment_type", "kwargs"),
    (
        (UAVBaseStationEnv, {"n_uavs": 3, "n_users": 6}),
        (
            UAVCooperativeNetworkEnv,
            {"n_uavs": 3, "n_users": 6, "n_ground_bs": 2},
        ),
        (
            UAVMultiHopEnv,
            {
                "n_uavs": 4,
                "n_users": 8,
                "n_ground_bs": 4,
                "n_clusters": 2,
            },
        ),
    ),
)
def test_scenario_raw_and_adapter_reset_step_observation_contracts(
    environment_type, kwargs
):
    raw_environment = environment_type(seed=91, **kwargs)
    raw_observations, _ = raw_environment.reset(seed=92)
    for agent, observation in raw_observations.items():
        observation_space = raw_environment.observation_space(agent)
        assert observation_space.contains(observation)
        assert observation["obs"].dtype == np.float32
        assert observation["action_mask"].dtype == np.float32

    raw_actions = {
        agent: np.zeros(3, dtype=np.float32) for agent in raw_environment.agents
    }
    next_raw_observations = raw_environment.step(raw_actions)[0]
    for agent, observation in next_raw_observations.items():
        observation_space = raw_environment.observation_space(agent)
        assert observation_space.contains(observation)
        assert observation["obs"].dtype == np.float32
        assert observation["action_mask"].dtype == np.float32

    adapter = ParallelToArrayAdapter(environment_type(seed=91, **kwargs))
    observations, _ = adapter.reset(seed=92)
    assert observations.shape == adapter.observation_space.shape
    assert observations.dtype == np.float32
    assert adapter.observation_space.contains(observations)

    actions = np.zeros(adapter.action_space.shape, dtype=np.float32)
    next_observations, _, _, _, _ = adapter.step(actions)
    assert next_observations.shape == adapter.observation_space.shape
    assert next_observations.dtype == np.float32
    assert adapter.observation_space.contains(next_observations)


def test_benchmark_contract_runs_bitwise_oracle():
    result = benchmark.run_benchmark(repeats=31)
    assert result["schema"] == "uav_path_loss_cache_benchmark_v2"
    assert result["bitwise_output_and_rng_oracle"] is True
    assert result["repeats"] == 31
    assert result["cases"].keys() == {"scenario1", "scenario2", "scenario3"}
    assert len(result["source_fingerprint"]["digest"]) == 64
    assert len(result["commit_fingerprint"]) in (40, 64)
    assert len(result["configuration_fingerprint"]["digest"]) == 64
    for case in result["cases"].values():
        assert case["reference_median_seconds"] > 0.0
        assert case["optimized_median_seconds"] > 0.0
        assert set(case["rng_fingerprints"]) == {
            "after_reset",
            "after_oracle_step",
        }
        assert all(len(value) == 64 for value in case["rng_fingerprints"].values())


@pytest.mark.parametrize("repeats", (0, 1, 29, 30, 32))
def test_benchmark_rejects_short_or_even_sample_counts(repeats):
    with pytest.raises(ValueError, match="odd integer"):
        benchmark.run_benchmark(repeats=repeats)


def test_benchmark_main_always_fails_a_nonpositive_gate(monkeypatch, capsys):
    monkeypatch.setattr(
        benchmark,
        "run_benchmark",
        lambda **_kwargs: {"optimized_default_eligible": False},
    )
    monkeypatch.setattr(benchmark.sys, "argv", ["benchmark_uav_path_loss_cache.py"])
    assert benchmark.main() == 1
    assert "optimized_default_eligible" in capsys.readouterr().out
