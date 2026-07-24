from __future__ import annotations

from pathlib import Path
import shutil

import pytest
import torch

from scripts import run_direction_balanced_full_actor_g30 as runner


@pytest.fixture(scope="module")
def exercise_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("g30_formal_path") / "exercise"
    runner.train(
        run_root=root,
        source_commit="0" * 40,
        formal=False,
        authorization_token=None,
    )
    runner.evaluate(run_root=root)
    result = runner.analyze(run_root=root)
    assert result["status"] == "COMPLETE"
    assert result["operational_valid"] is True
    assert result["branch"] == runner.NONFORMAL_BRANCH
    return root


def _passing_metrics() -> dict[str, object]:
    return {
        "operational_valid": True,
        "g17_iid_utility_ci95": [0.91, 0.95, 0.97],
        "g17_heldout_utility_ci95": [0.92, 0.95, 0.97],
        "g17_gain_ci95": [0.11, 0.20, 0.30],
        "g17_minimum_episode": 0.81,
        "g17_minimum_effort_correlation": 0.91,
        "g17_minimum_mix_correlation": 0.92,
        "g17_maximum_effort_mae": 0.04,
        "g17_maximum_mix_mae": 0.03,
        "g18_utility_ci95": [0.96, 0.98, 0.99],
        "g18_gain_ci95": [0.11, 0.20, 0.30],
        "g18_spike_utility_ci95": [0.91, 0.95, 0.98],
        "g18_rotating_effort_share_ci95": [0.76, 0.90, 0.96],
        "g18_minimum_replicate_utility": 0.91,
    }


def test_formal_configuration_token_seeds_and_precedence_are_frozen(
    tmp_path: Path,
) -> None:
    configuration = runner._configuration(formal=True)
    assert configuration["replicates"] == 3
    assert configuration["g17_fast_updates"] == 100
    assert configuration["g17_direction_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_direction_updates"] == 300
    assert configuration["eval_episodes"] == 128
    assert configuration["bootstrap_repetitions"] == 10_000
    assert runner._seeds("g17", 2, formal=True)["model"] == 7_119_002
    assert runner._seeds("g18", 2, formal=True)["action"] == 7_239_002

    passing = _passing_metrics()
    assert runner.select_result_branch(passing) == runner.USABLE_BRANCH
    assert runner.select_result_branch(
        passing | {"g17_minimum_episode": 0.79}
    ) == runner.NO_G17_BRANCH
    assert runner.select_result_branch(
        passing | {"g18_gain_ci95": [0.09, 0.2, 0.3]}
    ) == runner.NO_G18_ACCESS_BRANCH
    assert runner.select_result_branch(
        passing | {"g18_rotating_effort_share_ci95": [0.74, 0.9, 0.96]}
    ) == runner.NO_G18_MECHANISM_BRANCH
    assert runner.select_result_branch(
        passing | {"g18_minimum_replicate_utility": 0.89}
    ) == runner.UNSTABLE_BRANCH
    assert runner.select_result_branch(
        passing | {"operational_valid": False}
    ) == runner.INVALID_BRANCH

    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "wrong_token",
            source_commit="1" * 40,
            formal=True,
            authorization_token="wrong",
        )


def test_nonformal_exercise_closes_and_formal_analyzer_rejects(
    exercise_root: Path,
) -> None:
    training = runner._read_json(exercise_root / "train_manifest.json")
    evaluation = runner._read_json(exercise_root / "evaluation_manifest.json")
    analysis = runner._read_json(exercise_root / "analysis_result.json")
    assert training["formal"] is False
    assert len(training["source_results"]) == 2
    assert len(evaluation["cells"]) == 7
    assert analysis["branch"] == runner.NONFORMAL_BRANCH
    assert all(
        row["minimum_actor_optimizer_step_increment"] == 1.0
        for row in training["source_results"]
    )
    with pytest.raises(ValueError, match="requires formal G30 artifacts"):
        runner.analyze(run_root=exercise_root, require_formal=True)


def test_checkpoint_identity_tamper_fails_closed(
    exercise_root: Path, tmp_path: Path
) -> None:
    tampered = tmp_path / "checkpoint_tamper"
    shutil.copytree(exercise_root, tampered)
    manifest = runner._read_json(tampered / "train_manifest.json")
    checkpoint = tampered / manifest["source_results"][0]["final_checkpoint"]
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    payload["algorithm"] = "WRONG"
    torch.save(payload, checkpoint)

    result = runner.analyze(run_root=tampered)

    assert result["status"] == "INVALID"
    assert result["branch"] == runner.INVALID_BRANCH
    assert any(
        "checkpoint algorithm mismatch" in error
        for error in result["operational_errors"]
    )


def test_duplicate_evaluation_cell_fails_closed(
    exercise_root: Path, tmp_path: Path
) -> None:
    tampered = tmp_path / "cell_tamper"
    shutil.copytree(exercise_root, tampered)
    evaluation_path = tampered / "evaluation_manifest.json"
    evaluation = runner._read_json(evaluation_path)
    evaluation["cells"][1] = dict(evaluation["cells"][0])
    runner._write_json(evaluation_path, evaluation)

    result = runner.analyze(run_root=tampered)

    assert result["status"] == "INVALID"
    assert result["branch"] == runner.INVALID_BRANCH
    assert any(
        "cell duplicate or misdirected" in error
        for error in result["operational_errors"]
    )
