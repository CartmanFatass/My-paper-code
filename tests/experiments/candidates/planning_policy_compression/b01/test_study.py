import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.finite_model_decision_value.b01.belief import take_local
from experiments.candidates.finite_model_decision_value.b01.host import CrossingHost, Worlds
from experiments.candidates.finite_model_decision_value.b01.study import Config as OldConfig
from experiments.candidates.finite_model_decision_value.b01.study import collect_calibration as old_calibration
from experiments.candidates.finite_model_decision_value.b01.study import evaluate_batch
from experiments.candidates.planning_policy_compression.b01.model import Student, features
from experiments.candidates.planning_policy_compression.b01.study import (
    Config, calibration, episode_batch, run_study, stage_weights, train_stage,
)


@pytest.fixture
def tiny():
    return Config(initial_contexts=1, rollout_contexts=1, evaluation_contexts=1,
                  horizon=48, batch=1, epochs=(1, 1), train_batch=2, particles=2,
                  block_seeds=(1401, 1402), block_model_seeds=(1501, 1502),
                  evaluation_seed=1403, evaluation_model_seed=1503,
                  collect_phases=(170, 171, 172), evaluation_phases=(180, 181, 182))


def test_calibration_prefix_and_lawful_features(tiny):
    ids = (0, 1)
    theta, pos, q, _, moves, _, _ = calibration(1401, 170, ids)
    old_theta, old_pos = old_calibration(OldConfig(seed=1401, calibration_phase=170), ids)
    np.testing.assert_array_equal(theta, old_theta)
    np.testing.assert_array_equal(pos, old_pos[:, :5])
    host = CrossingHost(Worlds.make(1401, 171, ids, 48, theta))
    local = take_local(host, 0)
    encoded = features(local, moves)
    assert encoded.shape == (2, 35)
    assert np.all(encoded[:, 7:14] == 0)  # invalid sent payload
    assert np.all(encoded[:, 14:21] == 0)  # invalid received payload
    assert np.all(encoded[:, -4:] == moves)
    with pytest.raises(ValueError):
        features(local, np.column_stack((moves, theta)))
    assert q.shape == (2, 4)


def test_teacher_equal_and_shadow_updates(tmp_path, tiny):
    ids = (0,)
    theta, _, q, _, moves, _, _ = calibration(1401, 170, ids)
    rows, data, cost = episode_batch(ids, theta, q, moves, seed=1401, phase=171,
        model_seed=1501, model_phase=172, config=tiny, arm="TEACHER", labels=True,
        trace_path=tmp_path / "teacher.npz")
    reference, trace, old_cost = evaluate_batch(
        OldConfig(seed=1401, model_seed=1501, horizon=48, particles=2,
                  evaluation_phase=171, model_phase=172), ids, theta, q,
        "P32", tmp_path / "old.npz")
    assert rows[0]["completed_jobs"] == reference[0]["completed_jobs"]
    assert rows[0]["packets"] == reference[0]["packets"]
    np.testing.assert_array_equal(data["mask"].reshape(1, 2, 48).any(1)[0], trace["eligible"][0])
    for tick in range(48):
        sender = tick % 2
        if trace["eligible"][0, tick]:
            assert data["delta"].reshape(1, 2, 48)[0, sender, tick] == trace["delta"][0, tick]
            assert data["mc_se"].reshape(1, 2, 48)[0, sender, tick] == trace["mc_se"][0, tick]
            assert bool(data["y"].reshape(1, 2, 48)[0, sender, tick]) == bool(trace["requested"][0, tick])
    assert cost["model"] == old_cost["model"]
    assert cost["filter"]["observations"] == 2 * 48
    saved_cost = json.loads((tmp_path / "teacher.cost.json").read_text())
    assert saved_cost["wall_seconds"] == cost["wall_seconds"]
    assert saved_cost["cpu_seconds"] == cost["cpu_seconds"]
    assert saved_cost["timing"] == cost["timing"]
    assert cost["timing"]["trace_save_seconds"] > 0
    with np.load(tmp_path / "teacher.npz") as trace_data:
        np.testing.assert_array_equal(trace_data["x"], data["x"])
        np.testing.assert_array_equal(trace_data["mask"], data["mask"])
        np.testing.assert_array_equal(trace_data["mc_se"], data["mc_se"])
    # On student actions the teacher is still asked only at actual optional roots.
    torch.manual_seed(1)
    student = Student()
    _, labeled, student_cost = episode_batch(ids, theta, q, moves, seed=1401, phase=171,
        model_seed=1501, model_phase=172, config=tiny, arm="BC_ROLLIN", model=student, labels=True)
    assert student_cost["filter"]["observations"] == 2 * 48
    assert int(labeled["mask"].sum()) == student_cost["optional_roots"]
    _, _, deployment_cost = episode_batch(ids, theta, q, moves, seed=1401, phase=171,
        model_seed=1501, model_phase=172, config=tiny, arm="BC0", model=student)
    assert deployment_cost["model"] == {}
    assert deployment_cost["filter"] == {}


def test_recurrence_weights_and_update_accounting():
    model = Student()
    sequence = torch.randn(2, 8, 35)
    full, _ = model(sequence)
    memory = None
    pieces = []
    for t in range(8):
        logit, memory = model(sequence[:, t:t + 1], memory)
        pieces.append(logit)
    torch.testing.assert_close(full, torch.cat(pieces, dim=1), rtol=1e-5, atol=1e-6)
    fresh, _ = model(sequence)
    torch.testing.assert_close(full, fresh)
    data = dict(x=np.zeros((2, 48, 35), np.float32), y=np.zeros((2, 48), np.float32),
                mask=np.zeros((2, 48), bool), delta=np.zeros((2, 48), np.float32))
    data["mask"][:, 0] = True
    data["delta"][0, 0] = .5
    w, info = stage_weights(data)
    assert info["weight_mean"] == pytest.approx(1)
    assert info["weight_min"] > 0
    data["delta"].fill(0)
    assert np.all(stage_weights(data)[0][data["mask"]] == 1)
    initial = {key: value.clone() for key, value in model.state_dict().items()}
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    curves, updates, rows, _ = train_stage(model, optimizer, data, weighted=False,
        model_seed=11, block=0, stage=1, epochs=1, batch=2, initial=initial)
    assert updates == 1 and rows == 96
    assert curves[-1]["parameter_movement_l2"] > 0


def test_tiny_complete_study(tmp_path, tiny):
    result = run_study(tmp_path / "run", "fixture-sha", tiny)
    assert result["state"] == "COMPLETE"
    counts = result["counts"]
    assert counts["policy_fits_started"] == counts["policy_fits_completed"] == 4
    assert counts["optimizer_updates"] == 16
    assert counts["processed_agent_time_rows"] == 4 * 2 * 48 * (1 + 3)
    assert counts["collection_team_ticks"] == 2 * 3 * 48
    assert counts["evaluation_team_ticks"] == 6 * 48
    assert result["config"]["parameter_count"] == 27329
    assert result["model_branch_transition_upper"] == (2 * 3 * 48 + 48) * 2 * 2 * 32
    assert len(result["fits"]) == 4
    assert result["fits"][0]["initial_state_sha256"] == result["fits"][1]["initial_state_sha256"]
    assert len(result["endpoint_diagnostics"]) == 8
    assert len(json.loads((tmp_path / "run" / "per_context.json").read_text())) == 1
    assert all(fit["parameter_movement_l2"] > 0 for fit in result["fits"])
    assert (tmp_path / "run" / "raw" / "training_block0.npz").is_file()
    assert (tmp_path / "run" / "raw" / "evaluation_AF_0000.episodes.json").is_file()
    with pytest.raises(FileExistsError):
        run_study(tmp_path / "run", "fixture-sha", tiny)


def test_native_files_allowed_and_partial_batch_preserved(tmp_path, tiny, monkeypatch):
    import experiments.candidates.planning_policy_compression.b01.study as study
    out = tmp_path / "admitted"
    out.mkdir()
    (out / "native-manifest.json").write_text("{}")
    theta, _, q, _, moves, _, _ = calibration(1401, 170, (0,))
    real_query = study.paired_values
    calls = [0]
    def fail(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 2:
            raise RuntimeError("fixture query failure")
        return real_query(*args, **kwargs)
    monkeypatch.setattr(study, "paired_values", fail)
    trace = tmp_path / "partial.npz"
    with pytest.raises(RuntimeError, match="fixture query failure"):
        episode_batch((0,), theta, q, moves, seed=1401, phase=171,
            model_seed=1501, model_phase=172, config=tiny, arm="TEACHER",
            labels=True, trace_path=trace)
    cost = json.loads(trace.with_suffix(".cost.json").read_text())
    assert cost["state"] == "FAILED"
    assert cost["observed_ticks"] == 2 and cost["executed_ticks"] == 1
    assert cost["feature_ticks"] == 2
    assert trace.is_file()
    with np.load(trace) as partial:
        assert partial["x"].shape == (2, 2, 35)
        assert partial["mask"].shape == (2, 2)
        assert partial["mask"].sum() == 1
        assert partial["mask"][0, 0]
        assert not partial["mask"][:, 1].any()
        assert partial["delta"].shape == (2, 2)
        assert partial["mc_se"].shape == (2, 2)
    # No scientific marker exists, so a native launcher-created manifest is allowed.
    calls[0] = 1
    with pytest.raises(RuntimeError, match="fixture query failure"):
        run_study(out, "fixture-sha", tiny)
    assert json.loads((out / "summary.json").read_text())["state"] == "FAILED"


def test_entry_refuses_before_science(tmp_path):
    root = Path(__file__).resolve().parents[5]
    output = tmp_path / "refused"
    env = os.environ.copy()
    env.pop("HMASD_LAUNCH_ADMISSION", None)
    process = subprocess.run([sys.executable, str(root / "scripts/run_ppc_b01.py"),
        "--out", str(output), "--launch-sha", "unadmitted"],
        cwd=root, env=env, capture_output=True, text=True)
    assert process.returncode != 0
    assert not output.exists()
