from __future__ import annotations

import json

import torch

from experiments.candidates.ebcr_variable_k.config import PRODUCTION_CONFIG, RunConfig
from experiments.candidates.ebcr_variable_k.models import PPOHazardLearner
from experiments.candidates.ebcr_variable_k.run import _collect_safety_failures, exercise


def test_local_and_coord_start_from_paired_but_disjoint_parameters_and_optimizers():
    local = PPOHazardLearner(17)
    coord = PPOHazardLearner(17)
    for left, right in zip(local.actor.parameters(), coord.actor.parameters()):
        assert torch.equal(left, right)
        assert left.data_ptr() != right.data_ptr()
    assert local.actor_optimizer is not coord.actor_optimizer
    assert local.actor_parameter_count == coord.actor_parameter_count == 1441
    assert local.critic_parameter_count == coord.critic_parameter_count == 5249


def test_safety_validation_fails_closed_on_missing_arm_cell_coverage():
    bounded = RunConfig(
        base_seeds=(17,), training_episodes=1,
        primary_episodes_per_cell=1, safety_episodes_per_cell=1,
        selection_episodes_per_cell=1, ppo_epochs=1, minibatch_ticks=32,
    )
    failures = _collect_safety_failures({"17": {}}, bounded)
    assert failures
    assert all(row["reason"] == "incomplete_safety_panel_coverage" for row in failures)


def test_bounded_internal_complete_flow_reaches_activity_without_changing_defaults(tmp_path):
    bounded = RunConfig(
        base_seeds=(17,), training_episodes=2,
        primary_episodes_per_cell=2, safety_episodes_per_cell=2,
        selection_episodes_per_cell=1, ppo_epochs=1, minibatch_ticks=64,
        wall_seconds=120,
    )
    output_root = tmp_path / "flow"
    result_path = tmp_path / "result.json"
    result = exercise(output_root=output_root, result_path=result_path, config=bounded)
    assert result["production_defaults"] is False
    assert result["scientific_activity"]["reached"] is True
    assert set(result["scientific_activity"]["arms"]) == {"LOCAL", "COORD"}
    assert result["actual_budgets"]["training_team_ticks"] == 512
    assert result["selected_fixed_arm"] in {"FIXED-4", "FIXED-8", "FIXED-16", "FIXED-32"}
    assert (output_root / "checkpoints" / "seed_17" / "LOCAL.pt").is_file()
    assert (output_root / "checkpoints" / "seed_17" / "COORD.pt").is_file()
    assert json.loads(result_path.read_text(encoding="utf-8"))["scientific_activity"]["reached"]
    assert PRODUCTION_CONFIG.training_episodes == 512
    assert PRODUCTION_CONFIG.ppo_epochs == 4
