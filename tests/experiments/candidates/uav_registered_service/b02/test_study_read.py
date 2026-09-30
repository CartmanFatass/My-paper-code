import json

import numpy as np
import pytest

from experiments.candidates.uav_registered_service.b01 import study as old
from experiments.candidates.uav_registered_service.b02 import study, read, run, metrics
from experiments.candidates.uav_registered_service.b02.scheduler import Scheduler


def collect(tmp_path, arm, seed=98101, horizon=8, **kwargs):
    env = study.factory(seed)
    env.env.max_steps = horizon
    out = tmp_path / f'{arm}-{seed}'
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        row = study.collect_episode(env, arm, seed, out, counts, horizon=horizon, **kwargs)
    finally:
        env.close()
    return row, read.load_episode(row['raw']['path']), counts


@pytest.mark.parametrize('arm', study.ARMS)
def test_full_small_fixture_endpoint_reader_and_materialize_once(tmp_path, arm, monkeypatch):
    row, raw, counts = collect(tmp_path, arm)
    assert counts['team_steps'] == 8 and counts['complete_episodes'] == 1
    # The reader can neither construct nor advance a new native episode.
    from envs.pettingzoo.uav_env import MultiUAVEnv
    def forbid(*args, **kwargs):
        raise AssertionError('reader constructed or advanced environment')
    monkeypatch.setattr(MultiUAVEnv, '__init__', forbid)
    monkeypatch.setattr(MultiUAVEnv, 'step', forbid)
    for array in raw.values():
        array.setflags(write=False)
    result = read.verify_episode(row, raw)
    assert result['verified_steps'] == 8 and result['max_native_J_error'] < 1e-12
    assert row['F'] == sum(row['per_window_coverage'])
    if arm in ('G', 'O'):
        assert raw['terminal_history_complete'] and raw['model_valid'].all()
        assert result['verified_model_transitions'] == 8
        assert raw['forecast_lengths'].tolist() == [4, 2]
        assert np.isnan(raw['forecast'][-1, :, 2:]).all()
    if arm == 'G':
        assert row['gate_computed_rounds'] == row['gate_eligible_rounds'] == 2
        assert raw['gate_executed_transitions'].sum() == row['gate_executed_transitions']
        assert row['gate_truth_scope'].startswith('evaluator only')


@pytest.mark.parametrize('arm', ['O', 'S2'])
def test_unchanged_frozen_exact_fixture_equivalence(tmp_path, arm):
    row, raw, _ = collect(tmp_path, arm, seed=98102)
    env = old.factory(98102)
    env.env.max_steps = 8
    out = tmp_path / 'old'
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        retained = old.collect_episode(env, arm, 98102, out, counts, horizon=8)
    finally:
        env.close()
    saved = read.load_episode(retained['raw']['path'])
    assert raw.keys() == saved.keys()
    timing = {'c_wall', 'c_cpu', 'scheduler_wall', 'scheduler_cpu', 'history_wall', 'history_cpu',
              'prefix_wall', 'prefix_cpu', 'candidate_wall', 'candidate_cpu', 'terminal_history_wall', 'terminal_history_cpu'}
    for name in saved:
        if name not in timing:
            np.testing.assert_array_equal(raw[name], saved[name])
    assert row['J'] == retained['J'] and row['F'] == retained['F']
    assert row['controller_counts'] == retained['controller_counts']


def test_censored_then_all_team_late_fallback_and_terminal_reader(tmp_path):
    class FirstMissing(Scheduler):
        def decide(self, *args, **kwargs):
            if args[3] == 0:
                kwargs['started'] -= 10
            return super().decide(*args, **kwargs)
    row, raw, _ = collect(tmp_path, 'G', seed=98103, horizon=12, scheduler_type=FirstMissing)
    assert raw['timely'].tolist() == [False, True, True]
    assert raw['gate_computed'].tolist() == [False, True, True]
    assert raw['gate_eligible'].tolist() == [False, False, False]
    assert raw['terminal_history_start'] == 4 and not raw['model_valid'][:4].any()
    assert read.verify_episode(row, raw)['verified_model_transitions'] == 8
    class LaterLate(Scheduler):
        def decide(self, *args, **kwargs):
            if args[3] > 0:
                kwargs['started'] -= 10
            return super().decide(*args, **kwargs)
    row, raw, _ = collect(tmp_path, 'G', seed=98104, horizon=12, scheduler_type=LaterLate)
    assert raw['timely'].tolist() == [True, False, False]
    np.testing.assert_array_equal(raw['commands'][2:], np.broadcast_to(raw['commitments'][0], (10, 5, 3)))
    assert not raw['gate_computed'][1:].any()
    assert read.verify_episode(row, raw)['verified_model_transitions'] == 12


@pytest.mark.parametrize('field', ['gate_released', 'gate_eligible', 'gate_window', 'ordering_keys',
                                   'gate_actual_prefix_bits', 'model_contacts', 'gate_executed_transitions',
                                   'gate_command_changed', 'terminal_last'])
def test_reader_detects_gate_key_history_and_exposure_corruption(tmp_path, field):
    row, raw, _ = collect(tmp_path, 'G', seed=98105)
    corrupt = {key: value.copy() for key, value in raw.items()}
    if field == 'ordering_keys':
        q, mask = corrupt['candidate_order'][0, 0]
        corrupt[field][0, q, mask, 0] += 1
    elif field == 'gate_window':
        corrupt[field][0] += 1
    elif field in ('gate_actual_prefix_bits', 'model_contacts'):
        corrupt[field][0, 0] = ~corrupt[field][0, 0]
    elif field == 'terminal_last':
        corrupt[field][0] += 1
    else:
        corrupt[field][0] = not bool(corrupt[field][0]) if corrupt[field].dtype == bool else corrupt[field][0] + 1
    with pytest.raises(AssertionError):
        read.verify_episode(row, corrupt)


@pytest.mark.parametrize('arm', ['G', 'S2'])
def test_full_horizon_declared_candidate_physics_and_terminal(tmp_path, arm):
    row, raw, _ = collect(tmp_path, arm, seed=98106, horizon=256)
    result = read.verify_episode(row, raw)
    assert result['verified_steps'] == 256
    assert raw['round_tick'][[0, 15, 31, 63]].tolist() == [0, 60, 124, 252]
    assert raw['forecast_lengths'][-1] == 2 and np.isnan(raw['forecast'][-1, :, 2:]).all()
    if arm == 'G':
        assert not raw['gate_eligible'][[15, 31, 47]].any()
        assert result['candidate_physics_pairs'] >= raw['candidate_plans'][[0, 15, 31, 63]].sum()
        assert raw['gate_actual_prefix_bits'][-1].tolist() == raw['actual_contacts'][192:254].any(axis=0).tolist()
    else:
        assert result['additional_candidate_physics_scope'].endswith('reports0,60,124,252')


def test_truth_report_prefix_and_future_window_are_distinct():
    horizon = 128
    raw = study.allocate_raw(horizon, 'G', np.zeros((50, 2)), b'x')
    raw['completed_steps'][...] = horizon
    raw['round_count'][...] = horizon // 4
    raw['round_tick'][:] = np.arange(0, horizon, 4)
    index = 14  # report56: truth at report excludes t56/t57, arrival includes them.
    raw['gate_computed'][index] = raw['gate_eligible'][index] = raw['gate_released'][index] = raw['timely'][index] = True
    raw['gate_window'][index] = 0
    raw['prefix_windows'][index, 0] = True
    raw['connections'][57, :, :49] = True
    raw['model_valid'][:] = True
    raw['model_contacts'][57] = True
    from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
    add_contact_raw(raw, horizon)
    metrics.add_gate_raw(raw, horizon)
    assert not raw['gate_actual_report_bits'][index].any()
    assert raw['gate_actual_prefix_bits'][index].sum() == 49
    result = metrics.gate_metrics(raw, horizon)
    assert result['gate_prefix_false_releases'] == result['gate_timely_prefix_false_releases'] == 1
    assert result['gate_release_prefix_missing_user_events'] == 1
    assert result['gate_windows'][0]['next_window_missing_users'] == 50
    read.verify_gate_evaluation(raw, horizon)


def test_fixed_panel_order_source_identity_and_incomplete_refusal(tmp_path):
    assert study.SEED == 29309000 and study.WORLDS == 64
    assert len(study.ARM_ORDERS) == 6
    for position in range(3):
        assert all(sum(order[position] == arm for order in study.ARM_ORDERS) == 2 for arm in study.ARMS)
    identities = {row['path']: row for row in study.source_identities()}
    for path in ('experiments/candidates/uav_registered_service/b01/history.py',
                 'experiments/candidates/uav_registered_service/b02/scheduler.py', 'envs/pettingzoo/uav_radio.py'):
        assert identities[path]['bytes'] > 0 and len(identities[path]['sha256']) == 64
    assert not hasattr(study, 'CPU_LIMIT_SECONDS')
    with pytest.raises(ValueError):
        study.paired_reading([], [98107])
    class Broken:
        def reset(self, **kwargs):
            raise RuntimeError('fixture reset failure')
        def close(self):
            pass
    result = study.run_batch(tmp_path / 'broken', 'fixture', make_env=lambda seed: Broken(), seeds=(98107,), horizon=8)
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE' and 'paired' not in result
    assert result['counts']['team_steps'] == 0 and result['config']['cpu_limit_seconds'] is None
    with pytest.raises(ValueError):
        read.read_result(tmp_path / 'broken')


def test_synthetic_three_arm_batch_complete_paired_vector(tmp_path):
    def small_env(seed):
        env = study.factory(seed)
        env.env.max_steps = 8
        return env
    result = study.run_batch(tmp_path / 'fixture', 'fixture-sha', make_env=small_env, seeds=(98108,), horizon=8)
    assert result['status'] == 'COMPLETE' and not result['scientific_invocation']
    assert result['counts'] == dict(constructors=1, explicit_resets=3, native_step_calls=24, team_steps=24,
                                    complete_episodes=3, fit_started=0, optimizer_steps=0)
    assert set(result['paired']['comparisons']) == {'O-S2', 'G-S2', 'G-O'}
    assert result['paired']['primary'] == 'G-O'
    for row in result['rows']:
        assert 'F' in row and 'closed_unserved_gaps' in row and 'satisfied_window_histogram' in row
        read.verify_episode(row, read.load_episode(row['raw']['path']))
    assert json.loads((tmp_path / 'fixture' / 'summary.json').read_text()) == result
    with pytest.raises(ValueError):
        read.read_result(tmp_path / 'fixture')


def test_admission_before_effects_and_fixed_seed(tmp_path, monkeypatch):
    from scripts import hmasd_admission
    def refuse(*args, **kwargs):
        assert kwargs['direction'] == 'uav_registered_service'
        raise RuntimeError('fixture refusal')
    monkeypatch.setattr(hmasd_admission, 'require_admission', refuse)
    with pytest.raises(RuntimeError, match='fixture refusal'):
        run.main(['--out', str(tmp_path / 'absent'), '--launch-sha', 'fixture', '--seed', '29309000'])
    assert not (tmp_path / 'absent').exists()
    with pytest.raises(SystemExit):
        run.main(['--out', str(tmp_path / 'absent'), '--launch-sha', 'fixture', '--seed', '98109'])


def test_saved_panel_reader_integration_and_single_materialization(tmp_path, monkeypatch):
    # A tiny fixture registration exercises the complete file reader without panel exposure.
    seed = 98110
    def small_env(value):
        env = study.factory(value)
        env.env.max_steps = 8
        return env
    out = tmp_path / 'read-integration'
    summary = study.run_batch(out, 'fixture-sha', make_env=small_env, seeds=(seed,), horizon=8)
    summary['scientific_invocation'] = True
    study.write_json(out / 'summary.json', summary)
    study.write_json(out / 'process-exit.json', dict(exit_code=0))
    monkeypatch.setattr(read, 'SEED', seed)
    monkeypatch.setattr(read, 'WORLDS', 1)
    monkeypatch.setattr(read, 'HORIZON', 8)
    original = read.load_episode
    loaded = []
    def load(path):
        loaded.append(path)
        return original(path)
    monkeypatch.setattr(read, 'load_episode', load)
    from envs.pettingzoo.uav_env import MultiUAVEnv
    def forbid(*args, **kwargs):
        raise AssertionError('pure reader created native episode')
    monkeypatch.setattr(MultiUAVEnv, '__init__', forbid)
    monkeypatch.setattr(MultiUAVEnv, 'step', forbid)
    result = read.read_result(out)
    assert result['status'] == 'VERIFIED_COMPLETE' and result['verified_raw_files'] == 3
    assert len(loaded) == len(set(loaded)) == 3
    paired = result['paired']['comparisons']['G-O']
    assert 'closed_unserved_gaps.mean' in paired and 'satisfied_window_histogram.4' in paired
    assert 'per_window_coverage.0' in paired and 'left_censored_gaps' in paired
    summary['config']['source_identities'][0]['sha256'] = 'corrupt'
    study.write_json(out / 'summary.json', summary)
    with pytest.raises(AssertionError, match='source bytes'):
        read.read_result(out)
    assert len(loaded) == 3
