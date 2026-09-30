"""Cell b05 arms L and D_100 (coupled_host_joint_skills_stage1): clock re-plans on an unchanged map
with the trigger active between, one call per decision, the shared cap, D_100's one-time harness
grant and its truth guard, the B0 reference regression, the reader-side split and the two-world
probe (1011, 1001) against the committed b04 reference and gate.

Stub checks use b04's scripted fixture on a shortened host (world 9103, budget 60) with shortened
clock steps; the reference-regression and probe tests use the committed runs.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1 import b05_sighting_ceiling as B5
from experiments.candidates.coupled_host_joint_skills_stage1 import run_b05
from experiments.candidates.coupled_host_replan_timing import rules as R

from tests.experiments.candidates.coupled_host_joint_skills_stage1.test_b04_lawful_sensing import (  # noqa: F401,E501
    # fixtures re-used by name
    BUDGET,
    WORLD,
    TruthAccess,
    scripted,
    small_host,
    truth_guard,
)

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "runs" / "coupled_host_joint_skills_stage1"
GATE = RUNS / "b01_gate_dev_a01"
REFERENCE = RUNS / "b04_b0_dev_a01"
CLOCK = (10, 20, 30, 40)
STEPS = 50


def drive(env, cls, steps=STEPS, truth=None, **kwargs):
    result, rec = B5.run_arm(env, cls, WORLD, BUDGET, steps, users_truth=truth,
                             clock_steps=CLOCK, **kwargs)
    return result, rec


def test_declared_constants():
    assert B5.CLOCK_STEPS == (100, 200, 300, 400) and B5.GRANT_STEP == 100
    assert B5.MAX_REPLANS == B4.MAX_REPLANS == 20
    assert B5.FOCUS_WORLDS == (1008, 1011, 1029, 1031) and B5.SPLIT_MIN_NEVER_SIGHTED == 5
    arm = B5.LArm(small_host(), WORLD, BUDGET)
    assert arm.clock_steps == B5.CLOCK_STEPS and arm.max_replans == 20
    assert B5.D100Arm(small_host(), WORLD, BUDGET).grant_step == 100
    with pytest.raises(ValueError, match="clock step"):
        B5.D100Arm(small_host(), WORLD, BUDGET, grant_step=150)


# ------------------------------------------------------------------------------ (a) L


def test_l_replans_at_every_clock_step_on_an_unchanged_map(scripted):
    script, calls = scripted
    script[0] = {u: (float(u), 0.0) for u in range(6)}                   # first plan at 0
    script[15] = {6: (6.0, 0.0), 7: (7.0, 0.0), 8: (8.0, 0.0)}             # trigger between clocks
    script[25] = {9: (9.0, 0.0), 10: (10.0, 0.0)}                           # 2 new: no trigger
    script[30] = {11: (11.0, 0.0)}                                          # 3rd new AT a clock
    _result, rec = drive(small_host(), B5.LArm)
    kinds = [(p["decision_step"], p["kind"], p["trigger_fired"]) for p in rec["plans"]]
    assert kinds == [(0, "trigger", True), (10, "clock", False), (15, "trigger", True),
                     (20, "clock", False), (30, "clock", True), (40, "clock", False)]
    assert rec["clock_plan_steps"] == [10, 20, 30, 40] and rec["trigger_steps"] == [0, 15]
    assert rec["replans"] == 6 == len(calls) and rec["replans_by_kind"] == {"trigger": 2, "clock": 4}
    assert [len(c) for c in calls] == [6, 6, 9, 9, 12, 12]                 # 10/20/40: unchanged map
    assert rec["evaluations_used"] == 6 * 14 and not rec["cap_hit"]


def test_l_equals_b0_before_the_first_clock_and_b0_is_untouched(scripted):
    script, _calls = scripted
    script[0] = {u: (float(u), 0.0) for u in range(6)}
    script[5] = {6: (6.0, 0.0), 7: (7.0, 0.0), 8: (8.0, 0.0)}
    b0_env, l_env = small_host(), small_host()
    b0 = B4.B0Arm(b0_env, WORLD, BUDGET)
    r0 = R.rollout(b0_env, b0.targets, 0, STEPS)
    rl, rec = drive(l_env, B5.LArm)
    assert r0["coverage_backhauled"][:CLOCK[0]] == rl["coverage_backhauled"][:CLOCK[0]]
    assert [p["decision_step"] for p in b0.plans] == [0, 5]
    assert "kind" not in b0.plans[0]                                       # B0 records unchanged
    assert rec["plan_steps"] == [0, 5, 10, 20, 30, 40]


def test_clock_calls_count_toward_the_cap(scripted):
    script, calls = scripted
    script[0] = {u: (float(u), 0.0) for u in range(6)}                   # triggers at 0, 2, 4, 6
    for k in (1, 2, 3):
        script[2 * k] = {3 + 3 * k + j: (float(k), float(j)) for j in range(3)}
    _result, rec = drive(small_host(), B5.LArm, max_replans=5)
    assert rec["plan_steps"] == [0, 2, 4, 6, 10] and len(calls) == 5
    assert rec["cap_hit"] and [h["step"] for h in rec["cap_hits"]] == [20, 30, 40]
    assert all(h["kind"] == "clock" for h in rec["cap_hits"])


# ------------------------------------------------------------------------------ (b) D_100


def test_d100_grant_at_the_grant_step_only_and_no_trigger_after(scripted):
    script, calls = scripted
    env = small_host()
    truth = np.array(env.user_positions, dtype=float, copy=True)
    script[0] = {u: tuple(truth[u]) for u in range(8)}
    script[3] = {u: tuple(truth[u]) for u in range(8, 11)}                  # trigger at 3
    script[25] = {u: tuple(truth[u]) for u in range(11, 20)}                # would trigger in L
    _result, rec = drive(env, B5.D100Arm, truth=truth, grant_step=10)
    assert rec["privileged_grant"]["step"] == 10 and rec["privileged_grant"]["users"] == env.n_users
    assert rec["privileged_grant"]["newly_known"] == env.n_users - 11
    assert rec["privileged_grant"]["sighted_xy_differing_from_truth"] == 0
    assert rec["trigger_steps"] == [0, 3] and rec["clock_plan_steps"] == [10, 20, 30, 40]
    assert [len(c) for c in calls] == [8, 11, 50, 50, 50, 50]
    assert np.array_equal(calls[2], truth)                                 # full map in index order
    assert rec["plans"][2]["trigger_fired"] is True                         # one call, kind clock
    l_rec = drive(small_host(), B5.LArm)[1]
    assert l_rec["trigger_steps"] == [0, 3, 25]                             # control: L does trigger


def test_grant_truth_contract():
    env = small_host()
    arm = B5.D100Arm(env, WORLD, BUDGET, clock_steps=CLOCK, grant_step=10)
    with pytest.raises(AssertionError, match="declared"):
        B5.grant_truth(arm, np.zeros((50, 2)), 9)
    B5.grant_truth(arm, np.zeros((50, 2)), 10)
    with pytest.raises(AssertionError, match="one-time"):
        B5.grant_truth(arm, np.zeros((50, 2)), 10)
    with pytest.raises(TypeError):
        B5.grant_truth(B5.LArm(small_host(), WORLD, BUDGET), np.zeros((50, 2)), 100)
    with pytest.raises(ValueError, match="only D_100"):
        B5.run_arm(small_host(), B5.LArm, WORLD, BUDGET, 5, users_truth=np.zeros((50, 2)))
    silent = B5.D100Arm(small_host(), WORLD, BUDGET, clock_steps=CLOCK, grant_step=10)
    with pytest.raises(AssertionError, match="no grant"):                  # the grant is mandatory
        R.rollout(silent.env, silent.targets, 0, 12)


def test_d100_never_reads_user_positions(truth_guard):
    env = small_host()
    truth = np.array(env.user_positions, dtype=float, copy=True)            # harness set-up read
    truth_guard["live"] = env
    with pytest.raises(TruthAccess):                                        # negative control
        _ = env.user_positions
    result, rec = B5.run_arm(env, B5.D100Arm, WORLD, BUDGET, STEPS, users_truth=truth,
                             clock_steps=CLOCK, grant_step=10)
    truth_guard["live"] = None
    assert result["t_end"] == STEPS and rec["privileged_grant"]["step"] == 10
    assert truth_guard["accessor_calls"] == STEPS + 1 and truth_guard["rows_read"] > 0
    assert rec["clock_plan_steps"] == list(CLOCK)
    assert all(p["n_known"] == env.n_users for p in rec["plans"] if p["decision_step"] >= 10)
    assert all(p["kind"] == "clock" for p in rec["plans"] if p["decision_step"] >= 10)


# ------------------------------------------------------------------------------ (c) reference regression


@pytest.mark.skipif(not (REFERENCE / "worlds" / "1011.json").exists(), reason="reference absent")
def test_b0_reference_mismatch_raises():
    ref = json.loads((REFERENCE / "worlds" / "1011.json").read_text())
    b0 = copy.deepcopy(ref["B0"])
    B5.check_b0_reference(1011, b0, ref)                                   # identical: passes
    bad = copy.deepcopy(b0)
    bad["coverage_backhauled"][250] += 0.02
    with pytest.raises(AssertionError, match="world 1011.*series"):
        B5.check_b0_reference(1011, bad, ref)
    bad = copy.deepcopy(b0)
    bad["first_known_step"].pop(next(iter(bad["first_known_step"])))
    with pytest.raises(AssertionError, match="first_known_step"):
        B5.check_b0_reference(1011, bad, ref)
    with pytest.raises(AssertionError, match="world"):
        B5.check_b0_reference(1012, b0, ref)


@pytest.mark.skipif(not (REFERENCE / "worlds" / "1011.json").exists(), reason="reference absent")
def test_run_world_raises_on_a_perturbed_reference(monkeypatch):
    gate = json.loads((GATE / "worlds" / "1011.json").read_text())
    ref = json.loads((REFERENCE / "worlds" / "1011.json").read_text())
    ref["B0"]["coverage_backhauled"][-1] += 0.02
    ran = []
    monkeypatch.setattr(B5, "run_arm", lambda *a, **k: ran.append(1))
    with pytest.raises(AssertionError, match="world 1011: B0 differs"):
        B5.run_world_b05(1011, 3000, gate=gate, reference_world_record=ref)
    assert not ran                                                          # raised before L / D_100


@pytest.mark.skipif(not (REFERENCE / "summary.json").exists(), reason="reference absent")
def test_split_flag_matches_the_declared_counts():
    flagged = []
    for world in (1001, 1011, 1026):
        gate = json.loads((GATE / "worlds" / f"{world}.json").read_text())
        ref = json.loads((REFERENCE / "worlds" / f"{world}.json").read_text())
        split = B5.split_flag(world, gate, ref)
        flagged.append(split["f_backhauls_ge5_never_sighted"])
        if world == 1001:
            assert split["f_backhauled_never_sighted"] == 0                 # Oracle item 2 (iv)
        if world == 1011:
            assert split["f_backhauled_never_sighted"] == 20                # NOTES b04 check
    assert flagged == [False, True, False]


# ------------------------------------------------------------------------------ (d) two-world probe


@pytest.mark.skipif(not (REFERENCE / "summary.json").exists() or not (GATE / "summary.json").exists(),
                    reason="gate or reference absent")
def test_two_world_probe_end_to_end(tmp_path, monkeypatch):
    monkeypatch.delenv(run_b05.ADMISSION_ENV, raising=False)
    out = tmp_path / "probe"
    assert run_b05.main(["--worlds", "1011", "1001", "--out", str(out), "--budget", "3000",
                         "--launch-sha", "test"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["worlds"] == [1011, 1001] and summary["training_fits_performed"] == 0
    assert summary["regression_equals_gate_all_worlds"] is True
    assert summary["b0_equals_reference_all_worlds"] is True
    for key in ("per_world", "means", "cpu_seconds", "wall_clock_s", "git_head", "launch_sha",
                "arguments", "interpreter", "definitions", "information_contract", "gate_run",
                "reference_run", "timing_totals"):
        assert key in summary
    contract = summary["information_contract"]
    assert contract["clock_steps"] == [100, 200, 300, 400] and contract["max_replans"] == 20
    assert len(contract["reference_run_summary_sha256"]) == 64
    for block in (summary["means"]["stakes"],
                  summary["means"]["stakes_split_f_backhauls_ge5_never_sighted"]["true"],
                  summary["means"]["stakes_focus_worlds"]):
        for stake in run_b05.STAKES:
            assert set(block[stake]) >= {"mean", "sd", "min", "max", "n", "n_positive"}
    assert summary["means"]["stakes_focus_worlds"]["worlds"] == [1011]
    reference = {w: json.loads((REFERENCE / "worlds" / f"{w}.json").read_text()) for w in (1011, 1001)}
    for row in summary["per_world"]:
        arms, stakes = row["arms"], row["stakes"]
        assert set(arms) == {"B0", "L", "D100"}
        for arm in arms.values():
            assert set(run_b05.ARM_ROW_KEYS) <= set(arm)
            assert arm["replans"] <= 20 and not arm["cap_hit"]
        assert arms["B0"]["all_mean"] == reference[row["world"]]["B0"]["all_mean"]
        assert stakes["c_ceil"] == arms["D100"]["all_mean"] - arms["L"]["all_mean"]
        assert stakes["delta_l"] == arms["L"]["all_mean"] - arms["B0"]["all_mean"]
        assert stakes["f_minus_d100"] == row["F"]["all_mean"] - arms["D100"]["all_mean"]
        assert stakes["c_ceil_final100"] == (arms["D100"]["final_100_mean"]
                                             - arms["L"]["final_100_mean"])
        assert row["F"]["regression_all_mean"] == row["F"]["gate_all_mean"] == row["F"]["all_mean"]
        assert row["D100_privileged_grant"]["step"] == 100 and row["D100_privileged_grant"]["users"] == 50
        assert [p["step"] for p in arms["L"]["plans"] if p["kind"] == "clock"] == [100, 200, 300, 400]
        assert [p["step"] for p in arms["D100"]["plans"] if p["kind"] == "clock"] == [100, 200, 300, 400]
        assert all(p["n_known"] == 50 for p in arms["D100"]["plans"] if p["step"] >= 100)
        assert not [p for p in arms["D100"]["plans"] if p["step"] > 100 and p["kind"] == "trigger"]
        assert len(row["reference_file_sha256"]) == 64
    by_world = {r["world"]: r for r in summary["per_world"]}
    assert by_world[1011]["split"]["f_backhauls_ge5_never_sighted"] is True
    assert by_world[1001]["split"]["f_backhauls_ge5_never_sighted"] is False
    world = json.loads((out / "worlds" / "1011.json").read_text())
    assert all(len(world["arms"][a]["coverage_backhauled"]) == 500 for a in ("B0", "L", "D100"))
    # refuses to overwrite; refuses a cap the reference run was not made at
    assert run_b05.main(["--worlds", "1011", "--out", str(out)]) == 2
    assert run_b05.main(["--worlds", "1011", "--out", str(tmp_path / "b"), "--max-replans", "5"]) == 2
