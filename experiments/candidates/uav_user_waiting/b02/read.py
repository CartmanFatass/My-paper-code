#!/usr/bin/env python3
"""Independent saved-data reconstruction; no native environment steps or fits."""

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

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.read import assert_close, observed_rows, radio
from experiments.candidates.uav_registered_service.b01.read import load_episode, verify_periodic, compare_metrics
from experiments.candidates.uav_service_age.b01 import read as age_reader
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_user_waiting.b02.metrics import episode_metrics, paired_reading
from experiments.candidates.uav_user_waiting.b02.study import (
    ARMS, ARM_ORDERS, SEED, WORLDS, frozen_config, file_identity, write_json,
)


def advance(last, windows, burden, tick, contacts):
    """Reader recurrence does not call scheduler/history update methods."""
    last[contacts] = tick
    windows[tick // 64] |= contacts
    ages = np.empty(50, dtype=np.int64)
    for user in range(50):
        ages[user] = tick - int(last[user])
        burden[user] += ages[user]
    return int(ages.sum()), int(np.dot(ages, ages))


def check_history(record, start, last, windows, burden):
    assert record['start_tick'] == start
    np.testing.assert_array_equal(record['last'], last)
    np.testing.assert_array_equal(record['windows'], windows)
    np.testing.assert_array_equal(record['burden'], burden)
    assert record['burden_unknown'] == (start > 0)


def native_key(pair, score, proposal_q):
    q, mask = pair
    return (float(score[0]), float(score[1]), int(q == proposal_q),
            mask.bit_count(), -mask, -q)


def two_orders(keys, current_mask, proposal_q):
    requests = []

    def choose(pairs):
        pairs = list(pairs)
        requests.extend(pairs)
        return max(pairs, key=lambda pair: keys[pair])

    q, _ = choose((q, current_mask) for q in range(27))
    first = choose((q, mask) for mask in range(1, 32))
    _, mask = choose((proposal_q, mask) for mask in range(1, 32))
    second = choose((q, mask) for q in range(27))
    return max((first, second), key=lambda pair: keys[pair]), first, second, requests


def verify_post_c_nav(raw):
    controllers = [LocalController(history=False) for _ in range(5)]
    for index, tick in enumerate(raw['round_tick']):
        for member, controller in enumerate(controllers):
            command, _ = controller.act(raw['observations'][tick, member], int(tick))
            np.testing.assert_array_equal(command, raw['proposals'][tick, member])
            assert controller._nav_index == int(raw['post_c_nav'][index, member])


def verify_stage(stage, sites, *, full_physics=False, extra_physics=()):
    """Rebuild every stored candidate cost/key and the declared physical subset."""
    tick, length, member = int(stage['tick']), int(stage['length']), int(stage['member'])
    assert member == (tick // 4) % 5 and length > 0
    positions, actual, proposals = stage['positions'], stage['actual'], stage['proposals']
    current_mask = int(stage['current_mask'])
    hist = stage['input_history']
    start = int(hist['start_tick'])
    last, windows, burden = (hist[key].copy() for key in ('last', 'windows', 'burden'))
    point = positions.copy()
    prefix_count = int(stage['prefix_count'])
    assert 0 <= prefix_count <= 2
    for offset in range(prefix_count):
        point = np.clip(point + actual * 30., p.LOW, p.HIGH)
        _, connections, _ = radio(point, sites, current_mask)
        contacts = connections.any(axis=0)
        np.testing.assert_array_equal(stage['prefix_positions'][offset], point)
        np.testing.assert_array_equal(stage['prefix_contacts'][offset], contacts)
        advance(last, windows, burden, tick + offset, contacts)
    evaluated = [tuple(map(int, pair)) for pair in stage['evaluated_pairs']]
    assert len(evaluated) == len(set(evaluated))
    assert not evaluated or stage['prefix_valid']
    check_history(stage['prefix_history'], start, last, windows, burden)
    if stage['prefix_valid']:
        assert prefix_count == 2
    else:
        assert not evaluated and not stage['partial']
        return dict(candidate_physics_pairs=0, keys={}, evaluated={})
    forecasts = []
    for q in range(27):
        commands = proposals.copy()
        commands[member] = COMMANDS[q]
        trajectory, position = [], point.copy()
        for _ in range(length):
            position = np.clip(position + 30. * commands, p.LOW, p.HIGH)
            trajectory.append(position.copy())
        forecasts.append(trajectory)
    forecasts = np.asarray(forecasts)
    if np.isfinite(stage['forecast']).any():
        np.testing.assert_array_equal(stage['forecast'], forecasts)
    else:
        assert not evaluated
    proposal_q = p.command_index(proposals[member])
    keys = {label: {} for label in ('O', 'W', 'S', 'R')}
    candidate_index = {pair: i for i, pair in enumerate(evaluated)}
    for i, pair in enumerate(evaluated):
        contacts = stage['contacts'][i]
        assert contacts.shape == (length, 50)
        private_last, private_windows, private_burden = last.copy(), windows.copy(), burden.copy()
        age_sums, square_sums = [], []
        for offset, served in enumerate(contacts):
            a, q2 = advance(private_last, private_windows, private_burden, tick + 2 + offset, served)
            age_sums.append(a)
            square_sums.append(q2)
        np.testing.assert_array_equal(stage['endpoint_last'][i], private_last)
        np.testing.assert_array_equal(stage['endpoint_burden'][i], private_burden)
        np.testing.assert_array_equal(stage['age_sum'][i], age_sums)
        np.testing.assert_array_equal(stage['age_square_sum'][i], square_sums)
        assert stage['age_cost'][i] == sum(age_sums)
        assert stage['q2_cost'][i] == sum(square_sums)
        score = stage['native'][i]
        assert_close(score[1], contacts.sum(axis=1).mean(), 1e-12)
        assert_close(score[0], .7 * score[1] / 50 + .3 * score[2], 1e-12)
        tail = native_key(pair, score, proposal_q)
        distinct = contacts.any(axis=0)
        keys['O'][pair] = tuple(int(distinct[last == value].sum()) for value in np.unique(last)) + tail
        keys['W'][pair] = (-sum(age_sums),) + tail
        keys['S'][pair] = (-sum(square_sums),) + tail
        keys['R'][pair] = (-int(private_burden.max()), -int(private_burden.sum())) + tail
        for label in keys:
            assert_close(stage['keys'][label][i], keys[label][pair], 0)
    requested = [tuple(map(int, pair)) for pair in stage['request_pairs']]
    indices = stage['request_candidate_index']
    assert len(requested) == len(indices) == len(stage['request_orderings'])
    assert all(0 <= q < 27 and 1 <= mask < 32 for q, mask in requested)
    for pair, index in zip(requested, indices):
        if index >= 0:
            assert evaluated[index] == pair
        else:
            assert pair not in candidate_index
    assert evaluated == list(dict.fromkeys(pair for pair in requested if pair in candidate_index))
    for label, search in stage['searches'].items():
        if not search['completed']:
            continue
        selected, first, second, expected = two_orders(keys[label], current_mask, proposal_q)
        assert tuple(search['motion_pair']) == first
        assert tuple(search['mask_pair']) == second
        assert tuple(search['selected_pair']) == selected
        begin, end = int(search['request_start']), int(search['request_end'])
        assert requested[begin:end] == expected and end - begin == 116
        assert all(value == label for value in stage['request_orderings'][begin:end])
    subset = set(evaluated) if full_physics else set()
    subset.update(tuple(map(int, pair)) for pair in extra_physics if tuple(map(int, pair)) in candidate_index)
    for search in stage['searches'].values():
        if search['completed']:
            subset.add(tuple(map(int, search['selected_pair'])))
    for q, mask in subset:
        i, values = candidate_index[q, mask], []
        for offset, point in enumerate(forecasts[q]):
            _, connections, metrics = radio(point, sites, mask)
            np.testing.assert_array_equal(stage['contacts'][i, offset], connections.any(axis=0))
            values.append((metrics['J'], metrics['served'], metrics['quality']))
        assert_close(stage['native'][i], np.mean(values, axis=0), 1e-12)
    partial = stage['partial']
    if partial:
        q, mask = map(int, partial['pair'])
        assert (q, mask) not in candidate_index
        pl, pw, pb = last.copy(), windows.copy(), burden.copy()
        assert len(partial['contacts']) <= length
        for offset, served in enumerate(partial['contacts']):
            _, connections, metrics = radio(forecasts[q, offset], sites, mask)
            np.testing.assert_array_equal(served, connections.any(axis=0))
            age, square = advance(pl, pw, pb, tick + 2 + offset, served)
            assert partial['age_sum'][offset] == age and partial['age_square_sum'][offset] == square
            assert_close(partial['native'][offset], [metrics['J'], metrics['served'], metrics['quality']], 1e-12)
        check_history(partial['history'], start, pl, pw, pb)
    return dict(candidate_physics_pairs=len(subset) + int(bool(partial)), keys=keys, evaluated=candidate_index,
                prefix_last=last, prefix_windows=windows, prefix_burden=burden, forecasts=forecasts)


def verify_branch(branch, current, checked, sites, nav, horizon, *, full_physics):
    pair = tuple(map(int, branch['first_pair']))
    index = checked['evaluated'][pair]
    tick = current['tick']
    assert branch['model_tick'] == tick + 4
    assert current['length'] == 4
    assert branch['current_q2'] == current['q2_cost'][index]
    np.testing.assert_array_equal(branch['model_positions'], current['forecast'][pair[0], 1])
    last, windows, burden = (checked['prefix_' + key].copy() for key in ('last', 'windows', 'burden'))
    for offset in range(2):
        advance(last, windows, burden, tick + 2 + offset, current['contacts'][index, offset])
    check_history(branch['input_history'], current['input_history']['start_tick'], last, windows, burden)
    first_commands = current['proposals'].copy()
    first_commands[current['member']] = COMMANDS[pair[0]]
    observation = branch['synthetic_observations']
    if len(observation):
        expected = observed_rows(branch['model_positions'], sites, pair[1], tick + 4)
        expected[:, -1] = (tick + 4) / horizon
        assert_close(observation, expected, 1e-6)
    counters = {}
    assert 0 <= branch['virtual_c_count'] <= 5
    for member in range(branch['virtual_c_count']):
        clone = LocalController(history=False)
        clone._nav_index = int(nav[member])
        command, diagnostics = clone.act(observation[member], tick + 4)
        np.testing.assert_array_equal(command, branch['virtual_proposals'][member])
        assert clone._nav_index == branch['virtual_nav'][member]
        for key, value in diagnostics.items():
            if value is not None:
                compare_metrics(value, branch['virtual_diagnostics'][str(member)][key])
        for key, value in clone.counters.items():
            counters[key] = counters.get(key, 0) + value
    assert counters == branch['virtual_c_counters']
    if len(branch['report_packets']):
        assert branch['virtual_c_count'] == 5
        expected = p.encode_reports(observation[:, :3], first_commands, branch['virtual_proposals'],
                                    tick + 4, branch['virtual_nav'])
        assert expected == tuple(packet.tobytes() for packet in branch['report_packets'])
    if branch['decoded']:
        positions, actual, proposals, next_nav = p.decode_reports(
            tuple(packet.tobytes() for packet in branch['report_packets']), tick + 4)
        np.testing.assert_array_equal(positions, branch['model_positions'])
        np.testing.assert_array_equal(positions, branch['decoded_positions'])
        np.testing.assert_array_equal(actual, first_commands)
        np.testing.assert_array_equal(proposals, branch['decoded_proposals'])
        np.testing.assert_array_equal(next_nav, branch['decoded_nav'])
    stage = branch['continuation']
    if not stage:
        assert not branch['completed']
        return 0
    assert branch['decoded']
    np.testing.assert_array_equal(stage['positions'], branch['decoded_positions'])
    np.testing.assert_array_equal(stage['actual'], first_commands)
    np.testing.assert_array_equal(stage['proposals'], branch['decoded_proposals'])
    np.testing.assert_array_equal(stage['nav'], branch['decoded_nav'])
    assert stage['tick'] == tick + 4 and stage['current_mask'] == pair[1]
    check_history(stage['input_history'], current['input_history']['start_tick'], last, windows, burden)
    next_checked = verify_stage(stage, sites, full_physics=full_physics)
    # The prefix is a re-expression of already scored first-block transitions.
    count = stage['prefix_count']
    np.testing.assert_array_equal(stage['prefix_positions'][:count], current['forecast'][pair[0], 2:2 + count])
    np.testing.assert_array_equal(stage['prefix_contacts'][:count], current['contacts'][index, 2:2 + count])
    if branch['prefix_matches']:
        assert stage['prefix_valid']
        np.testing.assert_array_equal(stage['prefix_history']['last'], current['endpoint_last'][index])
        np.testing.assert_array_equal(stage['prefix_history']['burden'], current['endpoint_burden'][index])
    if branch['completed']:
        assert stage['completed'] and branch['prefix_matches']
        chosen = tuple(map(int, stage['searches']['S']['selected_pair']))
        future_q2 = int(stage['q2_cost'][next_checked['evaluated'][chosen]])
        assert branch['continuation_q2'] == future_q2
        assert branch['q8'] == int(current['q2_cost'][index]) + future_q2
        assert stage['length'] == min(4, horizon - tick - 6)
    return next_checked['candidate_physics_pairs']


def verify_decisions(row, raw, records):
    steps, arm = row['steps'], row['arm']
    sites = p.decode_map(raw['map_packet'].tobytes())
    anchors, last, windows = {}, np.full(50, -1, dtype=np.int64), np.zeros((4, 50), bool)
    burden = np.zeros(50, dtype=np.int64)
    predicted, valid = np.zeros((steps, 50), bool), np.zeros(steps, bool)
    cursor, position, start, physics_pairs = 0, None, None, 0
    diagnostics, history_errors = [], []

    def settle(stop):
        nonlocal cursor, position
        while cursor < stop:
            origin = anchors.get(cursor, position)
            assert origin is not None
            position = np.clip(origin + 30 * raw['commands'][cursor], p.LOW, p.HIGH)
            _, connected, _ = radio(position, sites, int(raw['mask'][cursor]))
            served = connected.any(axis=0)
            predicted[cursor], valid[cursor] = served, True
            advance(last, windows, burden, cursor, served)
            cursor += 1
        if stop in anchors:
            position = anchors[stop].copy()

    assert len(records) == steps // 4
    for index, record in enumerate(records):
        tick = index * 4
        assert record['arm'] == arm and record['tick'] == tick and record['horizon'] == steps
        assert record['history_before'] == cursor
        sent = len(record['report_packets']) > 0
        if sent:
            packets = tuple(packet.tobytes() for packet in record['report_packets'])
            assert packets == p.encode_reports(raw['observations'][tick, :, :3], raw['commands'][tick],
                                                raw['proposals'][tick], tick, raw['post_c_nav'][index])
            np.testing.assert_array_equal(record['report_packets'], raw['report_packets'][index])
        else:
            assert not raw['report_packets'][index].any()
        if record['decoded_anchor']:
            assert sent
            decoded, committed, proposed, nav = p.decode_reports(packets, tick)
            for name, value in (('positions', decoded), ('actual', committed), ('proposals', proposed), ('nav', nav)):
                np.testing.assert_array_equal(record['decoded_' + name], value)
            anchors[tick] = decoded.copy()
            if start is None:
                start, cursor, position = tick, tick, decoded.copy()
        after = int(record['history_after'])
        assert cursor <= after <= tick
        assert record['counts']['history_reductions'] == after - cursor
        settle(after)
        assert record['history_start'] == (-1 if start is None else start)
        for name, value in (('last', last), ('windows', windows), ('burden', burden)):
            np.testing.assert_array_equal(record['history_' + name], value)
        assert record['burden_unknown'] == (start is not None and start > 0)
        if record['snapshot_valid']:
            assert after == tick and record['decoded_anchor']
            if start == 0:
                error = burden - raw['actual_ages'][:tick].sum(axis=0, dtype=np.int64)
                history_errors.append(dict(tick=tick, differing_users=int(np.count_nonzero(error)),
                                           max_absolute_error=int(np.abs(error).max())))
        current = record['current']
        checked = None
        if current:
            assert record['snapshot_valid']
            check_history(current['input_history'], start, last, windows, burden)
            for key in ('positions', 'actual', 'proposals', 'nav'):
                np.testing.assert_array_equal(current[key], record['decoded_' + key])
            assert current['tick'] == tick and current['length'] == min(4, steps - tick - 2)
            assert current['current_mask'] == raw['mask'][tick]
            checked = verify_stage(current, sites, full_physics=tick in (0, 60, 124, 248),
                                   extra_physics=record['first_finalists'])
            physics_pairs += checked['candidate_physics_pairs']
            for branch in record['branches'].values():
                physics_pairs += verify_branch(branch, current, checked, sites, record['decoded_nav'], steps,
                                                full_physics=tick in (0, 60, 124, 248))
        else:
            assert not record['branches']
        if current and current['completed']:
            assert checked is not None
            if arm == 'M':
                finalists = [tuple(map(int, current['searches'][label]['selected_pair'])) for label in ('O', 'W')]
                requested = max(finalists, key=lambda pair: checked['keys']['W'][pair])
            else:
                label = 'R' if arm == 'R' else 'S'
                requested = tuple(map(int, current['searches'][label]['selected_pair']))
                if arm in ('A', 'S'):
                    np.testing.assert_array_equal(record['s_pair'], requested)
                    search = current['searches']['S']
                    finalists = list(dict.fromkeys(tuple(map(int, search[key])) for key in ('motion_pair', 'mask_pair')))
                    np.testing.assert_array_equal(record['first_finalists'], finalists)
            if record['continuation_used']:
                assert arm == 'A' and len(record['first_finalists']) == 2 and tick + 4 < steps
                if len(record['branches']) == 2 and all(branch['completed'] for branch in record['branches'].values()):
                    branches = list(record['branches'].values())
                    winner = max(range(2), key=lambda i: (-int(branches[i]['q8']),) + checked['keys']['S'][tuple(branches[i]['first_pair'])])
                    if record['selected_branch'] >= 0:
                        assert record['selected_branch'] == winner
                        requested = tuple(map(int, branches[winner]['first_pair']))
                if record['c_diagnostics_valid']:
                    assert tuple(record['c0_pair']) == tuple(record['s_pair'])
                    assert tuple(record['c1_pair']) == requested
                    for label in ('c0', 'c1'):
                        branch = next(branch for branch in record['branches'].values()
                                      if np.array_equal(branch['first_pair'], record[label + '_pair']))
                        for key in ('current_q2', 'continuation_q2', 'q8'):
                            assert record[label + '_' + key] == branch[key]
            else:
                assert not record['branches']
                if arm == 'A':
                    assert len(record['first_finalists']) == 1 or tick + 4 == steps
            if np.all(record['requested_pair'] >= 0):
                assert tuple(record['requested_pair']) == requested
        if record['timely']:
            assert raw['timely'][index] and record['fallback_reason'] == ''
            q, mask = map(int, record['requested_pair'])
            assert q == raw['selected_q'][index] and mask == raw['selected_mask'][index]
            commands = record['decoded_proposals'].copy()
            commands[(tick // 4) % 5] = COMMANDS[q]
            assert p.decode_command(record['delivered_command_packet'].tobytes(), tick) == (mask, (tick // 4) % 5, q)
            assert record['wall_seconds'] <= p.DEADLINE_SECONDS
        else:
            assert not raw['timely'][index] and record['fallback_reason']
            commands, mask = raw['commands'][tick], int(raw['mask'][tick])
            assert raw['selected_q'][index] == raw['selected_mask'][index] == -1
            assert len(record['delivered_command_packet']) == 0
        np.testing.assert_array_equal(record['returned_commands'], commands)
        np.testing.assert_array_equal(raw['commitments'][index], commands)
        assert record['returned_mask'] == raw['applied_mask'][index] == mask
        length = raw['command_packet_lengths'][index]
        np.testing.assert_array_equal(raw['command_packets'][index, :length], record['delivered_command_packet'])
        assert not raw['command_packets'][index, length:].any()
        assert raw['round_bytes'][index] == (125 if sent else 0) + len(record['delivered_command_packet'])
        assert raw['scheduler_wall'][index] == record['wall_seconds']
        assert raw['scheduler_cpu'][index] == record['cpu_seconds']
        assert record['wall_seconds'] + 1e-12 >= raw['c_wall'][tick]
        assert record['cpu_seconds'] + 1e-12 >= raw['c_cpu'][tick]
        assert record['actual_timeout'] == (record['wall_seconds'] > p.DEADLINE_SECONDS)
        for unit in ('wall', 'cpu'):
            values = list(record['phase_' + unit].values())
            assert all(np.isfinite(value) and value >= 0 for value in values)
            assert sum(values) <= record[unit + '_seconds'] + 1e-9
        stages = ([current] if current else []) + [branch['continuation'] for branch in record['branches'].values() if branch['continuation']]
        counts = record['counts']
        assert counts['candidate_requests'] == sum(len(stage['request_pairs']) for stage in stages)
        assert counts['candidate_plans'] == sum(len(stage['evaluated_pairs']) for stage in stages)
        assert counts['state_reductions'] == sum(len(stage['evaluated_pairs']) * stage['length'] + len(stage['partial'].get('contacts', [])) for stage in stages)
        assert counts['geometry_snapshots'] == sum(int(stage['geometry_count_by_q'].sum()) for stage in stages)
        assert counts['prefix_ticks'] == sum(stage['prefix_count'] for stage in stages)
        assert counts['virtual_c_decisions'] == sum(branch['virtual_c_count'] for branch in record['branches'].values())
        assert counts['candidate_cache_hits'] + counts['candidate_uncached_requests'] == counts['candidate_requests']
        assert counts['interrupted_candidate_requests'] == counts['candidate_uncached_requests'] - counts['candidate_plans']
        for name in ('candidate_requests', 'candidate_plans', 'state_reductions', 'geometry_snapshots', 'prefix_ticks'):
            assert raw[name][index] == counts[name]
        if record['c_diagnostics_valid']:
            item = {key: record[key] for key in ('tick', 'timely', 'c0_current_q2', 'c1_current_q2',
                    'c0_continuation_q2', 'c1_continuation_q2', 'c0_q8', 'c1_q8')}
            item['changed'] = not np.array_equal(record['c0_pair'], record['c1_pair'])
            if record['timely']:
                branch = record['branches']['branch_' + str(record['selected_branch'])]
                future_tick = tick + 4
                item['next_report_position_abs_error_max'] = float(np.abs(branch['model_positions'] - raw['positions'][future_tick]).max())
                item['next_c_command_mismatches'] = int(np.any(branch['virtual_proposals'] != raw['proposals'][future_tick], axis=1).sum())
                item['next_c_nav_mismatches'] = int((branch['virtual_nav'] != raw['post_c_nav'][index + 1]).sum())
                item['next_observation_abs_error_max'] = float(np.abs(branch['synthetic_observations'] - raw['observations'][future_tick]).max())
                next_pair = branch['continuation']['searches']['S']['selected_pair']
                actual_pair = (raw['selected_q'][index + 1], raw['selected_mask'][index + 1])
                item['virtual_S_vs_actual_A_pair_differs'] = not np.array_equal(next_pair, actual_pair)
            diagnostics.append(item)
    before = cursor
    if start is not None:
        settle(steps)
    assert raw['terminal_history_reductions'] == cursor - before
    assert raw['terminal_history_start'] == (-1 if start is None else start)
    assert bool(raw['terminal_history_complete']) == (start is not None and cursor == steps)
    assert bool(raw['terminal_burden_unknown']) == (start is not None and start > 0)
    for key, value in (('model_valid', valid), ('model_contacts', predicted), ('terminal_last', last),
                       ('terminal_windows', windows), ('terminal_burden', burden)):
        np.testing.assert_array_equal(raw[key], value)
    return dict(verified_model_transitions=int(valid.sum()), candidate_physics_pairs=physics_pairs,
                continuation_slots=diagnostics, settled_burden_errors=history_errors,
                terminal_model_minus_actual_burden=(burden - raw['actual_ages'].sum(axis=0, dtype=np.int64)).tolist() if start == 0 else None,
                physics_scope='all current/continuation selected plans and both A finalists; all evaluated candidates at0/60/124/248; all completed cost/key arithmetic',
                kernel_scope='shared native radio; independent history/cost/ranking/trajectory reconstruction; frozen independent observation reader')


def verify_episode(row, raw, *, verify_observations=True):
    assert str(raw['program']) == row['arm'] and int(raw['world_seed']) == row['seed']
    records = unpack_records(raw)
    result = age_reader.verify_native(row, raw, verify_observations=verify_observations)
    verify_post_c_nav(raw)
    verify_periodic(row, raw)
    age_reader.verify_age(row, raw)
    result.update(verify_decisions(row, raw, records))
    users = raw['actual_ages'].sum(axis=0, dtype=np.int64) / row['steps']
    assert_close(row['F_user'], users.max(), 0)
    assert_close(row['per_user_mean_age'], users, 0)
    for key, value in episode_metrics(raw, row['steps'], row['arm'], records).items():
        compare_metrics(value, row[key])
    result.update(arm=row['arm'], seed=row['seed'])
    return result


def summarize_continuation(rows):
    slots = [slot for row in rows for slot in row['continuation_slots']]
    executed = [slot for slot in slots if slot['timely']]
    return dict(complete_two_branch_slots=len(slots), executed_two_branch_slots=len(executed),
                executed_pair_changes=sum(slot['changed'] for slot in executed),
                current_sacrifice=sum(slot['c1_current_q2'] - slot['c0_current_q2'] for slot in executed),
                modeled_continuation_gain=sum(slot['c0_continuation_q2'] - slot['c1_continuation_q2'] for slot in executed),
                modeled_total_gain=sum(slot['c0_q8'] - slot['c1_q8'] for slot in executed),
                next_c_command_mismatches=sum(slot['next_c_command_mismatches'] for slot in executed),
                next_c_nav_mismatches=sum(slot['next_c_nav_mismatches'] for slot in executed),
                max_next_observation_abs_error=max((slot['next_observation_abs_error_max'] for slot in executed), default=0.),
                max_next_report_position_abs_error=max((slot['next_report_position_abs_error_max'] for slot in executed), default=0.),
                virtual_S_vs_actual_A_pair_differences=sum(slot['virtual_S_vs_actual_A_pair_differs'] for slot in executed),
                scope='same-state two computed branches; next C/observation compared only for selected executed first branch; actual replanning as A differs from virtual S by design')


def read_result(out):
    started, cpu_started = time.perf_counter(), time.process_time()
    out = Path(out)
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['status'] == 'COMPLETE' and summary['scientific_invocation']
    config = json.loads((out / 'config.json').read_text())
    assert summary['config'] == config == frozen_config(summary['launch_sha'])
    seeds = list(range(SEED, SEED + WORLDS))
    expected_counts = dict(constructors=1, explicit_resets=256, native_step_calls=65536,
                           team_steps=65536, complete_episodes=256, fit_started=0, optimizer_steps=0)
    assert summary['counts'] == expected_counts
    assert summary['fixed_policy_evaluation_counts'] == dict(episodes=256, transitions=65536,
                                                            optimizer_updates=0, parameter_updates=0)
    assert [(row['arm'], row['seed']) for row in summary['rows']] == [
        (arm, seed) for index, seed in enumerate(seeds) for arm in ARM_ORDERS[index % 8]]
    assert sorted(summary['artifacts'], key=lambda x: x['path']) == sorted(
        [row['raw'] for row in summary['rows']], key=lambda x: x['path'])
    assert json.loads((out / 'process-exit.json').read_text())['exit_code'] == 0
    rows, worlds, total_bytes = [], {}, 0
    for row in summary['rows']:
        path = Path(row['raw']['path'])
        identity = file_identity(path)
        assert identity == row['raw'], f'raw identity mismatch: {path}'
        total_bytes += identity['bytes']
        raw = load_episode(path)
        world = raw['true_sites'], raw['positions'][0]
        if row['seed'] in worlds:
            for left, right in zip(world, worlds[row['seed']]):
                np.testing.assert_array_equal(left, right)
        else:
            worlds[row['seed']] = tuple(x.copy() for x in world)
        rows.append(verify_episode(row, raw))
        del raw
        print(json.dumps(dict(verified=len(rows), arm=row['arm'], seed=row['seed'])), flush=True)
    paired = paired_reading(summary['rows'], seeds, ARMS)
    assert paired == summary['paired']
    result = dict(status='VERIFIED_COMPLETE', launch_sha=summary['launch_sha'],
                  summary_sha256=file_identity(out / 'summary.json')['sha256'],
                  verified_raw_files=len(rows), verified_raw_bytes=total_bytes,
                  rows=rows, paired=paired, continuation_diagnostics=summarize_continuation(rows),
                  scope='all fixed256 native/C/age/periodic/history records; all completed key and continuation arithmetic; declared physical subset; zero native steps/fits',
                  wall_seconds=time.perf_counter() - started,
                  cpu_seconds=time.process_time() - cpu_started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  rss_scope='reader lifetime peak; Linux KiB')
    write_json(out / 'reading.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    return read_result(parser.parse_args(argv).out)


if __name__ == '__main__':
    main()
