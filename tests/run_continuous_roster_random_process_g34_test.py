from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts import run_continuous_roster_random_process_g34 as runner
from scripts import run_runtime_capacity_continuous_roster_g32 as g32_runner


def _passing_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "source_structural_valid": True,
        "fixed_control_confident_fail": False,
        "fixed_control_pass": True,
        "random_confident_fail": False,
        "random_pass": True,
    }


def test_first_match_precedence_is_exact() -> None:
    passing = _passing_metrics()
    assert runner.select_result_branch(passing) == runner.SUPPORTED_BRANCH
    assert runner.select_result_branch(passing | {"operational_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_result_branch(passing | {"source_structural_valid": False}) == runner.SOURCE_INVALID_BRANCH
    assert runner.select_result_branch(passing | {"fixed_control_confident_fail": True}) == runner.SOURCE_INVALID_BRANCH
    assert runner.select_result_branch(passing | {"random_confident_fail": True, "random_pass": False}) == runner.DEPENDENCE_BRANCH
    assert runner.select_result_branch(passing | {"random_pass": False}) == runner.UNDERPOWERED_BRANCH


@pytest.fixture
def exercise_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    checkpoint_root = tmp_path / "g32"
    run_root = tmp_path / "g34"
    fake_training = {"replicate_results": [{} for _ in range(3)]}
    monkeypatch.setattr(
        runner,
        "_validate_checkpoint_source",
        lambda path: (fake_training, g32_runner._configuration(formal=True)),
    )

    def fake_load(
        checkpoint_root: Path,
        training: object,
        configuration: object,
        *,
        replicate: int,
        kind: str,
        capacity: int,
    ):
        g32_runner.configure_runtime(10345000 + replicate + (0 if kind == "zero" else 100))
        return g32_runner.make_model(capacity)

    monkeypatch.setattr(runner, "_load_model", fake_load)
    result = runner.exercise(
        run_root=run_root,
        checkpoint_root=checkpoint_root,
        source_commit="1" * 40,
    )
    assert result["branch"] == runner.NONFORMAL_BRANCH
    assert result["operational_valid"] is True
    assert result["metrics"]["constructive_source_valid"] is True
    evaluation = json.loads((run_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    assert len(evaluation["cells"]) == 20
    assert {row["capacity"] for row in evaluation["cells"]} == {6, 8, 12}
    assert sum(row["cell"] == runner.FINAL_RANDOM_TIME_ROTATED for row in evaluation["cells"]) == 1
    assert sum(row["cell"] == runner.FINAL_RANDOM_REACTIVE_ABLATION for row in evaluation["cells"]) == 1
    return run_root, checkpoint_root


def test_nonformal_artifact_tamper_fails_operationally(
    exercise_result: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root, checkpoint_root = exercise_result
    monkeypatch.setattr(
        runner,
        "_validate_checkpoint_source",
        lambda path: ({"replicate_results": [{} for _ in range(3)]}, g32_runner._configuration(formal=True)),
    )
    path = run_root / "evaluation_manifest.json"
    evaluation = json.loads(path.read_text(encoding="utf-8"))
    model_cell = next(row for row in evaluation["cells"] if row["cell"] != runner.CONSTRUCTIVE_RANDOM)
    model_cell["state_after"] = "tampered"
    path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = runner.analyze(run_root=run_root, checkpoint_root=checkpoint_root)
    assert result["branch"] == runner.INVALID_BRANCH
    assert any("checkpoint state drift" in row for row in result["operational_errors"])


def test_cell_route_and_event_evidence_tamper_fail_closed(
    exercise_result: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root, checkpoint_root = exercise_result
    monkeypatch.setattr(
        runner,
        "_validate_checkpoint_source",
        lambda path: (
            {"replicate_results": [{} for _ in range(3)]},
            g32_runner._configuration(formal=True),
        ),
    )
    path = run_root / "evaluation_manifest.json"
    evaluation = json.loads(path.read_text(encoding="utf-8"))
    fixed = next(row for row in evaluation["cells"] if row["cell"] == runner.FINAL_FIXED_DET)
    fixed["process"] = "random"
    path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = runner.analyze(run_root=run_root, checkpoint_root=checkpoint_root)
    assert result["branch"] == runner.INVALID_BRANCH
    assert any("cell route mismatch" in row for row in result["operational_errors"])

    fixed["process"] = "fixed"
    fixed["episodes"][0]["event_window_utility"].pop("R")
    path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = runner.analyze(run_root=run_root, checkpoint_root=checkpoint_root)
    assert result["branch"] == runner.INVALID_BRANCH
    assert any(
        "episode support or pairing mismatch" in row
        for row in result["operational_errors"]
    )


def test_event_type_arrays_preserve_episode_pairing(
    exercise_result: tuple[Path, Path]
) -> None:
    run_root, _ = exercise_result
    evaluation = json.loads((run_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    values = runner._event_metric_arrays(
        evaluation, runner.FINAL_RANDOM_DET, "L"
    )
    assert set(values) == {6, 8, 12}
    assert all(array.shape == (1, 4) for array in values.values())


def test_exact_g32_checkpoint_source_and_formal_authority_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkpoint_root = tmp_path / "g32"
    checkpoint_root.mkdir()
    training = {"formal": True, "source_commit": "0" * 40}
    evaluation: dict[str, object] = {}
    result = {
        "operational_valid": True,
        "branch": g32_runner.USABLE_BRANCH,
    }
    (checkpoint_root / "train_manifest.json").write_text(
        json.dumps(training), encoding="utf-8"
    )
    (checkpoint_root / "evaluation_manifest.json").write_text(
        json.dumps(evaluation), encoding="utf-8"
    )
    (checkpoint_root / "analysis_result.json").write_text(
        json.dumps(result), encoding="utf-8"
    )
    monkeypatch.setattr(g32_runner, "_artifact_errors", lambda *args: [])
    with pytest.raises(ValueError, match="exact usable formal G32"):
        runner._validate_checkpoint_source(checkpoint_root)
    with pytest.raises(ValueError, match="authorization token"):
        runner.evaluate(
            run_root=tmp_path / "formal",
            checkpoint_root=checkpoint_root,
            source_commit="1" * 40,
            formal=True,
            authorization_token=None,
        )


def test_hierarchical_difference_keeps_whole_episode_pairing() -> None:
    rng = np.random.default_rng(123)
    left = {
        capacity: rng.uniform(0.2, 0.9, size=(3, 128))
        for capacity in runner.source.CAPACITIES
    }
    right = {capacity: values - 0.125 for capacity, values in left.items()}
    plan = runner._bootstrap_plan(replicates=3, episodes=128, repetitions=128)
    interval = runner._hierarchical_ci(
        runner._difference(left, right),
        selected_capacities=runner.source.CAPACITIES,
        plan=plan,
    )
    np.testing.assert_allclose(interval, [0.125, 0.125, 0.125], atol=1e-12)


def test_formal_validation_rejects_nonformal_exercise(
    exercise_result: tuple[Path, Path]
) -> None:
    run_root, checkpoint_root = exercise_result
    with pytest.raises(ValueError, match="requires formal"):
        runner.analyze(
            run_root=run_root,
            checkpoint_root=checkpoint_root,
            require_formal=True,
        )


def test_configuration_freezes_exact_cell_and_complexity_inventory() -> None:
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["episodes_per_capacity_replicate"] == 128
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["cells_per_replicate"] == 20
    assert formal["total_cells"] == 60
    assert formal["real_transitions_per_episode"] == 48
    assert formal["total_real_episode_transitions"] == 368_640
    assert formal["episode_exclusions"] == "none"
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_trajectory_count"] == 0
    assert formal["hypothetical_transitions"] == 0
    assert formal["nested_rollout"] is False
    assert formal["replanning"] is False
