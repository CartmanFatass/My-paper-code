from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_direct import (
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_direct_mvp import (
    OPEN_ROSTER_COUNT_LIMIT,
    OpenRosterDynamicEnv,
    make_open_roster_training_ledger,
)
from ha_ctse_process.open_roster_prefix_normalized_g8 import (
    DOMAIN_PROFILES,
    LEDGER_FACTORIES,
    BeyondCountEnv,
)
from scripts import run_open_roster_prefix_normalized_g8 as runner


def _run_constructive(environment: BeyondCountEnv) -> float:
    while environment.time < HORIZON:
        view = environment.observe()
        environment.step(constructive_actions(environment, view))
    return environment.outcome().utility


def test_prefix_mode_is_explicit_without_changing_parameter_shape() -> None:
    torch.manual_seed(17)
    raw = DirectPrimitiveARPolicy()
    torch.manual_seed(17)
    normalized = DirectPrimitiveARPolicy(
        autoregressive_prefix="active_fraction"
    )
    assert raw.roster_representation == {"autoregressive_prefix": "raw_count"}
    assert normalized.roster_representation == {
        "autoregressive_prefix": "active_fraction"
    }
    assert raw.parameter_count == normalized.parameter_count
    for left, right in zip(raw.parameters(), normalized.parameters()):
        assert torch.equal(left, right)
    with pytest.raises(ValueError):
        DirectPrimitiveARPolicy(autoregressive_prefix="bad")


def test_prefix_fraction_changes_only_autoregressive_inputs_and_replays() -> None:
    torch.manual_seed(29)
    raw = DirectPrimitiveARPolicy()
    torch.manual_seed(29)
    normalized = DirectPrimitiveARPolicy(
        autoregressive_prefix="active_fraction"
    )
    observations = torch.randn(1, 4, 15)
    active = torch.ones(1, 4, dtype=torch.bool)
    order = torch.tensor([[0, 1, 2, 3]])
    hidden = torch.zeros(1, 4, raw.hidden_dim)
    raw_output = raw.forward_step(
        observations=observations,
        active_mask=active,
        order=order,
        hidden=hidden,
        deterministic=True,
    )
    normalized_output = normalized.forward_step(
        observations=observations,
        active_mask=active,
        order=order,
        hidden=hidden,
        deterministic=True,
    )
    assert torch.equal(raw_output.next_hidden[:, 0], normalized_output.next_hidden[:, 0])
    assert not torch.equal(raw_output.next_hidden[:, 1:], normalized_output.next_hidden[:, 1:])
    replay = normalized.forward_step(
        observations=observations,
        active_mask=active,
        order=order,
        hidden=hidden,
        teacher_actions=normalized_output.actions,
    )
    assert torch.equal(normalized_output.prefix_counts, replay.prefix_counts)
    assert float(normalized_output.prefix_counts[:, -1].sum()) == 3.0


def test_selected_context_keeps_g5_sum_and_count_coordinate() -> None:
    model = runner._model()
    observations = torch.randn(1, 5, 15)
    active = torch.tensor([[True, True, True, False, False]])
    prepared = model.prepare_step(observations=observations, active_mask=active)
    padded = model.prepare_step(
        observations=torch.cat((observations, torch.randn(1, 4, 15)), dim=1),
        active_mask=torch.cat((active, torch.zeros(1, 4, dtype=torch.bool)), dim=1),
    )
    assert torch.equal(prepared.context_input, padded.context_input)
    assert prepared.context_input[0, -1].item() == pytest.approx(np.log1p(3))
    assert BeyondCountEnv._count_feature(40) == pytest.approx(
        np.log1p(40) / np.log1p(OPEN_ROSTER_COUNT_LIMIT)
    )
    assert BeyondCountEnv._count_feature(40) > 1.0


def test_stress_profiles_keep_original_task_and_constructive_controls() -> None:
    observed_profiles: set[str] = set()
    for domain, profiles in DOMAIN_PROFILES.items():
        factory = LEDGER_FACTORIES[domain]
        for episode_id, profile in enumerate(profiles):
            ledger = factory(
                episode_id, master_seed=runner.DOMAIN_LEDGER_SEEDS[domain]
            )
            environment = BeyondCountEnv(ledger)
            assert _run_constructive(environment) == 1.0
            outcome = environment.outcome()
            assert outcome.short_required_total == ledger.expected_short_requirement
            assert max(outcome.roster_sizes) <= 40
            observed_profiles.add(profile.name)
    assert len(observed_profiles) == 7


def test_prefix_normalized_training_preserves_lifecycle_contract() -> None:
    trajectory = collect_direct_trajectory(
        runner._model(),
        ledger_ids=(0, 1),
        ledger_seed=runner.TRAIN_LEDGER_SEED_BASE,
        action_seed=runner.ACTION_SEED_BASE,
        device=torch.device("cpu"),
        ledger_factory=make_open_roster_training_ledger,
        environment_factory=OpenRosterDynamicEnv,
    )
    assert trajectory.observations.shape[0] == HORIZON
    assert float(trajectory.prefix_counts.max()) <= 7.0


def test_nonformal_full_path_and_formal_rejection(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root)
    assert result["operational_valid"] is True
    assert result["branch"] == "NONFORMAL_PREFIX_NORMALIZED_G8_EXERCISE_COMPLETE"
    training = runner._read_json(run_root / "train_manifest.json")
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    assert training["representation"] == runner.SELECTED_REPRESENTATION
    assert all(cell["model_state_unchanged_exact"] for cell in evaluation["cells"])
    assert len(evaluation["cells"]) == 11

    tampered = deepcopy(training)
    tampered["formal"] = True
    runner._write_json(run_root / "train_manifest.json", tampered)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == "INVALID_PREFIX_NORMALIZED_OPEN_ROSTER_G8"


def test_formal_contract_and_first_match_boundaries(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        runner.train(
            run_root=tmp_path / "wrong_token",
            source_commit="a" * 40,
            formal=True,
            authorization_token="WRONG",
            replicates=runner.FORMAL_REPLICATES,
            updates=runner.FORMAL_UPDATES,
            num_envs=runner.FORMAL_NUM_ENVS,
            eval_episodes=runner.FORMAL_EVAL_EPISODES,
        )
    passing = {
        f"{domain}_deterministic_utility_ci95": [floor, floor, 1.0]
        for domain, floor in runner.DOMAIN_FLOORS.items()
    }
    passing.update(
        {
            "joint_final_minus_zero_ci95": [np.nextafter(0.0, 1.0), 0.5, 1.0],
            "joint_min_replicate_mean": runner.MINIMUM_JOINT_REPLICATE_FLOOR,
            "joint_stochastic_mean": runner.JOINT_STOCHASTIC_MEAN_FLOOR,
        }
    )
    assert runner.select_result_branch(passing) == "USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8"
    branches = {
        "iid": "NO_IID_ACCESS_PREFIX_NORMALIZED_G8",
        "heldout": "NO_HELDOUT_ACCESS_PREFIX_NORMALIZED_G8",
        "moderate_beyond": "NO_MODERATE_ACCESS_PREFIX_NORMALIZED_G8",
        "far_beyond": "NO_FAR_ACCESS_PREFIX_NORMALIZED_G8",
        "joint": "NO_JOINT_ACCESS_PREFIX_NORMALIZED_G8",
    }
    for domain, expected in branches.items():
        values = deepcopy(passing)
        values[f"{domain}_deterministic_utility_ci95"][0] = np.nextafter(
            runner.DOMAIN_FLOORS[domain], 0.0
        )
        assert runner.select_result_branch(values) == expected
    values = deepcopy(passing)
    values["joint_final_minus_zero_ci95"][0] = 0.0
    assert runner.select_result_branch(values) == "NO_LEARNING_GAIN_PREFIX_NORMALIZED_G8"
    values = deepcopy(passing)
    values["joint_min_replicate_mean"] = np.nextafter(
        runner.MINIMUM_JOINT_REPLICATE_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "UNSTABLE_PREFIX_NORMALIZED_G8"


def test_analyzer_rejects_representation_and_cell_tamper(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    runner.exercise(run_root=run_root)
    training = runner._read_json(run_root / "train_manifest.json")
    training["representation"]["autoregressive_prefix"] = "raw_count"
    runner._write_json(run_root / "train_manifest.json", training)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert "representation contract mismatch" in rejected["operational_errors"]

    training["representation"] = deepcopy(runner.SELECTED_REPRESENTATION)
    runner._write_json(run_root / "train_manifest.json", training)
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    evaluation["cells"][0]["model_state_unchanged_exact"] = False
    runner._write_json(run_root / "evaluation_manifest.json", evaluation)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert "evaluation changed model state" in rejected["operational_errors"]
