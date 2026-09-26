import json

import numpy as np
import pytest

from experiments.candidates.finite_model_decision_value.b01 import study
from scripts import hmasd_admission, run_fmdv_b01


def test_calibration_consumes_only_observed_prefix():
    # Two successes from4: independent direct likelihood for each stated law.
    positions = np.array([[33, 32, 32, 31, 31]])
    weights, successes = study.calibration_posterior(positions, 4)
    expected = np.array([(.35 * .65) ** 2, (.55 * .45) ** 2,
                         (.75 * .25) ** 2, (.95 * .05) ** 2])
    np.testing.assert_allclose(weights[0], expected / expected.sum(), atol=1e-15)
    assert successes.tolist() == [2]
    with pytest.raises(ValueError, match="only the requested"):
        study.calibration_posterior(np.tile(33, (1, 33)), 4)
    with pytest.raises(ValueError, match="unsaturated"):
        study.calibration_posterior(np.array([[2, 1, 0, 0, 0]]), 4)
    first = study.collect_calibration(study.Config(seed=449921), (7, 3))
    reordered = study.collect_calibration(study.Config(seed=449921), (3, 7))
    np.testing.assert_array_equal(first[0], reordered[0][::-1])
    np.testing.assert_array_equal(first[1], reordered[1][::-1])
    assert first[1].shape == (2, 33)
    assert first[1].min() >= 1


def test_exact_zero_uses_af_not_always_hold():
    np.testing.assert_array_equal(
        study.threshold_requests(np.array([0., 0., .01, -.01]), np.array([True, False, False, True])),
        [True, False, True, False])


def test_entry_requires_admission_before_output_or_science(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(study, "run_study", lambda *args: called.append(args))
    def reject(*args, **kwargs):
        raise RuntimeError("missing admission fixture")
    monkeypatch.setattr(hmasd_admission, "require_admission", reject)
    target = tmp_path / "uncreated"
    with pytest.raises(RuntimeError, match="missing admission"):
        run_fmdv_b01.main(["--out", str(target), "--launch-sha", "f" * 40])
    assert not called and not target.exists()
    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "f" * 40})
    with pytest.raises(ValueError, match="disagrees"):
        run_fmdv_b01.main(["--out", str(target), "--launch-sha", "e" * 40])
    assert not called
    run_fmdv_b01.main(["--out", str(target), "--launch-sha", "f" * 40])
    assert called == [(target, "f" * 40, study.Config())]


def test_small_complete_six_arm_fixture_and_artifact_recovery(tmp_path):
    # Different seeds/exposure from B01; this is a correctness fixture, no score selection.
    config = study.Config(seed=441731, model_seed=442973, contexts=2, batch=2, horizon=48, particles=2)
    out = tmp_path / "fixture"
    summary = study.run_study(out, "f" * 40, config)
    assert summary["state"] == "COMPLETE"
    assert summary["counts"]["calibration_fits_completed"] == 4
    assert summary["counts"]["evaluation_episodes"] == 12
    assert summary["counts"]["evaluation_team_ticks"] == 576
    assert summary["counts"]["calibration_steps"] == 64
    assert summary["counts"]["optimizer_updates"] == 0
    assert 0 < summary["counts"]["model_branch_transitions"] <= summary["counts"]["model_branch_transition_upper"]
    episodes = json.loads((out / "episodes.json").read_text())
    assert len(episodes) == 12
    assert all(row["jobs_started"] == 7 and row["packets"] == 12 for row in episodes)
    assert all(0 <= row["completed_jobs"] <= 7 for row in episodes)
    for artifact in summary["artifacts"]:
        path = out / artifact["path"]
        assert path.stat().st_size == artifact["bytes"]
        assert study.sha256(path) == artifact["sha256"]
    with np.load(out / "raw/P4_0000_0002.npz") as raw:
        assert int(raw["completed_steps"]) == 48
        mask = raw["evaluated"]
        np.testing.assert_array_equal(raw["sample_delta"][mask].mean(axis=1), raw["delta"][mask])
        np.testing.assert_allclose(raw["root_joint_weights"][mask].sum(axis=(1, 2)), 1, atol=1e-12)
    with pytest.raises(FileExistsError, match="no automatic repeat"):
        study.run_study(out, "f" * 40, config)


def test_failed_planner_retains_current_batch_work_and_partial_artifacts(tmp_path, monkeypatch):
    original = study.paired_values
    completed = {}
    def fail_after_model_work(*args, **kwargs):
        original(*args, **kwargs)
        completed.update(kwargs["counters"])
        raise RuntimeError("injected after completed model work")
    monkeypatch.setattr(study, "paired_values", fail_after_model_work)
    out = tmp_path / "failed_fixture"
    config = study.Config(seed=441735, model_seed=442977, contexts=1, batch=1, horizon=48, particles=2)
    with pytest.raises(RuntimeError, match="injected after"):
        study.run_study(out, "f" * 40, config)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "FAILED"
    assert summary["status"]["calibration_fits_completed"] == 2
    assert summary["status"]["completed_arm_contexts"] == 0
    cost, = summary["batch_costs"]
    assert cost["state"] == "FAILED" and cost["steps"] == 0
    assert cost["model"] == completed and completed["model_branch_transitions"] > 0
    assert cost["filtering"]["observations"] == 2
    assert cost["planning_seconds"] > 0 and cost["wall_seconds"] > 0
    assert any(a["path"].endswith(".cost.json") for a in summary["artifacts"])
    assert any(a["path"].endswith("P4_0000_0001.npz") for a in summary["artifacts"])
    for artifact in summary["artifacts"]:
        assert study.sha256(out / artifact["path"]) == artifact["sha256"]
