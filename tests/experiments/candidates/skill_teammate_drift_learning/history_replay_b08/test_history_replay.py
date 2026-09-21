import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.history_replay_b08 import study
from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05.learning import (
    DecisionLearner,
)
from scripts import run_skill_drift_history_replay_b08 as runner
from tools.research_support.interpreters import control_plane_interpreter


def _hand_state(spec):
    learner = DecisionLearner(spec, 4)
    learner.safe_count = 4
    learner.safe_reward_sum = 2.0
    learner.safe_updates = 4
    learner.cooperative_updates = 4
    if spec == study.RESPONSE_SPEC:
        learner.response_counts[:] = [1, 1, 1, 1]
        learner.response_reward_sums[:] = [0.0, 1.0, 0.0, 1.0]
    else:
        feature_rows = np.array(
            [
                [0.25, 0.25, 0.25, 0.25, 1, 0, 0, 0, 0, 0, 0, 0],
                [0.10, 0.20, 0.30, 0.40, 0, 1, 0, 0, 0, 0, 0, 0],
                [0.40, 0.30, 0.20, 0.10, 0, 0, 1, 0, 0, 0, 0, 0],
                [0.20, 0.30, 0.10, 0.40, 0, 0, 0, 1, 0, 0, 0, 0],
            ],
            dtype=np.float64,
        )
        rewards = np.array([0.0, 1.0, 1.0, 0.0])
        learner.xtx = feature_rows.T @ feature_rows
        learner.xty = feature_rows.T @ rewards
        learner.coefficients = np.linalg.solve(
            learner.xtx + 2.0 * np.eye(learner.dimension),
            learner.xty + 2.0 * learner.prior_coefficients,
        )
        learner.solve_calls = 4
    return learner.export_state()


def _rows(laws):
    return {
        "macro_index": np.array([2048, 2049], dtype=np.int32),
        "version": np.array([1, 1], dtype=np.int8),
        "context": np.array([0, 1], dtype=np.int16),
        "estimated_law": np.asarray(laws, dtype=np.float64),
        "collection_action": np.array([1, 0], dtype=np.int8),
        "outcome": np.array([3, 0], dtype=np.int8),
        "reward": np.array([1, 0], dtype=np.int8),
        "exact_values": np.array([[0.6, 0.75], [0.6, 0.45]], dtype=np.float64),
    }


def _analytic_first(spec, state, row):
    safe = (state["safe_reward_sum"][0] + 1.0) / (state["safe_count"][0] + 2.0)
    law = row["estimated_law"][0]
    if spec == study.RESPONSE_SPEC:
        means = (state["response_reward_sums"] + 1.0) / (state["response_counts"] + 2.0)
        cooperative = law @ means
    else:
        feature = np.zeros(12)
        feature[:4] = law
        feature[4 + 4 + int(row["context"][0])] = 1.0
        cooperative = feature @ state["coefficients"]
    return np.array([safe, cooperative])


@pytest.fixture(scope="module")
def tiny_crossing():
    # The one B08 learning fixture: two fits x two stored rows = four feedback updates.
    response_state = _hand_state(study.RESPONSE_SPEC)
    full_state = _hand_state(study.FULL_SPEC)
    r_history = _rows([[0.10, 0.20, 0.30, 0.40], [0.40, 0.10, 0.20, 0.30]])
    f_history = _rows([[0.25, 0.25, 0.25, 0.25], [0.10, 0.40, 0.20, 0.30]])
    donors_before = {
        "R": {key: value.copy() for key, value in r_history.items()},
        "F": {key: value.copy() for key, value in f_history.items()},
    }
    r_on_f = study.run_continuation(
        spec=study.RESPONSE_SPEC,
        source_state=response_state,
        donor_rows=f_history,
        expected_first_raw_prediction=_analytic_first(study.RESPONSE_SPEC, response_state, f_history),
    )
    f_on_r = study.run_continuation(
        spec=study.FULL_SPEC,
        source_state=full_state,
        donor_rows=r_history,
        expected_first_raw_prediction=_analytic_first(study.FULL_SPEC, full_state, r_history),
    )
    return {
        "response_state": response_state,
        "full_state": full_state,
        "r_history": r_history,
        "f_history": f_history,
        "donors_before": donors_before,
        "r_on_f": r_on_f,
        "f_on_r": f_on_r,
    }


def test_restore_roundtrips_every_exported_field_without_updates():
    for spec in (study.RESPONSE_SPEC, study.FULL_SPEC):
        source = _hand_state(spec)
        restored = study.restore_decision_learner(spec, 4, source).export_state()
        assert set(restored) == set(source)
        for key in source:
            np.testing.assert_array_equal(restored[key], source[key])
    broken = _hand_state(study.FULL_SPEC)
    broken.pop("xtx")
    with pytest.raises(ValueError, match="keys differ"):
        study.restore_decision_learner(study.FULL_SPEC, 4, broken)


def test_tiny_crossing_predicts_before_feedback_and_preserves_donor_rows(tiny_crossing):
    for name, payload, source in (
        ("r_on_f", tiny_crossing["r_on_f"], tiny_crossing["response_state"]),
        ("f_on_r", tiny_crossing["f_on_r"], tiny_crossing["full_state"]),
    ):
        trajectory = payload["trajectory"]
        initial_updates = int(source["safe_posterior_updates"][0] + source["cooperative_observations"][0])
        np.testing.assert_array_equal(trajectory["decision_updates_before"], [initial_updates, initial_updates + 1])
        assert payload["summary"]["counts"]["decision_observations"] == 2
        assert payload["summary"]["new_preupdate_q_predictions"] == 2
        assert payload["summary"]["scalar_policy_reductions"] == 4
        assert payload["summary"]["law_fits"] == 0
        assert payload["summary"]["environment_ticks"] == 0
        assert payload["summary"]["sampled_rewards"] == 0
        assert payload["summary"]["first_prediction_fidelity"]
        assert all(array.dtype != object for array in trajectory.values())
    for label, current in (("R", tiny_crossing["r_history"]), ("F", tiny_crossing["f_history"])):
        for key, before in tiny_crossing["donors_before"][label].items():
            np.testing.assert_array_equal(current[key], before)


def test_donor_preoutcome_law_features_are_used_and_frozen(tiny_crossing):
    response_state = tiny_crossing["response_state"]
    means = (response_state["response_reward_sums"] + 1.0) / (response_state["response_counts"] + 2.0)
    expected_first = tiny_crossing["f_history"]["estimated_law"][0] @ means
    assert tiny_crossing["r_on_f"]["trajectory"]["raw_predictions"][0, 1] == pytest.approx(expected_first)
    np.testing.assert_array_equal(
        tiny_crossing["r_on_f"]["trajectory"]["estimated_law"],
        tiny_crossing["f_history"]["estimated_law"],
    )
    altered = {key: value.copy() for key, value in tiny_crossing["f_history"].items()}
    altered["estimated_law"][1] = [1.0, 0.0, 0.0, 0.0]
    # Pure validation confirms the row is the only law-feature source; no law learner exists here.
    assert study._validate_donor_rows(altered) == 2


def test_same_history_reduction_arithmetic_and_context_contributions():
    readout = study.fixed_history_readouts(
        np.array([0.4, 0.7]), np.array([0.6, 0.8]), epsilon=0.2
    )
    assert readout == {
        "greedy_action": 1,
        "matched_epsilon_propensity": pytest.approx(0.9),
        "greedy_expected_return": pytest.approx(0.8),
        "matched_epsilon_expected_return": pytest.approx(0.78),
    }
    contexts = np.array([0, 1])
    panel = lambda values: {
        "context": contexts,
        "matched_epsilon_expected_return": np.array(values, dtype=np.float64),
    }
    reduced = study.reduce_crossed_histories(
        r_on_r=panel([0.8, 0.6]),
        f_on_r=panel([0.68, 0.48]),
        r_on_f=panel([0.65, 0.55]),
        f_on_f=panel([0.60, 0.50]),
    )
    full = reduced["by_endpoint"]["full"]
    table = full["matched_epsilon_2x2"]
    assert table["R_history"] == pytest.approx({"R": 0.70, "F": 0.58})
    assert table["F_history"] == pytest.approx({"R": 0.60, "F": 0.55})
    assert full["per_history_response_minus_full"] == pytest.approx(
        {"R_history": 0.12, "F_history": 0.05}
    )
    assert full["per_method_R_history_minus_F_history"] == pytest.approx(
        {"R": 0.10, "F": 0.03}
    )
    assert sum(
        row["R_minus_F_on_R_history"]
        for row in reduced["context_contributions"].values()
    ) == pytest.approx(0.12)
    assert reduced["no_actual_collector_or_sampled_reward_claim"]


def test_fixed_input_manifests_validate_and_reject_seed_source_or_digest():
    loaded = study.validate_block_inputs(
        input_root=runner.INPUT_ROOT,
        seed=95301,
        expected_manifest_sha256=runner.MANIFEST_SHA256[95301],
        expected_source_identity=runner.SCIENTIFIC_SOURCE,
    )
    assert loaded["seed"] == 95301
    assert set(loaded["branches"]) == {"R_E", "F_E"}
    assert len(loaded["branches"]["R_E"]["donor_rows"]["reward"]) == 256
    with pytest.raises(ValueError, match="manifest digest"):
        study.validate_block_inputs(
            input_root=runner.INPUT_ROOT,
            seed=95302,
            expected_manifest_sha256=runner.MANIFEST_SHA256[95301],
            expected_source_identity=runner.SCIENTIFIC_SOURCE,
        )
    with pytest.raises(ValueError, match="source identity"):
        study.validate_block_inputs(
            input_root=runner.INPUT_ROOT,
            seed=95301,
            expected_manifest_sha256=runner.MANIFEST_SHA256[95301],
            expected_source_identity="0" * 40,
        )
    with pytest.raises(ValueError, match="manifest digest"):
        study.validate_block_inputs(
            input_root=runner.INPUT_ROOT,
            seed=95301,
            expected_manifest_sha256="0" * 64,
            expected_source_identity=runner.SCIENTIFIC_SOURCE,
        )


def test_runner_fixed_identity_help_literal_guard_and_preexecution_rejections(monkeypatch, tmp_path):
    assert runner.SEEDS == (95301, 95302, 95303)
    assert runner.EVIDENCE_COMMIT == "6ab8db786a2dc2397d883e8476ccb0303b059f0e"
    assert runner.SCIENTIFIC_SOURCE == "03d3633bd55b4095d7b195ad5ecd3f44eb3c864a"
    assert runner.PLAN_COMMIT == "9d7f9a4d9624bec3a5ea69e88f04e1d9912ade78"
    assert runner.CONTINUATION_IDS == ("R_on_F_E_history", "F_on_R_E_history")
    assert hashlib.sha256((runner.INPUT_ROOT / "summary.json").read_bytes()).hexdigest() == runner.ROOT_SUMMARY_SHA256

    external_out = tmp_path / runner.OUTPUT_SUFFIX
    external_out.mkdir(parents=True)
    for name in (
        "admission-preflight.json",
        "launch-manifest.json",
        "launch-status.json",
        "stdout.log",
        "stderr.log",
    ):
        (external_out / name).write_text("launcher bookkeeping")
    assert runner.has_fixed_output_suffix(external_out)
    assert runner.prepare_output_directory(external_out) == external_out.resolve()
    (external_out / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError, match="existing B08 scientific output"):
        runner.prepare_output_directory(external_out)
    (external_out / "input-manifest.json").write_text("{}")
    seed_output = external_out / "seed_95301"
    seed_output.mkdir()
    (seed_output / "reduction.json").write_text("{}")
    stable_digests = runner.stable_science_digests(external_out)
    assert set(stable_digests) == {
        "summary.json",
        "input-manifest.json",
        "seed_95301/reduction.json",
    }

    metadata = {
        "fit_attempts": [],
        "started_decision_fits": 0,
        "completed_decision_fits": 0,
    }
    first = runner.begin_fit_attempt(
        metadata, seed=95301, continuation=study.CONTINUATIONS[0]
    )
    assert (metadata["started_decision_fits"], metadata["completed_decision_fits"]) == (1, 0)
    assert len(metadata["fit_attempts"]) == 1
    stub_summary = {
        "records_read": 256,
        "recorded_feedback_updates": 256,
        "compute_wall_seconds": 1.25,
        "counts": {"decision_observations": 256},
    }
    runner.complete_fit_attempt(metadata, first, stub_summary)
    assert (metadata["started_decision_fits"], metadata["completed_decision_fits"]) == (1, 1)
    assert first["status"] == "COMPLETE" and first["saved"] is False
    second = runner.begin_fit_attempt(
        metadata, seed=95301, continuation=study.CONTINUATIONS[1]
    )
    assert (metadata["started_decision_fits"], metadata["completed_decision_fits"]) == (2, 1)
    assert second["status"] == "RUNNING" and "saved" not in second
    runner.complete_fit_attempt(metadata, second, stub_summary)
    runner.mark_fit_attempts_saved((first, second))
    assert first["saved"] is True and second["saved"] is True

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
    admitted_out = tmp_path / "admitted" / runner.OUTPUT_SUFFIX
    base = ["--launch-sha", "a" * 40, "--out", str(admitted_out)]
    with pytest.raises(SystemExit):
        runner.main(["--seeds", "1", *base])
    with pytest.raises(SystemExit):
        runner.main(["--seeds", *map(str, runner.SEEDS), "--launch-sha", "a" * 40, "--out", str(tmp_path / "wrong")])
    assert not admission_calls and not stage_calls
    with pytest.raises(SystemExit):
        runner.main(["--seeds", *map(str, runner.SEEDS), *base])
    assert len(admission_calls) == 1 and not stage_calls


def test_json_contract_has_no_nonfinite_values(tiny_crossing):
    for key in ("r_on_f", "f_on_r"):
        json.dumps(tiny_crossing[key]["summary"], allow_nan=False)
