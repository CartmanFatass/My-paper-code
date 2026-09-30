"""Cell b01 piece 1 (coupled_host_planner_distillation): teacher T_10 at the macro interface.

Features (shape, normalisation, ego one-hot, purity), box-face counts, the 10-step macro hold,
trigger/cap at macro decisions, hold at spawn, the truth guard, determinism, the label replay and
the two-world end-to-end probe (1011, 1001) against the committed b04 B0 values.

Stub and host checks use a shortened static host outside the declared panels (world 9103,
60 steps, budget 60), as ``test_b04_lawful_sensing`` does.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.host import HOST_CONTRACT_KWARGS
from experiments.candidates.coupled_host_planner_distillation import run_teacher
from experiments.candidates.coupled_host_planner_distillation import teacher as T
from experiments.candidates.coupled_host_replan_timing import event_host as EH
from experiments.candidates.coupled_host_replan_timing import rules as R

ROOT = Path(__file__).resolve().parents[4]
B04_RUN = ROOT / "runs" / "coupled_host_joint_skills_stage1" / "b04_b0_dev_a01"
BUDGET = 60
WORLD, STEPS = 9103, 60


def small_host(world=WORLD, max_steps=STEPS):
    kwargs = dict(HOST_CONTRACT_KWARGS)
    kwargs["max_steps"] = max_steps
    env = EH.EventCoupledRelayHost(area_size=5000, seed=world,
                                   event_override={"t_e": B4.NO_EVENT_T_E}, **kwargs)
    env.reset(seed=world)
    return env


# ------------------------------------------------------------------------------ features


def test_features_shape_normalisation_and_ego():
    team = B4.TeamMap()
    team.update({0: (2500.0, 1000.0), 49: (5000.0, 0.0), 7: (1.0, 2.0)}, 3)
    team.update({7: (100.0, 4000.0)}, 9)                                  # latest xy wins
    uav = np.array([[0.0, 0.0, 50.0], [5000.0, 5000.0, 150.0], [2500.0, 1250.0, 100.0],
                    [10.0, 20.0, 60.0], [4000.0, 3000.0, 75.0], [1.0, 2.0, 149.0]])
    before = copy.deepcopy(team.latest)
    for ego in range(6):
        f = T.features(team, uav, ego)
        assert f.shape == (174,) == (T.FEATURE_DIM,) and f.dtype == np.float64
        users = f[:150].reshape(50, 3)
        assert np.array_equal(users[0], [1.0, 0.5, 0.2])
        assert np.array_equal(users[49], [1.0, 1.0, 0.0])
        assert np.array_equal(users[7], [1.0, 0.02, 0.8])
        unknown = [u for u in range(50) if u not in (0, 7, 49)]
        assert np.all(users[unknown] == 0.0)
        block = f[150:168].reshape(6, 3)
        assert np.allclose(block[:, :2], uav[:, :2] / 5000.0) and np.allclose(block[:, 2], (uav[:, 2] - 50) / 100)
        assert np.array_equal(block[0], [0.0, 0.0, 0.0]) and np.array_equal(block[1], [1.0, 1.0, 1.0])
        onehot = f[168:]
        assert onehot.sum() == 1.0 and onehot[ego] == 1.0
    assert team.latest == before                                          # pure
    stacked = T.team_features(team, uav)
    assert stacked.shape == (6, 174)
    assert np.array_equal(stacked[:, :168], np.tile(stacked[0, :168], (6, 1)))
    assert np.array_equal(stacked[:, 168:], np.eye(6))
    assert np.all(T.features(B4.TeamMap(), uav, 0)[:150] == 0.0)
    with pytest.raises(ValueError):
        T.features(team, uav, 6)
    with pytest.raises(ValueError):
        T.features(team, uav[:5], 0)


def test_box_face_counts():
    labels = np.array([[0.0, 10.0, 50.0], [5000.0, 5000.0, 150.0], [1.0, 2.0, 99.0]])
    faces = T.box_face_counts(labels)
    assert faces == {"x_low": 1, "x_high": 1, "y_low": 0, "y_high": 1, "z_low": 1, "z_high": 1,
                     "labels": 3, "labels_on_any_face": 2}


# ------------------------------------------------------------------------------ hold, trigger, cap


@pytest.fixture
def scripted(monkeypatch):
    """Scripted sightings {step: {user: xy}} and a planner stub (as test_b04_lawful_sensing)."""
    script: dict[int, dict[int, tuple]] = {}
    calls: list[np.ndarray] = []
    sighting_steps: list[int] = []

    def fake_sightings(env):
        step = int(env.current_step)
        sighting_steps.append(step)
        seen = {}
        for s in sorted(script):
            if s <= step:
                seen.update(script[s])
        return seen, [len(seen)] * env.n_uavs

    def fake_plan(env, users_xy, world, budget):
        calls.append(np.array(users_xy, copy=True))
        layout = np.array(env.uav_positions, dtype=float) + [[10.0 * len(calls), 0.0, 0.0]]
        result = SimpleNamespace(positions_xyz=layout, evaluations=7, contract_reward=0.0)
        return result, result

    monkeypatch.setattr(B4, "team_sightings", fake_sightings)
    monkeypatch.setattr(B4, "plan_on_known", fake_plan)
    monkeypatch.setattr(B4, "assign_targets", lambda initial, layout: np.arange(len(layout)))
    return script, calls, sighting_steps


def test_macro_hold_trigger_and_spawn_hold(scripted):
    script, calls, sighting_steps = scripted
    env = small_host()
    spawn = np.array(env.uav_positions, copy=True)
    script[0] = {0: (1.0, 1.0), 1: (2.0, 2.0)}                           # 2 known: hold at 0
    script[3] = {2: (3.0, 3.0)}                                          # B0 would plan at 3
    script[5] = {3: (4.0, 4.0), 4: (5.0, 5.0)}
    script[7] = {5: (6.0, 6.0)}                                          # 6 known at decision 10
    script[23] = {6: (7.0, 7.0), 7: (8.0, 8.0), 8: (9.0, 9.0)}           # 3 new: plan at 30
    teacher = T.TeacherT10(env, WORLD, BUDGET)
    issued: list[np.ndarray] = []
    positions: list[np.ndarray] = []

    def spy(t):
        positions.append(np.array(env.uav_positions, copy=True))
        out = teacher.targets(t)
        issued.append(np.array(out, copy=True))
        return out
    result = R.rollout(env, spy, 0, STEPS)
    teacher.finish(result["t_end"])
    rec = teacher.record()
    assert rec["trigger_steps"] == [10, 30] and rec["planner_calls"] == 2
    assert [len(c) for c in calls] == [6, 9]
    assert rec["decisions"] == STEPS // 10 and [d["step"] for d in teacher.decisions] == [0, 10, 20, 30, 40, 50]
    assert rec["hold_decisions_before_first_plan"] == 1 and rec["evaluations_used"] == 28
    assert sighting_steps == [0, 10, 20, 30, 40, 50, STEPS]              # decisions + terminal
    for t in range(10):                                                  # spawn hold
        assert np.array_equal(issued[t], spawn)
    for block in range(STEPS // 10):                                     # held for exactly 10 steps
        ref = issued[10 * block]
        assert all(np.array_equal(issued[10 * block + j], ref) for j in range(10))
        assert np.array_equal(ref, teacher.decisions[block]["targets"])
    assert not np.array_equal(issued[9], issued[10]) and not np.array_equal(issued[29], issued[30])
    assert np.array_equal(issued[10], positions[10] + [[10.0, 0.0, 0.0]])   # plan from positions at 10
    assert np.all([d["features"].shape == (6, 174) for d in teacher.decisions])
    assert teacher.decisions[1]["features"][0, :18].tolist() == [
        1.0, 1 / 5000, 1 / 5000, 1.0, 2 / 5000, 2 / 5000, 1.0, 3 / 5000, 3 / 5000,
        1.0, 4 / 5000, 4 / 5000, 1.0, 5 / 5000, 5 / 5000, 1.0, 6 / 5000, 6 / 5000]
    with pytest.raises(AssertionError, match="macro boundary"):
        teacher.decide(15)


def test_macro_hold_refuses_a_missing_decision():
    fn = T.macro_hold(lambda t: np.zeros((6, 3)))
    with pytest.raises(AssertionError):
        fn(3)


def test_cap_binds_at_macro_decisions(scripted):
    script, calls, _ = scripted
    env = small_host()
    for k in range(6):
        script[10 * k] = {3 * k + j: (float(k), float(j)) for j in range(3)}
    teacher = T.TeacherT10(env, WORLD, BUDGET, max_replans=2)
    result = R.rollout(env, teacher.targets, 0, STEPS)
    teacher.finish(result["t_end"])
    rec = teacher.record()
    assert rec["trigger_steps"] == [0, 10] and len(calls) == 2
    assert rec["cap_hit"] and rec["cap_hit_trigger_steps"] == 4              # 20, 30, 40, 50
    assert [d["cap_hit"] for d in teacher.decisions] == [False, False, True, True, True, True]
    assert T.TeacherT10(small_host(), WORLD, BUDGET).max_replans == B4.MAX_REPLANS == 20


# ------------------------------------------------------------------------------ truth guard
# Copied from tests/experiments/candidates/coupled_host_joint_skills_stage1/test_b04_lawful_sensing.py
# (``truth_guard``), with the arm replaced by T_10; importing test modules across directories
# without packages is fragile under pytest's default import mode.

FORBIDDEN = {"event", "_post_event_users", "post_event_user_positions", "event_info"}


class TruthAccess(AssertionError):
    pass


@pytest.fixture
def truth_guard(monkeypatch):
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
            raise TruthAccess(f"read user_positions[{key!r}] (not a visible row)")

        def __array__(self, *args, **kwargs):
            raise TruthAccess("read the whole user_positions array")

        def __len__(self):
            raise TruthAccess("read the user count through user_positions")

    def guarded(self, name):
        if self is state["live"] and not state["allowed"]:
            if name == "user_positions":
                if state["accessor"]:
                    return VisibleRows(self)
                raise TruthAccess("read env.user_positions outside the sighting accessor")
            if name in FORBIDDEN:
                raise TruthAccess(f"read env.{name}")
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


def test_teacher_never_reads_unseen_users(truth_guard):
    env = small_host()
    truth_guard["live"] = env
    with pytest.raises(TruthAccess):                                     # negative controls
        _ = env.user_positions
    with pytest.raises(TruthAccess):
        _ = env.event["t_e"]
    result, teacher = T.run_teacher(env, WORLD, BUDGET, STEPS)
    rec = teacher.record()
    assert result["t_end"] == STEPS and rec["planner_calls"] >= 1        # the teacher did act
    assert truth_guard["accessor_calls"] == STEPS // 10 + 1 and truth_guard["rows_read"] > 0
    truth_guard["live"] = None
    assert teacher.decisions[0]["n_known"] < env.n_users                  # unseen users existed


def test_guard_catches_a_leaking_accessor(truth_guard, monkeypatch):
    env = small_host()
    visible = {int(u) for i in range(env.n_uavs) for u, _ in env._get_local_users(i)}
    unseen = next(u for u in range(env.n_users) if u not in visible)

    def leaking(env_):
        _ = env_.user_positions[unseen]
        return {}, [0] * env_.n_uavs
    monkeypatch.setattr(B4, "team_sightings", truth_guard["as_accessor"](leaking))
    truth_guard["live"] = env
    with pytest.raises(TruthAccess, match="not a visible row"):
        T.run_teacher(env, WORLD, BUDGET, STEPS)


# ------------------------------------------------------------------------------ determinism, replay


def run_small():
    env = small_host()
    result, teacher = T.run_teacher(env, WORLD, BUDGET, STEPS)
    return result, teacher, np.array(env.uav_positions, copy=True)


def test_determinism_and_label_replay():
    a_result, a, a_end = run_small()
    b_result, b, b_end = run_small()
    assert a_result["coverage_backhauled"] == b_result["coverage_backhauled"]
    assert a_result["contract_reward"] == b_result["contract_reward"]
    assert np.array_equal(a_end, b_end)

    def untimed(rec):                                                     # CPU timings differ
        return {**rec, "plans": [{k: v for k, v in p.items() if k != "planner_cpu_s"} for p in rec["plans"]]}
    assert untimed(a.record()) == untimed(b.record()) and len(a.decisions) == STEPS // 10
    for da, db in zip(a.decisions, b.decisions):
        assert np.array_equal(da["features"], db["features"]) and np.array_equal(da["targets"], db["targets"])
    labels = np.stack([d["targets"] for d in a.decisions])
    env = small_host()
    replay = T.replay_labels(env, labels, STEPS)
    assert replay["coverage_backhauled"] == a_result["coverage_backhauled"]
    assert replay["contract_reward"] == a_result["contract_reward"]
    assert np.array_equal(env.uav_positions, a_end)                        # same trajectory
    bad = labels.copy()
    bad[-1, 0, 0] += 300.0                                                 # negative control
    env_bad = small_host()
    T.replay_labels(env_bad, bad, STEPS)
    assert not np.array_equal(env_bad.uav_positions, a_end)


# ------------------------------------------------------------------------------ runner probe


@pytest.mark.skipif(not (B04_RUN / "summary.json").exists(), reason="b04 reference absent")
def test_two_world_probe_end_to_end(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(run_teacher.ADMISSION_ENV, raising=False)
    out = tmp_path / "probe"
    assert run_teacher.main(["--worlds", "1011", "1001", "--out", str(out), "--budget", "3000",
                             "--launch-sha", "test"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["worlds"] == [1011, 1001] and summary["training_fits_performed"] == 0
    assert summary["direction"] == "coupled_host_planner_distillation"
    for key in ("per_world", "means", "cpu_seconds", "wall_clock_s", "git_head", "launch_sha",
                "arguments", "interpreter", "definitions", "information_contract", "b04_run",
                "cpu_projection"):
        assert key in summary
    b04 = {r["world"]: r["B0"]["all_mean"]
           for r in json.loads((B04_RUN / "summary.json").read_text())["per_world"]}
    readings = []
    for row in summary["per_world"]:
        assert set(run_teacher.ROW_KEYS) <= set(row)
        w = row["world"]
        assert row["decisions"] == 50 and row["samples"] == 300
        assert row["replay"] == {"series_identical": True, "contract_reward_identical": True}
        assert row["world_json_bytes"] < 2 * 1024 * 1024
        assert row["b04_B0_all_mean"] == b04[w]
        assert row["t10_minus_b0"] == row["all_mean"] - b04[w]
        readings.append((w, row["all_mean"], row["final_100_mean"], b04[w], row["planner_calls"],
                         row["evaluations_used"], row["cpu_s"]["planner"], row["cpu_s"]["total"]))
        world = json.loads((out / "worlds" / f"{w}.json").read_text())
        assert np.asarray(world["features"]).shape == (50, 6, 174)
        assert np.asarray(world["labels"]).shape == (50, 6, 3)
        assert len(world["coverage_backhauled"]) == 500
        assert [d["step"] for d in world["decision_record"]] == list(range(0, 500, 10))
    with capsys.disabled():
        for r in readings:
            print("\nreading world={} T10={:.4f} f100={:.4f} B0={:.4f} calls={} evals={} "
                  "cpu_planner={:.2f}s cpu_total={:.2f}s".format(*r))
    for w, t10, *_rest in readings:                                        # reading band from the L0
        assert abs(t10 - b04[w]) <= 0.05, f"world {w}: T_10 {t10} vs B0 {b04[w]}"
    assert run_teacher.main(["--worlds", "1011", "--out", str(out)]) == 2   # refuses to overwrite
