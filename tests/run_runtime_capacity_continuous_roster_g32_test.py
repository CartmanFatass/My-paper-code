from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from scripts import run_runtime_capacity_continuous_roster_g32 as runner


def _passing_metrics() -> dict[str, object]:
    return {
        "operational_valid": True,
        "padding_capacity_invariant": True,
        "capacity_8_utility_ci95": [0.91, 0.95, 0.98],
        "capacity_8_gain_ci95": [0.01, 0.1, 0.2],
        "mapping_lifecycle_gate": True,
        "capacity_6_utility_ci95": [0.91, 0.95, 0.98],
        "capacity_12_utility_ci95": [0.92, 0.95, 0.98],
        "heldout_gain_ci95": [0.01, 0.1, 0.2],
        "minimum_heldout_replicate": 0.86,
        "heldout_stochastic_mean": 0.81,
    }


def test_configuration_and_first_match_precedence_are_frozen(tmp_path: Path) -> None:
    configuration = runner._configuration(formal=True)
    assert configuration["replicates"] == 3
    assert configuration["fast_updates"] == 100
    assert configuration["return_to_go_updates"] == 100
    assert configuration["num_envs"] == 8
    assert configuration["ppo_passes"] == 2
    assert configuration["eval_episodes"] == 128
    assert configuration["bootstrap_repetitions"] == 10_000
    assert configuration["train_capacity"] == 8
    assert configuration["evaluation_capacities"] == [6, 8, 12]
    passing = _passing_metrics()
    assert runner.select_result_branch(passing) == runner.USABLE_BRANCH
    assert runner.select_result_branch(passing | {"padding_capacity_invariant": False, "capacity_8_utility_ci95": [0.0]}) == runner.NO_PADDING_BRANCH
    assert runner.select_result_branch(passing | {"capacity_8_gain_ci95": [0.0]}) == runner.NO_TRAIN_BRANCH
    assert runner.select_result_branch(passing | {"capacity_12_utility_ci95": [0.89]}) == runner.NO_CHURN_BRANCH
    assert runner.select_result_branch(passing | {"heldout_stochastic_mean": 0.79}) == runner.UNSTABLE_BRANCH
    assert runner.select_result_branch(passing | {"operational_valid": False}) == runner.INVALID_BRANCH
    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "wrong_token", source_commit="1" * 40,
            formal=True, authorization_token="wrong",
        )


@pytest.fixture(scope="module")
def exercise_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("g32_path") / "exercise"
    result = runner.exercise(run_root=root)
    assert result["status"] == "COMPLETE"
    assert result["operational_valid"] is True
    assert result["branch"] == runner.NONFORMAL_BRANCH
    return root


def test_nonformal_path_closes_and_formal_validation_rejects(exercise_root: Path) -> None:
    training = runner._read_json(exercise_root / "train_manifest.json")
    evaluation = runner._read_json(exercise_root / "evaluation_manifest.json")
    assert training["configuration"]["fast_updates"] == 1
    assert training["configuration"]["return_to_go_updates"] == 1
    assert len(evaluation["cells"]) == 10
    assert {row["member_capacity"] for row in evaluation["state_shape_diagnostics"]} == {6, 8, 12}
    assert all(row["state_before"] == row["state_after"] and row["optimizer_steps"] == 0 for row in evaluation["cells"])
    with pytest.raises(ValueError, match="requires formal G32 artifacts"):
        runner.analyze(run_root=exercise_root, require_formal=True)


def test_evaluation_state_and_cell_tamper_fail_closed(exercise_root: Path, tmp_path: Path) -> None:
    tampered = tmp_path / "tampered"
    shutil.copytree(exercise_root, tampered)
    path = tampered / "evaluation_manifest.json"
    evaluation = runner._read_json(path)
    evaluation["cells"][0]["state_after"] = "tampered"
    evaluation["cells"][1] = dict(evaluation["cells"][0])
    runner._write_json(path, evaluation)
    result = runner.analyze(run_root=tampered)
    assert result["status"] == "INVALID"
    assert result["branch"] == runner.INVALID_BRANCH
    assert any("zero-step state identity" in row or "duplicate" in row for row in result["operational_errors"])


def test_checkpoint_identity_tamper_fails_closed(exercise_root: Path, tmp_path: Path) -> None:
    import torch

    tampered = tmp_path / "checkpoint"
    shutil.copytree(exercise_root, tampered)
    training = runner._read_json(tampered / "train_manifest.json")
    checkpoint = tampered / training["replicate_results"][0]["final_checkpoint"]
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    payload["algorithm"] = "WRONG"
    torch.save(payload, checkpoint)
    result = runner.analyze(run_root=tampered)
    assert result["status"] == "INVALID"
    assert any("checkpoint algorithm mismatch" in row for row in result["operational_errors"])


def test_formal_analyzer_routes_finite_padding_mismatch_to_no_padding(
    exercise_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torch

    formal_root = tmp_path / "formal_padding_counterexample"
    shutil.copytree(exercise_root, formal_root)
    training_path = formal_root / "train_manifest.json"
    evaluation_path = formal_root / "evaluation_manifest.json"
    training = runner._read_json(training_path)
    evaluation = runner._read_json(evaluation_path)
    proof_configuration = training["configuration"]
    monkeypatch.setattr(
        runner,
        "_configuration",
        lambda *, formal: proof_configuration,
    )
    training["formal"] = True
    training["authorization_token"] = runner.AUTHORIZATION_TOKEN
    training["replicate_results"][0]["seeds"] = runner._seeds(
        0, formal=True
    )
    evaluation["formal"] = True
    evaluation["padding_diagnostics"][0][
        "maximum_value_mismatch"
    ] = 1e-6
    for kind in ("zero", "final"):
        checkpoint = (
            formal_root
            / training["replicate_results"][0][f"{kind}_checkpoint"]
        )
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        payload["formal"] = True
        torch.save(payload, checkpoint)
    runner._write_json(training_path, training)
    runner._write_json(evaluation_path, evaluation)

    result = runner.analyze(run_root=formal_root, require_formal=True)

    assert result["status"] == "COMPLETE"
    assert result["operational_valid"] is True
    assert result["operational_errors"] == []
    assert result["metrics"]["padding_capacity_invariant"] is False
    assert result["branch"] == runner.NO_PADDING_BRANCH
