"""Synthetic contract tests for the Stage C checkpoint-local audit."""

from __future__ import annotations

import copy
import importlib.util
import random
import sys
from pathlib import Path

import numpy as np
import pytest
import torch


_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


_SPEC = importlib.util.spec_from_file_location(
    "analyze_stage_c_skill_semantics",
    _ROOT / "scripts" / "analyze_stage_c_skill_semantics.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_AUDIT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_AUDIT)
cluster_bootstrap_ci = _AUDIT.cluster_bootstrap_ci
decide_outcome = _AUDIT.decide_outcome
natural_segments = _AUDIT.natural_segments
reconstruct_context_rows = _AUDIT.reconstruct_context_rows
load_audit_inputs = _AUDIT.load_audit_inputs


DELTA = 1.0 / 12.0
DELTA_STRATUM = 1.0 / 24.0


def _metrics(**overrides):
    values = {
        "all_pairs_exact_upper_below_delta": False,
        "all_pairs_forced_upper_below_delta": False,
        "frozen_pair_exact_lower": DELTA,
        "frozen_pair_forced_lower": DELTA,
        "stability_pooled_lower": DELTA,
        "stability_stratum_lowers": [DELTA_STRATUM] * 12,
        "stability_has_reversal": False,
        "natural_raw_pass": True,
        "natural_nuisance_lower": 0.01,
        "natural_matched_margin": 0.01,
        "policy_lineage_ok": True,
        "support_ok": True,
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        (_metrics(all_pairs_exact_upper_below_delta=True, all_pairs_forced_upper_below_delta=True), "A_NO_MATERIAL_Z_DEPENDENCE"),
        (_metrics(frozen_pair_exact_lower=0.0), "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"),
        (_metrics(stability_stratum_lowers=[0.0] + [DELTA_STRATUM] * 11), "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"),
        (_metrics(stability_has_reversal=True), "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"),
        (_metrics(natural_raw_pass=False), "C_STABLE_FORCED_NO_NATURAL_OVERLAP"),
        (_metrics(natural_nuisance_lower=0.0), "E_NUISANCE_SHORTCUT"),
        (_metrics(natural_matched_margin=0.0), "E_NUISANCE_SHORTCUT"),
        (_metrics(policy_lineage_ok=False), "F_UNDERPOWERED_OR_UNIDENTIFIABLE"),
        (_metrics(support_ok=False), "F_UNDERPOWERED_OR_UNIDENTIFIABLE"),
        (_metrics(), "D_STABLE_LOCAL_NATURAL_OVERLAP"),
    ],
)
def test_decide_outcome_follows_frozen_a_to_f_order(metrics, expected):
    assert decide_outcome(metrics) == expected


def test_reconstruct_context_rows_reads_only_lifecycle_fields_and_preserves_rejoin_age():
    rows = [
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 0, "physical_time": 0, "skill": 1, "active_n": 2, "reward": 99},
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 0, "physical_time": 1, "skill": 1, "active_n": 2, "owner": 12},
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 1, "physical_time": 3, "skill": 1, "active_n": 2, "progress": 3},
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 1, "physical_time": 4, "skill": 2, "active_n": 2, "success": True},
    ]

    contexts = reconstruct_context_rows(rows)

    assert [row["active_age"] for row in contexts] == [0, 1, 2, 0]
    assert [row["entry"] for row in contexts] == [True, True, True, True]
    assert all("reward" not in row and "owner" not in row and "progress" not in row for row in contexts)


def test_natural_segments_caps_windows_and_weights_each_eligible_segment_once():
    rows = []
    for step in range(15):
        rows.append({"episode": 0, "lifecycle_key": "long", "membership_epoch": 0, "physical_time": step, "skill": 0, "active_n": 2, "observation": [step]})
    for step in range(12):
        rows.append({"episode": 1, "lifecycle_key": "exact", "membership_epoch": 0, "physical_time": step, "skill": 1, "active_n": 2, "observation": [100 + step]})
    rows.extend({"episode": 2, "lifecycle_key": "short", "membership_epoch": 0, "physical_time": step, "skill": 2, "active_n": 2, "observation": [200 + step]} for step in range(11))

    segments = natural_segments(rows)

    assert [(segment["episode"], len(segment["rows"])) for segment in segments] == [(0, 12), (1, 12)]
    assert all(segment["weight"] == 1.0 for segment in segments)


def test_cluster_bootstrap_uses_local_rng_without_mutating_global_rng_or_inputs():
    values = [
        {"episode": 0, "value": 0.1},
        {"episode": 0, "value": 0.3},
        {"episode": 1, "value": 0.8},
    ]
    original = copy.deepcopy(values)
    random.seed(91)
    np.random.seed(92)
    torch.manual_seed(93)
    python_before = random.getstate()
    numpy_before = copy.deepcopy(np.random.get_state())
    torch_before = torch.get_rng_state().clone()

    ci = cluster_bootstrap_ci(values, value_key="value", repetitions=100, seed=307057)

    assert len(ci) == 3
    assert values == original
    assert random.getstate() == python_before
    assert np.array_equal(np.random.get_state()[1], numpy_before[1])
    assert torch.equal(torch.get_rng_state(), torch_before)


def test_load_audit_inputs_reconstructs_final_actor_strictly_without_rng_mutation(tmp_path):
    from ha_ctse_process.variable_roster_event import EventLowActor

    actor = EventLowActor(obs_dim=3, n_skills=3, action_dim=3, hidden_dim=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "event_architecture": {
                "architecture_state": {"obs_dim": 3, "n_skills": 3, "action_dim": 3, "low_hidden_dim": 4, "action_space_type": "discrete"},
                "low_actor_state": actor.state_dict(),
            }
        },
        checkpoint_path,
    )
    result_path = tmp_path / "result.json"
    result_path.write_text("{\"synthetic\": true}", encoding="utf-8")
    torch.manual_seed(94)
    before = torch.get_rng_state().clone()

    loaded = load_audit_inputs(result_path, checkpoint_path)

    assert isinstance(loaded["actor"], EventLowActor)
    assert all(torch.equal(loaded["actor"].state_dict()[key], value) for key, value in actor.state_dict().items())
    assert torch.equal(torch.get_rng_state(), before)
