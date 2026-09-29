import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01 import study as previous
from experiments.candidates.uav_radio_activation.b03 import study
from experiments.candidates.uav_radio_activation.b03.read import verify_episode
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler


def collect(tmp_path, arm, seed=811, horizon=12, **kwargs):
    env = study.factory(seed)
    env.env.max_steps = horizon
    out = tmp_path / arm
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        row = study.collect_episode(env, arm, seed, out, counts, horizon=horizon, **kwargs)
    finally:
        env.close()
    with np.load(row['raw']['path']) as stored:
        raw = {key: stored[key].copy() for key in stored.files}
    return row, raw, counts


@pytest.mark.parametrize('arm', ['S2', 'T2'])
def test_delayed_commitments_and_complete_native_reconstruction(tmp_path, arm):
    row, raw, counts = collect(tmp_path, arm)
    assert counts == dict(explicit_resets=1, native_step_calls=12, team_steps=12, complete_episodes=1)
    assert row['controller_counts']['decisions'] == 15
    assert row['controller_counts']['ingests'] == 15
    np.testing.assert_array_equal(raw['c_decision'], [True, False, False, False] * 3)
    np.testing.assert_array_equal(raw['mask'][:2], 31)
    np.testing.assert_array_equal(raw['commands'][:2], np.broadcast_to(raw['proposals'][0], (2, 5, 3)))
    for index, tick in enumerate((0, 4, 8)):
        length = min(4, 12 - tick - 2)
        np.testing.assert_array_equal(raw['commands'][tick + 2:tick + 2 + length], np.broadcast_to(raw['commitments'][index], (length, 5, 3)))
        np.testing.assert_array_equal(raw['mask'][tick + 2:tick + 2 + length], raw['applied_mask'][index])
        assert raw['forecast_lengths'][index] == length
        assert raw['prefix_ticks'][index] == 2
        assert raw['scheduler_cpu'][index] >= raw['c_cpu'][tick]
        assert raw['scheduler_wall'][index] >= raw['c_wall'][tick]
    reading = verify_episode(row, raw)
    assert reading['verified_steps'] == 12
    assert reading['max_native_J_error'] < 1e-12
    assert reading['candidate_physics_pairs'] > 0
    assert reading['report_age_ticks']['count'] == 10
    assert reading['report_age_ticks']['mean'] == 3.3
    assert raw['round_tick'].tolist() == [0, 4, 8]
    assert np.isnan(raw['forecast'][-1, :, 2:]).all()
    corrupted = {key: value.copy() for key, value in raw.items()}
    corrupted['mask'][0] = 1
    with pytest.raises(AssertionError, match='mask arrived'):
        verify_episode(row, corrupted, verify_observations=False)
    corrupted = {key: value.copy() for key, value in raw.items()}
    corrupted['commitments'][0, 4] = -raw['commitments'][0, 4] + .5
    with pytest.raises(AssertionError):
        verify_episode(row, corrupted, verify_observations=False)


class KnownC(LocalController):
    def act(self, obs, tick):
        _, diagnostics = super().act(obs, tick)
        return COMMANDS[1 + tick // 4].copy(), diagnostics


class FirstThenLate(Scheduler):
    def decide(self, *args, **kwargs):
        if args[3] > 0:
            kwargs['started'] -= 10
        return super().decide(*args, **kwargs)


def test_miss_holds_previous_actual_team_not_new_suggestions(tmp_path):
    row, raw, _ = collect(tmp_path, 'S2', seed=812, scheduler_type=FirstThenLate, controller_type=KnownC)
    assert raw['timely'].tolist() == [True, False, False]
    assert np.any(raw['proposals'][4] != raw['commands'][4])
    np.testing.assert_array_equal(raw['commands'][6:12], np.broadcast_to(raw['commands'][4], (6, 5, 3)))
    np.testing.assert_array_equal(raw['mask'][6:12], raw['mask'][4])
    assert row['controller_counts']['decisions'] == 15
    assert row['deadline_misses'] == 2 and raw['round_bytes'][1] == 0
    assert not raw['command_packets'][1:].any()
    assert np.any(raw['proposals'][8] != raw['commands'][8])


def test_R_retains_original_C_and_E_trajectory(tmp_path):
    row, raw, _ = collect(tmp_path, 'R', seed=813, horizon=8)
    env = previous.factory(813)
    env.env.max_steps = 8
    out = tmp_path / 'old'
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        old = previous.collect_episode(env, 'E', 813, out, counts, horizon=8)
    finally:
        env.close()
    with np.load(old['raw']['path']) as original:
        for key in ('observations', 'positions', 'commands', 'mask', 'reward', 'sinr', 'connections',
                    'served', 'quality', 'fallback', 'selected_index', 'report_packets', 'command_packets',
                    'candidate_scores', 'candidate_states', 'candidate_order'):
            np.testing.assert_array_equal(raw[key], original[key])
    assert row['controller_counts'] == old['controller_counts']
    assert row['J'] == old['J'] and row['mean_served'] == old['mean_served']
    assert verify_episode(row, raw, verify_observations=False)['verified_steps'] == 8


def test_balanced_order_and_incomplete_pair_refusal():
    for position in range(3):
        values = [study.ARM_ORDERS[i % 6][position] for i in range(64)]
        counts = [values.count(arm) for arm in study.ARMS]
        assert max(counts) - min(counts) <= 1
    with pytest.raises(ValueError):
        study.paired_reading([], [814])


def test_resource_ceiling_keeps_incomplete_evidence(tmp_path, monkeypatch):
    calls = [0]

    def ceiling():
        calls[0] += 1
        if calls[0] == 3:
            raise study.ResourceLimit('fixture CPU ceiling')

    def short_env(seed):
        env = study.factory(seed)
        env.env.max_steps = 8
        return env

    monkeypatch.setattr(study, 'check_cpu', ceiling)
    result = study.run_batch(tmp_path / 'incomplete', 'fixture', make_env=short_env, seeds=(815,), horizon=8)
    assert result['status'] == 'INCOMPLETE_RESOURCE_LIMIT'
    assert result['counts']['team_steps'] == 1 and result['counts']['complete_episodes'] == 0
    assert 'paired' not in result and len(result['artifacts']) == 1
    with np.load(result['artifacts'][0]['path']) as raw:
        assert raw['completed_steps'] == 1


def test_entry_admission_precedes_output(tmp_path, monkeypatch):
    from experiments.candidates.uav_radio_activation.b03 import run
    from scripts import hmasd_admission

    def refuse(*args, **kwargs):
        raise RuntimeError('fixture admission refused')

    monkeypatch.setattr(hmasd_admission, 'require_admission', refuse)
    out = tmp_path / 'absent'
    with pytest.raises(RuntimeError, match='fixture admission refused'):
        run.main(['--out', str(out), '--launch-sha', 'fixture', '--seed', '29307000'])
    assert not out.exists()


def test_repeated_misses_remain_readable_and_age_without_expired_hold(tmp_path):
    row, raw, _ = collect(tmp_path, 'S2', seed=816, horizon=16,
                          scheduler_type=FirstThenLate)
    assert raw['timely'].tolist() == [True, False, False, False]
    np.testing.assert_array_equal(raw['commands'][2:], np.broadcast_to(raw['commitments'][0], (14, 5, 3)))
    reading = verify_episode(row, raw)
    assert reading['report_age_ticks']['count'] == 14
    assert reading['report_age_ticks']['mean'] == 8.5
    assert reading['report_age_ticks']['max_abs'] == 15
    assert row['deadline_misses'] == 3


@pytest.mark.parametrize('recover', [False, True])
def test_first_miss_keeps_startup_source_age_in_complete_denominator(tmp_path, recover):
    class InitialMiss(Scheduler):
        def decide(self, *args, **kwargs):
            if args[3] == 0 or not recover:
                kwargs['started'] -= 10
            return super().decide(*args, **kwargs)

    row, raw, _ = collect(tmp_path, 'S2', seed=817, scheduler_type=InitialMiss)
    reading = verify_episode(row, raw)
    assert not raw['timely'][0]
    assert reading['report_age_ticks']['count'] == 10
    if recover:
        assert raw['timely'].tolist() == [False, True, True]
        assert reading['startup_hold_ticks_after_delivery'] == 4
        assert reading['report_age_ticks']['mean'] == 3.3
    else:
        assert reading['startup_hold_ticks_after_delivery'] == 10
        assert reading['report_age_ticks']['mean'] == 6.5
        assert reading['report_age_ticks']['max_abs'] == 11
        np.testing.assert_array_equal(raw['commands'], np.broadcast_to(raw['proposals'][0], (12, 5, 3)))


def test_fixed_full_panel_work_counts_and_terminal_layout():
    from experiments.candidates.uav_radio_activation.b03 import protocol
    rounds = len(protocol.REPORT_TICKS)
    assert rounds == 64 and protocol.REPORT_TICKS[-1] == 252
    assert study.SEED == 29307000 and study.WORLDS == 64
    assert study.ARMS == ('R', 'S2', 'T2')
    assert 64 * (64 * 31 + 64 * (116 + 837)) == 4030464
    assert 64 * (31 * 255 + (116 + 837) * 254) == 15997888
    assert 64 * (255 + 2 * 27 * 254) == 894144
    assert 64 * 2 * rounds * 2 == 16384
    assert 63 * (2 + 3 + 4 + 5) + 2 + 3 == 887
