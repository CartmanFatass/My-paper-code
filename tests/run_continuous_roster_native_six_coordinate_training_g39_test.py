from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts import run_continuous_roster_native_six_coordinate_training_g39 as runner


def _valid_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "source_valid": True,
        "const_access_pass": False,
        "native_access_pass": False,
        "const_access_confident_fail": False,
        "native_access_confident_fail": False,
        "native_noninferior": False,
        "material_const_advantage": False,
        "initial_match_pass": True,
    }


def test_first_match_truth_table_and_precedence_are_exact() -> None:
    row = _valid_metrics()
    assert runner.select_g39_result_branch(row | {"operational_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_g39_result_branch(row | {"source_valid": False}) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g39_result_branch(
        row | {"const_access_confident_fail": True, "native_access_confident_fail": True}
    ) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g39_result_branch(
        row | {"native_access_pass": True, "native_noninferior": True}
    ) == runner.NATIVE_SUFFICIENT_BRANCH
    assert runner.select_g39_result_branch(
        row
        | {
            "native_access_pass": True,
            "native_noninferior": True,
            "initial_match_pass": False,
            "const_access_pass": True,
            "native_access_confident_fail": True,
        }
    ) == runner.CONST_ADVANTAGE_BRANCH
    assert runner.select_g39_result_branch(
        row | {"const_access_pass": True, "material_const_advantage": True}
    ) == runner.CONST_ADVANTAGE_BRANCH
    assert runner.select_g39_result_branch(row) == runner.UNDERPOWERED_BRANCH


def test_exact_formal_and_nonformal_inventory() -> None:
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["arms"] == ["CONST10_FOLD6", "NATIVE6_CS"]
    assert formal["fast_updates"] == 100
    assert formal["return_to_go_updates"] == 100
    assert formal["num_envs"] == 8
    assert formal["ppo_passes"] == 2
    assert formal["evaluation_episodes_per_cell"] == 64
    assert formal["total_cells"] == 90
    assert formal["training_transitions"] == 460_800
    assert formal["evaluation_transitions"] == 276_480
    assert formal["total_real_transitions"] == 737_280
    assert formal["optimizer_steps"] == 3_600
    assert formal["evaluation_cell_workers"] == 1
    assert formal["evaluation_parallelism"] == "serial_cells_native_batched_episodes"
    assert formal["training_arm_update_workers"] == 2
    assert formal["training_update_parallelism"] == "disjoint_arm_optimizers_only"
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_transitions"] == 0
    assert formal["nested_rollout"] is False
    assert formal["replanning"] is False
    assert formal["per_episode_complexity"] == "O(H)"

    nonformal = runner._configuration(formal=False)
    assert nonformal["replicates"] == 1
    assert nonformal["fast_updates"] == 10
    assert nonformal["return_to_go_updates"] == 10
    assert nonformal["evaluation_episodes_per_cell"] == 6
    assert nonformal["total_cells"] == 30
    assert nonformal["training_transitions"] == 15_360
    assert nonformal["evaluation_transitions"] == 8_640
    assert nonformal["total_real_transitions"] == 24_000
    assert nonformal["optimizer_steps"] == 120
    assert nonformal["bootstrap_resamples"] == 250


def _assert_optimizer_state_equal(
    expected: torch.optim.Optimizer, actual: torch.optim.Optimizer
) -> None:
    left = expected.state_dict()
    right = actual.state_dict()
    assert left["param_groups"] == right["param_groups"]
    assert left["state"].keys() == right["state"].keys()
    for key, expected_row in left["state"].items():
        actual_row = right["state"][key]
        assert expected_row.keys() == actual_row.keys()
        for name, expected_value in expected_row.items():
            actual_value = actual_row[name]
            if isinstance(expected_value, torch.Tensor):
                assert torch.equal(expected_value, actual_value), (key, name)
            else:
                assert expected_value == actual_value, (key, name)


def _assert_models_equal(
    expected: dict[str, runner.source.G39Policy],
    actual: dict[str, runner.source.G39Policy],
) -> None:
    for arm in runner.source.ARMS:
        for name, expected_value in expected[arm].state_dict().items():
            assert torch.equal(expected_value, actual[arm].state_dict()[name]), (
                arm,
                name,
            )


def test_disjoint_arm_optimizer_parallelism_is_bitwise_serial_equivalent() -> None:
    runner.configure_runtime(10_991_000)
    serial_models = runner.source.make_paired_models(8, initialization_seed=10_991_000)
    parallel_models = runner.source.make_paired_models(8, initialization_seed=10_991_000)
    trajectories = {
        arm: runner._collect(
            serial_models[arm],
            episode_ids=tuple(range(8)),
            ledger_seed=10_992_000,
            action_seed=10_993_000,
        )
        for arm in runner.source.ARMS
    }
    serial_fast = {
        arm: runner._optimizer(
            model,
            model.fast_actor_parameters() + tuple(model.credit_baselines.parameters()),
        )
        for arm, model in serial_models.items()
    }
    parallel_fast = {
        arm: runner._optimizer(
            model,
            model.fast_actor_parameters() + tuple(model.credit_baselines.parameters()),
        )
        for arm, model in parallel_models.items()
    }

    serial_metrics = {
        arm: runner.optimize_fast_anchor_update(
            serial_models[arm],
            serial_fast[arm],
            trajectories[arm],
            device=torch.device("cpu"),
            ppo_passes=1,
        )
        for arm in runner.source.ARMS
    }
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            arm: executor.submit(
                runner.optimize_fast_anchor_update,
                parallel_models[arm],
                parallel_fast[arm],
                trajectories[arm],
                device=torch.device("cpu"),
                ppo_passes=1,
            )
            for arm in runner.source.ARMS
        }
        parallel_metrics = {
            arm: futures[arm].result() for arm in runner.source.ARMS
        }
    assert serial_metrics == parallel_metrics
    _assert_models_equal(serial_models, parallel_models)
    for arm in runner.source.ARMS:
        _assert_optimizer_state_equal(serial_fast[arm], parallel_fast[arm])

    for models in (serial_models, parallel_models):
        for model in models.values():
            model.begin_direction_balanced_phase()
    trajectories = {
        arm: runner._collect(
            serial_models[arm],
            episode_ids=tuple(range(8, 16)),
            ledger_seed=10_992_000,
            action_seed=10_993_000,
        )
        for arm in runner.source.ARMS
    }
    serial_actor = {
        arm: runner._optimizer(model, model.full_actor_parameters())
        for arm, model in serial_models.items()
    }
    serial_critic = {
        arm: runner._optimizer(model, model.critic_parameters())
        for arm, model in serial_models.items()
    }
    parallel_actor = {
        arm: runner._optimizer(model, model.full_actor_parameters())
        for arm, model in parallel_models.items()
    }
    parallel_critic = {
        arm: runner._optimizer(model, model.critic_parameters())
        for arm, model in parallel_models.items()
    }

    serial_metrics = {
        arm: runner.optimize_return_to_go_direction_balanced_update(
            serial_models[arm],
            serial_actor[arm],
            serial_critic[arm],
            trajectories[arm],
            device=torch.device("cpu"),
            ppo_passes=1,
            gamma=runner.GAMMA,
        )
        for arm in runner.source.ARMS
    }
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            arm: executor.submit(
                runner.optimize_return_to_go_direction_balanced_update,
                parallel_models[arm],
                parallel_actor[arm],
                parallel_critic[arm],
                trajectories[arm],
                device=torch.device("cpu"),
                ppo_passes=1,
                gamma=runner.GAMMA,
            )
            for arm in runner.source.ARMS
        }
        parallel_metrics = {
            arm: futures[arm].result() for arm in runner.source.ARMS
        }
    assert serial_metrics == parallel_metrics
    _assert_models_equal(serial_models, parallel_models)
    for arm in runner.source.ARMS:
        _assert_optimizer_state_equal(serial_actor[arm], parallel_actor[arm])
        _assert_optimizer_state_equal(serial_critic[arm], parallel_critic[arm])


def test_proof_training_collects_both_before_update_and_uses_fresh_phase_states(
    tmp_path: Path,
) -> None:
    configuration = runner._configuration(formal=False) | {
        "fast_updates": 1,
        "return_to_go_updates": 1,
        "ppo_passes": 1,
    }
    run_root = tmp_path / "proof"
    (run_root / "checkpoints").mkdir(parents=True)
    row = runner._train_replicate(
        run_root=run_root,
        source_commit="d" * 40,
        formal=False,
        replicate=0,
        configuration=configuration,
    )
    assert row["paired_collection_before_update"] is True
    assert row["zero_function_digest_equal"] is True
    assert row["initial_forward_match"]["passed"] is True
    assert row["initial_trajectory_match"]["passed"] is True
    assert runner.source.validate_initial_gradient_audit_record(
        row["initial_gradient_audit"]
    )
    assert row["initial_fast_optimizer_states_empty_separate"] is True
    assert row["fast_optimizer_states_discarded"] is True
    assert row["direction_optimizer_states_fresh_empty_separate"] is True
    for arm in runner.source.ARMS:
        assert row["arms"][arm]["stored_replay_observation_width"] == 6
        assert row["arms"][arm]["fast_optimizer_steps"] == 1
        assert row["arms"][arm]["return_to_go_actor_optimizer_steps"] == 1
        assert row["arms"][arm]["return_to_go_critic_optimizer_steps"] == 1
    checkpoints = sorted(path.name for path in (run_root / "checkpoints").iterdir())
    assert len(checkpoints) == 3
    assert all("final" in name for name in checkpoints)
    assert row["folded_const_final"]["optimizer_steps_after_fold"] == 0


def test_dead_common_baseline_group_fails_before_first_optimizer_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = runner._configuration(formal=False) | {
        "fast_updates": 1,
        "return_to_go_updates": 1,
        "ppo_passes": 1,
    }
    original_make = runner.source.make_paired_models
    original_audit = runner.source.initial_gradient_audit
    captured: dict[str, object] = {}

    def models_with_dead_common_baseline(
        *args: object, **kwargs: object
    ) -> dict[str, runner.source.G39Policy]:
        models = original_make(*args, **kwargs)
        baseline = models[runner.source.CONST10_ARM].credit_baselines
        original_forward = baseline.forward

        def zero_gradient_forward(input: torch.Tensor) -> torch.Tensor:
            output = original_forward(input)
            zero_connection = output.new_zeros(())
            for parameter in baseline.parameters():
                zero_connection = zero_connection + 0.0 * parameter.sum()
            return output.detach() + zero_connection

        baseline.forward = zero_gradient_forward
        return models

    def capture_actual_audit(*args: object, **kwargs: object) -> dict[str, object]:
        audit = original_audit(*args, **kwargs)
        captured.clear()
        captured.update(audit)
        return audit

    optimizer_calls = 0

    def forbidden_first_step(*args: object, **kwargs: object) -> object:
        nonlocal optimizer_calls
        optimizer_calls += 1
        raise AssertionError("optimizer ran before the registered-group gate")

    monkeypatch.setattr(
        runner.source,
        "make_paired_models",
        models_with_dead_common_baseline,
    )
    monkeypatch.setattr(runner.source, "initial_gradient_audit", capture_actual_audit)
    monkeypatch.setattr(runner, "optimize_fast_anchor_update", forbidden_first_step)
    with pytest.raises(RuntimeError, match="initial function/trajectory/gradient gate"):
        runner._train_replicate(
            run_root=tmp_path / "dead-group",
            source_commit="e" * 40,
            formal=False,
            replicate=0,
            configuration=configuration,
        )
    assert captured["scalar_liveness"]["all_136_removable_scalars_live"] is True
    dead_group = captured["registered_trainable_groups"][runner.source.CONST10_ARM][
        "immediate_baseline"
    ]
    assert dead_group["finite"] is True
    assert dead_group["live"] is False
    assert dead_group["fast_objective_gradient_norm"] == 0.0
    assert dead_group["return_to_go_objective_gradient_norm"] == 0.0
    assert optimizer_calls == 0


def test_g34_eval_pairing_and_whole_episode_hierarchical_bootstrap() -> None:
    processes = runner.source.make_process_ledgers(
        replicate=0, capacity=6, episode_count=6, formal=False
    )
    models = runner.source.make_paired_models(6, initialization_seed=11_291_000)
    const = runner.source.fold_const_checkpoint(models[runner.source.CONST10_ARM])
    const_rows, const_lifecycle = runner.source.evaluate_g39_model(
        const,
        processes=processes,
        action_seed=11_296_000,
        process_kind="random",
        deterministic=False,
    )
    native_rows, native_lifecycle = runner.source.evaluate_g39_model(
        models[runner.source.NATIVE6_ARM],
        processes=processes,
        action_seed=11_296_000,
        process_kind="random",
        deterministic=False,
    )
    assert const_lifecycle is True
    assert native_lifecycle is True
    assert [row["signature"] for row in const_rows] == [row["signature"] for row in native_rows]
    assert [row["episode_id"] for row in const_rows] == [row["episode_id"] for row in native_rows]

    values = {capacity: np.full((3, 64), 0.125) for capacity in runner.g34.CAPACITIES}
    plan = runner._bootstrap_plan(formal=True, replicates=3, episodes=64, repetitions=128)
    interval = runner._hierarchical_ci(values, capacities=runner.g34.CAPACITIES, plan=plan)
    np.testing.assert_allclose(interval, [0.125, 0.125, 0.125], atol=0, rtol=0)
    assert plan[0].shape == (128, 3)
    assert plan[1].shape == (128, 3, 3, 64)


def _write_preflight(root: Path, source_commit: str) -> None:
    configuration = runner._configuration(formal=False)
    root.mkdir()
    training = {
        "formal": False,
        "source_commit": source_commit,
        "configuration": configuration,
        "stage_wall_time_seconds": 1.0,
    }
    evaluation = dict(training)
    (root / "train_manifest.json").write_text(json.dumps(training), encoding="utf-8")
    (root / "evaluation_manifest.json").write_text(json.dumps(evaluation), encoding="utf-8")
    projection = 1.25 * (30.0 + 32.0 + 40.0)
    analysis = {
        "formal": False,
        "algorithm": runner.ALGORITHM_ID,
        "source_id": runner.source.SOURCE_ID,
        "source_commit": source_commit,
        "branch": runner.NONFORMAL_BRANCH,
        "operational_valid": True,
        "operational_errors": [],
        "stage_wall_time_seconds": 1.0,
        "training_manifest_digest": runner._artifact_digest(root / "train_manifest.json"),
        "evaluation_manifest_digest": runner._artifact_digest(root / "evaluation_manifest.json"),
        "formal_projection_seconds": projection,
        "formal_projection_executable": True,
    }
    (root / "analysis_result.json").write_text(json.dumps(analysis), encoding="utf-8")


def test_formal_authority_binds_alignment_source_and_three_preflight_digests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_commit = "a" * 40
    root = tmp_path / "preflight"
    _write_preflight(root, source_commit)
    monkeypatch.setattr(runner, "_evaluation_errors", lambda *args: [])
    valid_digests = runner._validate_formal_preflight(
        root,
        source_commit=source_commit,
        alignment_disposition="ALIGNED",
        aligned_source_commit=source_commit,
    )
    assert valid_digests == {
        "training": runner._artifact_digest(root / "train_manifest.json"),
        "evaluation": runner._artifact_digest(root / "evaluation_manifest.json"),
        "analysis": runner._artifact_digest(root / "analysis_result.json"),
    }
    with pytest.raises(ValueError, match="ALIGNED same-source"):
        runner._validate_formal_preflight(
            root,
            source_commit=source_commit,
            alignment_disposition="NOT_ALIGNED",
            aligned_source_commit=source_commit,
        )
    with pytest.raises(ValueError, match="ALIGNED same-source"):
        runner._validate_formal_preflight(
            root,
            source_commit=source_commit,
            alignment_disposition="ALIGNED",
            aligned_source_commit="f" * 40,
        )
    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=source_commit,
            formal=True,
            authorization_token="WRONG_TOKEN",
            preflight_root=root,
            alignment_disposition="ALIGNED",
            aligned_source_commit=source_commit,
        )
    with pytest.raises(ValueError, match="cannot carry formal authority"):
        runner.train(
            run_root=tmp_path / "run",
            source_commit="b" * 40,
            formal=False,
            authorization_token=runner.AUTHORIZATION_TOKEN,
        )

    training_path = root / "train_manifest.json"
    analysis_path = root / "analysis_result.json"
    original_training = json.loads(training_path.read_text(encoding="utf-8"))
    original_analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    changed_configuration = json.loads(json.dumps(original_training))
    changed_configuration["configuration"]["hypothetical_transitions"] = 1
    training_path.write_text(json.dumps(changed_configuration), encoding="utf-8")
    changed_analysis = dict(original_analysis)
    changed_analysis["training_manifest_digest"] = runner._artifact_digest(training_path)
    analysis_path.write_text(json.dumps(changed_analysis), encoding="utf-8")
    with pytest.raises(ValueError, match="not executable"):
        runner._validate_formal_preflight(
            root,
            source_commit=source_commit,
            alignment_disposition="ALIGNED",
            aligned_source_commit=source_commit,
        )
    training_path.write_text(json.dumps(original_training), encoding="utf-8")
    analysis_path.write_text(json.dumps(original_analysis), encoding="utf-8")
    over_cap = dict(original_training)
    over_cap["stage_wall_time_seconds"] = 1_201.0
    training_path.write_text(json.dumps(over_cap), encoding="utf-8")
    over_cap_analysis = dict(original_analysis)
    over_cap_analysis["training_manifest_digest"] = runner._artifact_digest(training_path)
    over_cap_analysis["formal_projection_seconds"] = 1.25 * (
        30.0 * 1_201.0 + 32.0 + 40.0
    )
    over_cap_analysis["formal_projection_executable"] = True
    analysis_path.write_text(json.dumps(over_cap_analysis), encoding="utf-8")
    with pytest.raises(ValueError, match="not executable"):
        runner._validate_formal_preflight(
            root,
            source_commit=source_commit,
            alignment_disposition="ALIGNED",
            aligned_source_commit=source_commit,
        )
    training_path.write_text(json.dumps(original_training), encoding="utf-8")
    analysis_path.write_text(json.dumps(original_analysis), encoding="utf-8")

    formal_training = {
        "schema_version": runner.SCHEMA_VERSION,
        "algorithm": runner.ALGORITHM_ID,
        "source_id": runner.source.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": True,
        "source_commit": source_commit,
        "authorization_token": runner.AUTHORIZATION_TOKEN,
        "alignment_audit_id": runner.ALIGNMENT_AUDIT_ID,
        "alignment_disposition": "ALIGNED",
        "aligned_source_commit": source_commit,
        "preflight_root": str(root.resolve()),
        "preflight_artifact_digests": valid_digests,
        "configuration": runner._configuration(formal=True),
        "source_controls": runner.source.source_controls(),
        "replicate_results": [],
    }
    changed_analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    changed_analysis["nonbranch_diagnostic"] = "tampered"
    analysis_path.write_text(json.dumps(changed_analysis), encoding="utf-8")
    errors = runner._training_errors(root, formal_training)
    assert "G39 formal preflight digest binding mismatch" in errors


def test_bounded_end_to_end_train_evaluate_analyze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proof_counts = {
        "replicates": 1,
        "fast_updates": 1,
        "return_to_go_updates": 1,
        "num_envs": 8,
        "ppo_passes": 1,
        "evaluation_episodes_per_cell": 2,
        "bootstrap_resamples": 32,
    }
    monkeypatch.setattr(runner, "_counts", lambda *, formal: dict(proof_counts))
    root = tmp_path / "bounded"
    training = runner.train(
        run_root=root,
        source_commit="c" * 40,
        formal=False,
        authorization_token=None,
    )
    evaluation = runner.evaluate(run_root=root)
    analysis = runner.analyze(run_root=root)
    assert training["status"] == "COMPLETE"
    assert len(evaluation["cells"]) == 30
    assert [
        (cell["replicate"], cell["capacity"], cell["arm"], cell["cell"])
        for cell in evaluation["cells"]
    ] == [
        (replicate, capacity, arm, cell)
        for replicate in range(1)
        for capacity in runner.g34.CAPACITIES
        for arm in runner.source.ARMS
        for cell in runner.MODEL_CELLS
    ]
    assert all(len(cell["episodes"]) == 2 for cell in evaluation["cells"])
    assert analysis["operational_valid"] is True, analysis["operational_errors"]
    assert analysis["branch"] in (runner.NONFORMAL_BRANCH, runner.NON_EXECUTABLE_BRANCH)
    tampered_training = copy.deepcopy(training)
    dead_group = tampered_training["replicate_results"][0][
        "initial_gradient_audit"
    ]["registered_trainable_groups"][runner.source.NATIVE6_ARM]["immediate_baseline"]
    dead_group["fast_objective_gradient_norm"] = 0.0
    dead_group["return_to_go_objective_gradient_norm"] = 0.0
    dead_group["live"] = False
    assert "G39 initialization/training gate mismatch" in runner._training_errors(
        root,
        tampered_training,
    )
    tampered_evaluation = dict(evaluation)
    tampered_evaluation["aligned_source_commit"] = "f" * 40
    assert "G39 evaluation identity/source mismatch" in runner._evaluation_errors(
        root,
        training,
        tampered_evaluation,
    )
