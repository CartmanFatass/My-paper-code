"""Guards for the intra-step communication-cache trust window (stage 2 of the
C++ env migration track, docs/project/HANDOFF_CPP_MIGRATION.md).

These tests exercise `envs/pettingzoo/scenario_base.py`'s
`_refresh_step_communication_cache`, `_current_step_communication_cache` and
the base `step()`. They compare an env against itself (or against a
cache-disabled twin at the same seed) -- never against another scenario's
frozen guard, which stays untouched.
"""

import numpy as np
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

from config_1 import Config
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv


def make_env(seed=53):
    config = Config("S7-S1")
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def zero_actions(env):
    return {agent: np.zeros(4, dtype=np.float32) for agent in env.agents}


def test_flag_is_false_after_reset_true_inside_post_channel_phases_false_after_step():
    env = make_env(seed=53)
    try:
        env.reset(seed=53)
        assert not bool(getattr(env, "_intra_step_cache_trusted", False))

        observed_during_routing = []
        original_compute_routing_paths = env._compute_routing_paths

        def wrapper():
            observed_during_routing.append(
                bool(getattr(env, "_intra_step_cache_trusted", False))
            )
            return original_compute_routing_paths()

        env._compute_routing_paths = wrapper

        env.step(zero_actions(env))

        assert observed_during_routing == [True]
        assert not bool(getattr(env, "_intra_step_cache_trusted", False))
    finally:
        env.close()


def test_flag_clears_on_exception_paired_negative_watched_failing_without_finally():
    """The finally in step() must clear the flag even when the step body raises.

    This is the paired negative for that finally: with the finally wiring
    removed, this test goes red because the flag is left True after the
    raised exception. That was watched directly during development (see the
    implementer report) rather than only asserted here.
    """
    env = make_env(seed=61)
    try:
        env.reset(seed=61)

        def raise_instead(*args, **kwargs):
            raise RuntimeError("synthetic failure inside step()")

        env._simulate_packet_flow = raise_instead

        with pytest.raises(RuntimeError):
            env.step(zero_actions(env))

        assert not bool(getattr(env, "_intra_step_cache_trusted", False))
    finally:
        env.close()


def test_outside_step_detection_still_has_full_resolution_to_one_ulp():
    env = make_env(seed=53)
    try:
        env.reset(seed=53)
        env._compute_link_sinr = Mock(wraps=env._compute_link_sinr)

        baseline = env._get_link_capacity("uav", 0, "uav", 1)
        calls_after_baseline = env._compute_link_sinr.call_count
        repeated = env._get_link_capacity("uav", 0, "uav", 1)
        assert repeated == baseline
        assert env._compute_link_sinr.call_count == calls_after_baseline

        original_value = float(env.uav_positions[0, 0])
        env.uav_positions[0, 0] = np.nextafter(original_value, np.inf)
        env._get_link_capacity("uav", 0, "uav", 1)
        assert env._compute_link_sinr.call_count > calls_after_baseline
        calls_after_ulp_change = env._compute_link_sinr.call_count

        env.uav_positions[0, 0] = original_value
        restored = env._get_link_capacity("uav", 0, "uav", 1)
        assert restored == baseline
        assert env._compute_link_sinr.call_count == calls_after_ulp_change
    finally:
        env.close()


def test_mask_flip_outside_step_still_detected():
    env = make_env(seed=53)
    try:
        env.reset(seed=53)
        env._compute_link_sinr = Mock(wraps=env._compute_link_sinr)

        baseline = env._get_link_capacity("uav", 0, "uav", 1)
        calls_after_baseline = env._compute_link_sinr.call_count

        env.uav_failed[2] = True
        env._get_link_capacity("uav", 0, "uav", 1)
        assert env._compute_link_sinr.call_count > calls_after_baseline

        env.uav_failed[2] = False
        restored = env._get_link_capacity("uav", 0, "uav", 1)
        assert restored == baseline
    finally:
        env.close()


def test_trust_window_serves_identical_state_to_a_cache_free_reference():
    env_windowed = make_env(seed=71)
    env_cache_free = make_env(seed=71)
    env_cache_free._disable_step_communication_cache = True
    try:
        env_windowed.reset(seed=71)
        env_cache_free.reset(seed=71)

        for _ in range(3):
            actions = zero_actions(env_windowed)
            env_windowed.step(actions)
            env_cache_free.step(actions)

            np.testing.assert_array_equal(
                env_windowed.sinr_matrix, env_cache_free.sinr_matrix
            )
            np.testing.assert_array_equal(
                env_windowed.connections, env_cache_free.connections
            )
            np.testing.assert_array_equal(
                env_windowed.user_serving_uav, env_cache_free.user_serving_uav
            )
    finally:
        env_windowed.close()
        env_cache_free.close()
