"""Bounded native fixtures and independent endpoint/reader checks, no result panel."""

import numpy as np
import pytest

from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from experiments.candidates.uav_service_age.b01.metrics import add_age_raw
from experiments.candidates.uav_user_waiting.b01.metrics import waiting_metrics, paired_reading, METRICS


def test_worst_user_is_max_of_complete_means_not_mean_of_tick_maxima():
    contacts = np.ones((4, 50), bool)
    contacts[:, :2] = [[True, False], [False, True], [True, False], [False, True]]
    raw = {'connections': contacts[:, None, :]}
    add_contact_raw(raw, 4)
    add_age_raw(raw, 4)
    result = waiting_metrics(raw, 4)
    assert result['F_user'] == .5
    assert result['worst_users'] == [0, 1]
    assert raw['actual_ages'].max(axis=1).mean() == 1.
    assert result['per_user_gaps']['left_censored']['counts'][1] == 1
    assert result['per_user_gaps']['right_censored']['counts'][0] == 1
    assert result['per_user_gaps']['closed']['counts'][:2] == [1, 1]


def test_paired_world_integrity_and_primary_sign():
    rows = [dict(arm=arm, seed=seed, **{key: value for key in METRICS})
            for arm, value in [('R', 1.), ('O', 2.), ('W', 3.), ('M', 4.)]
            for seed in [7, 8]]
    result = paired_reading(rows, [7, 8])
    assert result['contrasts']['R-O']['F_user']['mean'] == -1.
    assert result['contrasts']['R-O']['F_user']['values'] == [-1., -1.]
    with pytest.raises(ValueError, match='complete'):
        paired_reading(rows[:-1], [7, 8])
    with pytest.raises(ValueError, match='complete'):
        paired_reading(rows + [rows[0]], [7, 8])


@pytest.mark.parametrize('arm', ['R', 'O', 'W', 'M'])
def test_native_eight_tick_fixture_and_reader(tmp_path, arm):
    from experiments.candidates.uav_user_waiting.b01.study import collect_episode, factory, save_episode
    from experiments.candidates.uav_user_waiting.b01.read import verify_episode
    from experiments.candidates.uav_registered_service.b01.read import load_episode
    out = tmp_path / arm
    (out / 'raw').mkdir(parents=True)
    env = factory(712301)
    env.env.max_steps = 8
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        row, raw = collect_episode(env, arm, 712301, out, counts, horizon=8)
    finally:
        env.close()
    save_episode(out, row, raw)
    raw = load_episode(row['raw']['path'])
    result = verify_episode(row, raw)
    assert result['verified_steps'] == 8
    assert counts == dict(explicit_resets=1, native_step_calls=8, team_steps=8, complete_episodes=1)
    np.testing.assert_array_equal(raw['forecast_lengths'], [4, 2])
    np.testing.assert_array_equal(raw['candidate_requests'], [232, 232] if arm == 'M' else [116, 116])
    assert row['F_user'] == raw['actual_ages'].sum(axis=0).max() / 8
    if arm == 'R':
        assert len(result['rankings']) == 2
        corrupted = dict(raw)
        corrupted['terminal_burden'] = raw['terminal_burden'].copy()
        corrupted['terminal_burden'][0] += 1
        with pytest.raises(AssertionError):
            verify_episode(row, corrupted)


def test_late_first_anchor_retains_unknown_burden_through_reader(tmp_path):
    from experiments.candidates.uav_user_waiting.b01.scheduler import Scheduler
    from experiments.candidates.uav_user_waiting.b01.study import collect_episode, factory
    from experiments.candidates.uav_user_waiting.b01.read import verify_episode

    class FirstMiss(Scheduler):
        def decide(self, own_observation, actual_commands, proposals, tick, current_mask,
                   *, started=None, cpu_started=None):
            if tick == 0:
                started = self.clock() - 2.
            return super().decide(own_observation, actual_commands, proposals, tick, current_mask,
                                  started=started, cpu_started=cpu_started)

    (tmp_path / 'raw').mkdir()
    env = factory(712302)
    env.env.max_steps = 8
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        row, raw = collect_episode(env, 'R', 712302, tmp_path, counts,
                                   horizon=8, scheduler_type=FirstMiss)
    finally:
        env.close()
    result = verify_episode(row, raw)
    assert result['verified_model_transitions'] == 4
    np.testing.assert_array_equal(raw['model_valid'], [False] * 4 + [True] * 4)
    np.testing.assert_array_equal(raw['burden_burden_unknown'], [False, True])
    assert bool(raw['terminal_burden_unknown'])
    assert row['deadline_misses'] == 1
