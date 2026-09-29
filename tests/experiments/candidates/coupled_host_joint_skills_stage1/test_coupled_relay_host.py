"""Host contract checks for coupled_host_joint_skills_stage1 b01 (T1).

World seeds used here are outside the declared dev (1000-1031) and hold-out (2000-2031)
panels.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from experiments.candidates.coupled_host_joint_skills_stage1.host import (
    HOST_CONTRACT_KWARGS,
    ContractError,
    CoupledRelayHost,
    check_contract,
    contract_denominator,
    make_host,
    static_evaluate,
)

WORLDS = (9101, 9102, 9103)
D_EXPECTED = 6 * 20e6 * math.log2(1.0 + 1000.0)


def _independent_reward(env: CoupledRelayHost) -> dict[str, float]:
    """Contract reward rebuilt from connections / routing_paths / sinr_matrix."""
    connections = np.asarray(env.connections, dtype=bool)
    backhauled = 0
    s_formula = 0.0
    s_method = 0.0
    for i in range(env.n_uavs):
        users = np.flatnonzero(connections[i])
        if users.size == 0 or i not in env.routing_paths:
            continue
        backhauled += users.size
        worst = float(np.min(env.sinr_matrix[i, users]))
        s_formula += env.bandwidth * math.log2(1.0 + 10.0 ** (worst / 10.0))
        s_method += env._compute_uav_frontend_capacity(i, users.tolist())
    c_bh = backhauled / env.n_users
    return {"c_bh": c_bh, "s_formula": s_formula, "s_method": s_method,
            "r": 0.5 * (c_bh + s_formula / D_EXPECTED)}


def _random_placement(env: CoupledRelayHost, rng: np.random.Generator, near_bs: bool) -> np.ndarray:
    positions = np.empty((env.n_uavs, 3))
    if near_bs:
        centre = env.ground_bs_positions[0, :2]
        positions[:, :2] = np.clip(centre + rng.uniform(-1500, 1500, (env.n_uavs, 2)),
                                   0, env.area_size)
    else:
        positions[:, :2] = rng.uniform(0, env.area_size, (env.n_uavs, 2))
    positions[:, 2] = rng.uniform(*env.height_range, env.n_uavs)
    return positions


def test_make_host_contract_constants():
    env = make_host(9101)
    assert isinstance(env, CoupledRelayHost)
    assert env.channel_model == "free_space"
    assert env.max_connections == 10
    assert env.noise_power == -80
    assert env.tx_power == 23
    assert env.min_sinr == 3
    assert env.bandwidth == 20e6
    assert env.ground_bs_tx_power == 23
    assert env.n_uavs == 6 and env.n_users == 50 and env.max_hops == 3
    assert env.area_size == 5000 and env.max_steps == 500
    assert env.ground_bs_positions.tolist() == [[2500.0, 2500.0, 30.0]]
    assert env.a2a_enabled is True
    assert env.world_seed == 9101
    assert make_host(9101, area_size=6000).area_size == 6000


@pytest.mark.parametrize("attribute, value", [
    ("channel_model", "urban"),
    ("max_connections", 12),
    ("noise_power", -90),
    ("tx_power", 20),
])
def test_contract_violation_raises(attribute, value):
    env = make_host(9101)
    setattr(env, attribute, value)
    with pytest.raises(ContractError):
        check_contract(env)


def test_non_free_space_construction_is_refused():
    kwargs = dict(HOST_CONTRACT_KWARGS, channel_model="urban")
    env = CoupledRelayHost(area_size=5000, seed=9101, **kwargs)
    with pytest.raises(ContractError):
        check_contract(env)


def test_denominator_constant():
    env = make_host(9102)
    assert env.contract_denominator_bps == pytest.approx(D_EXPECTED, rel=0, abs=1e-3)
    assert contract_denominator(6, 20e6) == env.contract_denominator_bps
    rng = np.random.default_rng(0)
    for _ in range(10):
        info = static_evaluate(env, _random_placement(env, rng, near_bs=True))
        assert env.contract_denominator_bps == pytest.approx(D_EXPECTED, rel=0, abs=1e-3)
        s_bps = info["frontend_capacity_with_path_mbps"] * 1e6
        assert info["throughput_term"] == pytest.approx(s_bps / D_EXPECTED, rel=1e-12, abs=1e-15)


@pytest.mark.parametrize("world", WORLDS)
def test_reward_formula_matches_independent_recomputation(world):
    env = make_host(world)
    rng = np.random.default_rng(world)
    routed_with_relay = 0
    positive = 0
    for trial in range(60):
        positions = _random_placement(env, rng, near_bs=(trial % 2 == 0))
        info = static_evaluate(env, positions)
        expected = _independent_reward(env)
        assert expected["s_method"] == pytest.approx(expected["s_formula"], rel=1e-12, abs=1e-6)
        assert info["coverage_backhauled"] == pytest.approx(expected["c_bh"], rel=0, abs=1e-15)
        assert info["frontend_capacity_with_path_mbps"] * 1e6 == pytest.approx(
            expected["s_formula"], rel=1e-12, abs=1e-6)
        assert info["contract_reward"] == pytest.approx(expected["r"], rel=1e-12, abs=1e-15)
        assert info["coverage_access"] == pytest.approx(np.sum(env.connections) / env.n_users)
        routed_with_relay += sum(len(path) > 2 for path in env.routing_paths.values())
        positive += info["contract_reward"] > 0
    # The sample exercises routed and relayed states, not only the all-zero plateau.
    assert positive >= 10
    assert routed_with_relay >= 1


@pytest.mark.parametrize("world", WORLDS)
def test_original_reward_is_the_parent_value(world):
    host = make_host(world)
    plain = UAVCooperativeNetworkEnv(area_size=5000, seed=world, **HOST_CONTRACT_KWARGS)
    rng = np.random.default_rng(world + 7)
    for _ in range(20):
        positions = _random_placement(host, rng, near_bs=True)
        info = static_evaluate(host, positions)
        plain.uav_positions = positions.copy()
        plain._begin_path_loss_step()
        plain._update_channel_state()
        plain._update_uav_connections()
        plain._compute_routing_paths()
        original = plain._compute_reward()
        assert info["original_normalized_reward"] == original
        assert info["avg_hops"] == plain.reward_info["avg_hops"]
        assert np.array_equal(host.connections, plain.connections)
        assert host.routing_paths == plain.routing_paths


def _inject_state(env: CoupledRelayHost, sinr_db: float) -> None:
    connections = np.zeros((env.n_uavs, env.n_users), dtype=bool)
    for j in range(env.n_users):
        connections[j % env.n_uavs, j] = True
    env.connections = connections
    env.sinr_matrix = np.full((env.n_uavs, env.n_users), float(sinr_db))
    env.routing_paths = {i: [("uav", i), ("ground_bs", 0)] for i in range(env.n_uavs)}


def test_reward_is_not_clipped():
    env = make_host(9101)
    _inject_state(env, sinr_db=40.0)
    reward = env._compute_reward()
    assert env.reward_info["coverage_backhauled"] == 1.0
    assert env.reward_info["throughput_term"] > 1.0
    assert reward > 1.0
    assert reward == pytest.approx(0.5 * (1.0 + env.reward_info["throughput_term"]))


def test_reward_monotone_in_s_with_backhauled_coverage_fixed():
    env = make_host(9101)
    _inject_state(env, sinr_db=5.0)
    rewards = []
    for delta in (0.0, 1.0, 3.0, 10.0):
        env.sinr_matrix[0, :] = 5.0 + delta
        rewards.append(env._compute_reward())
        assert env.reward_info["coverage_backhauled"] == 1.0
    assert all(b > a for a, b in zip(rewards, rewards[1:]))


def _relay_line(env: CoupledRelayHost) -> np.ndarray:
    """UAVs on a line east of the BS, 800 m apart: only UAV 0 reaches the BS directly."""
    bs = env.ground_bs_positions[0]
    positions = np.zeros((env.n_uavs, 3))
    for i in range(env.n_uavs):
        positions[i] = [bs[0] + 800.0 * (i + 1), bs[1], 100.0]
    positions[:, 0] = np.clip(positions[:, 0], 0, env.area_size)
    return positions


def test_a2a_disabled_forms_no_uav_links():
    env = make_host(9101, area_size=10000)
    positions = _relay_line(env)
    on = static_evaluate(env, positions, allow_a2a=True)
    assert on["uav_connection_count"] > 0
    assert any(len(path) > 2 for path in env.routing_paths.values())
    routed_on = set(env.routing_paths)

    off = static_evaluate(env, positions, allow_a2a=False)
    assert env.a2a_enabled is False
    assert off["uav_connection_count"] == 0
    assert not env.uav_connections.any()
    assert all(len(path) == 2 for path in env.routing_paths.values())
    assert set(env.routing_paths) == {i for i in range(env.n_uavs) if env.uav_bs_connections[i].any()}
    assert set(env.routing_paths) < routed_on
    assert off["a2a_enabled"] is False and on["a2a_enabled"] is True


def test_a2a_flag_is_live_during_construction():
    env = CoupledRelayHost(area_size=1000, seed=9101, a2a_enabled=False,
                           **HOST_CONTRACT_KWARGS)
    assert not env.uav_connections.any()
    check_contract(env)


@pytest.mark.parametrize("world", WORLDS)
def test_world_seed_determinism(world):
    first = make_host(world)
    second = make_host(world)
    assert np.array_equal(first.user_positions, second.user_positions)
    assert np.array_equal(first.uav_positions, second.uav_positions)
    initial = first.uav_positions.copy()
    users = first.user_positions.copy()
    static_evaluate(first, _random_placement(first, np.random.default_rng(1), near_bs=True))
    first.reset(seed=world)
    assert np.array_equal(first.uav_positions, initial)
    assert np.array_equal(first.user_positions, users)
    other = make_host(world + 1000)
    assert not np.array_equal(other.user_positions, users)


def test_static_evaluate_does_not_advance_step_and_rejects_outside_positions():
    env = make_host(9102)
    env.step({agent: np.zeros(3) for agent in env.agents})
    assert env.current_step == 1
    positions = _random_placement(env, np.random.default_rng(3), near_bs=True)
    static_evaluate(env, positions)
    assert env.current_step == 1
    assert np.array_equal(env.uav_positions, positions)
    bad = positions.copy()
    bad[0, 0] = env.area_size + 1.0
    with pytest.raises(ValueError):
        static_evaluate(env, bad)
    bad = positions.copy()
    bad[0, 2] = env.height_range[1] + 1.0
    with pytest.raises(ValueError):
        static_evaluate(env, bad)


def test_step_reward_is_team_scalar_over_n_uavs():
    env = make_host(9103, area_size=1000)
    rng = np.random.default_rng(5)
    for _ in range(20):
        actions = {agent: rng.uniform(-1, 1, 3) for agent in env.agents}
        _obs, rewards, _terms, _truncs, infos = env.step(actions)
        r = env.reward_info["contract_reward"]
        for agent in env.agents:
            assert rewards[agent] == pytest.approx(r / env.n_uavs, rel=0, abs=1e-15)
        assert infos[env.agents[0]]["reward_info"]["contract_reward"] == r
        # The returned reward uses the routing refreshed after the move (second call).
        expected = _independent_reward(env)
        assert r == pytest.approx(expected["r"], rel=1e-12, abs=1e-15)
