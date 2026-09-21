import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.native_joint_b09 import study
from scripts import run_skill_drift_native_joint_b09 as runner
from tools.research_support.interpreters import control_plane_interpreter


@pytest.fixture(scope="module")
def tiny_evidence():
    # The sole real-host fixture: one tiny fit and one nominal eight-branch panel.
    exposure = {key: 0 for key in study.EXPOSURE_KEYS}
    result = study.run_block(study.TINY_CONFIG, seed=95991, exposure=exposure)
    nominal = study.nominal_response_table()
    return {"result": result, "exposure": exposure, "nominal": nominal}


def test_joint_learner_prior_versions_and_exact_projection():
    learner = study.JointLawLearner()
    np.testing.assert_array_equal(learner.predict(0), np.full(4, 0.25))
    np.testing.assert_array_equal(learner.predict(1), np.full(4, 0.25))
    learner.observe(0, 1)
    np.testing.assert_allclose(learner.predict(0), [1 / 6, 3 / 6, 1 / 6, 1 / 6])
    np.testing.assert_array_equal(learner.predict(1), np.full(4, 0.25))
    projected = study.marginal_product(np.array([0.4, 0.1, 0.2, 0.3]))
    np.testing.assert_allclose(projected, [0.3, 0.2, 0.3, 0.2])
    assert study.joint_contrast(study.SOURCE_Q) == pytest.approx(-0.7)
    assert study.joint_contrast(study.TARGET_Q) == pytest.approx(0.2)
    assert study.joint_contrast(study.marginal_product(study.TARGET_Q)) == pytest.approx(-0.25)


def test_tiny_cost_and_complete_raw_evidence(tiny_evidence):
    result = tiny_evidence["result"]
    assert result["summary"]["counts"] == {
        "training_team_steps": 4,
        "observed_joint_labels": 4,
        "preupdate_probability_queries": 4,
        "initial_probability_export_queries": 2,
        "snapshot_probability_export_queries": 4,
        "final_probability_export_queries": 2,
        "state_export_probability_queries": 8,
        "total_learner_probability_queries": 12,
        "training_marginal_projection_constructions": 4,
        "evaluation_frozen_projection_constructions": 2,
        "summary_projection_diagnostics": 3,
        "joint_log_loss_terms": 4,
        "projected_log_loss_terms": 4,
        "count_updates": 4,
        "evaluation_episodes": 4,
        "evaluation_team_steps": 8,
        "planner_native_step_calls": 64,
        "evaluation_response_tables": 8,
        "evaluation_joint_q_vectors": 8,
        "evaluation_projected_q_vectors": 8,
        "evaluation_joint_choices": 8,
        "evaluation_projected_choices": 8,
        "evaluation_true_q_vectors_after_choice": 8,
        "evaluation_true_chosen_values_after_choice": 8,
        "evaluation_true_regrets_after_choice": 8,
        "evaluation_count_updates": 0,
        "real_team_ticks": 12,
        "native_step_calls": 76,
        "native_constructors": 6,
        "implicit_constructor_resets": 6,
        "logical_episode_initializations": 6,
        "custom_geometry_channel_refreshes": 6,
        "deep_copies": 64,
        "gradient_calls": 0,
        "actor_value_network_forwards": 0,
        "external_innovation_draws": 12,
        "focal_uniform_collection_draws": 4,
    }
    assert tiny_evidence["exposure"] == {
        "native_constructors": 6,
        "implicit_constructor_resets": 6,
        "logical_episode_initializations": 6,
        "custom_geometry_channel_refreshes": 6,
        "deep_copies": 64,
        "training_native_step_calls": 4,
        "evaluation_native_step_calls": 8,
        "planner_native_step_calls": 64,
    }
    assert result["training"]["pre_positions"].shape == (4, 3, 3)
    assert result["training"]["pre_observations"].shape[0:2] == (4, 3)
    assert result["training"]["pre_connections"].shape == (4, 3, 1)
    assert result["training"]["pre_sinr"].shape == (4, 3, 1)
    assert result["evaluation"]["response_adapter_reward"].shape == (8, 2, 4)
    assert result["evaluation"]["response_after_positions"].shape == (8, 2, 4, 3, 3)
    assert result["evaluation"]["response_after_sinr"].shape == (8, 2, 4, 3, 1)
    assert all(value.dtype != object for value in result["training"].values())
    assert all(value.dtype != object for value in result["evaluation"].values())
    assert all(value.dtype != object for value in result["state"].values())
    json.dumps(result["summary"], allow_nan=False)


def test_training_is_preupdate_command_derived_and_version_separated(tiny_evidence):
    training = tiny_evidence["result"]["training"]
    expected_counts = np.zeros((2, 4), dtype=np.int64)
    for index in range(4):
        version = int(training["version"][index])
        np.testing.assert_array_equal(training["counts_before"][index], expected_counts)
        expected_probability = (expected_counts[version] + 0.5) / (
            expected_counts[version].sum() + 2.0
        )
        np.testing.assert_allclose(
            training["probabilities_before"][index], expected_probability
        )
        decoded_bits, decoded_row = study.decode_teammate_row(
            training["pre_positions"][index], training["issued_actions"][index]
        )
        np.testing.assert_array_equal(decoded_bits, training["teammate_bits"][index])
        assert decoded_row == training["joint_row"][index]
        expected_counts[version, decoded_row] += 1
        np.testing.assert_array_equal(training["counts_after"][index], expected_counts)
        assert training["joint_log_loss"][index] == pytest.approx(
            -np.log(expected_probability[decoded_row])
        )
    np.testing.assert_array_equal(training["probabilities_before"][2], np.full(4, 0.25))
    assert training["terminated"].tolist() == [False, True, False, True]
    assert training["terminal_id"].tolist() == [-1, 0, -1, 1]


def test_snapshots_projection_pairing_and_clone_isolation(tiny_evidence):
    result = tiny_evidence["result"]
    state = result["state"]
    np.testing.assert_array_equal(state["snapshot_target_observations"], [1, 2])
    np.testing.assert_array_equal(
        state["snapshot_counts"][:, 0],
        np.repeat(state["final_counts"][None, 0], 2, axis=0),
    )
    assert state["snapshot_counts"][0, 1].sum() == 1
    assert state["snapshot_counts"][1, 1].sum() == 2
    evaluation = result["evaluation"]
    assert evaluation["response_source_state_unchanged"].all()
    for index in range(len(evaluation["view"])):
        joint = evaluation["joint_probabilities"][index]
        projected = evaluation["projected_probabilities"][index]
        np.testing.assert_allclose(projected, study.marginal_product(joint))
        np.testing.assert_allclose(
            [joint[2] + joint[3], joint[1] + joint[3]],
            [projected[2] + projected[3], projected[1] + projected[3]],
        )
        np.testing.assert_allclose(
            evaluation["response_team_reward"][index],
            3.0 * evaluation["response_adapter_reward"][index],
        )
        snapshot_index = 0 if evaluation["snapshot_step"][index] == 1 else 1
        np.testing.assert_array_equal(
            evaluation["frozen_counts"][index], state["snapshot_counts"][snapshot_index]
        )
    addresses = {}
    for index, address in enumerate(evaluation["rng_address"]):
        key = (int(evaluation["episode"][index]), int(evaluation["tick"][index]))
        addresses.setdefault(key, []).append(
            (tuple(address.tolist()), float(evaluation["external_uniform"][index]))
        )
    for paired in addresses.values():
        assert len(paired) == 4
        assert len({address for address, _ in paired}) == 1
        assert len({slot for _, slot in paired}) == 1
    initial_rows = evaluation["tick"] == 0
    np.testing.assert_array_equal(
        evaluation["pre_positions"][initial_rows],
        np.repeat(evaluation["pre_positions"][initial_rows][0:1], 4, axis=0),
    )


def test_primary_reduction_and_team_scaling(tiny_evidence):
    result = tiny_evidence["result"]
    summary = result["summary"]
    evaluation = result["evaluation"]
    for snapshot, snapshot_value in (("1", 1), ("2", 2)):
        reduced = summary["reductions"]["by_snapshot"][snapshot]
        raw_returns = []
        for view in (0, 1):
            rows = (evaluation["snapshot_step"] == snapshot_value) & (
                evaluation["view"] == view
            )
            raw_returns.append(float(evaluation["adapter_reward"][rows].sum()))
        np.testing.assert_allclose(
            reduced["J_emp_cumulative_adapter_rewards"], [raw_returns[0]]
        )
        np.testing.assert_allclose(
            reduced["M_proj_cumulative_adapter_rewards"], [raw_returns[1]]
        )
        expected = np.array([raw_returns[0] - raw_returns[1]])
        np.testing.assert_allclose(reduced["paired_J_minus_M_adapter_returns"], expected)
        assert reduced["mean_J_minus_M_adapter_return"] == pytest.approx(expected.mean())
        np.testing.assert_allclose(
            reduced["paired_J_minus_M_team_returns"], 3.0 * expected
        )
    assert summary["reductions"]["by_snapshot"]["1"]["role"] == "descriptive"
    assert summary["reductions"]["by_snapshot"]["2"]["role"] == "primary"
    assert summary["no_standard_hmasd_claim"]


def test_selected_planner_branch_matches_real_native_transition(tiny_evidence):
    evaluation = tiny_evidence["result"]["evaluation"]
    for index in range(len(evaluation["tick"])):
        focal = int(evaluation["focal_bit"][index])
        row = int(evaluation["joint_row"][index])
        decoded_bits, decoded_row = study.decode_teammate_row(
            evaluation["pre_positions"][index], evaluation["issued_actions"][index]
        )
        np.testing.assert_array_equal(decoded_bits, evaluation["teammate_bits"][index])
        assert decoded_row == row
        assert evaluation["adapter_reward"][index] == evaluation[
            "response_adapter_reward"
        ][index, focal, row]
        assert evaluation["team_reward"][index] == evaluation[
            "response_team_reward"
        ][index, focal, row]
        for actual, planned in (
            ("issued_actions", "response_issued_actions"),
            ("after_positions", "response_after_positions"),
            ("after_observations", "response_after_observations"),
            ("after_connections", "response_after_connections"),
            ("after_sinr", "response_after_sinr"),
            ("reward_components", "response_reward_components"),
            ("terminated", "response_terminated"),
            ("truncated", "response_truncated"),
            ("terminal_agents", "response_terminal_agents"),
            ("truncated_agents", "response_truncated_agents"),
        ):
            np.testing.assert_array_equal(
                evaluation[actual][index], evaluation[planned][index, focal, row]
            )
    for snapshot in (1, 2):
        for view in (0, 1):
            rows = (evaluation["snapshot_step"] == snapshot) & (
                evaluation["view"] == view
            )
            assert evaluation["terminated"][rows].tolist() == [False, True]
            assert evaluation["terminal_id"][rows].tolist() == [-1, 0]


def test_nominal_eight_branches_match_declared_physics_and_clone_consistency(tiny_evidence):
    nominal = tiny_evidence["nominal"]
    assert nominal["source_state_unchanged"].item()
    scalar = nominal["adapter_reward"]
    for focal in (0, 1):
        for row in range(4):
            near = focal + row // 2 + row % 2
            expected = 0.238774637 if near == 1 else 0.0
            assert scalar[focal, row] == pytest.approx(expected, abs=2e-7)
            assert nominal["team_reward"][focal, row] == pytest.approx(
                3.0 * scalar[focal, row], abs=1e-12
            )
            positions = nominal["after_positions"][focal, row]
            radii = np.linalg.norm(positions[:, :2] - study.USER_POSITION, axis=1)
            bits = np.array([focal, row // 2, row % 2])
            np.testing.assert_allclose(radii, np.where(bits == 1, 50.0, 110.0), atol=1e-12)


def test_runner_bindings_digests_accounting_and_literal_guard(monkeypatch, tmp_path):
    assert runner.SEEDS == (95401, 95402, 95403)
    assert runner.PLAN_SOURCE == "ee2d70c69abc0c5a45881da6e74937a7ac166689"
    assert runner.OUTPUT_SUFFIX.as_posix() == "runs/skill_teammate_drift_learning/b09_native_joint"
    manifest = runner.source_manifest()
    assert runner.validate_source_manifest(manifest)
    tampered = copy.deepcopy(manifest)
    tampered["files"]["study"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        runner.validate_source_manifest(tampered)
    roundtrip = tmp_path / "tuple-config.json"
    runner.write_json(roundtrip, {"config": asdict(study.Config())})
    assert json.loads(roundtrip.read_text())["config"]["snapshot_steps"] == [16, 64]

    out = tmp_path / runner.OUTPUT_SUFFIX
    out.mkdir(parents=True)
    for name in ("admission-preflight.json", "launch-manifest.json", "launch-status.json", "stdout.log"):
        (out / name).write_text("native bookkeeping")
    assert runner.prepare_output_directory(out) == out.resolve()
    (out / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError, match="existing B09 scientific output"):
        runner.prepare_output_directory(out)
    (out / "source-manifest.json").write_text("{}")
    seed_dir = out / "seed_95401"
    seed_dir.mkdir()
    (seed_dir / "summary.json").write_text("{}")
    assert set(runner.stable_science_digests(out)) == {
        "summary.json",
        "source-manifest.json",
        "seed_95401/summary.json",
    }

    metadata = {"fit_attempts": [], "started_fits": 0, "completed_fits": 0}
    attempt = runner.begin_fit(metadata, 95401)
    assert metadata["started_fits"] == 1 and metadata["completed_fits"] == 0
    attempt["partial_exposure"]["native_constructors"] = 1
    assert attempt["status"] == "RUNNING" and "saved" not in attempt
    complete_attempts = [
        {
            "status": "COMPLETE",
            "exposure_complete": True,
            "partial_exposure": {"native_constructors": value, "deep_copies": 8 * value},
        }
        for value in (1, 2, 3)
    ]
    assert runner.aggregate_completed_exposure(complete_attempts) == {
        "deep_copies": 48,
        "native_constructors": 6,
    }

    script = Path(runner.__file__)
    help_result = subprocess.run(
        [sys.executable, "-B", str(script), "--help"],
        cwd=runner.ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert help_result.returncode == 0, help_result.stderr
    guard_program = (
        "from pathlib import Path; import sys; "
        "from scripts.hmasd_launch import _validate_guard_contract; "
        "_validate_guard_contract(Path(sys.argv[1]), 'skill_teammate_drift_learning')"
    )
    guard = subprocess.run(
        [control_plane_interpreter(), "-B", "-c", guard_program, str(script)],
        cwd=runner.ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert guard.returncode == 0, guard.stderr

    stage_calls = []
    admission_calls = []
    monkeypatch.setattr(runner, "run_stage", lambda *args: stage_calls.append(True))
    monkeypatch.setattr(
        runner,
        "require_admission",
        lambda *args, **kwargs: admission_calls.append(True) or {"sha": "b" * 40},
    )
    valid_out = tmp_path / "admitted" / runner.OUTPUT_SUFFIX
    base = ["--launch-sha", "a" * 40, "--out", str(valid_out)]
    with pytest.raises(SystemExit):
        runner.main(["--seeds", "1", *base])
    with pytest.raises(SystemExit):
        runner.main(["--seeds", *map(str, runner.SEEDS), "--launch-sha", "a" * 40, "--out", str(tmp_path / "wrong")])
    assert not admission_calls and not stage_calls
    with pytest.raises(SystemExit):
        runner.main(["--seeds", *map(str, runner.SEEDS), *base])
    assert len(admission_calls) == 1 and not stage_calls
