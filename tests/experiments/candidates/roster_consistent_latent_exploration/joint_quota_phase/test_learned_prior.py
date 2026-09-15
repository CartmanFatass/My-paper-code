"""Synthetic B13 contracts; no scientific root or native environment is executed."""
from types import SimpleNamespace
import hashlib
import json
import math

import numpy as np
import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase import policy, study
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import PublicObservation


def public_fixture(n=8):
    return PublicObservation(tick=24, claim_required=True, roster_event=True, new_epoch=False,
        positions=(0, 0, 30, 70, 70, 100, 110, 119) if n == 8 else tuple(range(0, 120, 10)),
        angular_ranks=tuple(range(n)), previous_displacements=(0,) * n,
        newcomers=(False,) * (n-1) + (True,), beacon_positions=(6, 26, 46, 66, 86, 106),
        demands=(2, 1, 2, 1, 1, 1) if n == 8 else (2,) * 6)


def greedy_index(public):
    return int(np.abs(policy.quota_arrays([public])[-1][0]).sum(-1).argmin())


def test_initial_law_and_old_checkpoint_inventory_are_preserved_without_rng_draw():
    rng_before = torch.get_rng_state().clone()
    old = policy.PhasePolicy(greedy_anchored=True)
    new = policy.PhasePolicy(greedy_anchored=True, learned_prior_strength=True)
    old.initialize(lambda name, count: np.linspace(.13, .89, count))
    new.initialize(lambda name, count: np.linspace(.13, .89, count))
    assert torch.equal(rng_before, torch.get_rng_state())
    assert sum(p.numel() for p in old.parameters()) == 2561
    assert sum(p.numel() for p in new.parameters()) == 2562
    assert 'log_prior_strength' not in old.state_dict()
    assert float(new.log_prior_strength) == 0
    assert set(new.state_dict()) == set(old.state_dict()) | {'log_prior_strength'}
    for name, tensor in old.state_dict().items():
        assert torch.equal(tensor, new.state_dict()[name])
    for n in (8, 12):
        public = [public_fixture(n)]
        assert torch.equal(policy.phase_log_probabilities(old, public)[0],
                           policy.phase_log_probabilities(new, public)[0])
    restored = policy.PhasePolicy(greedy_anchored=True)
    restored.load_state_dict(old.state_dict(), strict=True)
    with pytest.raises(ValueError, match='requires the greedy'):
        policy.PhasePolicy(learned_prior_strength=True)


@pytest.mark.parametrize('n', [8, 12])
@pytest.mark.parametrize('eta', [-.7, 0, .4])
def test_eta_scores_the_actual_normalized_law(n, eta, monkeypatch):
    model = policy.PhasePolicy(greedy_anchored=True, learned_prior_strength=True)
    with torch.no_grad():
        model.log_prior_strength.fill_(eta)
    logits = torch.linspace(-.8, 1.2, n, dtype=torch.float64).reshape(1, n)
    monkeypatch.setattr(model, 'forward', lambda features, context: logits)
    public = public_fixture(n)
    greedy = greedy_index(public)
    logp, _ = policy.phase_log_probabilities(model, [public])
    probability_greedy = float(logp[0, greedy].detach().exp())
    for phase in (greedy, (greedy + 1) % n):
        actual, = torch.autograd.grad(logp[0, phase], model.log_prior_strength, retain_graph=True)
        expected = math.exp(eta) * math.log(9*n + 1) * (float(phase == greedy) - probability_greedy)
        assert float(actual) == pytest.approx(expected, rel=1e-12, abs=1e-13)


def test_real_full_return_adam_updates_eta_and_baseline():
    torch.set_num_threads(1)
    model = policy.PhasePolicy(greedy_anchored=True, learned_prior_strength=True)
    model.initialize(lambda name, count: np.linspace(.13, .89, count))
    public = public_fixture()
    greedy = greedy_index(public)
    p = policy.phase_log_probabilities(model, [public])[0].detach().exp()[0].numpy()
    u = float(p[:greedy].sum() + p[greedy]/2)
    _, score, phases = policy.sampled_phase(model, [public]*64, [u]*64)
    assert phases.tolist() == [greedy]*64
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4, betas=(.9, .999), eps=1e-8,
                                 weight_decay=0, foreach=False)
    baselines = torch.zeros(8, dtype=torch.float64)
    updated, facts = policy.adam_update(model, optimizer, torch.ones(64, dtype=torch.float64),
        16*score, torch.arange(8).repeat_interleave(8), baselines)
    assert float(model.log_prior_strength) > 0
    assert float(optimizer.state[model.log_prior_strength]['step']) == 1
    assert facts['backward_calls'] == facts['optimizer_calls'] == 1
    torch.testing.assert_close(updated, torch.full_like(updated, 1-.95))
    assert torch.equal(baselines, torch.zeros_like(baselines))


def test_modal_uses_learned_prior_and_scorer_together(monkeypatch):
    model = policy.PhasePolicy(greedy_anchored=True, learned_prior_strength=True)
    public = public_fixture()
    greedy = greedy_index(public)
    alternative = (greedy + 1) % 8
    logits = torch.zeros(1, 8, dtype=torch.float64)
    logits[0, alternative] = 3
    monkeypatch.setattr(model, 'forward', lambda features, context: logits)
    assert policy.modal_phase(model, [public])[1].tolist() == [greedy]
    with torch.no_grad():
        model.log_prior_strength.fill_(-1)
    assert policy.modal_phase(model, [public])[1].tolist() == [alternative]


def test_b13_synthetic_whole_driver_keeps_five_panels_and_exact_new_counts(tmp_path, monkeypatch):
    original_hash = hashlib.sha256
    domains, training, evaluation = [], [], []
    def synthetic_hash(data=b''):
        if data.startswith((study.B13_OBJECT + '/').encode('ascii')):
            domains.append(data)
            return original_hash(b'SYNTHETIC-TEST-B13-WIRING/' + data)
        return original_hash(data)
    monkeypatch.setattr(study.hashlib, 'sha256', synthetic_hash)
    monkeypatch.setattr(study, 'bind_native_backend',
                        lambda **kwargs: SimpleNamespace(source_sha256='SYNTHETIC-TEST-NATIVE'))
    monkeypatch.setattr(study, 'uniforms', lambda key, binding, addresses: [.5]*len(addresses))
    values = dict(initialization=.4, final1024=.3, greedy=.35, nearest=.45, modal=.36)
    def fake_rollout(model, role, key, binding, coordinates, training=False):
        assert model.greedy_anchored and model.log_prior_strength is not None
        if training:
            assert role == 'learned'
            training_rows = tuple(c.update_or_scenario for c in coordinates)
            training_calls.append(training_rows)
            value = .5
        else:
            evaluation.append((role, float(model.log_prior_strength.detach()), len(coordinates)))
            value = values[role]
        result = [dict(Y=.5, U=value, F=0, tau=40, unmet_ticks=40*value,
                       agent_ticks=640, agent_claims=160) for _ in coordinates]
        return result, torch.zeros(len(coordinates), dtype=torch.float64) if training else None
    training_calls = training
    monkeypatch.setattr(study, 'rollout', fake_rollout)
    def fake_update(model, optimizer, returns, scores, indices, baselines):
        with torch.no_grad():
            model.log_prior_strength.add_(.001)
        return baselines, dict(backward_calls=1, optimizer_calls=1, parameter_step_norm=.001)
    monkeypatch.setattr(study, 'adam_update', fake_update)
    result = study.run_b13_learned_prior1024(tmp_path, 'SYNTHETIC-TEST-SOURCE', 33)
    assert domains == [f'{study.B13_OBJECT}/seed/33'.encode('ascii')]
    assert len(training) == 2048 and all(len(row) == 32 for row in training)
    assert [row[0] for row in training] == [u for u in range(1,1025) for _ in (0,1)]
    assert [role for role, _, _ in evaluation] == [r for r in values for _ in range(16)]
    assert len(training) + len(evaluation) == 2128
    assert result['parameters'] == 2562
    assert result['training_updates'] == result['backward_calls'] == result['optimizer_calls'] == 1024
    assert result['training_episodes'] == 65536 and result['native_ticks'] == 4358144
    assert result['evaluation_episodes'] == {r:512 for r in values}
    assert result['phase_draws_evaluation'] == 16384 and result['modal_team_decisions'] == 8192
    assert result['comparison']['D_g']['mean'] == pytest.approx(.05)
    assert result['comparison']['G_U']['mean'] == pytest.approx(.1)
    assert result['modal_comparison']['D_g']['mean'] == pytest.approx(-.01)
    assert 'G_U' not in result['modal_comparison']
    assert result['evaluation_parameter_displacement'] == 0
    assert result['prior_strength']['final_log'] == pytest.approx(1.024)
    assert result['prior_strength']['final'] == pytest.approx(math.exp(1.024))
    for role in values:
        assert len(json.loads((tmp_path/(role+'.json')).read_text())) == 512
    checkpoint = torch.load(tmp_path/'final1024.pt', weights_only=True)
    assert checkpoint['object_id'] == study.B13_OBJECT and checkpoint['seed'] == 33
    assert checkpoint['learned_prior_strength'] is True
    assert float(checkpoint['model']['log_prior_strength']) == pytest.approx(1.024)
    initial = torch.load(tmp_path/'initialization.pt', weights_only=True)
    assert float(initial['log_prior_strength']) == 0
    assert len((tmp_path/'curves.jsonl').read_text().splitlines()) == 1024
    assert json.loads((tmp_path/'summary.json').read_text()) == result


def test_crossed_b13_seed_stops_before_construction(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('scientific construction reached')
    monkeypatch.setattr(study, '_run', forbidden)
    with pytest.raises(ValueError, match='seed must match'):
        study.run_b13_learned_prior1024(tmp_path, 'SYNTHETIC-TEST-SOURCE', 32)
