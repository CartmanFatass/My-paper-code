import pytest
import sys
import numpy as np
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
gym = pytest.importorskip("gymnasium")

from _scenario7_fixtures import (
    capture_structured_evidence,
    make_env,
    rng_states_equal,
    zero_actions,
)
from config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from train_multiproc_config_1 import validate_scenario7_configuration


class _FixedObservationParallelEnv:
    """Small Parallel API fixture for adapter input-contract checks."""

    possible_agents = ("uav_0", "uav_1")

    def __init__(self):
        self._observation_spaces = {
            agent: gym.spaces.Dict(
                {
                    "obs": gym.spaces.Box(
                        low=-np.inf,
                        high=np.inf,
                        shape=(3,),
                        dtype=np.float32,
                    )
                }
            )
            for agent in self.possible_agents
        }
        self._action_spaces = {
            agent: gym.spaces.Discrete(2) for agent in self.possible_agents
        }

    def get_state_dim(self):
        return 2

    def get_obs_dim(self):
        return 3

    def observation_space(self, agent):
        return self._observation_spaces[agent]

    def action_space(self, agent):
        return self._action_spaces[agent]

    def reset(self, *, seed=None, options=None):
        del seed, options
        return self._valid_observations(), {}

    def step(self, actions):
        del actions
        # PettingZoo may omit an observation for an agent that has just ended.
        return (
            {"uav_0": {"obs": np.array([1.0, 2.0, 3.0], dtype=np.float32)}},
            {"uav_0": 0.0, "uav_1": 0.0},
            {"uav_0": False, "uav_1": True},
            {"uav_0": False, "uav_1": False},
            {"uav_0": {}, "uav_1": {}},
        )

    def _get_state(self):
        return np.zeros(2, dtype=np.float32)

    def close(self):
        return None

    @staticmethod
    def _valid_observations():
        return {
            "uav_0": {"obs": np.array([1.0, 2.0, 3.0], dtype=np.float32)},
            "uav_1": {"obs": np.array([4.0, 5.0, 6.0], dtype=np.float32)},
        }


def _adapter_fixture():
    return ParallelToArrayAdapter(_FixedObservationParallelEnv())


def test_adapter_preserves_valid_fixed_team_observations():
    adapter = _adapter_fixture()
    try:
        observations = adapter._dict_to_array(
            _FixedObservationParallelEnv._valid_observations()
        )
        np.testing.assert_array_equal(
            observations,
            np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32),
        )
        assert observations.dtype == np.float32
    finally:
        adapter.close()


@pytest.mark.parametrize(
    ("payload", "exception"),
    [
        (None, TypeError),
        ({"uav_0": {"obs": np.ones(3, dtype=np.float32)}}, ValueError),
        (
            {
                "uav_0": {"obs": np.ones(3, dtype=np.float32)},
                "uav_1": {"obs": np.ones(3, dtype=np.float32)},
                "unknown": {"obs": np.ones(3, dtype=np.float32)},
            },
            ValueError,
        ),
        (
            {
                "uav_0": {"obs": None},
                "uav_1": {"obs": np.ones(3, dtype=np.float32)},
            },
            ValueError,
        ),
        (
            {
                "uav_0": {},
                "uav_1": {"obs": np.ones(3, dtype=np.float32)},
            },
            ValueError,
        ),
        (
            {
                "uav_0": {"obs": np.ones(2, dtype=np.float32)},
                "uav_1": {"obs": np.ones(3, dtype=np.float32)},
            },
            ValueError,
        ),
        (
            {
                "uav_0": {"obs": np.ones(3, dtype=np.float64)},
                "uav_1": {"obs": np.ones(3, dtype=np.float32)},
            },
            TypeError,
        ),
        (
            {
                "uav_0": {"obs": np.array([0.0, np.nan, 1.0], dtype=np.float32)},
                "uav_1": {"obs": np.ones(3, dtype=np.float32)},
            },
            ValueError,
        ),
    ],
)
def test_adapter_rejects_malformed_or_nonfinite_active_observations(
    payload, exception
):
    adapter = _adapter_fixture()
    try:
        with pytest.raises(exception):
            adapter._dict_to_array(payload)
    finally:
        adapter.close()


def test_adapter_terminal_padding_is_explicit_and_never_pads_active_agents():
    adapter = _adapter_fixture()
    try:
        padded = adapter._dict_to_array(
            {"uav_0": {"obs": np.array([1.0, 2.0, 3.0], dtype=np.float32)}},
            terminal_agents={"uav_1"},
        )
        np.testing.assert_array_equal(
            padded,
            np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]], dtype=np.float32),
        )
        with pytest.raises(ValueError, match="active agent 'uav_0'"):
            adapter._dict_to_array({}, terminal_agents={"uav_1"})
    finally:
        adapter.close()


def test_adapter_step_uses_explicit_terminal_padding_from_transition_flags():
    adapter = _adapter_fixture()
    try:
        observations, _, terminated, truncated, _ = adapter.step(
            np.array([0, 0], dtype=np.int64)
        )
        assert terminated
        assert not truncated
        np.testing.assert_array_equal(
            observations,
            np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]], dtype=np.float32),
        )
    finally:
        adapter.close()


def test_observation_and_state_use_fixed_team_and_station_identity():
    env = make_env("S7-S3", seed=31)
    observations, _ = env.reset(seed=31)
    agent = env.agents[0]

    assert env.n_uavs == 8
    assert env.max_energy_observed_uavs == 8
    assert observations[agent]["obs"].shape == (env.obs_dim,)
    assert env._get_state().shape == (env.state_dim,)
    assert env.energy_obs_extra_dim == 8 * 13 + 2 * 8


def test_startup_validation_accepts_parallel_array_adapter():
    config = Config("S7-S3")
    raw_env = UAVEnergyAwareRelayEnv(config=config, seed=43)
    adapter = ParallelToArrayAdapter(raw_env, seed=43)
    args = SimpleNamespace(scenario="energy", config="config_1")
    try:
        validate_scenario7_configuration(config, args, env=adapter)
    finally:
        adapter.close()


def test_scenario7_skips_discarded_base_views_without_changing_transitions():
    fast = make_env("S7-S1", seed=45)
    reference = make_env("S7-S1", seed=45)
    assert getattr(fast, "_defer_base_view_materialization", False)
    reference._defer_base_view_materialization = False

    fast._get_observation = Mock(wraps=fast._get_observation)
    reference._get_observation = Mock(wraps=reference._get_observation)
    fast._get_state = Mock(wraps=fast._get_state)
    reference._get_state = Mock(wraps=reference._get_state)
    try:
        fast_reset = fast.reset(seed=45)
        reference_reset = reference.reset(seed=45)
        assert capture_structured_evidence(fast_reset) == capture_structured_evidence(
            reference_reset
        )
        assert fast._get_observation.call_count == fast.n_uavs
        assert reference._get_observation.call_count == 2 * reference.n_uavs
        assert fast._get_state.call_count == 1
        assert reference._get_state.call_count == 2

        fast._get_observation.reset_mock()
        reference._get_observation.reset_mock()
        fast._get_state.reset_mock()
        reference._get_state.reset_mock()
        actions = zero_actions(fast)
        fast_step = fast.step(actions)
        reference_step = reference.step(zero_actions(reference))

        assert capture_structured_evidence(fast_step) == capture_structured_evidence(
            reference_step
        )
        assert fast._get_observation.call_count == fast.n_uavs
        assert reference._get_observation.call_count == 2 * reference.n_uavs
        assert fast._get_state.call_count == 1
        assert reference._get_state.call_count == 2
        assert rng_states_equal(
            capture_structured_evidence(fast.np_random.get_state()),
            capture_structured_evidence(reference.np_random.get_state()),
        )
    finally:
        fast.close()
        reference.close()
