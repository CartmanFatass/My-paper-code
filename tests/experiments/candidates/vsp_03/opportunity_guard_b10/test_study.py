import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.vsp_03.opportunity_guard_b10 import study


def _row(world, phase):
    jobs = [
        {"units": -40, "success": 0, "attempt": 0, "failed_attempt": 0,
         "non_submission": 1, "waiting_ticks": 40, "submission_time": -1},
        {"units": -40, "success": 0, "attempt": 0, "failed_attempt": 0,
         "non_submission": 1, "waiting_ticks": 40, "submission_time": -1},
    ]
    row = {
        "world": world,
        "phase_zero_identity": phase,
        "return": -0.2,
        "jobs": jobs,
        "fixed_clocks": 17,
        "pending_clocks": 17,
        "eligible_decisions": 17,
        "blocked_pending": 0,
        "blocked_final_clocks": 0,
    }
    row.update({name: 0 for name in study.ROW_FIELDS[6:]})
    return row


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _identity(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def _source_fixture(tmp_path, episodes=2):
    source = tmp_path / "source"
    for seed in study.SEEDS:
        block = source / str(seed)
        block.mkdir(parents=True)
        phase = np.arange(episodes, dtype=np.int64) % 2
        rows = [_row(world, int(phase[world])) for world in range(episodes)]
        _write_json(block / "fitted_model.json", {
            "c": 4.0, "p": 0.5, "metadata": {"success": True, "message": "synthetic"}
        })
        np.savez_compressed(
            block / "evaluation_worlds.npz",
            draws=np.ones((episodes, 40, 2), dtype=np.float64),
            phase=phase,
        )
        for arm in study.REFERENCE_ARMS:
            _write_json(block / f"{arm}.json", rows)
        x = np.zeros((episodes, 14), dtype=np.float32)
        x[:, 0] = 22 / 40
        x[:, 1] = 1
        x[:, 6] = 1
        x[:, 11] = 1
        np.savez_compressed(
            block / "O_self_decisions.npz",
            x=x,
            actions=np.zeros(episodes, dtype=np.float32),
            episode_ids=np.arange(episodes, dtype=np.int64),
            times=np.full(episodes, 22, dtype=np.int64),
        )
        artifacts = {
            name: _identity(block / name) for name in study.REQUIRED_INPUTS
        }
        reference = study._reference_metrics(rows)
        _write_json(block / "summary.json", {
            "seed": seed,
            "status": "complete",
            "artifacts": artifacts,
            "arms": {arm: reference for arm in study.REFERENCE_ARMS},
            "comparisons": {"O-O_self": {"mean": 0.0}},
        })
    return source


class _SelfWaitPlanner:
    def __init__(self, c, p):
        assert (c, p) == (4.0, 0.5)

    def actions(self, x, mode):
        assert mode == "self"
        return np.zeros(len(x), dtype=bool)


def _fake_rollout(fail_call=None):
    state = {"calls": 0}

    def fake(draws, phase, scripted, activity, trace):
        state["calls"] += 1
        if state["calls"] == fail_call:
            raise RuntimeError("literal injected guard failure")
        n = len(draws)
        x = np.zeros((n, 14), dtype=np.float32)
        x[:, 0] = 22 / 40
        x[:, 1] = 1
        x[:, 6] = 1
        x[:, 11] = 1
        actions = scripted(np.arange(n), 22, np.zeros(n, dtype=np.int64), x)
        assert np.all(actions)
        activity["episodes_started"] += n
        activity["episodes_completed"] += n
        activity["team_ticks"] += n * 40
        activity["target_transitions"] += n * 80
        activity["decision_rows"] += n
        return {
            "x": x,
            "actions": actions.astype(np.float32),
            "episode_ids": np.arange(n, dtype=np.int64),
            "times": np.full(n, 22, dtype=np.int64),
            "units": np.full((n, 2), -40, dtype=np.int64),
            "interval_units": np.zeros((n, 40), dtype=np.int64),
            "rows": [_row(i, int(phase[i])) for i in range(n)],
            "trace": [],
        }

    return fake


def _fake_save_panel(out, name, batch, phase):
    assert name == "guard"
    _write_json(out / "guard.json", batch["rows"])
    np.savez_compressed(
        out / "guard_decisions.npz",
        **{key: batch[key] for key in
           ("x", "actions", "episode_ids", "times", "units", "interval_units")},
    )
    return batch["rows"], study._reference_metrics(batch["rows"])


def _patch_synthetic_execution(monkeypatch, fail_call=None):
    monkeypatch.setattr(study, "EVAL_EPISODES", 2)
    monkeypatch.setattr(study, "Planner", _SelfWaitPlanner)
    monkeypatch.setattr(study, "rollout", _fake_rollout(fail_call))
    monkeypatch.setattr(study, "save_panel", _fake_save_panel)
    monkeypatch.setattr(study.torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(study.torch, "set_num_interop_threads", lambda n: None)


def test_guard_actions_changes_only_t22_with_partner_pending():
    class Planner:
        def actions(self, x, mode):
            assert mode == "self"
            return np.array([False, False, False, True, False])

    x = np.zeros((5, 14), dtype=np.float32)
    x[:, 0] = np.array([20, 22, 22, 22, 24]) / 40
    x[:, 11] = np.array([1, 1, 0, 1, 1])
    x[:, 5] = 0  # Readiness is deliberately irrelevant.
    assert study.guard_actions(Planner(), x).tolist() == [False, True, False, True, False]


def test_successful_synthetic_run_retains_all_worlds_and_zero_fit_cost(monkeypatch, tmp_path):
    _patch_synthetic_execution(monkeypatch)
    source = _source_fixture(tmp_path)
    out = tmp_path / "out"
    summary = study.run(out, "launch-sha", source_run=source)

    assert summary["status"] == "complete"
    assert summary["fits_started"] == summary["fits_completed"] == 0
    assert summary["optimizer_steps"] == summary["gradient_steps"] == 0
    assert summary["panels_started"] == summary["panels_completed"] == 3
    assert summary["actual_evaluation_episodes"] == 6
    assert summary["actual_team_ticks"] == 240
    assert summary["actual_target_transitions"] == 480
    assert summary["actual_planning_reconstructions"] == 3
    assert summary["reference_panels_replayed"] == 0
    assert set(summary["artifacts"]) == {"config.json", "input_digests.json"}
    assert (out / "input_digests.json").exists()
    for seed in study.SEEDS:
        disagreements = json.loads(
            (out / str(seed) / "first_guard_self_disagreements.json").read_text()
        )
        assert len(disagreements) == 2
        assert all(row["first_disagreement"]["t"] == 22 for row in disagreements)
        assert all(row["first_disagreement"]["direction"] == "guard_SUBMIT_self_WAIT"
                   for row in disagreements)
        paired = json.loads((out / str(seed) / "paired_differences.json").read_text())
        assert [row["world"] for row in paired] == [0, 1]


def test_corrupt_input_refuses_before_any_evaluation(monkeypatch, tmp_path):
    _patch_synthetic_execution(monkeypatch)
    source = _source_fixture(tmp_path)
    with (source / "21802" / "evaluation_worlds.npz").open("ab") as stream:
        stream.write(b"corruption")
    monkeypatch.setattr(study, "rollout", lambda *args, **kwargs: pytest.fail("rollout started"))
    out = tmp_path / "out-corrupt"

    with pytest.raises(ValueError, match="artifact mismatch"):
        study.run(out, "launch-sha", source_run=source)
    retained = json.loads((out / "summary.json").read_text())
    assert retained["panels_started"] == retained["panels_completed"] == 0
    assert retained["technical_failures"][0]["stage"] == "input_validation"
    assert not any((out / str(seed)).exists() for seed in study.SEEDS)


def test_panel_failure_retains_completed_and_started_counts(monkeypatch, tmp_path):
    _patch_synthetic_execution(monkeypatch, fail_call=2)
    source = _source_fixture(tmp_path)
    out = tmp_path / "out-failure"

    with pytest.raises(RuntimeError, match="literal injected guard failure"):
        study.run(out, "launch-sha", source_run=source)
    retained = json.loads((out / "summary.json").read_text())
    assert retained["fits_started"] == retained["fits_completed"] == 0
    assert retained["panels_started"] == 2
    assert retained["panels_completed"] == 1
    assert retained["technical_failures"] == [{
        "stage": "guard_panel", "seed": 21802,
        "error": "RuntimeError('literal injected guard failure')",
    }]
    failed = json.loads((out / "21802" / "summary.json").read_text())
    assert failed["status"] == "incomplete"
    assert failed["panels_started"] == 1 and failed["panels_completed"] == 0


def test_aggregate_uses_signed_capture_fraction_and_fixed_majority_rule():
    blocks = []
    for seed, guard_self, fixed in zip(study.SEEDS, (0.006, 0.007, 0.005), (0.01, 0.01, 0.01)):
        comparisons = {}
        for key, value in (("guard-O_self", guard_self), ("O-guard", fixed - guard_self),
                           ("guard-G", 0.02)):
            comparisons[key] = {"mean": value, "signed_components": {"return": value}}
        blocks.append({"seed": seed, "status": "complete", "comparisons": comparisons,
                       "fixed_O-O_self": {"mean": fixed}})
    comparisons, reading = study.aggregate(blocks)
    assert comparisons["guard-O_self"]["mean"] == pytest.approx(0.006)
    assert reading["signed_capture_fraction"] == pytest.approx(0.6)
    assert reading["label"] == "MAJORITY_EXPLANATION"


def test_runner_refuses_bad_sha_before_output_or_scientific_import(tmp_path):
    root = Path(__file__).resolve().parents[5]
    output = tmp_path / "refused"
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/run_vsp03_opportunity_guard_b10.py"),
         "--seeds", "21801", "21802", "21803", "--launch-sha", "a" * 40,
         "--out", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "admission" in proc.stderr.lower()
    assert not output.exists()
