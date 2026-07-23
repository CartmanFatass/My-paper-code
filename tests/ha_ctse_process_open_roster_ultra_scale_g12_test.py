from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_direct import collect_direct_trajectory
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_high_churn_g9 import (
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from ha_ctse_process.open_roster_ultra_scale_g12 import (
    DOMAIN_PROFILES,
    EDGE_SCALE_PROFILE,
    FAR_SCALE_PROFILE,
    ULTRA_SCALE_PROFILE,
)
from scripts import run_open_roster_ultra_scale_g12 as runner


def test_profiles_cross_n40_and_are_constructively_solvable() -> None:
    expected = {
        "edge_ultra_scale": (64, 48),
        "far_ultra_scale": (80, 64),
        "mixed_churn": (96, 80),
    }
    for domain, profiles in DOMAIN_PROFILES.items():
        profile = profiles[0]
        capacity, maximum = expected[domain]
        profile.validate()
        assert profile.capacity == capacity
        assert max(expected_roster_schedule(profile)) == maximum
        ledger = runner.LEDGER_FACTORIES[domain](
            0, master_seed=runner.DOMAIN_LEDGER_SEEDS[domain]
        )
        environment = HighChurnEnv(ledger)
        while environment.time < HORIZON:
            view = environment.observe()
            environment.step(constructive_actions(environment, view))
        outcome = environment.outcome()
        assert outcome.utility == 1.0
        assert outcome.roster_sizes == expected_roster_schedule(profile)
        assert outcome.short_required_total == ledger.expected_short_requirement

    assert EDGE_SCALE_PROFILE.maximum_active_count == 48
    assert FAR_SCALE_PROFILE.maximum_active_count == 64
    assert ULTRA_SCALE_PROFILE.maximum_active_count == 80


def test_ultra_profile_preserves_lifecycle_state_contract() -> None:
    trajectory = collect_direct_trajectory(
        runner._model(),
        ledger_ids=(0,),
        ledger_seed=runner.DOMAIN_LEDGER_SEEDS["mixed_churn"],
        action_seed=runner.ACTION_SEED_BASE,
        device=torch.device("cpu"),
        ledger_factory=runner.LEDGER_FACTORIES["mixed_churn"],
        environment_factory=HighChurnEnv,
    )
    assert trajectory.observations.shape[:3] == (HORIZON, 1, 96)
    assert high_churn_lifecycle_contract_valid(
        trajectory,
        ledger_seed=runner.DOMAIN_LEDGER_SEEDS["mixed_churn"],
        ledger_factory=runner.LEDGER_FACTORIES["mixed_churn"],
    )


def test_g12_contract_keeps_g8_policy_and_uses_bounded_eval() -> None:
    assert runner.ALGORITHM_ID == "ULTRA_SCALE_OPEN_ROSTER_G12"
    assert runner.FORMAL_EVAL_EPISODES == 64
    assert runner.core.G8_EVAL_EPISODES == 128
    assert runner.core.FORMAL_EVAL_EPISODES == 64
    assert runner._model().roster_representation == {
        "autoregressive_prefix": "active_fraction"
    }


def test_nonformal_full_path_and_tamper_rejection(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root)
    assert result["operational_valid"] is True
    assert result["branch"] == "NONFORMAL_ULTRA_SCALE_G12_EXERCISE_COMPLETE"
    training = runner._read_json(run_root / "train_manifest.json")
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    assert training["optimizer_steps"] == 0
    assert all(
        row["optimizer_steps"] == 0
        and row["source_model_copy_maximum_difference"] == 0.0
        for row in training["replicate_results"]
    )
    assert len(evaluation["cells"]) == 6
    assert all(cell["model_state_unchanged_exact"] for cell in evaluation["cells"])

    nonformal_as_formal = deepcopy(training)
    nonformal_as_formal["formal"] = True
    runner._write_json(run_root / "train_manifest.json", nonformal_as_formal)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == runner.INVALID_BRANCH

    runner._write_json(run_root / "train_manifest.json", training)
    tampered = deepcopy(evaluation)
    tampered["source_controls"]["rows"][0]["roster_sizes"][44] -= 1
    runner._write_json(run_root / "evaluation_manifest.json", tampered)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == runner.INVALID_BRANCH
    assert "source-control row mismatch" in rejected["operational_errors"]


def test_formal_contract_and_first_match_boundaries(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authorization token"):
        runner.train(
            run_root=tmp_path / "wrong_token",
            source_commit="a" * 40,
            formal=True,
            authorization_token="WRONG",
            g8_run_root=runner.DEFAULT_G8_RUN_ROOT,
            replicates=runner.FORMAL_REPLICATES,
            eval_episodes=runner.FORMAL_EVAL_EPISODES,
        )

    passing = {
        "edge_ultra_scale_deterministic_utility_ci95": [0.90, 0.95, 1.0],
        "far_ultra_scale_deterministic_utility_ci95": [0.90, 0.95, 1.0],
        "mixed_churn_deterministic_utility_ci95": [0.90, 0.95, 1.0],
        "mixed_churn_min_replicate_mean": runner.MINIMUM_MIXED_REPLICATE_FLOOR,
        "mixed_churn_stochastic_mean": runner.MIXED_STOCHASTIC_MEAN_FLOOR,
    }
    assert (
        runner.select_result_branch(passing)
        == "ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12"
    )

    cases = (
        ("edge_ultra_scale_deterministic_utility_ci95", "NO_EDGE_SCALE_ACCESS_G12"),
        ("far_ultra_scale_deterministic_utility_ci95", "NO_FAR_SCALE_ACCESS_G12"),
        ("mixed_churn_deterministic_utility_ci95", "NO_ULTRA_SCALE_ACCESS_G12"),
    )
    for metric, expected in cases:
        values = deepcopy(passing)
        values[metric][0] = np.nextafter(0.90, 0.0)
        assert runner.select_result_branch(values) == expected
    values = deepcopy(passing)
    values["mixed_churn_min_replicate_mean"] = np.nextafter(
        runner.MINIMUM_MIXED_REPLICATE_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "UNSTABLE_ULTRA_SCALE_G12"
