from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_direct import collect_direct_trajectory
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_high_churn_g9 import (
    DOMAIN_PROFILES,
    LEDGER_FACTORIES,
    MAXIMUM_ACTIVE_COUNT,
    REPEATED_REJOIN_PROFILE,
    ChurnEvent,
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from scripts import run_open_roster_high_churn_g9 as runner


def test_profiles_have_exact_membership_and_constructive_access() -> None:
    for domain, profiles in DOMAIN_PROFILES.items():
        profile = profiles[0]
        ledger = LEDGER_FACTORIES[domain](
            0, master_seed=runner.DOMAIN_LEDGER_SEEDS[domain]
        )
        environment = HighChurnEnv(ledger)
        observed_events = {}
        while environment.time < HORIZON:
            view = environment.observe()
            change = view.membership_change
            if any(
                (
                    change.joined,
                    change.temporarily_left,
                    change.rejoined,
                    change.terminally_left,
                )
            ):
                observed_events[view.time] = change
            environment.step(constructive_actions(environment, view))
        outcome = environment.outcome()
        assert outcome.utility == 1.0
        assert outcome.roster_sizes == expected_roster_schedule(profile)
        assert max(outcome.roster_sizes) <= MAXIMUM_ACTIVE_COUNT
        assert outcome.short_required_total == ledger.expected_short_requirement
        assert len(observed_events) == len(profile.events) + 1
        assert observed_events[0].joined == profile.initial_join
        for event in profile.events:
            change = observed_events[event.time]
            assert change.temporarily_left == event.temporarily_left
            assert change.rejoined == event.rejoined
            assert change.joined == event.joined
            assert change.terminally_left == event.terminally_left


def test_profile_validation_rejects_collision_and_terminal_reuse() -> None:
    first = REPEATED_REJOIN_PROFILE.events[0]
    collision = replace(
        REPEATED_REJOIN_PROFILE,
        events=(replace(first, joined=(6,)),)
        + REPEATED_REJOIN_PROFILE.events[1:],
    )
    with pytest.raises(ValueError, match="collide"):
        collision.validate()

    terminal_reuse = replace(
        REPEATED_REJOIN_PROFILE,
        events=REPEATED_REJOIN_PROFILE.events[:-1]
        + (ChurnEvent(68, joined=(0,)),),
    )
    with pytest.raises(ValueError, match="reuse"):
        terminal_reuse.validate()


def test_repeated_absence_freezes_hidden_and_new_join_starts_zero() -> None:
    torch.manual_seed(19)
    mixed_trajectory = None
    for domain, factory in LEDGER_FACTORIES.items():
        trajectory = collect_direct_trajectory(
            runner._model(),
            ledger_ids=(0,),
            ledger_seed=runner.DOMAIN_LEDGER_SEEDS[domain],
            action_seed=runner.ACTION_SEED_BASE,
            device=torch.device("cpu"),
            ledger_factory=factory,
            environment_factory=HighChurnEnv,
        )
        assert trajectory.observations.shape[:3] == (HORIZON, 1, 20)
        assert high_churn_lifecycle_contract_valid(
            trajectory,
            ledger_seed=runner.DOMAIN_LEDGER_SEEDS[domain],
            ledger_factory=factory,
        )
        if domain == "mixed_churn":
            mixed_trajectory = trajectory

    assert mixed_trajectory is not None
    corrupted = replace(
        mixed_trajectory,
        hidden_after=mixed_trajectory.hidden_after.clone(),
    )
    corrupted.hidden_after[41, 0, 6, 0] += 1.0
    assert not high_churn_lifecycle_contract_valid(
        corrupted,
        ledger_seed=runner.DOMAIN_LEDGER_SEEDS["mixed_churn"],
        ledger_factory=LEDGER_FACTORIES["mixed_churn"],
    )


def test_g9_keeps_the_selected_prefix_normalized_policy() -> None:
    model = runner._model()
    assert model.roster_representation == {
        "autoregressive_prefix": "active_fraction"
    }
    assert runner.G8_REPRESENTATION == {
        "active_aggregation": "sum",
        "count_coordinate": "log1p",
        "autoregressive_prefix": "active_fraction",
    }


def test_nonformal_full_path_and_fail_closed_tamper(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root)
    assert result["operational_valid"] is True
    assert result["branch"] == "NONFORMAL_HIGH_FREQUENCY_CHURN_G9_EXERCISE_COMPLETE"
    training = runner._read_json(run_root / "train_manifest.json")
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    assert training["training_operation"] == "none_frozen_g8_checkpoint_import"
    assert training["optimizer_steps"] == 0
    assert all(
        row["source_model_copy_maximum_difference"] == 0.0
        for row in training["replicate_results"]
    )
    assert len(evaluation["cells"]) == 6
    assert all(cell["model_state_unchanged_exact"] for cell in evaluation["cells"])

    nonformal_as_formal = deepcopy(training)
    nonformal_as_formal["formal"] = True
    runner._write_json(run_root / "train_manifest.json", nonformal_as_formal)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == "INVALID_HIGH_FREQUENCY_CHURN_G9"

    provenance_tamper = deepcopy(training)
    provenance_tamper["g8_provenance"]["counts"]["updates"] -= 1
    runner._write_json(run_root / "train_manifest.json", provenance_tamper)
    rejected = runner.analyze(run_root=run_root)
    assert "G8 provenance mismatch" in rejected["operational_errors"]

    runner._write_json(run_root / "train_manifest.json", training)
    profile_tamper = deepcopy(evaluation)
    profile_tamper["cells"][0]["profile_names"][0] = "tampered"
    runner._write_json(run_root / "evaluation_manifest.json", profile_tamper)
    rejected = runner.analyze(run_root=run_root)
    assert "evaluation profile inventory mismatch" in rejected["operational_errors"]

    source_tamper = deepcopy(evaluation)
    source_tamper["source_controls"]["rows"][0]["roster_sizes"][0] += 1
    runner._write_json(run_root / "evaluation_manifest.json", source_tamper)
    rejected = runner.analyze(run_root=run_root)
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
        f"{domain}_deterministic_utility_ci95": [floor, floor, 1.0]
        for domain, floor in runner.DOMAIN_FLOORS.items()
    }
    passing.update(
        {
            "mixed_churn_min_replicate_mean": runner.MINIMUM_MIXED_REPLICATE_FLOOR,
            "mixed_churn_stochastic_mean": runner.MIXED_STOCHASTIC_MEAN_FLOOR,
        }
    )
    assert runner.select_result_branch(passing) == "ROBUST_HIGH_FREQUENCY_CHURN_G9"

    failures = (
        ("repeated_rejoin", "NO_REPEATED_REJOIN_ACCESS_G9"),
        ("load_proximal", "NO_LOAD_PROXIMAL_CHURN_ACCESS_G9"),
        ("mixed_churn", "NO_MIXED_CHURN_ACCESS_G9"),
    )
    for domain, expected in failures:
        values = deepcopy(passing)
        values[f"{domain}_deterministic_utility_ci95"][0] = np.nextafter(
            runner.DOMAIN_FLOORS[domain], 0.0
        )
        assert runner.select_result_branch(values) == expected

    values = deepcopy(passing)
    values["mixed_churn_min_replicate_mean"] = np.nextafter(
        runner.MINIMUM_MIXED_REPLICATE_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "UNSTABLE_HIGH_FREQUENCY_CHURN_G9"
    values = deepcopy(passing)
    values["mixed_churn_stochastic_mean"] = np.nextafter(
        runner.MIXED_STOCHASTIC_MEAN_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "UNSTABLE_HIGH_FREQUENCY_CHURN_G9"
