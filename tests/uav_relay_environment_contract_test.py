"""Stable interface contracts for the relocated UAV relay environments."""

from pathlib import Path
import sys

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

from config_1 import Config
from envs.pettingzoo.relay.belief_map import UAVBeliefMapEnv
from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv
from envs.pettingzoo.relay.progressive import UAVProgressiveRelayEnv
from envs.pettingzoo.relay.routed_core import UAVRoutedRelayEnv
from ha_ctse_process.config import Config as ProcessConfig
from ha_ctse_process.env_factory import EnvSpec, make_env


def make_config():
    config = Config()
    config.max_steps = 2
    return config


def make_forced_relay_environment(seed):
    return UAVForcedRelayEnv(config=make_config(), seed=seed)


def make_belief_map_environment(seed):
    return UAVBeliefMapEnv(
        n_uavs=3,
        n_users=4,
        n_ground_bs=1,
        n_clusters=1,
        max_observed_uavs=3,
        max_observed_users=4,
        max_observed_bs=1,
        max_steps=2,
        seed=seed,
    )


def make_routed_core_environment(seed):
    return UAVRoutedRelayEnv(config=make_config(), seed=seed)


def make_progressive_environment(seed):
    return UAVProgressiveRelayEnv(
        config=make_config(),
        scale_mode="train",
        seed=seed,
    )


ENVIRONMENT_FACTORIES = (
    pytest.param(make_forced_relay_environment, id="forced_relay"),
    pytest.param(make_belief_map_environment, id="belief_map"),
    pytest.param(make_progressive_environment, id="progressive"),
)


LOCAL_VIEW_ENVIRONMENT_FACTORIES = (
    pytest.param(make_forced_relay_environment, id="forced_relay"),
    pytest.param(make_belief_map_environment, id="belief_map"),
    pytest.param(make_routed_core_environment, id="routed_core"),
)


def _assert_distance_order(environment, agent_idx, local_items, positions):
    own_position = environment.uav_positions[agent_idx]
    distances = [np.linalg.norm(own_position - positions[item[0]]) for item in local_items]
    assert distances == sorted(distances)


@pytest.mark.parametrize("make_environment", LOCAL_VIEW_ENVIRONMENT_FACTORIES)
def test_relay_local_view_contract(make_environment):
    seed = 17
    environment_a = make_environment(seed)
    environment_b = make_environment(seed)
    try:
        environment_a.reset(seed=seed)
        environment_b.reset(seed=seed)

        for agent_idx in range(environment_a.n_uavs):
            users_a = environment_a._get_local_users(agent_idx)
            uavs_a = environment_a._get_local_uavs(agent_idx)
            base_stations_a = environment_a._get_local_bs(agent_idx)

            assert users_a == environment_b._get_local_users(agent_idx)
            assert uavs_a == environment_b._get_local_uavs(agent_idx)
            assert base_stations_a == environment_b._get_local_bs(agent_idx)
            assert agent_idx not in [uav_idx for uav_idx, _ in uavs_a]
            _assert_distance_order(environment_a, agent_idx, users_a, environment_a.user_positions)
            _assert_distance_order(environment_a, agent_idx, uavs_a, environment_a.uav_positions)
            _assert_distance_order(environment_a, agent_idx, base_stations_a, environment_a.ground_bs_positions)

        observations_dict = {"uav_0": np.array([1.0], dtype=np.float32)}
        assert environment_a._update_observations_dict(observations_dict) is observations_dict
    finally:
        environment_a.close()
        environment_b.close()


@pytest.mark.parametrize("make_environment", ENVIRONMENT_FACTORIES)
def test_relocated_relay_environment_contract(make_environment):
    seed = 17
    environment_a = make_environment(seed)
    environment_b = make_environment(seed)
    try:
        observations_a, _ = environment_a.reset(seed=seed)
        observations_b, _ = environment_b.reset(seed=seed)

        assert tuple(observations_a) == tuple(observations_b)
        for agent, observation in observations_a.items():
            reference_observation = observations_b[agent]
            observation_space = environment_a.observation_space(agent)

            assert set(observation) == set(reference_observation)
            assert set(observation) == set(observation_space.spaces)
            for field, value in observation.items():
                np.testing.assert_array_equal(value, reference_observation[field])
                assert value.shape == observation_space.spaces[field].shape

            action_space = environment_a.action_space(agent)
            assert action_space.shape

        assert environment_a._get_state().shape == (environment_a.state_dim,)
        actions = {}
        for agent in environment_a.agents:
            action_space = environment_a.action_space(agent)
            action = np.zeros(action_space.shape, dtype=action_space.dtype)
            assert action.shape == action_space.shape
            actions[agent] = action
        transition = environment_a.step(actions)

        assert isinstance(transition, tuple)
        assert len(transition) == 5
        assert all(isinstance(value, dict) for value in transition)
    finally:
        environment_a.close()
        environment_b.close()


def test_belief_map_raw_observations_match_declared_dtype_on_reset_and_step():
    environment = make_belief_map_environment(seed=23)
    try:
        observations, _ = environment.reset(seed=23)
        for agent, observation in observations.items():
            observation_space = environment.observation_space(agent)
            assert observation_space.contains(observation)
            for key, value in observation.items():
                assert value.shape == observation_space.spaces[key].shape
                assert value.dtype == observation_space.spaces[key].dtype

        action = np.zeros(
            environment.action_space("uav_0").shape,
            dtype=environment.action_space("uav_0").dtype,
        )
        observations = environment.step(
            {agent: action.copy() for agent in environment.agents}
        )[0]
        for agent, observation in observations.items():
            observation_space = environment.observation_space(agent)
            assert observation_space.contains(observation)
            for key, value in observation.items():
                assert value.shape == observation_space.spaces[key].shape
                assert value.dtype == observation_space.spaces[key].dtype
    finally:
        environment.close()


def test_belief_map_factory_strict_adapter_accepts_reset_and_next_step():
    environment = make_env(
        ProcessConfig(),
        EnvSpec(scenario="belief_map", seed=29, rank=0, scale_mode="train"),
    )()
    try:
        observations, _ = environment.reset(seed=29)
        assert observations.shape == environment.observation_space.shape
        assert observations.dtype == environment.observation_space.dtype

        action = np.zeros(
            environment.action_space.shape,
            dtype=environment.action_space.dtype,
        )
        next_observations, *_ = environment.step(action)
        assert next_observations.shape == environment.observation_space.shape
        assert next_observations.dtype == environment.observation_space.dtype
    finally:
        environment.close()
