import math
from pathlib import Path

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_pcpv.config import (
    CHURN_CELLS, EVAL_CELLS, MAX_EPISODES, MAX_TICKS, ROOT_LABELS,
    SCRIPTED_EPISODES, cell_name,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.inference import (
    complete_inference, interval, stage_a_inference,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.run import (
    WallDeadline, WallLimitExceeded, WorkCounter, validate_output_path,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.training import train_arm
import experiments.candidates.roster_consistent_latent_exploration_pcpv.run as run_module


def _ep(tau, loss, frag=0.0):
    return {"tau": float(tau), "U": float(loss), "F": float(frag), "Y": 0.5}


def _panels(mode="rekey"):
    stage_a = {}
    learned = {}
    for root in ROOT_LABELS:
        scripted = {}
        for package in ("CARRY", "REPLAN", "FRAGMENTED", "NEAREST"):
            scripted[package] = {}
            for cell in EVAL_CELLS:
                churn = cell in CHURN_CELLS
                if package == "CARRY": value = _ep(0, 0)
                elif package == "REPLAN": value = _ep(4 if churn else 0, 0)
                elif package == "FRAGMENTED": value = _ep(5 if churn else 0,
                                                            0.05 if churn else 0)
                else: value = _ep(20, 0.2, 0.2)
                scripted[package][cell_name(cell)] = value
        stage_a[root] = scripted
        arms = {"KEEP": {}, "FLEX": {}, "CLAMP": {}}
        for cell in EVAL_CELLS:
            churn = cell in CHURN_CELLS
            keep = _ep(0, 0.04, 0.0)
            flex = _ep(5, 0.05, 0.1)
            clamp = _ep(0, 0.04, 0.0)
            if mode == "geometry": clamp = _ep(5, 0.05, 0.1)
            elif mode == "package": clamp = _ep(2, 0.08, 0.05)
            elif mode == "flex":
                keep, flex, clamp = _ep(5, 0.05), _ep(0, 0.04), _ep(0, 0.04)
            elif mode == "no_material_fragment":
                keep, flex, clamp = _ep(5, 0.05, 0), _ep(5, 0.05, 0.1), _ep(5, 0.05)
            elif mode == "no_material":
                keep = flex = clamp = _ep(5, 0.05, 0)
            elif mode == "unresolved":
                keep, flex, clamp = _ep(5, 0.05), _ep(6.5, 0.08), _ep(6, 0.07)
            elif mode == "incompetent":
                keep, flex, clamp = _ep(0, 0), _ep(18, 0.13), _ep(18, 0.13)
            arms["KEEP"][cell_name(cell)] = keep
            arms["FLEX"][cell_name(cell)] = flex
            if churn:
                arms["CLAMP"][cell_name(cell)] = clamp
        learned[root] = arms
    return stage_a, learned


def test_stage_a_gates_tail_count_and_complete_branch_precedence():
    stage_a, learned = _panels("rekey")
    gates = stage_a_inference(stage_a)
    assert len(gates["tails"]) == 32
    assert gates["assay_sensitivity"]
    assert gates["public_scaffold"]
    assert gates["physical_persistence_opportunity"]
    assert complete_inference(stage_a, learned,
                              gates["physical_winning_paths"])["branch"] == \
        "KEEP_TARGET_ALIGNED_REKEY_VALUE"
    expected = {
        "geometry": "KEEP_TRAINING_GEOMETRY_VALUE",
        "package": "KEEP_PACKAGE_ONLY",
        "flex": "FLEX_CONTAINING_SUPERIOR",
        "no_material_fragment": "FRAGMENTATION_WITHOUT_DIRECT_VALUE",
        "no_material": "TARGET_SPECIFIC_NO_MATERIAL",
        "unresolved": "TARGET_UNRESOLVED",
        "incompetent": "FLEX_COMPETENCE_NOT_ESTABLISHED",
    }
    for mode, branch in expected.items():
        stage_a, learned = _panels(mode)
        result = complete_inference(stage_a, learned, ["5->10", "10->5"])
        assert len(result["tails"]) == 70
        assert result["branch"] == branch

    stage_a, learned = _panels("rekey")
    for root in ROOT_LABELS:
        for cell in CHURN_CELLS:
            stage_a[root]["FRAGMENTED"][cell_name(cell)] = _ep(0, 0)
    assert complete_inference(stage_a, learned, ["5->10"])["branch"] == \
        "ASSAY_SENSITIVITY_NOT_ESTABLISHED"


def test_nonfinite_rejected_and_stage_conditional_work_arithmetic():
    with pytest.raises(ValueError):
        interval([0.0] * 15 + [math.nan])
    work = WorkCounter()
    work.add(SCRIPTED_EPISODES)
    work.require(SCRIPTED_EPISODES)
    work.add(MAX_EPISODES - SCRIPTED_EPISODES)
    work.require(MAX_EPISODES)
    assert work.ticks == MAX_TICKS
    with pytest.raises(RuntimeError):
        work.add(1)


def test_monotonic_wall_enforcer_and_output_confinement(tmp_path):
    now = [10.0]
    deadline = WallDeadline(5.0, clock=lambda: now[0])
    deadline.check()
    now[0] = 15.0
    with pytest.raises(WallLimitExceeded):
        deadline.check()
    allowed = tmp_path.joinpath(
        "temp", "directions", "roster_consistent_latent_exploration", "exp",
        "2026-08-28.10-clean-01a04a02-rcle-public-plan-01", "result.json")
    assert validate_output_path(allowed, tmp_path) == allowed.resolve()
    with pytest.raises(ValueError):
        validate_output_path(tmp_path / "result.json", tmp_path)
    with pytest.raises(ValueError):
        validate_output_path(allowed.with_name("other.json"), tmp_path)


def test_stage_a_orchestration_stops_or_requires_complete_stage_b(monkeypatch, tmp_path):
    stage_a, learned = _panels("rekey")
    failed_stage_a = {
        root: {package: {cell: dict(value) for cell, value in cells.items()}
               for package, cells in packages.items()}
        for root, packages in stage_a.items()
    }
    for root in ROOT_LABELS:
        for cell in CHURN_CELLS:
            failed_stage_a[root]["FRAGMENTED"][cell_name(cell)] = _ep(0, 0)

    calls = []
    def fail_map(function, arguments, workers, deadline):
        calls.append(function.__name__)
        assert function is run_module._stage_a_root
        return [(root, failed_stage_a[root], 0) for root in ROOT_LABELS]

    monkeypatch.setattr(run_module, "_parallel_map", fail_map)
    result = run_module.execute(1, 30.0, tmp_path / "unused.json")
    assert calls == ["_stage_a_root"]
    assert result["downstream_status"] == "PROSPECTIVELY_NOT_REQUIRED"
    assert "stage_b" not in result
    assert result["accounting"] == {
        "episodes": SCRIPTED_EPISODES, "ticks": SCRIPTED_EPISODES * 56}
    assert result["conformance"]["all_pass"]
    assert result["technical_validity"] == "VALID"

    calls.clear()
    training = {
        root: {arm: {"updates": 256, "episodes": 8192}
               for arm in ("KEEP", "FLEX")} for root in ROOT_LABELS
    }
    def pass_map(function, arguments, workers, deadline):
        calls.append(function.__name__)
        if function is run_module._stage_a_root:
            return [(root, stage_a[root], 0) for root in ROOT_LABELS]
        assert function is run_module._stage_b_root
        return [(root, learned[root], training[root]) for root in ROOT_LABELS]

    monkeypatch.setattr(run_module, "_parallel_map", pass_map)
    result = run_module.execute(1, 30.0, tmp_path / "unused.json")
    assert calls == ["_stage_a_root", "_stage_b_root"]
    assert result["downstream_status"] == "COMPLETE"
    assert result["accounting"] == {"episodes": MAX_EPISODES,
                                     "ticks": MAX_TICKS}
    assert result["conformance"]["all_pass"]
    assert result["technical_validity"] == "VALID"
    assert "peak_process_group_working_set_bytes_observed" not in result["runtime"]
    assert "terminal_process_group_working_set_bytes_observed" in result["runtime"]

    bad_training = {
        root: {arm: dict(facts) for arm, facts in arms.items()}
        for root, arms in training.items()
    }
    bad_training[ROOT_LABELS[0]]["FLEX"]["episodes"] = 8191
    def bad_map(function, arguments, workers, deadline):
        if function is run_module._stage_a_root:
            return [(root, stage_a[root], 0) for root in ROOT_LABELS]
        return [(root, learned[root], bad_training[root]) for root in ROOT_LABELS]
    monkeypatch.setattr(run_module, "_parallel_map", bad_map)
    invalid = run_module.execute(1, 30.0, tmp_path / "unused.json")
    assert not invalid["conformance"]["all_pass"]
    assert invalid["technical_validity"] == "INVALID"
    assert invalid["branch"] == "INVALID_OR_INCOMPLETE"


def test_train_arm_balances_cells_and_steps_before_next_baseline_use():
    events = []
    losses = []
    step_count = [0]

    def fake_rollout(policy, arm, root, cell, scenario, phase, update=None):
        if update == 1:
            assert step_count[0] == 1
        events.append(("rollout", update, cell, scenario))
        return {"Y": 1.0}, torch.tensor(1.0, dtype=torch.float64)

    def fake_step(policy, loss):
        events.append(("step", step_count[0]))
        losses.append(float(loss))
        step_count[0] += 1
        return 0.0005

    def fake_baseline(old, mean):
        events.append(("baseline", step_count[0] - 1))
        return 0.95 * old + 0.05 * mean

    facts = train_arm(object(), "KEEP", 0, rollout_fn=fake_rollout,
                      step_fn=fake_step, baseline_update_fn=fake_baseline,
                      update_blocks=2)
    assert facts["updates"] == 2 and facts["episodes"] == 64
    for update in range(2):
        calls = [event for event in events
                 if event[0] == "rollout" and event[1] == update]
        assert len(calls) == 32
        for cell in ((6, 6), (9, 9), (6, 9), (9, 6)):
            assert sorted(event[3] for event in calls if event[2] == cell) == list(range(8))
    first_step = events.index(("step", 0))
    first_baseline = events.index(("baseline", 0))
    first_next_rollout = events.index(("rollout", 1, (6, 6), 0))
    assert first_step < first_baseline < first_next_rollout
    assert sum(event == ("baseline", 0) for event in events) == 4
    assert sum(event == ("baseline", 1) for event in events) == 4
    assert losses == pytest.approx([-1.0, -0.95])
