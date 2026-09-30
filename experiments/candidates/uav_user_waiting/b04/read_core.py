"""Independent causal reconstruction of ordinary searches and local service floors."""

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b01.read import assert_close, radio
from experiments.candidates.uav_registered_service.b01.read import verify_periodic, compare_metrics
from experiments.candidates.uav_service_age.b01 import read as age_reader
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.read import (
    advance, check_history, verify_stage, verify_post_c_nav,
)
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from .metrics import episode_metrics


def verify_search_paths(stage, checked, arm):
    """Reconstruct exact complete paths and prefixes of interrupted paths."""
    labels = ('O', 'W', 'S') if arm in ('U', 'K') else (('O', 'W') if arm == 'M' else ('S',))
    searches = stage['searches']
    assert list(searches) == list(labels[:len(searches)])
    requests = [tuple(map(int, pair)) for pair in stage['request_pairs']]
    cursor = 0
    proposal_q = p.command_index(stage['proposals'][stage['member']])

    class InterruptedPath(Exception):
        pass

    for label, search in searches.items():
        assert search['request_start'] == cursor
        stop = int(search['request_end'])
        assert cursor <= stop <= len(requests)
        keys = checked['keys'].get(label, {})

        def choose(pairs):
            nonlocal cursor
            candidates = []
            for pair in pairs:
                if cursor == stop:
                    raise InterruptedPath
                assert requests[cursor] == pair
                assert stage['request_orderings'][cursor] == label
                completed = int(stage['request_candidate_index'][cursor]) >= 0
                cursor += 1
                if not completed:
                    assert cursor == stop == len(requests)
                    raise InterruptedPath
                candidates.append(pair)
            return max(candidates, key=lambda pair: keys[pair])

        try:
            q, _ = choose((q, int(stage['current_mask'])) for q in range(27))
            first = choose((q, mask) for mask in range(1, 32))
            np.testing.assert_array_equal(search['motion_pair'], first)
            _, mask = choose((proposal_q, mask) for mask in range(1, 32))
            second = choose((q, mask) for q in range(27))
            np.testing.assert_array_equal(search['mask_pair'], second)
            winner = max((first, second), key=lambda pair: keys[pair])
            np.testing.assert_array_equal(search['selected_pair'], winner)
            assert search['completed'] and cursor == stop
        except InterruptedPath:
            assert not search['completed'] and cursor == stop == len(requests)
            assert label == list(searches)[-1]
    assert cursor == len(requests)
    if stage['completed']:
        assert list(searches) == list(labels)
        assert all(search['completed'] for search in searches.values())
        assert len(requests) == 116 * len(labels)


def verify_program(record, checked):
    """Saved contacts supply integer totals; independently reconstructed keys select."""
    current, arm = record['current'], record['arm']
    assert not record['branches'] and not record['continuation_used']
    assert not record['c_diagnostics_valid'] and record['selected_branch'] == -1
    assert all(record['counts'][name] == 0 for name in (
        'virtual_c_decisions', 'synthetic_observations', 'synthetic_reports',
        'observation_user_links', 'observation_peer_links', 'continuation_prefix_ticks'))
    assert 'union' in record if arm in ('U', 'K') else 'union' not in record
    if current:
        verify_search_paths(current, checked, arm)
    requested = None
    if arm in ('M', 'S'):
        if current and current['completed']:
            if arm == 'M':
                finalists = [tuple(map(int, current['searches'][label]['selected_pair'])) for label in ('O', 'W')]
                requested = max(finalists, key=lambda pair: checked['keys']['W'][pair])
            else:
                requested = tuple(map(int, current['searches']['S']['selected_pair']))
                np.testing.assert_array_equal(record['s_pair'], requested)
        if np.all(record['requested_pair'] >= 0):
            assert requested == tuple(record['requested_pair'])
        if record['timely']:
            assert requested is not None
        return None
    union = record['union']
    pairs = [tuple(map(int, pair)) for pair in union['pool_pairs']]
    expected_pairs = list(checked['evaluated']) if current else []
    assert pairs == expected_pairs
    totals = current['contacts'].sum(axis=(1, 2), dtype=np.int64) if current else np.empty(0, np.int64)
    np.testing.assert_array_equal(union['service_totals'], totals)
    assert isinstance(union['service_floor_total'], (int, np.integer))
    assert np.asarray(union['service_totals']).dtype.kind in 'iu'
    floor = int(union['service_floor_total'])
    have_m = bool(np.all(union['m_pair'] >= 0))
    if have_m:
        assert current and all(current['searches'][label]['completed'] for label in ('O', 'W'))
        finalists = [tuple(map(int, current['searches'][label]['selected_pair'])) for label in ('O', 'W')]
        m_pair = max(finalists, key=lambda pair: checked['keys']['W'][pair])
        np.testing.assert_array_equal(union['m_pair'], m_pair)
        assert floor == int(totals[pairs.index(m_pair)])
    else:
        assert floor == -1 and not union['completed']
        np.testing.assert_array_equal(union['m_pair'], [-1, -1])
        assert not current or 'S' not in current['searches']
    feasible = totals >= floor if have_m else np.zeros(len(pairs), bool)
    np.testing.assert_array_equal(union['feasible'], feasible)
    if np.all(union['s_pair'] >= 0):
        assert current['searches']['S']['completed'] and have_m
        np.testing.assert_array_equal(union['s_pair'], current['searches']['S']['selected_pair'])
        np.testing.assert_array_equal(record['s_pair'], union['s_pair'])
    else:
        np.testing.assert_array_equal(union['s_pair'], [-1, -1])
    have_rank = bool(np.all(union['u_pair'] >= 0))
    if have_rank:
        assert current['completed'] and have_m
        u_pair = max(pairs, key=lambda pair: checked['keys']['S'][pair])
        k_pair = max((pair for pair, good in zip(pairs, feasible) if good),
                     key=lambda pair: checked['keys']['S'][pair])
        np.testing.assert_array_equal(union['u_pair'], u_pair)
        np.testing.assert_array_equal(union['k_pair'], k_pair)
        assert bool(feasible[pairs.index(m_pair)])
        assert int(totals[pairs.index(k_pair)]) >= floor
    else:
        assert not union['completed']
        np.testing.assert_array_equal(union['u_pair'], [-1, -1])
        np.testing.assert_array_equal(union['k_pair'], [-1, -1])
    if union['completed']:
        assert current['completed'] and have_rank
        requested = u_pair if arm == 'U' else k_pair
        np.testing.assert_array_equal(record['requested_pair'], requested)
    else:
        np.testing.assert_array_equal(record['requested_pair'], [-1, -1])
        assert not record['timely']
    if record['timely']:
        assert union['completed']
    if not union['completed']:
        return None
    indices = {name: pairs.index(tuple(map(int, union[name + '_pair']))) for name in ('m', 's', 'u', 'k')}
    chosen = indices['u' if arm == 'U' else 'k']
    return dict(tick=int(record['tick']), timely=bool(record['timely']), pool_size=len(pairs),
        floor_total=floor, feasible_candidates=int(feasible.sum()),
        pairs={name: list(pairs[index]) for name, index in indices.items()},
        service_totals={name: int(totals[index]) for name, index in indices.items()},
        q2={name: int(current['q2_cost'][index]) for name, index in indices.items()},
        filter_changes=indices['k'] != indices['u'], U_differs_S=indices['u'] != indices['s'],
        K_differs_M=indices['k'] != indices['m'],
        selected_service_margin=int(totals[chosen]) - floor,
        selected_forecast_differs_M=bool(pairs[chosen][1] != pairs[indices['m']][1] or
            not np.array_equal(current['forecast'][pairs[chosen][0]],
                               current['forecast'][pairs[indices['m']][0]])))


def verify_decisions(row, raw, records):
    steps, arm = row['steps'], row['arm']
    sites = p.decode_map(raw['map_packet'].tobytes())
    anchors, last, windows = {}, np.full(50, -1, dtype=np.int64), np.zeros((4, 50), bool)
    burden = np.zeros(50, dtype=np.int64)
    predicted, valid = np.zeros((steps, 50), bool), np.zeros(steps, bool)
    cursor, position, start, physics_pairs = 0, None, None, 0
    physics_transitions, prefix_transitions = 0, 0
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
                                   extra_physics=[record['requested_pair']] + [record['union'][name + '_pair']
                                       for name in ('m', 's', 'u', 'k') if 'union' in record])
            physics_pairs += checked['candidate_physics_pairs']
            partial_length = len(current['partial'].get('contacts', []))
            physics_transitions += ((checked['candidate_physics_pairs'] - int(bool(current['partial']))) *
                                    current['length'] + partial_length)
            prefix_transitions += int(current['prefix_count'])
        diagnostic = verify_program(record, checked)
        if diagnostic is not None:
            if record['timely']:
                length = current['length']
                chosen = 'u' if arm == 'U' else 'k'
                actual_total = int(raw['connections'][tick + 2:tick + 2 + length].sum())
                diagnostic['actual_delivered_service_total'] = actual_total
                diagnostic['actual_minus_modeled_service_total'] = actual_total - diagnostic['service_totals'][chosen]
            diagnostics.append(diagnostic)
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
                union_slots=diagnostics, candidate_physics_transitions=physics_transitions,
                prefix_physics_transitions=prefix_transitions, settled_burden_errors=history_errors,
                terminal_model_minus_actual_burden=(burden - raw['actual_ages'].sum(axis=0, dtype=np.int64)).tolist() if start == 0 else None,
                physics_scope='all selected M/S/U/K programs and search winners; all evaluated candidates at0/60/124/248; all contact-to-cost/key/path/pool/floor arithmetic',
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
