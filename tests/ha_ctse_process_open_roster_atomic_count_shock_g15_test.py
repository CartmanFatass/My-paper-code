from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_direct import collect_direct_trajectory
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_atomic_count_shock_g15 import (
    MODERATE_SPEC,
    ULTRA_SPEC,
    WIDE_SPEC,
    make_atomic_count_shock_profile,
)
from ha_ctse_process.open_roster_high_churn_g9 import (
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from scripts import run_open_roster_atomic_count_shock_g15 as runner


def test_atomic_shock_profiles_are_unique_unequal_transactions() -> None:
    specs = (
        ("shock_moderate", MODERATE_SPEC),
        ("shock_wide", WIDE_SPEC),
        ("mixed_churn", ULTRA_SPEC),
    )
    signatures: set[tuple[tuple[int, ...], ...]] = set()
    for domain, spec in specs:
        for episode_id in range(12):
            profile = make_atomic_count_shock_profile(
                episode_id,
                master_seed=runner.DOMAIN_LEDGER_SEEDS[domain],
                spec=spec,
            )
            assert profile == make_atomic_count_shock_profile(
                episode_id,
                master_seed=runner.DOMAIN_LEDGER_SEEDS[domain],
                spec=spec,
            )
            profile.validate()
            counts = expected_roster_schedule(profile)
            event_counts = [counts[event.time] for event in profile.events]
            assert spec.low_count_low <= counts[0] <= spec.low_count_high
            assert all(
                spec.high_count_low <= event_counts[index] <= spec.high_count_high
                if index % 2 == 0
                else spec.low_count_low <= event_counts[index] <= spec.low_count_high
                for index in range(len(event_counts))
            )
            assert all(
                event.joined
                and event.terminally_left
                and len(event.joined) != len(event.terminally_left)
                and not event.temporarily_left
                and not event.rejoined
                for event in profile.events
            )
            signatures.add(
                tuple(
                    event.joined + event.terminally_left for event in profile.events
                )
            )
    assert len(signatures) > 30


def test_atomic_shock_profiles_are_constructively_solvable() -> None:
    for domain, factory in runner.LEDGER_FACTORIES.items():
        for episode_id in range(3):
            ledger = factory(
                episode_id, master_seed=runner.DOMAIN_LEDGER_SEEDS[domain]
            )
            environment = HighChurnEnv(ledger)
            while environment.time < HORIZON:
                view = environment.observe()
                environment.step(constructive_actions(environment, view))
            outcome = environment.outcome()
            assert outcome.utility == 1.0
            assert outcome.roster_sizes == expected_roster_schedule(ledger.profile)
            assert outcome.short_required_total == ledger.expected_short_requirement


def test_atomic_shock_ultra_preserves_cold_start_and_terminal_lifecycle() -> None:
    trajectory = collect_direct_trajectory(
        runner._model(),
        ledger_ids=(1,),
        ledger_seed=runner.DOMAIN_LEDGER_SEEDS["mixed_churn"],
        action_seed=runner.ACTION_SEED_BASE,
        device=torch.device("cpu"),
        ledger_factory=runner.LEDGER_FACTORIES["mixed_churn"],
        environment_factory=HighChurnEnv,
    )
    assert trajectory.observations.shape[:3] == (HORIZON, 1, 224)
    assert high_churn_lifecycle_contract_valid(
        trajectory,
        ledger_seed=runner.DOMAIN_LEDGER_SEEDS["mixed_churn"],
        ledger_factory=runner.LEDGER_FACTORIES["mixed_churn"],
    )


def test_g15_contract_keeps_g8_policy_and_bounded_budget() -> None:
    assert runner.ALGORITHM_ID == "ATOMIC_COUNT_SHOCK_G15"
    assert runner.FORMAL_EVAL_EPISODES == 24
    assert runner.core.G8_EVAL_EPISODES == 128
    assert runner.core.EXPECTED_EVENT_COUNT == 6
    assert runner.core.REQUIRED_EVENT_OPERATIONS == ("joined", "terminally_left")
    assert runner._model().roster_representation == {
        "autoregressive_prefix": "active_fraction"
    }


def test_nonformal_full_path_and_atomic_shock_tamper_rejection(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root)
    assert result["operational_valid"] is True
    assert result["branch"] == runner.NONFORMAL_BRANCH
    training = runner._read_json(run_root / "train_manifest.json")
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    controls = evaluation["source_controls"]
    assert training["optimizer_steps"] == 0
    assert len(evaluation["cells"]) == 6
    assert len(controls["rows"]) == 12
    assert controls["all_profile_names_unique"] is True
    assert controls["all_event_operation_types_present"] is True
    assert all(cell["model_state_unchanged_exact"] for cell in evaluation["cells"])

    nonformal_as_formal = deepcopy(training)
    nonformal_as_formal["formal"] = True
    runner._write_json(run_root / "train_manifest.json", nonformal_as_formal)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == runner.INVALID_BRANCH

    runner._write_json(run_root / "train_manifest.json", training)
    tampered = deepcopy(evaluation)
    tampered["source_controls"]["rows"][0]["roster_sizes"][9] += 1
    runner._write_json(run_root / "evaluation_manifest.json", tampered)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
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
        "shock_moderate_deterministic_utility_ci95": [0.90, 0.95, 1.0],
        "shock_wide_deterministic_utility_ci95": [0.90, 0.95, 1.0],
        "mixed_churn_deterministic_utility_ci95": [0.90, 0.95, 1.0],
        "mixed_churn_min_replicate_mean": runner.MINIMUM_MIXED_REPLICATE_FLOOR,
        "mixed_churn_stochastic_mean": runner.MIXED_STOCHASTIC_MEAN_FLOOR,
    }
    assert runner.select_result_branch(passing) == "ROBUST_ATOMIC_COUNT_SHOCK_G15"
    cases = (
        (
            "shock_moderate_deterministic_utility_ci95",
            "NO_ATOMIC_SHOCK_MODERATE_ACCESS_G15",
        ),
        (
            "shock_wide_deterministic_utility_ci95",
            "NO_ATOMIC_SHOCK_WIDE_ACCESS_G15",
        ),
        (
            "mixed_churn_deterministic_utility_ci95",
            "NO_ATOMIC_SHOCK_ULTRA_ACCESS_G15",
        ),
    )
    for metric, expected in cases:
        values = deepcopy(passing)
        values[metric][0] = np.nextafter(0.90, 0.0)
        assert runner.select_result_branch(values) == expected
    values = deepcopy(passing)
    values["mixed_churn_stochastic_mean"] = np.nextafter(
        runner.MIXED_STOCHASTIC_MEAN_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "UNSTABLE_ATOMIC_COUNT_SHOCK_G15"
