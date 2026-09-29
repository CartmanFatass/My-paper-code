"""Planner, closed-loop executor, floors and gate script (coupled_host_joint_skills_stage1 b01, T2).

World seeds used here are outside the declared dev (1000-1031) and hold-out (2000-2031)
panels.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import experiments.candidates.coupled_host_joint_skills_stage1.planner as planner
from experiments.candidates.coupled_host_joint_skills_stage1.host import make_host, static_evaluate
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    assign_targets,
    build_candidates,
    closed_loop_execute,
    cluster_layout,
    kmeans,
    kmeans_centres,
    link_ranges,
    max_routable_relays,
    plateau_potential,
    random_floor,
    relay_distances,
    relays_needed,
    search_placement,
    stationary_floor,
)

ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "experiments" / "candidates" / "coupled_host_joint_skills_stage1" / "run_gate.py"
DIRECTION = "coupled_host_joint_skills_stage1"


@pytest.fixture
def counted(monkeypatch):
    calls: list[dict] = []
    original = planner.static_evaluate

    def wrapper(env, positions, allow_a2a=True):
        info = original(env, positions, allow_a2a=allow_a2a)
        calls.append({"allow_a2a": allow_a2a, "links": int(env.uav_connections.sum()),
                      "reward": info["contract_reward"]})
        return info

    monkeypatch.setattr(planner, "static_evaluate", wrapper)
    return calls


def test_kmeans_is_deterministic_and_separates_blobs():
    rng = np.random.default_rng(0)
    centres = np.array([[0.0, 0.0], [1000.0, 0.0], [0.0, 1000.0], [1000.0, 1000.0]])
    points = np.concatenate([c + rng.normal(0, 20, (15, 2)) for c in centres])
    a, labels_a = kmeans(points, 4, np.random.default_rng(3))
    b, labels_b = kmeans(points, 4, np.random.default_rng(3))
    assert np.array_equal(a, b) and np.array_equal(labels_a, labels_b)
    found = sorted(map(tuple, np.round(a / 1000.0)))
    assert found == sorted(map(tuple, centres / 1000.0))


def test_candidates_equal_for_equal_rng_and_well_formed():
    env = make_host(9201)
    first = build_candidates(env, np.random.default_rng(9201))
    second = build_candidates(env, np.random.default_rng(9201))
    assert [(c["kind"], c["k"]) for c in first[:3]] == [("kmeans_plain", k) for k in (4, 5, 6)]
    assert all(c["kind"] in ("subset_relay", "subset_flat") for c in first[3:])
    assert any(c["kind"] == "subset_relay" for c in first) and any(c["kind"] == "subset_flat" for c in first)
    assert [c["index"] for c in first] == list(range(len(first)))
    assert len(first) == len(second)
    for a, b in zip(first, second):
        assert np.array_equal(a["positions_xyz"], b["positions_xyz"])
        assert a["positions_xyz"].shape == (env.n_uavs, 3)
        assert np.all(a["positions_xyz"][:, 2] == 100.0)
        assert np.all((a["positions_xyz"][:, :2] >= 0) & (a["positions_xyz"][:, :2] <= 5000))
    k4 = first[0]["positions_xyz"]
    bs = env.ground_bs_positions[0, :2]
    # Plain family: relays (indices 4, 5) at the midpoints of BS -> centroid lines.
    for relay, target in zip(k4[4:], first[0]["relay_targets"]):
        assert np.allclose(relay[:2], 0.5 * (bs + k4[target, :2]))


def test_link_ranges_from_host_constants():
    ranges = link_ranges(make_host(9201))
    # PL_max = 23 + 80 - 3 = 100 dB; FSPL(2 GHz) = 20 log10(d) + 38.46 dB.
    assert ranges["r_link_uav_m"] == pytest.approx(1193.66, abs=0.01)
    assert ranges["r_link_bs_m"] == pytest.approx(ranges["r_link_uav_m"])
    assert ranges["r_direct_horizontal_m"] == pytest.approx(
        np.sqrt(ranges["r_link_bs_m"] ** 2 - 70.0 ** 2))
    assert ranges["relay_spacing_m"] == 1100.0


def _independent_ranges() -> tuple[float, float]:
    """R_link (3-D) and R_direct (horizontal, UAV at 100 m vs BS at 30 m) from first principles."""
    path_loss_max_db = 23.0 - (-80.0) - 3.0  # tx - noise - threshold
    fspl_constant_db = 20.0 * np.log10(4.0 * np.pi * 2e9 / 3e8)
    r_link = 10.0 ** ((path_loss_max_db - fspl_constant_db) / 20.0)
    return r_link, float(np.sqrt(r_link ** 2 - (100.0 - 30.0) ** 2))


def _expected_relays(distance: float, r_direct: float, spacing: float = 1100.0) -> int:
    n = 0
    while r_direct + n * spacing < distance:
        n += 1
    return n


def test_relay_count_fixtures_off_the_boundary():
    _r_link, r_direct = _independent_ranges()
    assert r_direct == pytest.approx(1191.6, abs=0.1)
    assert relays_needed(800.0, r_direct) == _expected_relays(800.0, r_direct) == 0
    assert relays_needed(3000.0, r_direct) == _expected_relays(3000.0, r_direct) == 2
    assert relays_needed(3500.0, r_direct) == _expected_relays(3500.0, r_direct) == 3


@pytest.mark.parametrize("offset", [-1.0, 1.0])
@pytest.mark.parametrize("multiple", [0, 1, 2, 3])
def test_relays_needed_and_spacing(offset, multiple):
    ranges = link_ranges(make_host(9201))
    r_link, r_direct = _independent_ranges()
    assert ranges["r_direct_horizontal_m"] == pytest.approx(r_direct, rel=1e-12)
    assert ranges["r_link_uav_m"] == pytest.approx(r_link, rel=1e-12)
    distance = r_direct + multiple * 1100.0 + offset
    n = relays_needed(distance, ranges["r_direct_horizontal_m"])
    assert n == _expected_relays(distance, r_direct)
    along = relay_distances(distance, n)
    assert len(along) == n
    legs = np.diff([0.0, *along, distance])
    if n:
        assert legs[0] <= r_direct + 1e-9  # BS link
        assert np.all(legs[1:] <= 1100.0 + 1e-9)  # UAV-UAV links
        assert np.all(legs > 0)


def test_router_chains_at_most_max_hops_relays():
    env = make_host(9223, area_size=10000)
    assert max_routable_relays(env) == env.max_hops == 3
    bs = env.ground_bs_positions[0]
    for relays, routed in ((3, True), (4, False)):
        positions = np.array([[bs[0] + 1000.0 * (i + 1), bs[1], 100.0] for i in range(env.n_uavs)])
        service = relays  # UAVs 0..relays-1 are the chain, UAV `relays` is the service end
        positions[service + 1:, :2] = [bs[0], bs[1] - 3000.0]  # park the rest out of range
        static_evaluate(env, positions, allow_a2a=True)
        assert (service in env.routing_paths) is routed
        if routed:
            assert len(env.routing_paths[service]) - 2 == relays


def test_generator_excludes_chains_longer_than_max_hops():
    env = make_host(9223, area_size=10000)
    ranges = link_ranges(env)
    bs = env.ground_bs_positions[0, :2]
    centres = np.array([bs + [3000.0, 0.0], bs + [0.0, 5000.0]])
    clusters = {"centres": centres, "labels": np.array([0] * 25 + [1] * 25),
                "sizes": np.array([25, 25])}
    report: dict = {}
    out = planner._subset_candidates(env, 2, clusters, "relay", ranges, report)
    assert relays_needed(5000.0, ranges["r_direct_horizontal_m"]) == 4 > env.max_hops
    assert [entry["centre"] for entry in report["excluded_centres"]] == [1]
    assert report["excluded_centres"][0]["relays_needed"] == 4
    assert out and all(1 not in candidate["served"] for candidate in out)
    assert [c["relays"] for c in out] == [{0: 2}]


def test_relay_subset_candidates_route_every_served_centre():
    env = make_host(9215)
    candidates = build_candidates(env, np.random.default_rng(9215), allow_a2a=True)
    subsets = [c for c in candidates if c["kind"] == "subset_relay"]
    assert subsets
    r_direct = link_ranges(env)["r_direct_horizontal_m"]
    bs = env.ground_bs_positions[0, :2]
    for candidate in subsets:
        total = sum(1 + n for n in candidate["relays"].values())
        assert total <= env.n_uavs
        assert len(candidate["roles"]) == env.n_uavs
        info = static_evaluate(env, candidate["positions_xyz"], allow_a2a=True)
        assert info["contract_reward"] >= 0
        for position, role in zip(candidate["positions_xyz"], candidate["roles"]):
            if role.startswith("service:") or role.startswith("relay:"):
                # Every service and relay UAV of a served chain has a backhaul path.
                index = [i for i, r in enumerate(candidate["roles"]) if r == role][0]
                assert index in env.routing_paths, (candidate["served"], role)
        for c, n in candidate["relays"].items():
            service = candidate["positions_xyz"][candidate["roles"].index(f"service:{c}")]
            d = np.linalg.norm(service[:2] - bs)
            assert n == relays_needed(d, r_direct)


@pytest.mark.parametrize("world", [9215, 9216, 9217, 9218])
def test_flat_subset_candidates_park_every_centre_within_direct_range(world):
    env = make_host(world)
    r_direct = link_ranges(env)["r_direct_horizontal_m"]
    bs = env.ground_bs_positions[0, :2]
    report: dict = {}
    candidates = build_candidates(env, np.random.default_rng(world), allow_a2a=False, report=report)
    clusters = kmeans_centres(env, np.random.default_rng(world))
    subsets = [c for c in candidates if c["kind"] == "subset_flat"]
    assert report["subset"] == report["subset_flat"] == len(subsets)
    assert report["subset_relay"] == 0 and report["excluded_centre_count"] == 0
    # One UAV per served centre and no relays: every non-empty subset of <= 6 centres, minus
    # layouts that repeat an earlier one (e.g. {A} + 5 leftovers at B == {A, B} + 4 at B).
    assert len(subsets) + report["duplicates_removed"] == sum(2 ** k - 1 for k in (5, 4, 6))
    for candidate in subsets:
        assert all(n == 0 for n in candidate["relays"].values())
        assert not any(role.startswith("relay:") for role in candidate["roles"])
        horizontal = np.linalg.norm(candidate["positions_xyz"][:, :2] - bs, axis=1)
        assert np.all(horizontal <= r_direct - 1.0 + 1e-6)  # every flat UAV keeps direct range
        info = static_evaluate(env, candidate["positions_xyz"], allow_a2a=False)
        assert info["uav_connection_count"] == 0
        assert len(env.routing_paths) == env.n_uavs  # every UAV is routed directly
    far_seen = 0
    for k, cluster in clusters.items():
        for c, centre in enumerate(cluster["centres"]):
            d = np.linalg.norm(centre - bs)
            expected = bs + min(d, r_direct - 1.0) * (centre - bs) / d
            # The singleton layout for this centre exists (possibly first built under
            # another k whose solution shares the centre: duplicates are removed).
            parked = [cand for cand in subsets if cand["k"] == k and cand["served"] == [c]]
            assert len(parked) <= 1
            if parked:
                service = parked[0]["positions_xyz"][parked[0]["roles"].index(f"service:{c}")]
                assert np.allclose(service[:2], expected)
            assert any(np.any(np.all(np.isclose(cand["positions_xyz"][:, :2], expected), axis=1))
                       for cand in subsets)
            far_seen += d > r_direct
    assert far_seen > 0  # these worlds exercise far centres


def test_flat_and_relay_share_kmeans_centres():
    env = make_host(9209, area_size=2500)
    relay = build_candidates(env, np.random.default_rng(9209), allow_a2a=True)
    flat = build_candidates(env, np.random.default_rng(9209), allow_a2a=False)
    for a, b in zip(relay[:3], flat[:3]):
        assert np.array_equal(a["positions_xyz"], b["positions_xyz"])


@pytest.mark.parametrize("world", [9209, 9215, 9301])
def test_flat_candidate_layouts_are_contained_in_relay_candidates_and_distinct(world):
    env = make_host(world)
    relay_report: dict = {}
    relay = build_candidates(env, np.random.default_rng(world), allow_a2a=True, report=relay_report)
    flat = build_candidates(env, np.random.default_rng(world), allow_a2a=False)

    def key(c):
        return np.round(np.asarray(c["positions_xyz"], dtype=float), 6).tobytes()

    relay_keys = [key(c) for c in relay]
    flat_keys = [key(c) for c in flat]
    assert len(set(relay_keys)) == len(relay_keys)  # no duplicate layouts survive
    assert len(set(flat_keys)) == len(flat_keys)
    assert set(flat_keys) <= set(relay_keys)  # the flat search cannot see a layout the relay search lacks
    assert relay_report["subset_relay"] > 0 and relay_report["subset_flat"] > 0
    assert relay_report["total"] == relay_report["plain"] + relay_report["subset"]


@pytest.mark.parametrize("budget", [1, 3, 10, 57, 200, 1000])
@pytest.mark.parametrize("allow_a2a", [True, False])
def test_search_never_exceeds_budget(counted, budget, allow_a2a):
    env = make_host(9202, area_size=1000)
    result = search_placement(env, allow_a2a, budget=budget, rng=np.random.default_rng(1))
    assert result.evaluations == len(counted) <= budget
    assert result.candidates_evaluated == min(budget, len(result.candidates))
    descent_evaluations = sum(start["evaluations"] for start in result.starts)
    assert result.candidates_evaluated + descent_evaluations == result.evaluations
    for start in result.starts:
        assert start["evaluations"] <= start["share"]
        if not start["converged"]:
            assert start["evaluations"] == start["share"]
    assert sum(start["share"] for start in result.starts) == budget - result.candidates_evaluated
    assert len(result.starts) == min(3, result.candidates_evaluated)


def test_multistart_uses_top3_candidates_and_returns_best():
    env = make_host(9219)
    result = search_placement(env, True, budget=600, rng=np.random.default_rng(9219))
    evaluated = result.candidates[: result.candidates_evaluated]
    ranked = sorted(range(len(evaluated)), key=lambda i: (-evaluated[i]["contract_reward"], i))[:3]
    assert [start["candidate_index"] for start in result.starts] == ranked
    assert [start["share"] for start in result.starts] == [
        (600 - len(evaluated)) // 3 + (1 if s < (600 - len(evaluated)) % 3 else 0) for s in range(3)]
    assert result.contract_reward == max(start["final_reward"] for start in result.starts)
    for start in result.starts:
        assert start["final_reward"] >= start["start_reward"]


def test_search_refuses_zero_budget():
    env = make_host(9202)
    with pytest.raises(ValueError):
        search_placement(env, True, budget=0, rng=np.random.default_rng(1))


@pytest.mark.parametrize("world, area", [(9203, 1000), (9204, 2500), (9205, 5000)])
def test_flat_search_never_forms_uav_links(counted, world, area):
    env = make_host(world, area_size=area)
    flat = search_placement(env, False, budget=300, rng=np.random.default_rng(world))
    assert counted and all(call["allow_a2a"] is False and call["links"] == 0 for call in counted)
    assert flat.max_uav_connections_seen == 0
    assert flat.info["uav_connection_count"] == 0
    recheck = static_evaluate(env, flat.positions_xyz, allow_a2a=False)
    assert recheck["contract_reward"] == flat.contract_reward
    assert recheck["uav_connection_count"] == 0


@pytest.mark.parametrize("world, area", [(9206, 1000), (9207, 2500), (9208, 5000)])
def test_descent_never_decreases_accepted_reward(world, area):
    env = make_host(world, area_size=area)
    for allow in (True, False):
        result = search_placement(env, allow, budget=400, rng=np.random.default_rng(world))
        for s in range(len(result.starts)):
            entries = [e for e in result.history if e.get("start") == s]
            assert entries[0]["stage"] == "start"
            for previous, entry in zip(entries, entries[1:]):
                if entry["stage"] == "descent":
                    assert entry["contract_reward"] > previous["contract_reward"]
                else:
                    assert entry["stage"] == "plateau"
                    assert abs(entry["contract_reward"] - previous["contract_reward"]) <= 1e-12
                    assert entry["potential"] < previous["potential"]
            assert entries[-1]["contract_reward"] == result.starts[s]["final_reward"]
        evaluated = result.candidates[: result.candidates_evaluated]
        assert result.contract_reward >= max(c["contract_reward"] for c in evaluated)
        again = static_evaluate(env, result.positions_xyz, allow_a2a=allow)
        assert again["contract_reward"] == result.contract_reward
        assert np.all(result.positions_xyz[:, 2] == 100.0)


def test_plateau_potential_definition():
    env = make_host(9220)
    bs = env.ground_bs_positions[0]
    positions = np.array([
        [bs[0] + 500.0, bs[1], 100.0],     # routed directly
        [bs[0] + 1500.0, bs[1], 100.0],    # routed via UAV 0 when A2A is on
        [bs[0], bs[1] + 2000.0, 100.0],    # unrouted in both modes
        [bs[0] - 2000.0, bs[1], 100.0],    # unrouted
        [bs[0], bs[1] - 2000.0, 100.0],    # unrouted
        [bs[0] + 2000.0, bs[1] + 2000.0, 100.0],  # unrouted
    ])
    static_evaluate(env, positions, allow_a2a=True)
    routed = set(env.routing_paths)
    assert {0, 1} <= routed and not ({2, 3, 4, 5} & routed)
    nodes = [bs] + [positions[i] for i in sorted(routed)]
    expected = sum(min(np.linalg.norm(positions[i] - n) for n in nodes)
                   for i in range(6) if i not in routed)
    assert plateau_potential(env, True) == pytest.approx(expected)
    static_evaluate(env, positions, allow_a2a=False)
    assert set(env.routing_paths) == {0}
    expected_flat = sum(np.linalg.norm(positions[i] - bs) for i in range(1, 6))
    assert plateau_potential(env, False) == pytest.approx(expected_flat)


@pytest.mark.parametrize("allow_a2a", [True, False])
def test_plateau_tie_break_leaves_a_zero_plateau(monkeypatch, allow_a2a):
    env = make_host(9221)
    corner = np.array([[150.0 + 60.0 * i, 150.0, 100.0] for i in range(env.n_uavs)])

    def only_corner(host, rng, allow=True, **kwargs):
        return [{"index": 0, "kind": "constructed", "k": 0, "positions_xyz": corner.copy()}]

    monkeypatch.setattr(planner, "build_candidates", only_corner)
    assert static_evaluate(env, corner, allow_a2a=allow_a2a)["contract_reward"] == 0.0
    result = search_placement(env, allow_a2a, budget=1500, rng=np.random.default_rng(0))
    plateau = [e for e in result.history if e["stage"] == "plateau"]
    assert plateau, "the tie-break never moved off the zero plateau"
    accepted = [e for e in result.history if e["stage"] in ("descent", "plateau")]
    # Without the tie-break no single move leaves the zero plateau: the first accepted moves
    # are plateau moves at reward 0 with strictly falling potential.
    assert accepted[0]["stage"] == "plateau" and accepted[0]["contract_reward"] == 0.0
    first_descent = next(i for i, e in enumerate(accepted) if e["stage"] == "descent")
    assert first_descent > 0
    assert all(e["stage"] == "plateau" and e["contract_reward"] == 0.0
               for e in accepted[:first_descent])
    assert result.starts[0]["accepted_plateau"] == len(plateau)
    # Plateau moves bring UAVs toward the BS until one is routed and the reward rises.
    assert result.contract_reward > 0.0


def test_descent_improves_on_small_arena():
    env = make_host(9210, area_size=1000)
    result = search_placement(env, True, budget=500, rng=np.random.default_rng(9210))
    assert len(result.history) > 1
    assert result.contract_reward >= result.history[0]["contract_reward"]
    assert any(e["stage"] == "descent" for e in result.history)


def test_assign_targets_minimises_makespan():
    initial = np.array([[0.0, 0, 0], [10, 0, 0], [20, 0, 0]])
    targets = np.array([[21.0, 0, 0], [1, 0, 0], [11, 0, 0]])
    perm = assign_targets(initial, targets)
    assert perm.tolist() == [1, 2, 0]


def test_closed_loop_reaches_targets_and_holds():
    env = make_host(9211, area_size=1000)
    result = search_placement(env, True, budget=200, rng=np.random.default_rng(9211))
    run = closed_loop_execute(env, result.positions_xyz)
    assert run["steps"] == env.max_steps == 500
    assert run["arrival_step"] is not None
    stride = env.max_speed * env.time_step
    assert run["arrival_step"] <= int(np.ceil(run["max_travel_distance_m"] / stride)) + 1
    assert run["final_max_distance_to_target_m"] <= 1e-6
    assert sorted(run["target_permutation"]) == list(range(env.n_uavs))
    # Holding: the reward is constant after arrival and equals the static target value
    # (targets are a permutation of the planned set; UAVs are homogeneous).
    tail = np.asarray(run["series"]["contract_reward"][run["arrival_step"] + 1:])
    assert np.allclose(tail, tail[0], rtol=0, atol=1e-12)
    assigned = np.asarray(result.positions_xyz)[run["target_permutation"]]
    static = static_evaluate(env, assigned, allow_a2a=True)["contract_reward"]
    assert tail[-1] == pytest.approx(static, rel=0, abs=1e-12)
    assert run["contract_reward_mean_final100"] == pytest.approx(static, rel=0, abs=1e-12)


def test_closed_loop_starts_from_world_initial_positions():
    env = make_host(9212, area_size=1000)
    initial = env.uav_positions.copy()
    search_placement(env, False, budget=50, rng=np.random.default_rng(1))
    targets = np.full((env.n_uavs, 3), 500.0)
    targets[:, 2] = 100.0
    run = closed_loop_execute(env, targets)
    assert np.array_equal(np.asarray(run["initial_positions_xyz"]), initial)
    assert env.a2a_enabled is True  # restored to the host contract by the episode


@pytest.mark.parametrize("assignment", ["min_makespan", "identity"])
def test_closed_loop_actions_inside_unit_ball(monkeypatch, assignment):
    env = make_host(9222)
    recorded: list[np.ndarray] = []
    moved: list[float] = []
    original_step = env.step

    def recording_step(actions):
        before = env.uav_positions.copy()
        recorded.append(np.stack([np.asarray(actions[a], dtype=float) for a in env.agents]))
        result = original_step(actions)
        moved.append(float(np.max(np.linalg.norm(env.uav_positions - before, axis=1))))
        return result

    monkeypatch.setattr(env, "step", recording_step)
    targets = np.array([[4900.0, 4900.0, 150.0], [100.0, 100.0, 50.0], [4900.0, 100.0, 150.0],
                        [100.0, 4900.0, 50.0], [2500.0, 4900.0, 100.0], [2500.0, 100.0, 100.0]])
    closed_loop_execute(env, targets, max_steps=60, assignment=assignment)
    norms = np.linalg.norm(np.concatenate(recorded), axis=1)
    assert norms.max() <= 1.0 + 1e-12
    assert norms.max() >= 1.0 - 1e-12  # far targets: full speed
    assert max(moved) <= env.max_speed * env.time_step + 1e-9


def test_floors_run():
    env = make_host(9213)
    initial = env.uav_positions.copy()
    still = stationary_floor(env)
    assert still["steps"] == 500
    assert np.array_equal(np.asarray(still["final_positions_xyz"]), initial)
    assert len(set(still["series"]["contract_reward"])) == 1
    noisy_a = random_floor(env, np.random.default_rng(4))
    noisy_b = random_floor(env, np.random.default_rng(4))
    assert noisy_a["steps"] == 500
    assert noisy_a["series"] == noisy_b["series"]
    assert not np.array_equal(np.asarray(noisy_a["final_positions_xyz"]), initial)
    for run in (still, noisy_a):
        assert 0.0 <= run["final"]["far_cluster_backhauled_share"] <= 1.0
        assert run["far_cluster"]["centre_source"] == "generator_replay"


def test_cluster_layout_replay_and_fallback():
    env = make_host(9214)
    layout = cluster_layout(env)
    assert layout["centre_source"] == "generator_replay"
    assert layout["membership"].tolist() == [j // 10 for j in range(50)]
    member_means = np.stack([env.user_positions[layout["membership"] == c].mean(axis=0)
                             for c in range(5)])
    assert np.all(np.linalg.norm(member_means - layout["centres"], axis=1) < 600.0)
    env.reset()  # unseeded: next world from the stream, the replay no longer matches
    assert cluster_layout(env)["centre_source"] == "member_mean"


def _python() -> str:
    return sys.executable


def test_run_gate_smoke_writes_json(tmp_path):
    out = tmp_path / "gate"
    completed = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9301", "9302", "--budget", "30",
         "--out", str(out), "--smoke-no-admission"],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["worlds"] == [9301, 9302]
    assert summary["training_fits_performed"] == 0
    assert summary["launch_sha"] is None
    assert summary["G"]["n"] == 2 and summary["G_C"]["n"] == 2
    assert set(summary["closed_loop"]) == {
        "closed_loop_relay", "closed_loop_flat_a2a_on", "closed_loop_flat_a2a_off_diagnostic",
        "stationary_floor", "random_floor"}
    assert set(summary["closed_loop_labels"]) == set(summary["closed_loop"])
    assert summary["static"]["P_relay"]["evaluations"]["max"] <= 30
    assert summary["cpu_seconds"]["total_s"] > 0
    for world in (9301, 9302):
        row = json.loads((out / "worlds" / f"{world}.json").read_text(encoding="utf-8"))
        assert row["G_world"] == pytest.approx(
            row["static"]["P_relay"]["contract_reward"] - row["static"]["P_flat"]["contract_reward"])
        assert row["static"]["P_flat"]["max_uav_connections_seen"] == 0
        assert set(row["timing"]) >= {"search_relay", "search_flat", "closed_loop_relay",
                                      "closed_loop_flat_a2a_on",
                                      "closed_loop_flat_a2a_off_diagnostic",
                                      "stationary_floor", "random_floor"}
        assert row["closed_loop"]["closed_loop_flat_a2a_on"]["allow_a2a"] is True
        assert row["closed_loop"]["closed_loop_flat_a2a_off_diagnostic"]["allow_a2a"] is False
    # A second run into the same directory is refused without --force.
    again = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9301", "--budget", "3", "--out", str(out),
         "--smoke-no-admission"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert again.returncode == 2


@pytest.mark.parametrize("worlds, out_kind", [
    (["1000"], "temp"), (["2031"], "temp"), (["9301"], "outside"),
])
def test_smoke_path_refuses_panels_and_non_temp_output(tmp_path, worlds, out_kind):
    out = tmp_path / "refused" if out_kind == "temp" else ROOT / "runs" / DIRECTION / "never-created"
    completed = subprocess.run(
        [_python(), str(RUNNER), "--worlds", *worlds, "--budget", "3", "--out", str(out),
         "--smoke-no-admission"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert completed.returncode == 2
    assert not out.exists()


def test_run_gate_without_admission_is_refused(tmp_path):
    completed = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9301", "--budget", "3", "--out",
         str(tmp_path / "x")], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert completed.returncode != 0
    assert not (tmp_path / "x").exists()


def test_run_gate_has_exactly_one_admission_literal():
    from scripts.hmasd_launch import _validate_guard_contract

    _validate_guard_contract(RUNNER, DIRECTION)
    text = RUNNER.read_text(encoding="utf-8")
    assert text.count('require_admission(__file__, direction="coupled_host_joint_skills_stage1")') == 1


def test_parse_worlds():
    from experiments.candidates.coupled_host_joint_skills_stage1.run_gate import parse_worlds

    assert parse_worlds(["1000-1003"]) == [1000, 1001, 1002, 1003]
    assert parse_worlds(["9001", "9002,9003"]) == [9001, 9002, 9003]
    with pytest.raises(ValueError):
        parse_worlds(["5", "5"])
