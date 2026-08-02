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


def test_constrained_safety_reward_metrics_are_exposed():
    env = make_env("S7-S3", seed=5)
    env.reset(seed=5)

    _, rewards, _, _, infos = env.step(zero_actions(env))
    reward_info = infos[env.agents[0]]["reward_info"]

    assert reward_info["scenario7_reward_model"] == "constrained_qos_safety_pbrs_v2"
    assert "qos_satisfaction_ratio" in reward_info
    assert "normalized_propulsion_energy" in reward_info
    assert "return_constraint_cost" in reward_info
    assert "return_constraint_cost_raw" in reward_info
    assert reward_info["return_cost_cap"] == 1.0
    assert "return_risk_penalty" in reward_info
    assert "cutoff_event_count" in reward_info
    assert "depletion_event_count" in reward_info
    assert "graph_potential_delta" in reward_info
    assert "instantaneous_bits_per_joule" in reward_info
    assert np.isclose(
        reward_info["scenario7_reward"],
        reward_info["safety_reward_before_pbrs"]
        + reward_info["graph_potential_delta"],
    )
    assert np.isfinite(np.mean(list(rewards.values())))

def test_scalar_qos_demand_seam_is_backwards_equivalent(monkeypatch):
    env = make_env("S7-S1", seed=83)
    try:
        env.reset(seed=83)
        qos_bps = env.user_qos_rate_mbps * 1e6
        raw_rates = np.linspace(0.0, 2.0 * qos_bps, env.n_users)
        monkeypatch.setattr(
            env,
            "_calculate_end_to_end_user_rates",
            lambda: (
                raw_rates.copy(),
                np.zeros((env.n_uavs, env.n_users)),
                np.zeros(env.n_uavs),
            ),
        )
        monkeypatch.setattr(env, "_normalized_step_energy", lambda: (0.0, 0.0))
        monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: np.ones(env.n_uavs))

        metrics = env._calculate_constrained_safety_reward(
            0.0, 0.0, 0.0, 0.0, False, 0.0, {}
        )

        np.testing.assert_array_equal(
            env._current_user_qos_demand_bps(),
            np.full(env.n_users, qos_bps),
        )
        assert np.isclose(
            metrics["task_utility"],
            np.mean(np.clip(raw_rates / qos_bps, 0.0, 1.0)),
        )
        np.testing.assert_array_equal(
            env.last_delivered_traffic_bps,
            np.minimum(raw_rates, qos_bps),
        )
    finally:
        env.close()

def test_end_to_end_rate_respects_access_and_backhaul_and_avoids_soft_handover_double_count(monkeypatch):
    env = make_env("S7-S3", seed=47)
    env.reset(seed=47)
    env.connections[:] = False
    env.connections[0, 0] = True
    env.connections[1, 0] = True
    env.connections[0, 1] = True
    env.routing_paths = {
        0: ([("uav", 0), ("ground_bs", 0)], 6e6),
        1: ([("uav", 1), ("ground_bs", 0)], 2e6),
    }

    def fixed_access(uav_idx, user_idx, bandwidth_hz, relaxed, **_reuse_context):
        capacities = {
            (0, 0): 4e6,
            (0, 1): 4e6,
            (1, 0): 3e6,
        }
        return capacities.get((uav_idx, user_idx), 0.0)

    monkeypatch.setattr(env, "_access_capacity_bps", fixed_access)
    rates, access, backhaul = env._calculate_end_to_end_user_rates()

    # UAV 0 has 8 Mbps access and 6 Mbps backhaul, so both links are scaled to 3 Mbps.
    assert np.isclose(rates[0], 3e6)
    assert np.isclose(rates[1], 3e6)
    # UAV 1 offers only 2 Mbps after backhaul scaling; soft handover takes max, not sum.
    assert np.sum(rates) <= np.sum(np.minimum(np.sum(access, axis=1), backhaul)) + 1e-6
    assert np.isclose(rates[0], max(3e6, 2e6))

def test_graph_pbrs_has_discounted_telescope_boundary():
    env = make_env("S7-S3", seed=53)
    gamma = env.reward_discount_gamma
    potentials = [0.2, 0.5, 0.4, 0.7]
    rewards = [
        env._graph_potential_reward(potentials[t], potentials[t + 1], terminal=False)
        for t in range(len(potentials) - 1)
    ]
    rewards.append(env._graph_potential_reward(potentials[-1], 0.0, terminal=True))

    discounted_sum = sum((gamma ** t) * reward for t, reward in enumerate(rewards))
    assert np.isclose(discounted_sum, -potentials[0])

def test_graph_potential_increases_when_relay_moves_toward_reachable_backhaul(monkeypatch):
    env = make_env("S7-S3", seed=57)
    env.reset(seed=57)
    qos_bps = env.user_qos_rate_mbps * 1e6
    monkeypatch.setattr(
        env,
        "_access_capacity_bps",
        lambda *args, **kwargs: 2.0 * qos_bps,
    )

    bs_xy = env.ground_bs_positions[0, :2].copy()

    def position_based_backhaul(**_reuse_context):
        distances = np.linalg.norm(env.uav_positions[:, :2] - bs_xy, axis=1)
        return np.clip(1.0 - distances / (env.area_size * np.sqrt(2.0)), 0.0, 1.0) * qos_bps

    monkeypatch.setattr(env, "_widest_backhaul_capacities", position_based_backhaul)
    env.uav_positions[:, :2] = env.area_size
    far_potential = env._graph_service_potential()
    env.uav_positions[0, :2] = bs_xy
    near_potential = env._graph_service_potential()

    assert near_potential > far_potential

def test_runtime_safety_dual_changes_only_adaptive_return_penalty():
    env = make_variant_env("qos_adaptive_safety_graph_pbrs", seed=59)
    env.reset(seed=59)
    env.set_scenario7_safety_dual(3.0)
    _, _, _, _, infos = env.step(zero_actions(env))
    metrics = infos[env.agents[0]]["reward_info"]

    assert metrics["safety_dual"] == 3.0
    assert metrics["return_penalty_coefficient"] == 3.0
    assert np.isclose(
        metrics["return_risk_penalty"],
        3.0 * metrics["return_constraint_cost"],
    )

@pytest.mark.parametrize(
    "variant",
    [
        "qos_only",
        "qos_depletion_penalty",
        "qos_fixed_safety",
        "qos_fixed_safety_graph_pbrs",
        "qos_adaptive_safety_graph_pbrs",
    ],
)
def test_reward_ablation_variants_have_explicit_objectives(variant):
    env = make_variant_env(variant, seed=61)
    env.reset(seed=61)
    _, rewards, _, _, infos = env.step(zero_actions(env))
    metrics = infos[env.agents[0]]["reward_info"]
    reward = rewards[env.agents[0]]

    if variant == "qos_only":
        expected = metrics["qos_satisfaction_ratio"]
    elif variant == "qos_depletion_penalty":
        expected = (
            metrics["qos_satisfaction_ratio"]
            - metrics["depletion_event_penalty"]
        )
    elif variant == "qos_fixed_safety":
        expected = metrics["safety_reward_before_pbrs"]
        assert metrics["shaping_potential_delta"] == 0.0
    else:
        expected = (
            metrics["safety_reward_before_pbrs"]
            + metrics["shaping_potential_delta"]
        )

    assert metrics["scenario7_reward_variant"] == variant
    assert np.isclose(reward, expected)

def test_return_constraint_is_zero_for_positive_margins_and_uses_worst_uav(monkeypatch):
    env = make_variant_env("qos_fixed_safety", seed=67)
    env.reset(seed=67)
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
        lambda: np.full(env.n_uavs, 0.01),
    )
    safe = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert safe["return_constraint_cost"] == 0.0

    margins = np.full(env.n_uavs, 0.20)
    margins[3] = -0.05
    monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins)
    unsafe = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert np.isclose(unsafe["return_constraint_cost"], 1.0)
    assert np.isclose(unsafe["return_risk_penalty"], env.lambda_return)

def test_v2_return_risk_is_bounded_even_for_severe_deficit(monkeypatch):
    env = make_arm_env("C", seed=69)
    env.reset(seed=69)
    margins = np.full(env.n_uavs, 0.20)
    margins[5] = -0.25
    monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins)

    metrics = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )

    assert np.isclose(metrics["return_constraint_cost_raw"], 5.0)
    assert metrics["return_constraint_cost"] == 1.0
    assert metrics["return_risk_penalty"] == 2.0
    assert 0.0 <= metrics["return_risk_penalty"] <= 2.0

def test_arm_a_preserves_unbounded_v1_return_risk(monkeypatch):
    env = make_arm_env("A", seed=70)
    env.reset(seed=70)
    margins = np.full(env.n_uavs, 0.20)
    margins[5] = -0.25
    monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins)

    metrics = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )

    assert env.scenario7_reward_model == "constrained_qos_safety_pbrs_v1"
    assert env.battery_capacity_wh == 200.0
    assert np.isinf(metrics["return_cost_cap"])
    assert metrics["return_constraint_cost_raw"] == 5.0
    assert metrics["return_constraint_cost"] == 5.0
    assert metrics["return_risk_penalty"] == 10.0

def test_legacy_ablation_restores_original_reward_weights():
    config = Config("S7-S3")
    config.apply_scenario7_reward_variant("legacy_engineering")

    assert config.w_load_balance == 0.35
    assert config.w_backhaul_outage == 0.8
    assert config.w_energy_motion == 0.02
    assert config.w_charge_progress == 0.20
