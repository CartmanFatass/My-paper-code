"""Frozen B04 native/C checks with explicit paid-query counters on failure."""

import numpy as np

from experiments.candidates.uav_service_age.b01 import read as legacy
from . import protocol as p


def c_act(controller, observation, tick, paid):
    paid['reader_current_c_calls_attempted'] += 1
    before = dict(controller.counters)
    try:
        result = controller.act(observation, tick)
        paid['reader_current_c_calls'] += 1
        return result
    finally:
        for name, value in controller.counters.items():
            paid['reader_c_' + name] += value - before.get(name, 0)


def verify_native(row, raw, paid):
    """Same native/C semantics as the frozen reader, no environment instance."""
    steps = int(raw['completed_steps'])
    assert steps == row['steps'] == len(raw['commands'])
    assert raw['round_count'] == steps // 4
    np.testing.assert_array_equal(raw['round_tick'], np.arange(0, steps, 4))
    expected_c = np.arange(steps) % 4 == 0
    for name in ('c_called', 'c_decision'):
        np.testing.assert_array_equal(raw[name], expected_c)
    assert raw['map_packet'].tobytes() == legacy.encode_map(raw['true_sites'])
    rng = np.random.RandomState(row['seed'])
    initial = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)] for _ in range(p.N)])
    sites = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(p.U)])
    np.testing.assert_array_equal(initial, raw['positions'][0])
    np.testing.assert_array_equal(sites, raw['true_sites'])
    legacy.assert_close(raw['positions'][1:], np.clip(raw['positions'][:-1] + 30 * raw['commands'],
                                                   legacy.p.LOW, legacy.p.HIGH), 0)
    controllers = [legacy.LocalController(history=False) for _ in range(p.N)]
    current_mask, actual, proposals, pairs = 31, None, None, None
    max_j = max_sinr = max_obs = 0.
    for tick in range(steps):
        assert raw['mask'][tick] == current_mask, 'early or incorrect mask delivery'
        paid['native_observation_attempts'] += 1
        observation = legacy.observed_rows(raw['positions'][tick], sites, current_mask, tick)
        paid['native_observations_completed'] += 1
        observation[:, -1] = tick / steps
        legacy.assert_close(raw['observations'][tick], observation, 1e-6)
        max_obs = max(max_obs, float(np.abs(raw['observations'][tick] - observation).max()))
        if expected_c[tick]:
            pairs = [c_act(controller, raw['observations'][tick, member], tick, paid)
                     for member, controller in enumerate(controllers)]
            proposals = np.array([pair[0] for pair in pairs])
        np.testing.assert_array_equal(raw['proposals'][tick], proposals)
        for name in ('fallback', 'selected_index'):
            np.testing.assert_array_equal(raw[name][tick], [pair[1][name] for pair in pairs])
        observation = raw['observations'][tick]
        np.testing.assert_array_equal(raw['n_current'][tick],
            (observation[:, 3:63].reshape(p.N, 20, 3)[:, :, 2] > 0).sum(axis=1))
        np.testing.assert_array_equal(raw['n_visible_peers'][tick],
            (observation[:, 63:103].reshape(p.N, 10, 4)[:, :, 3] > 0).sum(axis=1))
        if tick == 0:
            actual = proposals.copy()
        np.testing.assert_array_equal(raw['commands'][tick], actual)
        paid['native_physics_attempts'] += 1
        sinr, connected, metrics = legacy.radio(raw['positions'][tick + 1], sites, current_mask)
        paid['native_physics_completed'] += 1
        legacy.assert_close(raw['sinr'][tick], sinr)
        np.testing.assert_array_equal(raw['connections'][tick], connected)
        legacy.assert_close([raw['reward'][tick], raw['served'][tick], raw['quality'][tick]],
                            [metrics['J'], metrics['served'], metrics['quality']], 1e-12)
        max_j = max(max_j, abs(float(raw['reward'][tick]) - metrics['J']))
        finite = np.isfinite(sinr)
        max_sinr = max(max_sinr, float(np.abs(raw['sinr'][tick][finite] - sinr[finite]).max()))
        if tick + 1 >= 2 and (tick - 1) % 4 == 0:
            index = (tick - 1) // 4
            current_mask, actual = int(raw['applied_mask'][index]), raw['commitments'][index]
    paid['native_observation_attempts'] += 1
    terminal = legacy.observed_rows(raw['positions'][-1], sites, current_mask, steps)
    paid['native_observations_completed'] += 1
    terminal[:, -1] = 1.
    legacy.assert_close(raw['observations'][-1], terminal, 1e-6)
    for key, value in row['controller_counts'].items():
        assert sum(controller.counters[key] for controller in controllers) == value
    np.testing.assert_array_equal(raw['controller_counts'],
        [row['controller_counts'][str(key)] for key in raw['controller_counter_keys']])
    return dict(verified_steps=steps, max_native_J_error=max_j, max_native_sinr_error=max_sinr,
                max_observation_error=max_obs)


def verify_post_c_nav(raw, paid):
    controllers = [legacy.LocalController(history=False) for _ in range(p.N)]
    for index, tick in enumerate(raw['round_tick']):
        for member, controller in enumerate(controllers):
            command, _ = c_act(controller, raw['observations'][tick, member], int(tick), paid)
            np.testing.assert_array_equal(command, raw['proposals'][tick, member])
            assert controller._nav_index == int(raw['post_c_nav'][index, member])
