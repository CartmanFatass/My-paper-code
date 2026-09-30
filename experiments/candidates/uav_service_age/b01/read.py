#!/usr/bin/env python3
"""Complete saved-data reading. No native episode, suffix rollout or new fit."""

import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time

for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.read import assert_close, observed_rows, radio
from experiments.candidates.uav_radio_activation.b01.protocol import ALL_ON, N, U, encode_map
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_registered_service.b01.read import load_episode, verify_periodic
from experiments.candidates.uav_registered_service.b02.read import verify_episode as verify_retained, compare_metrics
from experiments.candidates.uav_service_age.b01.features import FEATURE_DIM, FEATURE_SPEC
from experiments.candidates.uav_service_age.b01.learner import Learner, innovations, parameter_digest
from experiments.candidates.uav_service_age.b01.metrics import paired_reading
from experiments.candidates.uav_service_age.b01.study import (ARMS, ARM_ORDERS, NEW_ARMS, TRAIN_SEED, TRAIN_EPISODES, EVAL_SEED,
                    WORLDS, HORIZON, episode_metrics, source_identities, file_identity, write_json,
                    frozen_config)


def verify_age(row, raw):
    """Scalar age recurrence, independent of the collector's maximum-accumulate code."""
    contacts = raw['connections'].any(axis=1)
    ages = np.zeros_like(contacts, dtype=np.int16)
    current = np.zeros(U, dtype=np.int16)
    for tick, served in enumerate(contacts):
        for user in range(U):
            current[user] = 0 if served[user] else current[user] + 1
        ages[tick] = current
    np.testing.assert_array_equal(raw['actual_ages'], ages)
    assert_close(raw['per_user_mean_age'], ages.mean(axis=0), 0)
    assert row['age_sum'] == int(ages.sum())
    assert_close(row['A'], ages.sum() / (U * len(ages)), 0)
    rewards = np.array([-float(ages[t:t + 4].sum()) / (U * len(ages)) for t in range(0, len(ages), 4)])
    assert_close(raw['report_rewards'], rewards, 0)
    assert_close(rewards.sum(), -row['A'], 1e-12)
    # Gap triangular sums include both boundary-censored and never-served runs.
    gap_sum = sum(int(gap[3]) * (int(gap[3]) + 1) // 2 for gap in raw['unserved_gap_rows'])
    assert gap_sum == row['age_sum']


def verify_native(row, raw, *, verify_observations=True):
    steps = int(raw['completed_steps'])
    assert steps == row['steps'] == len(raw['commands'])
    assert raw['round_count'] == steps // 4
    np.testing.assert_array_equal(raw['round_tick'], np.arange(0, steps, 4))
    expected_c = np.arange(steps) % 4 == 0
    np.testing.assert_array_equal(raw['c_called'], expected_c)
    np.testing.assert_array_equal(raw['c_decision'], expected_c)
    assert raw['map_packet'].tobytes() == encode_map(raw['true_sites'])
    rng = np.random.RandomState(row['seed'])
    initial = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)] for _ in range(N)])
    sites = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(U)])
    np.testing.assert_array_equal(initial, raw['positions'][0])
    np.testing.assert_array_equal(sites, raw['true_sites'])
    assert_close(raw['positions'][1:], np.clip(raw['positions'][:-1] + 30 * raw['commands'], p.LOW, p.HIGH), 0)
    controllers = [LocalController(history=False) for _ in range(N)]
    current_mask, actual, proposals, pairs = ALL_ON, None, None, None
    max_j = max_sinr = max_obs = 0.
    for tick in range(steps):
        assert raw['mask'][tick] == current_mask, 'early or incorrect mask delivery'
        if verify_observations:
            observation = observed_rows(raw['positions'][tick], sites, current_mask, tick)
            observation[:, -1] = tick / steps
            assert_close(raw['observations'][tick], observation, 1e-6)
            max_obs = max(max_obs, float(np.abs(raw['observations'][tick] - observation).max()))
        if expected_c[tick]:
            pairs = [controller.act(raw['observations'][tick, member], tick) for member, controller in enumerate(controllers)]
            proposals = np.array([pair[0] for pair in pairs])
        np.testing.assert_array_equal(raw['proposals'][tick], proposals)
        for name in ('fallback', 'selected_index'):
            np.testing.assert_array_equal(raw[name][tick], [pair[1][name] for pair in pairs])
        observation = raw['observations'][tick]
        np.testing.assert_array_equal(raw['n_current'][tick], (observation[:, 3:63].reshape(N,20,3)[:,:,2] > 0).sum(axis=1))
        np.testing.assert_array_equal(raw['n_visible_peers'][tick], (observation[:,63:103].reshape(N,10,4)[:,:,3] > 0).sum(axis=1))
        if tick == 0:
            actual = proposals.copy()
        np.testing.assert_array_equal(raw['commands'][tick], actual)
        sinr, connected, metrics = radio(raw['positions'][tick + 1], sites, current_mask)
        assert_close(raw['sinr'][tick], sinr)
        np.testing.assert_array_equal(raw['connections'][tick], connected)
        assert_close([raw['reward'][tick], raw['served'][tick], raw['quality'][tick]],
                     [metrics['J'], metrics['served'], metrics['quality']], 1e-12)
        max_j = max(max_j, abs(float(raw['reward'][tick]) - metrics['J']))
        finite = np.isfinite(sinr)
        max_sinr = max(max_sinr, float(np.abs(raw['sinr'][tick][finite] - sinr[finite]).max()))
        if tick + 1 >= 2 and (tick - 1) % 4 == 0:
            index = (tick - 1) // 4
            current_mask, actual = int(raw['applied_mask'][index]), raw['commitments'][index]
    if verify_observations:
        terminal = observed_rows(raw['positions'][-1], sites, current_mask, steps)
        terminal[:, -1] = 1.
        assert_close(raw['observations'][-1], terminal, 1e-6)
    for key, value in row['controller_counts'].items():
        assert sum(controller.counters[key] for controller in controllers) == value
    np.testing.assert_array_equal(raw['controller_counts'], [row['controller_counts'][str(key)] for key in raw['controller_counter_keys']])
    return dict(verified_steps=steps, max_native_J_error=max_j, max_native_sinr_error=max_sinr,
                max_observation_error=max_obs)


def two_order_selection(keys, size, current_mask, proposal_q):
    requests = []
    def choose(pairs):
        pairs = list(pairs)
        requests.extend(pairs)
        values = [tuple(keys[pair][:size]) for pair in pairs]
        assert np.isfinite(values).all(), 'selection consumed unavailable key'
        return pairs[max(range(len(pairs)), key=lambda i: values[i])]
    q, _ = choose((q, current_mask) for q in range(27))
    first = choose((q, mask) for mask in range(1, 32))
    _, mask = choose((proposal_q, mask) for mask in range(1, 32))
    second = choose((q, mask) for q in range(27))
    return max((first, second), key=lambda pair: tuple(keys[pair][:size])), requests


def check_features(raw, index, sites, last, model_tick, start):
    """Rebuild each declared feature slice from independently checked causal values."""
    tick, horizon = int(raw['round_tick'][index]), len(raw['commands'])
    get = lambda name: raw['age_' + name][index]
    expected = np.zeros(FEATURE_DIM, dtype=np.float32)
    slices = {field['name']: slice(field['start'], field['stop']) for field in FEATURE_SPEC['fields']}
    def put(name, value):
        expected[slices[name]] = np.asarray(value, dtype=np.float32).reshape(-1)
    def bits(mask):
        return [(int(mask) >> i) & 1 for i in range(N)]
    put('map', sites / 1000.)
    put('actual_commands', raw['commands'][tick])
    put('actual_mask', bits(raw['mask'][tick]))
    if raw['decoded_anchor'][index]:
        decoded, _, proposals = p.decode_reports(tuple(packet.tobytes() for packet in raw['report_packets'][index]), tick)
        put('positions', (decoded - p.LOW) / (p.HIGH - p.LOW))
        put('proposals', proposals)
    available = start is not None
    if available:
        put('model_ages', (model_tick - last) / 256.)
        put('model_unknown', (last == -1) & (start > 0))
    if raw['prefix_valid'][index]:
        put('prefix_ages', (tick + 1 - raw['prefix_last'][index]) / 256.)
        put('prefix_unknown', (raw['prefix_last'][index] == -1) & (start > 0))
    put('clock', [tick / 256., (horizon - tick) / 256., min(4, horizon - tick - 2) / 4.,
                  model_tick / 256. if available else 0., (tick - raw['history_after'][index]) / 256.])
    mover = np.zeros(N)
    mover[index % N] = 1
    put('mover', mover)
    put('availability', [raw['decoded_anchor'][index], raw['decoded_anchor'][index], available, raw['prefix_valid'][index]])
    for plan, label in enumerate(('O', 'W')):
        if not get('plan_available')[plan]:
            continue
        put(label + '_commands', get('plan_commands')[plan])
        put(label + '_mask', bits(get('plan_masks')[plan]))
        put(label + '_endpoint_ages', get('plan_endpoint_ages')[plan] / 256.)
        put(label + '_endpoint_unknown', get('plan_endpoint_unknown')[plan])
        native = get('plan_scores')[plan]
        put(label + '_summary', [native[0], native[1] / 50., native[2], get('plan_costs')[plan] / 51200.])
        put(label + '_available', 1)
    np.testing.assert_array_equal(get('features'), expected)
    np.testing.assert_array_equal(get('model_last'), last)
    assert get('model_tick') == model_tick
    np.testing.assert_array_equal(get('actual_commands'), raw['commands'][tick])
    assert get('actual_mask') == raw['mask'][tick]
    np.testing.assert_array_equal(get('feature_availability'),
                                  [raw['decoded_anchor'][index], available, raw['prefix_valid'][index], *get('plan_available')])
    assert bool(get('feature_available'))


def verify_new_history(row, raw, selector=None):
    arm, steps = row['arm'], row['steps']
    sites = p.decode_map(raw['map_packet'].tobytes())
    anchors, last, windows = {}, np.full(U, -1, dtype=int), np.zeros((4, U), bool)
    predicted, valid = np.zeros((steps, U), bool), np.zeros(steps, bool)
    cursor, position, start = 0, None, None
    physics_pairs = sampled_slots = aliases = disagreements = 0
    gaps = []
    def settle(stop):
        nonlocal cursor, position
        while cursor < stop:
            origin = anchors.get(cursor, position)
            assert origin is not None, 'history used missing lawful anchor'
            position = np.clip(origin + 30 * raw['commands'][cursor], p.LOW, p.HIGH)
            _, connected, _ = radio(position, sites, int(raw['mask'][cursor]))
            served = connected.any(axis=0)
            predicted[cursor], valid[cursor] = served, True
            last[served] = cursor
            windows[cursor // 64] |= served
            cursor += 1
        if stop in anchors:
            position = anchors[stop].copy()
    expected_uniforms = innovations(row['seed'], training=bool(raw['training_episode']))[:steps // 4]
    np.testing.assert_array_equal(raw['choice_innovations'], expected_uniforms)
    for index, tick in enumerate(range(0, steps, 4)):
        get = lambda name: raw['age_' + name][index]
        length, member = min(4, steps - tick - 2), index % N
        proposal_q = p.command_index(raw['proposals'][tick, member])
        current_mask = int(raw['mask'][tick])
        assert raw['history_before'][index] == cursor
        report_sent = bool(raw['report_packets'][index].any())
        decoded = actual_wire = proposals = None
        if report_sent:
            packets = tuple(packet.tobytes() for packet in raw['report_packets'][index])
            assert packets == p.encode_reports(raw['observations'][tick, :, :3], raw['commands'][tick], raw['proposals'][tick], tick)
            decoded, actual_wire, proposals = p.decode_reports(packets, tick)
        if raw['decoded_anchor'][index]:
            assert report_sent
            np.testing.assert_array_equal(get('decoded_positions'), decoded)
            np.testing.assert_array_equal(get('decoded_proposals'), proposals)
            anchors[tick] = decoded.copy()
            if start is None:
                start, cursor, position = tick, tick, decoded.copy()
        after = int(raw['history_after'][index])
        assert cursor <= after <= tick
        assert raw['history_reductions'][index] == after - cursor
        settle(after)
        assert raw['history_start'][index] == (-1 if start is None else start)
        np.testing.assert_array_equal(raw['window_valid'][index], np.arange(4) * 64 >= (256 if start is None else start))
        np.testing.assert_array_equal(raw['unknown_age'][index], (last == -1) & (start is not None and start > 0))
        if raw['snapshot_valid'][index]:
            assert after == tick and raw['decoded_anchor'][index]
            np.testing.assert_array_equal(raw['snapshot_last'][index], last)
            np.testing.assert_array_equal(raw['snapshot_windows'][index], windows)
        prefix_last, prefix_windows = last.copy(), windows.copy()
        prefix_position = None if decoded is None else decoded.copy()
        prefix_ticks = int(raw['prefix_ticks'][index])
        assert 0 <= prefix_ticks <= 2
        if prefix_ticks:
            assert raw['snapshot_valid'][index]
            for offset in range(prefix_ticks):
                prefix_position = np.clip(prefix_position + actual_wire * 30, p.LOW, p.HIGH)
                _, connected, _ = radio(prefix_position, sites, current_mask)
                served = connected.any(axis=0)
                np.testing.assert_array_equal(get('prefix_contacts')[offset], served)
                prefix_last[served] = tick + offset
                prefix_windows[(tick + offset) // 64] |= served
        assert not get('prefix_contacts')[prefix_ticks:].any()
        plan_count = int(raw['candidate_plans'][index])
        order = [tuple(map(int, pair)) for pair in raw['candidate_order'][index, :plan_count]]
        scores = raw['candidate_scores'][index]
        assert len(set(order)) == plan_count == np.isfinite(scores[:, :, 0]).sum()
        assert raw['candidate_requests'][index] == raw['candidate_cache_hits'][index] + raw['candidate_uncached_requests'][index]
        assert raw['interrupted_candidate_requests'][index] == raw['candidate_uncached_requests'][index] - plan_count
        request_count = int(get('request_count'))
        assert request_count == raw['candidate_requests'][index]
        request_pairs = [tuple(map(int, pair)) for pair in get('request_pairs')[:request_count]]
        request_orders = get('request_orderings')[:request_count]
        assert np.all(get('request_pairs')[request_count:] == -1)
        assert np.all(get('request_orderings')[request_count:] == -1)
        assert all(0 <= q < 27 and 1 <= mask <= 31 for q, mask in request_pairs)
        assert np.isin(request_orders, (0, 1)).all()
        np.testing.assert_array_equal(get('ordering_requests'), [(request_orders == plan).sum() for plan in range(2)])
        assert order == list(dict.fromkeys(pair for pair in request_pairs if np.isfinite(scores[pair][0])))
        assert raw['forecast_lengths'][index] == length
        assert np.isnan(raw['forecast'][index, :, length:]).all()
        available = get('plan_available').astype(bool)
        assert not available.any() or raw['prefix_valid'][index]
        if arm == 'W':
            assert not available[0] and get('ordering_requests')[0] == 0
        if raw['prefix_valid'][index]:
            assert raw['snapshot_valid'][index] and prefix_ticks == 2
            np.testing.assert_array_equal(raw['prefix_last'][index], prefix_last)
            np.testing.assert_array_equal(raw['prefix_windows'][index], prefix_windows)
            np.testing.assert_array_equal(get('prefix_unknown'), (prefix_last == -1) & (start > 0))
            forecasts = []
            for q in range(27):
                commands = proposals.copy()
                commands[member] = COMMANDS[q]
                point, trajectory = prefix_position.copy(), []
                for _ in range(length):
                    point = np.clip(point + 30 * commands, p.LOW, p.HIGH)
                    trajectory.append(point.copy())
                forecasts.append(trajectory)
            forecasts = np.array(forecasts)
            # A timeout after prefix construction may precede the forecast assignment.
            if np.isfinite(raw['forecast'][index, :, :length]).any():
                assert_close(raw['forecast'][index, :, :length], forecasts, 0)
            else:
                assert not order and not available.any()
            group_ages = sorted(set(prefix_last.tolist()))
            o_size = int(get('o_key_length'))
            assert o_size == (0 if arm == 'W' else len(group_ages) + 6)
            for q, mask in order:
                contacts = raw['candidate_contacts'][index, q, mask, :length]
                assert not raw['candidate_contacts'][index, q, mask, length:].any()
                private_last, cost = prefix_last.copy(), 0
                for offset, served in enumerate(contacts):
                    at = tick + 2 + offset
                    private_last[served] = at
                    cost += int((at - private_last).sum())
                np.testing.assert_array_equal(get('candidate_endpoint_last')[q, mask], private_last)
                assert get('candidate_age_costs')[q, mask] == cost
                assert_close(scores[q, mask, 1], contacts.sum(axis=1).mean(), 1e-12)
                assert_close(scores[q, mask, 0], .7 * scores[q, mask, 1] / 50 + .3 * scores[q, mask, 2], 1e-12)
                native = (scores[q, mask, 0], scores[q, mask, 1], int(q == proposal_q), mask.bit_count(), -mask, -q)
                assert_close(get('w_ordering_keys')[q, mask], (-cost,) + native, 0)
                if arm != 'W':
                    contact_any = contacts.any(axis=0)
                    counts = tuple(int(contact_any[prefix_last == age].sum()) for age in group_ages)
                    assert_close(get('o_ordering_keys')[q, mask, :o_size], counts + native, 0)
                    assert np.isnan(get('o_ordering_keys')[q, mask, o_size:]).all()
            if arm == 'W':
                assert np.isnan(get('o_ordering_keys')).all()
            subset = set(order) if tick in (0, 60, 124, 252) else set()
            for plan in range(2):
                if not available[plan]:
                    continue
                matrix, size = (get('o_ordering_keys'), o_size) if plan == 0 else (get('w_ordering_keys'), 7)
                selected, requests = two_order_selection(matrix, size, current_mask, proposal_q)
                assert tuple(get('plan_pairs')[plan]) == selected
                assert get('ordering_requests')[plan] == 116
                assert [pair for pair, source in zip(request_pairs, request_orders) if source == plan] == requests
                q, mask = selected
                subset.add(selected)
                commands = proposals.copy()
                commands[member] = COMMANDS[q]
                np.testing.assert_array_equal(get('plan_commands')[plan], commands)
                assert get('plan_masks')[plan] == mask
                assert_close(get('plan_scores')[plan], scores[selected], 0)
                assert get('plan_costs')[plan] == get('candidate_age_costs')[selected]
                np.testing.assert_array_equal(get('plan_endpoint_last')[plan], get('candidate_endpoint_last')[selected])
                endpoint_last = get('candidate_endpoint_last')[selected]
                assert_close(get('plan_endpoint_ages')[plan], tick + 1 + length - endpoint_last, 0)
                np.testing.assert_array_equal(get('plan_endpoint_unknown')[plan], (endpoint_last == -1) & (start > 0))
                assert_close(get('plan_w_keys')[plan], get('w_ordering_keys')[selected], 0)
                if arm != 'W':
                    assert_close(get('plan_o_keys')[plan, :o_size], get('o_ordering_keys')[selected][:o_size], 0)
            for q, mask in sorted(subset):
                values = []
                for slot, point in enumerate(forecasts[q]):
                    _, connected, metrics = radio(point, sites, mask)
                    np.testing.assert_array_equal(raw['candidate_contacts'][index, q, mask, slot], connected.any(axis=0))
                    values.append((metrics['J'], metrics['served'], metrics['quality']))
                assert_close(scores[q, mask], np.mean(values, axis=0), 1e-12)
                physics_pairs += 1
        else:
            assert not order and not available.any()
        alias = bool(available.all() and get('plan_masks')[0] == get('plan_masks')[1]
                     and np.array_equal(get('plan_commands')[0], get('plan_commands')[1]))
        assert bool(get('alias')) == alias
        aliases += int(alias)
        m_choice = max(range(2), key=lambda plan: tuple(get('plan_w_keys')[plan])) if available.all() else -1
        assert get('m_choice') == m_choice
        sampled = bool(get('sampled'))
        sampled_slots += int(sampled)
        assert bool(get('effective_actor_row')) == sampled and float(get('actor_weight')) == float(sampled)
        if sampled:
            assert arm in ('L', 'L0', 'L1') and available.all() and not alias
            probabilities = get('probabilities')
            assert np.isfinite(probabilities).all() and np.all(probabilities >= 0)
            assert_close(probabilities.sum(), 1., 1e-12)
            choice = int(expected_uniforms[index] >= probabilities[0])
            assert get('sampled_choice') == get('requested_choice') == choice
            assert_close(get('logp'), np.log(probabilities[choice]), 1e-12)
            if selector is not None:
                expected = np.asarray(selector(get('features')), dtype=np.float64)
                expected /= expected.sum()
                expected[1] = 1 - expected[0]
                assert_close(probabilities, expected, 1e-7)
            disagreements += int(choice != m_choice)
            gaps.append(float(get('plan_costs')[choice] - get('plan_costs')[m_choice]))
        else:
            assert get('sampled_choice') == -1 and get('logp') == 0
            assert not get('probabilities').any()
        assert bool(get('sampled_late')) == (sampled and not raw['timely'][index])
        assert bool(get('forced_before_sampling')) == (arm in ('L', 'L0', 'L1') and not sampled)
        if get('requested_available'):
            choice = int(get('requested_choice'))
            assert available[choice]
            if not sampled:
                assert choice == (1 if arm == 'W' else m_choice)
            np.testing.assert_array_equal(get('requested_commands'), get('plan_commands')[choice])
            assert get('requested_mask') == get('plan_masks')[choice]
        if raw['timely'][index]:
            assert get('requested_available') and get('actual_choice') == get('requested_choice')
            choice = int(get('actual_choice'))
            np.testing.assert_array_equal(raw['commitments'][index], get('plan_commands')[choice])
            q, mask = map(int, get('plan_pairs')[choice])
            assert (raw['selected_q'][index], raw['selected_mask'][index]) == (q, mask)
            assert p.decode_command(raw['command_packets'][index].tobytes(), tick) == (mask, member, q)
            assert raw['applied_mask'][index] == mask and raw['round_bytes'][index] == 136
            assert raw['scheduler_wall'][index] <= p.DEADLINE_SECONDS
            assert raw['candidate_requests'][index] == (116 if arm == 'W' else 232)
            assert raw['state_reductions'][index] == length * plan_count
            assert raw['geometry_snapshots'][index] == 27 * length
        else:
            np.testing.assert_array_equal(raw['commitments'][index], raw['commands'][tick])
            assert raw['applied_mask'][index] == current_mask
            assert raw['selected_q'][index] == raw['selected_mask'][index] == -1
            assert get('actual_choice') == -1 and not raw['command_packets'][index].any()
            assert raw['round_bytes'][index] == (120 if report_sent else 0)
        assert raw['scheduler_wall'][index] + 1e-12 >= raw['c_wall'][tick]
        assert raw['scheduler_cpu'][index] + 1e-12 >= raw['c_cpu'][tick]
        for unit in ('wall', 'cpu'):
            phase_times = [raw[name + '_' + unit][index] for name in ('history', 'prefix', 'candidate')]
            phase_times += [get('feature_' + unit), get('actor_' + unit)]
            assert all(np.isfinite(value) and value >= 0 for value in phase_times)
            assert sum(phase_times) <= raw['scheduler_' + unit][index] + 1e-9
        assert bool(raw['actual_timeout'][index]) == (raw['scheduler_wall'][index] > p.DEADLINE_SECONDS)
        check_features(raw, index, sites, last, cursor - 1, start)
    before = cursor
    if start is not None:
        settle(steps)
    assert raw['terminal_history_reductions'] == cursor - before
    assert raw['terminal_history_start'] == (-1 if start is None else start)
    assert bool(raw['terminal_history_complete']) == (start is not None and cursor == steps)
    np.testing.assert_array_equal(raw['model_valid'], valid)
    np.testing.assert_array_equal(raw['model_contacts'], predicted)
    np.testing.assert_array_equal(raw['terminal_last'], last)
    np.testing.assert_array_equal(raw['terminal_windows'], windows)
    return dict(verified_model_transitions=int(valid.sum()), candidate_physics_pairs=physics_pairs,
                sampled_slots=sampled_slots, alias_slots=aliases, sampled_M_disagreements=disagreements,
                requested_predicted_cost_minus_M=gaps,
                candidate_physics_scope='all available O/W plan pairs; all evaluated pairs at reports0/60/124/252; all completed candidate costs/keys/endpoints',
                kernel_scope='shared native radio; independent causal history/age/key/feature arithmetic')


def verify_episode(row, raw, *, selector=None, verify_observations=True):
    assert int(raw['world_seed']) == row['seed'] and str(raw['program']) == row['arm']
    if row['arm'] in NEW_ARMS:
        result = verify_native(row, raw, verify_observations=verify_observations)
        result.update(verify_new_history(row, raw, selector))
        verify_periodic(row, raw)
    else:
        result = verify_retained(row, raw, verify_observations=verify_observations)
    verify_age(row, raw)
    for key, value in episode_metrics(raw, row['steps'], row['arm']).items():
        compare_metrics(value, row[key])
    result.update(arm=row['arm'], seed=row['seed'])
    return result


def verified_artifact(identity):
    path = Path(identity['path'])
    assert file_identity(path) == identity, f'artifact identity mismatch: {path}'
    return path


def read_result(out):
    started, cpu_started = time.perf_counter(), time.process_time()
    out = Path(out)
    summary = json.loads((out / 'summary.json').read_text())
    if summary['status'] != 'COMPLETE' or not summary['scientific_invocation']:
        raise ValueError('complete fixed scientific invocation required')
    config = summary['config']
    assert config == frozen_config(summary['launch_sha']), 'fixed source/config drift'
    assert json.loads((out / 'config.json').read_text()) == config
    assert json.loads((out / 'process-exit.json').read_text())['exit_code'] == 0
    expected_training = [('L', seed) for seed in range(TRAIN_SEED, TRAIN_SEED + TRAIN_EPISODES)]
    expected_eval = [(arm, seed) for i, seed in enumerate(range(EVAL_SEED, EVAL_SEED + WORLDS))
                     for arm in ARM_ORDERS[i % len(ARM_ORDERS)]]
    assert [(row['arm'], row['seed']) for row in summary['training']] == expected_training
    assert [(row['arm'], row['seed']) for row in summary['rows']] == expected_eval
    assert summary['counts']['constructors'] == 1
    for key, expected in dict(explicit_resets=960, native_step_calls=245760, team_steps=245760,
                              complete_episodes=960, fit_started=1, fit_completed=1,
                              training_episodes=512, evaluation_episodes=448).items():
        assert summary['counts'][key] == expected
    assert summary['fixed_policy_evaluation_counts'] == dict(episodes=448, transitions=114688,
                                                            optimizer_updates=0, parameter_updates=0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    learner, initial = Learner(FEATURE_DIM), Learner(FEATURE_DIM)
    checkpoint0 = torch.load(verified_artifact(summary['initial_checkpoint']), map_location='cpu', weights_only=True)
    assert parameter_digest(learner.actor) == checkpoint0['actor_sha256']
    assert parameter_digest(learner.critic) == checkpoint0['critic_sha256']
    for name, expected in learner.state().items():
        if isinstance(expected, dict):
            for key in expected:
                torch.testing.assert_close(checkpoint0[name][key], expected[key], atol=0, rtol=0)
        else:
            assert checkpoint0[name] == expected
    verified, worlds = [], {}
    bytes_read = 0
    update_cpu = 0.
    for episode, row in enumerate(summary['training']):
        path = verified_artifact(row['raw'])
        bytes_read += row['raw']['bytes']
        raw = load_episode(path)
        assert row['steps'] == HORIZON and raw['training_episode'] and raw['episode_index'] == episode
        assert str(raw['actor_before_sha256']) == parameter_digest(learner.actor)
        assert str(raw['critic_before_sha256']) == parameter_digest(learner.critic)
        result = verify_episode(row, raw, selector=learner.probabilities)
        update_start = time.process_time()
        update, arrays = learner.update(raw['age_features'], raw['age_sampled_choice'], raw['age_logp'],
                                        raw['age_sampled'], raw['report_rewards'])
        update_cpu += time.process_time() - update_start
        compare_metrics(update, row['update'])
        for key, value in arrays.items():
            assert_close(raw['learning_' + key], value, 1e-7)
        verified.append(result)
        del raw
        print(json.dumps(dict(verified=len(verified), stage='training', seed=row['seed'])), flush=True)
    final = torch.load(verified_artifact(summary['final_checkpoint']), map_location='cpu', weights_only=True)
    assert parameter_digest(learner.actor) == final['actor_sha256'] == summary['learner']['actor_sha256']
    assert parameter_digest(learner.critic) == final['critic_sha256'] == summary['learner']['critic_sha256']
    for name, expected in learner.state().items():
        if isinstance(expected, dict):
            assert final[name].keys() == expected.keys()
            for key in expected:
                torch.testing.assert_close(final[name][key], expected[key], atol=0, rtol=0)
        else:
            assert final[name] == expected
    assert learner.actor_updates == summary['counts']['actor_updates']
    assert learner.critic_updates == summary['counts']['critic_updates'] == 2048
    for row in summary['rows']:
        path = verified_artifact(row['raw'])
        bytes_read += row['raw']['bytes']
        raw = load_episode(path)
        assert row['steps'] == HORIZON and not raw['training_episode']
        world = (raw['true_sites'], raw['positions'][0])
        if row['seed'] in worlds:
            for actual, expected in zip(world, worlds[row['seed']]):
                np.testing.assert_array_equal(actual, expected)
        else:
            worlds[row['seed']] = tuple(value.copy() for value in world)
        selector = initial.probabilities if row['arm'] == 'L0' else learner.probabilities if row['arm'] == 'L1' else None
        verified.append(verify_episode(row, raw, selector=selector))
        del raw
        print(json.dumps(dict(verified=len(verified), stage='evaluation', arm=row['arm'], seed=row['seed'])), flush=True)
    expected_artifacts = [row['raw'] for row in summary['training'] + summary['rows']]
    expected_artifacts += [summary['initial_checkpoint'], summary['final_checkpoint']]
    assert sorted(summary['artifacts'], key=lambda x:x['path']) == sorted(expected_artifacts, key=lambda x:x['path'])
    paired = paired_reading(summary['rows'], config['evaluation_seeds'], ARMS)
    assert paired == summary['paired']
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = dict(status='VERIFIED_COMPLETE', launch_sha=summary['launch_sha'],
                  summary_sha256=file_identity(out / 'summary.json')['sha256'],
                  verified_raw_files=len(verified), verified_raw_bytes=bytes_read,
                  verified_native_steps=sum(row['verified_steps'] for row in verified),
                  fit_count=1, replayed_actor_updates=learner.actor_updates,
                  replayed_critic_updates=learner.critic_updates,
                  optimizer_replay_cpu_seconds=update_cpu, rows=verified, paired=paired,
                  scope='all960 actual/native/C/age/periodic trajectories; all causal history/feature/selection and512 saved PPO updates; candidate physical subset; no environment steps or new fit',
                  wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started,
                  process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
                  peak_rss_kib=usage.ru_maxrss, rss_scope='reader process lifetime peak; Linux KiB')
    write_json(out / 'reading.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    result = read_result(args.out)
    print(json.dumps({key:result[key] for key in ('status','verified_raw_files','verified_native_steps','wall_seconds','cpu_seconds')}), flush=True)


if __name__ == '__main__':
    main()
