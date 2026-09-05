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
    classify_r02, contact_integrity,
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


def test_second_root_contact_rules_and_real_module_publisher(tmp_path, monkeypatch):
    assert inspect.signature(experiment.execute).parameters["seed"].default == 1
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
        rule = {**base, **contact, "r07_binding": True, "first_tight_contact_update": first,
                "initial_tight_clip_changed_exactly_five": False}
        expected = "R07_NO_OBSERVED_CONTACT" if first is None else "R07_N15_WITHIN_MEI"
        assert classify_r02(rule, branch_prefix="R07") == expected
        assert not contact_integrity(initial, curves, 99)["contact_history_truthful"]
        assert not contact_integrity({**initial, "tight_changed_coordinates": 99}, curves, first)["initial_projection_conformant"]
        if curves["PHY_TRUST"]:
            curves["PHY_TRUST"][0]["box_contact"] = not curves["PHY_TRUST"][0]["box_contact"]
            assert not contact_integrity(initial, curves, first)["contact_history_truthful"]
    rule = {**base, "r07_binding": True, "initial_projection_conformant": True,
            "contact_history_truthful": True, "first_tight_contact_update": 3}
    for d, e, branch in ((0.005, 0, "MATERIAL_TIGHT_FAVORED"), (-0.005, 0, "MATERIAL_TIGHT_ADVERSE"),
                         (0.006, -0.001, "EDGE_BELOW_UNIFORM"), (0.004, 0, "WITHIN_MEI")):
        descriptors = [{"roster": 9, "d_128": -0.01, "e_128": -0.01},
                       {"roster": 15, "d_128": d, "e_128": e}]
        assert classify_r02({**rule, "update_128_descriptors": descriptors}, branch_prefix="R07") == "R07_N15_" + branch
    for field in ("r07_binding", "initial_projection_conformant", "contact_history_truthful"):
        assert classify_r02({**rule, field: False}, branch_prefix="R07") == "R07_INVALID_INCOMPLETE"
    assert classify_r02({**rule, "final_optimizer_group_lr": {}}, branch_prefix="R07") == "R07_INVALID_INCOMPLETE"
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
        for kwargs in ({}, {"seed": 2}):
            with pytest.raises(BindingObserved):
                experiment.execute(output_root=(tmp_path / "unused").resolve(), admission_receipt=receipt, **kwargs)
    assert observed == [(ROOT_HEX, SEED_LABEL), ("0000000000000000000000000000000000000000000000000000000000000002", "FRRIE-B07-CONTACT-BLOCK-002")]
    output = (tmp_path / "result").resolve()
    root = Path(experiment.__file__).resolve().parents[4]
    completed = subprocess.run([
        sys.executable, "-m", "scripts.run_frrie_b01_contact_r07",
        "--output-root", str(output), "--admission-receipt", str(receipt), "--test-only",
    ], cwd=root, capture_output=True, text=True, timeout=55)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((output / "summary.json").read_text())
    assert (summary["seed"], summary["seed_root_hex"], summary["seed_label"]) == (2, "0000000000000000000000000000000000000000000000000000000000000002", "FRRIE-B07-CONTACT-BLOCK-002")
    assert summary["object_id"] == "FRRIE-B01-CONTACT-R128-LR003-R07-SECOND-ROOT-20260905"
    assert summary["branch"] == "TEST_ONLY_NON_RESULT"
    inputs = summary["deterministic_rule_inputs"]
    assert all(inputs[name] for name in ("r07_binding", "initial_projection_conformant", "contact_history_truthful"))
    assert inputs["initial_optimizer_group_lr"] == inputs["final_optimizer_group_lr"] == lr
    assert summary["work"]["successful_paired_updates"] == 1
    assert len(summary["cells"]) == 10
    assert {row["roster"] for row in summary["cells"]} == {9, 15}
    assert inputs["adam_steps"] == 2
    assert summary["exposure"]["first_tight_contact_update"] == inputs["first_tight_contact_update"]
    assert summary["resources"]["wall_seconds"] > 0
