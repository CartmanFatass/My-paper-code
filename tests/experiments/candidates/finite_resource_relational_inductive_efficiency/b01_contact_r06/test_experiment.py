from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import experiment
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.semantics import (
    OBJECT_ID, TEST_ROOT_HEX, classify_r02, exposure_record, initialize_contact_pair,
    initialize_test_contact_pair,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import MIN_AVAILABLE_BYTES


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


def test_selected_lr_defaults_branches_and_real_publisher(tmp_path):
    for function in (initialize_contact_pair, initialize_test_contact_pair, experiment.execute, experiment.main):
        assert inspect.signature(function).parameters["adam_lr"].default == 0.0003
    for function in (experiment.execute, experiment.main):
        assert inspect.signature(function).parameters["object_id"].default == OBJECT_ID
        assert inspect.signature(function).parameters["branch_prefix"].default == "R02"
    for kwargs, expected_lr in (({}, 0.0003), ({"adam_lr": 0.003}, 0.003)):
        _, optimizers, audit, _ = initialize_test_contact_pair(**kwargs)
        assert all(group["lr"] == expected_lr for opt in optimizers.values() for group in opt.param_groups)
        assert audit["initial_optimizer_group_lr"] == {
            "PHY_TRUST_004": [expected_lr], "EDGE_FLEX_150": [expected_lr],
        }
        assert audit["optimizer_state_unchanged_by_initial_projection"]
    assert exposure_record(128)["adam_lr"] == 0.0003
    assert exposure_record(128, adam_lr=0.003)["line"] == (
        "updates=128; adam_lr=0.003; nominal_lr_exposure=0.384; "
        "init_half_range=0.05; nominal_exposure_over_init_half_range=7.68; "
        "tight_box_half_width=0.04; initial_projection_changed_coordinates=5"
    )
    assert classify_r02(_rule()) == "R02_SMALL_OR_ROSTER_MIXED"
    lr = {"PHY_TRUST_004": [0.003], "EDGE_FLEX_150": [0.003]}
    rule = _rule(initial_optimizer_group_lr=lr, final_optimizer_group_lr=lr)
    assert classify_r02(rule, branch_prefix="R06") == "R06_SMALL_OR_ROSTER_MIXED"
    for field in ("initial_optimizer_group_lr", "final_optimizer_group_lr"):
        for wrong in (None, {**lr, "EDGE_FLEX_150": [0.0003]}):
            assert classify_r02({**rule, field: wrong}, branch_prefix="R06") == "R06_INVALID_INCOMPLETE"
    for d, e, branch in ((0.005, 0.0, "FAVORABLE_BOTH"), (-0.005, 0.0, "ADVERSE_OR_MIXED"), (0.005, -0.001, "EDGE_BELOW_UNIFORM")):
        rows = [{"roster": n, "d_128": d, "e_128": e} for n in (9, 15)]
        assert classify_r02({**rule, "update_128_descriptors": rows}, branch_prefix="R06") == "R06_" + branch
    receipt = (tmp_path / "admission.json").resolve()
    _admission(receipt)
    output = (tmp_path / "result").resolve()
    root = Path(experiment.__file__).resolve().parents[4]
    completed = subprocess.run([
        sys.executable, str(root / "scripts/run_frrie_b01_contact_r06.py"),
        "--output-root", str(output), "--admission-receipt", str(receipt),
        "--seed", "1", "--test-only",
    ], cwd=root, capture_output=True, text=True, timeout=55)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((output / "summary.json").read_text())
    assert summary["object_id"] == "FRRIE-B01-CONTACT-ACTIVE-R128-LR003-R06-20260904"
    assert summary["branch"] == "TEST_ONLY_NON_RESULT"
    assert summary["seed_root_hex"] == TEST_ROOT_HEX
    assert summary["exposure"]["adam_lr"] == 0.003
    for field in ("initial_optimizer_group_lr", "final_optimizer_group_lr"):
        assert summary["deterministic_rule_inputs"][field] == lr
    assert summary["initialization_audit"]["initial_optimizer_group_lr"] == lr
    assert summary["work"]["successful_paired_updates"] == 1
    assert len(summary["cells"]) == 10
    assert len(summary["projection_audit"]["checkpoint_state"]) == 4
    assert summary["deterministic_rule_inputs"]["adam_steps"] == 2
    assert summary["resources"]["wall_seconds"] > 0
    assert all(value > 0 for value in summary["resources"]["per_arm_wall_seconds_per_update"].values())
