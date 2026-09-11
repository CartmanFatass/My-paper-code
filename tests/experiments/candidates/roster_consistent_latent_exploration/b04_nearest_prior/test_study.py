"""Supplied tensors/outputs only: no native episode, RNG master or scientific fit."""
import json
import time
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.b04_nearest_prior import study
from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_runner as runner
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import make_conformance_fixture_model


def test_action_score_checkpoint_and_publication(monkeypatch, tmp_path):
    torch.set_num_threads(1)
    helper = make_conformance_fixture_model()
    monkeypatch.setattr(study.b03, "initialize_block_models", lambda rng: {study.b03.FLEX: helper})
    model = study.initialize_model(None)
    assert model.parameter_count == 26161
    candidates = torch.zeros(2, 6, 4, dtype=torch.float64)
    candidates[0, :, 3] = torch.tensor([.4, -.1, .1, .3, -.2, .5])
    candidates[1, :, 3] = torch.tensor([.6, -.5, .4, -.3, .2, -.1])
    packed = SimpleNamespace(counts=[2], contexts=torch.zeros(1, 4, dtype=torch.float64),
                             own=torch.ones(1, 2, 5, dtype=torch.float64), candidates=candidates[None])
    monkeypatch.setattr(runner, "_batched_public_tensors", lambda snapshots: packed)
    monkeypatch.setattr(runner, "_batched_manager", lambda m, p: SimpleNamespace(
        pooled_summary=torch.ones(1, 64, dtype=torch.float64)))
    captured = []
    def draw(coords, snapshots, probabilities):
        captured.append(probabilities)
        # Two fixed uniforms on opposite sides of the most-probable claim interval.
        return (torch.tensor([[.5], [.01]], dtype=torch.float64) > probabilities.cumsum(-1)).sum(-1).tolist()
    plans = SimpleNamespace(current={11: torch.ones(4, dtype=torch.float64),
                                     22: torch.ones(4, dtype=torch.float64)}, claim_scores=[])
    actions = runner._draw_claims_batch(model, study.b03.FLEX, SimpleNamespace(claim_compact=draw),
                                        [None], [SimpleNamespace(transport_keys=(11, 22))], [plans])
    expected = torch.full((2, 6), .02, dtype=torch.float64)
    expected[0, 1] = .9  # lowest index wins the +/- equal-distance tie
    expected[1, 5] = .9  # absolute distance, not minimum signed distance
    torch.testing.assert_close(captured[0], expected)
    claims = torch.tensor(actions[0].claims)
    torch.testing.assert_close(torch.stack(plans.claim_scores), captured[0].gather(-1, claims[:, None]).log().squeeze(-1))
    (-torch.stack(plans.claim_scores).sum()).backward()
    assert torch.isfinite(model.pointer_score.weight.grad).all()
    assert torch.linalg.vector_norm(model.pointer_score.weight.grad) > 0
    with torch.no_grad():
        model.pointer_score.weight.add_(model.pointer_score.weight.grad, alpha=-.01)
    study.save_model(model, tmp_path / "roundtrip.pt")
    checkpoint = torch.load(tmp_path / "roundtrip.pt", weights_only=True)
    restored = study.NearestPriorModel()
    restored.load_state_dict(checkpoint["state_dict"])
    assert checkpoint["action_law"] == study.LAW
    pointer = torch.zeros(2, 6, 81, dtype=torch.float64)
    pointer[..., 76] = candidates[..., 3]
    torch.testing.assert_close(model.claim_probabilities(pointer), restored.claim_probabilities(pointer))

    rows = [[dict(cell=cell, index=i, U=u + .001 * i, Y=.5 if u != .3 else None, tau=40., F=f)
             for cell in study.host.HELDOUT_CELLS for i in range(4)]
            for u, f in ((.4, .1), (.2, .15), (.3, .1))]
    monkeypatch.setattr(study, "make_rng", lambda seed: (SimpleNamespace(root_digest="fixture", certificate={"native": {}}), None))
    monkeypatch.setattr(study, "initialize_model", lambda rng: model)
    monkeypatch.setattr(study.b03, "panel", lambda m, rng, label, *args: rows[0 if label == "B04-INITIAL" else 1])
    calls = []
    def supplied_update(m, rng, update, baselines, weight):
        calls.append((update, weight))
        return baselines, dict(training_episodes=64, nonzero=True, update=update)
    monkeypatch.setattr(study.b03, "training_update", supplied_update)
    monkeypatch.setattr(study.host, "evaluate_scripted", lambda rng, count: list(reversed(rows[2])))
    learned = study.run("learned", tmp_path / "learned", "sha", tmp_path / "admit.json", time.perf_counter(), 30)
    reference = study.run("reference", tmp_path / "reference", "sha", tmp_path / "admit.json",
                          time.perf_counter(), 30, tmp_path / "learned/summary.json")
    assert calls == [(i, 100.) for i in range(200)]
    assert learned["status"] == reference["status"] == "COMPLETE"
    assert torch.load(tmp_path / "learned/parameters.pt", weights_only=True)["action_law"] == study.LAW
    published = json.loads((tmp_path / "reference/summary.json").read_text())
    primary = published["comparison"]["primary"]
    assert primary["Delta_ref"] == pytest.approx(.1)
    assert primary["G_U"] == pytest.approx(.2)
    assert primary["reference_gap"] == pytest.approx(-.1)
    assert len(published["comparison"]["cells"]) == 8
    assert published["eight_cell_mean"]["Y_mean"] is None
    assert "mixed native consequences" in published["reading"]
    bad = [dict(row) for row in rows[2]]
    bad[0]["index"] = 99
    with pytest.raises(ValueError, match="paired indices"):
        study.comparisons(rows[0], rows[1], bad)


@pytest.mark.parametrize("delta,gain,expected", [
    (.05, .01, "above-interest reference improvement with learning"),
    (.049, .01, "small reference improvement"),
    (0, .01, "learning from prior with reference deficit"),
    (-.1, .01, "learning from prior with reference deficit"),
    (.1, 0, "no positive learning from initialization"),
])
def test_reading_boundaries(delta, gain, expected):
    assert study.reading(delta, gain, False) == [expected]
