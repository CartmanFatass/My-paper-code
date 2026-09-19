"""Synthetic runner checks only; no selected native fit or evaluation."""

import importlib.util
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.last_sighting_a01.publication import (
    EVALUATION_SEED,
    OPTIMIZER_STEPS,
    PANEL_EPISODES,
    TRAIN_EPISODES,
    TRAINING_SEEDS,
)


def load_runner(name):
    path = Path(__file__).resolve().parents[5] / "scripts/run_folr_last_sighting_a01.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def argv(path, out, arm="LAST_SIGHTING", seed=TRAINING_SEEDS[0]):
    return [
        str(path),
        "--arm",
        arm,
        "--seed",
        str(seed),
        "--evaluation-seed",
        str(EVALUATION_SEED),
        "--launch-sha",
        "synthetic-source",
        "--out",
        str(out),
    ]


def install_runtime(monkeypatch, runner, fail_evaluation=False):
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.last_sighting_a01 import artifacts, learner
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection

    facts = {"constructed": [], "seeds": [], "epsilons": [], "collects": 0}

    class FakeActor(torch.nn.Linear):
        def __init__(self, arm):
            super().__init__(1, 1)
            self.arm = arm

    class FakeLearner:
        def __init__(self, arm):
            facts["constructed"].append(arm)
            self.actor = FakeActor(arm)
            self.mixer = torch.nn.Linear(1, 1)
            self.updates = 0

        def update(self, _batch, _episode_num):
            self.updates += 1
            return float(self.updates)

        def save(self, path):
            torch.save({"arm": self.actor.arm, "updates": self.updates}, path)

    def fake_collect(_env, _actor, epsilon):
        facts["collects"] += 1
        if fail_evaluation and facts["collects"] == TRAIN_EPISODES + 2:
            raise RuntimeError("synthetic final failure")
        facts["epsilons"].append(epsilon)
        return {"reward": np.zeros(20, dtype=np.float32)}, 2.0, {
            "births": 1,
            "departures": 2,
        }

    def fake_panel(path, episodes):
        path.write_bytes(b"synthetic-panel")
        return {
            "path": str(path),
            "artifact_sha256": "1" * 64,
            "content_sha256": "2" * 64,
            "arrays": ["reward"],
            "episodes": len(episodes),
            "transitions": len(episodes) * 20,
        }

    monkeypatch.setattr(
        runner, "require_admission", lambda *_args, **_kwargs: {"sha": "synthetic-source"}
    )
    monkeypatch.setattr(learner, "Learner", FakeLearner)
    monkeypatch.setattr(environment, "EntityHistoryEnv", lambda **_kwargs: object())
    monkeypatch.setattr(collection, "collect", fake_collect)
    monkeypatch.setattr(collection, "sample", lambda _replay: {})
    monkeypatch.setattr(collection, "epsilon_at", lambda transitions: transitions / 100000)
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
            lambda seed, label=label: facts["seeds"].append((label, seed)),
        )
    return facts


def test_admission_refusal_precedes_output_and_scientific_construction(tmp_path, monkeypatch):
    path, runner = load_runner("last_sighting_refusal")
    out = tmp_path / "unused"
    monkeypatch.setattr(
        runner,
        "require_admission",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("refused")),
    )
    monkeypatch.setattr("sys.argv", argv(path, out))
    with pytest.raises(RuntimeError, match="refused"):
        runner.main()
    assert not out.exists()


def test_runner_fixed_counts_progress_final_arrays_and_zero_eval_updates(tmp_path, monkeypatch):
    path, runner = load_runner("last_sighting_complete")
    facts = install_runtime(monkeypatch, runner)
    out = tmp_path / "complete"
    monkeypatch.setattr("sys.argv", argv(path, out))
    runner.main()

    summary = json.loads((out / "summary.json").read_text())
    assert facts["constructed"] == ["LAST_SIGHTING"]
    assert summary["status"] == "complete"
    assert (
        summary["training_episodes"],
        summary["training_transitions"],
        summary["optimizer_steps"],
    ) == (TRAIN_EPISODES, TRAIN_EPISODES * 20, OPTIMIZER_STEPS)
    assert (
        summary["evaluation_episodes"],
        summary["evaluation_transitions"],
        summary["evaluation_optimizer_steps"],
    ) == (PANEL_EPISODES, PANEL_EPISODES * 20, 0)
    assert len(summary["training_returns"]) == TRAIN_EPISODES
    assert len(summary["evaluation_returns"]) == PANEL_EPISODES
    rows = (out / "training-progress.jsonl").read_text().splitlines()
    assert len(rows) == TRAIN_EPISODES
    assert sum(json.loads(row)["update_loss"] is not None for row in rows) == OPTIMIZER_STEPS
    assert summary["training_progress"]["rows"] == TRAIN_EPISODES
    assert summary["final_panel"]["episodes"] == PANEL_EPISODES
    assert torch.load(out / "final.pt", weights_only=True)["updates"] == OPTIMIZER_STEPS
    assert facts["seeds"] == [
        (label, seed)
        for seed in (TRAINING_SEEDS[0], EVALUATION_SEED)
        for label in ("python", "numpy", "torch")
    ]
    assert facts["epsilons"][-PANEL_EPISODES:] == [0.0] * PANEL_EPISODES


def test_evaluation_failure_retains_training_and_partial_final_arrays(tmp_path, monkeypatch):
    path, runner = load_runner("last_sighting_failure")
    install_runtime(monkeypatch, runner, fail_evaluation=True)
    out = tmp_path / "failure"
    monkeypatch.setattr("sys.argv", argv(path, out, arm="GENERIC_RETAIN"))
    with pytest.raises(RuntimeError, match="synthetic final failure"):
        runner.main()
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["optimizer_steps"] == OPTIMIZER_STEPS
    assert summary["evaluation_episodes"] == 1
    assert summary["partial_final_panel"]["episodes"] == 1
    assert summary["error"] == "RuntimeError: synthetic final failure"
    assert (out / "final.pt").exists()
    assert (out / "training-progress.jsonl").exists()


@pytest.mark.parametrize("seed", [784102, 784202, 784302])
def test_unselected_seed_refuses_before_admission_or_output(tmp_path, monkeypatch, seed):
    path, runner = load_runner(f"last_sighting_seed_{seed}")
    called = []
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_k: called.append(True))
    out = tmp_path / "unused"
    monkeypatch.setattr("sys.argv", argv(path, out, seed=seed))
    with pytest.raises(SystemExit):
        runner.main()
    assert called == [] and not out.exists()

