"""Changed binding and publication only; all scientific execution is stubbed."""
import inspect
import json
import time
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.b04_nearest_prior import study as b04
from experiments.candidates.roster_consistent_latent_exploration.b05_nearest_prior1000 import study


def test_binding_domains_without_scientific_rng(monkeypatch):
    defaults = inspect.signature(b04.run).parameters
    assert (defaults["seed"].default, defaults["updates"].default,
            defaults["object_id"].default, defaults["panel_label"].default) == (24, 200, b04.OBJECT_ID, "B04")
    keys, domains = [], []
    def key(text):
        keys.append(text)
        return b"supplied"
    def digest(key, domain, block):
        domains.append((key, domain, block))
        return "supplied"
    monkeypatch.setattr(b04.host, "seed_root_key", key)
    monkeypatch.setattr(b04.host, "block_digest_hex", digest)
    monkeypatch.setattr(b04.host, "native_certificate_payload", lambda: {})
    monkeypatch.setattr(b04.host, "B01BlockAuthority", lambda **kw: SimpleNamespace(**kw))
    monkeypatch.setattr(b04.b03, "SemanticRNG", lambda *args, **kw: None)
    b04.make_rng(24)
    b04.make_rng(study.SEED, object_id=study.OBJECT_ID)
    assert keys == [f"{b04.OBJECT_ID}/seed/24", f"{study.OBJECT_ID}/seed/25"]
    assert domains == [(b"supplied", b04.OBJECT_ID, 0), (b"supplied", study.OBJECT_ID, 0)]


def test_final1000_counts_checkpoints_and_primary(monkeypatch, tmp_path):
    # Two fixed FP64 scalars stand in for the accepted full model; no full allocation.
    model = torch.nn.Module()
    model.action_law = dict(b04.LAW)
    model.register_parameter("fixture", torch.nn.Parameter(torch.tensor([1., 2.], dtype=torch.float64)))
    rng_calls, panels, updates = [], [], []
    def rng(seed, object_id):
        rng_calls.append((seed, object_id))
        return SimpleNamespace(root_digest="supplied", certificate={"native": {}}), None
    monkeypatch.setattr(b04, "make_rng", rng)
    monkeypatch.setattr(b04.host, "seed_root_key", lambda text: b"supplied")
    monkeypatch.setattr(b04, "initialize_model", lambda rng, action_law=None: model)
    rows = [[dict(cell=cell, index=i, U=u + .001 * i, Y=y, tau=40., F=f)
             for cell in study.host.HELDOUT_CELLS for i in range(4)]
            for u, y, f in ((.4, .5, .1), (.2, .6, .15), (.3, None, .1))]
    def panel(m, rng, label, *args):
        panels.append((label, len(updates)))
        return rows[0 if label == "B05-INITIAL" else 1]
    def update(m, rng, number, baselines, weight):
        updates.append((number, weight))
        if number == 999:
            with torch.no_grad():
                m.fixture[0].add_(.02)  # A supplied final-step change tests checkpoint ordering.
        return baselines, dict(training_episodes=64, nonzero=True, update=number)
    monkeypatch.setattr(b04.b03, "panel", panel)
    monkeypatch.setattr(b04.b03, "training_update", update)
    monkeypatch.setattr(study.host, "evaluate_scripted", lambda *args: rows[2])
    learned = study.run("learned", tmp_path / "learned", "source", tmp_path / "admit.json", time.perf_counter(), 30)
    reference = study.run("reference", tmp_path / "reference", "source", tmp_path / "admit.json",
                          time.perf_counter(), 30, tmp_path / "learned/summary.json")
    assert learned["status"] == reference["status"] == "COMPLETE"
    assert rng_calls == [(25, study.OBJECT_ID)] * 2
    assert learned["object"] == reference["object"] == study.OBJECT_ID
    assert panels == [("B05-INITIAL", 0), ("B05-FINAL", 1000)]
    assert updates == [(i, 100.) for i in range(1000)]
    assert learned["counts"]["training_episodes"] == 64000
    assert learned["counts"]["backward_step_calls"] == learned["updates_per_fit"] == 1000
    assert len((tmp_path / "learned/completed_blocks.jsonl").read_text().splitlines()) == 1000
    initial = torch.load(tmp_path / "learned/initial_parameters.pt", weights_only=True)
    final = torch.load(tmp_path / "learned/parameters.pt", weights_only=True)
    assert final["state_dict"]["fixture"][0] - initial["state_dict"]["fixture"][0] == pytest.approx(.02)
    assert learned["final_displacement"] == pytest.approx(.02)
    primary = json.loads((tmp_path / "reference/summary.json").read_text())["comparison"]["primary"]
    assert primary["Delta_ref"] == pytest.approx(.1)
    assert primary["G_U"] == pytest.approx(.2)
    assert len(reference["comparison"]["cells"]) == 8
    assert reference["eight_cell_mean"]["Y_mean"] is None
    assert "above-interest reference improvement with learning" in reference["reading"]
    assert "mixed native consequences" in reference["reading"]
