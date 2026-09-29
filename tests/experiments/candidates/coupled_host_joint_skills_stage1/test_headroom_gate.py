"""T-G headroom gate: planner helpers and run_headroom_gate.py (coupled_host_joint_skills_stage1).

World seeds used here are outside the declared dev (1000-1031) and hold-out (2000-2031)
panels.  The runner smokes need pytest's --basetemp under this checkout's temp/ (the smoke
path refuses outputs elsewhere).
"""

from __future__ import annotations

import json
from fractions import Fraction
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import experiments.candidates.coupled_host_joint_skills_stage1.run_headroom_gate as gate
from experiments.candidates.coupled_host_joint_skills_stage1.host import make_host, static_evaluate
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    XY_STEPS_M,
    closed_loop_execute,
    retargeting_closed_loop_execute,
    search_placement,
)

ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "experiments" / "candidates" / "coupled_host_joint_skills_stage1" / "run_headroom_gate.py"
GATE = ROOT / "experiments" / "candidates" / "coupled_host_joint_skills_stage1" / "run_gate.py"
DIRECTION = "coupled_host_joint_skills_stage1"


def _python() -> str:
    return sys.executable


# ------------------------------------------------------------------------------ planner helpers


def test_default_xy_steps_argument_is_the_old_behaviour():
    env = make_host(9311)
    implicit = search_placement(env, True, 400, np.random.default_rng(9311))
    explicit = search_placement(env, True, 400, np.random.default_rng(9311), xy_steps_m=XY_STEPS_M)
    assert np.array_equal(implicit.positions_xyz, explicit.positions_xyz)
    assert implicit.history == explicit.history and implicit.starts == explicit.starts
    assert "xy_steps_m" not in implicit.to_json()  # default outputs keep their key set
    with pytest.raises(ValueError):
        search_placement(env, True, 400, np.random.default_rng(9311), xy_steps_m=())


def test_headroom_search_extends_the_reference_search():
    """Same rng, same flat incumbent, starts >= 3, a prefix-extended step schedule: r cannot fall."""
    world = 9312
    env = make_host(world)
    flat = search_placement(env, False, 3000, np.random.default_rng(world))
    relay = search_placement(env, True, 3000, np.random.default_rng(world),
                             extra_candidates=[flat.positions_xyz])
    assert relay.candidates_evaluated == len(relay.candidates)
    wide = search_placement(env, True, 9000, np.random.default_rng(world), n_starts=6,
                            extra_candidates=[flat.positions_xyz],
                            xy_steps_m=XY_STEPS_M + (10.0,))
    assert wide.evaluations <= 9000
    assert wide.contract_reward >= relay.contract_reward
    assert wide.to_json()["xy_steps_m"] == [100.0, 50.0, 25.0, 10.0]
    # The first three starts are the reference's, each continued from its converged point.
    for ref_start, wide_start in zip(relay.starts, wide.starts[:3]):
        assert ref_start["candidate_index"] == wide_start["candidate_index"]
        assert wide_start["final_reward"] >= ref_start["final_reward"]


def test_identity_correction_reproduces_closed_loop_execute_bit_for_bit():
    world = 9313
    env = make_host(world)
    targets = search_placement(env, True, 200, np.random.default_rng(world)).positions_xyz
    reference = closed_loop_execute(env, targets)
    eval_env = make_host(world)
    calls: list[int] = []

    def identity(t, assigned):
        calls.append(t)
        static_evaluate(eval_env, assigned, allow_a2a=True)  # must not touch the episode env
        return assigned

    corrected = retargeting_closed_loop_execute(env, targets, identity, 10)
    assert calls == list(range(0, 500, 10))
    assert corrected["series"] == reference["series"]
    assert corrected["final_positions_xyz"] == reference["final_positions_xyz"]
    assert corrected["arrival_step"] == reference["arrival_step"]
    assert corrected["target_permutation"] == reference["target_permutation"]
    assert max(corrected["final_target_drift_from_anchor_m"]) == 0.0
    assert all(d["moved_uavs"] == 0 for d in corrected["decisions"])


def test_retargeting_follows_moved_targets():
    world = 9314
    env = make_host(world)
    targets = np.array(env.uav_positions, dtype=float)  # hold at the start ...

    def shift(t, assigned):
        if t == 20:
            assigned[0, 0] = min(assigned[0, 0] + 90.0, env.area_size)  # ... then move UAV 0
        return assigned

    result = retargeting_closed_loop_execute(env, targets, shift, 10, max_steps=40,
                                             assignment="identity")
    assert result["decisions"][2] == {"t": 20, "moved_uavs": 1}
    assert result["final_max_distance_to_target_m"] <= 1e-6
    with pytest.raises(ValueError):
        retargeting_closed_loop_execute(env, targets, shift, 0)


# ------------------------------------------------------------------------------ correction sweep


def test_local_target_sweep_improves_and_respects_the_cap():
    world = 9315
    env = make_host(world)
    anchor = search_placement(env, True, 300, np.random.default_rng(world)).positions_xyz
    eval_env = make_host(world)
    new, record = gate.local_target_sweep(eval_env, anchor)
    assert record["evaluations"] <= 1 + 6 * 26 <= gate.CORRECTION_MAX_EVALUATIONS
    assert len(gate.CORRECTION_OFFSETS) == 26
    before = static_evaluate(make_host(world), anchor)["backhauled_users"]
    after = static_evaluate(make_host(world), new)["backhauled_users"]
    assert record["static_before"]["backhauled_users"] == before
    assert record["static_after"]["backhauled_users"] == after
    assert after >= before
    assert (after > before) == bool(record["moves"])  # moves only on a strict count increase
    moved = {m["uav"] for m in record["moves"]}
    for uav in range(6):
        delta = new[uav] - anchor[uav]
        if uav in moved:
            assert np.all(np.abs(delta[:2]) <= 25.0) and abs(delta[2]) <= 50.0
        else:
            assert np.array_equal(new[uav], anchor[uav])
    assert np.all(new[:, 2] >= 50.0) and np.all(new[:, 2] <= 150.0)
    with pytest.raises(ValueError):
        gate.local_target_sweep(eval_env, anchor, max_evaluations=100)


def test_sweep_skips_offsets_outside_the_feasible_set(monkeypatch):
    world = 9316
    anchor = search_placement(make_host(world), True, 300, np.random.default_rng(world)).positions_xyz
    anchor = np.array(anchor, dtype=float)
    anchor[:, 0] = np.clip(anchor[:, 0], 400.0, 4600.0)
    anchor[:, 2] = 75.0
    assigned = anchor.copy()
    assigned[0, 0] += 290.0  # UAV 0 is 10 m inside the 300 m disc
    assigned[0, 2] += 50.0  # and on the |dz| = 50 m bound (125 m; +z clips to 150 m, dz 75 m)
    seen: list[np.ndarray] = []

    import experiments.candidates.coupled_host_joint_skills_stage1.host as host_module

    original = host_module.static_evaluate

    def spy(env, positions, allow_a2a=True):
        seen.append(np.array(positions, dtype=float))
        return original(env, positions, allow_a2a=allow_a2a)

    monkeypatch.setattr(host_module, "static_evaluate", spy)
    new, record = gate.local_target_sweep(make_host(world), assigned, anchor=anchor)
    for positions in seen:
        for uav in range(6):
            assert gate.inside_feasible_set(positions[uav], anchor[uav])
    # UAV 0: every +x offset (315 m) and every +z offset (|dz| = 100 m) is skipped.
    assert record["skipped_infeasible"] >= 9 + 9 - 3  # dx = +1 or dz = +1 for UAV 0
    assert record["max_xy_drift_m"] <= 300.0 and record["max_abs_dz_m"] <= 50.0
    assert all(gate.inside_feasible_set(new[i], anchor[i]) for i in range(6))
    outside = assigned.copy()
    outside[1, 1] += 301.0
    with pytest.raises(ValueError):
        gate.local_target_sweep(make_host(world), outside, anchor=anchor)


def test_kill_reading_is_exact_on_the_thresholds():
    # 32 worlds, each one user better statically (1/50 = .02 exactly) and a closed-loop gain of
    # exactly .01: both conditions sit on the threshold -> not bought.
    reading = gate.kill_reading([1] * 32, [250] * 32, [500] * 32, 50)
    assert reading["mean_H_static_cbh_exact"] == "1/50" and reading["mean_H_corr_exact"] == "1/100"
    assert reading["d1prime_not_bought"] is True
    assert 0.72 - 0.70 > 0.02  # the float reading would have been on the wrong side
    one_more = gate.kill_reading([1] * 31 + [2], [250] * 32, [500] * 32, 50)
    assert one_more["static_condition_met"] is False and one_more["d1prime_not_bought"] is False
    corr_over = gate.kill_reading([0] * 32, [250] * 31 + [251], [500] * 32, 50)
    assert corr_over["corr_condition_met"] is False and corr_over["d1prime_not_bought"] is False
    assert Fraction(corr_over["mean_H_corr_exact"]) == Fraction(250 * 32 + 1, 32 * 500 * 50)
    assert gate.coverage_counts([0.7, 0.72, 0.0, 1.0], 50) == [35, 36, 0, 50]
    with pytest.raises(AssertionError):
        gate.coverage_counts([0.701], 50)


def test_canonical_paths_map_snapshot_worktrees_back():
    snap = Path("/x/checkout/.git/hmasd-launch-sources/abc")
    assert gate.canonical_data_root(snap) == Path("/x/checkout")
    assert gate.canonical_data_root(Path("/x/checkout")) == Path("/x/checkout")
    assert gate.resolve_input(snap / "runs" / "r") == Path("/x/checkout/runs/r")


# ------------------------------------------------------------------------------ runner


def _reference(tmp: Path, worlds: list[str], budget: int) -> Path:
    ref = tmp / "reference"
    completed = subprocess.run(
        [_python(), str(GATE), "--worlds", *worlds, "--budget", str(budget), "--out", str(ref),
         "--smoke-no-admission"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert completed.returncode == 0, completed.stderr
    return ref


def test_headroom_runner_smoke_writes_json(tmp_path):
    ref = _reference(tmp_path, ["9321", "9322"], 300)
    out = tmp_path / "headroom"
    completed = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9321", "9322", "--budget", "300",
         "--headroom-budget", "900", "--headroom-starts", "6", "--reference-dir", str(ref),
         "--out", str(out), "--smoke-no-admission"],
        cwd=ROOT, capture_output=True, text=True, timeout=900)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["worlds"] == [9321, 9322]
    assert summary["training_fits_performed"] == 0 and summary["launch_sha"] is None
    assert summary["panel"].startswith("other")
    assert summary["reference"]["reproduced_bit_for_bit"] is True
    assert set(summary["reference"]["world_sha256"]) == {"9321", "9322"}
    assert summary["headroom_search"]["xy_steps_m"] == [100.0, 50.0, 25.0, 10.0]
    assert summary["evaluations"]["correction_max_per_decision"] <= 300
    h_static, h_corr = [], []
    for world in (9321, 9322):
        row = json.loads((out / "worlds" / f"{world}.json").read_text(encoding="utf-8"))
        sealed = json.loads((ref / "worlds" / f"{world}.json").read_text(encoding="utf-8"))
        assert row["reference_static"]["coverage_backhauled"] == sealed["static"]["P_relay"]["coverage_backhauled"]
        assert row["H_static_cbh"] == pytest.approx(
            row["headroom_static"]["coverage_backhauled"] - row["reference_static"]["coverage_backhauled"],
            rel=0, abs=1e-15)
        assert Fraction(row["H_static_cbh_exact"]) == Fraction(row["H_static_backhauled_user_diff"], 50)
        assert Fraction(row["H_corr_exact"]) == Fraction(
            row["H_corr_backhauled_user_step_diff_sum"], 500 * 50)
        assert row["correction"]["max_xy_drift_m"] <= 300.0
        assert row["correction"]["max_abs_dz_m"] <= 50.0
        assert max(row["corrected_closed_loop"]["final_target_drift_from_anchor_m"]) <= 300.0 + 50.0
        assert row["anchor_closed_loop"]["coverage_backhauled_mean_all"] == \
            sealed["closed_loop"]["closed_loop_relay"]["coverage_backhauled_mean_all"]
        assert row["H_corr"] == pytest.approx(
            float(np.mean(row["corrected_closed_loop"]["series"]["coverage_backhauled"]))
            - row["anchor_closed_loop"]["coverage_backhauled_mean_all"], rel=0, abs=1e-12)
        assert row["headroom_static"]["evaluations"] <= 900
        decisions = row["correction"]["decisions"]
        assert [d["t"] for d in decisions] == list(range(0, 500, 10))
        assert all(d["evaluations"] <= 300 for d in decisions)
        assert row["correction"]["evaluations_total"] == sum(d["evaluations"] for d in decisions)
        h_static.append(row["H_static_cbh"])
        h_corr.append(row["H_corr"])
    assert summary["H_static_cbh"]["mean"] == pytest.approx(np.mean(h_static), rel=0, abs=1e-12)
    assert summary["H_corr"]["mean"] == pytest.approx(np.mean(h_corr), rel=0, abs=1e-12)
    kill = summary["kill_rule"]
    assert kill["H_static_cbh_threshold"] == "1/50" and kill["H_corr_threshold"] == "1/100"
    assert "comparison_tolerance" not in kill
    assert kill["d1prime_not_bought"] == (Fraction(kill["mean_H_static_cbh_exact"]) <= Fraction(1, 50)
                                          and Fraction(kill["mean_H_corr_exact"]) <= Fraction(1, 100))
    assert {"reproduction", "headroom_search", "corrected_closed_loop"} <= set(summary["timing_per_world"])
    # A second run into the same directory is refused without --force.
    again = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9321", "--budget", "300", "--headroom-budget", "900",
         "--reference-dir", str(ref), "--out", str(out), "--smoke-no-admission"],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert again.returncode == 2


def test_headroom_runner_stops_on_a_reference_mismatch(tmp_path):
    ref = _reference(tmp_path, ["9323"], 60)
    path = ref / "worlds" / "9323.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    row["static"]["P_relay"]["positions_xyz"][0][0] += 1e-9
    path.write_text(json.dumps(row), encoding="utf-8")
    out = tmp_path / "headroom"
    completed = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9323", "--budget", "60", "--headroom-budget", "120",
         "--reference-dir", str(ref), "--out", str(out), "--smoke-no-admission"],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert completed.returncode == 4
    assert "P_relay.positions_xyz" in completed.stderr
    assert not out.exists()
    missing = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9324", "--budget", "60", "--headroom-budget", "120",
         "--reference-dir", str(ref), "--out", str(out), "--smoke-no-admission"],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert missing.returncode == 4 and not out.exists()


@pytest.mark.parametrize("worlds, out_kind", [
    (["1000"], "temp"), (["2031"], "temp"), (["9301"], "outside"),
])
def test_smoke_path_refuses_panels_and_non_temp_output(tmp_path, worlds, out_kind):
    out = tmp_path / "refused" if out_kind == "temp" else ROOT / "runs" / DIRECTION / "never-created"
    completed = subprocess.run(
        [_python(), str(RUNNER), "--worlds", *worlds, "--budget", "3", "--headroom-budget", "3",
         "--out", str(out), "--smoke-no-admission"], cwd=ROOT, capture_output=True, text=True,
        timeout=120)
    assert completed.returncode == 2
    assert not out.exists()


def test_admitted_run_requires_declared_budgets_and_admission(tmp_path):
    shrunk = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9301", "--budget", "300", "--out", str(tmp_path / "x")],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert shrunk.returncode == 2 and "declared budgets" in shrunk.stderr
    unadmitted = subprocess.run(
        [_python(), str(RUNNER), "--worlds", "9301", "--out", str(tmp_path / "x")],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert unadmitted.returncode != 0
    assert not (tmp_path / "x").exists()


def test_headroom_runner_has_exactly_one_admission_literal():
    from scripts.hmasd_launch import _validate_guard_contract

    _validate_guard_contract(RUNNER, DIRECTION)
    text = RUNNER.read_text(encoding="utf-8")
    assert text.count('require_admission(__file__, direction="coupled_host_joint_skills_stage1")') == 1
