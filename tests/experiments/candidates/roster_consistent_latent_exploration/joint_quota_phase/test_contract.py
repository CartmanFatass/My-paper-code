"""TEST-only fixtures for B08 through B12 public phase, learner and publication."""
from dataclasses import replace
from types import SimpleNamespace
import hashlib
import json
import math

import numpy as np
import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase import policy, study
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
    PublicObservation, EpisodeTape, run_oracle_trace,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_runner import _compact_coordinate_columns
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.native_backend import (
    bind_native_backend, materialize_fixtures_compact as native_materialize_fixtures_compact,
)


def model_fixture():
    model = policy.PhasePolicy()
    model.initialize(lambda name, count: np.linspace(.13, .89, count))
    return model


def public_fixture():
    return PublicObservation(tick=24, claim_required=True, roster_event=True, new_epoch=False,
        positions=(0, 0, 30, 70, 70, 100, 110, 119), angular_ranks=tuple(range(8)),
        previous_displacements=(0,) * 8, newcomers=(False,) * 7 + (True,),
        beacon_positions=(6, 26, 46, 66, 86, 106), demands=(2, 1, 2, 1, 1, 1))


def test_public_quota_mapping_greedy_tie_and_uniform_likelihood():
    model = model_fixture()
    assert sum(p.numel() for p in model.parameters()) == 2561
    public = public_fixture()
    _, _, _, actions, _, signed = policy.quota_arrays([public])
    for phase in actions[0]:
        assert np.bincount(phase, minlength=6).tolist() == list(public.demands)
    rows, context, _ = policy.phase_features([public])
    assert tuple(rows.shape) == (1, 8, 8, 8)
    assert tuple(context.shape) == (1, 4)
    chosen, score, phase = policy.sampled_phase(model, [public], [.4])
    assert phase.tolist() == [3]
    assert chosen.tolist() == actions[:, 3].tolist()
    assert float(score) == pytest.approx(-math.log(8))  # one phase score, not eight copies
    greedy = policy.greedy_phase([public])[0]
    costs = np.abs(signed[0]).sum(axis=-1)
    assert greedy.tolist() == actions[0, next(i for i, x in enumerate(costs) if x == costs.min())].tolist()
    # All agents at one point gives every phase the same multiset of distances.
    tied = replace(public, positions=(0,) * 8)
    tie_actions = policy.quota_arrays([tied])[3]
    assert policy.greedy_phase([tied]).tolist() == tie_actions[:, 0].tolist()
    changed_private = replace(public, previous_displacements=(3,) * 8)
    assert torch.equal(policy.phase_features([changed_private])[0], rows)


def test_adam_is_one_full_return_score_step_then_baseline_and_rejects_before_mutation():
    model = model_fixture()
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4, betas=(.9, .999), eps=1e-8, foreach=False)
    baseline = torch.zeros(8, dtype=torch.float64)
    public = [public_fixture()] * 64
    _, score, _ = policy.sampled_phase(model, public, np.linspace(.001, .999, 64))
    returns = torch.linspace(.2, .9, 64, dtype=torch.float64)
    cell = torch.arange(8).repeat_interleave(8)
    before = policy.flat_parameters(model).clone()
    updated, facts = policy.adam_update(model, optimizer, returns, 16 * score, cell, baseline)
    assert facts['optimizer_calls'] == facts['backward_calls'] == 1
    assert facts['parameter_step_norm'] > 0
    assert not torch.equal(before, policy.flat_parameters(model))
    torch.testing.assert_close(updated, (1 - .95) * returns.reshape(8, 8).mean(1))
    assert torch.equal(baseline, torch.zeros_like(baseline))
    assert all(float(s['step']) == 1 for s in optimizer.state.values())
    zero_model = policy.PhasePolicy()
    zero_optimizer = torch.optim.Adam(zero_model.parameters(), lr=3e-4)
    infinite_gradient = zero_model.score.weight[0, 0].sqrt().expand(64)
    with pytest.raises(FloatingPointError, match='gradient before'):
        policy.adam_update(zero_model, zero_optimizer, returns, infinite_gradient, cell, baseline)
    assert not zero_optimizer.state
    assert torch.count_nonzero(policy.flat_parameters(zero_model)) == 0
    frozen = policy.flat_parameters(model).clone()
    _, score, _ = policy.sampled_phase(model, public, [.2] * 64)
    with pytest.raises(FloatingPointError, match='before'):
        policy.adam_update(model, optimizer, returns * float('nan'), score, cell, updated)
    assert torch.equal(frozen, policy.flat_parameters(model))
    assert all(float(s['step']) == 1 for s in optimizer.state.values())


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    torch.set_num_threads(1)
    return bind_native_backend(build_root=tmp_path_factory.mktemp('native'))


@pytest.mark.parametrize('role', ['final256', 'greedy', 'nearest'])
def test_native_current_entity_event_and_endpoints_against_action_tape_oracle(native, role):
    key = hashlib.sha256(b'SYNTHETIC-TEST-RCLE-B08-CONTRACT').digest()
    coordinates = tuple(study.EpisodeCoordinate(0, c, 0, row) for c in study.HELDOUT_CELLS for row in range(4))
    cols = _compact_coordinate_columns(coordinates)
    fixtures = native_materialize_fixtures_compact(key, 0, *cols, binding=native)
    clocks = [[] for _ in coordinates]
    newcomers = [()] * len(coordinates)
    def observe(tick, snapshots, actions):
        for lane, (snapshot, action) in enumerate(zip(snapshots, actions)):
            clocks[lane].append(tuple(action.claims))
            assert len(action.claims) == len(snapshot.positions)
            assert sorted(snapshot.angular_ranks) == list(range(len(action.claims)))
            if role != 'nearest':
                assert np.bincount(action.claims, minlength=6).tolist() == list(snapshot.demands)
            if tick == 24:
                before, after, event = (
                    len(fixtures[lane].initial_keys), len(fixtures[lane].after_keys), coordinates[lane].cell)
                assert len(snapshot.positions) == after
                assert snapshot.roster_event == (before != after)
                assert snapshot.new_epoch == event.endswith('NEW_EPOCH')
                assert set(snapshot.transport_keys) == set(fixtures[lane].after_keys)
                newcomers[lane] = tuple(x for x, flag in zip(snapshot.positions, snapshot.newcomers) if flag)
    results, scores = study.rollout(model_fixture(), role, key, native, coordinates,
                                   training=(role == 'final256'), observe=observe)
    for lane, (result, fixture) in enumerate(zip(results, fixtures)):
        tape = EpisodeTape(fixture, tuple(clocks[lane]), newcomers[lane])
        expected = run_oracle_trace(tape)[-1]
        for field in ('Y', 'U', 'F', 'tau'):
            assert result[field] == pytest.approx(getattr(expected, field))
        if scores is not None:
            expected_score = -6 * math.log(len(fixture.initial_keys)) - 10 * math.log(len(fixture.after_keys))
            assert float(scores[lane]) == pytest.approx(expected_score)


def test_four_role_paired_publication_and_all_reading_branches(tmp_path):
    values = dict(initialization=.4, final256=.3, greedy=.35, nearest=.31)
    panels = {role: [dict(cell=c, scenario=i, U=u, F=0, tau=40, Y=.5, unmet_ticks=40*u)
                    for c in study.HELDOUT_CELLS for i in range(64)] for role, u in values.items()}
    result = study.contrasts(panels)
    assert result['D_g']['mean'] == pytest.approx(.05)
    assert result['D_n']['mean'] == pytest.approx(.01)
    assert result['G_U']['mean'] == pytest.approx(.1)
    assert result['D_g']['conditional_se'] < 1e-10
    output = dict(comparison=result, means={r: study.cell_means(p) for r, p in panels.items()})
    study.write_json(tmp_path / 'summary.json', output)
    assert json.loads((tmp_path / 'summary.json').read_text()) == output
    assert len(output['means']) == 4
    assert all(len(cells) == 8 for cells in output['means'].values())
    for values, expected in [((.025,.025,.01),'useful_one_fit_signal'),
        ((.01,.03,.01),'small_positive_benefits'), ((0,.03,.01),'no_increment_over_greedy'),
        ((.03,0,.01),'local_increment_nearest_deficit'), ((0,0,.01),'no_endpoint_advantage'),
        ((.03,.03,0),'no_positive_own_initialization_learning')]:
        assert expected in study.reading(*values)


def test_b09_exact_snapshot_anchor_reuses_integer_distances_and_combined_score(monkeypatch):
    model = policy.PhasePolicy(greedy_anchored=True)
    model.initialize(lambda name, count: np.linspace(.13, .89, count))
    original = policy.quota_arrays
    calls = []
    def counted(public):
        calls.append(len(public))
        return original(public)
    monkeypatch.setattr(policy, 'quota_arrays', counted)
    for public in (public_fixture(), replace(public_fixture(), positions=(0,) * 8),
                   replace(public_fixture(), positions=tuple(range(0, 120, 10)),
                           angular_ranks=tuple(range(12)), newcomers=(False,) * 12,
                           demands=(2,) * 6)):
        n = len(public.positions)
        arrays = original([public])
        greedy = int(np.abs(arrays[-1][0]).sum(-1).argmin())
        expected = torch.full((1, n), .1 / n, dtype=torch.float64)
        expected[0, greedy] += .9
        before = len(calls)
        logp, targets = policy.phase_log_probabilities(model, [public])
        assert len(calls) == before + 1
        torch.testing.assert_close(logp.exp(), expected, rtol=1e-14, atol=1e-15)
        assert targets.tolist() == arrays[3].tolist()
        cdf = expected[0].numpy().cumsum()
        for phase in range(n):
            u = (cdf[phase] + (cdf[phase - 1] if phase else 0)) / 2
            before = len(calls)
            action, score, chosen = policy.sampled_phase(model, [public], [u])
            assert len(calls) == before + 1
            assert chosen.tolist() == [phase]
            assert action.tolist() == arrays[3][:, phase].tolist()
            assert float(score) == pytest.approx(math.log(float(expected[0, phase])))
    # A learned residual is normalized with q, and its derivative scores that same law.
    logits = torch.linspace(-.7, .6, 8, dtype=torch.float64).reshape(1, 8).requires_grad_()
    monkeypatch.setattr(model, 'forward', lambda features, context: logits)
    public = public_fixture()
    greedy = int(np.abs(original([public])[-1][0]).sum(-1).argmin())
    q = torch.full((1, 8), .1 / 8, dtype=torch.float64)
    q[0, greedy] += .9
    probability = (q * logits.detach().exp())
    probability /= probability.sum()
    _, score, phases = policy.sampled_phase(model, [public], [.04])
    phase = int(phases[0])
    assert float(score) == pytest.approx(math.log(float(probability[0, phase])))
    score.sum().backward()
    expected_gradient = -probability.clone()
    expected_gradient[0, phase] += 1
    torch.testing.assert_close(logits.grad, expected_gradient, rtol=1e-13, atol=1e-15)


def test_b09_fresh_identity_rejects_crossed_seed_before_scientific_construction(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('scientific construction reached on an invalid identity')
    monkeypatch.setattr(study.hashlib, 'sha256', forbidden)
    monkeypatch.setattr(study, 'PhasePolicy', forbidden)
    with pytest.raises(ValueError, match='seed must match'):
        study.run(tmp_path, 'TEST', seed=28, greedy_anchored=True)
    with pytest.raises(ValueError, match='seed must match'):
        study.run(tmp_path, 'TEST', seed=29, greedy_anchored=False)
    assert study.B09_OBJECT != study.OBJECT
    # Failing a competent rule must never erase an independent positive learning observation.
    flags = study.reading(-.1, -.05, .02)
    assert 'no_endpoint_advantage' in flags
    assert 'no_positive_own_initialization_learning' not in flags


def test_b10_b12_and_legacy_entries_bind_only_their_fixed_identity_and_endpoint(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(study, '_run', lambda *args: calls.append(args))
    study.run(tmp_path, 'TEST', 28)
    study.run(tmp_path, 'TEST', 29, greedy_anchored=True)
    study.run_exposure1024(tmp_path, 'TEST', 30)
    study.run_replication1024(tmp_path, 'TEST', 31)
    study.run_b12_exposure1024(tmp_path, 'TEST', 32)
    assert [c[2:] for c in calls] == [
        (28, study.OBJECT, 256, False), (29, study.B09_OBJECT, 256, True),
        (30, study.B10_OBJECT, 1024, True), (31, study.B11_OBJECT, 1024, True),
        (32, study.B12_OBJECT, 1024, True)]
    with pytest.raises(ValueError, match='seed must match'):
        study.run_exposure1024(tmp_path, 'TEST', 29)
    with pytest.raises(ValueError, match='seed must match'):
        study.run_replication1024(tmp_path, 'TEST', 30)
    with pytest.raises(ValueError, match='seed must match'):
        study.run_b12_exposure1024(tmp_path, 'TEST', 31)
    assert len(calls) == 5
    assert len({study.B10_OBJECT, study.B11_OBJECT, study.B12_OBJECT}) == 3


@pytest.mark.parametrize('entry,seed,object_id', [
    (study.run_exposure1024, 30, study.B10_OBJECT),
    (study.run_replication1024, 31, study.B11_OBJECT),
    (study.run_b12_exposure1024, 32, study.B12_OBJECT),
])
def test_b10_b12_synthetic_driver_reaches1024_and_publishes_the_actual_final_role(
        tmp_path, monkeypatch, entry, seed, object_id):
    # Wiring fixture only: no native environment, real scientific master or learning.
    original_sha256 = hashlib.sha256
    domains, updates_seen, evaluated = [], [], []
    def test_hash(data=b''):
        if data.startswith((object_id + '/').encode('ascii')):
            domains.append(data)
            return original_sha256(b'SYNTHETIC-TEST-FINAL1024-WIRING/' + data)
        return original_sha256(data)
    monkeypatch.setattr(study.hashlib, 'sha256', test_hash)
    monkeypatch.setattr(study, 'bind_native_backend',
                        lambda **kwargs: SimpleNamespace(source_sha256='SYNTHETIC-TEST-NATIVE'))
    monkeypatch.setattr(study, 'uniforms', lambda key, binding, addresses: [.5] * len(addresses))
    def fake_rollout(model, role, key, binding, coordinates, training=False):
        assert role == 'learned' and training and model.greedy_anchored
        updates_seen.append(tuple(c.update_or_scenario for c in coordinates))
        return [dict(Y=.5, U=.5, F=0, tau=40, agent_ticks=640, agent_claims=160)
                for _ in coordinates], torch.zeros(len(coordinates), dtype=torch.float64)
    monkeypatch.setattr(study, 'rollout', fake_rollout)
    def fake_update(model, optimizer, returns, scores, indices, baselines):
        return baselines, dict(backward_calls=1, optimizer_calls=1, parameter_step_norm=0)
    monkeypatch.setattr(study, 'adam_update', fake_update)
    values = dict(initialization=.4, final1024=.3, greedy=.35, nearest=.31)
    def fake_evaluate(model, role, key, binding, out):
        evaluated.append(role)
        return [dict(cell=c, scenario=i, U=values[role], F=0, tau=40, Y=.5,
                     unmet_ticks=40*values[role]) for c in study.HELDOUT_CELLS for i in range(64)]
    monkeypatch.setattr(study, 'evaluate', fake_evaluate)
    result = entry(tmp_path, 'SYNTHETIC-TEST-SOURCE', seed)
    assert domains[0] == f'{object_id}/seed/{seed}'.encode('ascii')
    assert len(updates_seen) == 2048
    assert all(len(row) == 32 for row in updates_seen)
    assert [row[0] for row in updates_seen] == [u for u in range(1,1025) for _ in (0,1)]
    assert all(len(set(row)) == 1 for row in updates_seen)
    assert evaluated == ['initialization', 'final1024', 'greedy', 'nearest']
    assert result['training_updates'] == result['backward_calls'] == result['optimizer_calls'] == 1024
    assert result['training_episodes'] == 65536 and result['native_ticks'] == 4325376
    assert result['evaluation_episodes'] == {r:512 for r in evaluated}
    assert result['comparison']['D_g']['mean'] == pytest.approx(.05)
    assert result['comparison']['G_U']['mean'] == pytest.approx(.1)
    checkpoint = torch.load(tmp_path/'final1024.pt', weights_only=True)
    assert checkpoint['updates'] == 1024 and checkpoint['seed'] == seed
    assert checkpoint['object_id'] == object_id
    assert not (tmp_path/'final256.pt').exists()
    assert len((tmp_path/'curves.jsonl').read_text().splitlines()) == 1024
    assert json.loads((tmp_path/'summary.json').read_text()) == result
