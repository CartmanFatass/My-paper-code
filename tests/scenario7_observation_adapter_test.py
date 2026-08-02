import pytest
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

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
