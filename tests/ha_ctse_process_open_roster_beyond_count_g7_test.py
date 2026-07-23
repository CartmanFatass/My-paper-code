from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import shutil

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_direct import (
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
)
from ha_ctse_process.dynamic_roster_testbed import (
    HORIZON,
    OBSERVATION_DIM,
    TERMINAL,
    constructive_actions,
)
from ha_ctse_process.open_roster_beyond_count_g7 import (
    DOMAIN_PROFILES,
    OPEN_ROSTER_COUNT_LIMIT,
    BeyondCountEnv,
    make_far_beyond_ledger,
    make_joint_ledger,
    make_moderate_beyond_ledger,
    beyond_count_lifecycle_contract_valid,
)
from scripts import run_open_roster_beyond_count_g7 as runner


PROJECT_ROOT = Path(__file__).resolve().parents[1]
G5_RUN_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1"
)


def _complete_constructively(ledger):
    environment = BeyondCountEnv(ledger)
    changes = {}
    while environment.time < HORIZON:
        view = environment.observe()
        if any(
            (
                view.membership_change.joined,
                view.membership_change.temporarily_left,
                view.membership_change.rejoined,
                view.membership_change.terminally_left,
            )
        ):
            changes[view.time] = view.membership_change
        environment.step(constructive_actions(environment, view))
    return environment, environment.outcome(), changes


def test_profiles_constructive_controls_and_actual_wave_requirement() -> None:
    factories = {
        "moderate_beyond": make_moderate_beyond_ledger,
        "far_beyond": make_far_beyond_ledger,
        "joint": make_joint_ledger,
    }
    assert max(
        max(profile.phase_counts)
        for profiles in DOMAIN_PROFILES.values()
        for profile in profiles
    ) == 40
    for domain, profiles in DOMAIN_PROFILES.items():
        for episode_id, profile in enumerate(profiles):
            ledger = factories[domain](episode_id)
            for count in profile.phase_counts:
                feature = BeyondCountEnv._count_feature(count)
                assert np.isfinite(feature)
                if count > OPEN_ROSTER_COUNT_LIMIT:
                    assert feature > 1.0
            environment, outcome, changes = _complete_constructively(ledger)
            first, second, third = profile.membership_event_times
            expected_schedule = tuple(
                profile.active_count_at(time) for time in range(HORIZON)
            )
            expected_requirement = sum(
                profile.active_count_at(arrival) - 1
                for arrival in ledger.wave_arrivals
            )
            assert outcome.utility == 1.0
            assert outcome.roster_sizes == expected_schedule
            assert outcome.short_required_total == expected_requirement
            assert changes[first].temporarily_left == ledger.temporary_leave
            assert changes[second].rejoined == ledger.temporary_leave
            assert changes[second].joined == ledger.genuine_join
            assert changes[third].terminally_left == ledger.terminal_leave
            assert all(
                environment.lifecycles[key].status == TERMINAL
                for key in ledger.terminal_leave
            )


def test_configured_events_preserve_hidden_lifecycle_ownership() -> None:
    torch.manual_seed(610)
    trajectory = collect_direct_trajectory(
        DirectPrimitiveARPolicy(),
        ledger_ids=(0, 1),
        ledger_seed=runner.FAR_BEYOND_LEDGER_SEED,
        action_seed=runner.ACTION_SEED_BASE,
        device=torch.device("cpu"),
        ledger_factory=make_far_beyond_ledger,
        environment_factory=BeyondCountEnv,
    )
    assert beyond_count_lifecycle_contract_valid(
        trajectory,
        ledger_seed=runner.FAR_BEYOND_LEDGER_SEED,
        ledger_factory=make_far_beyond_ledger,
    )


def test_count_feature_and_padding_are_invariant_to_extra_inactive_rows() -> None:
    assert BeyondCountEnv._count_feature(16) == 1.0
    assert BeyondCountEnv._count_feature(8) == float(
        np.log1p(8) / np.log1p(OPEN_ROSTER_COUNT_LIMIT)
    )
    for active_count in (20, 24, 28, 40):
        feature = BeyondCountEnv._count_feature(active_count)
        assert np.isfinite(feature)
        assert feature > 1.0
    torch.manual_seed(611)
    model = DirectPrimitiveARPolicy()
    active_keys = tuple(range(40))
    base_observations = torch.randn(1, 48, OBSERVATION_DIM)
    wide_observations = torch.randn(1, 56, OBSERVATION_DIM)
    wide_observations[:, :48] = base_observations
    base_mask = torch.zeros(1, 48, dtype=torch.bool)
    wide_mask = torch.zeros(1, 56, dtype=torch.bool)
    base_mask[:, active_keys] = True
    wide_mask[:, active_keys] = True
    base_order = torch.full((1, 48), -1, dtype=torch.long)
    wide_order = torch.full((1, 56), -1, dtype=torch.long)
    base_order[0, :40] = torch.tensor(active_keys)
    wide_order[0, :40] = torch.tensor(active_keys)
    base_hidden = torch.randn(1, 48, model.hidden_dim)
    wide_hidden = torch.randn(1, 56, model.hidden_dim)
    wide_hidden[:, :48] = base_hidden
    base = model.forward_step(
        observations=base_observations,
        active_mask=base_mask,
        order=base_order,
        hidden=base_hidden,
        deterministic=True,
    )
    wide = model.forward_step(
        observations=wide_observations,
        active_mask=wide_mask,
        order=wide_order,
        hidden=wide_hidden,
        deterministic=True,
    )
    assert torch.equal(base.actions[:, active_keys], wide.actions[:, active_keys])
    assert torch.equal(base.next_hidden[:, active_keys], wide.next_hidden[:, active_keys])
    assert torch.equal(base.value, wide.value)


def test_strict_g5_provenance_and_tamper_rejection(tmp_path: Path) -> None:
    manifest = runner.train(
        run_root=tmp_path / "imported",
        source_commit="7" * 40,
        formal=False,
        authorization_token=None,
        g5_run_root=G5_RUN_ROOT,
        eval_episodes=3,
    )
    assert manifest["training_operation"] == "none_frozen_g5_checkpoint_import"
    assert manifest["optimizer_steps"] == 0
    assert manifest["replicate_results"][0]["completed_updates"] == 250
    assert manifest["replicate_results"][0]["g5_manifest_seeds"]["model"] == 551000
    assert manifest["replicate_results"][0]["checkpoint_embedded_rng_constants"]["model_initialization_seed"] == 57056

    for mutation in ("source", "checkpoint"):
        bad_g5 = tmp_path / f"bad_g5_{mutation}"
        shutil.copytree(G5_RUN_ROOT, bad_g5)
        if mutation == "source":
            training = runner._read_json(bad_g5 / "train_manifest.json")
            training["source_commit"] = "0" * 40
            runner._write_json(bad_g5 / "train_manifest.json", training)
        else:
            checkpoint = bad_g5 / "checkpoints" / "replicate_0_final.pt"
            bundle = torch.load(checkpoint, map_location="cpu", weights_only=False)
            first_key = next(iter(bundle["model_state"]))
            bundle["model_state"][first_key] = bundle["model_state"][first_key].clone()
            bundle["model_state"][first_key].view(-1)[0] += 1.0
            torch.save(bundle, checkpoint)
        with pytest.raises(ValueError, match="G5 provenance"):
            runner.train(
                run_root=tmp_path / f"rejected_{mutation}",
                source_commit="7" * 40,
                formal=False,
                authorization_token=None,
                g5_run_root=bad_g5,
                eval_episodes=3,
            )


def test_g5_authorization_token_missing_or_wrong_is_rejected(tmp_path: Path) -> None:
    for mutation in ("missing", "wrong"):
        bad_g5 = tmp_path / f"bad_g5_token_{mutation}"
        shutil.copytree(G5_RUN_ROOT, bad_g5)
        training = runner._read_json(bad_g5 / "train_manifest.json")
        if mutation == "missing":
            training.pop("authorization_token")
        else:
            training["authorization_token"] = "wrong"
        runner._write_json(bad_g5 / "train_manifest.json", training)
        with pytest.raises(ValueError, match="G5 provenance"):
            runner.train(
                run_root=tmp_path / f"rejected_token_{mutation}",
                source_commit="7" * 40,
                formal=False,
                authorization_token=None,
                g5_run_root=bad_g5,
                eval_episodes=3,
            )


def test_zero_training_full_nonformal_path_and_model_immutability(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root, g5_run_root=G5_RUN_ROOT)
    assert result["formal"] is False
    assert result["operational_valid"] is True
    assert result["branch"] == "NONFORMAL_BEYOND_DECLARED_COUNT_G7_EXERCISE_COMPLETE"
    training = runner._read_json(run_root / "train_manifest.json")
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    assert training["optimizer_steps"] == 0
    assert len(training["replicate_results"]) == 1
    assert len(evaluation["cells"]) == 6
    assert all(cell["model_state_unchanged_exact"] for cell in evaluation["cells"])
    assert all(len(cell["utility"]) == runner.EXERCISE_EVAL_EPISODES for cell in evaluation["cells"])

    training["replicate_results"][0]["completed_updates"] = 249
    runner._write_json(run_root / "train_manifest.json", training)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == "INVALID_BEYOND_DECLARED_COUNT_G7"


def test_formal_boundary_and_first_match_branch_logic(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authorization token"):
        runner.train(
            run_root=tmp_path / "bad_token",
            source_commit="7" * 40,
            formal=True,
            authorization_token="wrong",
            g5_run_root=G5_RUN_ROOT,
            eval_episodes=runner.FORMAL_EVAL_EPISODES,
        )
    with pytest.raises(ValueError, match="distinct"):
        runner.train(
            run_root=tmp_path / "same_source",
            source_commit=runner.G5_SOURCE_COMMIT,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            g5_run_root=G5_RUN_ROOT,
            eval_episodes=runner.FORMAL_EVAL_EPISODES,
        )

    passing = {
        "moderate_beyond_deterministic_utility_ci95": [0.90, 0.92, 0.93],
        "far_beyond_deterministic_utility_ci95": [0.90, 0.92, 0.93],
        "joint_deterministic_utility_ci95": [0.90, 0.92, 0.93],
        "joint_replicate_means": [0.85, 0.91, 0.92],
        "joint_min_replicate_mean": 0.85,
        "joint_stochastic_mean": 0.80,
    }
    assert runner.select_result_branch(passing) == "ROBUST_BEYOND_DECLARED_COUNT_G7"
    cases = (
        ("moderate_beyond_deterministic_utility_ci95", "NO_MODERATE_BEYOND_COUNT_G7"),
        ("far_beyond_deterministic_utility_ci95", "NO_FAR_BEYOND_COUNT_G7"),
        ("joint_deterministic_utility_ci95", "NO_JOINT_BEYOND_COUNT_G7"),
    )
    for key, expected in cases:
        values = deepcopy(passing)
        values[key] = [float(np.nextafter(0.90, 0.0)), 0.91, 0.93]
        assert runner.select_result_branch(values) == expected
    unstable = deepcopy(passing)
    unstable["joint_min_replicate_mean"] = float(np.nextafter(0.85, 0.0))
    assert runner.select_result_branch(unstable) == "UNSTABLE_BEYOND_COUNT_G7"
    unstable = deepcopy(passing)
    unstable["joint_stochastic_mean"] = float(np.nextafter(0.80, 0.0))
    assert runner.select_result_branch(unstable) == "UNSTABLE_BEYOND_COUNT_G7"
