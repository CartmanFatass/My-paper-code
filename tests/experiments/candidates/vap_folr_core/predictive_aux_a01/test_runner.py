import importlib.util
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.predictive_aux_a01.publication import (
    EVALUATION_SEED,
    OPTIMIZER_STEPS,
    PANEL_EPISODES,
    PROBE_SEED,
    TRAIN_EPISODES,
    TRAINING_SEED,
)
from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import collect


def load_runner(name):
    path = Path(__file__).resolve().parents[5] / "scripts/run_folr_predictive_aux_a01.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def argv(path, out, arm="DETACHED"):
    return [
        str(path), "--arm", arm, "--seed", str(TRAINING_SEED),
        "--evaluation-seed", str(EVALUATION_SEED), "--probe-seed", str(PROBE_SEED),
        "--launch-sha", "synthetic-source", "--out", str(out),
    ]


def install_synthetic_runtime(
    monkeypatch, runner, *, nonfinite_update=False, nonfinite_final_panel=False
):
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.predictive_aux_a01 import artifacts, learner
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection

    facts = {"seed_calls": [], "epsilons": [], "constructed": [], "panel_calls": 0}

    class FakeLearner:
        def __init__(self, arm):
            facts["constructed"].append(arm)
            self.actor = torch.nn.Linear(1, 1)
            self.actor.arm = "GENERIC_RETAIN"
            self.mixer = torch.nn.Linear(1, 1)
            self.predictor = torch.nn.Linear(1, 1)
            self.updates = self.predictor_updates = 0

        def update(self, _batch, _episode_num):
            self.updates += 1
            self.predictor_updates += 1
            return {
                "native_loss": 1.0,
                "prediction_mse": float("nan") if nonfinite_update else 1.0,
                "prediction_count": 1,
                "prediction_sum": 1.0,
                "prediction_square_sum": 1.0,
                "target_sum": 0.0,
                "target_square_sum": 0.0,
                "error_sum": 1.0,
                "error_square_sum": 1.0,
            }

        def save(self, output):
            torch.save(
                {
                    "actor": self.actor.state_dict(),
                    "mixer": self.mixer.state_dict(),
                    "predictor": self.predictor.state_dict(),
                    "updates": self.updates,
                    "predictor_updates": self.predictor_updates,
                },
                output,
            )

    def fake_collect(_env, _actor, epsilon):
        facts["epsilons"].append(epsilon)
        return {"reward": np.zeros(20, dtype=np.float32)}, 2.0, {
            "births": 1,
            "departures": 0,
        }

    def fake_panel(output, episodes, _actor, _predictor):
        output.write_bytes(b"synthetic-panel")
        assert len(episodes) == PANEL_EPISODES
        facts["panel_calls"] += 1
        prediction_mse = (
            float("nan") if nonfinite_final_panel and facts["panel_calls"] == 1 else 1.0
        )
        return {
            "path": str(output),
            "artifact_sha256": "1" * 64,
            "input_sha256": "2" * 64,
            "panel_sha256": "3" * 64,
            "prediction": {"count": PANEL_EPISODES, "mse": prediction_mse},
            "post_event_window": {"tick_count": 0},
            "episodes": PANEL_EPISODES,
            "transitions": PANEL_EPISODES * 20,
        }

    monkeypatch.setattr(
        runner, "require_admission", lambda *_a, **_kw: {"sha": "synthetic-source"}
    )
    monkeypatch.setattr(learner, "Learner", FakeLearner)
    monkeypatch.setattr(environment, "EntityHistoryEnv", lambda **_kw: object())
    monkeypatch.setattr(collection, "collect", fake_collect)
    monkeypatch.setattr(collection, "sample", lambda _replay: {})
    monkeypatch.setattr(collection, "epsilon_at", lambda ticks: ticks / 100000)
    monkeypatch.setattr(artifacts, "write_panel", fake_panel)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _value: None)
    for label, module, name in (
        ("python", random, "seed"),
        ("numpy", np.random, "seed"),
        ("torch", torch, "manual_seed"),
    ):
        monkeypatch.setattr(
            module,
            name,
            lambda seed, label=label: facts["seed_calls"].append((label, seed)),
        )
    return facts


def test_runner_refuses_before_output_or_scientific_construction(tmp_path, monkeypatch):
    path, runner = load_runner("folr_predictive_aux_refusal_test")
    out = tmp_path / "unused"
    monkeypatch.setattr(
        runner, "require_admission", lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("refused"))
    )
    monkeypatch.setattr("sys.argv", argv(path, out))
    with pytest.raises(RuntimeError, match="refused"):
        runner.main()
    assert not out.exists()


def test_runner_fixed_counts_phase_seeds_and_no_evaluation_updates(tmp_path, monkeypatch):
    path, runner = load_runner("folr_predictive_aux_synthetic_test")
    facts = install_synthetic_runtime(monkeypatch, runner)

    out = tmp_path / "output"
    monkeypatch.setattr("sys.argv", argv(path, out, arm="COUPLED"))
    runner.main()
    summary = json.loads((out / "summary.json").read_text())
    assert facts["constructed"] == ["COUPLED"]
    assert summary["status"] == "complete"
    assert (
        summary["training_episodes"], summary["training_transitions"],
        summary["native_optimizer_steps"], summary["predictor_optimizer_steps"],
    ) == (TRAIN_EPISODES, TRAIN_EPISODES * 20, OPTIMIZER_STEPS, OPTIMIZER_STEPS)
    assert (
        summary["final_episodes"], summary["final_transitions"],
        summary["probe_episodes"], summary["probe_transitions"],
        summary["evaluation_optimizer_steps"],
    ) == (PANEL_EPISODES, PANEL_EPISODES * 20, PANEL_EPISODES, PANEL_EPISODES * 20, 0)
    assert len(summary["training_returns"]) == TRAIN_EPISODES
    assert len(summary["final_returns"]) == len(summary["probe_returns"]) == PANEL_EPISODES
    assert len(facts["epsilons"]) == TRAIN_EPISODES + 2 * PANEL_EPISODES
    assert facts["epsilons"][-2 * PANEL_EPISODES:-PANEL_EPISODES] == [
        0.0
    ] * PANEL_EPISODES
    assert facts["epsilons"][-PANEL_EPISODES:] == [1.0] * PANEL_EPISODES
    assert facts["seed_calls"] == [
        (label, seed)
        for seed in (TRAINING_SEED, EVALUATION_SEED, PROBE_SEED)
        for label in ("python", "numpy", "torch")
    ]
    update_rows = (out / "training-updates.jsonl").read_text().splitlines()
    assert len(update_rows) == OPTIMIZER_STEPS
    assert summary["training_update_artifact"]["rows"] == OPTIMIZER_STEPS
    checkpoint = torch.load(out / "final.pt", weights_only=True)
    assert checkpoint["updates"] == checkpoint["predictor_updates"] == OPTIMIZER_STEPS


def test_nonfinite_update_retains_actual_counts_and_invalid_diagnostic(tmp_path, monkeypatch):
    path, runner = load_runner("folr_predictive_aux_nonfinite_update_test")
    install_synthetic_runtime(monkeypatch, runner, nonfinite_update=True)
    out = tmp_path / "update-failure"
    monkeypatch.setattr("sys.argv", argv(path, out))
    with pytest.raises(ValueError, match="Out of range float values"):
        runner.main()

    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["training_episodes"] == 32
    assert summary["training_transitions"] == 640
    assert summary["native_optimizer_steps"] == summary["predictor_optimizer_steps"] == 1
    assert summary["invalid_update_diagnostic"]["prediction_mse"] is None
    assert "$.invalid_update_diagnostic.prediction_mse" in summary["invalid_nonfinite_paths"]
    assert summary["error"].startswith("ValueError: Out of range float values")


def test_nonfinite_final_panel_is_published_incomplete_with_invalid_path(tmp_path, monkeypatch):
    path, runner = load_runner("folr_predictive_aux_nonfinite_panel_test")
    install_synthetic_runtime(monkeypatch, runner, nonfinite_final_panel=True)
    out = tmp_path / "panel-failure"
    monkeypatch.setattr("sys.argv", argv(path, out))
    with pytest.raises(ValueError, match="Out of range float values"):
        runner.main()

    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["native_optimizer_steps"] == OPTIMIZER_STEPS
    assert summary["predictor_optimizer_steps"] == OPTIMIZER_STEPS
    assert summary["final_episodes"] == summary["probe_episodes"] == PANEL_EPISODES
    assert summary["final_panel"]["prediction"]["mse"] is None
    assert "$.final_panel.prediction.mse" in summary["invalid_nonfinite_paths"]
    assert summary["error"].startswith("ValueError: Out of range float values")


def test_common_seed_uniform_collection_is_byte_identical_across_policy_values():
    class SyntheticEnv:
        max_steps = 20

        def reset(self):
            self.t = 0
            self.birth = np.ones(5, dtype=bool)
            self.departure = np.zeros(5, dtype=bool)
            self.continuation = np.zeros(5, dtype=bool)
            self.event = False

        def observation(self, previous):
            return {
                "entities": np.full((5, 1), self.t, dtype=np.float32),
                "entity_mask": np.zeros(5, dtype=bool),
                "continuation": self.continuation.copy(),
                "birth": self.birth.copy(),
                "departure": self.departure.copy(),
                "event": np.asarray(self.event),
                "previous_action": np.eye(5, dtype=np.float32)[previous],
            }

        def step(self, actions):
            self.t += 1
            self.birth[:] = False
            self.continuation[:] = True
            return np.float64(actions.sum()), self.t == self.max_steps, {}

    class SyntheticActor:
        arm = "GENERIC_RETAIN"

        def __init__(self, sign):
            self.sign = sign

        def __call__(self, batch, hidden=None):
            batch_size, steps = batch["entities"].shape[:2]
            q = torch.arange(25, dtype=torch.float32).reshape(1, 1, 5, 5)
            q = self.sign * q.expand(batch_size, steps, -1, -1)
            state = torch.zeros(batch_size, steps, 5, 1)
            return q, state

    torch.manual_seed(2783101)
    first, first_score, first_counts = collect(SyntheticEnv(), SyntheticActor(1), 1.0)
    torch.manual_seed(2783101)
    second, second_score, second_counts = collect(SyntheticEnv(), SyntheticActor(-1), 1.0)
    assert first.keys() == second.keys()
    assert all(
        first[key].dtype == second[key].dtype and first[key].tobytes() == second[key].tobytes()
        for key in first
    )
    assert first_score == second_score and first_counts == second_counts
