"""Independent local-state recurrence and bounded LRS physical/priority checks."""

from collections import Counter

import numpy as np

from envs.pettingzoo.uav_radio import free_space_user_path_loss, user_sinr_from_path_loss
from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b01.read import assert_close
from experiments.candidates.uav_user_waiting.b02 import protocol as wire
from experiments.candidates.uav_user_waiting.b02.read import advance, native_key, two_orders
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_user_waiting.b04.read_core import verify_program


def values_at(position, sites, mask, paid=None):
    if paid is not None:
        paid['modeled_physics_attempts'] += 1
        paid['modeled_sinr_link_entries'] += 250
    losses = free_space_user_path_loss(position, sites)
    values = user_sinr_from_path_loss(losses, transmitter_mask=wire.mask_array(mask))
    if paid is not None:
        paid['modeled_physics_completed'] += 1
    return values


def reference_grants(values, own_last, *, rows=5, paid=None):
    """Independent Python tuple ordering, with no candidate allocator import."""
    assert values.shape == own_last.shape == (5, 50)
    assert np.all(np.isfinite(values) | np.isneginf(values))
    eligible = values >= 3.
    assert np.all(eligible.sum(axis=0) <= 1)
    result = np.full((5, 10), -1, np.int8)
    for member in range(rows):
        if paid is not None:
            paid['reference_lrs_row_attempts'] += 1
        users = [user for user in range(50) if eligible[member, user]]
        chosen = sorted(users, key=lambda user: (int(own_last[member, user]),
                                                 -float(values[member, user]), user))[:10]
        result[member, :len(chosen)] = chosen
        if paid is not None:
            paid['reference_lrs_rows_completed'] += 1
    return result


def consume_grants(own_last, tick, grants, *, rows=5):
    """Validate compact identities and independently advance local timestamps."""
    grants = np.asarray(grants)
    assert grants.shape == (5, 10) and grants.dtype == np.int8
    connections = np.zeros((5, 50), bool)
    for member in range(5):
        ids = [int(value) for value in grants[member] if value >= 0]
        assert all(0 <= user < 50 for user in ids) and len(ids) == len(set(ids))
        assert np.all(grants[member, len(ids):] == -1)
        assert member < rows or not ids
        if member < rows:
            # The oldest timestamp is the first priority, even outside the
            # independently verified SINR subset. Quality ties need physics.
            stamps = [int(own_last[member, user]) for user in ids]
            assert stamps == sorted(stamps)
            own_last[member, ids] = tick
            connections[member, ids] = True
    assert np.all(connections.sum(axis=0) <= 1)
    return connections


def native_terms(values, connections):
    served = int(connections.sum())
    selected = [float(values[member, user]) for member in range(5) for user in range(50)
                if connections[member, user]]
    quality = sum(min(1., max(0., (value - 3.) / 30.)) for value in selected) / max(served, 1)
    return np.asarray([.7 * served / 50 + .3 * quality, served, quality], np.float64)


def check_history(record, start, last, windows, burden, own_last):
    assert record['start_tick'] == start
    for name, value in (('last', last), ('windows', windows), ('burden', burden), ('last_grant', own_last)):
        np.testing.assert_array_equal(record[name], value)
    assert record['burden_unknown'] == (start is not None and start > 0)


def check_partial_row(partial, position, sites, mask, tick, start, last, windows, burden, own_last, paid=None):
    if not partial:
        return 0
    assert int(partial['tick']) == tick and int(partial['mask']) == mask
    np.testing.assert_array_equal(partial['positions'], position)
    check_history(partial['input_history'], start, last, windows, burden, own_last)
    rows = int(partial['completed_rows'])
    assert 0 <= rows <= 5
    expected = reference_grants(values_at(position, sites, mask, paid), own_last, rows=rows, paid=paid)
    np.testing.assert_array_equal(partial['grants'], expected)
    return 1


def verify_stage(stage, sites, *, full_physics=False, extra_physics=(), paid=None):
    tick, length, member = int(stage['tick']), int(stage['length']), int(stage['member'])
    assert member == (tick // 4) % 5 and 0 < length <= 4
    positions, actual, proposals = stage['positions'], stage['actual'], stage['proposals']
    mask = int(stage['current_mask'])
    history = stage['input_history']
    start = int(history['start_tick'])
    last, windows, burden, own = (history[name].copy() for name in ('last', 'windows', 'burden', 'last_grant'))
    point = positions.copy()
    prefix_count = int(stage['prefix_count'])
    assert 0 <= prefix_count <= 2
    assert stage['prefix_grants'].shape == (2, 5, 10)
    for offset in range(prefix_count):
        point = np.clip(point + actual * 30., wire.LOW, wire.HIGH)
        values = values_at(point, sites, mask, paid)
        expected = reference_grants(values, own, paid=paid)
        np.testing.assert_array_equal(stage['prefix_grants'][offset], expected)
        connection = consume_grants(own, tick + offset, stage['prefix_grants'][offset])
        np.testing.assert_array_equal(stage['prefix_positions'][offset], point)
        np.testing.assert_array_equal(stage['prefix_contacts'][offset], connection.any(axis=0))
        advance(last, windows, burden, tick + offset, connection.any(axis=0))
    assert np.all(stage['prefix_grants'][prefix_count:] == -1)
    prefix_partial = stage['prefix_partial']
    prefix_extra = check_partial_row(prefix_partial, np.clip(point + actual * 30., wire.LOW, wire.HIGH),
        sites, mask, tick + prefix_count, start, last, windows, burden, own, paid) if prefix_partial else 0
    check_history(stage['prefix_history'], start, last, windows, burden, own)
    evaluated = [tuple(map(int, pair)) for pair in stage['evaluated_pairs']]
    assert len(evaluated) == len(set(evaluated))
    assert not evaluated or stage['prefix_valid']
    empty = dict(candidate_physics_pairs=0, candidate_physics_transitions=0,
                 prefix_physics_transitions=prefix_count + prefix_extra, keys={}, evaluated={})
    if not stage['prefix_valid']:
        assert not evaluated and not stage['partial']
        return empty
    assert prefix_count == 2 and not prefix_partial
    forecasts = []
    for q in range(27):
        commands, position = proposals.copy(), point.copy()
        commands[member] = COMMANDS[q]
        trajectory = []
        for _ in range(length):
            position = np.clip(position + commands * 30., wire.LOW, wire.HIGH)
            trajectory.append(position.copy())
        forecasts.append(trajectory)
    forecasts = np.asarray(forecasts)
    if np.isfinite(stage['forecast']).any():
        np.testing.assert_array_equal(stage['forecast'], forecasts)
    else:
        assert not evaluated
    proposal_q = wire.command_index(proposals[member])
    keys = {label: {} for label in ('O', 'W', 'S', 'R')}
    candidate_index = {pair: index for index, pair in enumerate(evaluated)}
    assert stage['candidate_grants'].shape == (len(evaluated), length, 5, 10)
    for index, pair in enumerate(evaluated):
        private_last, private_windows, private_burden, private_own = (
            value.copy() for value in (last, windows, burden, own))
        sums, squares = [], []
        for offset, grants in enumerate(stage['candidate_grants'][index]):
            contacts = consume_grants(private_own, tick + 2 + offset, grants).any(axis=0)
            np.testing.assert_array_equal(stage['contacts'][index, offset], contacts)
            age, square = advance(private_last, private_windows, private_burden, tick + 2 + offset, contacts)
            sums.append(age)
            squares.append(square)
        for name, expected in (('endpoint_last', private_last), ('endpoint_burden', private_burden),
                               ('age_sum', sums), ('age_square_sum', squares)):
            np.testing.assert_array_equal(stage[name][index], expected)
        assert stage['age_cost'][index] == sum(sums) and stage['q2_cost'][index] == sum(squares)
        score = stage['native'][index]
        contacts = stage['contacts'][index]
        assert np.isfinite(score).all() and 0 <= score[2] <= 1
        assert_close(score[1], contacts.sum(axis=1).mean(), 1e-12)
        assert_close(score[0], .7 * score[1] / 50 + .3 * score[2], 1e-12)
        tail = native_key(pair, score, proposal_q)
        distinct = contacts.any(axis=0)
        keys['O'][pair] = tuple(int(distinct[last == value].sum()) for value in np.unique(last)) + tail
        keys['W'][pair], keys['S'][pair] = (-sum(sums),) + tail, (-sum(squares),) + tail
        keys['R'][pair] = (-int(private_burden.max()), -int(private_burden.sum())) + tail
        for label in keys:
            assert_close(stage['keys'][label][index], keys[label][pair], 0)
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
        assert label == 'S'
        if not search['completed']:
            continue
        selected, first, second, expected = two_orders(keys[label], mask, proposal_q)
        assert tuple(search['motion_pair']) == first and tuple(search['mask_pair']) == second
        assert tuple(search['selected_pair']) == selected
        begin, end = int(search['request_start']), int(search['request_end'])
        assert requested[begin:end] == expected and end - begin == 116
        assert all(value == label for value in stage['request_orderings'][begin:end])
    subset = set(evaluated) if full_physics else set()
    subset.update(tuple(map(int, pair)) for pair in extra_physics if tuple(map(int, pair)) in candidate_index)
    subset.update(tuple(map(int, search['selected_pair'])) for search in stage['searches'].values() if search['completed'])
    physical_ticks = 0
    for q, candidate_mask in sorted(subset):
        index, private_own, native = candidate_index[q, candidate_mask], own.copy(), []
        for offset, point in enumerate(forecasts[q]):
            values = values_at(point, sites, candidate_mask, paid)
            expected = reference_grants(values, private_own, paid=paid)
            np.testing.assert_array_equal(stage['candidate_grants'][index, offset], expected)
            connections = consume_grants(private_own, tick + 2 + offset, expected)
            native.append(native_terms(values, connections))
            physical_ticks += 1
        assert_close(stage['native'][index], np.mean(native, axis=0), 1e-12)
    partial = stage['partial']
    if partial:
        q, candidate_mask = map(int, partial['pair'])
        assert (q, candidate_mask) not in candidate_index
        pl, pw, pb, po = (value.copy() for value in (last, windows, burden, own))
        n = len(partial['contacts'])
        assert n <= length and len(partial['grants']) == n
        for offset, grants in enumerate(partial['grants']):
            values = values_at(forecasts[q, offset], sites, candidate_mask, paid)
            expected = reference_grants(values, po, paid=paid)
            np.testing.assert_array_equal(grants, expected)
            connections = consume_grants(po, tick + 2 + offset, grants)
            contacts = connections.any(axis=0)
            np.testing.assert_array_equal(partial['contacts'][offset], contacts)
            age, square = advance(pl, pw, pb, tick + 2 + offset, contacts)
            assert partial['age_sum'][offset] == age and partial['age_square_sum'][offset] == square
            assert_close(partial['native'][offset], native_terms(values, connections), 1e-12)
            physical_ticks += 1
        check_history(partial['history'], start, pl, pw, pb, po)
        if partial['row_partial']:
            assert n < length
            physical_ticks += check_partial_row(partial['row_partial'], forecasts[q, n], sites,
                candidate_mask, tick + 2 + n, start, pl, pw, pb, po, paid)
    return dict(candidate_physics_pairs=len(subset) + int(bool(partial)),
                candidate_physics_transitions=physical_ticks, prefix_physics_transitions=prefix_count + prefix_extra,
                keys=keys, evaluated=candidate_index)


def verify_decisions(raw, paid=None):
    records, steps = unpack_records(raw), int(raw['completed_steps'])
    sites = wire.decode_map(raw['map_packet'].tobytes())
    last, windows, burden = np.full(50, -1, np.int64), np.zeros((4, 50), bool), np.zeros(50, np.int64)
    own = np.full((5, 50), -1, np.int64)
    predicted, valid = np.zeros((steps, 50), bool), np.zeros(steps, bool)
    predicted_grants = np.full((steps, 5, 10), -1, np.int8)
    anchors, cursor, position, start = {}, 0, None, None
    work = Counter()

    def settle(stop):
        nonlocal cursor, position
        while cursor < stop:
            origin = anchors.get(cursor, position)
            assert origin is not None
            position = np.clip(origin + raw['commands'][cursor] * 30., wire.LOW, wire.HIGH)
            grants = reference_grants(values_at(position, sites, int(raw['mask'][cursor]), paid), own, paid=paid)
            connections = consume_grants(own, cursor, grants)
            predicted_grants[cursor], predicted[cursor], valid[cursor] = grants, connections.any(axis=0), True
            advance(last, windows, burden, cursor, predicted[cursor])
            cursor += 1
        if stop in anchors:
            position = anchors[stop].copy()

    assert len(records) == steps // 4
    for index, record in enumerate(records):
        tick = index * 4
        assert record['arm'] == 'S' and record['tick'] == tick and record['horizon'] == steps
        assert record['history_before'] == cursor
        sent = len(record['report_packets']) > 0
        if sent:
            packets = tuple(packet.tobytes() for packet in record['report_packets'])
            assert packets == wire.encode_reports(raw['observations'][tick, :, :3], raw['commands'][tick],
                                                  raw['proposals'][tick], tick, raw['post_c_nav'][index])
            np.testing.assert_array_equal(record['report_packets'], raw['report_packets'][index])
        else:
            assert not raw['report_packets'][index].any()
        if record['decoded_anchor']:
            assert sent
            decoded, committed, proposed, nav = wire.decode_reports(packets, tick)
            for name, expected in (('positions', decoded), ('actual', committed), ('proposals', proposed), ('nav', nav)):
                np.testing.assert_array_equal(record['decoded_' + name], expected)
            anchors[tick] = decoded.copy()
            if start is None:
                start, cursor, position = tick, tick, decoded.copy()
        after = int(record['history_after'])
        assert cursor <= after <= tick and record['counts']['history_reductions'] == after - cursor
        settled = after - cursor
        settle(after)
        assert record['history_start'] == (-1 if start is None else start)
        for name, expected in (('last', last), ('windows', windows), ('burden', burden), ('last_grant', own)):
            np.testing.assert_array_equal(record['history_' + name], expected)
        assert record['burden_unknown'] == (start is not None and start > 0)
        # A successful episode can time out between atomic transitions, but
        # must not contain a failed allocator row disguised as completion.
        assert not record['settlement_partial']
        if record['snapshot_valid']:
            assert after == tick and record['decoded_anchor']
        stage, checked = record['current'], None
        if stage:
            assert record['snapshot_valid']
            check_history(stage['input_history'], start, last, windows, burden, own)
            for name in ('positions', 'actual', 'proposals', 'nav'):
                np.testing.assert_array_equal(stage[name], record['decoded_' + name])
            assert stage['tick'] == tick and stage['length'] == min(4, steps - tick - 2)
            assert stage['current_mask'] == raw['mask'][tick]
            checked = verify_stage(stage, sites, full_physics=tick in (0, 60, 124, 248),
                                   extra_physics=[record['requested_pair']], paid=paid)
            for name in ('candidate_physics_pairs', 'candidate_physics_transitions', 'prefix_physics_transitions'):
                work[name] += checked[name]
        verify_program(record, checked)
        if record['timely']:
            assert raw['timely'][index] and record['fallback_reason'] == ''
            q, mask = map(int, record['requested_pair'])
            assert q == raw['selected_q'][index] and mask == raw['selected_mask'][index]
            commands = record['decoded_proposals'].copy()
            commands[(tick // 4) % 5] = COMMANDS[q]
            assert wire.decode_command(record['delivered_command_packet'].tobytes(), tick) == (mask, (tick // 4) % 5, q)
            assert record['wall_seconds'] <= wire.DEADLINE_SECONDS
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
        assert raw['scheduler_wall'][index] == record['wall_seconds'] and raw['scheduler_cpu'][index] == record['cpu_seconds']
        assert record['wall_seconds'] + 1e-12 >= raw['c_wall'][tick]
        assert record['cpu_seconds'] + 1e-12 >= raw['c_cpu'][tick]
        assert record['actual_timeout'] == (record['wall_seconds'] > wire.DEADLINE_SECONDS)
        for unit in ('wall', 'cpu'):
            phases = list(record['phase_' + unit].values())
            assert all(np.isfinite(value) and value >= 0 for value in phases)
            assert sum(phases) <= record[unit + '_seconds'] + 1e-9
        counts = record['counts']
        candidates = len(stage['evaluated_pairs']) if stage else 0
        reductions = candidates * stage['length'] + len(stage['partial'].get('contacts', [])) if stage else 0
        prefix = stage['prefix_count'] if stage else 0
        geometry = int(stage['geometry_count_by_q'].sum()) if stage else 0
        assert counts['candidate_requests'] == (len(stage['request_pairs']) if stage else 0)
        assert counts['candidate_plans'] == candidates and counts['state_reductions'] == reductions
        assert counts['geometry_snapshots'] == geometry and counts['prefix_ticks'] == prefix
        assert counts['virtual_c_decisions'] == 0
        assert counts['candidate_cache_hits'] + counts['candidate_uncached_requests'] == counts['candidate_requests']
        assert counts['interrupted_candidate_requests'] == counts['candidate_uncached_requests'] - candidates
        total_ticks = settled + prefix + reductions
        expected_work = dict(model_fleet_ticks=total_ticks, model_transitions_completed=total_ticks,
                             lrs_row_selections=5 * total_ticks, lrs_rows_completed=5 * total_ticks,
                             sinr_link_entries=250 * total_ticks, model_geometry_snapshots=settled + prefix + geometry)
        for name, expected in expected_work.items():
            assert counts[name] == expected
            factor = 250 if name == 'sinr_link_entries' else 5 if name in ('lrs_row_selections', 'lrs_rows_completed') else 1
            assert counts['history_' + name] == factor * settled
        for name in ('candidate_requests', 'candidate_plans', 'state_reductions', 'geometry_snapshots', 'prefix_ticks'):
            assert raw[name][index] == counts[name]
            work['producer_' + name] += counts[name]
    before = cursor
    if start is not None:
        settle(steps)
    assert raw['terminal_history_reductions'] == cursor - before
    assert raw['terminal_history_start'] == (-1 if start is None else start)
    assert bool(raw['terminal_history_complete']) == (start is not None and cursor == steps)
    assert bool(raw['terminal_burden_unknown']) == (start is not None and start > 0)
    for name, expected in (('model_valid', valid), ('model_contacts', predicted), ('model_lrs_grants', predicted_grants),
                           ('terminal_last', last), ('terminal_windows', windows), ('terminal_burden', burden),
                           ('terminal_last_grant', own)):
        np.testing.assert_array_equal(raw[name], expected)
    terminal = unpack_records(dict(decision_schema=raw['terminal_lrs_schema'], decision_bytes=raw['terminal_lrs_bytes']))
    assert terminal == [{}]
    expected_execution = dict(model_fleet_ticks=int(valid.sum()), model_transitions_completed=int(valid.sum()),
                              lrs_row_selections=5 * int(valid.sum()), lrs_rows_completed=5 * int(valid.sum()),
                              sinr_link_entries=250 * int(valid.sum()), model_geometry_snapshots=int(valid.sum()))
    assert dict(zip(raw['execution_lrs_count_names'].tolist(), raw['execution_lrs_counts'].tolist())) == expected_execution
    work['verified_model_transitions'] = int(valid.sum())
    return dict(work)
