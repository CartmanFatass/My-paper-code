"""Parallel API conformance, lifecycle, reproducibility and snapshots."""

from __future__ import annotations

import numpy as np
import pytest
from gymnasium.spaces import Box
from pettingzoo.test import parallel_api_test

from envs.uav_service_restoration import UAVServiceRestorationEnv, config_from_dict
from envs.uav_service_restoration.env import REWARD_INFO_FIELDS, TRAINING_INFO_FIELDS


def make(config, **kwargs):
    return UAVServiceRestorationEnv(config, **kwargs)


def zero_actions(env):
    return {agent: np.zeros(3, dtype=np.float32) for agent in env.agents}


def run_episode(env, seed=7, controller=None):
    env.reset(seed=seed)
    rewards = []
    steps = 0
    while env.agents:
        actions = controller(env) if controller else zero_actions(env)
        _, reward, terminated, truncated, _ = env.step(actions)
        rewards.append(float(next(iter(reward.values()))))
        steps += 1
    return steps, rewards, terminated, truncated


# --------------------------------------------------------------------------------------
# API conformance
# --------------------------------------------------------------------------------------


def test_parallel_api_test_passes(short_config):
    parallel_api_test(make(short_config), num_cycles=12)


def test_spaces_are_the_same_objects_across_calls(short_config):
    env = make(short_config)
    for agent in env.possible_agents:
        assert env.observation_space(agent) is env.observation_space(agent)
        assert env.action_space(agent) is env.action_space(agent)


def test_space_shapes_and_dtypes(short_config):
    env = make(short_config)
    observation_space = env.observation_space(env.possible_agents[0])
    action_space = env.action_space(env.possible_agents[0])
    assert isinstance(observation_space, Box) and observation_space.dtype == np.float32
    assert isinstance(action_space, Box) and action_space.dtype == np.float32
    assert action_space.shape == (3,)
    assert float(action_space.low.min()) == -1.0
    assert float(action_space.high.max()) == 1.0
    assert observation_space.shape == (env.get_obs_dim(),)
    assert env.state_space.shape == (env.get_state_dim(),)


def test_reset_returns_observations_and_infos_for_every_agent(short_config):
    env = make(short_config)
    observations, infos = env.reset(seed=3)
    assert set(observations) == set(env.possible_agents)
    assert set(infos) == set(env.possible_agents)
    for agent, observation in observations.items():
        assert observation.dtype == np.float32
        assert observation.shape == (env.get_obs_dim(),)
        assert np.isfinite(observation).all()
        assert set(infos[agent]) <= set(TRAINING_INFO_FIELDS)


def test_state_is_float32_and_finite(short_config):
    env = make(short_config)
    env.reset(seed=3)
    state = env.state()
    assert state.dtype == np.float32
    assert state.shape == (env.get_state_dim(),)
    assert np.isfinite(state).all()
    np.testing.assert_array_equal(state, env._get_state())  # noqa: SLF001


def test_options_are_tolerated(short_config):
    env = make(short_config)
    env.reset(seed=0, options={"options": 1})
    assert env.agents


# --------------------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------------------


def test_continuing_task_truncates_and_never_terminates(short_config):
    env = make(short_config)
    steps, _, terminated, truncated = run_episode(env)
    assert steps == short_config.n_decision_steps
    assert all(truncated.values())
    assert not any(terminated.values())
    assert env.agents == []


def test_finite_horizon_semantics_terminate_instead(config_doc):
    config_doc["episode"]["duration_s"] = 40.0
    config_doc["episode"]["semantics"] = "finite_horizon"
    env = make(config_from_dict(config_doc))
    _, _, terminated, truncated = run_episode(env)
    assert all(terminated.values())
    assert not any(truncated.values())


def test_the_real_terminal_observation_is_returned(short_config):
    env = make(short_config)
    env.reset(seed=11)
    final_observations = None
    while env.agents:
        observations, _, _, truncated, _ = env.step(zero_actions(env))
        if any(truncated.values()):
            final_observations = observations
    assert final_observations is not None
    assert set(final_observations) == set(env.possible_agents)
    for observation in final_observations.values():
        # Not zero padding: the terminal observation is the state before the boundary.
        assert np.isfinite(observation).all()
        assert np.abs(observation).sum() > 0.0
    # The post-reset observation differs from the retained terminal one.
    after_reset, _ = env.reset(seed=11)
    assert not np.allclose(after_reset["uav_0"], final_observations["uav_0"])


def test_no_implicit_second_reset_inside_a_decision_interval(short_config):
    env = make(short_config)
    run_episode(env)
    with pytest.raises(RuntimeError, match="after every agent finished"):
        env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.possible_agents})


def test_missing_and_unknown_agent_actions_are_refused(short_config):
    env = make(short_config)
    env.reset(seed=1)
    with pytest.raises(ValueError, match="missing actions"):
        env.step({"uav_0": np.zeros(3, dtype=np.float32)})
    actions = zero_actions(env)
    actions["uav_99"] = np.zeros(3, dtype=np.float32)
    with pytest.raises(ValueError, match="unknown agents"):
        env.step(actions)


def test_reset_clears_telemetry_events_and_metrics(short_config):
    env = make(short_config)
    run_episode(env)
    finished = env.episode_summary()
    assert finished["total_time_s"] > 0.0
    env.reset(seed=7)
    fresh = env.episode_summary()
    assert fresh["total_time_s"] == 0.0
    assert fresh["delivered_mbit_total"] == 0.0
    assert env.physical_time_s == 0.0
    assert env._store.pending == []  # noqa: SLF001


# --------------------------------------------------------------------------------------
# Reward contract
# --------------------------------------------------------------------------------------


def test_every_agent_receives_the_identical_team_reward(short_config):
    env = make(short_config)
    env.reset(seed=5)
    _, rewards, _, _, _ = env.step(zero_actions(env))
    values = list(rewards.values())
    assert len(values) == short_config.n_uavs
    assert all(value == values[0] for value in values)


def test_the_mean_over_agents_equals_the_team_reward(short_config):
    """The shared adapter averages agent rewards; that average must be ``r`` itself."""

    env = make(short_config)
    env.reset(seed=5)
    _, rewards, _, _, _ = env.step(zero_actions(env))
    assert float(np.mean(list(rewards.values()))) == pytest.approx(
        float(next(iter(rewards.values()))), abs=0.0
    )


def test_reward_is_the_negative_normalised_unmet_integral(short_config):
    env = make(short_config)
    env.reset(seed=5)
    _, rewards, _, _, infos = env.step(zero_actions(env))
    info = infos["uav_0"]["reward_info"]
    assert set(info) == set(REWARD_INFO_FIELDS)
    expected = -info["unmet_mbit_interval"] / (
        short_config.reward.reference_scale_mbps * short_config.reward.reference_dt_s
    )
    assert info["service_term"] == pytest.approx(expected)
    assert info["motion_term"] == 0.0  # motion_weight is zero in the preset
    assert float(rewards["uav_0"]) == pytest.approx(info["reward_total"])
    assert info["unmet_mbit_interval"] >= 0.0
    assert info["delivered_mbit_interval"] <= info["offered_mbit_interval"] + 1e-9


def test_motion_penalty_is_applied_when_configured(config_doc):
    config_doc["episode"]["duration_s"] = 20.0
    config_doc["reward"]["motion_weight"] = 0.5
    config_doc["reward"]["motion_weight_rationale"] = "test: confirm the term is wired"
    env = make(config_from_dict(config_doc))
    env.reset(seed=5)
    actions = {agent: np.array([1.0, 0.0, 0.0], dtype=np.float32) for agent in env.agents}
    _, rewards, _, _, infos = env.step(actions)
    info = infos["uav_0"]["reward_info"]
    assert info["motion_effort_integral_s"] > 0.0
    assert info["motion_term"] < 0.0
    assert float(rewards["uav_0"]) == pytest.approx(
        info["service_term"] + info["motion_term"]
    )


# --------------------------------------------------------------------------------------
# Reproducibility, isolation and snapshots
# --------------------------------------------------------------------------------------


def test_same_seed_reproduces_the_same_episode(short_config):
    first = make(short_config)
    second = make(short_config)
    observations_a, _ = first.reset(seed=4242)
    observations_b, _ = second.reset(seed=4242)
    np.testing.assert_array_equal(observations_a["uav_0"], observations_b["uav_0"])
    assert (
        first.episode_descriptor.episode_id == second.episode_descriptor.episode_id
    )
    assert first.event_schedule.summary() == second.event_schedule.summary()

    rewards_a, rewards_b = [], []
    generator = np.random.default_rng(1)
    plan = [
        generator.uniform(-1, 1, (short_config.n_uavs, 3))
        for _ in range(short_config.n_decision_steps)
    ]
    for step in plan:
        actions = {
            agent: step[index].astype(np.float32)
            for index, agent in enumerate(first.possible_agents)
        }
        _, reward_a, _, _, _ = first.step(actions)
        _, reward_b, _, _, _ = second.step(actions)
        rewards_a.append(reward_a["uav_0"])
        rewards_b.append(reward_b["uav_0"])
    assert rewards_a == rewards_b


def test_different_policies_do_not_alter_the_exogenous_process(short_config):
    still = make(short_config)
    moving = make(short_config)
    still.reset(seed=808)
    moving.reset(seed=808)
    assert still.event_schedule.summary() == moving.event_schedule.summary()
    assert still.episode_descriptor == moving.episode_descriptor

    generator = np.random.default_rng(3)
    while still.agents and moving.agents:
        still.step(zero_actions(still))
        moving.step(
            {
                agent: generator.uniform(-1, 1, 3).astype(np.float32)
                for agent in moving.agents
            }
        )
    # Same exogenous world: identical offered demand, identical events.
    np.testing.assert_allclose(
        still.episode_summary()["offered_mbit_per_point"],
        moving.episode_summary()["offered_mbit_per_point"],
        rtol=0.0,
        atol=1e-9,
    )
    assert still.event_schedule.summary() == moving.event_schedule.summary()
    # ...and genuinely different behaviour, or the comparison proves nothing.
    assert moving.episode_summary()["flight_distance_m_total"] > 0.0
    assert still.episode_summary()["flight_distance_m_total"] == 0.0


def test_instances_are_isolated(short_config):
    first = make(short_config)
    second = make(short_config)
    first.reset(seed=1)
    second.reset(seed=2)
    for _ in range(3):
        first.step(
            {agent: np.array([1.0, 0.0, 0.0], dtype=np.float32) for agent in first.agents}
        )
    before = second.uav_positions_m.copy()
    second.step(zero_actions(second))
    np.testing.assert_allclose(second.uav_positions_m, before, atol=1e-12)
    assert not np.allclose(first.uav_positions_m, before)


def test_global_numpy_state_is_untouched(short_config):
    np.random.seed(99)
    before = np.random.get_state()
    env = make(short_config)
    run_episode(env, seed=17)
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_rng_streams_are_independent(short_config):
    env = make(short_config)
    env.reset(seed=5)
    names = set(env._rngs)  # noqa: SLF001
    assert {"episode", "layout", "events", "observation_noise", "channel"} == names
    states = [
        env._rngs[name].bit_generator.state["state"]["state"]  # noqa: SLF001
        for name in sorted(names)
    ]
    assert len(set(states)) == len(states)


def test_snapshot_restores_and_continues_identically(short_config):
    env = make(short_config)
    env.reset(seed=606)
    generator = np.random.default_rng(11)
    plan = [generator.uniform(-1, 1, (short_config.n_uavs, 3)) for _ in range(4)]
    env.step({a: plan[0][i].astype(np.float32) for i, a in enumerate(env.possible_agents)})
    snapshot = env.get_probe_snapshot()

    reference = []
    for step in plan[1:]:
        _, reward, _, _, _ = env.step(
            {a: step[i].astype(np.float32) for i, a in enumerate(env.possible_agents)}
        )
        reference.append(reward["uav_0"])

    restored = make(short_config)
    restored.reset(seed=606)
    restored.set_probe_snapshot(snapshot)
    replayed = []
    for step in plan[1:]:
        _, reward, _, _, _ = restored.step(
            {a: step[i].astype(np.float32) for i, a in enumerate(restored.possible_agents)}
        )
        replayed.append(reward["uav_0"])
    assert replayed == reference


def test_snapshot_refuses_a_different_dataset_identity(short_config, config_doc):
    env = make(short_config)
    env.reset(seed=1)
    snapshot = env.get_probe_snapshot()
    snapshot["dataset_hash"] = "0" * 64
    with pytest.raises(ValueError, match="different dataset content hash"):
        env.set_probe_snapshot(snapshot)
    snapshot["dataset_hash"] = env.demand_source.metadata().dataset_hash
    snapshot["schema"] = "something.else"
    with pytest.raises(ValueError, match="schema mismatch"):
        env.set_probe_snapshot(snapshot)


def test_render_and_diagnostic_reads_do_not_advance_time_or_rng(short_config):
    env = make(short_config)
    env.reset(seed=77)
    env.step(zero_actions(env))
    time_before = env.physical_time_s
    rng_before = {
        name: generator.bit_generator.state
        for name, generator in env._rngs.items()  # noqa: SLF001
    }
    for _ in range(5):
        env.render()
        env.state()
        env.get_current_state()
        env.get_privileged_diagnostics()
        env.episode_summary()
    assert env.physical_time_s == time_before
    assert {
        name: generator.bit_generator.state
        for name, generator in env._rngs.items()  # noqa: SLF001
    } == rng_before


def test_consecutive_resets_without_a_seed_advance_the_episode(short_config):
    env = make(short_config)
    env.reset(seed=500)
    first = env.episode_descriptor.episode_id
    ids = {first}
    for _ in range(6):
        env.reset()
        ids.add(env.episode_descriptor.episode_id)
    assert len(ids) > 1
    env.reset(seed=500)
    assert env.episode_descriptor.episode_id == first
