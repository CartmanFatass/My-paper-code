"""Cell b04 arm B0 (coupled_host_joint_skills_stage1): sightings, team map, trigger, cap, hold,
static host, regression against the sealed gate, the objective's user set, the truth guard and
the two-world probe (1002, 1024).

Stub checks need no planner; host checks use shortened hosts outside the declared panels
(world 9103, budget 60) except the regression (1002 at the declared budget) and the probe.
"""
from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1 import run_b04
from experiments.candidates.coupled_host_joint_skills_stage1.host import HOST_CONTRACT_KWARGS
from experiments.candidates.coupled_host_replan_timing import event_host as EH
from experiments.candidates.coupled_host_replan_timing import rules as R

ROOT = Path(__file__).resolve().parents[4]
GATE = ROOT / "runs" / "coupled_host_joint_skills_stage1" / "b01_gate_dev_a01"
BUDGET = 60
WORLD, STEPS = 9103, 60


def small_host(world=WORLD, max_steps=STEPS):
    kwargs = dict(HOST_CONTRACT_KWARGS)
    kwargs["max_steps"] = max_steps
    env = EH.EventCoupledRelayHost(area_size=5000, seed=world,
                                   event_override={"t_e": B4.NO_EVENT_T_E}, **kwargs)
    env.reset(seed=world)
    return env


def visible_union(env):
    return {int(u) for i in range(env.n_uavs) for u, _ in env._get_local_users(i)}


# ------------------------------------------------------------------------------ sightings, map


def test_sightings_only_from_visible_users():
    env = small_host()
    sightings, views = B4.team_sightings(env)
    visible = visible_union(env)
    assert set(sightings) == visible and 0 < len(visible) < env.n_users
    assert views == [len(env._get_local_users(i)) for i in range(env.n_uavs)]
    positions = np.asarray(env.user_positions)
    for user, xy in sightings.items():
        assert xy == tuple(positions[user])
    stub = SimpleNamespace(n_uavs=2, user_positions=positions,
                           _get_local_users=lambda i: [[(3, 9.0), (41, 4.0)], [(41, 5.0)]][i])
    assert set(B4.team_sightings(stub)[0]) == {3, 41}


def test_map_keeps_latest_position_and_absence_moves_nobody():
    team = B4.TeamMap()
    assert team.update({1: (10.0, 10.0), 2: (20.0, 20.0)}, 0) == [1, 2]
    assert team.update({1: (15.0, 10.0)}, 4) == []                       # moved, not new
    assert team.update({}, 5) == []                                       # absence keeps rows
    assert team.update({3: (30.0, 0.0)}, 6) == [3]
    users, xy = team.users_xy()
    assert users == [1, 2, 3]
    assert np.array_equal(xy, [[15.0, 10.0], [20.0, 20.0], [30.0, 0.0]])
    assert team.latest[1][0] == 4 and team.latest[2][0] == 0


# ------------------------------------------------------------------------------ trigger, cap, hold


@pytest.fixture
def scripted(monkeypatch):
    """Scripted sightings {step: {user: xy}}; the planner stub returns a marker layout."""
    script: dict[int, dict[int, tuple]] = {}
    calls: list[np.ndarray] = []

    def fake_sightings(env):
        step = int(env.current_step)
        seen = {}
        for s in sorted(script):
            if s <= step:
                seen.update(script[s])                     # static users stay visible
        return seen, [len(seen)] * env.n_uavs

    def fake_plan(env, users_xy, world, budget):
        calls.append(np.array(users_xy, copy=True))
        layout = np.array(env.uav_positions, dtype=float) + [[10.0 * len(calls), 0.0, 0.0]]
        result = SimpleNamespace(positions_xyz=layout, evaluations=7, contract_reward=0.0)
        return result, result

    monkeypatch.setattr(B4, "team_sightings", fake_sightings)
    monkeypatch.setattr(B4, "plan_on_known", fake_plan)
    monkeypatch.setattr(B4, "assign_targets", lambda initial, layout: np.arange(len(layout)))
    return script, calls


def drive(env, steps, **arm_kwargs):
    arm = B4.B0Arm(env, WORLD, BUDGET, **arm_kwargs)
    result = R.rollout(env, arm.targets, 0, steps)
    arm.finish(result["t_end"])
    return arm, arm.record()


def test_trigger_at_three_newly_known_and_hold_before_first_plan(scripted):
    script, calls = scripted
    env = small_host()
    spawn = np.array(env.uav_positions, copy=True)
    script[0] = {0: (1.0, 1.0), 1: (2.0, 2.0)}                           # 2 known: hold
    script[3] = {2: (3.0, 3.0)}                                          # 3 known: first plan
    script[5] = {3: (4.0, 4.0), 4: (5.0, 5.0)}                           # 2 new: no plan
    script[7] = {5: (6.0, 6.0)}                                          # 3 new: re-plan
    probe = copy.deepcopy(env)
    arm = B4.B0Arm(probe, WORLD, BUDGET)
    R.rollout(probe, arm.targets, 0, 3)
    assert np.array_equal(probe.uav_positions, spawn) and not arm.plans   # held at spawn
    _arm, rec = drive(env, 12)
    assert rec["trigger_steps"] == [3, 7] and rec["replans"] == 2
    assert rec["hold_steps_before_first_plan"] == 3
    assert rec["evaluations_used"] == 28 and not rec["cap_hit"]
    assert [len(c) for c in calls] == [3, 6]
    assert rec["plans"][0]["newly_known"] == 3 and rec["plans"][1]["newly_known"] == 3


def test_cap_five(scripted):
    script, calls = scripted
    env = small_host()
    for k in range(8):
        script[2 * k] = {3 * k + j: (float(k), float(j)) for j in range(3)}
    _arm, rec = drive(env, 20, max_replans=5)
    assert rec["max_replans"] == 5 and rec["replans"] == 5 == len(calls)
    assert rec["trigger_steps"] == [0, 2, 4, 6, 8]
    assert rec["cap_hit"] and rec["first_cap_hit_step"] == 10
    assert B4.MAX_REPLANS == 20
    with pytest.raises(ValueError):
        B4.B0Arm(small_host(), WORLD, BUDGET, max_replans=0)


def test_default_cap_twenty_does_not_bind_at_eight_triggers(scripted):
    script, calls = scripted
    env = small_host()
    for k in range(8):
        script[2 * k] = {3 * k + j: (float(k), float(j)) for j in range(3)}
    _arm, rec = drive(env, 20)
    assert rec["max_replans"] == B4.MAX_REPLANS == 20
    assert rec["replans"] == 8 == len(calls) and not rec["cap_hit"]


def test_first_plan_below_kmeans_minimum_is_an_error():
    env = small_host()
    with pytest.raises(ValueError, match="k-means"):
        B4.plan_on_known(env, np.zeros((5, 2)), WORLD, BUDGET)


# ------------------------------------------------------------------------------ host


def test_no_event_ever_applies_over_500_steps():
    env = B4.make_static_host(1024)
    env.reset(seed=1024)
    users0 = np.array(env.user_positions, copy=True)
    assert env.event["t_e"] == B4.NO_EVENT_T_E > env.max_steps == 500
    bs = np.asarray(env.ground_bs_positions[0], dtype=float) + [0.0, 0.0, 70.0]
    result = R.rollout(env, lambda t: np.tile(bs, (env.n_uavs, 1)), 0, 500)
    assert result["t_end"] == 500 and int(env.current_step) == 500
    B4.assert_static(env, users0, "test")
    assert not env.event_applied


def test_planner_objective_ignores_unknown_users():
    env = small_host()
    sightings, _ = B4.team_sightings(env)
    team = B4.TeamMap()
    team.update(sightings, 0)
    users, xy = team.users_xy()
    base = B4.known_users_host(env, xy)
    assert base.n_users == len(users) and base.connections.shape == (6, len(users))
    assert np.array_equal(base.user_positions, xy) and base.event is None
    moved = copy.deepcopy(env)                               # every unknown user relocated
    unknown = [u for u in range(env.n_users) if u not in sightings]
    assert unknown
    positions = np.array(moved.user_positions, copy=True)
    positions[unknown] = np.random.default_rng(0).uniform(0, 5000, (len(unknown), 2))
    moved.user_positions = positions
    fp = R.state_fingerprint(env)
    relay_a, flat_a = B4.plan_on_known(env, xy, WORLD, BUDGET)
    relay_b, flat_b = B4.plan_on_known(moved, xy, WORLD, BUDGET)
    R.assert_unchanged(env, fp, "plan_on_known")
    assert np.array_equal(relay_a.positions_xyz, relay_b.positions_xyz)
    assert (relay_a.evaluations, flat_a.evaluations) == (relay_b.evaluations, flat_b.evaluations)
    assert relay_a.contract_reward == relay_b.contract_reward


@pytest.mark.skipif(not (GATE / "worlds" / "1002.json").exists(), reason="gate reference absent")
def test_regression_equals_gate_on_one_world():
    gate = json.loads((GATE / "worlds" / "1002.json").read_text())
    env = B4.make_static_host(1002)
    env.reset(seed=1002)
    initial = np.array(env.uav_positions, copy=True)
    users = np.array(env.user_positions, copy=True)
    reg = B4.regression_rollout(env, 1002, 3000, 500)
    means = B4.series_means(reg["coverage_backhauled"])
    B4.check_regression(1002, reg, means, initial, users, gate)          # raises on any mismatch
    assert means["all_mean"] == gate["closed_loop"]["closed_loop_relay"]["coverage_backhauled_mean_all"]
    bad = copy.deepcopy(gate)
    bad["closed_loop"]["closed_loop_relay"]["series"]["coverage_backhauled"][-1] += 0.02
    with pytest.raises(AssertionError, match="series"):
        B4.check_regression(1002, reg, means, initial, users, bad)


# ------------------------------------------------------------------------------ truth guard


FORBIDDEN = {"event", "_post_event_users", "post_event_user_positions", "event_info"}


class TruthAccess(AssertionError):
    pass


@pytest.fixture
def truth_guard(monkeypatch):
    """On the live arm host: any ``user_positions`` read outside host dynamics raises, except in
    the sighting accessor, where only rows of currently visible users can be read."""
    state = {"allowed": 0, "accessor": 0, "live": None, "accessor_calls": 0, "rows_read": 0}
    plain = object.__getattribute__
    original_local_users = EH.EventCoupledRelayHost._get_local_users

    class VisibleRows:
        def __init__(self, env):
            self._array = plain(env, "user_positions")
            state["allowed"] += 1
            try:
                self._visible = {int(u) for i in range(plain(env, "n_uavs"))
                                 for u, _ in original_local_users(env, i)}
            finally:
                state["allowed"] -= 1

        def __getitem__(self, key):
            if isinstance(key, (int, np.integer)) and int(key) in self._visible:
                state["rows_read"] += 1
                return np.array(self._array[int(key)], copy=True)
            raise TruthAccess(f"arm read user_positions[{key!r}] (not a visible row)")

        def __array__(self, *args, **kwargs):
            raise TruthAccess("arm read the whole user_positions array")

        def __len__(self):
            raise TruthAccess("arm read the user count through user_positions")

    def guarded(self, name):
        if self is state["live"] and not state["allowed"]:
            if name == "user_positions":
                if state["accessor"]:
                    return VisibleRows(self)
                raise TruthAccess("arm read env.user_positions outside the sighting accessor")
            if name in FORBIDDEN:
                raise TruthAccess(f"arm read env.{name}")
        return plain(self, name)

    def allow(function):
        def wrapper(*args, **kwargs):
            state["allowed"] += 1
            try:
                return function(*args, **kwargs)
            finally:
                state["allowed"] -= 1
        return wrapper

    def as_accessor(function):
        def wrapper(*args, **kwargs):
            state["accessor"] += 1
            state["accessor_calls"] += 1
            try:
                return function(*args, **kwargs)
            finally:
                state["accessor"] -= 1
        return wrapper

    monkeypatch.setattr(EH.EventCoupledRelayHost, "step", allow(EH.EventCoupledRelayHost.step))
    monkeypatch.setattr(EH.EventCoupledRelayHost, "_get_local_users", allow(original_local_users))
    monkeypatch.setattr(B4, "team_sightings", as_accessor(B4.team_sightings))
    monkeypatch.setattr(EH.EventCoupledRelayHost, "__getattribute__", guarded)
    state["as_accessor"] = as_accessor
    return state


def test_arm_never_reads_unseen_users(truth_guard):
    env = small_host()
    truth_guard["live"] = env
    with pytest.raises(TruthAccess):                                     # negative controls
        _ = env.user_positions
    with pytest.raises(TruthAccess):
        _ = env.event["t_e"]
    result, rec = B4.run_b0(env, WORLD, BUDGET, STEPS)
    assert result["t_end"] == STEPS and rec["replans"] >= 1              # the arm did act
    assert truth_guard["accessor_calls"] == STEPS + 1 and truth_guard["rows_read"] > 0
    truth_guard["live"] = None
    assert len(rec["known_users_at"]["0"]) < env.n_users                  # unseen users existed


def test_guard_catches_a_leaking_accessor(truth_guard, monkeypatch):
    env = small_host()
    unseen = next(u for u in range(env.n_users) if u not in visible_union(env))

    def leaking(env_):
        positions = env_.user_positions
        _ = positions[unseen]
        return {}, [0] * env_.n_uavs
    monkeypatch.setattr(B4, "team_sightings", truth_guard["as_accessor"](leaking))
    truth_guard["live"] = env
    with pytest.raises(TruthAccess, match="not a visible row"):
        B4.run_b0(env, WORLD, BUDGET, STEPS)

    def whole_array(env_):
        return {u: tuple(row) for u, row in enumerate(np.asarray(env_.user_positions))}, []
    monkeypatch.setattr(B4, "team_sightings", truth_guard["as_accessor"](whole_array))
    with pytest.raises(TruthAccess, match="whole"):
        B4.team_sightings(env)


# ------------------------------------------------------------------------------ runner


@pytest.mark.skipif(not (GATE / "summary.json").exists(), reason="gate reference absent")
def test_two_world_probe_end_to_end(tmp_path, monkeypatch):
    monkeypatch.delenv(run_b04.ADMISSION_ENV, raising=False)
    out = tmp_path / "probe"
    cpu0 = time.process_time()
    assert run_b04.main(["--worlds", "1002", "1024", "--probe", "2", "--out", str(out),
                         "--budget", "3000", "--launch-sha", "test"]) == 0
    assert time.process_time() - cpu0 < 120
    summary = json.loads((out / "summary.json").read_text())
    assert summary["worlds"] == [1002, 1024] and summary["training_fits_performed"] == 0
    assert summary["regression_equals_gate_all_worlds"] is True
    for key in ("per_world", "means", "cpu_seconds", "wall_clock_s", "git_head", "launch_sha",
                "arguments", "interpreter", "definitions", "information_contract", "gate_run"):
        assert key in summary
    for stake in run_b04.STAKES:
        assert set(summary["means"]["stakes"][stake]) >= {"mean", "sd", "min", "max", "n", "n_positive"}
    for row in summary["per_world"]:
        assert set(run_b04.B0_ROW_KEYS) <= set(row["B0"])
        assert len(row["gate_file_sha256"]) == 64
        for key in ("users_known", "clusters_known"):
            assert set(row["B0"][key]) == {"0", "100", "250", "500"}
        assert row["F"]["regression_all_mean"] == row["F"]["gate_all_mean"] == row["F"]["all_mean"]
        assert row["stakes"]["s_info0"] == row["F"]["all_mean"] - row["B0"]["all_mean"]
        assert row["stakes"]["s_info0_final100"] == (row["F"]["final_100_mean"]
                                                     - row["B0"]["final_100_mean"])
        assert row["B0"]["replans"] <= B4.MAX_REPLANS
        assert row["B0"]["evaluations_used"] <= 2 * 3000 * B4.MAX_REPLANS
    by_world = {r["world"]: r for r in summary["per_world"]}
    assert by_world[1024]["B0"]["clusters_known"]["0"] == 2                # census: 2 clusters at spawn
    world = json.loads((out / "worlds" / "1024.json").read_text())
    assert len(world["B0"]["coverage_backhauled"]) == 500
    # refuses to overwrite; refuses a budget the gate run was not made at
    assert run_b04.main(["--worlds", "1002", "--out", str(out)]) == 2
    assert run_b04.main(["--worlds", "1002", "--out", str(tmp_path / "b"), "--budget", "60"]) == 2
