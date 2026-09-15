import importlib.util
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_current_increment_b01.learner import Learner
from experiments.candidates.vap_folr_core.entity_current_increment_b01.publication import (
    EVALUATION_SEED, OBJECT, TRAINING_SEED, attach_primary, pair_result,
)
from experiments.candidates.vap_folr_core.entity_history_augmentation_b01.model import AugmentedActor
from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor


@pytest.fixture(scope="module", autouse=True)
def one_thread():
    torch.set_num_threads(1)


def observations():
    torch.manual_seed(713)
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(2, 21, 1, 1)
    visible[:, :, 0, 1] = True
    continuation = torch.ones(2, 21, 5, dtype=torch.bool)
    continuation[:, 0] = False
    return {
        "entities": torch.rand(2, 21, 5, 4),
        "previous_action": torch.zeros(2, 21, 5, 5),
        "entity_mask": torch.zeros(2, 21, 5, dtype=torch.bool),
        "visible": visible, "obs_mask": ~visible, "seen": visible.clone(),
        "age": torch.zeros_like(visible, dtype=torch.int16),
        "birth": ~continuation, "continuation": continuation,
        "departure": torch.zeros_like(continuation),
        "event": torch.zeros(2, 21, dtype=torch.bool),
    }


def endpoint(arm, value=0.0, **changes):
    result = {
        "object": OBJECT, "arm": arm, "status": "complete",
        "training_seed": TRAINING_SEED, "evaluation_seed": EVALUATION_SEED,
        "training_episodes": 5000, "training_ticks": 100000, "optimizer_steps": 4969,
        "evaluation_episodes": 128, "evaluation_ticks": 2560,
        "evaluation_returns": [value] * 128, "launch_sha": "synthetic-source",
    }
    result.update(changes)
    return result


def test_distinct_programs_align_only_compatible_modules_and_external_rng():
    torch.manual_seed(914)
    generic = Learner("GENERIC_RETAIN")
    after_generic = torch.random.get_rng_state()
    torch.manual_seed(914)
    current = Learner("AUGMENTED_CURRENT_ONLY")
    assert torch.equal(after_generic, torch.random.get_rng_state())
    assert type(generic.actor) is Actor and type(current.actor) is AugmentedActor
    assert current.actor.arm == "AUGMENTED_CURRENT_ONLY"
    assert generic.actor.fc3.weight.shape == (5, 64)
    assert current.actor.head.weight.shape == (5, 128)
    assert not hasattr(generic.actor, "entity_rnn")
    assert sum(p.numel() for p in generic.actor.parameters()) == 103173
    assert sum(p.numel() for p in current.actor.parameters()) == 192741
    for module in ("fc1", "attn", "fc2", "rnn"):
        for name, expected in getattr(generic.actor, module).state_dict().items():
            torch.testing.assert_close(
                getattr(current.actor, module).state_dict()[name], expected, rtol=0, atol=0
            )
    for name, value in generic.mixer.state_dict().items():
        torch.testing.assert_close(value, current.mixer.state_dict()[name], rtol=0, atol=0)
    batch = observations()
    _, gstate = generic.actor(batch)
    _, zstate = current.actor(batch)
    assert gstate.shape == (2, 21, 5, 64) and zstate.shape == (2, 21, 5, 144)
    torch.testing.assert_close(gstate, zstate[..., :64])
    assert generic.actor is not current.actor and generic.optimiser is not current.optimiser


@pytest.mark.parametrize("arm,head", [("GENERIC_RETAIN", "fc3"), ("AUGMENTED_CURRENT_ONLY", "head")])
def test_synthetic_update_keeps_targets_separate_and_publishes_checkpoint(tmp_path, arm, head):
    torch.manual_seed(912)
    learner = Learner(arm)
    batch = observations()
    batch.update(actions=torch.zeros(2, 20, 5, dtype=torch.long),
                 reward=torch.ones(2, 20), terminated=torch.zeros(2, 20))
    batch["terminated"][:, -1] = 1
    online = getattr(learner.actor, head).weight
    target = getattr(learner.target_actor, head).weight
    before, target_before = online.detach().clone(), target.detach().clone()
    loss = learner.update(batch, 1)
    assert np.isfinite(loss) and learner.updates == 1
    assert not torch.equal(before, online) and online.data_ptr() != target.data_ptr()
    torch.testing.assert_close(target_before, target)
    assert learner.mixer is not learner.target_mixer
    path = tmp_path / "final.pt"
    learner.save(path)
    saved = torch.load(path, weights_only=True)
    assert saved["arm"] == arm and saved["updates"] == 1 and saved["optimiser"]["state"]
    torch.testing.assert_close(saved["actor"][head + ".weight"], online)
    torch.testing.assert_close(saved["target_actor"][head + ".weight"], target)


@pytest.mark.parametrize("difference,rule", [
    (1.1, "CURRENT_ONLY_ABOVE_MEI"), (1.0, "WITHIN_MEI"),
    (-1.0, "WITHIN_MEI"), (-1.1, "GENERIC_ABOVE_MEI"),
])
def test_primary_sign_and_strict_mei_boundaries(difference, rule):
    result = pair_result(endpoint("GENERIC_RETAIN"), endpoint("AUGMENTED_CURRENT_ONLY", difference))
    assert result["current_only_minus_generic"] == pytest.approx(difference)
    assert result["rule"] == rule and result["paired_difference_se"] is None
    assert result["training_instances_per_arm"] == 1
    assert result["generic"]["negative_count"] == 0
    assert result["current_only"]["negative_count"] == (128 if difference < 0 else 0)


@pytest.mark.parametrize("changes", [
    None, {"status": "incomplete"}, {"object": "old-object"},
    {"training_seed": 781701}, {"launch_sha": "foreign-source"},
    {"optimizer_steps": 4968}, {"evaluation_returns": [0.0] * 127},
    {"evaluation_returns": [float("nan")] * 128}, {"arm": "AUGMENTED_PERSISTENT"},
])
def test_unusable_comparator_keeps_current_only_facts_without_polarity(changes):
    generic = None if changes is None else endpoint("GENERIC_RETAIN")
    if generic is not None:
        generic.update(changes)
    current = endpoint("AUGMENTED_CURRENT_ONLY", 2.0)
    attach_primary(current, generic)
    assert current["status"] == "complete" and current["evaluation_returns"] == [2.0] * 128
    assert current["pair_primary"] is None
    assert "no Z-minus-G polarity" in current["pair_primary_unavailable"]


@pytest.mark.parametrize("arm,foreign", [
    ("GENERIC_RETAIN", False), ("AUGMENTED_CURRENT_ONLY", False),
    ("AUGMENTED_CURRENT_ONLY", True),
])
def test_runner_follows_selected_arm_then_publishes_only_bound_primary(tmp_path, monkeypatch, arm, foreign):
    runner_path = Path(__file__).resolve().parents[5] / "scripts/run_folr_entity_current_increment_b01.py"
    spec = importlib.util.spec_from_file_location("folr_current_runner_test", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    from experiments.candidates.vap_folr_core.entity_current_increment_b01 import learner
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection

    constructed, seed_calls = [], []

    class FakeLearner:
        def __init__(self, selected):
            constructed.append(selected)
            self.actor = torch.nn.Linear(1, 1)
            self.actor.arm = selected
            self.updates = 0

        def update(self, batch, episode_num):
            self.updates += 1

        def save(self, path):
            torch.save({"arm": self.actor.arm, "updates": self.updates}, path)

    monkeypatch.setattr(learner, "Learner", FakeLearner)
    monkeypatch.setattr(environment, "EntityHistoryEnv", lambda **_: object())
    monkeypatch.setattr(collection, "collect", lambda env, actor, epsilon: ({}, 2.0, {}))
    monkeypatch.setattr(collection, "sample", lambda replay: {})
    monkeypatch.setattr(collection, "epsilon_at", lambda ticks: 0.0)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _: None)
    for label, module, name in (("python", random, "seed"), ("numpy", np.random, "seed"),
                                ("torch", torch, "manual_seed")):
        monkeypatch.setattr(module, name, lambda seed, label=label: seed_calls.append((label, seed)))
    out = tmp_path / "output"
    argv = [str(runner_path), "--arm", arm, "--seed", str(TRAINING_SEED),
            "--evaluation-seed", str(EVALUATION_SEED), "--launch-sha", "synthetic-source", "--out", str(out)]
    if arm == "AUGMENTED_CURRENT_ONLY":
        generic_path = tmp_path / "generic.json"
        generic_path.write_text(json.dumps(endpoint("GENERIC_RETAIN", object="old-object" if foreign else OBJECT)))
        argv += ["--generic-summary", str(generic_path)]
    monkeypatch.setattr("sys.argv", argv)
    runner.main()
    summary = json.loads((out / "summary.json").read_text())
    assert constructed == [arm]
    assert torch.load(out / "final.pt", weights_only=True) == {"arm": arm, "updates": 4969}
    assert (summary["training_episodes"], summary["training_ticks"], summary["optimizer_steps"]) == (5000, 100000, 4969)
    assert (summary["evaluation_episodes"], summary["evaluation_ticks"]) == (128, 2560)
    assert summary["status"] == "complete" and summary["native_panel"]["mean"] == 2.0
    if arm == "GENERIC_RETAIN":
        assert "pair_primary" not in summary
    elif foreign:
        assert summary["pair_primary"] is None and "foreign or incomplete" in summary["pair_primary_unavailable"]
    else:
        assert summary["pair_primary"]["current_only_minus_generic"] == 2.0
        assert summary["pair_primary"]["rule"] == "CURRENT_ONLY_ABOVE_MEI"
    assert seed_calls == [(label, seed) for seed in (TRAINING_SEED, EVALUATION_SEED)
                          for label in ("python", "numpy", "torch")]
