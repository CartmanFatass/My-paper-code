import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.fixed_radial_b10 import study
from experiments.candidates.skill_teammate_drift_learning.native_joint_b09 import (
    study as b09,
)
from scripts import run_skill_drift_fixed_radial_b10 as runner
from tools.research_support.interpreters import control_plane_interpreter


@pytest.fixture(scope="module")
def tiny_evaluation():
    # The sole native B10 fixture: zero fits, 8 actual plus 32 planning calls.
    frozen = study.load_frozen_state(
        runner.INPUT_ROOT,
        95401,
        expected_root_artifacts_sha256=runner.ROOT_ARTIFACTS_SHA256,
    )
    before = {key: value.copy() for key, value in frozen["state"].items()}
    exposure = {key: 0 for key in study.EXPOSURE_KEYS}
    result = study.run_evaluation(
        study.TINY_CONFIG,
        95992,
        frozen,
        exposure=exposure,
    )
    return {"frozen": frozen, "before": before, "result": result, "exposure": exposure}


def test_frozen_state_bundle_and_tamper_checks_are_read_only(tmp_path):
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
        np.testing.assert_array_equal(item["state"]["final_updates"], [64, 64])
        np.testing.assert_array_equal(
            item["projected_probabilities"],
            b09.marginal_product(item["target_probabilities"]),
        )
        assert set(item["verified_digests"]) == {
            "artifacts.json", "summary.json", "state.npz"
        }
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


def test_tiny_zero_fit_cost_complete_traces_and_frozen_state(tiny_evaluation):
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
        "loaded_target_probability_views": 1,
        "frozen_projection_constructions": 1,
        "projection_equivalence_calculations": 1,
        "total_marginal_projection_calculations": 2,
        "evaluation_episodes": 4,
        "evaluation_team_steps": 8,
        "response_tables": 4,
        "joint_q_vectors": 4,
        "projected_q_vectors": 4,
        "joint_choices": 4,
        "projected_choices": 4,
        "actual_focal_policy_choices": 8,
        "J_emp_deployment_choices": 2,
        "M_proj_deployment_choices": 2,
        "fixed_IN_choice_assignments": 2,
        "fixed_OUT_choice_assignments": 2,
        "true_q_vectors_after_choice": 4,
        "true_chosen_values_after_choice": 4,
        "true_regrets_after_choice": 4,
        "external_innovation_draw_calls": 8,
        "unique_external_innovation_addresses": 2,
        "native_constructors": 4,
        "implicit_constructor_resets": 4,
        "logical_episode_initializations": 4,
        "custom_geometry_channel_refreshes": 4,
        "actual_native_step_calls": 8,
        "planning_native_step_calls": 32,
        "deep_copies": 32,
        "total_native_step_calls": 40,
    }
    assert tiny_evaluation["exposure"] == {
        "native_constructors": 4,
        "implicit_constructor_resets": 4,
        "logical_episode_initializations": 4,
        "custom_geometry_channel_refreshes": 4,
        "deep_copies": 32,
        "training_native_step_calls": 0,
        "evaluation_native_step_calls": 8,
        "planner_native_step_calls": 32,
    }
    assert result["trajectory"]["policy_index"].shape == (8,)
    assert result["planning"]["policy_index"].shape == (4,)
    assert all(array.dtype != object for array in result["trajectory"].values())
    assert all(array.dtype != object for array in result["planning"].values())
    for key, before in tiny_evaluation["before"].items():
        np.testing.assert_array_equal(tiny_evaluation["frozen"]["state"][key], before)
        np.testing.assert_array_equal(result["frozen_state"][key], before)
    assert result["summary"]["frozen_base_seed"] == 95401
    assert result["summary"]["historical_input_cost"]["fits"] == 1
    assert result["summary"]["historical_input_cost"]["recorded_counts"]["count_updates"] == 128
    json.dumps(result["summary"], allow_nan=False)


def test_pairing_fixed_bits_raw_reduction_and_selected_branches(tiny_evaluation):
    result = tiny_evaluation["result"]
    trajectory = result["trajectory"]
    planning = result["planning"]
    for tick in (0, 1):
        rows = trajectory["tick"] == tick
        assert rows.sum() == 4
        assert np.unique(trajectory["rng_address"][rows], axis=0).shape == (1, 5)
        assert np.unique(trajectory["external_uniform"][rows]).size == 1
        assert np.unique(trajectory["joint_row"][rows]).size == 1
    initial = trajectory["tick"] == 0
    np.testing.assert_array_equal(
        trajectory["pre_positions"][initial],
        np.repeat(trajectory["pre_positions"][initial][0:1], 4, axis=0),
    )
    assert np.all(trajectory["rng_address"][:, 1:3] == [2, 2])
    assert np.all(trajectory["focal_bit"][trajectory["policy_index"] == 2] == 1)
    assert np.all(trajectory["focal_bit"][trajectory["policy_index"] == 3] == 0)
    assert np.all(trajectory["planner_record_index"][trajectory["policy_index"] >= 2] == -1)

    for planner_index, trajectory_index in enumerate(planning["trajectory_index"]):
        trajectory_index = int(trajectory_index)
        focal = int(trajectory["focal_bit"][trajectory_index])
        row = int(trajectory["joint_row"][trajectory_index])
        assert int(trajectory["planner_record_index"][trajectory_index]) == planner_index
        assert trajectory["adapter_reward"][trajectory_index] == planning[
            "response_adapter_reward"
        ][planner_index, focal, row]
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

    reduced = result["summary"]["reduction"]
    raw = {}
    for index, policy in enumerate(study.POLICIES):
        rows = trajectory["policy_index"] == index
        raw[policy] = float(trajectory["adapter_reward"][rows].sum())
        np.testing.assert_allclose(reduced["episode_adapter_returns"][policy], [raw[policy]])
    assert reduced["contrasts"]["J_minus_IN"]["base_mean_adapter_return"] == pytest.approx(raw["J_emp"] - raw["IN"])
    assert reduced["contrasts"]["J_minus_OUT"]["base_mean_adapter_return"] == pytest.approx(raw["J_emp"] - raw["OUT"])
    assert reduced["contrasts"]["J_minus_M"]["base_mean_adapter_return"] == pytest.approx(raw["J_emp"] - raw["M_proj"])
    assert reduced["contrasts"]["M_minus_OUT"]["base_mean_adapter_return"] == pytest.approx(raw["M_proj"] - raw["OUT"])


def test_in_overshoot_and_agent_specific_zero_radius_convention_are_pure():
    positions = np.array(
        [
            [500.1, 500.0, 50.0],
            [500.0, 500.0, 50.0],
            [500.0, 500.0, 50.0],
        ]
    )
    actions = b09.commands_from_bits(positions, np.array([1, 0, 1], dtype=np.int8))
    after_xy = positions[:, :2] + 30.0 * actions[:, :2]
    assert after_xy[0, 0] < b09.USER_POSITION[0]
    np.testing.assert_allclose(actions[1, :2], [np.cos(2 * np.pi / 3), np.sin(2 * np.pi / 3)])
    np.testing.assert_allclose(actions[2, :2], [-np.cos(4 * np.pi / 3), -np.sin(4 * np.pi / 3)])
    recomputed = b09.commands_from_bits(
        np.column_stack((after_xy, np.full(3, 50.0))),
        np.zeros(3, dtype=np.int8),
    )
    assert recomputed[0, 0] < 0.0


def _synthetic_block(seed, values):
    config = study.Config(episodes=2, steps=1)
    adapter_reward = []
    policy_index = []
    episode = []
    for index, policy in enumerate(study.POLICIES):
        for episode_index, value in enumerate(values[policy]):
            policy_index.append(index)
            episode.append(episode_index)
            adapter_reward.append(value)
    trajectories = {
        "policy_index": np.asarray(policy_index),
        "episode": np.asarray(episode),
        "adapter_reward": np.asarray(adapter_reward, dtype=np.float64),
        "team_reward": 3.0 * np.asarray(adapter_reward, dtype=np.float64),
    }
    return {"seed": seed, "reduction": study.reduce_episode_returns(trajectories, config)}


def test_unequal_three_base_primary_and_secondary_reductions():
    blocks = [
        _synthetic_block(95401, {"J_emp": [10, 20], "M_proj": [7, 15], "IN": [1, 17], "OUT": [4, 12]}),
        _synthetic_block(95402, {"J_emp": [3, 9], "M_proj": [2, 4], "IN": [5, 1], "OUT": [0, 8]}),
        _synthetic_block(95403, {"J_emp": [12, 2], "M_proj": [9, 1], "IN": [8, 0], "OUT": [5, 3]}),
    ]
    reduced = study.reduce_blocks(blocks)
    assert reduced["base_means"] == pytest.approx(
        {
            "J_minus_IN": [6.0, 3.0, 3.0],
            "J_minus_OUT": [7.0, 2.0, 3.0],
            "J_minus_M": [4.0, 3.0, 2.0],
            "M_minus_OUT": [3.0, -1.0, 1.0],
        }
    )
    assert reduced["equal_weight_three_base_means"] == pytest.approx(
        {"J_minus_IN": 4.0, "J_minus_OUT": 4.0, "J_minus_M": 3.0, "M_minus_OUT": 1.0}
    )
    assert reduced["paired_episode_values_by_base"]["J_minus_IN"][0] == [9.0, 3.0]
    assert reduced["paired_episode_values_by_base"]["J_minus_M"][1] == [1.0, 5.0]
    assert reduced["paired_episode_values_by_base"]["M_minus_OUT"][2] == [4.0, -2.0]


def test_runner_identity_output_protection_partial_exposure_and_literal_guard(monkeypatch, tmp_path):
    assert runner.SEEDS == (95401, 95402, 95403)
    assert runner.PLAN_SOURCE == "75ef4a931de474ab27e6903c6f16929eab932d85"
    assert runner.B09_EVIDENCE_COMMIT == "69a55e71d9f1bca4e8cdd204adce256cd05a7676"
    assert runner.INPUT_SUFFIX.as_posix() == "runs/skill_teammate_drift_learning/b09_native_joint"
    assert runner.OUTPUT_SUFFIX.as_posix() == "runs/skill_teammate_drift_learning/b10_fixed_radial_controls"
    assert hashlib.sha256((runner.INPUT_ROOT / "artifacts.json").read_bytes()).hexdigest() == runner.ROOT_ARTIFACTS_SHA256

    out = tmp_path / runner.OUTPUT_SUFFIX
    out.mkdir(parents=True)
    for name in ("admission-preflight.json", "launch-manifest.json", "launch-status.json", "stdout.log"):
        (out / name).write_text("launcher bookkeeping")
    assert runner.prepare_output_directory(out) == out.resolve()
    (out / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError, match="existing B10 scientific output"):
        runner.prepare_output_directory(out)
    (out / "input-manifest.json").write_text("{}")
    (out / "source-manifest.json").write_text("{}")
    block = out / "seed_95401"
    block.mkdir()
    (block / "summary.json").write_text("{}")
    assert set(runner.stable_science_digests(out)) == {
        "summary.json", "input-manifest.json", "source-manifest.json", "seed_95401/summary.json"
    }

    metadata = {"evaluation_attempts": [], "started_evaluation_blocks": 0, "completed_evaluation_blocks": 0}
    exposure = {key: 0 for key in study.EXPOSURE_KEYS}
    attempt = runner.begin_evaluation(metadata, 95401, exposure)
    exposure["native_constructors"] = 1
    assert attempt["status"] == "RUNNING"
    assert attempt["partial_exposure"]["native_constructors"] == 1
    assert metadata["started_evaluation_blocks"] == 1

    runner_source = Path(runner.__file__).read_text()
    study_source = Path(study.__file__).read_text()
    forbidden = {"run_block", "_training", "JointLawLearner"}
    called = set()
    for tree in (ast.parse(runner_source), ast.parse(study_source)):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)
    assert called.isdisjoint(forbidden)

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
