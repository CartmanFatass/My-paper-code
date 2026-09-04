from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import numpy as np

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import r128_smoke
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    MIN_AVAILABLE_BYTES, TEST_SEED_LABEL,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import (
    NativePrimitives,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import (
    create_test_seed_packet,
)


def _rule_inputs(**overrides):
    value = {
        "complete": True,
        "admission_valid": True,
        "exposure_present": True,
        "paired_information_work_equal": True,
        "precontact_full_state_equal": True,
        "precontact_evaluation_equal": True,
        "evaluation_preserved_model_bytes": True,
        "required_measurements_present": True,
        "learner_transitions": 1,
        "training_episodes": 1,
        "backward_calls": 1,
        "adam_steps": 1,
        "evaluation_episodes": 1,
        "first_tight_contact_update": None,
    }
    value.update(overrides)
    return value


def test_exposure_and_branch_rules_are_literal():
    exposure = r128_smoke.exposure_record(128)
    assert exposure == {
        "updates": 128,
        "adam_lr": 0.0003,
        "nominal_lr_exposure": 0.0384,
        "init_half_range": 0.05,
        "nominal_exposure_over_init_half_range": 0.768,
        "line": (
            "updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; "
            "init_half_range=0.05; nominal_exposure_over_init_half_range=0.768"
        ),
    }
    assert r128_smoke.classify_r128(_rule_inputs()) == "R128_VALID_NO_CONTACT"
    assert r128_smoke.classify_r128(
        _rule_inputs(first_tight_contact_update=71)
    ) == "R128_VALID_CONTACT"
    assert r128_smoke.classify_r128(
        _rule_inputs(adam_steps=0)
    ) == "R128_INVALID_INCOMPLETE"
    assert r128_smoke.classify_r128(_rule_inputs(), test_only=True) == "TEST_ONLY_NON_RESULT"
    assert r128_smoke.cost_config(128, (0, 32, 64, 128), 256) == {
        "updates": 128, "checkpoints": [0, 32, 64, 128],
        "evaluation_episodes_per_cell": 256,
        "learned_training_per_arm": 630_784,
        "learned_evaluation_per_arm": 24_576,
        "learned_total_per_arm": 655_360,
        "shared_uniform": 6_144, "invocation": 1_316_864,
        "optimizer_steps_per_arm": 128, "cells": 18,
        "evaluation_episodes_total": 4_608,
        "factual_learner_transitions_per_arm": 98_304,
        "factual_learner_transitions_total": 196_608,
    }


def test_launch_sha_is_repository_bound(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    expected = subprocess.run(
        ["git", "-C", str(r128_smoke.REPOSITORY_ROOT), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert r128_smoke._launch_sha() == expected


class _FakeNativeEnvironment:
    tape_ids = {}

    def __init__(self, adapter, *, roster, lanes):
        assert adapter == "TEST_ONLY_FAKE_ADAPTER"
        self.roster = roster
        self.lanes = lanes
        self.slot = 0

    def reset(self, tapes):
        assert len(tapes) == self.lanes
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
            roles=roles,
            legal_masks=masks,
            slots=(self.slot,) * self.lanes,
            terminals=(False,) * self.lanes,
        )

    def step(self, actions):
        actions = np.asarray(actions)
        assert actions.shape == (self.lanes, self.roster)
        self.slot += 1
        primitive = NativePrimitives(
            dw=1, de=1, waste=0.25,
            duplicate=1, expired=2, collision=3, empty_radio=4,
            radio_actions=8, waste_actions=2, successful_deliveries=2,
        )
        return SimpleNamespace(
            terminals=(self.slot == 12,) * self.lanes,
            returns=(0.45,) * self.lanes,
            primitives=(primitive,) * self.lanes,
        )


def test_test_only_runner_emits_non_result_summary(monkeypatch, tmp_path):
    packet = (tmp_path / "test-seeds.json").resolve()
    create_test_seed_packet(packet)
    receipt = (tmp_path / "admission.json").resolve()
    receipt.write_text(json.dumps({
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
    builds = []
    _FakeNativeEnvironment.tape_ids = {}
    monkeypatch.setattr(
        r128_smoke, "_build_adapter",
        lambda: builds.append("once") or "TEST_ONLY_FAKE_ADAPTER",
    )
    monkeypatch.setattr(r128_smoke, "NativeEnvironment", _FakeNativeEnvironment)
    monkeypatch.setattr(
        r128_smoke, "make_actor_critic",
        lambda *_: (_ for _ in ()).throw(AssertionError("production model constructed")),
    )
    output = (tmp_path / "result").resolve()

    assert r128_smoke.main([
        "--output-root", str(output),
        "--seed-packet", str(packet),
        "--admission-receipt", str(receipt),
        "--seed-label", TEST_SEED_LABEL,
        "--test-only",
    ]) == 0

    summary = json.loads((output / "summary.json").read_text(encoding="ascii"))
    assert builds == ["once"]
    assert summary["branch"] == "TEST_ONLY_NON_RESULT"
    assert summary["test_only"] is True
    assert summary["seed_label"] == TEST_SEED_LABEL
    assert summary["admission"]["validated"] is True
    assert summary["work"]["expected_cost_law"] == {
        "learned_training_per_arm": 4_928,
        "learned_evaluation_per_arm": 48,
        "learned_total_per_arm": 4_976,
        "shared_uniform": 24,
        "invocation": 9_976,
        "optimizer_steps_per_arm": 1,
        "updates": 1, "checkpoints": [0, 1],
        "evaluation_episodes_per_cell": 1, "cells": 10,
        "evaluation_episodes_total": 10,
        "factual_learner_transitions_per_arm": 768,
        "factual_learner_transitions_total": 1_536,
    }
    assert summary["work"]["observed_training_slots"] == {
        "EDGE_FLEX": 4_928, "PHY_TRUST": 4_928,
    }
    assert summary["deterministic_rule_inputs"]["evaluation_episodes"] == 10
    assert summary["deterministic_rule_inputs"]["backward_calls"] == 2
    assert summary["deterministic_rule_inputs"]["adam_steps"] == 2
    assert len(summary["cells"]) == 10
    assert all(cell["model_bytes_preserved"] for cell in summary["cells"])
    assert all(
        sum(cell["action_counts"]) == cell["transitions"] * cell["roster"]
        for cell in summary["cells"]
    )
    assert len(summary["descriptive_estimands"]) == 4
    assert summary["projection_audit"]["changed_coordinate_inventory"] == []
    assert summary["evaluation_tape_reuse"] == {
        "rosters": [9, 15], "episodes_per_roster": 1,
        "expected_cell_uses_per_roster": 5,
        "completed_cell_uses_per_roster": {"9": 5, "15": 5},
        "same_tape_objects_reused": True,
    }
