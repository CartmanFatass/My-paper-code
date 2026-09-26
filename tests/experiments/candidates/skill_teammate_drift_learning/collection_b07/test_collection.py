import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.collection_b07 import study
from scripts import run_skill_drift_collection_b07 as runner
from tools.research_support.interpreters import control_plane_interpreter


@pytest.fixture(scope="module")
def tiny_result():
    # The sole real learning fixture in this module: 8 fits, 128 macros, 384 ticks.
    return study.run_block(
        study.Config(source_macros=16, target_macros=16), seed=95971
    )


def test_epsilon_propensity_and_action_mapping_are_exact():
    np.testing.assert_array_equal(
        study.cooperative_propensity(np.array([0, 1]), 0.20), [0.10, 0.90]
    )
    np.testing.assert_array_equal(
        study.cooperative_propensity(np.array([0, 1]), 1.0), [0.5, 0.5]
    )
    for uniform in (0.1, 0.49, 0.5, 0.9):
        for greedy in (study.SAFE, study.COOPERATIVE):
            assert study.action_from_uniform(
                uniform, study.cooperative_propensity(greedy, 1.0)
            ) == int(uniform >= 0.5)
    assert study.action_from_uniform(0.89, 0.10) == study.SAFE
    assert study.action_from_uniform(0.90, 0.10) == study.COOPERATIVE
    truth = np.array([0.6, 0.8])
    readout = study.exact_policy_readouts(np.array([0.4, 0.7]), truth, 0.3, 0.2)
    assert readout == {
        "greedy_action": 1,
        "matched_epsilon_cooperative_probability": pytest.approx(0.9),
        "greedy_expected_return": pytest.approx(0.8),
        "matched_epsilon_expected_return": pytest.approx(0.78),
        "actual_collector_expected_return": pytest.approx(0.66),
    }


def test_tiny_contract_has_four_actual_branches_and_full_numeric_evidence(tiny_result):
    assert set(tiny_result["branches"]) == {"R_U", "F_U", "R_E", "F_E"}
    assert tiny_result["summary"]["counts"] == {
        "decision_fits": 4,
        "law_fits": 4,
        "actual_macros": 128,
        "duplicated_source_macros": 64,
        "primitive_ticks": 384,
        "sampled_reward_labels": 128,
        "q_truth_panels": 128,
        "scalar_policy_values": 384,
        "evaluation_environment_ticks": 0,
        "evaluation_reward_draws": 0,
        "gradient_optimizer_calls": 0,
    }
    for branch, payload in tiny_result["branches"].items():
        assert payload["trajectory"]["raw_predictions"].shape == (32, 2)
        assert payload["trajectory"]["exact_values"].shape == (32, 2)
        assert payload["summary"]["counts"]["actual_macros"] == 32
        assert payload["summary"]["counts"]["decision_observations"] == 32
        assert payload["summary"]["counts"]["q_truth_panels"] == 32
        assert payload["summary"]["counts"]["scalar_policy_values"] == 96
        assert payload["summary"]["compute_wall_seconds"] >= 0.0
        assert all(array.dtype != object for array in payload["trajectory"].values())
        assert all(array.dtype != object for array in payload["state"].values())
        assert "source_law_counts" in payload["state"]
        assert "final_law_counts" in payload["state"]
        assert "source_decision_estimate" in payload["state"]
        assert "final_decision_estimate" in payload["state"]
        json.dumps(payload["summary"], allow_nan=False)


def test_source_prefixes_and_uniform_histories_are_identical(tiny_result):
    branches = tiny_result["branches"]
    source = slice(0, 16)
    trajectory_keys = (
        "collection_propensity",
        "collection_action",
        "outcome",
        "terminal_outcome",
        "reward",
        "reward_probability",
        "pre_positions",
        "primitive_actions",
        "post_positions",
    )
    reference = branches["R_U"]["trajectory"]
    for payload in branches.values():
        for key in trajectory_keys:
            np.testing.assert_array_equal(
                payload["trajectory"][key][source], reference[key][source]
            )
    for key in trajectory_keys + (
        "estimated_law",
        "law_counts_before",
        "law_counts_after",
    ):
        np.testing.assert_array_equal(
            branches["R_U"]["trajectory"][key],
            branches["F_U"]["trajectory"][key],
        )


def test_propensities_are_preoutcome_and_each_law_uses_only_own_cooperation(
    tiny_result,
):
    slots = tiny_result["common"]["collector_uniform"]
    for branch, payload in tiny_result["branches"].items():
        trajectory = payload["trajectory"]
        expected = np.full(32, 0.5)
        if branch.endswith("_E"):
            expected[16:] = 0.1 + 0.8 * trajectory["greedy_action"][16:]
        np.testing.assert_array_equal(trajectory["collection_propensity"], expected)
        np.testing.assert_array_equal(
            trajectory["collection_action"], slots >= 1.0 - expected
        )
        counts = np.zeros((2, 4), dtype=np.int64)
        for index in range(32):
            version = int(trajectory["version"][index])
            context = int(trajectory["context"][index])
            assert trajectory["law_counts_before"][index] == counts[version, context]
            if trajectory["collection_action"][index] == study.COOPERATIVE:
                counts[version, context] += 1
            assert trajectory["law_counts_after"][index] == counts[version, context]


def test_three_policy_readouts_remain_distinct_and_reconstruct_exactly(tiny_result):
    for branch, payload in tiny_result["branches"].items():
        trajectory = payload["trajectory"]
        truth = trajectory["exact_values"]
        rows = np.arange(32)
        np.testing.assert_array_equal(
            trajectory["greedy_expected_return"],
            truth[rows, trajectory["greedy_action"]],
        )
        matched_p = 0.1 + 0.8 * trajectory["greedy_action"]
        matched = (1 - matched_p) * truth[:, 0] + matched_p * truth[:, 1]
        actual_p = trajectory["collection_propensity"]
        actual = (1 - actual_p) * truth[:, 0] + actual_p * truth[:, 1]
        np.testing.assert_allclose(
            trajectory["matched_epsilon_expected_return"], matched
        )
        np.testing.assert_allclose(
            trajectory["actual_collector_expected_return"], actual
        )
        if branch.endswith("_E"):
            np.testing.assert_allclose(
                trajectory["matched_epsilon_expected_return"][16:],
                trajectory["actual_collector_expected_return"][16:],
            )
        else:
            assert payload["summary"]["matched_epsilon_readout_role"] == "off_collector"
            assert np.any(
                trajectory["matched_epsilon_expected_return"][16:]
                != trajectory["actual_collector_expected_return"][16:]
            )


def _synthetic_branch_summaries():
    matched_values = {"R_U": 0.61, "F_U": 0.60, "R_E": 0.66, "F_E": 0.62}
    summaries = {}
    for branch, value in matched_values.items():
        endpoints = {}
        for endpoint, offset in (("first64", -0.01), ("full", 0.0), ("late64", 0.01)):
            matched = value + (offset if branch == "R_E" else 0.0)
            actual = 0.60 if branch.endswith("_U") else matched
            endpoints[endpoint] = {
                "mean_actual_collector_expected_return": actual,
                "mean_matched_epsilon_expected_return": matched,
                "mean_sampled_return": actual - 0.03,
            }
        summaries[branch] = {"target_by_endpoint": endpoints}
    return summaries


def test_synthetic_feedback_interaction_uses_matched_values_in_both_regimes():
    reduced = study.reduce_branch_summaries(_synthetic_branch_summaries())
    full = reduced["by_endpoint"]["full"]
    assert full["primary_executed_e_response_minus_full"] == pytest.approx(0.04)
    assert full["matched_e_response_minus_full"] == pytest.approx(0.04)
    assert full["matched_u_response_minus_full"] == pytest.approx(0.01)
    assert full["matched_feedback_interaction"] == pytest.approx(0.03)
    assert full["uniform_actual_response_minus_full"] == pytest.approx(0.0)
    assert not full["u_matched_readout_is_executed_return"]
    assert [
        reduced["by_endpoint"][endpoint]["primary_executed_e_response_minus_full"]
        for endpoint in ("first64", "full", "late64")
    ] == pytest.approx([0.03, 0.04, 0.05])


def test_runner_aggregate_is_descriptive_and_seed_ordered():
    base = study.reduce_branch_summaries(_synthetic_branch_summaries())
    rows = [
        {"seed": seed, "reductions": base}
        for seed in reversed(runner.SEEDS)
    ]
    reduced = runner.aggregate_reductions(rows)
    primary = reduced["by_endpoint"]["full"][
        "primary_executed_e_response_minus_full"
    ]
    assert primary["paired_values"] == pytest.approx([0.04, 0.04, 0.04])
    assert primary["mean"] == pytest.approx(0.04)
    assert primary["role"] == "primary_exploratory"
    assert reduced["no_confirmation_threshold"]
    assert reduced["interaction_uses_matched_epsilon_in_both_regimes"]


def test_runner_saves_raw_arrays_states_identity_and_digests(tiny_result, tmp_path):
    runner.save_block(tmp_path, tiny_result, 95971, "a" * 40)
    block = tmp_path / "seed_95971"
    summary = json.loads((block / "summary.json").read_text())
    assert summary["object"] == runner.OBJECT
    assert summary["source_identity"] == "a" * 40
    with np.load(block / "R_E" / "trajectory.npz", allow_pickle=False) as arrays:
        assert arrays["collection_propensity"].shape == (32,)
    with np.load(block / "F_E" / "state.npz", allow_pickle=False) as arrays:
        assert "final_decision_estimate" in arrays
    for relative, digest in json.loads((block / "artifacts.json").read_text()).items():
        assert hashlib.sha256((block / relative).read_bytes()).hexdigest() == digest


def test_cli_help_literal_guard_and_preexecution_rejections(monkeypatch, tmp_path):
    script = Path(runner.__file__)
    help_result = subprocess.run(
        [sys.executable, "-B", str(script), "--help"],
        cwd=runner.ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "--seeds" in help_result.stdout and "--launch-sha" in help_result.stdout

    program = (
        "from pathlib import Path; import sys; "
        "from scripts.hmasd_launch import _validate_guard_contract; "
        "_validate_guard_contract(Path(sys.argv[1]), 'skill_teammate_drift_learning')"
    )
    guard = subprocess.run(
        [control_plane_interpreter(), "-B", "-c", program, str(script)],
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
    base = ["--launch-sha", "a" * 40, "--out", str(tmp_path / "out")]
    with pytest.raises(SystemExit):
        runner.main(["--seeds", "1", *base])
    assert not admission_calls and not stage_calls
    with pytest.raises(SystemExit):
        runner.main(["--seeds", *map(str, runner.SEEDS), *base])
    assert len(admission_calls) == 1 and not stage_calls
    assert not (tmp_path / "out").exists()


def test_fixed_runner_identity_and_config():
    assert runner.SEEDS == (95301, 95302, 95303)
    assert runner.BRANCH_IDS == ("R_U", "F_U", "R_E", "F_E")
    assert runner.EPSILON == 0.20
    assert runner.RESPONSE_SETTING == "response_all__response__prior2"
    assert runner.FULL_SETTING == "fingerprint_full__hybrid__prior2"
    assert study.Config() == study.Config(2048, 256, 4, 3, 0.20)
    assert {
        branch.id: (branch.collector, branch.spec.id) for branch in study.BRANCHES
    } == {
        "R_U": ("uniform", runner.RESPONSE_SETTING),
        "F_U": ("uniform", runner.FULL_SETTING),
        "R_E": ("epsilon_greedy", runner.RESPONSE_SETTING),
        "F_E": ("epsilon_greedy", runner.FULL_SETTING),
    }
