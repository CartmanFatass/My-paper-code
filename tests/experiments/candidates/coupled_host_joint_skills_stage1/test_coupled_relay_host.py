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


# ------------------------------------------------------------------------------ T3 additions
# Host contract items added by the DM disposition of the Pro review (item 1): use_shadowing pin,
# the unit-ball action clip inside the host, and the T1b fresh-state acceptance tests.


def test_use_shadowing_is_pinned_in_the_contract_kwargs():
    assert HOST_CONTRACT_KWARGS["use_shadowing"] is False
    env = make_host(9104)
    assert env.use_shadowing is False
    env.use_shadowing = True
    with pytest.raises(ContractError):
        check_contract(env)


def test_action_clip_to_unit_ball_counts_events_and_leaves_caller_arrays_untouched():
    env = make_host(9105)
    env.reset(seed=9105)
    # Keep every UAV away from the arena and height boundaries so the displacement is the action.
    env.uav_positions[:, :2] = 2500.0
    env.uav_positions[:, 2] = 100.0
    start = env.uav_positions.copy()
    raw = np.zeros((env.n_uavs, 3), dtype=np.float32)
    raw[0] = [1.0, 1.0, 1.0]            # |a| = sqrt(3): clipped
    raw[1] = [0.6, 0.0, 0.0]            # inside the ball: unchanged
    raw[2] = [0.0, -2.0, 0.0]           # |a| = 2: clipped
    raw[3] = [0.0, 0.0, 0.0]
    raw[4] = [0.6, 0.8, 0.0]            # |a| = 1 exactly: not an event
    raw[5] = [-0.1, 0.2, -0.3]
    actions = {agent: raw[i] for i, agent in enumerate(env.agents)}
    snapshot = raw.copy()
    _obs, _rewards, _terms, _truncs, infos = env.step(actions)
    np.testing.assert_array_equal(raw, snapshot)
    assert all(np.shares_memory(actions[agent], raw) for agent in env.agents)
    moved = env.uav_positions - start
    speed = np.linalg.norm(moved, axis=1)
    assert np.all(speed <= env.max_speed * env.time_step + 1e-4)
    np.testing.assert_allclose(moved[0], 30.0 * np.ones(3) / math.sqrt(3.0), rtol=1e-6)
    np.testing.assert_allclose(moved[1], [18.0, 0.0, 0.0], atol=1e-5)
    np.testing.assert_allclose(moved[2], [0.0, -30.0, 0.0], atol=1e-5)
    np.testing.assert_allclose(moved[4], [18.0, 24.0, 0.0], atol=1e-5)
    assert env.reward_info["action_clip_events"] == 2
    assert infos[env.agents[0]]["reward_info"]["action_clip_events"] == 2
    env.step({agent: np.array([3.0, 0.0, 0.0]) for agent in env.agents})
    assert env.reward_info["action_clip_events"] == 6
    assert env.action_clip_events_episode == 8
    env.reset(seed=9105)
    assert env.action_clip_events_episode == 0


def test_clip_is_identity_inside_the_ball():
    host = make_host(9106)
    plain = UAVCooperativeNetworkEnv(area_size=5000, seed=9106, **HOST_CONTRACT_KWARGS)
    rng = np.random.default_rng(6)
    for _ in range(15):
        raw = rng.uniform(-0.5, 0.5, (host.n_uavs, 3))
        host.step({agent: raw[i] for i, agent in enumerate(host.agents)})
        plain.step({agent: raw[i] for i, agent in enumerate(plain.agents)})
        assert host.reward_info["action_clip_events"] == 0
        np.testing.assert_array_equal(host.uav_positions, plain.uav_positions)
        assert host.routing_paths == plain.routing_paths


BS_XY = (2500.0, 2500.0)
FAR_CORNERS = [(100.0, 100.0, 150.0), (4900.0, 100.0, 150.0), (100.0, 4900.0, 150.0),
               (4900.0, 4900.0, 150.0), (4900.0, 2500.0, 150.0)]


def _designed_users(env: CoupledRelayHost, groups: list[tuple[float, float, int]]) -> None:
    """Static users: listed groups within 40 m of their centres, the rest at (2500, 50)."""
    rng = np.random.default_rng(11)
    users = np.tile([[BS_XY[0], 50.0]], (env.n_users, 1))
    j = 0
    for x, y, count in groups:
        users[j:j + count] = np.array([x, y]) + rng.uniform(-40, 40, (count, 2))
        j += count
    env.user_positions = users


def _fresh_evaluation(world: int, users: np.ndarray, positions: np.ndarray, allow_a2a: bool):
    """A new host that has never seen another placement (no cache, no previous links)."""
    fresh = CoupledRelayHost(area_size=5000, seed=world, a2a_enabled=allow_a2a, **HOST_CONTRACT_KWARGS)
    fresh.user_positions = users.copy()
    fresh.uav_positions = positions.copy()
    fresh._begin_path_loss_step()
    fresh._update_channel_state()
    fresh._update_uav_connections()
    fresh._compute_routing_paths()
    fresh._compute_reward()
    return fresh


def _placement(uav0_x: float, relay_x: float | None = None) -> np.ndarray:
    positions = np.array([(0, 0, 0)] + FAR_CORNERS, dtype=float)
    positions[0] = [BS_XY[0] + uav0_x, BS_XY[1], 100.0]
    if relay_x is not None:
        positions[1] = [BS_XY[0] + relay_x, BS_XY[1], 100.0]
    return positions


def test_fresh_state_order_through_bs_disconnect_and_reconnect():
    world = 9107
    env = make_host(world)
    _designed_users(env, [(BS_XY[0] + 800.0, BS_XY[1], 8), (BS_XY[0] + 1600.0, BS_XY[1], 8)])
    in_range, out_of_range = _placement(800.0), _placement(1600.0)
    readings = []
    for positions in (in_range, out_of_range, in_range, out_of_range):
        info = static_evaluate(env, positions, allow_a2a=True)
        fresh = _fresh_evaluation(world, env.user_positions, positions, allow_a2a=True)
        # Cache invalidation -> SINR/association -> routing -> reward, each equal to a new host's.
        np.testing.assert_array_equal(env.sinr_matrix, fresh.sinr_matrix)
        np.testing.assert_array_equal(env.connections, fresh.connections)
        np.testing.assert_array_equal(env.uav_bs_connections, fresh.uav_bs_connections)
        assert env.routing_paths == fresh.routing_paths
        expected = _independent_reward(env)
        assert info["coverage_backhauled"] == pytest.approx(expected["c_bh"], abs=1e-15)
        assert info["frontend_capacity_with_path_mbps"] * 1e6 == pytest.approx(expected["s_formula"], rel=1e-12)
        assert info["contract_reward"] == fresh.reward_info["contract_reward"]
        readings.append((bool(env.uav_bs_connections[0, 0]), 0 in env.routing_paths, info))
    (link_a, routed_a, info_a), (link_b, routed_b, info_b), (link_c, routed_c, info_c), _ = readings
    assert link_a and routed_a and not link_b and not routed_b and link_c and routed_c
    assert info_a["coverage_backhauled"] > 0 and info_a["throughput_term"] > 0
    assert info_b["coverage_backhauled"] == 0.0 and info_b["throughput_term"] == 0.0
    assert info_b["coverage_access"] > 0.0            # served but not backhauled counts zero
    assert info_c == info_a                           # reconnect restores the same reading


def test_a2a_switch_on_static_updates_relay_rescue():
    world = 9108
    env = make_host(world)
    _designed_users(env, [(BS_XY[0] + 1900.0, BS_XY[1], 8)])
    positions = _placement(1900.0, relay_x=950.0)
    on = static_evaluate(env, positions, allow_a2a=True)
    assert env.routing_paths[0] == [("uav", 0), ("uav", 1), ("ground_bs", 0)]
    assert on["coverage_backhauled"] == pytest.approx(8 / 50)
    fresh_on = _fresh_evaluation(world, env.user_positions, positions, allow_a2a=True)
    assert fresh_on.routing_paths == env.routing_paths
    off = static_evaluate(env, positions, allow_a2a=False)
    assert 0 not in env.routing_paths and not env.uav_connections.any()
    assert off["coverage_backhauled"] == 0.0
    fresh_off = _fresh_evaluation(world, env.user_positions, positions, allow_a2a=False)
    assert fresh_off.routing_paths == env.routing_paths
    assert off["contract_reward"] == fresh_off.reward_info["contract_reward"]


def test_a2a_off_holds_on_every_graph_update_of_a_stepped_episode():
    world = 9109
    off = make_host(world)
    on = make_host(world)
    for env, flag in ((off, False), (on, True)):
        env.a2a_enabled = flag
        env.reset(seed=world)
        assert flag or not env.uav_connections.any()
        static_evaluate(env, _relay_line(env) * [0.5, 1, 1] + [1250, 0, 0], allow_a2a=flag)
    rng = np.random.default_rng(9)
    links_on = 0
    for _ in range(60):
        raw = rng.uniform(-0.3, 0.3, (off.n_uavs, 3))
        off.step({agent: raw[i] for i, agent in enumerate(off.agents)})
        on.step({agent: raw[i] for i, agent in enumerate(on.agents)})
        assert not off.uav_connections.any()
        assert all(len(path) == 2 for path in off.routing_paths.values())
        np.testing.assert_array_equal(off.uav_positions, on.uav_positions)
        links_on += int(on.uav_connections.any())
    assert links_on > 0  # the same trajectory forms links when A2A is on


def test_terminal_step_500_contract_reward_and_flags():
    env = make_host(9110)
    env.reset(seed=9110)
    zero = {agent: np.zeros(3) for agent in env.agents}
    for t in range(1, 501):
        _obs, rewards, terms, truncs, _infos = env.step(zero)
        assert not any(truncs.values())
        assert all(terms.values()) == (t == 500) and any(terms.values()) == (t == 500)
    expected = _independent_reward(env)
    assert env.reward_info["contract_reward"] == pytest.approx(expected["r"], rel=1e-12, abs=1e-15)
    for agent in env.agents:
        assert rewards[agent] * env.n_uavs == pytest.approx(env.reward_info["contract_reward"], abs=1e-12)


def test_uav_without_users_contributes_zero_to_s():
    env = make_host(9101)
    _inject_state(env, sinr_db=12.0)
    env.connections[0, :] = False                       # UAV 0 routed, serves nobody
    with_route = env._compute_reward()
    s_with = env.reward_info["frontend_capacity_with_path_mbps"]
    env.routing_paths.pop(0)
    without_route = env._compute_reward()
    assert env.reward_info["frontend_capacity_with_path_mbps"] == s_with
    assert with_route == without_route
    served = sum(1 for i in range(1, env.n_uavs) if env.connections[i].any())
    per_uav = env.bandwidth * math.log2(1.0 + 10.0 ** 1.2)
    assert s_with * 1e6 == pytest.approx(served * per_uav, rel=1e-12)


def test_max_connections_reached_leaves_the_eleventh_user_unserved():
    env = make_host(9102)
    users = np.tile([[2500.0, 50.0]], (env.n_users, 1))    # 39 users beyond every UAV's reach
    users[:11] = np.array([2700.0, 2500.0]) + np.random.default_rng(2).uniform(-30, 30, (11, 2))
    env.user_positions = users
    positions = _placement(200.0)
    info = static_evaluate(env, positions)
    assert env.connections[0, :11].sum() == 10
    unassigned = [j for j in range(11) if not env.connections[:, j].any()]
    assert len(unassigned) == 1
    assert not env.connections[:, 11:].any()
    assert 0 in env.routing_paths
    assert info["coverage_backhauled"] == pytest.approx(10 / 50)
    assert info["coverage_access"] == pytest.approx(10 / 50)


def test_weak_user_boundary_trade_off_on_the_contract_formula():
    env = make_host(9101)
    n = env.n_uavs
    connections = np.zeros((n, env.n_users), dtype=bool)
    connections[0, :5] = True
    sinr = np.full((n, env.n_users), 20.0)
    sinr[0, 4] = 3.0                                     # the weak user at the threshold
    env.connections, env.sinr_matrix = connections, sinr
    env.routing_paths = {0: [("uav", 0), ("ground_bs", 0)]}
    r_with = env._compute_reward()
    c_with, s_with = env.reward_info["coverage_backhauled"], env.reward_info["throughput_term"]
    env.connections[0, 4] = False                        # drop the weak backhauled user
    r_without = env._compute_reward()
    c_without, s_without = env.reward_info["coverage_backhauled"], env.reward_info["throughput_term"]
    assert c_without - c_with == pytest.approx(-0.02, abs=1e-15)
    delta_s = env.bandwidth * (math.log2(1 + 10 ** 2.0) - math.log2(1 + 10 ** 0.3)) / D_EXPECTED
    assert s_without - s_with == pytest.approx(delta_s, rel=1e-12)
    assert delta_s == pytest.approx(0.0849, abs=5e-4)
    assert r_without - r_with == pytest.approx(0.5 * (-0.02 + delta_s), rel=1e-12)
    assert r_without - r_with == pytest.approx(0.0324, abs=5e-4) and r_without > r_with


def test_original_reward_never_overrides_the_contract_reward():
    from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

    host = make_host(9103)
    adapter = ParallelToArrayAdapter(host, seed=9103)
    adapter.reset(seed=9103)
    rng = np.random.default_rng(13)
    differing = 0
    for _ in range(40):
        _obs, scalar, _term, _trunc, info = adapter.step(rng.uniform(-1, 1, (host.n_uavs, 3)))
        contract = host.reward_info["contract_reward"]
        original = host.reward_info["original_normalized_reward"]
        assert info["reward_info"]["contract_reward"] == contract
        assert info["reward_components"]["reward_info"]["contract_reward"] == contract
        for agent in host.agents:
            assert info["rewards_dict"][agent] == pytest.approx(contract / host.n_uavs, abs=1e-15)
        assert host.n_uavs * scalar == pytest.approx(contract, abs=1e-12)
        differing += not math.isclose(original, contract, abs_tol=1e-9)
    assert differing > 0  # the two rewards differ on real steps, and the contract one is returned
