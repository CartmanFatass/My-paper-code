import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.law_table_b11 import study
from experiments.candidates.skill_teammate_drift_learning.native_joint_b09 import (
    study as b09,
)
from scripts import run_skill_drift_law_table_b11 as runner
from tools.research_support.interpreters import control_plane_interpreter


@pytest.fixture(scope="module")
def tiny_evaluation():
    # The sole native B11 fixture: zero fits, 8 actual plus 64 planning calls.
    frozen = study.load_frozen_state(
        runner.INPUT_ROOT,
        95401,
        expected_root_artifacts_sha256=runner.ROOT_ARTIFACTS_SHA256,
    )
    before = {key: value.copy() for key, value in frozen["state"].items()}
    exposure = {key: 0 for key in study.EXPOSURE_KEYS}
    result = study.run_evaluation(
        study.TINY_CONFIG,
        95993,
        frozen,
        exposure=exposure,
    )
    return {"frozen": frozen, "before": before, "result": result, "exposure": exposure}


def test_loader_reads_both_whole_tables_and_rejects_tamper(tmp_path):
    loaded = {
        seed: study.load_frozen_state(
            runner.INPUT_ROOT,
            seed,
            expected_root_artifacts_sha256=runner.ROOT_ARTIFACTS_SHA256,
        )
        for seed in runner.SEEDS
    }
    for seed, item in loaded.items():
        assert item["seed"] == seed
        assert not any(array.flags.writeable for array in item["state"].values())
        probabilities = item["state"]["final_probabilities"]
        assert probabilities.shape == (2, 4)
        assert not np.array_equal(probabilities[0], probabilities[1])
        np.testing.assert_array_equal(item["target_probabilities"], probabilities[1])
        np.testing.assert_array_equal(
            item["projected_probabilities"], b09.marginal_product(probabilities[1])
        )
    with pytest.raises(ValueError, match="root artifact-manifest digest"):
        study.load_frozen_state(
            runner.INPUT_ROOT,
            95401,
            expected_root_artifacts_sha256="0" * 64,
        )

    copied = tmp_path / "b09"
    (copied / "seed_95401").mkdir(parents=True)
    for relative in (
        "artifacts.json",
        "summary.json",
        "source-manifest.json",
        "seed_95401/artifacts.json",
        "seed_95401/summary.json",
        "seed_95401/state.npz",
    ):
        shutil.copy2(runner.INPUT_ROOT / relative, copied / relative)
    with (copied / "seed_95401/state.npz").open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(ValueError, match="per-seed artifact digest"):
        study.load_frozen_state(
            copied,
            95401,
            expected_root_artifacts_sha256=runner.ROOT_ARTIFACTS_SHA256,
        )


def test_tiny_zero_fit_counts_frozen_arrays_and_cost(tiny_evaluation):
    result = tiny_evaluation["result"]
    counts = result["summary"]["counts"]
    assert counts == {
        "new_fits": 0,
        "training_observations": 0,
        "count_updates": 0,
        "gradient_calls": 0,
        "actor_value_network_forwards": 0,
        "learner_probability_queries": 0,
        "loaded_fixed_states": 1,
        "loaded_source_probability_views": 1,
        "loaded_target_probability_views": 1,
        "loader_unused_marginal_product_views": 1,
        "evaluation_episodes": 4,
        "evaluation_team_steps": 8,
        "response_tables": 8,
        "source_table_q_vectors": 8,
        "target_table_q_vectors": 8,
        "source_table_candidate_choices": 8,
        "target_table_candidate_choices": 8,
        "actual_focal_policy_choices": 8,
        "true_law_q_vectors_after_choices": 8,
        "candidate_true_chosen_values_after_choice": 16,
        "candidate_true_regrets_after_choice": 16,
        "actual_true_chosen_values_after_choice": 8,
        "actual_true_regrets_after_choice": 8,
        "external_innovation_draw_calls": 8,
        "unique_external_innovation_addresses": 2,
        "native_constructors": 4,
        "implicit_constructor_resets": 4,
        "logical_episode_initializations": 4,
        "custom_geometry_channel_refreshes": 4,
        "actual_native_step_calls": 8,
        "planning_native_step_calls": 64,
        "deep_copies": 64,
        "total_native_step_calls": 72,
    }
    assert tiny_evaluation["exposure"] == {
        "native_constructors": 4,
        "implicit_constructor_resets": 4,
        "logical_episode_initializations": 4,
        "custom_geometry_channel_refreshes": 4,
        "deep_copies": 64,
        "training_native_step_calls": 0,
        "evaluation_native_step_calls": 8,
        "planner_native_step_calls": 64,
    }
    assert result["trajectory"]["law_id"].shape == (8,)
    assert result["planning"]["law_id"].shape == (8,)
    assert all(array.dtype != object for array in result["trajectory"].values())
    assert all(array.dtype != object for array in result["planning"].values())
    for key, before in tiny_evaluation["before"].items():
        np.testing.assert_array_equal(tiny_evaluation["frozen"]["state"][key], before)
        np.testing.assert_array_equal(result["frozen_state"][key], before)
    assert result["summary"]["rng_master_seed"] == 95993
    assert result["summary"]["frozen_base_seed"] == 95401
    assert result["summary"]["historical_input_cost"]["fits"] == 1
    assert result["summary"]["pairing_checks"] == {
        "common_initial_geometries": 1,
        "common_uniform_slots": 2,
        "within_law_paired_teammate_ticks": 4,
        "first_state_table_choice_cross_law_equalities": 2,
    }
    json.dumps(result["summary"], allow_nan=False)
    for contrast in result["summary"]["reduction"]["contrasts"].values():
        assert contrast["paired_world_sample_standard_deviation"] is None


def test_four_cell_pairing_mapping_decoupling_and_branch_identity(tiny_evaluation):
    result = tiny_evaluation["result"]
    trajectory = result["trajectory"]
    planning = result["planning"]

    for tick in (0, 1):
        rows = trajectory["tick"] == tick
        assert int(rows.sum()) == 4
        assert np.unique(trajectory["rng_address"][rows], axis=0).shape == (1, 5)
        assert np.unique(trajectory["external_uniform"][rows]).size == 1
        for law_id in (0, 1):
            law_rows = rows & (trajectory["law_id"] == law_id)
            assert np.unique(trajectory["joint_row"][law_rows]).size == 1
            uniform = float(trajectory["external_uniform"][law_rows][0])
            expected_row = b09._sample_row(b09.TRUE_Q[law_id], uniform)
            assert np.all(trajectory["joint_row"][law_rows] == expected_row)
            np.testing.assert_array_equal(
                trajectory["teammate_bits"][law_rows][0],
                [expected_row // 2, expected_row % 2],
            )

    # Known uniforms demonstrate that the same slot can map differently by law.
    assert b09._sample_row(b09.SOURCE_Q, 0.2) == 1
    assert b09._sample_row(b09.TARGET_Q, 0.2) == 0
    assert b09._sample_row(b09.SOURCE_Q, 0.8) == 2
    assert b09._sample_row(b09.TARGET_Q, 0.8) == 3

    initial = trajectory["tick"] == 0
    np.testing.assert_array_equal(
        trajectory["pre_positions"][initial],
        np.repeat(trajectory["pre_positions"][initial][0:1], 4, axis=0),
    )
    assert np.all(trajectory["rng_address"][:, 1:3] == [3, 3])

    first_planning = planning["tick"] == 0
    for table_id in (0, 1):
        rows = first_planning & (planning["actual_table_id"] == table_id)
        assert int(rows.sum()) == 2
        np.testing.assert_array_equal(
            planning["candidate_choices"][rows][0],
            planning["candidate_choices"][rows][1],
        )
        assert np.unique(planning["selected_focal_bit"][rows]).size == 1

    # Within a law, changing the focal table leaves teammate paths paired.
    for law_id in (0, 1):
        for tick in (0, 1):
            rows = (trajectory["law_id"] == law_id) & (trajectory["tick"] == tick)
            assert int(rows.sum()) == 2
            np.testing.assert_array_equal(
                trajectory["after_positions"][rows][0, 1:],
                trajectory["after_positions"][rows][1, 1:],
            )

    probabilities = tiny_evaluation["frozen"]["state"]["final_probabilities"]
    for planner_index, trajectory_index in enumerate(planning["trajectory_index"]):
        trajectory_index = int(trajectory_index)
        law_id = int(planning["law_id"][planner_index])
        table_id = int(planning["actual_table_id"][planner_index])
        focal = int(trajectory["focal_bit"][trajectory_index])
        row = int(trajectory["joint_row"][trajectory_index])
        rewards = planning["response_adapter_reward"][planner_index]
        expected_values = np.stack((rewards @ probabilities[0], rewards @ probabilities[1]))
        expected_choices = np.asarray(
            [int(values[1] > values[0]) for values in expected_values], dtype=np.int8
        )
        expected_true = rewards @ b09.TRUE_Q[law_id]
        expected_regrets = np.max(expected_true) - expected_true[expected_choices]
        np.testing.assert_allclose(planning["candidate_values"][planner_index], expected_values)
        np.testing.assert_array_equal(planning["candidate_choices"][planner_index], expected_choices)
        np.testing.assert_allclose(
            planning["true_law_values_after_choices"][planner_index], expected_true
        )
        np.testing.assert_allclose(
            planning["candidate_true_regrets_after_choice"][planner_index],
            expected_regrets,
        )
        assert focal == int(expected_choices[table_id])
        assert int(trajectory["planner_record_index"][trajectory_index]) == planner_index
        assert trajectory["adapter_reward"][trajectory_index] == rewards[focal, row]
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
                trajectory[actual][trajectory_index],
                planning[planned][planner_index, focal, row],
            )

    np.testing.assert_allclose(
        trajectory["team_reward"], 3.0 * trajectory["adapter_reward"], atol=1e-12
    )
    assert trajectory["terminated"].tolist() == [False, True] * 4
    assert trajectory["terminal_id"].tolist() == [-1, 0] * 4
    for diagnostic in result["summary"]["occupancy_regret_diagnostics"].values():
        assert diagnostic["states"] == 2
        assert (
            diagnostic["matched_better_count"]
            + diagnostic["matched_equal_count"]
            + diagnostic["matched_worse_count"]
            == 2
        )


def _synthetic_block(seed, offset):
    config = study.Config(episodes=16, steps=1)
    episode = np.arange(16, dtype=np.float64)
    values = {
        "source_law_source_table": 10.0 + offset + 0.5 * episode,
        "source_law_target_table": 8.0 - offset + 0.1 * episode,
        "target_law_source_table": 7.0 + 0.2 * episode,
        "target_law_target_table": 6.0 + offset + 0.7 * episode,
    }
    records = {"law_id": [], "table_id": [], "episode": [], "adapter_reward": [], "team_reward": []}
    for law_id, table_id, label in study.CELLS:
        for episode_index, value in enumerate(values[label]):
            records["law_id"].append(law_id)
            records["table_id"].append(table_id)
            records["episode"].append(episode_index)
            records["adapter_reward"].append(value)
            records["team_reward"].append(3.0 * value)
    trajectories = {key: np.asarray(value) for key, value in records.items()}
    return {"seed": seed, "reduction": study.reduce_episode_returns(trajectories, config)}


def test_unequal_multibase_reduction_sum_interaction_sample_sd_and_mcse():
    blocks = [
        _synthetic_block(95401, 0.0),
        _synthetic_block(95402, 1.0),
        _synthetic_block(95403, -0.5),
    ]
    reduced = study.reduce_blocks(blocks)
    for block in blocks:
        contrasts = block["reduction"]["contrasts"]
        source = np.asarray(contrasts["D_source"]["paired_world_adapter_returns"])
        target = np.asarray(contrasts["D_target"]["paired_world_adapter_returns"])
        interaction = np.asarray(
            contrasts["interaction_sum"]["paired_world_adapter_returns"]
        )
        np.testing.assert_allclose(interaction, source + target)
        assert contrasts["interaction_sum"]["base_mean_adapter_return"] == pytest.approx(
            float(np.mean(source + target))
        )
        assert contrasts["interaction_sum"][
            "paired_world_sample_standard_deviation"
        ] == pytest.approx(float(np.std(source + target, ddof=1)))

    assert reduced["base_means"]["D_source"] == pytest.approx([5.0, 7.0, 4.0])
    assert reduced["base_means"]["D_target"] == pytest.approx([2.75, 3.75, 2.25])
    assert reduced["equal_weight_three_base_means"]["interaction_sum"] == pytest.approx(
        np.mean([7.75, 10.75, 6.25])
    )
    for name in ("D_source", "D_target", "interaction_sum"):
        sds = np.asarray(
            reduced["per_base_paired_world_sample_standard_deviations"][name]
        )
        expected_mcse = np.sqrt(np.sum(sds**2 / 16.0) / 9.0)
        assert reduced["conditional_fixed_base_monte_carlo_standard_errors"][
            name
        ] == pytest.approx(expected_mcse)
    assert reduced["no_threshold_confidence_interval_or_claim_rule"] is True
    assert set(reduced["equal_weight_three_base_cell_means"]) == {
        label for _, _, label in study.CELLS
    }


def test_runner_identity_output_source_partial_exposure_and_admission(monkeypatch, tmp_path):
    assert runner.SEEDS == (95401, 95402, 95403)
    assert runner.PLAN_SOURCE == "548ae30195031322d38804b3ac90bd37cb4d2b44"
    assert runner.B09_EVIDENCE_COMMIT == "69a55e71d9f1bca4e8cdd204adce256cd05a7676"
    assert runner.OUTPUT_SUFFIX.as_posix() == "runs/skill_teammate_drift_learning/b11_law_table_crossing"
    assert hashlib.sha256((runner.INPUT_ROOT / "artifacts.json").read_bytes()).hexdigest() == runner.ROOT_ARTIFACTS_SHA256

    out = tmp_path / runner.OUTPUT_SUFFIX
    out.mkdir(parents=True)
    for name in (
        "admission-preflight.json",
        "launch-manifest.json",
        "launch-status.json",
        "stdout.log",
    ):
        (out / name).write_text("launcher bookkeeping")
    assert runner.prepare_output_directory(out) == out.resolve()
    (out / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError, match="existing B11 scientific output"):
        runner.prepare_output_directory(out)

    manifest = runner.source_manifest()
    assert "b10_study" in manifest["files"]
    assert manifest["files"]["b10_study"]["sha256"] == runner.EXPECTED_B10_STUDY_SHA256
    frozen = study.load_frozen_state(
        runner.INPUT_ROOT,
        95401,
        expected_root_artifacts_sha256=runner.ROOT_ARTIFACTS_SHA256,
    )
    assert runner.validate_source_manifest(manifest, frozen["b09_source_manifest"])
    damaged = json.loads(json.dumps(manifest))
    damaged["files"]["b10_study"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source digest mismatch"):
        runner.validate_source_manifest(damaged, frozen["b09_source_manifest"])

    metadata = {
        "evaluation_attempts": [],
        "started_evaluation_blocks": 0,
        "completed_evaluation_blocks": 0,
    }
    exposure = {key: 0 for key in study.EXPOSURE_KEYS}
    attempt = runner.begin_evaluation(metadata, 95401, exposure)
    exposure["native_constructors"] = 1
    assert attempt["status"] == "RUNNING"
    assert attempt["partial_exposure"]["native_constructors"] == 1
    assert attempt["unfinished_work_not_counted_as_zero"] is True

    called = set()
    for source in (Path(runner.__file__).read_text(), Path(study.__file__).read_text()):
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)
    assert called.isdisjoint({"run_block", "_training", "JointLawLearner", "predict", "observe"})

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
        runner.main(
            [
                "--seeds",
                *map(str, runner.SEEDS),
                "--launch-sha",
                "a" * 40,
                "--out",
                str(tmp_path / "wrong"),
            ]
        )
    assert not admission_calls and not stage_calls
    with pytest.raises(SystemExit):
        runner.main(["--seeds", *map(str, runner.SEEDS), *base])
    assert len(admission_calls) == 1 and not stage_calls
