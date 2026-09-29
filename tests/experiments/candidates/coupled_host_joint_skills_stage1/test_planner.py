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
    random_floor,
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
    assert [c["k"] for c in first] == [4, 5, 6]
    for a, b in zip(first, second):
        assert np.array_equal(a["positions_xyz"], b["positions_xyz"])
        assert np.all(a["positions_xyz"][:, 2] == 100.0)
        assert np.all((a["positions_xyz"][:, :2] >= 0) & (a["positions_xyz"][:, :2] <= 5000))
    k4 = first[0]["positions_xyz"]
    bs = env.ground_bs_positions[0, :2]
    # Relays (indices 4, 5) sit at the midpoints of BS -> centroid lines.
    for relay, target in zip(k4[4:], first[0]["relay_targets"]):
        assert np.allclose(relay[:2], 0.5 * (bs + k4[target, :2]))


@pytest.mark.parametrize("budget", [3, 10, 57, 200])
@pytest.mark.parametrize("allow_a2a", [True, False])
def test_search_never_exceeds_budget(counted, budget, allow_a2a):
    env = make_host(9202, area_size=1000)
    result = search_placement(env, allow_a2a, budget=budget, rng=np.random.default_rng(1))
    assert result.evaluations == len(counted) <= budget
    if not result.converged:
        assert result.evaluations == budget


def test_search_refuses_budget_below_candidates():
    env = make_host(9202)
    with pytest.raises(ValueError):
        search_placement(env, True, budget=2, rng=np.random.default_rng(1))


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
        rewards = [entry["contract_reward"] for entry in result.history]
        assert all(b > a for a, b in zip(rewards, rewards[1:]))
        assert result.contract_reward == rewards[-1]
        assert result.contract_reward >= max(c["contract_reward"] for c in result.candidates)
        again = static_evaluate(env, result.positions_xyz, allow_a2a=allow)
        assert again["contract_reward"] == result.contract_reward
        assert np.all(result.positions_xyz[:, 2] == 100.0)


def test_relay_and_flat_share_candidates():
    env = make_host(9209, area_size=2500)
    relay = search_placement(env, True, budget=50, rng=np.random.default_rng(9209))
    flat = search_placement(env, False, budget=50, rng=np.random.default_rng(9209))
    for a, b in zip(relay.candidates, flat.candidates):
        assert np.array_equal(a["positions_xyz"], b["positions_xyz"])


def test_descent_improves_on_small_arena():
    env = make_host(9210, area_size=1000)
    result = search_placement(env, True, budget=500, rng=np.random.default_rng(9210))
    assert len(result.history) > 1
    assert result.contract_reward > result.history[0]["contract_reward"]


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
        "closed_loop_relay", "closed_loop_flat", "stationary_floor", "random_floor"}
    assert summary["static"]["P_relay"]["evaluations"]["max"] <= 30
    assert summary["cpu_seconds"]["total_s"] > 0
    for world in (9301, 9302):
        row = json.loads((out / "worlds" / f"{world}.json").read_text(encoding="utf-8"))
        assert row["G_world"] == pytest.approx(
            row["static"]["P_relay"]["contract_reward"] - row["static"]["P_flat"]["contract_reward"])
        assert row["static"]["P_flat"]["max_uav_connections_seen"] == 0
        assert set(row["timing"]) >= {"search_relay", "search_flat", "closed_loop_relay",
                                      "closed_loop_flat", "stationary_floor", "random_floor"}
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
