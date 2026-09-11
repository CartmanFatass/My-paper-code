from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import MIN_AVAILABLE_BYTES
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import experiment
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.semantics import (
    ROOT_HEX, SEED_LABEL,
    classify_r02, contact_integrity, cost_config,
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


def test_third_root_contact_rules_and_real_module_publisher(tmp_path, monkeypatch):
    assert inspect.signature(experiment.execute).parameters["seed"].default == 1
    assert inspect.signature(experiment.execute).parameters["role_column_cut"].default is False
    costs = cost_config(128, (0,32,64,128), 256)
    assert (costs["cells"], costs["invocation"], costs["evaluation_episodes_total"]) == (18, 1316864, 4608)
    assert classify_r02(_rule()) == "R02_SMALL_OR_ROSTER_MIXED"
    lr = {"PHY_TRUST_004": [0.003], "EDGE_FLEX_150": [0.003]}
    base = _rule(initial_optimizer_group_lr=lr, final_optimizer_group_lr=lr)
    assert classify_r02(base, branch_prefix="R06") == "R06_SMALL_OR_ROSTER_MIXED"
    for initial_indices, rows, first in (([2], [], 0), ([], [[], [3]], 2), ([], [[], []], None)):
        initial = {
            "tight_changed_coordinate_indices": initial_indices,
            "tight_changed_coordinates": len(initial_indices),
            "tight_projection_matches_direct_clip": True,
            "wide_initial_projection_identity": True,
            "first_tight_contact_update": 0 if initial_indices else None,
        }
        curves = {"PHY_TRUST": [
            {"update": u, "projection_changed_indices": indices, "box_contact": bool(indices)}
            for u, indices in enumerate(rows, 1)
        ], "EDGE_FLEX": []}
        contact = contact_integrity(initial, curves, first)
        assert all(contact.values())
        rule = {**base, **contact, "r09_binding": True, "first_tight_contact_update": first,
                "initial_tight_clip_changed_exactly_five": False}
        expected = "R09_NO_OBSERVED_CONTACT" if first is None else "R09_N15_WITHIN_MEI"
        assert classify_r02(rule, branch_prefix="R09") == expected
        assert not contact_integrity(initial, curves, 99)["contact_history_truthful"]
        assert not contact_integrity({**initial, "tight_changed_coordinates": 99}, curves, first)["initial_projection_conformant"]
        if curves["PHY_TRUST"]:
            curves["PHY_TRUST"][0]["box_contact"] = not curves["PHY_TRUST"][0]["box_contact"]
            assert not contact_integrity(initial, curves, first)["contact_history_truthful"]
    old = {**base, "r07_binding": True, "initial_projection_conformant": True,
           "contact_history_truthful": True, "first_tight_contact_update": None}
    assert classify_r02(old, branch_prefix="R07") == "R07_NO_OBSERVED_CONTACT"
    old.update(r08_binding=True, cut_panel_complete=True, first_tight_contact_update=0,
               cut_contrasts=[{"roster": n, "d_I": 0.006, "d_C": 0.006,
                               "a": 0.0, "e_I": 0.001, "e_C": 0.001} for n in (9,15)])
    assert classify_r02(old, branch_prefix="R08") == "R08_INTERACTION_WITHIN_MEI"
    rule = {**base, "r09_binding": True, "initial_projection_conformant": True,
            "contact_history_truthful": True, "first_tight_contact_update": 3}
    for d, e, branch in ((0.005, 0, "MATERIAL_TIGHT_FAVORED"), (-0.005, 0, "MATERIAL_TIGHT_ADVERSE"),
                         (0.006, -0.001, "EDGE_BELOW_UNIFORM"), (0.004, 0, "WITHIN_MEI")):
        descriptors = [{"roster": 9, "d_128": -0.01, "e_128": -0.01},
                       {"roster": 15, "d_128": d, "e_128": e}]
        assert classify_r02({**rule, "update_128_descriptors": descriptors}, branch_prefix="R09") == "R09_N15_" + branch
    for field in ("r09_binding", "initial_projection_conformant", "contact_history_truthful"):
        assert classify_r02({**rule, field: False}, branch_prefix="R09") == "R09_INVALID_INCOMPLETE"
    assert classify_r02({**rule, "final_optimizer_group_lr": {}}, branch_prefix="R09") == "R09_INVALID_INCOMPLETE"
    receipt = (tmp_path / "admission.json").resolve()
    _admission(receipt)
    # Stop at the first evaluation-tape call, before a native adapter/model/learner exists.
    class BindingObserved(Exception):
        pass
    def observe(root, *, seed_label, roster, episode):
        observed.append((root.hex(), seed_label))
        raise BindingObserved
    observed = []
    with monkeypatch.context() as changed:
        changed.setattr(experiment, "evaluation_tape", observe)
        for kwargs in ({}, {"seed": 3}):
            with pytest.raises(BindingObserved):
                experiment.execute(output_root=(tmp_path / "unused").resolve(), admission_receipt=receipt, **kwargs)
    assert observed == [(ROOT_HEX, SEED_LABEL), ("0000000000000000000000000000000000000000000000000000000000000003", "FRRIE-B09-CONTACT-BLOCK-003")]
    output = (tmp_path / "result").resolve()
    root = Path(experiment.__file__).resolve().parents[4]
    completed = subprocess.run([
        sys.executable, "-m", "scripts.run_frrie_b01_contact_r09",
        "--output-root", str(output), "--admission-receipt", str(receipt), "--test-only",
    ], cwd=root, capture_output=True, text=True, timeout=55)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((output / "summary.json").read_text())
    assert (summary["seed"], summary["seed_root_hex"], summary["seed_label"]) == (3, "0000000000000000000000000000000000000000000000000000000000000003", "FRRIE-B09-CONTACT-BLOCK-003")
    assert summary["object_id"] == "FRRIE-B01-CONTACT-R128-LR003-R09-THIRD-ROOT-20260905"
    assert summary["branch"] == "TEST_ONLY_NON_RESULT"
    inputs = summary["deterministic_rule_inputs"]
    assert all(inputs[name] for name in ("r09_binding", "initial_projection_conformant", "contact_history_truthful"))
    assert inputs["initial_optimizer_group_lr"] == inputs["final_optimizer_group_lr"] == lr
    assert summary["work"]["successful_paired_updates"] == 1
    assert len(summary["cells"]) == 10
    assert {row["roster"] for row in summary["cells"]} == {9, 15}
    assert inputs["adam_steps"] == 2
    assert summary["exposure"]["first_tight_contact_update"] == inputs["first_tight_contact_update"]
    assert summary["resources"]["wall_seconds"] > 0
    assert {row["intervention"] for row in summary["cells"]} == {"INTACT"}
    assert summary["cut_contrasts"] == []
    assert summary["evaluation_tape_reuse"]["expected_cell_uses_per_roster"] == 5
    assert len(summary["descriptive_estimands"]) == 4
    assert len(summary["projection_audit"]["checkpoint_state"]) == 4
    assert all(len(rows) == 1 for rows in summary["projection_audit"]["per_update"].values())
    for row in summary["cells"]:
        assert all(name in row for name in ("J", "D_W", "D_E", "min_D", "WASTE", "action_counts", "native_event_counts", "episodes", "transitions"))
    assert all(row["factual_learner_transitions"] == 768 for row in summary["work"]["per_arm"].values())
