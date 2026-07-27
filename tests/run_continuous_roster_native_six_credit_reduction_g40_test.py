from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts import run_continuous_roster_native_six_credit_reduction_g40 as runner


def _valid_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "source_valid": True,
        "g31_access_pass": False,
        "ordinary_access_pass": False,
        "g31_access_confident_fail": False,
        "ordinary_access_confident_fail": False,
        "ordinary_noninferior": False,
        "material_g31_advantage": False,
        "branch_start_equality_pass": True,
    }


def test_first_match_order_is_exact_and_diagnostics_cannot_relabel() -> None:
    row = _valid_metrics()
    assert (
        runner.select_g40_result_branch(row | {"operational_valid": False})
        == runner.INVALID_BRANCH
    )
    assert (
        runner.select_g40_result_branch(row | {"source_valid": False})
        == runner.SOURCE_FAILURE_BRANCH
    )
    assert (
        runner.select_g40_result_branch(
            row
            | {
                "g31_access_confident_fail": True,
                "ordinary_access_confident_fail": True,
            }
        )
        == runner.SOURCE_FAILURE_BRANCH
    )
    assert (
        runner.select_g40_result_branch(
            row
            | {
                "ordinary_access_pass": True,
                "ordinary_noninferior": True,
            }
        )
        == runner.ORDINARY_SUFFICIENT_BRANCH
    )
    assert (
        runner.select_g40_result_branch(
            row
            | {
                "ordinary_access_pass": True,
                "ordinary_noninferior": True,
                "branch_start_equality_pass": False,
                "g31_access_pass": True,
                "ordinary_access_confident_fail": True,
            }
        )
        == runner.G31_ADVANTAGE_BRANCH
    )
    assert (
        runner.select_g40_result_branch(
            row | {"g31_access_pass": True, "material_g31_advantage": True}
        )
        == runner.G31_ADVANTAGE_BRANCH
    )
    assert runner.select_g40_result_branch(row) == runner.UNDERPOWERED_BRANCH


def test_exact_formal_and_nonformal_inventory_and_cpp_binding() -> None:
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["anchor_updates"] == 100
    assert formal["branch_updates_per_arm"] == 100
    assert formal["num_envs"] == 8
    assert formal["ppo_passes"] == 2
    assert formal["evaluation_episodes_per_cell"] == 64
    assert formal["total_cells"] == 90
    assert formal["anchor_training_transitions"] == 115_200
    assert formal["branch_training_transitions"] == 230_400
    assert formal["training_transitions"] == 345_600
    assert formal["evaluation_transitions"] == 276_480
    assert formal["total_real_transitions"] == 622_080
    assert formal["optimizer_steps"] == 3_000
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert formal["environment_python_fallback"] is False
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_transitions"] == 0

    nonformal = runner._configuration(formal=False)
    assert nonformal["replicates"] == 1
    assert nonformal["anchor_updates"] == 10
    assert nonformal["branch_updates_per_arm"] == 10
    assert nonformal["evaluation_episodes_per_cell"] == 6
    assert nonformal["total_cells"] == 30
    assert nonformal["training_transitions"] == 11_520
    assert nonformal["evaluation_transitions"] == 8_640
    assert nonformal["total_real_transitions"] == 20_160
    assert nonformal["optimizer_steps"] == 100
    assert nonformal["bootstrap_resamples"] == 250


def test_whole_episode_paired_bootstrap_has_registered_shape_and_seed() -> None:
    first = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=64, repetitions=32
    )
    second = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=64, repetitions=32
    )
    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])
    assert first[0].shape == (32, 3)
    assert first[1].shape == (32, 3, 3, 64)
    values = {capacity: np.full((3, 64), 0.125) for capacity in runner.g34.CAPACITIES}
    assert runner._hierarchical_ci(
        values, capacities=runner.g34.CAPACITIES, plan=first
    ) == [0.125, 0.125, 0.125]


def test_formal_and_nonformal_authority_fail_closed_before_compute(
    tmp_path: Path,
) -> None:
    source_commit = "a" * 40
    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=source_commit,
            formal=True,
            authorization_token="WRONG",
        )
    with pytest.raises(ValueError, match="cannot carry formal authority"):
        runner.train(
            run_root=tmp_path / "nonformal",
            source_commit=source_commit,
            formal=False,
            authorization_token=runner.AUTHORIZATION_TOKEN,
        )


def _assert_optimizer_state_equal(
    left: torch.optim.Optimizer, right: torch.optim.Optimizer
) -> None:
    left_state, right_state = left.state_dict(), right.state_dict()
    assert left_state["param_groups"] == right_state["param_groups"]
    assert left_state["state"].keys() == right_state["state"].keys()
    for key, left_row in left_state["state"].items():
        right_row = right_state["state"][key]
        assert left_row.keys() == right_row.keys()
        for name, left_value in left_row.items():
            right_value = right_row[name]
            if isinstance(left_value, torch.Tensor):
                assert torch.equal(left_value, right_value), (key, name)
            else:
                assert left_value == right_value, (key, name)


def test_disjoint_branch_parallel_updates_are_bitwise_serial_equivalent() -> None:
    runner.configure_runtime(10_401_000)
    anchor = runner.source.make_model(8, initialization_seed=10_401_000)
    serial = runner.source.clone_anchor_models(anchor)
    parallel = copy.deepcopy(serial)
    for models in (serial, parallel):
        for model in models.values():
            model.begin_credit_branch_phase()
    trajectories = {
        arm: runner.source.collect_g40_trajectory(
            serial[arm],
            episode_ids=(0, 1),
            ledger_seed=10_406_000,
            action_seed=10_406_000,
            device=torch.device("cpu"),
        )
        for arm in runner.source.ARMS
    }

    def optimizers(models):
        return (
            {
                arm: runner._optimizer(model.actor_credit_parameters())
                for arm, model in models.items()
            },
            {
                arm: runner._optimizer(model.slow_critic_parameters())
                for arm, model in models.items()
            },
        )

    serial_actor, serial_critic = optimizers(serial)
    parallel_actor, parallel_critic = optimizers(parallel)
    serial_metrics = {
        arm: runner.source.optimize_credit_branch_update(
            arm,
            serial[arm],
            serial_actor[arm],
            serial_critic[arm],
            trajectories[arm],
            ppo_passes=1,
        )
        for arm in runner.source.ARMS
    }
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            arm: executor.submit(
                runner.source.optimize_credit_branch_update,
                arm,
                parallel[arm],
                parallel_actor[arm],
                parallel_critic[arm],
                trajectories[arm],
                ppo_passes=1,
            )
            for arm in runner.source.ARMS
        }
        parallel_metrics = {
            arm: futures[arm].result() for arm in runner.source.ARMS
        }
    assert serial_metrics == parallel_metrics
    for arm in runner.source.ARMS:
        for name, value in serial[arm].state_dict().items():
            assert torch.equal(value, parallel[arm].state_dict()[name]), (arm, name)
        _assert_optimizer_state_equal(serial_actor[arm], parallel_actor[arm])
        _assert_optimizer_state_equal(serial_critic[arm], parallel_critic[arm])


def test_bounded_cpp_backed_train_evaluate_analyze_closes_all_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "EXERCISE_ANCHOR_UPDATES", 1)
    monkeypatch.setattr(runner, "EXERCISE_BRANCH_UPDATES", 1)
    monkeypatch.setattr(runner, "EXERCISE_PPO_PASSES", 1)
    monkeypatch.setattr(runner, "EXERCISE_EVAL_EPISODES", 1)
    monkeypatch.setattr(runner, "EXERCISE_BOOTSTRAP_REPETITIONS", 16)
    run_root = tmp_path / "proof"
    result = runner.exercise(run_root=run_root, source_commit="b" * 40)
    training = json.loads((run_root / "train_manifest.json").read_text("utf-8"))
    evaluation = json.loads(
        (run_root / "evaluation_manifest.json").read_text("utf-8")
    )
    assert result["operational_valid"] is True, result["operational_errors"]
    assert result["branch"] == runner.NONFORMAL_BRANCH
    assert result["gae1_return_identity_valid"] is True
    assert result["native_backend"]["python_fallback"] is False
    assert training["native_backend"]["required"] is True
    assert training["native_backend"]["python_fallback"] is False
    assert training["gae1_return_identity_valid"] is True
    assert evaluation["gae1_return_identity_valid"] is True
    assert len(evaluation["cells"]) == 30
    assert runner._training_errors(run_root, training) == []
    assert runner._evaluation_errors(run_root, training, evaluation) == []

    row = training["replicate_results"][0]
    assert row["source_preflight_audit"]["passed"] is True
    assert row["pre_common_gradient_audit"]["passed"] is True
    assert row["branch_boundary_audit"]["passed"] is True
    assert row["first_branch_forward_match"]["passed"] is True
    assert row["first_branch_trajectory_match"]["passed"] is True
    assert runner.source.validate_branch_gradient_audit(
        row["first_branch_gradient_audit"]
    )
    assert row["torch_rng_unchanged_by_branch_objective"] is True
    assert row["common_anchor"]["optimizer_steps"] == 1
    assert row["common_anchor"]["optimizer_state_discarded"] is True
    assert row["gae1_return_identity_max_error"] <= 1e-6
    for arm in runner.source.ARMS:
        assert row["arms"][arm]["actor_optimizer_steps"] == 1
        assert row["arms"][arm]["slow_critic_optimizer_steps"] == 1
    assert sorted(path.name for path in (run_root / "checkpoints").iterdir()) == sorted(
        [
            Path(row["common_anchor"]["checkpoint"]).name,
            *[
                Path(row["arms"][arm]["final_checkpoint"]).name
                for arm in runner.source.ARMS
            ],
        ]
    )
