import importlib.util
import hashlib
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_augmentation_repeat_b01.publication import (
    BLOCKS, OBJECT, attach_primary, pair_result, study_result,
)


@pytest.fixture(scope="module", autouse=True)
def one_thread():
    torch.set_num_threads(1)


def endpoint(arm, block=1, value=0.0, **changes):
    result = {
        "object": OBJECT, "arm": arm, "block": block, "status": "complete",
        "training_seed": BLOCKS[block][0], "evaluation_seed": BLOCKS[block][1],
        "training_episodes": 5000, "training_ticks": 100000, "optimizer_steps": 4969,
        "evaluation_episodes": 128, "evaluation_ticks": 2560,
        "evaluation_returns": [value] * 128, "launch_sha": "synthetic-source",
    }
    result.update(changes)
    return result


def test_existing_factory_is_persistent_and_each_fit_owns_fresh_learning_state():
    from experiments.candidates.vap_folr_core.entity_history_augmentation_b01.learner import Learner
    from experiments.candidates.vap_folr_core.entity_history_augmentation_b01.model import AugmentedActor
    from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor

    fits = []
    for seed in (7411, 7412):
        torch.manual_seed(seed)
        g = Learner("GENERIC_RETAIN")
        g_rng = torch.random.get_rng_state()
        torch.manual_seed(seed)
        a = Learner("AUGMENTED_PERSISTENT")
        assert torch.equal(g_rng, torch.random.get_rng_state())
        assert type(g.actor) is Actor and type(a.actor) is AugmentedActor
        assert a.actor.arm == "AUGMENTED_PERSISTENT"
        assert (sum(p.numel() for p in g.actor.parameters()),
                sum(p.numel() for p in a.actor.parameters())) == (103173, 192741)
        assert g.actor.fc3.weight.shape == (5, 64) and a.actor.head.weight.shape == (5, 128)
        for name in ("fc1", "attn", "fc2", "rnn"):
            for key, value in getattr(g.actor, name).state_dict().items():
                torch.testing.assert_close(getattr(a.actor, name).state_dict()[key], value, rtol=0, atol=0)
        fits.extend((g, a))
    assert len({id(f.actor) for f in fits}) == 4
    assert len({id(f.optimiser) for f in fits}) == 4
    for f in fits:
        assert f.actor is not f.target_actor and f.mixer is not f.target_mixer
        assert f.updates == 0 and not f.optimiser.state


@pytest.mark.parametrize("d1,d2,rule", [
    (1.1, 2.0, "BOTH_A_ABOVE_MEI"), (-1.1, -2.0, "BOTH_G_ABOVE_MEI"),
    (1.0, -1.0, "BOTH_WITHIN_MEI"), (0.0, -0.5, "BOTH_WITHIN_MEI"),
    (12.0, -8.0, "MIXED_BLOCK_PATTERN"), (1.1, 1.0, "MIXED_BLOCK_PATTERN"),
    (-1.1, -1.0, "MIXED_BLOCK_PATTERN"), (2.0, -2.0, "MIXED_BLOCK_PATTERN"),
])
def test_ordered_primary_preserves_boundaries_and_disagreement(d1, d2, rule):
    result = study_result(endpoint("GENERIC_RETAIN", 1), endpoint("AUGMENTED_PERSISTENT", 1, d1),
                          endpoint("GENERIC_RETAIN", 2), endpoint("AUGMENTED_PERSISTENT", 2, d2))
    assert result["ordered_differences"] == pytest.approx([d1, d2])
    assert result["descriptive_mean_difference"] == pytest.approx((d1 + d2) / 2)
    assert result["rule"] == rule and result["population_interval"] is None
    assert result["training_instances_per_arm"] == result["independent_contrast_blocks"] == 2
    assert [r["block"] for r in result["blocks"]] == [1, 2]


@pytest.mark.parametrize("changes", [
    None, {"block": 2}, {"status": "incomplete"}, {"object": "old-object"},
    {"training_seed": 781801}, {"evaluation_seed": 1781801},
    {"launch_sha": "foreign"}, {"optimizer_steps": 4968},
    {"evaluation_returns": [0.0] * 127}, {"evaluation_returns": [float("nan")] * 128},
    {"arm": "AUGMENTED_CURRENT_ONLY"},
])
def test_unusable_own_block_g_keeps_a_endpoint_without_polarity(changes):
    g = None if changes is None else endpoint("GENERIC_RETAIN")
    if g is not None:
        g.update(changes)
    a = endpoint("AUGMENTED_PERSISTENT", value=2.0)
    attach_primary(a, g)
    assert a["status"] == "complete" and a["evaluation_returns"] == [2.0] * 128
    assert a["pair_primary"] is None and "no A-minus-G polarity" in a["pair_primary_unavailable"]


def test_study_cannot_duplicate_or_reverse_blocks_or_mix_sources():
    g1, a1 = endpoint("GENERIC_RETAIN", 1), endpoint("AUGMENTED_PERSISTENT", 1)
    g2, a2 = endpoint("GENERIC_RETAIN", 2), endpoint("AUGMENTED_PERSISTENT", 2)
    for endpoints in ((g1, a1, g1, a1), (g2, a2, g1, a1)):
        with pytest.raises(ValueError, match="fixed order"):
            study_result(*endpoints)
    g2["launch_sha"] = a2["launch_sha"] = "other"
    with pytest.raises(ValueError, match="different selected sources"):
        study_result(g1, a1, g2, a2)
    with pytest.raises(ValueError, match="foreign block"):
        pair_result(g1, endpoint("AUGMENTED_CURRENT_ONLY"))


def test_runner_rejects_foreign_block_seed_before_construction(tmp_path, monkeypatch):
    runner_path = Path(__file__).resolve().parents[5] / "scripts/run_folr_entity_augmentation_repeat_b01.py"
    spec = importlib.util.spec_from_file_location("folr_repeat_invalid_seed_test", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr("sys.argv", [str(runner_path), "--block", "2", "--arm", "GENERIC_RETAIN",
                                    "--seed", str(BLOCKS[1][0]), "--evaluation-seed", str(BLOCKS[1][1]),
                                    "--launch-sha", "synthetic-source", "--out", str(tmp_path / "unused")])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2 and not (tmp_path / "unused").exists()


@pytest.mark.parametrize("block,arm,foreign", [
    (1, "GENERIC_RETAIN", False), (1, "AUGMENTED_PERSISTENT", False),
    (2, "GENERIC_RETAIN", False), (2, "AUGMENTED_PERSISTENT", False),
    (2, "AUGMENTED_PERSISTENT", True),
])
def test_runner_binds_block_and_reads_g_only_after_its_complete_fit(tmp_path, monkeypatch, block, arm, foreign):
    runner_path = Path(__file__).resolve().parents[5] / "scripts/run_folr_entity_augmentation_repeat_b01.py"
    spec = importlib.util.spec_from_file_location("folr_repeat_runner_test", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    # This test isolates the frozen scientific loop. Real admission and direct
    # CLI refusal are covered separately; no real experiment is authorized here.
    monkeypatch.setattr(runner, "require_admission", lambda *a, **kw: {"sha": "synthetic-source"})
    from experiments.candidates.vap_folr_core.entity_history_augmentation_b01 import learner
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection

    constructed, seed_calls, collected = [], [], []

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

    def collect(*_):
        collected.append(1)
        if arm == "AUGMENTED_PERSISTENT":
            generic_path.write_text("source changed after binding")
        return {}, 2.0, {}

    monkeypatch.setattr(learner, "Learner", FakeLearner)
    monkeypatch.setattr(environment, "EntityHistoryEnv", lambda **_: object())
    monkeypatch.setattr(collection, "collect", collect)
    monkeypatch.setattr(collection, "sample", lambda _: {})
    monkeypatch.setattr(collection, "epsilon_at", lambda _: 0.0)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _: None)
    for label, module, name in (("python", random, "seed"), ("numpy", np.random, "seed"),
                                ("torch", torch, "manual_seed")):
        monkeypatch.setattr(module, name, lambda seed, label=label: seed_calls.append((label, seed)))
    out = tmp_path / "output"
    argv = [str(runner_path), "--block", str(block), "--arm", arm, "--seed", str(BLOCKS[block][0]),
            "--evaluation-seed", str(BLOCKS[block][1]), "--launch-sha", "synthetic-source", "--out", str(out)]
    if arm == "AUGMENTED_PERSISTENT":
        generic_path = tmp_path / "generic.json"
        generic_path.write_text(json.dumps(endpoint("GENERIC_RETAIN", 3-block if foreign else block)))
        original_read = Path.read_bytes

        def guarded_read(path, *args, **kwargs):
            if path == generic_path:
                assert len(collected) == 0
            return original_read(path, *args, **kwargs)

        digest = hashlib.sha256(generic_path.read_bytes()).hexdigest()
        monkeypatch.setattr(Path, "read_bytes", guarded_read)
        argv += ["--generic-summary", str(generic_path), "--generic-summary-sha256", digest]
    monkeypatch.setattr("sys.argv", argv)
    runner.main()
    summary = json.loads((out / "summary.json").read_text())
    if arm == "AUGMENTED_PERSISTENT":
        assert hashlib.sha256((out / "generic-input.json").read_bytes()).hexdigest() == digest
    assert constructed == [arm] and summary["block"] == block
    assert torch.load(out / "final.pt", weights_only=True) == {"arm": arm, "updates": 4969}
    assert (summary["training_episodes"], summary["training_ticks"], summary["optimizer_steps"]) == (5000, 100000, 4969)
    assert (summary["evaluation_episodes"], summary["evaluation_ticks"]) == (128, 2560)
    assert summary["status"] == "complete" and summary["native_panel"]["mean"] == 2.0
    if arm == "GENERIC_RETAIN":
        assert "pair_primary" not in summary
    elif foreign:
        assert summary["pair_primary"] is None and "foreign block" in summary["pair_primary_unavailable"]
    else:
        assert summary["pair_primary"]["block"] == block
        assert summary["pair_primary"]["persistent_minus_generic"] == 2.0
    assert seed_calls == [(label, seed) for seed in BLOCKS[block] for label in ("python", "numpy", "torch")]


@pytest.mark.parametrize("digest", [None, "0" * 64])
def test_generic_input_requires_matching_digest_before_training(tmp_path, monkeypatch, digest):
    runner_path = Path(__file__).resolve().parents[5] / "scripts/run_folr_entity_augmentation_repeat_b01.py"
    spec = importlib.util.spec_from_file_location("folr_digest_test", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(runner, "require_admission", lambda *a, **kw: {"sha": "synthetic-source"})
    generic = tmp_path / "generic.json"
    generic.write_text('{}')
    output = tmp_path / 'unused'
    argv = [str(runner_path), '--block', '1', '--arm', 'AUGMENTED_PERSISTENT',
            '--seed', str(BLOCKS[1][0]), '--evaluation-seed', str(BLOCKS[1][1]),
            '--launch-sha', 'synthetic-source', '--out', str(output), '--generic-summary', str(generic)]
    if digest:
        argv += ['--generic-summary-sha256', digest]
    monkeypatch.setattr('sys.argv', argv)
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2
    assert not output.exists()
