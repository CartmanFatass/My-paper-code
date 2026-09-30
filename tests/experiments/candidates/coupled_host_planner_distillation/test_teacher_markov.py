"""Cell b01 piece 2 (coupled_host_planner_distillation): Markov teacher T_M.

(a) pooling every host step, decisions only at 10-step boundaries; (b) re-plan iff the known set
changed, cache hit otherwise, hold below 6 known; (c) the planner receives the constant seed, not
the world id; (d) truth guard; (e) determinism and target replay; (f) label mode: one labelled
decision per re-plan with the layouts of seeds (0, 1, 2), seed 0 first and used for control;
(g) two-world end-to-end probe (1011, 1001) against the committed b04 B0 values.

Stub and host checks use a shortened static host outside the declared panels (world 9103,
60 steps, budget 60), as ``test_teacher`` does.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.host import HOST_CONTRACT_KWARGS
from experiments.candidates.coupled_host_planner_distillation import run_markov
from experiments.candidates.coupled_host_planner_distillation import teacher as T
from experiments.candidates.coupled_host_planner_distillation import teacher_markov as TM
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


def test_features_shared_is_the_encoding_without_ego():
    team = B4.TeamMap()
    team.update({0: (2500.0, 1000.0), 49: (5000.0, 0.0)}, 3)
    uav = np.array([[0.0, 0.0, 50.0], [5000.0, 5000.0, 150.0], [2500.0, 1250.0, 100.0],
                    [10.0, 20.0, 60.0], [4000.0, 3000.0, 75.0], [1.0, 2.0, 149.0]])
    shared = TM.features_shared(team, uav)
    assert shared.shape == (168,) == (TM.SHARED_FEATURE_DIM,) and shared.dtype == np.float64
    for ego in range(6):
        assert np.array_equal(T.features(team, uav, ego)[:168], shared)


# ------------------------------------------------------------------------------ stubbed rules


@pytest.fixture
def scripted(monkeypatch):
    """Scripted sightings {step: {user: xy}}; planner stub that records its seed argument."""
    script: dict[int, dict[int, tuple]] = {}
    calls: list[dict] = []
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
        calls.append({"n": len(users_xy), "seed": world, "budget": budget,
                      "step": int(env.current_step), "xy": np.array(users_xy, copy=True)})
        layout = np.array([[100.0 * (i + 1) + 10.0 * len(calls) + 1000.0 * world, 500.0, 50.0]
                           for i in range(6)])
        result = SimpleNamespace(positions_xyz=layout, evaluations=7, contract_reward=0.0)
        return result, result

    monkeypatch.setattr(B4, "team_sightings", fake_sightings)
    monkeypatch.setattr(B4, "plan_on_known", fake_plan)
    return script, calls, sighting_steps


def run_scripted(teacher, env):
    issued, positions = [], []

    def spy(t):
        positions.append(np.array(env.uav_positions, copy=True))
        out = teacher.targets(t)
        issued.append(np.array(out, copy=True))
        return out
    result = R.rollout(env, spy, 0, STEPS)
    teacher.finish(result["t_end"])
    return result, issued, positions


def test_pooling_every_step_decisions_at_boundaries(scripted, monkeypatch):
    script, calls, sighting_steps = scripted
    env = small_host()
    spawn = np.array(env.uav_positions, copy=True)
    script[0] = {u: (float(u), 1.0) for u in range(5)}                  # 5 known: hold at 0
    cumulative = B4.team_sightings

    def transient(env_):                                                 # user 5 visible at step 3 only
        seen, views = cumulative(env_)
        if int(env_.current_step) == 3:
            seen = {**seen, 5: (6.0, 6.0)}
        return seen, views
    monkeypatch.setattr(B4, "team_sightings", transient)
    teacher = TM.TeacherMarkov(env, WORLD, BUDGET)
    decided: list[int] = []
    original = teacher.decide

    def spy_decide(t):
        decided.append(t)
        return original(t)
    teacher._held = T.macro_hold(spy_decide)
    _result, issued, _positions = run_scripted(teacher, env)
    assert sighting_steps == list(range(STEPS)) + [STEPS]               # every step + terminal
    assert decided == [0, 10, 20, 30, 40, 50]                            # never at 3
    assert [d["n_known"] for d in teacher.decisions] == [5, 6, 6, 6, 6, 6]
    assert teacher.map.latest[5] == (3, 6.0, 6.0)                        # pooled at step 3 only
    assert teacher.decisions[0]["hold"] and not teacher.decisions[1]["hold"]
    assert calls[0]["step"] == 10 and calls[0]["n"] == 6
    for t in range(10):
        assert np.array_equal(issued[t], spawn)
    for block in range(STEPS // 10):
        assert all(np.array_equal(issued[10 * block + j], issued[10 * block]) for j in range(10))
        assert np.array_equal(issued[10 * block], teacher.decisions[block]["targets"])
    assert teacher.record()["hold_steps"] == 10 and teacher.observe_calls == STEPS + 1


def test_replan_iff_known_set_changed_cache_and_hold(scripted, monkeypatch):
    script, calls, _ = scripted
    env = small_host()
    script[0] = {u: (float(u), 1.0) for u in range(3)}                   # 3 known: hold at 0, 10
    script[12] = {u: (float(u), 2.0) for u in range(3, 6)}               # 6 known: plan at 20
    script[25] = {6: (7.0, 7.0)}                                         # 1 new: re-plan at 30
    script[33] = {6: (7.5, 7.5)}                                         # same set, new xy: cache
    perms = iter([np.arange(6), np.arange(6), np.arange(6)[::-1], np.arange(6)[::-1]])
    monkeypatch.setattr(B4, "assign_targets", lambda initial, layout: next(perms))
    teacher = TM.TeacherMarkov(env, WORLD, BUDGET)
    run_scripted(teacher, env)
    d = teacher.decisions
    assert [x["hold"] for x in d] == [True, True, False, False, False, False]
    assert [x["replanned"] for x in d] == [False, False, True, True, False, False]
    assert [x["cache_hit"] for x in d] == [False, False, False, False, True, True]
    assert [x["assignment_changed"] for x in d] == [None, None, None, None, True, False]
    assert [x["evaluations"] for x in d] == [0, 0, 14, 14, 0, 0]
    assert [c["step"] for c in calls] == [20, 30] and [c["n"] for c in calls] == [6, 7]
    rec = teacher.record()
    assert rec["planner_calls"] == 2 and rec["plan_steps"] == [20, 30] and rec["cache_hits"] == 2
    assert rec["hold_decisions"] == 2 and rec["hold_steps"] == 20 and rec["assignment_changes"] == 1
    assert set(teacher.cache) == {frozenset(range(6)), frozenset(range(7))}
    layout = teacher.cache[frozenset(range(7))]
    assert np.array_equal(d[4]["targets"], layout[::-1]) and np.array_equal(d[3]["targets"], layout)
    assert rec["labelled_decisions"] == 2 and [l["step"] for l in teacher.labelled] == [20, 30]


def test_no_planner_below_six_known_all_episode(scripted):
    script, calls, _ = scripted
    env = small_host()
    spawn = np.array(env.uav_positions, copy=True)
    script[0] = {u: (float(u), 1.0) for u in range(5)}
    teacher = TM.TeacherMarkov(env, WORLD, BUDGET)
    _result, issued, _ = run_scripted(teacher, env)
    assert not calls and all(np.array_equal(x, spawn) for x in issued)
    assert teacher.record()["hold_steps"] == STEPS


def test_planner_receives_the_seed_not_the_world_id(scripted):
    script, calls, _ = scripted
    script[0] = {u: (float(u), 1.0) for u in range(6)}
    script[20] = {6: (1.0, 2.0)}
    teacher = TM.TeacherMarkov(small_host(), WORLD, BUDGET)              # default seed 0
    run_scripted(teacher, teacher.env)
    assert [c["seed"] for c in calls] == [0, 0] and all(c["budget"] == BUDGET for c in calls)
    calls.clear()
    teacher = TM.TeacherMarkov(small_host(), WORLD, BUDGET, seed=5)
    run_scripted(teacher, teacher.env)
    assert [c["seed"] for c in calls] == [5, 5]
    assert all(c["seed"] != WORLD for c in calls)
    with pytest.raises(ValueError):
        TM.TeacherMarkov(small_host(), WORLD, BUDGET, trigger="new3")


def test_label_mode_three_layouts_seed_zero_first(scripted):
    script, calls, _ = scripted
    script[0] = {u: (float(u), 1.0) for u in range(6)}
    script[20] = {6: (1.0, 2.0)}
    env = small_host()
    teacher = TM.TeacherMarkov(env, WORLD, BUDGET, label_seeds=(0, 1, 2))
    run_scripted(teacher, env)
    assert [c["seed"] for c in calls] == [0, 1, 2, 0, 1, 2]
    assert [c["step"] for c in calls] == [0, 0, 0, 20, 20, 20]
    for a, b in zip(calls[0::3], calls[1::3]):                           # same known map per decision
        assert np.array_equal(a["xy"], b["xy"])
    assert teacher.record()["planner_calls"] == 2 and teacher.evaluations == 28   # control only
    assert len(teacher.labelled) == 2
    for lab, dec_step in zip(teacher.labelled, (0, 20)):
        assert lab["step"] == dec_step and lab["seeds"] == [0, 1, 2]
        assert lab["layouts"].shape == (3, 6, 3) and lab["features"].shape == (168,)
        assert lab["positions"].shape == (6, 3)
        assert lab["layouts"][0][0, 0] < 1000.0 < lab["layouts"][1][0, 0] < 2000.0 < lab["layouts"][2][0, 0]
        assert np.array_equal(lab["layouts"][0], teacher.cache[frozenset(lab["known"])])
    decision = next(d for d in teacher.decisions if d["step"] == 20)
    assert np.array_equal(np.sort(decision["targets"], axis=0), np.sort(teacher.labelled[1]["layouts"][0], axis=0))
    assert len(teacher.labelled[0]["known"]) == 6 and len(teacher.labelled[1]["known"]) == 7
    with pytest.raises(ValueError):
        TM.TeacherMarkov(small_host(), WORLD, BUDGET, label_seeds=(1, 0, 2))


# ------------------------------------------------------------------------------ truth guard
# Copied from test_teacher.py (itself from test_b04_lawful_sensing.py), the arm replaced by T_M.

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


def test_tm_never_reads_unseen_users(truth_guard):
    env = small_host()
    truth_guard["live"] = env
    with pytest.raises(TruthAccess):                                     # negative controls
        _ = env.user_positions
    with pytest.raises(TruthAccess):
        _ = env.event["t_e"]
    result, teacher = TM.run_markov(env, WORLD, BUDGET, horizon=STEPS, label_seeds=(0, 1))
    rec = teacher.record()
    assert result["t_end"] == STEPS and rec["planner_calls"] >= 1        # the teacher did act
    assert truth_guard["accessor_calls"] == STEPS + 1 and truth_guard["rows_read"] > 0
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
        TM.run_markov(env, WORLD, BUDGET, horizon=STEPS)


# ------------------------------------------------------------------------------ determinism, replay


def run_small(label_seeds=None):
    env = small_host()
    result, teacher = TM.run_markov(env, WORLD, BUDGET, horizon=STEPS, label_seeds=label_seeds)
    return result, teacher, np.array(env.uav_positions, copy=True)


def untimed(rec):
    return {**rec, "plans": [{k: v for k, v in p.items() if k != "planner_cpu_s"} for p in rec["plans"]]}


def test_determinism_and_target_replay():
    a_result, a, a_end = run_small()
    b_result, b, b_end = run_small()
    c_result, c, _ = run_small(label_seeds=(0, 1, 2))                   # labels do not alter control
    assert a_result["coverage_backhauled"] == b_result["coverage_backhauled"] == c_result["coverage_backhauled"]
    assert a_result["contract_reward"] == b_result["contract_reward"]
    assert np.array_equal(a_end, b_end)
    assert untimed(a.record()) == untimed(b.record()) and len(a.decisions) == STEPS // 10
    assert a.record()["planner_calls"] >= 1
    for da, db, dc in zip(a.decisions, b.decisions, c.decisions):
        assert np.array_equal(da["targets"], db["targets"]) and np.array_equal(da["targets"], dc["targets"])
        assert {k: v for k, v in da.items() if k != "targets"} == {k: v for k, v in db.items() if k != "targets"}
    for la, lb, lc in zip(a.labelled, b.labelled, c.labelled):
        assert np.array_equal(la["features"], lb["features"]) and np.array_equal(la["layouts"], lb["layouts"])
        assert np.array_equal(la["layouts"][0], lc["layouts"][0]) and lc["layouts"].shape[0] == 3
    targets = np.stack([d["targets"] for d in a.decisions])
    env = small_host()
    replay = T.replay_labels(env, targets, STEPS)
    assert replay["coverage_backhauled"] == a_result["coverage_backhauled"]
    assert replay["contract_reward"] == a_result["contract_reward"]
    assert np.array_equal(env.uav_positions, a_end)
    bad = targets.copy()
    bad[-1, 0, 0] += 300.0                                                 # negative control
    env_bad = small_host()
    T.replay_labels(env_bad, bad, STEPS)
    assert not np.array_equal(env_bad.uav_positions, a_end)


# ------------------------------------------------------------------------------ runner probe


@pytest.mark.skipif(not (B04_RUN / "summary.json").exists(), reason="b04 reference absent")
def test_two_world_probe_end_to_end(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(run_markov.ADMISSION_ENV, raising=False)
    out = tmp_path / "probe"
    assert run_markov.main(["--worlds", "1011", "1001", "--out", str(out), "--budget", "3000",
                            "--launch-sha", "test"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["worlds"] == [1011, 1001] and summary["training_fits_performed"] == 0
    assert summary["direction"] == "coupled_host_planner_distillation" and summary["seed"] == 0
    assert summary["mode"] == "dev_panel"
    for key in ("per_world", "means", "cpu_seconds", "wall_clock_s", "git_head", "launch_sha",
                "arguments", "interpreter", "definitions", "information_contract", "b04_run",
                "cpu_projection", "labels_total", "labels_z_all_50", "box_faces"):
        assert key in summary
    b04 = {r["world"]: r["B0"]["all_mean"]
           for r in json.loads((B04_RUN / "summary.json").read_text())["per_world"]}
    for row in summary["per_world"]:
        assert set(run_markov.ROW_KEYS) <= set(row)
        w = row["world"]
        assert row["decisions"] == 50 and row["planner_calls"] == row["labelled_decisions"] >= 1
        assert row["cache_hits"] + row["planner_calls"] + row["hold_decisions"] == 50
        assert row["replay"] == {"series_identical": True, "contract_reward_identical": True}
        assert row["world_json_bytes"] < 2 * 1024 * 1024
        assert row["b04_B0_all_mean"] == b04[w] and row["tm_minus_b0"] == row["all_mean"] - b04[w]
        world = json.loads((out / "worlds" / f"{w}.json").read_text())
        assert len(world["coverage_backhauled"]) == 500
        assert [d["step"] for d in world["decision_record"]] == list(range(0, 500, 10))
        assert np.asarray([d["targets"] for d in world["decision_record"]]).shape == (50, 6, 3)
        for lab in world["labelled"]:
            assert np.asarray(lab["features"]).shape == (168,) and lab["seeds"] == [0]
            assert np.asarray(lab["layouts"]).shape == (1, 6, 3)
        with capsys.disabled():
            print(f"\nreading world={w} TM={row['all_mean']:.4f} f100={row['final_100_mean']:.4f} "
                  f"B0={b04[w]:.4f} tm_minus_b0={row['tm_minus_b0']:+.4f} plans={row['planner_calls']} "
                  f"cache_hits={row['cache_hits']} hold_steps={row['hold_steps']} "
                  f"json={row['world_json_bytes']}B")
    assert run_markov.main(["--worlds", "1011", "--out", str(out)]) == 2   # refuses to overwrite
    with pytest.raises(SystemExit):
        run_markov.main(["--worlds", "1011", "--out", str(tmp_path / "x"), "--label-seeds", "1", "0"])
