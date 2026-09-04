from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import three_seed
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    MIN_AVAILABLE_BYTES, TEST_SEED_LABEL,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import (
    NativePrimitives,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import (
    create_test_seed_packet,
)


def _rules(**overrides):
    value = {
        "complete": True, "admission_valid": True, "exposure_present": True,
        "paired_information_work_equal": True, "precontact_full_state_equal": True,
        "precontact_evaluation_equal": True, "evaluation_preserved_state": True,
        "same_evaluation_tapes": True, "learner_transitions": 1,
        "training_episodes": 1, "backward_calls": 1, "adam_steps": 1,
        "evaluation_episodes": 1, "evaluation_transitions": 1,
    }
    value.update(overrides)
    return value


def test_production_counts_exposure_and_single_seed_rule_are_literal():
    assert three_seed.exposure_record(512)["line"] == (
        "updates=512; adam_lr=0.0003; nominal_lr_exposure=0.1536; "
        "init_half_range=0.05; nominal_exposure_over_init_half_range=3.072"
    )
    assert three_seed.cost_config(512, (0, 32, 64, 128, 256, 512), (6, 9, 15, 21), 256) == {
        "updates": 512, "checkpoints": [0, 32, 64, 128, 256, 512],
        "rosters": [6, 9, 15, 21],
        "interventions": ["INTACT", "SEMANTIC_COLUMN_ROTATE"],
        "evaluation_episodes_per_cell": 256,
        "learned_training_per_arm": 2_523_136,
        "learned_evaluation_per_arm": 147_456,
        "learned_total_per_arm": 2_670_592,
        "shared_uniform": 6_144,
        "factual_native_slots_per_arm": 393_216,
        "factual_suffix_audit_slots_per_arm": 638_976,
        "nonfactual_suffix_slots_per_arm": 1_490_944,
        "counterfactual_audit_slots_per_arm": 2_129_920,
        "invocation": 5_347_328,
        "optimizer_steps_per_arm": 512, "learned_cells": 96,
        "uniform_cells": 2, "cells": 98,
        "evaluation_episodes_total": 25_088,
        "evaluation_transitions_total": 301_056,
        "factual_learner_transitions_per_arm": 393_216,
        "factual_learner_transitions_total": 786_432,
    }
    assert three_seed.classify_seed(_rules()) == "B01_SEED_VALID_DIRECT"
    assert three_seed.classify_seed(_rules(adam_steps=0)) == "B01_INVALID"
    assert three_seed.classify_seed(_rules(), test_only=True) == "TEST_ONLY_NON_RESULT"


class _FakeNativeEnvironment:
    tape_ids: dict[int, tuple[int, ...]] = {}

    def __init__(self, adapter, *, roster, lanes):
        assert adapter == "TEST_ONLY_FAKE_ADAPTER"
        self.roster, self.lanes, self.slot = roster, lanes, 0

    def reset(self, tapes):
        direct = tuple(id(tape) for tape in tapes)
        if self.roster in self.tape_ids:
            assert self.tape_ids[self.roster] == direct
        else:
            self.tape_ids[self.roster] = direct
        self.slot = 0

    def observe(self):
        roles = np.broadcast_to(
            np.repeat(np.arange(3, dtype=np.int64), self.roster // 3),
            (self.lanes, self.roster),
        ).copy()
        masks = np.zeros((self.lanes, self.roster, 6), dtype=np.bool_)
        supports = ((0, 3, 5), (1, 3, 5), (2, 4, 5))
        for entity, role in enumerate(roles[0]):
            masks[:, entity, list(supports[int(role)])] = True
        return SimpleNamespace(
            observations=np.zeros((self.lanes, self.roster, 22), dtype=np.float32),
            roles=roles, legal_masks=masks, slots=(self.slot,) * self.lanes,
            terminals=(False,) * self.lanes,
        )

    def step(self, actions):
        assert np.asarray(actions).shape == (self.lanes, self.roster)
        self.slot += 1
        primitive = NativePrimitives(
            dw=1, de=1, waste=0.25, duplicate=1, expired=2, collision=3,
            empty_radio=4, radio_actions=8, waste_actions=2, successful_deliveries=2,
        )
        return SimpleNamespace(
            terminals=(self.slot == 12,) * self.lanes,
            returns=(0.45,) * self.lanes, primitives=(primitive,) * self.lanes,
        )


class _FakeActor:
    calls: list[tuple[str, bool, int]] = []

    def __init__(self, arm):
        self.arm_id, self.training, self.state = arm, True, 0

    def parameter_bytes(self):
        return bytes([self.state]) * 8

    def update(self):
        self.state += 1

    def eval(self):
        self.training = False

    def train(self, mode):
        self.training = mode

    def actor_step_batch(self, observations, roles, hidden, *, rotate_columns=False):
        import torch
        self.calls.append((self.arm_id, rotate_columns, id(hidden)))
        lanes, roster = roles.shape
        probabilities = torch.zeros((lanes, roster, 6), dtype=torch.float32)
        supports = ((0, 3, 5), (1, 3, 5), (2, 4, 5))
        for role, support in enumerate(supports):
            rows = roles == role
            weights = ((0.2, 0.3, 0.5) if not rotate_columns else (0.3, 0.2, 0.5))
            for action, weight in zip(support, weights):
                probabilities[:, :, action][rows] = weight
        return SimpleNamespace(probabilities=probabilities, hidden=hidden + 1.0)

    def actions_from_uniforms_batch(self, probabilities, uniforms):
        return (uniforms[:, :, None] >= probabilities.cumsum(dim=2)).sum(dim=2).clamp(max=5)


def test_test_only_runner_covers_rotated_publication_path(monkeypatch, tmp_path):
    packet = (tmp_path / "test-seeds.json").resolve()
    create_test_seed_packet(packet)
    receipt = (tmp_path / "admission.json").resolve()
    receipt.write_text(json.dumps({
        "schema_version": 1, "captured_at": "2026-09-04T00:00:00Z",
        "assessed_at": "2026-09-04T00:00:00Z",
        "measurement_source": "TEST_ONLY_DIRECT_FIXTURE",
        "minimum_available_bytes": MIN_AVAILABLE_BYTES,
        "available_physical_bytes": MIN_AVAILABLE_BYTES,
        "cgroup_memory_max_bytes": None, "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None, "effective_available_bytes": MIN_AVAILABLE_BYTES,
        "physical_floor_pass": True, "effective_floor_pass": True, "passed": True,
        "failure_reasons": [],
    }), encoding="utf-8")
    builds = []
    _FakeNativeEnvironment.tape_ids = {}
    _FakeActor.calls = []
    monkeypatch.setattr(
        three_seed, "_build_adapter",
        lambda: builds.append("once") or "TEST_ONLY_FAKE_ADAPTER",
    )
    monkeypatch.setattr(three_seed, "NativeEnvironment", _FakeNativeEnvironment)
    monkeypatch.setattr(three_seed, "_ToyPolicy", _FakeActor)
    monkeypatch.setattr(
        three_seed, "make_actor_critic",
        lambda *_: (_ for _ in ()).throw(AssertionError("production model constructed")),
    )
    output = (tmp_path / "result").resolve()

    assert three_seed.main([
        "--output-root", str(output), "--seed-packet", str(packet),
        "--admission-receipt", str(receipt), "--seed-label", TEST_SEED_LABEL,
        "--test-only",
    ]) == 0

    summary = json.loads((output / "summary.json").read_text(encoding="ascii"))
    assert builds == ["once"]
    assert summary["seed_validity"] == "TEST_ONLY_NON_RESULT"
    assert summary["aggregate_rule_status"] == "NOT_APPLIED_SINGLE_SEED_INVOCATION"
    assert summary["seed_label"] == TEST_SEED_LABEL
    assert summary["admission"]["validated"] is True
    assert summary["work"]["expected_cost_law"] == {
        "updates": 1, "checkpoints": [0, 1], "rosters": [6, 9],
        "interventions": ["INTACT", "SEMANTIC_COLUMN_ROTATE"],
        "evaluation_episodes_per_cell": 1, "learned_training_per_arm": 4_928,
        "learned_evaluation_per_arm": 96, "learned_total_per_arm": 5_024,
        "shared_uniform": 12, "factual_native_slots_per_arm": 768,
        "factual_suffix_audit_slots_per_arm": 1_248,
        "nonfactual_suffix_slots_per_arm": 2_912,
        "counterfactual_audit_slots_per_arm": 4_160, "invocation": 10_060,
        "optimizer_steps_per_arm": 1, "learned_cells": 16,
        "uniform_cells": 1, "cells": 17, "evaluation_episodes_total": 17,
        "evaluation_transitions_total": 204,
        "factual_learner_transitions_per_arm": 768,
        "factual_learner_transitions_total": 1_536,
    }
    assert len(summary["cells"]) == 17
    assert len(summary["descriptive_estimands"]) == 4
    assert {cell["intervention"] for cell in summary["cells"]} == {
        "INTACT", "SEMANTIC_COLUMN_ROTATE",
    }
    assert all(cell["model_bytes_preserved"] for cell in summary["cells"])
    assert all(
        sum(cell["action_counts"]) == cell["transitions"] * cell["roster"]
        for cell in summary["cells"]
    )
    assert summary["evaluation_tape_reuse"]["same_tape_objects_reused"] is True
    for arm in ("PHY_TRUST", "EDGE_FLEX"):
        direct = summary["work"]["per_arm"][arm]
        assert direct["factual_native_slots"] == 768
        assert direct["factual_suffix_audit_native_slots"] == 1_248
        assert direct["nonfactual_suffix_native_slots"] == 2_912
        assert direct["counterfactual_audit_native_slots"] == 4_160
        assert direct["total_training_environment_slots"] == 4_928
    assert summary["evaluation_tape_reuse"]["completed_cell_uses_per_roster"] == {
        "6": 8, "9": 9,
    }
    heldout = [row for row in summary["descriptive_estimands"] if row["roster"] == 6]
    assert all(row["I_u"] == 0.0 and row["V_u"] > 0.0 for row in heldout)
    assert any(
        left[0] == right[0] == "PHY_TRUST" and left[1] is False and right[1] is True
        and left[2] == right[2]
        for left, right in zip(_FakeActor.calls, _FakeActor.calls[1:])
    )
    assert "between-arm action-probability TV/raw traces" in summary["optional_measurement_gaps"]
