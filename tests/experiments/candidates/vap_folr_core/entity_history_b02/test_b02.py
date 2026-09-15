"""Synthetic contract checks only; no selected B02 scientific execution."""
import importlib.util
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_history_b02 import binding


def complete_generic(**changes):
    summary = dict(object=binding.OBJECT, arm='GENERIC_RETAIN', status='complete',
                   training_seed=binding.TRAINING_SEED,
                   evaluation_seed=binding.EVALUATION_SEED,
                   training_episodes=5000, training_ticks=100000,
                   optimizer_steps=4969, evaluation_episodes=128,
                   evaluation_ticks=2560, evaluation_returns=[0.0] * 128)
    summary.update(changes)
    return summary


def load_runner(name):
    path = Path(__file__).resolve().parents[5] / 'scripts/run_folr_entity_history_b01.py'
    spec = importlib.util.spec_from_file_location(name, path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner, path


@pytest.mark.parametrize('delta,rule', [(1.0, 'WITHIN_MEI'), (-1.0, 'WITHIN_MEI'),
                                      (1.1, 'BANK_ABOVE_MEI'),
                                      (-1.1, 'GENERIC_ABOVE_MEI')])
def test_b02_binding_and_original_mei_boundaries(delta, rule):
    generic = complete_generic()
    assert binding.require_generic(generic) is generic
    bank = dict(generic, arm='BANK', evaluation_returns=[delta] * 128)
    runner, _ = load_runner('folr_b02_mei_test')
    runner.add_bank_comparison(bank, generic, require_complete_exposure=True)
    assert bank['pair_primary']['rule'] == rule


@pytest.mark.parametrize('change,message', [
    ({'object': 'FOLR_ENTITY_HISTORY_B01_781201'}, 'B02 Generic arm'),
    ({'training_seed': 781201}, 'B02 Generic seed binding'),
])
def test_foreign_generic_identity_is_rejected(change, message):
    with pytest.raises(ValueError, match=message):
        binding.require_generic(complete_generic(**change))


def test_wrong_complete_exposure_cannot_produce_pair():
    generic = complete_generic(training_ticks=99980)
    assert binding.require_generic(generic) is generic
    assert not binding.complete_exposure(generic)
    bank = dict(complete_generic(), arm='BANK', evaluation_returns=[2.0] * 128)
    runner, _ = load_runner('folr_b02_wrong_exposure_test')
    runner.add_bank_comparison(bank, generic, require_complete_exposure=True)
    assert bank['pair_primary'] is None
    assert 'wrong complete exposure' in bank['pair_primary_unavailable']


def test_incomplete_selected_generic_is_accepted_for_own_arm_only():
    generic = complete_generic(status='incomplete', training_episodes=4032,
                               training_ticks=80640, optimizer_steps=4001,
                               evaluation_episodes=0, evaluation_ticks=0,
                               evaluation_returns=[])
    assert binding.require_generic(generic) is generic
    bank = dict(complete_generic(), arm='BANK', evaluation_returns=[2.0] * 128)
    runner, _ = load_runner('folr_b02_incomplete_comparator_test')
    runner.add_bank_comparison(bank, generic)
    assert bank['pair_primary'] is None
    assert 'incomplete; no BANK-minus-Generic estimate' in bank['pair_primary_unavailable']


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
        path.write_text(self.actor.arm)


@pytest.mark.parametrize('arm,generic_status', [('GENERIC_RETAIN', None),
                                                ('BANK', 'incomplete'),
                                                ('BANK', 'wrong_exposure')])
def test_fresh_runner_constructs_full_learner_and_publishes_truthfully(
        arm, generic_status, tmp_path, monkeypatch):
    runner, path = load_runner('folr_b02_fresh_runner_' + arm)
    from experiments.candidates.vap_folr_core.entity_history_b01 import learner, retained_use
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection
    FakeLearner.constructed = []
    monkeypatch.setattr(learner, 'Learner', FakeLearner)
    monkeypatch.setattr(retained_use, 'load_retained_bank',
                        lambda *_: pytest.fail('fresh learning must not load retained weights'))
    monkeypatch.setattr(environment, 'EntityHistoryEnv', lambda **_: object())
    monkeypatch.setattr(collection, 'collect',
                        lambda env, actor, epsilon: ({}, 2.0 if actor.arm == 'BANK' else 0.0, {}))
    monkeypatch.setattr(collection, 'sample', lambda replay: {})
    monkeypatch.setattr(collection, 'epsilon_at', lambda ticks: 0.0)
    monkeypatch.setattr(torch, 'set_num_interop_threads', lambda _: None)
    monkeypatch.setattr(runner.time, 'monotonic', lambda: runner.START + 3601.0)
    seed_calls = []
    monkeypatch.setattr(random, 'seed', lambda seed: seed_calls.append(('python', seed)))
    monkeypatch.setattr(np.random, 'seed', lambda seed: seed_calls.append(('numpy', seed)))
    monkeypatch.setattr(torch, 'manual_seed', lambda seed: seed_calls.append(('torch', seed)))
    out = tmp_path / arm.lower()
    argv = [str(path), '--arm', arm, '--fresh-learning', '--seed', '781401',
            '--evaluation-seed', '1781401', '--cap-seconds', '3600',
            '--launch-sha', 'synthetic-source-revision', '--out', str(out)]
    if generic_status == 'incomplete':
        generic = complete_generic(status='incomplete', training_episodes=3199,
                                   training_ticks=63980, optimizer_steps=3168,
                                   evaluation_episodes=0, evaluation_ticks=0,
                                   evaluation_returns=[])
    elif generic_status == 'wrong_exposure':
        generic = complete_generic(training_ticks=99980)
    if generic_status:
        generic_path = tmp_path / 'generic.json'
        generic_path.write_text(json.dumps(generic))
        argv += ['--generic-summary', str(generic_path)]
    monkeypatch.setattr('sys.argv', argv)
    runner.main()
    summary = json.loads((out / 'summary.json').read_text())
    assert FakeLearner.constructed == [arm]
    assert summary['object'] == binding.OBJECT
    assert summary['training_identity_kind'] == 'fresh_unscreened_fit'
    assert (summary['training_seed'], summary['evaluation_seed'],
            summary['cap_seconds']) == (781401, 1781401, 3600)
    assert (summary['training_episodes'], summary['training_ticks'],
            summary['optimizer_steps']) == (5000, 100000, 4969)
    assert (summary['evaluation_episodes'], summary['evaluation_ticks']) == (128, 2560)
    assert summary['status'] == 'complete' and summary['runner_wall_seconds'] >= 3600
    assert (out / 'final.pt').read_text() == arm
    assert seed_calls == [
        ('python', 781401), ('numpy', 781401), ('torch', 781401),
        ('python', 1781401), ('numpy', 1781401), ('torch', 1781401),
    ]
    if arm == 'BANK':
        assert summary['pair_primary'] is None
        assert summary['native_panel']['mean'] == 2.0
        expected = 'incomplete' if generic_status == 'incomplete' else 'wrong complete exposure'
        assert expected in summary['pair_primary_unavailable']


def test_fresh_mode_rejects_retained_mixing(tmp_path, monkeypatch):
    runner, path = load_runner('folr_b02_rejection_test')
    common = [str(path), '--arm', 'BANK', '--fresh-learning', '--seed', '781401',
              '--evaluation-seed', '1781401', '--cap-seconds', '3600',
              '--launch-sha', 'synthetic-source-revision', '--out', str(tmp_path / 'out')]
    monkeypatch.setattr('sys.argv', common + ['--reference-use'])
    with pytest.raises(SystemExit):
        runner.main()
    checkpoint = tmp_path / 'retained.pt'
    monkeypatch.setattr('sys.argv', common + ['--retained-checkpoint', str(checkpoint)])
    with pytest.raises(SystemExit):
        runner.main()
