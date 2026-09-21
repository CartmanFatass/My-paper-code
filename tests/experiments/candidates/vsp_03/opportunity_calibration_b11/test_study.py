import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.vsp_03.opportunity_calibration_b11 import study


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _identity(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def _reference_fixture(monkeypatch, tmp_path):
    root = tmp_path / "references"
    identities = {}
    for seed in study.REFERENCE_SEEDS.values():
        path = root / str(seed) / "fitted_model.json"
        path.parent.mkdir(parents=True)
        _write_json(path, {
            "c": 4.0 + (seed - 21801) / 10,
            "p": 0.4,
            "metadata": {"success": True, "message": "synthetic"},
        })
        identities[seed] = _identity(path)
    monkeypatch.setattr(study, "FROZEN_MODEL_IDENTITIES", identities)
    return root


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


class _Counts:
    instances = []

    def __init__(self):
        self.batches = []
        self.counts = np.zeros((41, 42, 42), dtype=np.int64)
        self.transitions = 16
        self.__class__.instances.append(self)

    def add_batch(self, batch):
        assert set(batch) == {"x", "episode_ids", "times"}
        self.batches.append({key: value.copy() for key, value in batch.items()})


class _Planner:
    def __init__(self, c, p):
        self.c, self.p = c, p
        self.solo = np.zeros((33, 42), dtype=np.float64)
        self.joint = np.zeros((33, 42, 42), dtype=np.float64)

    def actions(self, x, mode):
        assert mode == "joint"
        return np.zeros(len(x), dtype=bool)


def _patch_execution(monkeypatch, fail_fit=False):
    state = {"collection_worlds": [], "evaluation_worlds": [], "fit_calls": 0,
             "evaluated_seeds": set(), "rollouts": 0}
    _Counts.instances = []
    monkeypatch.setattr(study, "COLLECTION_BATCH_SIZE", 2)
    monkeypatch.setattr(study, "EVAL_EPISODES", 2)
    monkeypatch.setattr(study, "EndpointCounts", _Counts)
    monkeypatch.setattr(study, "Planner", _Planner)
    monkeypatch.setattr(study.torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(study.torch, "set_num_interop_threads", lambda n: None)

    def fake_worlds(seed, split, first, count):
        if split == 100:
            assert seed not in state["evaluated_seeds"]
            state["collection_worlds"].append((seed, split, first, count))
        else:
            assert split == 200 and first == 0
            assert state["fit_calls"] > len(state["evaluation_worlds"])
            state["evaluated_seeds"].add(seed)
            state["evaluation_worlds"].append((seed, split, first, count))
        draws = np.full((count, 40, 2), seed + split + first, dtype=np.float64)
        phase = np.arange(count, dtype=np.int64) % 2
        return draws, phase

    def fake_rollout(draws, phase, rule="R0", activity=None, trace=False, scripted=None):
        state["rollouts"] += 1
        n = len(draws)
        if not trace:
            assert rule == "R0" and scripted is None
        elif scripted is None:
            assert rule == "R0"
        else:
            x_for_action = np.zeros((n, 14), dtype=np.float32)
            scripted(np.arange(n), 0, np.zeros(n, dtype=np.int64), x_for_action)
        activity["episodes_started"] += n
        activity["episodes_completed"] += n
        activity["team_ticks"] += n * 40
        activity["target_transitions"] += n * 80
        activity["decision_rows"] += n
        x = np.zeros((n, 14), dtype=np.float32)
        x[:, 1] = 1
        x[:, 6] = 1
        return {
            "x": x,
            "actions": np.zeros(n, dtype=np.float32),
            "episode_ids": np.arange(n, dtype=np.int64),
            "times": np.zeros(n, dtype=np.int64),
            "units": np.full((n, 2), -40, dtype=np.int64),
            "interval_units": np.zeros((n, 40), dtype=np.int64),
            "rows": [_row(i, int(phase[i])) for i in range(n)],
            "trace": [],
        }

    def fake_fit(counts):
        state["fit_calls"] += 1
        assert len(counts.batches) == 4
        if fail_fit:
            raise RuntimeError("literal injected fit failure")
        return {"c": 5.0, "p": 0.3,
                "metadata": {"success": True, "message": "synthetic",
                             "transition_observations": counts.transitions},
                "counts": {"transitions": counts.transitions}}

    def fake_save_panel(out, name, batch, phase):
        _write_json(out / f"{name}.json", batch["rows"])
        np.savez_compressed(
            out / f"{name}_decisions.npz",
            **{key: batch[key] for key in
               ("x", "actions", "episode_ids", "times", "units", "interval_units")},
        )
        return batch["rows"], {"episodes": len(batch["rows"]), "return": -0.2}

    monkeypatch.setattr(study, "worlds", fake_worlds)
    monkeypatch.setattr(study, "rollout", fake_rollout)
    monkeypatch.setattr(study, "fit_model", fake_fit)
    monkeypatch.setattr(study, "save_panel", fake_save_panel)
    return state


def test_complete_mocked_run_uses_only_four_public_r0_batches(monkeypatch, tmp_path):
    references = _reference_fixture(monkeypatch, tmp_path)
    state = _patch_execution(monkeypatch)
    out = tmp_path / "out"
    summary = study.run(out, "launch-sha", reference_root=references)

    assert summary["status"] == "complete"
    assert state["fit_calls"] == 3
    assert summary["fits_started"] == summary["fits_completed"] == summary["fit_calls"] == 3
    assert summary["optimizer_steps"] == summary["gradient_steps"] == 0
    assert summary["neural_model_constructions"] == summary["neural_policy_forwards"] == 0
    assert summary["panels_started"] == summary["panels_completed"] == 9
    assert summary["actual_collection_episodes"] == 24
    assert summary["actual_evaluation_episodes"] == 18
    assert summary["actual_total_episodes"] == 42
    assert state["collection_worlds"] == [
        (seed, 100, first, 2) for seed in study.SEEDS for first in (0, 2, 4, 6)
    ]
    assert state["evaluation_worlds"] == [(seed, 200, 0, 2) for seed in study.SEEDS]
    assert len(_Counts.instances) == 3
    assert all(len(counts.batches) == 4 for counts in _Counts.instances)
    for seed in study.SEEDS:
        with np.load(out / str(seed) / "calibration_public_endpoints.npz") as saved:
            assert saved.files == ["x", "episode_ids", "times"]
            assert saved["episode_ids"].tolist() == list(range(8))
        assert all((out / str(seed) / f"collection_batch_{batch:02d}.npz").exists()
                   for batch in range(4))
    assert set(summary["artifacts"]) == {"config.json", "input_digests.json"}
    assert all("t95" not in value and "equivalence" in value["scope"]
               for value in summary["comparisons"].values())


def test_reference_corruption_stops_before_world_creation(monkeypatch, tmp_path):
    references = _reference_fixture(monkeypatch, tmp_path)
    state = _patch_execution(monkeypatch)
    with (references / "21802" / "fitted_model.json").open("ab") as stream:
        stream.write(b"corruption")
    out = tmp_path / "out-corrupt"

    with pytest.raises(ValueError, match="identity mismatch"):
        study.run(out, "launch-sha", reference_root=references)
    assert state["collection_worlds"] == [] and state["evaluation_worlds"] == []
    retained = json.loads((out / "summary.json").read_text())
    assert retained["technical_failures"][0]["stage"] == "reference_validation"
    assert retained["fits_started"] == retained["panels_started"] == 0


def test_fit_failure_retains_collection_and_never_creates_evaluation(monkeypatch, tmp_path):
    references = _reference_fixture(monkeypatch, tmp_path)
    state = _patch_execution(monkeypatch, fail_fit=True)
    out = tmp_path / "out-failure"

    with pytest.raises(RuntimeError, match="literal injected fit failure"):
        study.run(out, "launch-sha", reference_root=references)
    retained = json.loads((out / "summary.json").read_text())
    block = json.loads((out / "22001" / "summary.json").read_text())
    assert retained["fits_started"] == retained["fit_calls"] == 1
    assert retained["fits_completed"] == 0
    assert retained["actual_collection_episodes"] == 8
    assert retained["actual_evaluation_episodes"] == 0
    assert state["evaluation_worlds"] == []
    assert block["status"] == "incomplete" and block["panels_started"] == 0
    assert block["fit_wall_s"] >= 0
    assert (out / "22001" / "public_endpoint_counts.npz").exists()
    assert retained["technical_failures"] == [{
        "stage": "block", "seed": 22001,
        "error": "RuntimeError('literal injected fit failure')",
    }]


def test_explicit_frozen_model_identities_match_published_b08_files():
    validated = study.validate_references()
    assert list(validated) == [21801, 21802, 21803]
    assert {seed: model["identity"] for seed, model in validated.items()} == \
        study.FROZEN_MODEL_IDENTITIES


def test_aggregate_is_signed_and_descriptive_only():
    blocks = []
    for seed, primary, secondary in zip(study.SEEDS, (-0.1, 0.0, 0.2), (0.2, 0.1, 0.0)):
        blocks.append({
            "seed": seed,
            "status": "complete",
            "comparisons": {
                "O_R0-O_full": {"mean": primary,
                                  "signed_components": {"return": primary}},
                "O_R0-R0": {"mean": secondary,
                              "signed_components": {"return": secondary}},
            },
        })
    result = study.aggregate(blocks)
    assert result["O_R0-O_full"]["per_block"] == [-0.1, 0.0, 0.2]
    assert result["O_R0-O_full"]["mean"] == pytest.approx(1 / 30)
    assert "t95" not in result["O_R0-O_full"]
    assert "no inferential or equivalence label" in result["O_R0-O_full"]["scope"]


def test_runner_refuses_bad_sha_before_output_or_scientific_import(tmp_path):
    root = Path(__file__).resolve().parents[5]
    output = tmp_path / "refused"
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/run_vsp03_opportunity_calibration_b11.py"),
         "--seeds", "22001", "22002", "22003", "--launch-sha", "a" * 40,
         "--out", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "admission" in proc.stderr.lower()
    assert not output.exists()
