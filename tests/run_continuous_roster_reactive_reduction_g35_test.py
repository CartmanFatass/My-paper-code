from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from ha_ctse_process import continuous_roster_reactive_reduction_g35 as source
from scripts import run_continuous_roster_reactive_reduction_g35 as runner


def _valid_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "source_valid": True,
        "rec_access_confident_fail": False,
        "cs_access_confident_fail": False,
        "current_state_sufficient": False,
        "recurrent_advantage": False,
    }


def test_first_match_truth_table_is_exact() -> None:
    row = _valid_metrics()
    assert runner.select_g35_result_branch({**row, "operational_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_g35_result_branch({**row, "source_valid": False}) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g35_result_branch(
        {**row, "rec_access_confident_fail": True, "cs_access_confident_fail": True}
    ) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g35_result_branch(
        {**row, "current_state_sufficient": True, "recurrent_advantage": True}
    ) == runner.CS_SUFFICIENT_BRANCH
    assert runner.select_g35_result_branch(
        {**row, "recurrent_advantage": True}
    ) == runner.REC_ADVANTAGE_BRANCH
    assert runner.select_g35_result_branch(row) == runner.UNDERPOWERED_BRANCH


def test_configuration_freezes_exact_inventory_and_complexity() -> None:
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["total_cells"] == 99
    assert formal["training_transitions"] == 460_800
    assert formal["evaluation_transitions"] == 608_256
    assert formal["total_real_transitions"] == 1_069_056
    assert formal["optimizer_steps"] == 3_600
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_transitions"] == 0
    assert formal["nested_rollout"] is False
    assert formal["replanning"] is False

    exercise = runner._configuration(formal=False)
    assert exercise["replicates"] == 1
    assert exercise["arms"] == list(source.ARMS)
    assert exercise["fast_updates"] == 10
    assert exercise["return_to_go_updates"] == 10
    assert exercise["training_transitions"] == 15_360
    assert exercise["evaluation_transitions"] == 12_672
    assert exercise["total_real_transitions"] == 28_032
    assert exercise["optimizer_steps"] == 120
    assert exercise["total_cells"] == 33


def test_hierarchical_plan_keeps_the_paired_arm_difference() -> None:
    plan = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=8, repetitions=100
    )
    base = {
        capacity: np.arange(24, dtype=np.float64).reshape(3, 8)
        + capacity
        for capacity in source.g34.CAPACITIES
    }
    rec = {capacity: values + 0.04 for capacity, values in base.items()}
    delta = runner._difference(rec, base)
    pooled = runner._hierarchical_ci(
        delta, capacities=source.g34.CAPACITIES, plan=plan
    )
    assert pooled == pytest.approx([0.04, 0.04, 0.04])


def test_formal_train_requires_authority_and_matching_preflight(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authorization"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit="1" * 40,
            formal=True,
            authorization_token=None,
        )
    with pytest.raises(ValueError, match="preflight"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit="1" * 40,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
        )


def test_formal_train_rejects_favorable_summary_only_preflight(
    tmp_path: Path,
) -> None:
    source_commit = "3" * 40
    preflight_root = tmp_path / "summary_only"
    preflight_root.mkdir()
    (preflight_root / "analysis_result.json").write_text(
        json.dumps(
            {
                "formal": False,
                "source_commit": source_commit,
                "operational_valid": True,
                "operational_errors": [],
                "branch": runner.NONFORMAL_BRANCH,
                "formal_projection_executable": True,
                "formal_projection_seconds": 1.0,
            }
        ),
        encoding="utf-8",
    )
    formal_root = tmp_path / "formal"
    with pytest.raises(ValueError, match="preflight"):
        runner.train(
            run_root=formal_root,
            source_commit=source_commit,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            preflight_root=preflight_root,
        )
    assert not formal_root.exists()


@pytest.fixture
def tiny_exercise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, object]]:
    monkeypatch.setattr(runner, "EXERCISE_FAST_UPDATES", 1)
    monkeypatch.setattr(runner, "EXERCISE_RETURN_TO_GO_UPDATES", 1)
    monkeypatch.setattr(runner, "EXERCISE_NUM_ENVS", 2)
    monkeypatch.setattr(runner, "EXERCISE_PPO_PASSES", 1)
    monkeypatch.setattr(runner, "EXERCISE_EVAL_EPISODES", 2)
    monkeypatch.setattr(runner, "EXERCISE_BOOTSTRAP_REPETITIONS", 20)
    root = tmp_path / "exercise"
    result = runner.exercise(run_root=root, source_commit="2" * 40)
    return root, result


def test_tiny_end_to_end_exercise_is_operational(tiny_exercise) -> None:
    root, result = tiny_exercise
    assert result["operational_valid"] is True
    assert result["branch"] == runner.NONFORMAL_BRANCH
    assert result["formal"] is False
    assert result["source_commit"] == "2" * 40
    assert result["formal_projection_executable"] is True
    training = json.loads((root / "train_manifest.json").read_text(encoding="utf-8"))
    evaluation = json.loads((root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    assert result["training_manifest_digest"] == runner._artifact_digest(
        root / "train_manifest.json"
    )
    assert result["evaluation_manifest_digest"] == runner._artifact_digest(
        root / "evaluation_manifest.json"
    )
    assert len(training["replicate_results"]) == 1
    assert set(training["replicate_results"][0]["arms"]) == set(source.ARMS)
    assert len(evaluation["cells"]) == 33


def test_formal_train_rejects_wrong_inventory_preflight(
    tiny_exercise, tmp_path: Path
) -> None:
    preflight_root, _ = tiny_exercise
    formal_root = tmp_path / "formal"
    with pytest.raises(ValueError, match="inventory"):
        runner.train(
            run_root=formal_root,
            source_commit="2" * 40,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            preflight_root=preflight_root,
        )
    assert not formal_root.exists()


def test_formal_artifact_validation_rechecks_serialized_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_preflight(_root: Path, *, source_commit: str) -> None:
        assert source_commit == "4" * 40
        raise ValueError("tampered preflight")

    monkeypatch.setattr(runner, "_validate_formal_preflight", reject_preflight)
    errors = runner._training_errors(
        tmp_path,
        {
            "formal": True,
            "source_commit": "4" * 40,
            "authorization_token": runner.AUTHORIZATION_TOKEN,
            "preflight_root": str((tmp_path / "preflight").resolve()),
        },
    )
    assert "formal preflight invalid" in " | ".join(errors).lower()


def test_reward_trace_tamper_fails_closed(tiny_exercise) -> None:
    root, _ = tiny_exercise
    path = root / "evaluation_manifest.json"
    evaluation = json.loads(path.read_text(encoding="utf-8"))
    evaluation["cells"][0]["episodes"][0]["reward_trace"][0] = 0.0
    path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = runner.analyze(run_root=root)
    assert result["operational_valid"] is False
    assert result["branch"] == runner.INVALID_BRANCH
    assert "trace" in " | ".join(result["operational_errors"]).lower()
