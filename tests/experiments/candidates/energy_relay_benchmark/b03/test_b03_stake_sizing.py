"""B03 Stage 2-0 stake sizing: assignment modes, the worker contract, readings, runner."""

from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic, VARIANTS
from experiments.candidates.energy_relay_benchmark.b01.native import B01Spec, heuristic_params
from experiments.candidates.energy_relay_benchmark.b03 import stake_sizing as ss
from experiments.candidates.energy_relay_benchmark.b03.assignment_modes import (
    ASSIGNMENT_MODES,
    AssignmentModeController,
    AssignmentModeHeuristic,
)
from scripts import run_energy_relay_benchmark_b03 as entry

H1 = heuristic_params("H1", B01Spec())
VOLATILE = {"wall_seconds", "worker_peak_rss_kib"}


def _hysteresis_state(heuristic, rng, uavs, points):
    """Previous targets near some points for about half the UAVs (NaN for the rest)."""
    heuristic.targets_xy[:] = np.nan
    for uav in uavs:
        if rng.random() < 0.5:
            heuristic.targets_xy[uav] = points[rng.integers(len(points))] + rng.normal(0, 20, 2)


def test_modes_are_declared_and_unknown_mode_refused():
    assert ASSIGNMENT_MODES == ("hungarian", "identity", "independent_nearest")
    with pytest.raises(ValueError, match="assignment mode"):
        AssignmentModeHeuristic(H1, "greedy")
    assert H1 == replace(VARIANTS["H1"], replan_period=30) and H1.information == "central"


@pytest.mark.parametrize("draw", range(6))
def test_hungarian_is_the_base_method_with_hysteresis(draw):
    rng = np.random.default_rng(700 + draw)
    own_xy = rng.uniform(0, 8000, size=(8, 2))
    uavs = np.flatnonzero(rng.random(8) < 0.8) if draw % 2 else np.arange(8)
    points = rng.uniform(0, 8000, size=(len(uavs), 2))
    base, mode = LayoutHeuristic(H1), AssignmentModeHeuristic(H1, "hungarian")
    _hysteresis_state(base, rng, uavs, points)
    mode.targets_xy = base.targets_xy.copy()
    expected, observed = np.full((8, 2), np.nan), np.full((8, 2), np.nan)
    assigned_base = base._assign_targets(own_xy, uavs, points, expected)
    assigned_mode = mode._assign_targets(own_xy, uavs, points, observed)
    assert assigned_mode == assigned_base
    np.testing.assert_array_equal(observed, expected)


def test_identity_pairs_by_uav_index_regardless_of_positions():
    rng = np.random.default_rng(11)
    heuristic = AssignmentModeHeuristic(H1, "identity")
    points = rng.uniform(0, 8000, size=(8, 2))
    uavs = np.asarray([0, 2, 3, 5, 6, 7])      # UAVs 1 and 4 unavailable
    for own_xy in (rng.uniform(0, 8000, size=(8, 2)), np.zeros((8, 2))):
        _hysteresis_state(heuristic, rng, uavs, points)
        targets = np.full((8, 2), np.nan)
        assert heuristic._assign_targets(own_xy, uavs, points, targets) == set(uavs.tolist())
        np.testing.assert_array_equal(targets[uavs], points[uavs])
        assert np.isnan(targets[[1, 4]]).all()   # slots 1 and 4 served by nobody
    # fewer points than UAV indices: UAV i gets a target only if slot i exists
    targets = np.full((8, 2), np.nan)
    assert heuristic._assign_targets(np.zeros((8, 2)), uavs, points[:6], targets) == {0, 2, 3, 5}
    np.testing.assert_array_equal(targets[[0, 2, 3, 5]], points[[0, 2, 3, 5]])
    assert np.isnan(targets[[1, 4, 6, 7]]).all()


def _frame_inputs(frame):
    return {"users_xy": frame["user_positions"][:, :2], "bs_xy": frame["bs_positions"][:, :2]}


def _assert_same_record(first, second, skip=("targets",)):
    assert set(first) == set(second)
    for key in first:
        if key in skip:
            continue
        a, b = first[key], second[key]
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            np.testing.assert_array_equal(a, b, err_msg=key)
        else:
            assert a == b, key


def test_identity_all_available_is_uav_i_to_base_priority_i(live_frames):
    modes = np.zeros(8, dtype=bool)
    for frame in live_frames[::5]:
        base, identity = LayoutHeuristic(H1), AssignmentModeHeuristic(H1, "identity")
        base_plan = base.plan(frame["obs"], modes, _frame_inputs(frame))
        plan = identity.plan(frame["obs"], modes, _frame_inputs(frame))
        assert len(base_plan["priority"]) == 8 and base_plan["kinds"][:2] == ["relay", "relay"]
        np.testing.assert_array_equal(identity.targets_xy, base_plan["priority"])
        np.testing.assert_array_equal(plan["targets"], base_plan["priority"])
        _assert_same_record(plan, base_plan)


def test_identity_unavailable_uav_leaves_its_slot_empty(live_frames):
    for frame in live_frames[1::4]:
        for unavailable in (2, 0, 7):
            modes = np.zeros(8, dtype=bool)
            modes[unavailable] = True
            base, identity = LayoutHeuristic(H1), AssignmentModeHeuristic(H1, "identity")
            base_plan = base.plan(frame["obs"], modes, _frame_inputs(frame))
            plan = identity.plan(frame["obs"], modes, _frame_inputs(frame))
            priority = plan["priority"]
            others = [uav for uav in range(8) if uav != unavailable]
            np.testing.assert_array_equal(identity.targets_xy[others], priority[others])
            assert np.isnan(identity.targets_xy[unavailable]).all()
            empty_slot = priority[unavailable]
            assert not any(np.array_equal(identity.targets_xy[uav], empty_slot) for uav in others)
            assert not plan["search"] and plan["search_uavs"] == []
            # every record field that does not depend on the assignment equals the base plan's
            _assert_same_record(plan, base_plan)
            # the base (hungarian) plan covers only priority[:7]: slot 7 is dropped instead
            assert not any(np.array_equal(base.targets_xy[uav], priority[7]) for uav in others)


def test_hungarian_and_nearest_run_the_base_plan(live_frames, monkeypatch):
    calls = []
    original = LayoutHeuristic.plan
    monkeypatch.setattr(LayoutHeuristic, "plan",
                        lambda self, *a, **k: calls.append(self.mode) or original(self, *a, **k))
    frame = live_frames[0]
    for mode in ASSIGNMENT_MODES:
        AssignmentModeHeuristic(H1, mode).plan(frame["obs"], np.zeros(8, dtype=bool),
                                               _frame_inputs(frame))
    assert calls == ["hungarian", "independent_nearest"]


def test_independent_nearest_is_the_row_argmin_with_hysteresis_and_duplicates():
    rng = np.random.default_rng(12)
    heuristic = AssignmentModeHeuristic(H1, "independent_nearest")
    own_xy = rng.uniform(0, 8000, size=(8, 2))
    uavs = np.arange(8)
    points = rng.uniform(0, 8000, size=(8, 2))
    _hysteresis_state(heuristic, rng, uavs, points)
    cost = np.linalg.norm(own_xy[:, None, :] - points[None, :, :], axis=2)
    for row in range(8):
        previous = heuristic.targets_xy[row]
        if np.all(np.isfinite(previous)):
            cost[row, np.argmin(np.linalg.norm(points - previous, axis=1))] -= 300.0
    targets = np.full((8, 2), np.nan)
    assert heuristic._assign_targets(own_xy, uavs, points, targets) == set(range(8))
    np.testing.assert_array_equal(targets, points[np.argmin(cost, axis=1)])
    # Constructed: A, B two anchors; UAVs 0 and 1 both nearest A -> duplicate, B unserved.
    a, b = np.asarray((1000.0, 1000.0)), np.asarray((5000.0, 5000.0))
    points = np.stack((a, b))
    own = np.asarray([[1100.0, 1000.0], [900.0, 1000.0]])
    fresh = AssignmentModeHeuristic(H1, "independent_nearest")
    targets = np.full((8, 2), np.nan)
    assert fresh._assign_targets(own, np.asarray([0, 1]), points, targets) == {0, 1}
    np.testing.assert_array_equal(targets[:2], [a, a])
    # Hysteresis: previous target B; A closer by 200 m (< 300) keeps B, by 900 m switches.
    fresh.targets_xy[0] = b
    mid = (a + b) / 2
    direction = (a - b) / np.linalg.norm(a - b)
    for shift, expected in ((100.0, b), (450.0, a)):
        own = np.asarray([mid + shift * direction])
        targets = np.full((8, 2), np.nan)
        fresh._assign_targets(own, np.asarray([0]), points, targets)
        np.testing.assert_array_equal(targets[0], expected)


def test_every_available_uav_is_targeted_on_live_frames(live_frames):
    """The base ``plan`` invariant (central plans cover every available UAV) in all modes."""
    for mode in ASSIGNMENT_MODES:
        heuristic = AssignmentModeHeuristic(H1, mode)
        for index, frame in enumerate(live_frames):
            inputs = {"users_xy": frame["user_positions"][:, :2],
                      "bs_xy": frame["bs_positions"][:, :2]}
            modes = np.zeros(8, dtype=bool)
            if index % 3 == 2:
                modes[[1, 6]] = True    # two UAVs in shield mode: unavailable
            plan = heuristic.plan(frame["obs"], modes, inputs)   # raises if one is left
            assert not plan["search"]
            assert np.isfinite(heuristic.targets_xy[~modes]).all()
            assert np.isnan(heuristic.targets_xy[modes]).all()
            if mode == "identity":
                available = np.flatnonzero(~modes)
                np.testing.assert_array_equal(heuristic.targets_xy[available],
                                              plan["priority"][available])


def test_controller_uses_the_mode_heuristic(tiny_config):
    env = ev.make_env(tiny_config, 955001)
    try:
        controller = AssignmentModeController(H1, env, "identity")
        assert isinstance(controller.heuristic, AssignmentModeHeuristic)
        assert controller.heuristic.mode == "identity" and controller.env is env
    finally:
        env.close()


def test_hungarian_stake_task_equals_evaluate_task(tmp_path):
    common = dict(seed=955001, params=PRODUCTION_PARAMS, horizon=40, policy_seed=925031,
                  threads=1, heuristic=H1, log_dir=str(tmp_path))
    reference = ev.evaluate_task(ev.WorldTask(controller="H1", **common))
    stake = ss.evaluate_stake_task(ss.StakeTask(mode="hungarian", **common))
    assert stake["row"].pop("assignment_mode") == "hungarian"
    assert set(stake) == {"row", "arrays"}
    assert {k: v for k, v in stake["row"].items() if k not in VOLATILE} == \
           {k: v for k, v in reference["row"].items() if k not in VOLATILE}
    assert stake["row"]["replans"] == 2 and stake["row"]["failed"] is False
    assert set(stake["arrays"]) == set(reference["arrays"])
    for key, value in reference["arrays"].items():
        np.testing.assert_array_equal(stake["arrays"][key], value, err_msg=key)


def _row(seed, qos, j, pre=None, post=None, failed=False):
    if failed:
        return {"seed": seed, "failed": True}
    return {"seed": seed, "failed": False, "qos_per_step": qos, "raw_native_J": j,
            "native_J_per_step": j / 10.0, "qos_per_step_pre_entry": pre,
            "qos_per_step_entry_to_input": None, "qos_per_step_post_input": post}


def test_summary_arithmetic_on_synthetic_rows():
    worlds = (1, 2, 3, 4)
    hungarian = [_row(1, .8, 100, .9, .7), _row(2, .7, 90, .8, .6), _row(3, .6, 80, .7, None),
                 _row(4, .5, 70, .6, .4)]
    identity = [_row(1, .7, 95, .85, .65), _row(2, .72, 80, .78, .5), _row(3, .5, 60, .6, .3),
                _row(4, .45, 71, .55, .35)]
    nearest = [_row(1, .6, 90, .8, .5), _row(2, .5, 70, .7, .4), _row(3, .4, 50, .5, .3),
               _row(4, .3, 40, .4, .2)]
    readings = ss.stake_readings({"hungarian": hungarian, "identity": identity,
                                  "independent_nearest": nearest}, worlds)
    assert readings["better_free_rule"] == "identity"
    d_q = np.asarray([.1, -.02, .1, .05])      # hungarian - identity
    d_j = np.asarray([5.0, 10.0, 20.0, -1.0])
    s = readings["S"]
    assert s["sign"] == "hungarian - identity"
    assert s["qos_per_step"]["paired_mean"] == pytest.approx(d_q.mean())
    assert s["qos_per_step"]["paired_se"] == pytest.approx(d_q.std(ddof=1) / 2.0)
    assert s["qos_per_step"]["worlds_hungarian_leads"] == 3 and s["qos_per_step"]["n_worlds"] == 4
    assert s["raw_native_J"]["paired_mean"] == pytest.approx(d_j.mean())
    assert s["raw_native_J"]["paired_se"] == pytest.approx(d_j.std(ddof=1) / 2.0)
    assert s["raw_native_J"]["worlds_hungarian_leads"] == 3
    versus = readings["versus_hungarian"]["identity_minus_hungarian"]
    assert versus["qos_per_step"]["paired_mean"] == pytest.approx(-d_q.mean())
    assert versus["qos_per_step"]["worlds_difference_below_zero"] == 3
    assert versus["raw_native_J"]["worlds_difference_below_zero"] == 3
    assert versus["qos_per_step_pre_entry_difference"]["mean"] == pytest.approx(
        np.mean([-.05, -.02, -.1, -.05]))
    # world 3 has no post-input phase under hungarian: excluded and counted
    assert versus["qos_per_step_post_input_difference"] == pytest.approx(
        {"mean": np.mean([-.05, -.1, -.05]), "n_worlds": 3})
    near = readings["versus_hungarian"]["independent_nearest_minus_hungarian"]
    assert near["qos_per_step"]["paired_mean"] == pytest.approx(-.2)
    assert near["qos_per_step"]["worlds_difference_below_zero"] == 4
    per_mode = readings["per_mode"]["hungarian"]
    assert per_mode["qos_per_step"]["mean"] == pytest.approx(.65)
    assert per_mode["qos_per_step_post_input"] == pytest.approx(
        {"mean": np.mean([.7, .6, .4]), "n_worlds": 3, "per_world": [.7, .6, None, .4]})
    assert per_mode["qos_per_step_entry_to_input"]["mean"] is None
    assert per_mode["native_J_per_step"]["mean"] == pytest.approx(8.5)
    json.dumps(readings, allow_nan=False)
    # the other rule wins when its mean is higher; a failed world drops out of the pairs
    nearest_better = [_row(1, .9, 90), _row(2, .9, 70), _row(3, .9, 50), _row(4, 0, 0, failed=True)]
    flipped = ss.stake_readings({"hungarian": hungarian, "identity": identity,
                                 "independent_nearest": nearest_better}, worlds)
    assert flipped["better_free_rule"] == "independent_nearest"
    assert flipped["S"]["qos_per_step"]["n_worlds"] == 3
    assert flipped["S"]["qos_per_step"]["per_world"][3] is None
    assert flipped["per_mode"]["independent_nearest"]["failed_worlds"] == [4]
    # exact tie -> identity (the earlier free rule)
    tie = ss.stake_readings({"hungarian": hungarian, "identity": nearest,
                             "independent_nearest": nearest}, worlds)
    assert tie["better_free_rule"] == "identity"


def _recorded_panel(rows):
    return {"controller": "H1", "params": {"enter_margin": 0.0, "exit_margin": 0.05},
            "heuristic_params": H1.record(), "worlds": rows}


def test_consistency_check_both_branches(tmp_path):
    worlds = (955001, 955002)
    rows = [{"seed": 955001, "qos_per_step": 0.8, "raw_native_J": 2400.0},
            {"seed": 955002, "qos_per_step": 0.7, "raw_native_J": 2100.0}]
    path = tmp_path / "panel.json"
    path.write_text(json.dumps(_recorded_panel(rows)))
    ok = ss.consistency_check(rows, worlds, H1, path)
    assert ok["hungarian_matches_recorded"] is True and ok["differing_worlds"] == []
    close = [dict(rows[0], raw_native_J=2400.0 + 5e-10), rows[1]]
    assert ss.consistency_check(close, worlds, H1, path)["hungarian_matches_recorded"] is True
    off = [rows[0], dict(rows[1], qos_per_step=0.7 + 1e-6)]
    bad = ss.consistency_check(off, worlds, H1, path)
    assert bad["hungarian_matches_recorded"] is False
    assert bad["differing_worlds"] == [{"seed": 955002,
                                        "qos_per_step": {"stake": 0.7 + 1e-6, "recorded": 0.7},
                                        "raw_native_J": {"stake": 2100.0, "recorded": 2100.0}}]
    other_worlds = ss.consistency_check(rows[:1], worlds[:1], H1, path)
    assert other_worlds["hungarian_matches_recorded"] is False
    assert other_worlds["recorded_identity_problems"]
    missing = ss.consistency_check(rows, worlds, H1, tmp_path / "absent.json")
    assert missing["hungarian_matches_recorded"] is False and "unreadable" in missing["reason"]
    json.dumps([ok, bad, other_worlds, missing], allow_nan=False)


def test_recorded_stage1_panel_is_h_central_on_the_stake_worlds():
    """The tracked recorded panel passes the identity checks and agrees with itself."""
    path = ss.REPO_ROOT / ss.RECORDED_PANEL
    recorded = json.loads(path.read_text(encoding="utf-8"))
    assert [row["seed"] for row in recorded["worlds"]] == list(ss.STAKE_WORLDS)
    check = ss.consistency_check(recorded["worlds"], ss.STAKE_WORLDS, H1, path)
    assert check["recorded_identity_problems"] == []
    assert check["hungarian_matches_recorded"] is True and check["compared_worlds"] == 32


def test_runner_stake_sizing_arguments():
    args = entry.parse_args(["stake-sizing", "--out", "o", "--launch-sha", "s"])
    assert (args.command, args.workers, args.threads) == ("stake-sizing", 8, 2)
    for bad in (["stake-sizing", "--out", "o"],
                ["stake-sizing", "--out", "o", "--launch-sha", "s", "--worlds", "955001"],
                ["stake-sizing", "--out", "o", "--launch-sha", "s", "--mode", "identity"]):
        with pytest.raises(SystemExit):
            entry.parse_args(bad)


def test_runner_admission_precedes_stake_sizing(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    def refuse(*args, **kwargs):
        raise RuntimeError("no admission")

    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    target = tmp_path / "never-created"
    with pytest.raises(RuntimeError, match="no admission"):
        entry.main(["stake-sizing", "--out", str(target), "--launch-sha", "s"])
    assert not target.exists()
    order = []
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: order.append("admission") or {"sha": "s"})
    monkeypatch.setattr(ss, "run_stake_sizing", lambda **kwargs: order.append(kwargs) or {})
    entry.main(["stake-sizing", "--out", str(target), "--launch-sha", "s", "--workers", "4",
                "--threads", "1"])
    assert order[0] == "admission"
    assert {k: v for k, v in order[1].items() if k != "argv"} == \
           {"out": target, "launch_sha": "s", "workers": 4, "threads": 1}
    with pytest.raises(RuntimeError, match="admission"):
        entry.main(["stake-sizing", "--out", str(target), "--launch-sha", "other"])


def test_run_refuses_existing_output_and_bad_plans(tmp_path):
    out = tmp_path / "run"
    (out / ss.STAKE_PHASE).mkdir(parents=True)
    (out / ss.STAKE_PHASE / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError):
        ss.run_stake_sizing(out=out, launch_sha="s", workers=1, threads=1, worlds=(955001,))
    for kwargs in ({"worlds": (957001,)}, {"modes": ("identity",)}, {"workers": 64}):
        target = tmp_path / f"bad_{len(list(tmp_path.iterdir()))}"
        values = {"worlds": (955001,), "workers": 1} | kwargs
        with pytest.raises(ValueError):
            ss.run_stake_sizing(out=target, launch_sha="s", threads=1, **values)
        assert not target.exists()


def test_tiny_end_to_end_through_the_runner(tmp_path, monkeypatch):
    """Monkeypatched: STAKE_SPEC horizon 3000 -> 20 and the worlds 955001-955032 -> 955001-2."""
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "sha-e2e"})
    monkeypatch.setattr(ss, "STAKE_SPEC", replace(B01Spec(), horizon=20))
    original = ss.run_stake_sizing
    monkeypatch.setattr(ss, "run_stake_sizing",
                        lambda **kwargs: original(worlds=(955001, 955002), **kwargs))
    out = tmp_path / "e2e"
    summary = entry.main(["stake-sizing", "--out", str(out), "--launch-sha", "sha-e2e",
                          "--workers", "2", "--threads", "1"])
    root = out / ss.STAKE_PHASE
    assert summary["status"] == "COMPLETE" and summary["counts"]["episodes_completed"] == 6
    written = json.loads((root / "summary.json").read_text())
    config = json.loads((root / "config.json").read_text())
    assert written["status"] == "COMPLETE" and written["readings"] == \
        json.loads(json.dumps(summary["readings"]))
    assert config["planned_episodes"] == 6 and config["horizon"] == 20
    assert config["policy_seed"] == 925031 and config["modes"] == list(ASSIGNMENT_MODES)
    assert config["heuristic"] == H1.record() and config["params"] == \
        {"enter_margin": 0.0, "exit_margin": 0.05}
    assert config["launch_sha"] == "sha-e2e" and (config["workers"], config["threads"]) == (2, 1)
    for mode in ASSIGNMENT_MODES:
        panel = json.loads((root / "panels" / f"{mode}.json").read_text())
        assert panel["assignment_mode"] == mode and panel["controller"] == "H1"
        assert panel["worlds"] == [955001, 955002]
        assert [row["seed"] for row in panel["rows"]] == [955001, 955002]
        assert all(row["assignment_mode"] == mode and row["actual_length"] == 20
                   for row in panel["rows"])
        assert panel["aggregate"]["completed_worlds"] == 2
        with np.load(root / "traces" / f"{mode}.npz") as trace:
            assert trace["world_1_target_xy"].shape == (20, 8, 2)
            assert int(trace["world_0_seed"]) == 955001
    events = [json.loads(line) for line in (root / "progress.jsonl").read_text().splitlines()]
    ends = [event for event in events if event["event"] == "world_end"]
    assert len(ends) == 6 and all({"mode", "seed", "qos_per_step", "wall"} <= set(e) for e in ends)
    assert set(written["readings"]["per_mode"]) == set(ASSIGNMENT_MODES)
    assert written["readings"]["better_free_rule"] in ("identity", "independent_nearest")
    assert written["readings"]["S"]["qos_per_step"]["n_worlds"] == 2
    # tiny horizon and two worlds: the check runs, reports false, and never aborts
    assert written["hungarian_matches_recorded"] is False
    assert written["consistency_check"]["recorded_identity_problems"]
