from __future__ import annotations

import inspect
import json
import runpy
import sys

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import MIN_AVAILABLE_BYTES
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import experiment
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.semantics import (
    ROOT_HEX, SEED_LABEL, classify_r02, cost_config, cut_contrasts,
)


def _rule(**overrides):
    value = {
        "complete": True,
        "admission_valid": True,
        "exposure_present": True,
        "raw_paired_initialization_equal": True,
        "initial_tight_clip_changed_exactly_five": True,
        "optimizer_moments_unchanged_by_projection": True,
        "paired_information_work_equal": True,
        "evaluation_preserved_model_bytes": True,
        "same_evaluation_tapes": True,
        "required_curves_and_counts_present": True,
        "learner_transitions": 196_608,
        "training_episodes": 16_384,
        "backward_calls": 256,
        "adam_steps": 256,
        "evaluation_episodes": 4_608,
        "first_tight_contact_update": 0,
        "update_128_descriptors": [
            {"roster": 9, "d_128": 0.001, "e_128": 0.001},
            {"roster": 15, "d_128": -0.001, "e_128": 0.001},
        ],
    }
    value.update(overrides)
    return value

def _admission(path):
    path.write_text(json.dumps({
        "schema_version": 1,
        "captured_at": "2026-09-04T00:00:00Z",
        "assessed_at": "2026-09-04T00:00:00Z",
        "measurement_source": "TEST_ONLY_DIRECT_FIXTURE",
        "minimum_available_bytes": MIN_AVAILABLE_BYTES,
        "available_physical_bytes": MIN_AVAILABLE_BYTES,
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None,
        "effective_available_bytes": MIN_AVAILABLE_BYTES,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }), encoding="utf-8")


def test_cut_rules_and_one_real_module_publisher(tmp_path, monkeypatch):
    assert inspect.signature(experiment.execute).parameters["role_column_cut"].default is False
    assert classify_r02(_rule()) == "R02_SMALL_OR_ROSTER_MIXED"
    lr = {"PHY_TRUST_004": [0.003], "EDGE_FLEX_150": [0.003]}
    rule = _rule(initial_optimizer_group_lr=lr, final_optimizer_group_lr=lr)
    assert classify_r02(rule, branch_prefix="R06") == "R06_SMALL_OR_ROSTER_MIXED"
    rule.update(r08_binding=True, initial_projection_conformant=True, cut_panel_complete=True)
    for e_i, d_i, e_c, a, branch in (
        (-0.001, 0.0, -0.001, 0.01, "INTACT_EDGE_BELOW_UNIFORM"),
        (0.0, 0.004, -0.001, 0.01, "NO_MATERIAL_POSITIVE_ANCHOR"),
        (0.0, 0.005, -0.001, 0.01, "ROTATED_EDGE_BELOW_UNIFORM"),
        (0.0, 0.005, 0.0, 0.005, "MATERIAL_ATTENUATION"),
        (0.0, 0.005, 0.0, -0.005, "MATERIAL_AMPLIFICATION"),
        (0.0, 0.005, 0.0, 0.004, "INTERACTION_WITHIN_MEI"),
    ):
        rows = [{"roster": n, "d_I": d_i, "d_C": d_i-a, "a": a, "e_I": e_i, "e_C": e_c} for n in (9,15)]
        rule["cut_contrasts"] = rows
        assert classify_r02(rule, branch_prefix="R08") == "R08_" + branch
    for name in ("r08_binding", "initial_projection_conformant", "cut_panel_complete", "same_evaluation_tapes", "evaluation_preserved_model_bytes"):
        assert classify_r02({**rule, name: False}, branch_prefix="R08") == "R08_INVALID_INCOMPLETE"
    assert classify_r02({**rule, "cut_contrasts": []}, branch_prefix="R08") == "R08_INVALID_INCOMPLETE"
    assert classify_r02({**rule, "final_optimizer_group_lr": {}}, branch_prefix="R08") == "R08_INVALID_INCOMPLETE"
    original = cost_config(128, (0,32,64,128), 256)
    assert original["cells"] == 18 and original["invocation"] == 1_316_864
    cut = cost_config(128, (0,32,64,128), 256, role_column_cut=True)
    assert (cut["cells"], cut["evaluation_episodes_total"], cut["learned_total_per_arm"], cut["invocation"]) == (22, 5632, 661504, 1329152)
    calls, cut_walls = [], []
    intact_evaluate, rotated_evaluate = experiment._evaluate_cell, experiment._evaluate_intervention_cell
    enforce = experiment._enforce_time_cap
    def intact(adapter, model, *, tapes):
        calls.append(("INTACT", tapes))
        return intact_evaluate(adapter, model, tapes=tapes)
    def rotated(adapter, model, *, tapes, intervention):
        calls.append((intervention, tapes))
        return rotated_evaluate(adapter, model, tapes=tapes, intervention=intervention)
    def cap(started, walls):
        if calls and calls[-1][0] == "SEMANTIC_COLUMN_ROTATE":
            cut_walls.append(dict(walls))
        return enforce(started, walls)
    receipt = (tmp_path / "admission.json").resolve()
    _admission(receipt)
    output = (tmp_path / "result").resolve()
    with monkeypatch.context() as changed:
        changed.setattr(experiment, "_evaluate_cell", intact)
        changed.setattr(experiment, "_evaluate_intervention_cell", rotated)
        changed.setattr(experiment, "_enforce_time_cap", cap)
        changed.setattr(sys, "argv", ["run_frrie_b01_contact_r08", "--output-root", str(output),
                                     "--admission-receipt", str(receipt), "--test-only"])
        with pytest.raises(SystemExit) as exited:
            runpy.run_module("scripts.run_frrie_b01_contact_r08", run_name="__main__")
        assert exited.value.code == 0
    summary = json.loads((output / "summary.json").read_text())
    assert (summary["seed"], summary["seed_root_hex"], summary["seed_label"]) == (1, ROOT_HEX, SEED_LABEL)
    assert summary["object_id"] == "FRRIE-B01-R128-LR003-R08-ROLE-COLUMN-CUT-20260905"
    assert summary["branch"] == "TEST_ONLY_NON_RESULT"
    inputs = summary["deterministic_rule_inputs"]
    assert inputs["initial_optimizer_group_lr"] == inputs["final_optimizer_group_lr"] == lr
    assert inputs["cut_panel_complete"] and inputs["r08_binding"]
    assert summary["initialization_audit"]["tight_changed_coordinate_indices"] == [2,4,11,12,16]
    assert len(calls) == len(summary["cells"]) == 14
    assert [kind for kind, _ in calls] == ["INTACT"] * 10 + ["SEMANTIC_COLUMN_ROTATE"] * 4
    for n in (9,15):
        tapes = [tape for _, tape in calls if tape[0].roster == n]
        assert len(tapes) == 7 and all(tape is tapes[0] for tape in tapes)
    assert len(cut_walls) == 4
    assert cut_walls[1]["PHY_TRUST"] > cut_walls[0]["PHY_TRUST"]
    assert cut_walls[3]["EDGE_FLEX"] > cut_walls[2]["EDGE_FLEX"]
    assert summary["work"]["successful_paired_updates"] == 1 and inputs["adam_steps"] == 2
    assert inputs["evaluation_episodes"] == 14
    assert all(row["learned_evaluation_episodes"] == 6 for row in summary["work"]["per_arm"].values())
    cells = summary["cells"]
    for row in summary["descriptive_estimands"]:
        selected = {cell["arm"]: cell["J"] for cell in cells if cell["intervention"] == "INTACT"
                    and cell["checkpoint"] == row["checkpoint"] and cell["roster"] == row["roster"]}
        assert row["d_u"] == selected["PHY_TRUST_004"] - selected["EDGE_FLEX_150"]
    contrasts, complete = cut_contrasts(cells, (0,1), 1)
    assert complete and contrasts == summary["cut_contrasts"]
    for row in contrasts:
        assert row["a"] == row["d_I"] - row["d_C"]
        assert row["a"] == pytest.approx(row["PHY_INTACT_minus_ROTATE"] - row["EDGE_INTACT_minus_ROTATE"])
    for field, bad in (("intervention", "INTACT"), ("episodes", 2), ("model_bytes_preserved", False)):
        altered = [*cells[:-1], {**cells[-1], field: bad}]
        assert cut_contrasts(altered, (0,1), 1) == ([], False)
    assert cut_contrasts(cells[:-1], (0,1), 1) == ([], False)
