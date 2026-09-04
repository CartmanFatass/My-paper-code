from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import batch_collector
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import B01ContractError
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    MIN_AVAILABLE_BYTES,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import (
    experiment,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.semantics import (
    PRODUCTION_CHECKPOINTS,
    ROOT_HEX,
    SEED_LABEL,
    TEST_ROOT_HEX,
    TEST_SEED_LABEL,
    classify_r02,
    cost_config,
    exposure_record,
    initialize_contact_pair,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.tapes import (
    production_training_inputs,
)

from ..b01.test_batch_collector import _FakeBatchEnvironment, _model


def test_factual_replay_relaxes_only_intermediate_bits(monkeypatch):
    import torch

    torch.set_num_threads(1)
    monkeypatch.setattr(batch_collector, "B01NativeBatchEnvironment", _FakeBatchEnvironment)
    tapes, origins = batch_collector.make_test_update_inputs(
        b"C" * 32, seed_label=batch_collector.TEST_SEED_LABELS[0], update=1,
    )
    positions = tuple(range(0, 64, 2))
    model = _model()

    def actor(observations, roles, incoming_hidden):
        # Exact test arithmetic isolates guard behavior from batch-width rounding.
        probabilities = torch.from_numpy(batch_collector._expected_masks(roles.numpy())).float()
        probabilities /= probabilities.sum(dim=2, keepdim=True)
        return SimpleNamespace(hidden=incoming_hidden + 0.125, probabilities=probabilities)

    monkeypatch.setattr(model, "actor_step_batch", actor)
    factual = batch_collector._collect_factual_roster(
        model=model, adapter=None, roster=9, positions=positions,
        tapes=tuple(tapes[i] for i in positions),
        origins=tuple(origins[i] for i in positions),
    )

    def audit(**kwargs):
        with torch.no_grad():
            return batch_collector._audit_factual_suffixes(
                model=model, adapter=None, factual=factual, **kwargs,
            )

    assert audit()[1] == 624
    for field, message in (
        ("incoming_hidden", "predecision trace differs"),
        ("postdecision_hidden", "actor trace differs"),
        ("probabilities", "actor trace differs"),
    ):
        with monkeypatch.context() as changed:
            for trace in factual.traces:
                for row in trace:
                    value = getattr(row, field)
                    changed.setattr(row, field, value + 1e-7)
            with pytest.raises(B01ContractError, match=message):
                audit()  # Legacy callers retain strict comparison by default.
            assert audit(require_intermediate_bit_equality=False)[1] == 624

    sample = model.actions_from_uniforms_batch

    def changed_action(probabilities, uniforms):
        actions = sample(probabilities, uniforms).clone()
        legal = batch_collector.LEGAL_ACTION_INDICES[0]
        actions[0, 0] = next(action for action in legal if action != actions[0, 0])
        return actions

    with monkeypatch.context() as changed:
        changed.setattr(model, "actions_from_uniforms_batch", changed_action)
        with pytest.raises(B01ContractError, match="actor trace differs"):
            audit(require_intermediate_bit_equality=False)

    class ChangedTrajectory(_FakeBatchEnvironment):
        def step(self, actions):
            result = super().step(actions)
            self.scores[0] += 1
            return result

    monkeypatch.setattr(batch_collector, "B01NativeBatchEnvironment", ChangedTrajectory)
    with pytest.raises(B01ContractError, match="origin transition differs"):
        audit(require_intermediate_bit_equality=False)


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


def test_frozen_projection_counts_branches_and_real_test_only_runner(tmp_path):
    assert exposure_record(128)["line"] == (
        "updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; "
        "init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; "
        "tight_box_half_width=0.04; initial_projection_changed_coordinates=5"
    )
    assert cost_config(128, PRODUCTION_CHECKPOINTS, 256) == {
        "updates": 128,
        "checkpoints": [0, 32, 64, 128],
        "evaluation_episodes_per_cell": 256,
        "learned_training_per_arm": 630_784,
        "learned_evaluation_per_arm": 24_576,
        "learned_total_per_arm": 655_360,
        "shared_uniform": 6_144,
        "invocation": 1_316_864,
        "optimizer_steps_per_arm": 128,
        "cells": 18,
        "evaluation_episodes_total": 4_608,
        "factual_learner_transitions_per_arm": 98_304,
        "factual_learner_transitions_total": 196_608,
    }
    assert classify_r02(_rule()) == "R02_SMALL_OR_ROSTER_MIXED"
    assert classify_r02(_rule(update_128_descriptors=[
        {"roster": 9, "d_128": 0.006, "e_128": 0.001},
        {"roster": 15, "d_128": 0.005, "e_128": 0.0},
    ])) == "R02_FAVORABLE_BOTH"
    assert classify_r02(_rule(update_128_descriptors=[
        {"roster": 9, "d_128": -0.006, "e_128": 0.001},
        {"roster": 15, "d_128": 0.008, "e_128": 0.001},
    ])) == "R02_ADVERSE_OR_MIXED"
    assert classify_r02(_rule(update_128_descriptors=[
        {"roster": 9, "d_128": 0.008, "e_128": -0.001},
        {"roster": 15, "d_128": 0.008, "e_128": 0.001},
    ])) == "R02_EDGE_BELOW_UNIFORM"
    assert classify_r02(_rule(adam_steps=0)) == "R02_INVALID_INCOMPLETE"

    models, optimizers, audit, _ = initialize_contact_pair()
    assert audit["raw_paired_arm_bytes_equal"] is True
    assert audit["raw_paired_model_bytes_equal"] is True
    assert audit["raw_beta_min"] == -0.038080986589193344
    assert audit["raw_beta_max"] == 0.048026394098997116
    assert audit["tight_changed_coordinates"] == 5
    assert audit["tight_projection_matches_direct_clip"] is True
    assert audit["wide_initial_projection_identity"] is True
    assert audit["optimizer_state_pair_equal_before_projection"] is True
    assert audit["optimizer_state_pair_equal_after_projection"] is True
    assert audit["optimizer_state_unchanged_by_initial_projection"] is True
    assert audit["first_tight_contact_update"] == 0
    checkpoint0 = [
        experiment._checkpoint_state(models[arm], optimizers[arm], checkpoint=0, arm=arm)
        for arm in ("PHY_TRUST", "EDGE_FLEX")
    ]
    assert {row["arm"] for row in checkpoint0} == {"PHY_TRUST_004", "EDGE_FLEX_150"}
    assert {row["optimizer_sha256"] for row in checkpoint0}.__len__() == 1
    assert all(row["adam_step"] == 0 and row["first_moment"]["nonzero"] == 0 for row in checkpoint0)

    training_tapes, _ = production_training_inputs(
        bytes.fromhex(TEST_ROOT_HEX), TEST_SEED_LABEL, 1,
    )
    assert [tape.roster for tape in training_tapes] == [9, 15] * 32
    assert {tape.seed_block for tape in training_tapes} == {TEST_SEED_LABEL}

    receipt = (tmp_path / "admission.json").resolve()
    _admission(receipt)
    output = (tmp_path / "result").resolve()
    repository_root = Path(experiment.__file__).resolve().parents[4]
    completed = subprocess.run([
        sys.executable,
        str(repository_root / "scripts" / "run_frrie_b01_contact_r02.py"),
        "--output-root", str(output),
        "--admission-receipt", str(receipt),
        "--seed", "1",
        "--test-only",
    ], cwd=repository_root, capture_output=True, text=True, timeout=55)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="ascii"))
    assert summary["branch"] == "TEST_ONLY_NON_RESULT"
    assert summary["seed"] == 1 and summary["seed_label"] == TEST_SEED_LABEL
    assert summary["seed_root_hex"] == TEST_ROOT_HEX
    assert summary["initialization_audit"]["tight_changed_coordinates"] == 1
    assert summary["initialization_audit"]["first_tight_contact_update"] == 0
    assert summary["runtime_configuration"]["training_roster_order"] == [9, 15] * 32
    assert summary["runtime_configuration"]["arm_ids"] == [
        "PHY_TRUST_004", "EDGE_FLEX_150", "UNIFORM_LEGAL",
    ]
    assert len(summary["cells"]) == 10
    assert {row["arm"] for row in summary["cells"]} == {
        "PHY_TRUST_004", "EDGE_FLEX_150", "UNIFORM_LEGAL",
    }
    assert summary["deterministic_rule_inputs"]["evaluation_episodes"] == 10
    assert summary["deterministic_rule_inputs"]["learner_transitions"] == 1_536
    assert summary["deterministic_rule_inputs"]["backward_calls"] == 2
    assert summary["deterministic_rule_inputs"]["adam_steps"] == 2
    assert summary["work"]["observed_training_slots"] == {
        "PHY_TRUST_004": 4_928, "EDGE_FLEX_150": 4_928,
    }
    assert summary["work"]["successful_paired_updates"] == 1
    assert all(
        len(summary["projection_audit"]["per_update"][arm]) == 1
        for arm in ("PHY_TRUST_004", "EDGE_FLEX_150")
    )
    assert len(summary["projection_audit"]["checkpoint_state"]) == 4
    assert {
        row["adam_step"] for row in summary["projection_audit"]["checkpoint_state"]
    } == {0, 1}
    assert summary["evaluation_tape_reuse"]["same_tape_objects_reused"] is True
