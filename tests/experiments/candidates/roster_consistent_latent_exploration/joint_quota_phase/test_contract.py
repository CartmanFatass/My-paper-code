"""TEST-only fixtures for B08's changed public phase, learner and publication."""
from dataclasses import replace
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
    bind_native_backend, native_materialize_fixtures_compact,
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
