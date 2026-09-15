"""Synthetic contract checks only; no selected B03 scientific execution."""
import importlib.util
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_history_b02 import binding as b02_binding
from experiments.candidates.vap_folr_core.entity_history_b03 import binding


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


@pytest.mark.parametrize('change,message', [
    ({'object': b02_binding.OBJECT}, 'B03 Generic arm'),
    ({'training_seed': b02_binding.TRAINING_SEED}, 'B03 Generic seed binding'),
])
def test_b03_rejects_foreign_generic_binding(change, message):
    with pytest.raises(ValueError, match=message):
        binding.require_generic(complete_generic(**change))


def test_incomplete_b03_generic_permits_bank_only_facts_without_primary():
    generic = complete_generic(status='incomplete', training_episodes=3199,
                               training_ticks=63980, optimizer_steps=3168,
                               evaluation_episodes=0, evaluation_ticks=0,
                               evaluation_returns=[])
    assert binding.require_generic(generic) is generic
    bank = dict(complete_generic(), arm='BANK', evaluation_returns=[2.0] * 128)
    runner, _ = load_runner('folr_b03_incomplete_comparator_test')
    runner.add_bank_comparison(bank, generic, True, binding.complete_exposure)
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


def run_fake(monkeypatch, tmp_path, mode, arm, generic=None):
    runner, path = load_runner(f'folr_{mode}_{arm}_runner_test')
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment, learner, retained_use
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
    selected = binding if mode == 'b03' else b02_binding
    mode_arg = '--fresh-learning-b03' if mode == 'b03' else '--fresh-learning'
    out = tmp_path / f'{mode}_{arm.lower()}'
    argv = [str(path), '--arm', arm, mode_arg,
            '--seed', str(selected.TRAINING_SEED),
            '--evaluation-seed', str(selected.EVALUATION_SEED),
            '--cap-seconds', '3600', '--launch-sha', 'synthetic-source-revision',
            '--out', str(out)]
    if generic is not None:
        generic_path = tmp_path / f'{mode}_generic.json'
        generic_path.write_text(json.dumps(generic))
        argv += ['--generic-summary', str(generic_path)]
    monkeypatch.setattr('sys.argv', argv)
    runner.main()
    return json.loads((out / 'summary.json').read_text()), out, seed_calls


@pytest.mark.parametrize('mode,selected', [('b02', b02_binding), ('b03', binding)])
def test_fresh_modes_route_separate_identity_and_preserve_learning(mode, selected,
                                                                   tmp_path, monkeypatch):
    summary, out, seed_calls = run_fake(monkeypatch, tmp_path, mode, 'GENERIC_RETAIN')
    assert FakeLearner.constructed == ['GENERIC_RETAIN']
    assert summary['object'] == selected.OBJECT
    assert summary['training_identity_kind'] == 'fresh_unscreened_fit'
    assert (summary['training_seed'], summary['evaluation_seed']) == (
        selected.TRAINING_SEED, selected.EVALUATION_SEED)
    assert (summary['training_episodes'], summary['training_ticks'],
            summary['optimizer_steps']) == (5000, 100000, 4969)
    assert (summary['evaluation_episodes'], summary['evaluation_ticks']) == (128, 2560)
    assert summary['status'] == 'complete'
    assert (out / 'final.pt').read_text() == 'GENERIC_RETAIN'
    assert seed_calls == [
        ('python', selected.TRAINING_SEED),
        ('numpy', selected.TRAINING_SEED),
        ('torch', selected.TRAINING_SEED),
        ('python', selected.EVALUATION_SEED),
        ('numpy', selected.EVALUATION_SEED),
        ('torch', selected.EVALUATION_SEED),
    ]


@pytest.mark.parametrize('generic,reason', [
    (complete_generic(status='incomplete', training_episodes=3199,
                      training_ticks=63980, optimizer_steps=3168,
                      evaluation_episodes=0, evaluation_ticks=0,
                      evaluation_returns=[]), 'incomplete'),
    (complete_generic(training_ticks=99980), 'wrong complete exposure'),
])
def test_b03_bank_constructs_fresh_learner_without_invalid_primary(
        generic, reason, tmp_path, monkeypatch):
    summary, out, _ = run_fake(monkeypatch, tmp_path, 'b03', 'BANK', generic)
    assert FakeLearner.constructed == ['BANK']
    assert summary['object'] == binding.OBJECT
    assert summary['native_panel']['mean'] == 2.0
    assert summary['pair_primary'] is None
    assert reason in summary['pair_primary_unavailable']
    assert (out / 'final.pt').read_text() == 'BANK'


def test_complete_b03_generic_produces_the_b03_primary(tmp_path, monkeypatch):
    summary, _, _ = run_fake(monkeypatch, tmp_path, 'b03', 'BANK', complete_generic())
    assert summary['pair_primary']['bank_minus_generic'] == 2.0
    assert summary['pair_primary']['rule'] == 'BANK_ABOVE_MEI'


def test_b03_mode_rejects_retained_use_and_checkpoint(tmp_path, monkeypatch):
    runner, path = load_runner('folr_b03_retained_rejection_test')
    common = [str(path), '--arm', 'BANK', '--fresh-learning-b03',
              '--seed', '781501', '--evaluation-seed', '1781501',
              '--cap-seconds', '3600', '--launch-sha', 'synthetic-source-revision',
              '--out', str(tmp_path / 'out')]
    monkeypatch.setattr('sys.argv', common + ['--reference-use'])
    with pytest.raises(SystemExit):
        runner.main()
    monkeypatch.setattr('sys.argv', common + ['--retained-checkpoint', str(tmp_path / 'old.pt')])
    with pytest.raises(SystemExit):
        runner.main()
