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
