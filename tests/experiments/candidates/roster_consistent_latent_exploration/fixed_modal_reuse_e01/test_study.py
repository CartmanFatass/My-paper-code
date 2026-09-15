"""Synthetic-only checks: no retained scientific checkpoint or native rollout."""
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.fixed_modal_reuse_e01 import study
from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase import policy
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import PublicObservation


def public_fixture():
    return PublicObservation(tick=0, claim_required=True, roster_event=False, new_epoch=False,
        positions=(0, 0, 30, 70, 70, 100, 110, 119), angular_ranks=tuple(range(8)),
        previous_displacements=(0,)*8, newcomers=(False,)*8,
        beacon_positions=(6, 26, 46, 66, 86, 106), demands=(2, 1, 2, 1, 1, 1))


def rows(u):
    return [dict(cell=cell, scenario=i, U=u, F=0., tau=3, Y=1-u, unmet_ticks=40*u,
                 agent_ticks=640, agent_claims=160)
            for cell in study.phase_study.HELDOUT_CELLS for i in range(64)]


def synthetic_inputs(tmp_path, monkeypatch):
    specs = {}
    for i, name in enumerate(("b10", "b12")):
        p = tmp_path / "inputs" / name
        p.mkdir(parents=True)
        model = policy.PhasePolicy(greedy_anchored=True)
        with torch.no_grad():
            model.score.bias.fill_(.25+i)
        spec = dict(seed=900+i, object_id=f"TEST_ONLY_MODAL_{name}", source_sha=str(i)*40)
        torch.save(dict(model=model.state_dict(), seed=spec["seed"], object_id=spec["object_id"],
            launch_sha=spec["source_sha"], updates=1024, action_law=study.LAW), p / "final1024.pt")
        (p / "greedy.json").write_text(json.dumps(rows(.25+i*.1)), encoding="utf8")
        spec["checkpoint_sha256"] = hashlib.sha256((p / "final1024.pt").read_bytes()).hexdigest()
        spec["greedy_sha256"] = hashlib.sha256((p / "greedy.json").read_bytes()).hexdigest()
        specs[name] = spec
    monkeypatch.setattr(study, "BASES", specs)
    return tmp_path / "inputs"


def test_modal_uses_anchor_and_lowest_combined_tie(monkeypatch):
    model = policy.PhasePolicy(greedy_anchored=True)
    public = public_fixture()
    _, _, _, targets, _, signed = policy.quota_arrays([public])
    greedy = int(np.abs(signed).sum(axis=-1).argmin(axis=-1)[0])
    competitor = (greedy+1) % 8
    raw = torch.zeros((1, 8), dtype=torch.float64)
    raw[0, competitor] = .5  # bare z prefers a different phase, but combined law does not.
    monkeypatch.setattr(model, "forward", lambda *args: raw)
    action, phase = policy.modal_phase(model, [public])
    assert phase.tolist() == [greedy] and action.tolist() == targets[:, greedy].tolist()
    lp = torch.tensor([[0., 2., 2., 1.]], dtype=torch.float64)
    choices = np.arange(12).reshape(1, 4, 3)
    monkeypatch.setattr(policy, "phase_log_probabilities", lambda *args: (lp, choices))
    action, phase = policy.modal_phase(model, [public])
    assert phase.tolist() == [1] and action.tolist() == [[3, 4, 5]]


def test_modal_rollout_dispatches_on_live_roster_without_phase_uniforms(monkeypatch):
    s = study.phase_study
    events, claim_sizes = [], []
    public = public_fixture()

    class FakeBatch:
        tick = 0
        applied = False

        @property
        def snapshots(self):
            n = 12 if self.applied else 8
            p = replace(public, tick=self.tick, positions=tuple((i*7+self.tick) % 120 for i in range(n)),
                        angular_ranks=tuple(range(n)), newcomers=(False,)*8+(True,)*(n-8),
                        demands=(2,)*6 if n == 12 else public.demands)
            return [SimpleNamespace(event_input_required=self.tick == 24 and not self.applied,
                claim_required=self.tick % 4 == 0, positions=p.positions, public_observation=lambda: p,
                U=.2, F=0., tau=3, Y=.8)]

        def __enter__(self): return self
        def __exit__(self, *args): return False
        def materialize_events_compact(self, *args): return "synthetic event"
        def apply_event(self, event):
            assert event == "synthetic event"
            events.append(self.tick)
            self.applied = True
            return self.snapshots
        def step(self, actions):
            if self.tick % 4 == 0:
                claim_sizes.append(len(actions[0].claims))
            self.tick += 1

    monkeypatch.setattr(s, "native_materialize_fixtures_compact", lambda *a, **k: None)
    monkeypatch.setattr(s, "reset_native_batch", lambda *a, **k: FakeBatch())
    def forbid(*args, **kwargs): raise AssertionError("sampling/native training is forbidden")
    monkeypatch.setattr(s, "phase_uniforms", forbid)
    monkeypatch.setattr(s, "sampled_phase", forbid)
    coordinates = (s.EpisodeCoordinate(0, "8_to_12.ACTIVE_CONTINUATION", 0, 0),)
    with torch.no_grad():
        result, scores = s.rollout(policy.PhasePolicy(greedy_anchored=True), "modal",
            hashlib.sha256(b"TEST_ONLY_MODAL_ROLLOUT").digest(), None, coordinates)
    assert events == [24] and claim_sizes == [8]*6+[12]*10 and scores is None
    assert result[0]["agent_ticks"] == 24*8+40*12
    with pytest.raises(ValueError, match="no training"):
        s.rollout(None, "modal", b"TEST_ONLY", None, (), training=True)


def test_loader_restores_non_state_dict_anchor_and_original_synthetic_domain(tmp_path, monkeypatch):
    inputs = synthetic_inputs(tmp_path, monkeypatch)
    def forbid(*a, **k): raise AssertionError("initialization/optimizer must not run")
    monkeypatch.setattr(policy.PhasePolicy, "initialize", forbid)
    monkeypatch.setattr(torch.optim, "Adam", forbid)
    model, panel, key = study.load_base(inputs, "b10")
    assert model.greedy_anchored is True and all(not p.requires_grad for p in model.parameters())
    assert float(model.score.bias) == .25 and len(panel) == 512
    assert key == hashlib.sha256(b"TEST_ONLY_MODAL_b10/seed/900").digest()
    assert key != hashlib.sha256(study.OBJECT.encode()).digest()


def test_loader_rejects_tampered_bytes_and_wrong_checkpoint_law(tmp_path, monkeypatch):
    inputs = synthetic_inputs(tmp_path, monkeypatch)
    p = inputs / "b10/final1024.pt"
    checkpoint = torch.load(p, weights_only=True)
    checkpoint["action_law"] = "bare score"
    torch.save(checkpoint, p)
    with pytest.raises(ValueError, match="frozen input"):
        study.load_base(inputs, "b10")
    study.BASES["b10"]["checkpoint_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="action_law"):
        study.load_base(inputs, "b10")


def test_complete_synthetic_publication_retains_each_base_and_zero_updates(tmp_path, monkeypatch):
    inputs = synthetic_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(study.phase_study, "bind_native_backend", lambda **k: SimpleNamespace(
        source_sha256="18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819"))
    keys = []
    def evaluate(model, role, key, binding, dest):
        assert role == "modal" and model.greedy_anchored
        keys.append(key)
        result = list(reversed(rows(.2 if dest.name == "b10" else .3)))
        study.phase_study.write_json(dest / "modal.json", result)
        return result
    monkeypatch.setattr(study.phase_study, "evaluate", evaluate)
    def forbid(*a, **k): raise AssertionError("new training is forbidden")
    monkeypatch.setattr(torch.optim, "Adam", forbid)
    out = tmp_path / "out"
    result = study.run(inputs, out, "c"*40)
    assert result["new_evaluation_episodes"] == 1024 and result["native_ticks"] == 65536
    assert result["new_fits"] == result["new_training_episodes"] == result["new_optimizer_calls"] == 0
    assert len(set(keys)) == 2
    for name in ("b10", "b12"):
        r = result["bases"][name]
        assert r["parameter_displacement"] == 0
        assert r["comparison"]["D_mode_g"]["mean"] == pytest.approx(.05)
        assert r["comparison"]["D_mode_g"]["paths"][study.phase_study.PRIMARY[0]]["favorable"] == 64
        assert (out / name / "modal.json").is_file() and (out / name / "greedy.json").is_file()
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"
    with pytest.raises(FileExistsError):
        study.run(inputs, out, "c"*40)


def test_parameter_mutation_cannot_be_reported_as_zero_learning(tmp_path, monkeypatch):
    inputs = synthetic_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(study.phase_study, "bind_native_backend", lambda **k: SimpleNamespace(
        source_sha256="18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819"))
    def mutate(model, *args):
        with torch.no_grad(): model.score.bias.add_(1)
        return rows(.2)
    monkeypatch.setattr(study.phase_study, "evaluate", mutate)
    with pytest.raises(ValueError, match="parameters changed"):
        study.run(inputs, tmp_path / "out", "d"*40)
    assert not (tmp_path / "out/summary.json").exists()
