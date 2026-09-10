import csv
import json

import pytest
import torch

from experiments.candidates.vsp_02.teammate_policy_change_b01 import study
from experiments.candidates.vsp_02.teammate_policy_change_b01.learner import RecurrentPolicy, training_streams


def test_primary_negative_zero_partial_and_bins():
    rows = []
    for arm, reward in (('CARRY', 2.), ('RESET', 1.)):
        rows.extend(dict(phase='adaptation', arm=arm, episode=i + 1,
                         **{'return': reward}, joint_steps=48, complete_episode=True)
                    for i in range(16))
    full, primary, _ = study.primary_readings(rows, 16)
    assert full and primary['delta_reset_minus_carry'] == -1
    for row in rows:
        row['return'] = 0
    assert study.primary_readings(rows, 16)[1]['delta_reset_minus_carry'] == 0
    rows[-1].update(complete_episode=False, joint_steps=3)
    full, primary, partial = study.primary_readings(rows, 16)
    assert not full and primary is None
    assert partial['RESET']['episodes'] == 15
    assert partial['RESET']['joint_steps'] == 15 * 48 + 3
    assert [row['episodes_in_bin'] for row in study.training_bins(rows)] == [16, 15]


def test_collector_retains_partial_steps_and_recurrent_state():
    model = RecurrentPolicy()
    seen_hidden = []
    original = model.forward
    def forward(obs, hidden=None):
        seen_hidden.append(hidden)
        return original(obs, hidden)
    model.forward = forward
    calls = 0
    def cutoff():
        nonlocal calls
        calls += 1
        if calls == 6:
            raise TimeoutError('four actual steps')
    records = []
    with pytest.raises(TimeoutError):
        study.collect(model, training_streams(99), 1, False, cutoff, records.extend)
    assert len(records) == 1 and records[0]['joint_steps'] == 4
    assert not records[0]['complete_episode']
    assert seen_hidden[0] is None
    assert all(hidden is not None for hidden in seen_hidden[1:])
    assert seen_hidden[3] is not None  # First action after a round reset.


def install_finite_chain(monkeypatch, fail_at=None):
    """Publication fixture only: no host interaction or optimizer work."""
    calls = []
    def collect(model, streams, batch_size, changed, check, record):
        check()
        calls.append(('collect', batch_size, changed))
        index = sum(c[0] == 'collect' for c in calls)
        if fail_at == ('evaluation', index):
            record([dict(episode=i + 1, **{'return': 0.}, joint_steps=2,
                         complete_episode=False) for i in range(batch_size)])
            raise TimeoutError('finite evaluation interruption')
        reward = float(index % 3)
        record([dict(episode=i + 1, **{'return': reward}, joint_steps=48,
                     complete_episode=True) for i in range(batch_size)])
        return {}
    def update(agent, rollout, check, record):
        calls.append(('update',))
        index = sum(c[0] == 'update' for c in calls)
        complete = fail_at != ('update', index)
        steps = 16 if complete else 3
        agent.global_steps += steps
        record(dict(optimizer_steps=steps, total_global_steps=agent.global_steps,
                    complete_update=complete, mean_policy_loss=0., mean_value_loss=0.,
                    mean_entropy=0., max_pre_clip_gradient_norm=0.))
        if not complete:
            raise TimeoutError('finite update interruption')
    monkeypatch.setattr(study, 'collect', collect)
    monkeypatch.setattr(study, 'update', update)
    monkeypatch.setattr(study, 'write_figure', lambda path, bins, ev: path.write_bytes(b'fixture'))
    return calls


def test_finite_chain_counts_shared_evaluation_once_and_uses_native_returns(monkeypatch, tmp_path):
    calls = install_finite_chain(monkeypatch)
    summary = study.run_study(study.StudyConfig(17, True), tmp_path, clock=lambda: 0)
    assert summary['status'] == 'COMPLETE'
    assert not summary['scientific_comparison_complete']
    counts = summary['counts']['total']
    assert (counts['training_episodes'], counts['training_joint_steps'], counts['optimizer_steps'],
            counts['evaluation_episodes'], counts['evaluation_joint_steps']) == (48, 2304, 48, 16, 768)
    train = list(csv.DictReader((tmp_path / 'training_returns.csv').open()))
    evaluation = list(csv.DictReader((tmp_path / 'evaluation_returns.csv').open()))
    assert sum(r['arm'] == 'SHARED' for r in evaluation) == 4
    means = {arm: sum(float(r['return']) for r in train if r['arm'] == arm) / 16
             for arm in ('CARRY', 'RESET')}
    assert summary['primary']['delta_reset_minus_carry'] == means['RESET'] - means['CARRY']
    assert json.loads((tmp_path / 'summary.json').read_text())['counts'] == summary['counts']
    assert len(calls) == 10  # Seven collectors plus three updates.


@pytest.mark.parametrize('failure', [('update', 3), ('evaluation', 6)])
def test_complete_native_windows_survive_later_interruption(monkeypatch, tmp_path, failure):
    install_finite_chain(monkeypatch, failure)
    summary = study.run_study(study.StudyConfig(17, True), tmp_path, clock=lambda: 0)
    assert summary['status'] == 'TIME_LIMIT'
    assert summary['primary_window_complete'] and summary['primary'] is not None
    assert not summary['scientific_comparison_complete']
    assert summary['terminal_means']['CARRY'] is None
    assert summary['terminal_means']['RESET'] is None
    if failure[0] == 'update':
        assert summary['counts']['total']['optimizer_steps'] == 35
    else:
        assert summary['counts']['total']['evaluation_episodes'] == 8
        assert summary['counts']['total']['evaluation_joint_steps'] == 8 * 48 + 4 * 2


def test_deadline_before_compute_publishes_empty_actual_counts(monkeypatch, tmp_path):
    readings = iter([0., 61.])
    clock = lambda: next(readings, 61.)
    summary = study.run_study(study.StudyConfig(17, True), tmp_path, clock=clock)
    assert summary['status'] == 'TIME_LIMIT'
    assert summary['primary'] is None and not summary['primary_window_complete']
    assert all(value == 0 for value in summary['counts']['total'].values())
    assert 'curves.png' in summary['missing_outputs']
    assert (tmp_path / 'summary.json').is_file()
