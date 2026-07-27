from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

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
    assert row["initial_gradient_audit"]["passed"] is True
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
    assert all(len(cell["episodes"]) == 2 for cell in evaluation["cells"])
    assert analysis["operational_valid"] is True, analysis["operational_errors"]
    assert analysis["branch"] in (runner.NONFORMAL_BRANCH, runner.NON_EXECUTABLE_BRANCH)
    tampered_evaluation = dict(evaluation)
    tampered_evaluation["aligned_source_commit"] = "f" * 40
    assert "G39 evaluation identity/source mismatch" in runner._evaluation_errors(
        root,
        training,
        tampered_evaluation,
    )
