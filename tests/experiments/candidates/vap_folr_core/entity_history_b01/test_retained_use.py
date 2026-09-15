"""Synthetic support fixtures only; no selected scientific seed or endpoint run."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_history_b01 import retained_use as use
from experiments.candidates.vap_folr_core.entity_history_b01.environment import EntityHistoryEnv
from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor


@pytest.fixture(scope='module', autouse=True)
def one_thread():
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)


def summaries(delta=0.0):
    generic = dict(object=use.USE_OBJECT, arm='GENERIC_RETAIN', status='complete',
                   training_seed=use.GENERIC_SEED, evaluation_seed=use.GENERIC_EVALUATION_SEED,
                   training_episodes=5000, training_ticks=100000, optimizer_steps=4969,
                   evaluation_episodes=128, evaluation_ticks=2560, evaluation_returns=[0.0]*128)
    bank = dict(generic, arm='BANK', training_seed=None, retained_training_seed=use.BANK_TRAINING_SEED,
                evaluation_seed=use.BANK_EVALUATION_SEED, training_episodes=0, training_ticks=0,
                optimizer_steps=0, evaluation_returns=[delta]*128)
    return generic, bank


@pytest.mark.parametrize('delta,rule', [(1.0, 'GENERIC_ONLY_WITHIN_MEI'),
                                      (-1.0, 'GENERIC_ONLY_WITHIN_MEI'),
                                      (1.1, 'OPTIONAL_BANK_REFERENCE'),
                                      (-1.1, 'GENERIC_ONLY_BANK_WORSE')])
def test_nonpaired_primary_and_missing_endpoint(delta, rule):
    generic, bank = summaries(delta)
    result = use.reference_use_result(generic, bank)
    assert result['rule'] == rule and result['d_use'] == delta
    assert result['training_pairs'] == 0 and result['paired_difference_se'] is None
    assert result['new_bank_training_instances'] == 0
    generic['status'] = 'incomplete'
    with pytest.raises(ValueError, match='Generic full endpoint'):
        use.reference_use_result(generic, bank)
    generic['status'] = 'complete'
    bank['evaluation_seed'] = generic['evaluation_seed']
    with pytest.raises(ValueError, match='fixed BANK new panel'):
        use.reference_use_result(generic, bank)


def fixture_checkpoint(tmp_path):
    torch.manual_seed(671331)
    actor = Actor('BANK')
    checkpoint = tmp_path/'synthetic_actor_fixture.pt'
    torch.save(dict(arm='BANK', updates=4969, actor=actor.state_dict()), checkpoint)
    return actor, checkpoint


def test_fixed_loader_exact_weights_and_lifetime_reset(tmp_path):
    original, checkpoint = fixture_checkpoint(tmp_path)
    loaded = use.load_retained_bank(checkpoint)
    assert not loaded.training and all(not p.requires_grad for p in loaded.parameters())
    for key, tensor in original.state_dict().items():
        torch.testing.assert_close(loaded.state_dict()[key], tensor, rtol=0, atol=0)
    env = EntityHistoryEnv(difficulty='easy', vision=1, seed=671332)
    env.reset()
    batch = {key: torch.as_tensor(value)[None, None]
             for key, value in env.observation(np.zeros(5, dtype=int)).items()}
    assert not batch['continuation'].any()
    q_empty, h_empty = loaded(batch)
    q_old, h_old = loaded(batch, torch.ones(1, 5, 5, 16))
    torch.testing.assert_close(q_empty, q_old)
    torch.testing.assert_close(h_empty, h_old)
    assert all(p.grad is None for p in loaded.parameters())


def test_bank_runner_no_learner_and_truthful_publication(tmp_path, monkeypatch):
    _, checkpoint = fixture_checkpoint(tmp_path)
    generic, _ = summaries()
    generic_file = tmp_path/'synthetic_generic_summary.json'
    generic_file.write_text(json.dumps(generic))
    from experiments.candidates.vap_folr_core.entity_history_b01 import learner
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment
    from experiments.candidates.vap_folr_core.public_lifecycle_b01 import collection
    monkeypatch.setattr(learner, 'Learner', lambda *a: pytest.fail('BANK must not construct a learner'))
    monkeypatch.setattr(collection, 'collect', lambda *a: ({}, 2.0, {}))
    monkeypatch.setattr(environment, 'EntityHistoryEnv', lambda **kw: object())
    seed_calls = []
    monkeypatch.setattr('random.seed', lambda seed: seed_calls.append(('python', seed)))
    monkeypatch.setattr(np.random, 'seed', lambda seed: seed_calls.append(('numpy', seed)))
    monkeypatch.setattr(torch, 'manual_seed', lambda seed: seed_calls.append(('torch', seed)))
    monkeypatch.setattr(torch, 'set_num_interop_threads', lambda n: None)  # already set above
    module_path = Path(__file__).resolve().parents[5]/'scripts/run_folr_entity_history_b01.py'
    spec = importlib.util.spec_from_file_location('folr_reference_runner_test', module_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    out = tmp_path/'synthetic_publication'
    monkeypatch.setattr('sys.argv', [str(module_path), '--arm', 'BANK', '--reference-use',
        '--seed', str(use.BANK_TRAINING_SEED), '--evaluation-seed', str(use.BANK_EVALUATION_SEED),
        '--cap-seconds', '300', '--launch-sha', 'synthetic-support-fixture', '--out', str(out),
        '--generic-summary', str(generic_file), '--retained-checkpoint', str(checkpoint)])
    runner.main()
    result = json.loads((out/'summary.json').read_text())
    assert result['status'] == 'complete' and result['training_seed'] is None
    assert result['training_episodes'] == result['optimizer_steps'] == result['actor_change_l2'] == 0
    assert result['use_primary']['d_use'] == 2.0 and 'pair_primary' not in result
    assert result['retained_checkpoint'] == str(checkpoint)
    assert not (out/'final.pt').exists()
    assert seed_calls == [(lib, seed) for seed in (use.BANK_TRAINING_SEED, use.BANK_EVALUATION_SEED)
                          for lib in ('python', 'numpy', 'torch')]
    # A later panel failure must retain its completed prefix and no primary.
    def failed_panel(*args):
        raise RuntimeError('synthetic evaluation failure')
    monkeypatch.setattr(collection, 'collect', failed_panel)
    failed_out = tmp_path/'synthetic_failure'
    argv = list(__import__('sys').argv)
    argv[argv.index('--out') + 1] = str(failed_out)
    monkeypatch.setattr('sys.argv', argv)
    with pytest.raises(RuntimeError, match='synthetic evaluation failure'):
        runner.main()
    failed = json.loads((failed_out/'summary.json').read_text())
    assert failed['status'] == 'incomplete' and failed['evaluation_episodes'] == 0
    assert 'use_primary' not in failed and 'pair_primary' not in failed
