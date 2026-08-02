import numpy as np
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

from config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from tests._scenario7_fixtures import (
    capture_environment_rng_state,
    capture_structured_evidence,
    make_arm_env,
    make_env,
    make_variant_env,
    rng_states_equal,
    zero_actions,
)


def test_cutoff_and_depletion_events_fire_once_per_uav(monkeypatch):
    env = make_variant_env("qos_fixed_safety", seed=71)
    env.reset(seed=71)
    monkeypatch.setattr(
        env,
        "_calculate_end_to_end_user_rates",
        lambda: (
            np.zeros(env.n_users),
            np.zeros((env.n_uavs, env.n_users)),
            np.zeros(env.n_uavs),
        ),
    )
    monkeypatch.setattr(env, "_normalized_step_energy", lambda: (0.0, 0.0))
    monkeypatch.setattr(
        env,
        "_raw_return_energy_margins",
        lambda: np.ones(env.n_uavs),
    )

    env.uav_battery_ratios[0] = env.service_cutoff_threshold * 0.5
    first_cutoff = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    repeated_cutoff = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert first_cutoff["cutoff_event_count"] == 1
    assert repeated_cutoff["cutoff_event_count"] == 0

    env.uav_battery_ratios[0] = 0.0
    first_depletion = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    repeated_depletion = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert first_depletion["cutoff_event_count"] == 0
    assert first_depletion["depletion_event_count"] == 1
    assert repeated_depletion["depletion_event_count"] == 0

@pytest.mark.parametrize("seed", [0, 3, 7])
def test_heuristic_layout_demonstrates_configured_qos_feasibility(seed):
    env = make_env("S7-S3", seed=seed)
    env.reset(seed=seed)
    result = env.estimate_heuristic_qos_feasibility()

    assert result["feasible"]
    assert result["qos_satisfaction_ratio"] >= env.qos_target_ratio

@pytest.mark.parametrize("seed", [0, 1, 2])
def test_rotation_charging_certificate_is_physically_feasible(seed):
    config = Config("S7-S3")
    env = UAVEnergyAwareRelayEnv(config=config, seed=seed)
    env.reset(seed=seed)
    result = env.estimate_rotation_charging_feasibility()

    assert result["effective_charging"]
    assert result["depletion_free"]
    assert (
        result["rotation_qos_satisfaction_ratio"]
        >= config.scenario7_heuristic_qos_min
    )
