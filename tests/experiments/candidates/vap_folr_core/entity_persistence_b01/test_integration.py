"""Focused synthetic checks for the complete persistence B01 integration."""

import importlib.util
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_persistence_b01.learner import (
    Learner,
)
from experiments.candidates.vap_folr_core.entity_persistence_b01.publication import (
    EVALUATION_SEED,
    OBJECT,
    TRAINING_SEED,
    attach_primary,
    pair_result,
)


@pytest.fixture(scope="module", autouse=True)
def one_thread():
    torch.set_num_threads(1)


def observations(t=21):
    torch.manual_seed(713)
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(2, t, 1, 1)
    visible[:, :, 0, 1] = True
    continuation = torch.ones(2, t, 5, dtype=torch.bool)
    continuation[:, 0] = False
    seen = torch.zeros_like(visible)
    age = torch.zeros_like(visible, dtype=torch.int16)
    for step in range(t):
        previous = seen[:, step - 1] if step else torch.zeros_like(seen[:, 0])
        seen[:, step] = previous | visible[:, step]
        if step:
            age[:, step] = torch.where(previous, age[:, step - 1] + 1, 0)
        age[:, step].masked_fill_(visible[:, step], 0)
    return {
        "entities": torch.rand(2, t, 5, 4),
        "previous_action": torch.zeros(2, t, 5, 5),
        "entity_mask": torch.zeros(2, t, 5, dtype=torch.bool),
        "visible": visible,
        "obs_mask": ~visible,
        "seen": seen,
        "age": age,
        "birth": ~continuation,
        "continuation": continuation,
        "departure": torch.zeros_like(continuation),
        "event": torch.zeros(2, t, dtype=torch.bool),
    }


def endpoint(arm, value=0.0, **changes):
    result = {
        "object": OBJECT,
        "arm": arm,
        "status": "complete",
        "training_seed": TRAINING_SEED,
        "evaluation_seed": EVALUATION_SEED,
        "training_episodes": 5000,
        "training_ticks": 100000,
        "optimizer_steps": 4969,
        "evaluation_episodes": 128,
        "evaluation_ticks": 2560,
        "evaluation_returns": [value] * 128,
        "launch_sha": "synthetic-source-revision",
    }
    result.update(changes)
    return result


def test_fresh_constructors_align_common_actor_mixer_and_external_rng():
    torch.manual_seed(914)
    generic = Learner("AUGMENTED_CURRENT_ONLY")
    after_generic = torch.random.get_rng_state()
    torch.manual_seed(914)
    augmented = Learner("AUGMENTED_PERSISTENT")
    assert torch.equal(after_generic, torch.random.get_rng_state())
    for module in ("fc1", "attn", "fc2", "rnn", "entity_fc1", "entity_rnn", "entity_token", "entity_attn", "entity_fc2", "head"):
        expected = getattr(generic.actor, module).state_dict()
        actual = getattr(augmented.actor, module).state_dict()
        for name in expected:
            torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=0)
    for name, value in generic.mixer.state_dict().items():
        torch.testing.assert_close(value, augmented.mixer.state_dict()[name], rtol=0, atol=0)
    assert generic.actor.arm == "AUGMENTED_CURRENT_ONLY"
    assert augmented.actor.arm == "AUGMENTED_PERSISTENT"
    assert generic.actor is not generic.target_actor
    assert augmented.actor is not augmented.target_actor
    assert generic.mixer is not generic.target_mixer
    assert augmented.mixer is not augmented.target_mixer
    assert generic.actor is not augmented.actor
    assert generic.optimiser is not augmented.optimiser


@pytest.mark.parametrize("arm", ["AUGMENTED_PERSISTENT", "AUGMENTED_CURRENT_ONLY"])
def test_augmented_real_update_target_ownership_and_checkpoint(tmp_path, arm):
    torch.manual_seed(912)
    learner = Learner(arm)
    batch = observations()
    batch.update(
        actions=torch.zeros(2, 20, 5, dtype=torch.long),
        reward=torch.ones(2, 20),
        terminated=torch.zeros(2, 20),
    )
    batch["terminated"][:, -1] = 1
    online_before = learner.actor.head.weight.detach().clone()
    target_before = learner.target_actor.head.weight.detach().clone()
    loss = learner.update(batch, 1)
    assert np.isfinite(loss) and learner.updates == 1
    assert not torch.equal(online_before, learner.actor.head.weight)
    torch.testing.assert_close(target_before, learner.target_actor.head.weight)
    assert learner.actor.head.weight.data_ptr() != learner.target_actor.head.weight.data_ptr()

    checkpoint = tmp_path / "final.pt"
    learner.save(checkpoint)
    saved = torch.load(checkpoint, weights_only=True)
    assert saved["arm"] == arm
    assert saved["updates"] == 1 and saved["optimiser"]["state"]
    torch.testing.assert_close(saved["actor"]["head.weight"], learner.actor.head.weight)
    torch.testing.assert_close(
        saved["target_actor"]["head.weight"], learner.target_actor.head.weight
    )


@pytest.mark.parametrize(
    "difference,rule",
    [
        (1.1, "PERSISTENT_ABOVE_MEI"),
        (1.0, "WITHIN_MEI"),
        (-1.0, "WITHIN_MEI"),
        (-1.1, "CURRENT_ONLY_ABOVE_MEI"),
    ],
)
def test_primary_strict_boundaries_and_binding(difference, rule):
    result = pair_result(
        endpoint("AUGMENTED_CURRENT_ONLY"),
        endpoint("AUGMENTED_PERSISTENT", difference),
    )
    assert result["persistent_minus_current_only"] == pytest.approx(difference)
    assert result["rule"] == rule
    assert result["paired_difference_se"] is None
    assert result["current_only"]["negative_count"] == 0
    assert result["persistent"]["negative_count"] == (128 if difference < 0 else 0)


@pytest.mark.parametrize(
    "generic",
    [
        None,
        endpoint("AUGMENTED_CURRENT_ONLY", status="incomplete"),
        endpoint("AUGMENTED_CURRENT_ONLY", object="FOLR_ENTITY_HISTORY_B03_781501"),
        endpoint("AUGMENTED_CURRENT_ONLY", evaluation_returns=[0.0] * 127),
        endpoint("AUGMENTED_CURRENT_ONLY", launch_sha="foreign-source"),
        endpoint("AUGMENTED_CURRENT_ONLY", evaluation_returns=[float("nan")] * 128),
    ],
)
def test_missing_incomplete_or_foreign_generic_preserves_augmented_facts(generic):
    augmented = endpoint("AUGMENTED_PERSISTENT", 2.0)
    attach_primary(augmented, generic)
    assert augmented["status"] == "complete"
    assert augmented["evaluation_returns"] == [2.0] * 128
    assert augmented["pair_primary"] is None
    assert "no A-minus-Z polarity" in augmented["pair_primary_unavailable"]


class FakeActor(torch.nn.Module):
    def __init__(self, arm):
        super().__init__()
        self.arm = arm
        self.weight = torch.nn.Parameter(torch.tensor([1.0]))


class FakeLearner:
    constructed = []

    def __init__(self, arm):
        self.constructed.append(arm)
        self.actor = FakeActor(arm)

    def update(self, batch, episode_num):
        return 0.0

    def save(self, path):
        torch.save({"arm": self.actor.arm, "updates": 4969}, path)


def test_runner_executes_complete_augmented_path_and_keeps_foreign_comparator(
    tmp_path, monkeypatch
):
    runner_path = Path(__file__).resolve().parents[5] / (
        "scripts/run_folr_entity_persistence_b01.py"
    )
    spec = importlib.util.spec_from_file_location("folr_augmentation_runner_test", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    from experiments.candidates.vap_folr_core.entity_persistence_b01 import learner
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection

    FakeLearner.constructed = []
    monkeypatch.setattr(learner, "Learner", FakeLearner)
    monkeypatch.setattr(environment, "EntityHistoryEnv", lambda **_: object())
    monkeypatch.setattr(
        collection,
        "collect",
        lambda env, actor, epsilon: ({}, 2.0, {}),
    )
    monkeypatch.setattr(collection, "sample", lambda replay: {})
    monkeypatch.setattr(collection, "epsilon_at", lambda ticks: 0.0)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _: None)
    seed_calls = []
    monkeypatch.setattr(random, "seed", lambda seed: seed_calls.append(("python", seed)))
    monkeypatch.setattr(np.random, "seed", lambda seed: seed_calls.append(("numpy", seed)))
    monkeypatch.setattr(torch, "manual_seed", lambda seed: seed_calls.append(("torch", seed)))

    foreign = tmp_path / "foreign_generic.json"
    foreign.write_text(json.dumps(endpoint("AUGMENTED_CURRENT_ONLY", object="old-object")))
    out = tmp_path / "augmented"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(runner_path),
            "--arm",
            "AUGMENTED_PERSISTENT",
            "--seed",
            str(TRAINING_SEED),
            "--evaluation-seed",
            str(EVALUATION_SEED),
            "--launch-sha",
            "synthetic-source-revision",
            "--out",
            str(out),
            "--current-only-summary",
            str(foreign),
        ],
    )
    runner.main()
    summary = json.loads((out / "summary.json").read_text())
    checkpoint = torch.load(out / "final.pt", weights_only=True)
    assert FakeLearner.constructed == ["AUGMENTED_PERSISTENT"]
    assert checkpoint == {"arm": "AUGMENTED_PERSISTENT", "updates": 4969}
    assert (summary["training_episodes"], summary["training_ticks"]) == (5000, 100000)
    assert summary["optimizer_steps"] == 4969
    assert (summary["evaluation_episodes"], summary["evaluation_ticks"]) == (128, 2560)
    assert summary["native_panel"]["mean"] == 2.0 and summary["status"] == "complete"
    assert summary["native_panel"]["negative_count"] == 0
    assert summary["pair_primary"] is None
    assert "foreign or incomplete" in summary["pair_primary_unavailable"]
    assert seed_calls == [
        ("python", TRAINING_SEED),
        ("numpy", TRAINING_SEED),
        ("torch", TRAINING_SEED),
        ("python", EVALUATION_SEED),
        ("numpy", EVALUATION_SEED),
        ("torch", EVALUATION_SEED),
    ]
