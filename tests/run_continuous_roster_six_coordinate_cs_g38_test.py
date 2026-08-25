from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts import run_continuous_roster_six_coordinate_cs_g38 as runner


def _valid_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "source_valid": True,
        "full_access_pass": False,
        "fold_access_pass": False,
        "full_access_confident_fail": False,
        "fold_access_confident_fail": False,
        "six_coordinate_noninferior": False,
        "material_info_advantage": False,
        "fold_equivalence_pass": True,
    }


def test_first_match_truth_table_and_branch_precedence_are_exact() -> None:
    row = _valid_metrics()
    assert runner.select_g38_result_branch(row | {"operational_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_g38_result_branch(row | {"source_valid": False}) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g38_result_branch(
        row | {"full_access_confident_fail": True, "fold_access_confident_fail": True}
    ) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g38_result_branch(
        row
        | {
            "fold_access_pass": True,
            "six_coordinate_noninferior": True,
            "full_access_pass": True,
            "material_info_advantage": True,
        }
    ) == runner.SIX_COORDINATE_SUFFICIENT_BRANCH
    assert runner.select_g38_result_branch(
        row | {"full_access_pass": True, "fold_access_confident_fail": True}
    ) == runner.FULL_INFORMATION_ADVANTAGE_BRANCH
    assert runner.select_g38_result_branch(
        row | {"full_access_pass": True, "material_info_advantage": True}
    ) == runner.FULL_INFORMATION_ADVANTAGE_BRANCH
    assert runner.select_g38_result_branch(row) == runner.UNDERPOWERED_BRANCH


def test_configuration_freezes_exact_formal_and_nonformal_inventory() -> None:
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["arms"] == ["FULL10_CS", "FOLD6_CS"]
    assert formal["fast_updates"] == 100
    assert formal["return_to_go_updates"] == 100
    assert formal["num_envs"] == 8
    assert formal["ppo_passes"] == 2
    assert formal["cells_per_arm_capacity"] == 5
    assert formal["cells_per_replicate"] == 30
    assert formal["total_cells"] == 90
    assert formal["training_transitions"] == 460_800
    assert formal["evaluation_transitions"] == 552_960
    assert formal["total_real_transitions"] == 1_013_760
    assert formal["optimizer_steps"] == 3_600
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_transitions"] == 0
    assert formal["nested_rollout"] is False
    assert formal["replanning"] is False
    assert formal["per_episode_complexity"] == "O(H)"

    nonformal = runner._configuration(formal=False)
    assert nonformal["replicates"] == 1
    assert nonformal["total_cells"] == 30
    assert nonformal["evaluation_episodes_per_cell"] == 8
    assert nonformal["training_transitions"] == 15_360
    assert nonformal["evaluation_transitions"] == 11_520
    assert nonformal["total_real_transitions"] == 26_880
    assert nonformal["optimizer_steps"] == 120
    assert nonformal["bootstrap_resamples"] == 250


def test_proof_sized_paired_training_updates_both_arms_and_folds_final(
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
    assert set(row["initial_gradient_audits"]) == set(runner.source.ARMS)
    assert all(
        row["initial_gradient_audits"][arm]["passed"] is True
        for arm in runner.source.ARMS
    )
    for arm in runner.source.ARMS:
        assert row["arms"][arm]["fast_optimizer_steps"] == 1
        assert row["arms"][arm]["return_to_go_actor_optimizer_steps"] == 1
        assert row["arms"][arm]["return_to_go_critic_optimizer_steps"] == 1
    assert row["arms"][runner.source.FULL10_ARM]["stored_replay_observation_width"] == 10
    assert row["arms"][runner.source.FOLD6_ARM]["stored_replay_observation_width"] == 6
    assert set(row["folded_checkpoints"]) == {"zero", "final"}
    assert row["folded_checkpoints"]["zero"]["pre_fold_source_digest"] == row["arms"][
        runner.source.FOLD6_ARM
    ]["zero_state_digest"]
    assert row["folded_checkpoints"]["final"]["pre_fold_source_digest"] == row["arms"][
        runner.source.FOLD6_ARM
    ]["final_state_digest"]


def test_bootstrap_plan_preserves_whole_episode_pairing_and_capacity_weight() -> None:
    values = {
        capacity: np.full((3, 128), 0.125, dtype=np.float64)
        for capacity in runner.g34.CAPACITIES
    }
    plan = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=128, repetitions=128
    )
    interval = runner._hierarchical_ci(
        values, capacities=runner.g34.CAPACITIES, plan=plan
    )
    np.testing.assert_allclose(interval, [0.125, 0.125, 0.125], atol=0, rtol=0)
    assert plan[0].shape == (128, 3)
    assert plan[1].shape == (128, 3, 3, 128)


def test_equality_semantics_are_inclusive_except_registered_strict_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=128, repetitions=64
    )

    def exact_margin(
        evaluation: object, arm: str, cell: str, metric: str
    ) -> dict[int, np.ndarray]:
        del evaluation, cell, metric
        value = 0.05 if arm == runner.source.FULL10_ARM else 0.0
        return {
            capacity: np.full((3, 128), value, dtype=np.float64)
            for capacity in runner.g34.CAPACITIES
        }

    monkeypatch.setattr(runner, "_metric_arrays", exact_margin)
    comparison = runner._information_comparison({}, plan)
    assert comparison["full10_minus_fold6_primary_ci95"] == [0.05, 0.05, 0.05]
    assert comparison["six_coordinate_noninferior"] is True
    assert comparison["material_info_advantage"] is False

    def access_arrays(
        evaluation: object, arm: str, cell: str, metric: str
    ) -> dict[int, np.ndarray]:
        del evaluation, arm
        if cell == runner.ZERO_RANDOM_DET:
            value = 0.89
        elif metric in ("minimum_event_window_utility", "minimum_process_segment_utility"):
            value = 0.85
        elif cell in (runner.FINAL_FIXED_STOCH, runner.FINAL_RANDOM_STOCH):
            value = 0.80
        else:
            value = 0.90
        return {
            capacity: np.full((3, 128), value, dtype=np.float64)
            for capacity in runner.g34.CAPACITIES
        }

    monkeypatch.setattr(runner, "_metric_arrays", access_arrays)
    access = runner._arm_access({}, runner.source.FOLD6_ARM, plan)
    assert access["access_pass"] is True

    def zero_gain(
        evaluation: object, arm: str, cell: str, metric: str
    ) -> dict[int, np.ndarray]:
        values = access_arrays(evaluation, arm, cell, metric)
        if cell == runner.ZERO_RANDOM_DET:
            return {
                capacity: np.full((3, 128), 0.90, dtype=np.float64)
                for capacity in runner.g34.CAPACITIES
            }
        return values

    monkeypatch.setattr(runner, "_metric_arrays", zero_gain)
    access = runner._arm_access({}, runner.source.FOLD6_ARM, plan)
    assert access["access_pass"] is False
    assert access["access_confident_fail"] is True


def _write_preflight(root: Path, source_commit: str) -> None:
    configuration = runner._configuration(formal=False)
    training = {
        "formal": False,
        "source_commit": source_commit,
        "configuration": configuration,
        "stage_wall_time_seconds": 1.0,
    }
    evaluation = {
        "formal": False,
        "source_commit": source_commit,
        "configuration": configuration,
        "stage_wall_time_seconds": 1.0,
    }
    root.mkdir()
    (root / "train_manifest.json").write_text(
        json.dumps(training, sort_keys=True), encoding="utf-8"
    )
    (root / "evaluation_manifest.json").write_text(
        json.dumps(evaluation, sort_keys=True), encoding="utf-8"
    )
    projection = 1.25 * (30.0 + 48.0 + 40.0)
    analysis = {
        "schema_version": runner.SCHEMA_VERSION,
        "algorithm": runner.ALGORITHM_ID,
        "source_id": runner.source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE",
        "formal": False,
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
    (root / "analysis_result.json").write_text(
        json.dumps(analysis, sort_keys=True), encoding="utf-8"
    )


def test_formal_authority_alignment_and_all_three_preflight_digests_are_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_commit = "a" * 40
    preflight = tmp_path / "preflight"
    _write_preflight(preflight, source_commit)
    monkeypatch.setattr(runner, "_evaluation_errors", lambda *args: [])
    digests = runner._validate_formal_preflight(
        preflight,
        source_commit=source_commit,
        alignment_disposition="ALIGNED",
        aligned_source_commit=source_commit,
    )
    assert digests == {
        "training": runner._artifact_digest(preflight / "train_manifest.json"),
        "evaluation": runner._artifact_digest(preflight / "evaluation_manifest.json"),
        "analysis": runner._artifact_digest(preflight / "analysis_result.json"),
    }
    with pytest.raises(ValueError, match="ALIGNED same-source"):
        runner._validate_formal_preflight(
            preflight,
            source_commit=source_commit,
            alignment_disposition="NOT_ALIGNED",
            aligned_source_commit=source_commit,
        )
    with pytest.raises(ValueError, match="ALIGNED same-source"):
        runner._validate_formal_preflight(
            preflight,
            source_commit=source_commit,
            alignment_disposition="ALIGNED",
            aligned_source_commit="b" * 40,
        )

    training = json.loads((preflight / "train_manifest.json").read_text(encoding="utf-8"))
    training["stage_wall_time_seconds"] = 2.0
    (preflight / "train_manifest.json").write_text(
        json.dumps(training, sort_keys=True), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="not executable"):
        runner._validate_formal_preflight(
            preflight,
            source_commit=source_commit,
            alignment_disposition="ALIGNED",
            aligned_source_commit=source_commit,
        )


def test_nonformal_train_rejects_every_formal_authority_binding(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot carry formal authority"):
        runner.train(
            run_root=tmp_path / "run",
            source_commit="c" * 40,
            formal=False,
            authorization_token=runner.AUTHORIZATION_TOKEN,
        )
